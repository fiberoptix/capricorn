"""
Data Export/Import Endpoints
Handles full backup and restore of all user data across all modules
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text
from datetime import datetime
import json
import io

from app.core.database import get_async_db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.models.user_profile import UserProfile
from app.models.portfolio_models import Portfolio, PortfolioTransaction, MarketPrice, InvestorProfile

router = APIRouter(prefix="/data", tags=["data"])


async def create_bootstrap_user(db: AsyncSession) -> dict:
    """
    Create minimal seed data to make the app functional.
    Called on startup if database is empty, and after clearing all data.
    Returns dict with what was created.
    """
    created = {}
    
    # Check if UserProfile exists
    result = await db.execute(select(UserProfile).where(UserProfile.id == 1))
    existing_profile = result.scalar_one_or_none()
    
    if not existing_profile:
        # Create minimal UserProfile with sensible defaults for a single person
        # All partner values explicitly set to 0 (not None) for single-person use
        profile = UserProfile(
            id=1,
            email="user@capricorn.local",
            first_name="Capricorn",
            last_name="User",
            user="User",
            partner="Partner",
            user_age=30,
            partner_age=30,
            years_of_retirement=30,
            user_years_to_retirement=35,
            partner_years_to_retirement=35,
            user_salary=100000.00,
            partner_salary=0.00,  # Single person - no partner income
            user_bonus_rate=0.05,
            user_raise_rate=0.05,
            partner_bonus_rate=0.05,
            partner_raise_rate=0.05,
            monthly_living_expenses=5000.00,
            annual_discretionary_spending=10000.00,
            annual_inflation_rate=0.04,
            user_401k_contribution=24000.00,
            partner_401k_contribution=0.00,
            user_employer_match=5000.00,
            partner_employer_match=0.00,
            user_current_401k_balance=100000.00,
            partner_current_401k_balance=0.00,
            user_401k_growth_rate=0.10,
            partner_401k_growth_rate=0.10,
            current_ira_balance=0.00,
            ira_return_rate=0.10,
            current_trading_balance=0.00,
            trading_return_rate=0.10,
            current_savings_balance=0.00,
            savings_return_rate=0.00,
            expected_inheritance=0.00,
            inheritance_year=20,
            state="NY",
            local_tax_rate=0.01,
            filing_status="single",
            retirement_growth_rate=0.05,
            withdrawal_rate=0.04,
            fixed_monthly_savings=1000.00,
            percentage_of_leftover=0.50,
            savings_destination="trading"
        )
        db.add(profile)
        created["user_profile"] = 1
    
    # Check if InvestorProfile exists
    result = await db.execute(select(InvestorProfile).where(InvestorProfile.id == 1))
    existing_investor = result.scalar_one_or_none()
    
    if not existing_investor:
        # Create minimal InvestorProfile (matches UserProfile defaults)
        investor = InvestorProfile(
            id=1,
            name="Default Investor",
            annual_household_income=100000.00,
            filing_status="single",
            state_of_residence="NY",
            local_tax_rate=0.01
        )
        db.add(investor)
        created["investor_profile"] = 1
    
    if created:
        await db.commit()
        
        # Reset sequences to start after id 1
        for table in ['user_profile', 'investor_profiles']:
            try:
                await db.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), 1, true)"))
            except Exception:
                pass
        await db.commit()
    
    return created


async def ensure_bootstrap_user(db: AsyncSession) -> dict:
    """
    Public function to check and create bootstrap user if needed.
    Safe to call multiple times - only creates if missing.
    """
    return await create_bootstrap_user(db)


def model_to_dict(obj):
    """Convert SQLAlchemy model to dictionary"""
    if obj is None:
        return None
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        # Handle datetime serialization
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        result[column.name] = value
    return result


@router.get("/bootstrap")
async def bootstrap_user(db: AsyncSession = Depends(get_async_db)):
    """
    Ensure minimal user data exists for app to function.
    Safe to call multiple times - only creates if missing.
    """
    created = await ensure_bootstrap_user(db)
    
    if created:
        return {
            "success": True,
            "message": "Bootstrap user created",
            "created": created
        }
    else:
        return {
            "success": True,
            "message": "User data already exists, no bootstrap needed",
            "created": {}
        }


@router.get("/summary")
async def get_data_summary(db: AsyncSession = Depends(get_async_db)):
    """Get counts of all user data tables"""
    
    counts = {}
    
    # Count each table
    result = await db.execute(select(UserProfile))
    counts["user_profile"] = len(result.scalars().all())
    
    result = await db.execute(select(Account))
    counts["accounts"] = len(result.scalars().all())
    
    result = await db.execute(select(Category))
    counts["categories"] = len(result.scalars().all())
    
    result = await db.execute(select(Transaction))
    counts["transactions"] = len(result.scalars().all())
    
    result = await db.execute(select(Portfolio))
    counts["portfolios"] = len(result.scalars().all())
    
    result = await db.execute(select(PortfolioTransaction))
    counts["portfolio_transactions"] = len(result.scalars().all())
    
    result = await db.execute(select(MarketPrice))
    counts["market_prices"] = len(result.scalars().all())
    
    result = await db.execute(select(InvestorProfile))
    counts["investor_profiles"] = len(result.scalars().all())
    
    # Calculate total
    counts["total"] = sum(counts.values())
    
    return {"success": True, "counts": counts}


@router.get("/export")
async def export_all_data(db: AsyncSession = Depends(get_async_db)):
    """Export all user data to JSON file"""
    
    # Query all tables
    user_profiles = await db.execute(select(UserProfile))
    accounts = await db.execute(select(Account))
    categories = await db.execute(select(Category))
    transactions = await db.execute(select(Transaction))
    portfolios = await db.execute(select(Portfolio))
    portfolio_transactions = await db.execute(select(PortfolioTransaction))
    market_prices = await db.execute(select(MarketPrice))
    investor_profiles = await db.execute(select(InvestorProfile))
    
    # Convert to lists of dicts
    data = {
        "user_profile": [model_to_dict(r) for r in user_profiles.scalars().all()],
        "accounts": [model_to_dict(r) for r in accounts.scalars().all()],
        "categories": [model_to_dict(r) for r in categories.scalars().all()],
        "transactions": [model_to_dict(r) for r in transactions.scalars().all()],
        "portfolios": [model_to_dict(r) for r in portfolios.scalars().all()],
        "portfolio_transactions": [model_to_dict(r) for r in portfolio_transactions.scalars().all()],
        "market_prices": [model_to_dict(r) for r in market_prices.scalars().all()],
        "investor_profiles": [model_to_dict(r) for r in investor_profiles.scalars().all()],
    }
    
    # Build counts
    counts = {key: len(value) for key, value in data.items()}
    counts["total"] = sum(counts.values())
    
    # Build export object
    export_data = {
        "export_info": {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "source": "Capricorn"
        },
        "data": data,
        "counts": counts
    }
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"Capricorn_UserData_{timestamp}.json"
    
    # Convert to JSON
    json_content = json.dumps(export_data, indent=2, default=str)
    
    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(json_content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/import")
async def import_all_data(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Import user data from JSON file (replaces all existing data)"""
    
    # Read and parse JSON
    try:
        content = await file.read()
        import_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")
    
    # Validate structure
    if "data" not in import_data:
        raise HTTPException(status_code=400, detail="Invalid export file format: missing 'data' key")
    
    data = import_data["data"]
    
    try:
        # Clear existing data (reverse dependency order)
        await db.execute(delete(PortfolioTransaction))
        await db.execute(delete(Transaction))
        await db.execute(delete(MarketPrice))
        await db.execute(delete(Portfolio))
        await db.execute(delete(Category))
        await db.execute(delete(Account))
        await db.execute(delete(InvestorProfile))
        await db.execute(delete(UserProfile))
        
        await db.commit()
        
        imported_counts = {}
        
        # Import user_profile
        for item in data.get("user_profile", []):
            # Remove any None values that could cause issues
            clean_item = {k: v for k, v in item.items() if v is not None or k == 'id'}
            # Handle datetime fields
            for date_field in ['created_at', 'updated_at']:
                if date_field in clean_item and isinstance(clean_item[date_field], str):
                    clean_item[date_field] = datetime.fromisoformat(clean_item[date_field].replace('Z', '+00:00'))
            db.add(UserProfile(**clean_item))
        imported_counts["user_profile"] = len(data.get("user_profile", []))
        
        # Import investor_profiles
        for item in data.get("investor_profiles", []):
            clean_item = {k: v for k, v in item.items() if v is not None or k == 'id'}
            for date_field in ['created_at', 'updated_at']:
                if date_field in clean_item and isinstance(clean_item[date_field], str):
                    clean_item[date_field] = datetime.fromisoformat(clean_item[date_field].replace('Z', '+00:00'))
            db.add(InvestorProfile(**clean_item))
        imported_counts["investor_profiles"] = len(data.get("investor_profiles", []))
        
        # Import accounts
        for item in data.get("accounts", []):
            clean_item = {k: v for k, v in item.items() if v is not None or k == 'id'}
            for date_field in ['created_at', 'updated_at']:
                if date_field in clean_item and isinstance(clean_item[date_field], str):
                    clean_item[date_field] = datetime.fromisoformat(clean_item[date_field].replace('Z', '+00:00'))
            db.add(Account(**clean_item))
        imported_counts["accounts"] = len(data.get("accounts", []))
        
        # Import categories
        for item in data.get("categories", []):
            clean_item = {k: v for k, v in item.items() if v is not None or k == 'id'}
            for date_field in ['created_at', 'updated_at']:
                if date_field in clean_item and isinstance(clean_item[date_field], str):
                    clean_item[date_field] = datetime.fromisoformat(clean_item[date_field].replace('Z', '+00:00'))
            db.add(Category(**clean_item))
        imported_counts["categories"] = len(data.get("categories", []))
        
        # Import portfolios
        for item in data.get("portfolios", []):
            clean_item = {k: v for k, v in item.items() if v is not None or k == 'id'}
            for date_field in ['created_at', 'updated_at']:
                if date_field in clean_item and isinstance(clean_item[date_field], str):
                    clean_item[date_field] = datetime.fromisoformat(clean_item[date_field].replace('Z', '+00:00'))
            db.add(Portfolio(**clean_item))
        imported_counts["portfolios"] = len(data.get("portfolios", []))
        
        # Import market_prices
        for item in data.get("market_prices", []):
            clean_item = {k: v for k, v in item.items() if v is not None or k == 'id'}
            for date_field in ['created_at', 'updated_at', 'last_updated']:
                if date_field in clean_item and isinstance(clean_item[date_field], str):
                    clean_item[date_field] = datetime.fromisoformat(clean_item[date_field].replace('Z', '+00:00'))
            db.add(MarketPrice(**clean_item))
        imported_counts["market_prices"] = len(data.get("market_prices", []))
        
        # Commit base tables first
        await db.commit()
        
        # Import transactions (depends on accounts, categories)
        for item in data.get("transactions", []):
            clean_item = {k: v for k, v in item.items() if v is not None or k == 'id'}
            for date_field in ['created_at', 'updated_at', 'transaction_date']:
                if date_field in clean_item and isinstance(clean_item[date_field], str):
                    if 'T' in clean_item[date_field]:
                        clean_item[date_field] = datetime.fromisoformat(clean_item[date_field].replace('Z', '+00:00'))
                    else:
                        # Just a date, not datetime
                        from datetime import date
                        clean_item[date_field] = datetime.strptime(clean_item[date_field], '%Y-%m-%d').date()
            db.add(Transaction(**clean_item))
        imported_counts["transactions"] = len(data.get("transactions", []))
        
        # Import portfolio_transactions (depends on portfolios)
        for item in data.get("portfolio_transactions", []):
            clean_item = {k: v for k, v in item.items() if v is not None or k == 'id'}
            for date_field in ['created_at', 'updated_at', 'transaction_date']:
                if date_field in clean_item and isinstance(clean_item[date_field], str):
                    if 'T' in clean_item[date_field]:
                        clean_item[date_field] = datetime.fromisoformat(clean_item[date_field].replace('Z', '+00:00'))
                    else:
                        from datetime import date
                        clean_item[date_field] = datetime.strptime(clean_item[date_field], '%Y-%m-%d').date()
            db.add(PortfolioTransaction(**clean_item))
        imported_counts["portfolio_transactions"] = len(data.get("portfolio_transactions", []))
        
        await db.commit()
        
        # Reset sequences for all tables
        tables_with_sequences = [
            'user_profile', 'accounts', 'categories', 'transactions',
            'portfolios', 'portfolio_transactions', 'market_prices', 'investor_profiles'
        ]
        
        for table in tables_with_sequences:
            try:
                await db.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
                ))
            except Exception:
                pass  # Some tables might not have sequences
        
        await db.commit()
        
        imported_counts["total"] = sum(imported_counts.values())
        
        return {
            "success": True,
            "message": "Data imported successfully",
            "imported": imported_counts
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.delete("/clear")
async def clear_all_data(db: AsyncSession = Depends(get_async_db)):
    """Clear all user data from the database"""
    
    try:
        deleted_counts = {}
        
        # Get counts before deletion
        result = await db.execute(select(PortfolioTransaction))
        deleted_counts["portfolio_transactions"] = len(result.scalars().all())
        
        result = await db.execute(select(Transaction))
        deleted_counts["transactions"] = len(result.scalars().all())
        
        result = await db.execute(select(MarketPrice))
        deleted_counts["market_prices"] = len(result.scalars().all())
        
        result = await db.execute(select(Portfolio))
        deleted_counts["portfolios"] = len(result.scalars().all())
        
        result = await db.execute(select(Category))
        deleted_counts["categories"] = len(result.scalars().all())
        
        result = await db.execute(select(Account))
        deleted_counts["accounts"] = len(result.scalars().all())
        
        result = await db.execute(select(InvestorProfile))
        deleted_counts["investor_profiles"] = len(result.scalars().all())
        
        result = await db.execute(select(UserProfile))
        deleted_counts["user_profile"] = len(result.scalars().all())
        
        # Clear all user data tables (reverse dependency order)
        await db.execute(delete(PortfolioTransaction))
        await db.execute(delete(Transaction))
        await db.execute(delete(MarketPrice))
        await db.execute(delete(Portfolio))
        await db.execute(delete(Category))
        await db.execute(delete(Account))
        await db.execute(delete(InvestorProfile))
        await db.execute(delete(UserProfile))
        
        await db.commit()
        
        # Reset sequences
        tables_with_sequences = [
            'user_profile', 'accounts', 'categories', 'transactions',
            'portfolios', 'portfolio_transactions', 'market_prices', 'investor_profiles'
        ]
        
        for table in tables_with_sequences:
            try:
                await db.execute(text(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1"))
            except Exception:
                pass  # Some tables might not have sequences
        
        await db.commit()
        
        deleted_counts["total"] = sum(deleted_counts.values())
        
        # Create bootstrap user so app continues to function
        bootstrap_created = await create_bootstrap_user(db)
        
        return {
            "success": True,
            "message": "All user data has been cleared. Bootstrap user created.",
            "deleted": deleted_counts,
            "bootstrap_created": bootstrap_created
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")

