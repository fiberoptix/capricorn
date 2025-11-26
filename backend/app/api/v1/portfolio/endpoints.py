"""
Portfolio Manager API Endpoints

Real implementation connecting to PostgreSQL database.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete, text
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from app.core.database import get_async_db

# Import our service adapter that wraps all the portfolio services
# Service adapter not needed - using direct async services
from app.models.portfolio_models import Portfolio, PortfolioTransaction, MarketPrice, InvestorProfile
from app.services.transaction_service import TransactionService
from app.services.portfolio_service import PortfolioService
from app.services.investor_profile_service import InvestorProfileService
from app.services.market_data_service import MarketDataService, get_refresh_status, start_background_refresh
from app.core.config import settings

# Helper to get async database URL for background tasks
def get_async_db_url() -> str:
    """Get the async database URL for background tasks"""
    return settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
from app.services.profile_service import ProfileService  # Phase 3G - Use unified profile
from pydantic import BaseModel

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# Use portfolio_transactions table to avoid conflicts with Finance module's transactions table
TRANSACTIONS_TABLE = "portfolio_transactions"

# Simple database queries using raw SQL for now

@router.get("/health")
async def health_check():
    """Portfolio Manager health check"""
    return {
        "status": "healthy",
        "service": "portfolio-manager",
        "version": "2.0.0",
        "database": "connected"
    }

@router.get("/summary")
async def get_portfolio_summary(db: AsyncSession = Depends(get_async_db)):
    """Get overall portfolio summary across all portfolios"""
    try:
        # Get all portfolios with their values and gains
        portfolios_result = await db.execute(text(f"""
            SELECT 
                p.id,
                p.name,
                p.cash_on_hand,
                COALESCE(SUM(
                    CASE 
                        WHEN mp.current_price IS NOT NULL THEN t.quantity * mp.current_price
                        ELSE t.quantity * t.price_per_share
                    END
                ), 0) as securities_value,
                COALESCE(SUM(
                    CASE 
                        WHEN mp.current_price IS NOT NULL THEN (t.quantity * mp.current_price) - (t.quantity * t.price_per_share)
                        ELSE 0
                    END
                ), 0) as unrealized_gains
            FROM portfolios p
            LEFT JOIN {TRANSACTIONS_TABLE} t ON p.id = t.portfolio_id
            LEFT JOIN market_prices mp ON t.ticker_symbol = mp.ticker_symbol
            GROUP BY p.id, p.name, p.cash_on_hand
        """))
        
        portfolios = portfolios_result.fetchall()
        
        total_value = Decimal('0')
        total_securities = Decimal('0')
        total_unrealized_gains = Decimal('0')
        total_cash = Decimal('0')
        
        for portfolio in portfolios:
            cash = portfolio.cash_on_hand or Decimal('0')
            securities = portfolio.securities_value or Decimal('0')
            gains = portfolio.unrealized_gains or Decimal('0')
            portfolio_total = cash + securities
            
            total_value += portfolio_total
            total_securities += securities
            total_unrealized_gains += gains
            total_cash += cash
        
        # Use the new Tax API for accurate calculations (Phase 3G - use user_profile)
        from app.services.tax_calculation_service import TaxCalculationService
        tax_service = TaxCalculationService(db)
        
        tax_liability = Decimal('0')
        if total_unrealized_gains > 0:
            try:
                # Get profile from unified user_profile table
                profile_dict = await ProfileService.get_profile(db)
                
                # Calculate annual household income from profile
                from app.models.user_profile import UserProfile
                result = await db.execute(select(UserProfile).where(UserProfile.id == 1))
                profile_model = result.scalar_one_or_none()
                
                if profile_model:
                    annual_income = ProfileService.get_annual_household_income(profile_model)
                    
                    # For summary, use conservative short-term tax calculation
                    tax_result = await tax_service.calculate_short_term_capital_gains_tax(
                        gains=float(total_unrealized_gains),
                        base_income=annual_income,
                        filing_status=profile_dict.get('filing_status', 'married_filing_jointly'),
                        state=profile_dict.get('state', 'NY'),
                        local_tax_rate=profile_dict.get('local_tax_rate', 0.01),
                        year=2025
                    )
                    tax_liability = Decimal(str(tax_result['total_tax']))
            except Exception as e:
                print(f"Warning: Could not calculate tax liability via Tax API: {e}")
                tax_liability = total_unrealized_gains * Decimal('0.35')
        
        after_tax_value = total_value - tax_liability
        
        return {
            "total_value": float(total_value),
            "securities_value": float(total_securities),
            "tax_liability": float(tax_liability),
            "after_tax_value": float(after_tax_value),
            "cash_on_hand": float(total_cash),
            "unrealized_gains": float(total_unrealized_gains),
            "portfolio_count": len(portfolios)
        }
        
    except Exception as e:
        print(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolios")
async def get_portfolios(db: AsyncSession = Depends(get_async_db)):
    """Get all portfolios with calculated values"""
    try:
        # Get portfolios
        result = await db.execute(text("""
            SELECT 
                p.id,
                p.name,
                p.type,
                p.description,
                p.cash_on_hand,
                p.investor_profile_id,
                COALESCE(SUM(
                    CASE 
                        WHEN mp.current_price IS NOT NULL THEN t.quantity * mp.current_price
                        ELSE t.quantity * t.price_per_share
                    END
                ), 0) as securities_value,
                COALESCE(SUM(
                    CASE 
                        WHEN mp.current_price IS NOT NULL THEN (t.quantity * mp.current_price) - (t.quantity * t.price_per_share)
                        ELSE 0
                    END
                ), 0) as unrealized_gains
            FROM portfolios p
            LEFT JOIN portfolio_transactions t ON p.id = t.portfolio_id AND t.transaction_type = 'buy'
            LEFT JOIN market_prices mp ON t.ticker_symbol = mp.ticker_symbol
            GROUP BY p.id, p.name, p.type, p.description, p.cash_on_hand, p.investor_profile_id
            ORDER BY p.id
        """))
        
        portfolios = []
        for row in result:
            portfolio = {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "description": row[3],
                "cash_on_hand": float(row[4] or 0),
                "investor_profile_id": row[5],
                "securities_value": float(row[6] or 0),
                "total_unrealized_gains": float(row[7] or 0),
                "total_value": float(row[4] or 0) + float(row[6] or 0)
            }
            portfolios.append(portfolio)
        
        # Calculate total value
        total_value = sum(p["total_value"] for p in portfolios)
        
        return {
            "portfolios": portfolios,
            "total_value": total_value,
            "count": len(portfolios)
        }
    except Exception as e:
        print(f"Error getting portfolios: {e}")
        return {"portfolios": [], "total_value": 0, "count": 0}

@router.get("/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get single portfolio with details"""
    try:
        result = await db.execute(text("""
            SELECT 
                p.id,
                p.name,
                p.type,
                p.description,
                p.cash_on_hand,
                COUNT(DISTINCT t.id) as transaction_count,
                COALESCE(SUM(
                    CASE 
                        WHEN mp.current_price IS NOT NULL THEN t.quantity * mp.current_price
                        ELSE t.quantity * t.price_per_share
                    END
                ), 0) as securities_value
            FROM portfolios p
            LEFT JOIN portfolio_transactions t ON p.id = t.portfolio_id
            LEFT JOIN market_prices mp ON t.ticker_symbol = mp.ticker_symbol
            WHERE p.id = :portfolio_id
            GROUP BY p.id, p.name, p.type, p.description, p.cash_on_hand
        """), {"portfolio_id": portfolio_id})
        
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        return {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "description": row[3],
            "cash_on_hand": float(row[4] or 0),
            "transaction_count": row[5],
            "securities_value": float(row[6] or 0),
            "total_value": float(row[4] or 0) + float(row[6] or 0)
        }
    except Exception as e:
        print(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolios/{portfolio_id}/summary")
async def get_portfolio_summary(portfolio_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get portfolio summary statistics"""
    try:
        # Get transaction counts
        result = await db.execute(text(f"""
            SELECT 
                COUNT(*) as total_transactions,
                COUNT(CASE WHEN transaction_type = 'Buy' THEN 1 END) as buy_transactions,
                COUNT(CASE WHEN transaction_type = 'Sell' THEN 1 END) as sell_transactions,
                COUNT(DISTINCT ticker_symbol) as unique_stocks
            FROM portfolio_transactions
            WHERE portfolio_id = {portfolio_id}
        """))
        
        stats = result.fetchone()
        
        # Get portfolio info
        portfolio_result = await db.execute(text(f"""
            SELECT name, type, description, created_at, updated_at
            FROM portfolios WHERE id = {portfolio_id}
        """))
        
        portfolio = portfolio_result.fetchone()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        return {
            "portfolio_id": portfolio_id,
            "name": portfolio[0],
            "type": portfolio[1],
            "description": portfolio[2],
            "total_transactions": stats[0] if stats else 0,
            "buy_transactions": stats[1] if stats else 0,
            "sell_transactions": stats[2] if stats else 0,
            "unique_stocks": stats[3] if stats else 0,
            "created_at": portfolio[3].isoformat() if portfolio[3] else None,
            "updated_at": portfolio[4].isoformat() if portfolio[4] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolios/{portfolio_id}/market-value")
async def get_portfolio_market_value(portfolio_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get portfolio market value"""
    try:
        from app.services.portfolio_service import PortfolioService
        service = PortfolioService(db)
        value = await service.calculate_portfolio_value(portfolio_id)
        if not value:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return value
        
        # OLD CODE BELOW (keeping for reference) - this was reimplementing everything!
        # Get portfolio cash
        cash_result = await db.execute(text(f"""
            SELECT cash_on_hand FROM portfolios WHERE id = {portfolio_id}
        """))
        cash_row = cash_result.fetchone()
        if not cash_row:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        cash_on_hand = float(cash_row[0])
        
        # Get holdings aggregated by ticker with detailed calculations
        holdings_result = await db.execute(text(f"""
            SELECT 
                t.ticker_symbol,
                SUM(CASE WHEN t.transaction_type = 'Buy' THEN t.quantity ELSE -t.quantity END) as net_quantity,
                SUM(CASE WHEN t.transaction_type = 'Buy' THEN t.quantity * t.price_per_share ELSE 0 END) as total_invested,
                AVG(CASE WHEN t.transaction_type = 'Buy' THEN t.price_per_share END) as avg_cost_basis,
                mp.current_price,
                COUNT(*) as transaction_count
            FROM portfolio_transactions t
            LEFT JOIN market_prices mp ON t.ticker_symbol = mp.ticker_symbol
            WHERE t.portfolio_id = {portfolio_id}
            GROUP BY t.ticker_symbol, mp.current_price
            HAVING SUM(CASE WHEN t.transaction_type = 'Buy' THEN t.quantity ELSE -t.quantity END) > 0
        """))
        
        holdings = {}
        total_investment_value = 0
        total_cost_basis = 0
        
        for row in holdings_result:
            ticker = row[0]
            quantity = float(row[1])
            total_invested = float(row[2]) if row[2] else 0
            avg_cost = float(row[3]) if row[3] else 0
            current_price = float(row[4]) if row[4] else 0
            tx_count = row[5]
            
            market_value = quantity * current_price
            gain_loss = market_value - total_invested
            gain_loss_percent = (gain_loss / total_invested * 100) if total_invested > 0 else 0
            
            holdings[ticker] = {
                "quantity": quantity,
                "avg_cost_basis": avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "cost_basis": total_invested,
                "gain_loss": gain_loss,
                "gain_loss_percent": gain_loss_percent,
                "transaction_count": tx_count
            }
            
            total_investment_value += market_value
            total_cost_basis += total_invested
        
        total_market_value = total_investment_value + cash_on_hand
        total_gain_loss = total_investment_value - total_cost_basis
        total_gain_loss_percent = (total_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        return {
            "portfolio_id": portfolio_id,
            "investment_value": total_investment_value,
            "cash_on_hand": cash_on_hand,
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "total_gain_loss": total_gain_loss,
            "total_gain_loss_percent": total_gain_loss_percent,
            "holdings": holdings
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting market value: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/break-even/portfolio/{portfolio_id}")
async def calculate_portfolio_break_even(
    portfolio_id: int,
    request_body: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Calculate comprehensive tax-aware break-even analysis for entire portfolio"""
    try:
        from decimal import Decimal
        from datetime import date
        from app.services.tax_calculation_service import TaxCalculationService
        from app.models.user_profile import UserProfile
        
        # Get profile from unified user_profile table
        profile_dict = await ProfileService.get_profile(db)
        result = await db.execute(select(UserProfile).where(UserProfile.id == 1))
        profile_model = result.scalar_one_or_none()
        annual_income = ProfileService.get_annual_household_income(profile_model) if profile_model else 300000.0
        tax_service = TaxCalculationService(db)
        
        # Get portfolio
        portfolio_result = await db.execute(text(f"""
            SELECT name FROM portfolios WHERE id = {portfolio_id}
        """))
        portfolio = portfolio_result.fetchone()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Get all transactions with current prices
        transactions_result = await db.execute(text(f"""
            SELECT 
                t.id,
                t.ticker_symbol,
                t.quantity,
                t.price_per_share,
                t.transaction_date,
                t.transaction_type,
                mp.current_price,
                t.stock_name
            FROM portfolio_transactions t
            LEFT JOIN market_prices mp ON t.ticker_symbol = mp.ticker_symbol
            WHERE t.portfolio_id = {portfolio_id}
            AND t.transaction_type = 'buy'
            AND t.quantity > 0
        """))
        
        transactions = transactions_result.fetchall()
        
        all_transaction_analyses = []
        total_current_value = 0
        total_tax_owed = 0
        total_after_tax_proceeds = 0
        total_break_even_sum = 0
        valid_count = 0
        
        for tx_id, ticker, quantity, purchase_price, purchase_date, tx_type, current_price, stock_name in transactions:
            if not current_price:
                continue
            
            # Calculate values
            current_value = float(quantity * current_price)
            cost_basis = float(quantity * purchase_price)
            gain_loss = current_value - cost_basis
            gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
            
            # Determine holding period
            days_held = (date.today() - purchase_date).days if isinstance(purchase_date, date) else 0
            is_long_term = days_held > 365
            
            # Calculate tax using Tax API
            tax_result = None
            if gain_loss > 0:
                if is_long_term:
                    tax_result = await tax_service.calculate_long_term_capital_gains_tax(
                        gains=gain_loss,
                        base_income=annual_income,
                        filing_status=profile_dict.get('filing_status', 'married_filing_jointly'),
                        state=profile_dict.get('state', 'NY'),
                        local_tax_rate=profile_dict.get('local_tax_rate', 0.01),
                        year=2025
                    )
                else:
                    tax_result = await tax_service.calculate_short_term_capital_gains_tax(
                        gains=gain_loss,
                        base_income=annual_income,
                        filing_status=profile_dict.get('filing_status', 'married_filing_jointly'),
                        state=profile_dict.get('state', 'NY'),
                        local_tax_rate=profile_dict.get('local_tax_rate', 0.01),
                        year=2025
                    )
                
                total_tax = tax_result['total_tax']
                after_tax_proceeds = gain_loss - total_tax
                
                # Calculate break-even percentage
                break_even_price = cost_basis + total_tax
                break_even_drop_dollars = current_value - break_even_price
                break_even_drop_pct = (break_even_drop_dollars / current_value * 100) if current_value > 0 else 0
                
                # Recommendation logic
                if break_even_drop_pct >= 15:
                    recommendation = "hold"
                    risk_level = "Low Risk"
                elif break_even_drop_pct >= 5:
                    recommendation = "monitor_closely"
                    risk_level = "Medium Risk"
                else:
                    recommendation = "consider_selling"
                    risk_level = "High Risk"
                
                # Accumulate totals
                total_current_value += current_value
                total_tax_owed += total_tax
                total_after_tax_proceeds += after_tax_proceeds
                total_break_even_sum += break_even_drop_pct
                valid_count += 1
            else:
                # Position at a loss
                total_tax = 0
                after_tax_proceeds = gain_loss  # No tax on losses
                break_even_drop_pct = 0
                recommendation = "hold"  # Already at a loss
                risk_level = "N/A"
                total_current_value += current_value
            
            # Build transaction analysis
            transaction_analysis = {
                "transaction_id": tx_id,
                "ticker_symbol": ticker,
                "stock_name": stock_name,
                "position_status": "gain" if gain_loss > 0 else "loss",
                "recommendation": recommendation,
                "financial_analysis": {
                    "quantity": float(quantity),
                    "purchase_price": float(purchase_price),
                    "current_price": float(current_price),
                    "cost_basis": cost_basis,
                    "current_value": current_value,
                    "current_gain_loss": gain_loss,
                    "gain_loss_percentage": gain_loss_pct,
                    "holding_period_days": days_held
                },
                "tax_analysis": {
                    "gains_type": "long_term" if is_long_term else "short_term",
                    "total_tax_owed": total_tax if gain_loss > 0 else 0,
                    "after_tax_proceeds": after_tax_proceeds,
                    "effective_tax_rate": tax_result['effective_rate'] if tax_result else 0
                },
                "break_even_analysis": {
                    "loss_required_percentage": break_even_drop_pct,
                    "risk_level": risk_level
                }
            }
            
            all_transaction_analyses.append(transaction_analysis)
        
        # Calculate portfolio summary
        average_break_even = (total_break_even_sum / valid_count) if valid_count > 0 else 0
        
        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio[0],
            "total_positions": len(transactions),
            "positions_analyzed": len(all_transaction_analyses),
            "positions_with_gains": valid_count,
            "transactions": all_transaction_analyses,
            "portfolio_summary": {
                "total_current_value": total_current_value,
                "total_tax_if_all_sold": total_tax_owed,
                "total_after_tax_proceeds": total_after_tax_proceeds,
                "average_break_even_percentage": average_break_even
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error calculating break-even: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/portfolios/{portfolio_id}/cash")
async def update_portfolio_cash(
    portfolio_id: int,
    cash_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Update portfolio cash on hand"""
    try:
        cash_amount = float(cash_data.get('cash_on_hand', 0))
        
        result = await db.execute(text("""
            UPDATE portfolios
            SET cash_on_hand = :cash,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            RETURNING id, cash_on_hand
        """), {
            'id': portfolio_id,
            'cash': cash_amount
        })
        
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        await db.commit()
        
        return {
            "id": row[0],
            "cash_on_hand": float(row[1]),
            "message": "Cash updated successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Delete a portfolio and all its transactions
    
    Note: Transactions are deleted via CASCADE foreign key constraint.
    This automatically removes the portfolio's stocks from the market data fetch list.
    """
    try:
        # Check if portfolio exists first
        result = await db.execute(
            text("SELECT id, name FROM portfolios WHERE id = :id"),
            {'id': portfolio_id}
        )
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        portfolio_name = row[1]
        
        # Delete portfolio (CASCADE will delete transactions)
        result = await db.execute(
            text("DELETE FROM portfolios WHERE id = :id"),
            {'id': portfolio_id}
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Portfolio '{portfolio_name}' deleted successfully",
            "deleted_id": portfolio_id
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error deleting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/portfolios/{portfolio_id}")
async def update_portfolio(
    portfolio_id: int,
    portfolio_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Update an existing portfolio"""
    service = PortfolioService(db)
    
    updated_portfolio = await service.update_portfolio(
        portfolio_id=portfolio_id,
        name=portfolio_data.get('name'),
        type=portfolio_data.get('type'),
        description=portfolio_data.get('description'),
        cash_on_hand=portfolio_data.get('cash_on_hand'),
        investor_profile_id=portfolio_data.get('investor_profile_id')
    )
    
    if not updated_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "id": updated_portfolio.id,
        "name": updated_portfolio.name,
        "type": updated_portfolio.type,
        "description": updated_portfolio.description,
        "cash_on_hand": float(updated_portfolio.cash_on_hand),
        "investor_profile_id": updated_portfolio.investor_profile_id,
        "message": "Portfolio updated successfully"
    }

@router.post("/portfolios")
async def create_portfolio(
    portfolio_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new portfolio"""
    try:
        # Extract values from request body
        name = portfolio_data.get('name')
        portfolio_type = portfolio_data.get('type', 'real')
        description = portfolio_data.get('description', '')
        cash_on_hand = float(portfolio_data.get('cash_on_hand', 0))
        investor_profile_id = portfolio_data.get('investor_profile_id')
        
        # If no investor_profile_id provided, try to get the first one or use None
        if investor_profile_id is None:
            result = await db.execute(text("SELECT id FROM investor_profiles LIMIT 1"))
            row = result.first()
            investor_profile_id = row.id if row else None
        
        if not name:
            raise HTTPException(status_code=400, detail="Portfolio name is required")
        
        # Use parameterized query for security
        result = await db.execute(text("""
            INSERT INTO portfolios (name, type, description, cash_on_hand, investor_profile_id)
            VALUES (:name, :type, :description, :cash_on_hand, :investor_profile_id)
            RETURNING id, name, type, description, cash_on_hand, investor_profile_id
        """), {
            'name': name,
            'type': portfolio_type,
            'description': description,
            'cash_on_hand': cash_on_hand,
            'investor_profile_id': investor_profile_id
        })
        
        row = result.first()
        await db.commit()
        
        if row:
            return {
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "description": row.description,
                "cash_on_hand": float(row.cash_on_hand),
                "investor_profile_id": row.investor_profile_id,
                "message": "Portfolio created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create portfolio")
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions")
async def get_transactions(
    portfolio_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get transactions, optionally filtered by portfolio"""
    try:
        query = text("""
            SELECT 
                t.id,
                t.portfolio_id,
                t.stock_name,
                t.ticker_symbol,
                t.transaction_type,
                t.quantity,
                t.price_per_share,
                t.transaction_date,
                p.name as portfolio_name,
                mp.current_price
            FROM transactions t
            JOIN portfolios p ON t.portfolio_id = p.id
            LEFT JOIN market_prices mp ON t.ticker_symbol = mp.ticker_symbol
        """)
        
        if portfolio_id:
            query = text(f"""
                SELECT 
                    t.id,
                    t.portfolio_id,
                    t.stock_name,
                    t.ticker_symbol,
                    t.transaction_type,
                    t.quantity,
                    t.price_per_share,
                    t.transaction_date,
                    p.name as portfolio_name,
                    mp.current_price
                FROM portfolio_transactions t
                JOIN portfolios p ON t.portfolio_id = p.id
                LEFT JOIN market_prices mp ON t.ticker_symbol = mp.ticker_symbol
                WHERE t.portfolio_id = {portfolio_id}
                ORDER BY t.transaction_date DESC, t.id DESC
            """)
        
            query = text(query.text + " ORDER BY t.transaction_date DESC, t.id DESC") if not portfolio_id else query
        
        result = await db.execute(query)
        
        transactions = []
        for row in result:
            transaction = {
                "id": row[0],
                "portfolio_id": row[1],
                "stock_name": row[2],
                "ticker": row[3],  # Changed from ticker_symbol to ticker for frontend compatibility
                "ticker_symbol": row[3],  # Keep for backwards compatibility
                "transaction_type": row[4],
                "quantity": float(row[5]),
                "price_per_share": float(row[6]),
                "transaction_date": row[7].isoformat() if isinstance(row[7], date) else str(row[7]),
                "portfolio_name": row[8],
                "current_price": float(row[9]) if row[9] else None,
                "current_value": float(row[5]) * float(row[9]) if row[9] else None,
                "gain_loss": (float(row[9]) - float(row[6])) * float(row[5]) if row[9] else None
            }
            transactions.append(transaction)
        
        return {
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        print(f"Error getting transactions: {e}")
        return {"transactions": [], "count": 0}

# Request/Response models for transactions
class TransactionCreate(BaseModel):
    portfolio_id: int
    ticker: str
    transaction_type: str
    quantity: float
    price_per_share: float
    transaction_date: str

class TransactionUpdate(BaseModel):
    ticker: Optional[str] = None
    transaction_type: Optional[str] = None
    quantity: Optional[float] = None
    price_per_share: Optional[float] = None
    transaction_date: Optional[str] = None

@router.post("/transactions")
async def create_transaction(
    transaction_data: TransactionCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create new transaction in Capricorn's database"""
    service = TransactionService(db)
    
    # Parse date string
    from datetime import datetime
    transaction_date = datetime.strptime(transaction_data.transaction_date, "%Y-%m-%d").date()
    
    new_transaction = await service.create_transaction(
        portfolio_id=transaction_data.portfolio_id,
        ticker=transaction_data.ticker,
        transaction_type=transaction_data.transaction_type.lower(),  # Convert to lowercase for DB constraint
        quantity=Decimal(str(transaction_data.quantity)),
        price_per_share=Decimal(str(transaction_data.price_per_share)),
        transaction_date=transaction_date,
        stock_name=transaction_data.ticker  # Use ticker as stock name
    )
    
    return {
        "id": new_transaction.id,
        "portfolio_id": new_transaction.portfolio_id,
        "ticker": new_transaction.ticker_symbol,
        "transaction_type": new_transaction.transaction_type,
        "quantity": float(new_transaction.quantity),
        "price_per_share": float(new_transaction.price_per_share),
        "transaction_date": str(new_transaction.transaction_date),
        "message": "Transaction created successfully"
    }

@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get transaction by ID from Capricorn's database"""
    service = TransactionService(db)
    transaction = await service.get_transaction_by_id(transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "id": transaction.id,
        "portfolio_id": transaction.portfolio_id,
        "ticker": transaction.ticker_symbol,
        "transaction_type": transaction.transaction_type,
        "quantity": float(transaction.quantity),
        "price_per_share": float(transaction.price_per_share),
        "transaction_date": str(transaction.transaction_date)
    }

@router.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update transaction in Capricorn's database"""
    service = TransactionService(db)
    
    update_data = {}
    if transaction_data.ticker:
        update_data['ticker'] = transaction_data.ticker
    if transaction_data.transaction_type:
        update_data['transaction_type'] = transaction_data.transaction_type
    if transaction_data.quantity:
        update_data['quantity'] = Decimal(str(transaction_data.quantity))
    if transaction_data.price_per_share:
        update_data['price_per_share'] = Decimal(str(transaction_data.price_per_share))
    if transaction_data.transaction_date:
        from datetime import datetime
        update_data['transaction_date'] = datetime.strptime(transaction_data.transaction_date, "%Y-%m-%d").date()
    
    updated = await service.update_transaction(transaction_id, **update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "success": True,
        "message": "Transaction updated successfully"
    }

@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int, db: AsyncSession = Depends(get_async_db)):
    """Delete transaction from Capricorn's database"""
    service = TransactionService(db)
    success = await service.delete_transaction(transaction_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "success": True,
        "message": "Transaction deleted successfully"
    }

@router.get("/market-prices")
async def get_market_prices(db: AsyncSession = Depends(get_async_db)):
    """Get all market prices"""
    try:
        result = await db.execute(text("""
            SELECT ticker_symbol, current_price, last_updated
            FROM market_prices
            ORDER BY ticker_symbol
        """))
        
        prices = []
        for row in result:
            price = {
                "ticker": row[0],
                "ticker_symbol": row[0],  # Frontend compatibility
                "price": float(row[1]),
                "current_price": float(row[1]),  # Frontend compatibility
                "last_updated": (row[2].isoformat() + 'Z') if row[2] else None
            }
            prices.append(price)
        
        return {
            "prices": prices,
            "count": len(prices)
        }
    except Exception as e:
        print(f"Error getting market prices: {e}")
        return {"prices": [], "count": 0}

@router.put("/market-prices/{ticker}")
async def update_market_price_by_ticker(
    ticker: str,
    price_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Update or insert a market price for a specific ticker"""
    try:
        price = float(price_data.get('current_price', 0))
        
        if price <= 0:
            raise ValueError("Price must be positive")
        
        # Try update first
        result = await db.execute(
            text("""
                UPDATE market_prices 
                SET current_price = :price, last_updated = CURRENT_TIMESTAMP
                WHERE ticker_symbol = :ticker
            """),
            {'ticker': ticker.upper(), 'price': price}
        )
        
        if result.rowcount == 0:
            # Insert if not exists
            await db.execute(
                text("""
                    INSERT INTO market_prices (ticker_symbol, current_price)
                    VALUES (:ticker, :price)
                """),
                {'ticker': ticker.upper(), 'price': price}
            )
        
        await db.commit()
        
        # Fetch updated price
        result = await db.execute(
            text("""
                SELECT ticker_symbol, current_price, last_updated
                FROM market_prices
                WHERE ticker_symbol = :ticker
            """),
            {'ticker': ticker.upper()}
        )
        row = result.first()
        
        return {
            "ticker": row[0],
            "ticker_symbol": row[0],
            "price": float(row[1]),
            "current_price": float(row[1]),
            "last_updated": (row[2].isoformat() + 'Z') if row[2] else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        print(f"Error updating market price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market-prices/update")
async def update_market_price(
    ticker: str,
    price: float,
    db: AsyncSession = Depends(get_async_db)
):
    """Legacy endpoint - Update or insert a market price"""
    try:
        # Try update first
        result = await db.execute(text(f"""
            UPDATE market_prices 
            SET current_price = {price}, last_updated = CURRENT_TIMESTAMP
            WHERE ticker_symbol = '{ticker}'
        """))
        
        if result.rowcount == 0:
            # Insert if not exists
            await db.execute(text(f"""
                INSERT INTO market_prices (ticker_symbol, current_price)
                VALUES ('{ticker}', {price})
            """))
        
        await db.commit()
        return {"message": f"Price updated for {ticker}"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/investor-profiles")
async def get_investor_profiles(db: AsyncSession = Depends(get_async_db)):
    """Get investor profiles (single profile system)"""
    try:
        result = await db.execute(text("""
            SELECT id, name, annual_household_income, filing_status, 
                   state_of_residence, local_tax_rate
            FROM investor_profiles
            ORDER BY id
            LIMIT 1
        """))
        
        row = result.first()
        if row:
            profile = {
                "id": row[0],
                "name": row[1],
                "annual_household_income": float(row[2]),
                "filing_status": row[3],
                "state_of_residence": row[4],
                "local_tax_rate": float(row[5])
            }
            return {"profiles": [profile]}
        
        return {"profiles": []}
    except Exception as e:
        print(f"Error getting investor profiles: {e}")
        return {"profiles": []}


# ============= NEW INVESTOR PROFILE ENDPOINTS =============

@router.get("/investor-profile")
async def get_investor_profile(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get the single user's investor profile"""
    try:
        service = InvestorProfileService(db)
        profile = await service.get_or_create_profile()
        
        return {
            "id": profile.id,
            "name": profile.name,
            "annual_household_income": float(profile.annual_household_income),
            "filing_status": profile.filing_status,
            "state_of_residence": profile.state_of_residence,
            "local_tax_rate": float(profile.local_tax_rate),
            "local_tax_rate_percent": float(profile.local_tax_rate) * 100
        }
    except Exception as e:
        print(f"Error getting investor profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/investor-profile")
async def update_investor_profile(
    profile_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Update the investor profile"""
    try:
        service = InvestorProfileService(db)
        
        # Convert income to Decimal if provided
        kwargs = {}
        if 'name' in profile_data:
            kwargs['name'] = profile_data['name']
        if 'annual_household_income' in profile_data:
            kwargs['annual_household_income'] = Decimal(str(profile_data['annual_household_income']))
        if 'filing_status' in profile_data:
            kwargs['filing_status'] = profile_data['filing_status']
        if 'state_of_residence' in profile_data:
            kwargs['state_of_residence'] = profile_data['state_of_residence']
        if 'local_tax_rate' in profile_data:
            # Accept as percentage (1.0) or decimal (0.01)
            rate = profile_data['local_tax_rate']
            if rate > 1:  # Provided as percentage
                rate = rate / 100
            kwargs['local_tax_rate'] = Decimal(str(rate))
        
        profile = await service.update_profile(**kwargs)
        
        return {
            "id": profile.id,
            "name": profile.name,
            "annual_household_income": float(profile.annual_household_income),
            "filing_status": profile.filing_status,
            "state_of_residence": profile.state_of_residence,
            "local_tax_rate": float(profile.local_tax_rate),
            "local_tax_rate_percent": float(profile.local_tax_rate) * 100,
            "message": "Profile updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error updating investor profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investor-profile/tax-settings")
async def get_tax_settings(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get tax settings for the investor profile"""
    try:
        service = InvestorProfileService(db)
        return await service.get_tax_settings()
    except Exception as e:
        print(f"Error getting tax settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investor-profile/tax-brackets")
async def get_tax_brackets(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Calculate applicable tax brackets for the investor"""
    try:
        service = InvestorProfileService(db)
        return await service.calculate_tax_brackets()
    except Exception as e:
        print(f"Error calculating tax brackets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investor-profile/calculate-capital-gains-tax")
async def calculate_capital_gains_tax(
    tax_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Calculate tax on capital gains using Tax API"""
    try:
        capital_gains = float(tax_data.get('capital_gains', 0))
        is_long_term = tax_data.get('is_long_term', False)
        
        if capital_gains <= 0:
            raise ValueError("Capital gains must be positive")
        
        # Get profile from unified user_profile table (Phase 3G)
        from app.services.tax_calculation_service import TaxCalculationService
        from app.models.user_profile import UserProfile
        
        profile_dict = await ProfileService.get_profile(db)
        result = await db.execute(select(UserProfile).where(UserProfile.id == 1))
        profile_model = result.scalar_one_or_none()
        annual_income = ProfileService.get_annual_household_income(profile_model) if profile_model else 300000.0
        
        tax_service = TaxCalculationService(db)
        
        # Use appropriate Tax API based on holding period
        if is_long_term:
            tax_result = await tax_service.calculate_long_term_capital_gains_tax(
                gains=capital_gains,
                base_income=annual_income,
                filing_status=profile_dict.get('filing_status', 'married_filing_jointly'),
                state=profile_dict.get('state', 'NY'),
                local_tax_rate=profile_dict.get('local_tax_rate', 0.01),
                year=2025
            )
        else:
            tax_result = await tax_service.calculate_short_term_capital_gains_tax(
                gains=capital_gains,
                base_income=annual_income,
                filing_status=profile_dict.get('filing_status', 'married_filing_jointly'),
                state=profile_dict.get('state', 'NY'),
                local_tax_rate=profile_dict.get('local_tax_rate', 0.01),
                year=2025
            )
        
        # Return in expected format
        return {
            "capital_gains": capital_gains,
            "is_long_term": is_long_term,
            "federal_tax": tax_result['federal_tax'],
            "state_tax": tax_result['state_tax'],
            "niit_tax": tax_result.get('niit_tax', 0),
            "local_tax": tax_result['local_tax'],
            "total_tax": tax_result['total_tax'],
            "effective_rate": tax_result['effective_rate'],
            "after_tax_gains": tax_result['after_tax_gains']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error calculating capital gains tax: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investor-profile/states")
async def get_state_list() -> List[Dict[str, str]]:
    """Get list of US states for dropdown"""
    try:
        # Static list - no DB needed
        states = [
            {'code': 'AL', 'name': 'Alabama'}, {'code': 'AK', 'name': 'Alaska'},
            {'code': 'AZ', 'name': 'Arizona'}, {'code': 'AR', 'name': 'Arkansas'},
            {'code': 'CA', 'name': 'California'}, {'code': 'CO', 'name': 'Colorado'},
            {'code': 'CT', 'name': 'Connecticut'}, {'code': 'DE', 'name': 'Delaware'},
            {'code': 'FL', 'name': 'Florida'}, {'code': 'GA', 'name': 'Georgia'},
            {'code': 'HI', 'name': 'Hawaii'}, {'code': 'ID', 'name': 'Idaho'},
            {'code': 'IL', 'name': 'Illinois'}, {'code': 'IN', 'name': 'Indiana'},
            {'code': 'IA', 'name': 'Iowa'}, {'code': 'KS', 'name': 'Kansas'},
            {'code': 'KY', 'name': 'Kentucky'}, {'code': 'LA', 'name': 'Louisiana'},
            {'code': 'ME', 'name': 'Maine'}, {'code': 'MD', 'name': 'Maryland'},
            {'code': 'MA', 'name': 'Massachusetts'}, {'code': 'MI', 'name': 'Michigan'},
            {'code': 'MN', 'name': 'Minnesota'}, {'code': 'MS', 'name': 'Mississippi'},
            {'code': 'MO', 'name': 'Missouri'}, {'code': 'MT', 'name': 'Montana'},
            {'code': 'NE', 'name': 'Nebraska'}, {'code': 'NV', 'name': 'Nevada'},
            {'code': 'NH', 'name': 'New Hampshire'}, {'code': 'NJ', 'name': 'New Jersey'},
            {'code': 'NM', 'name': 'New Mexico'}, {'code': 'NY', 'name': 'New York'},
            {'code': 'NC', 'name': 'North Carolina'}, {'code': 'ND', 'name': 'North Dakota'},
            {'code': 'OH', 'name': 'Ohio'}, {'code': 'OK', 'name': 'Oklahoma'},
            {'code': 'OR', 'name': 'Oregon'}, {'code': 'PA', 'name': 'Pennsylvania'},
            {'code': 'RI', 'name': 'Rhode Island'}, {'code': 'SC', 'name': 'South Carolina'},
            {'code': 'SD', 'name': 'South Dakota'}, {'code': 'TN', 'name': 'Tennessee'},
            {'code': 'TX', 'name': 'Texas'}, {'code': 'UT', 'name': 'Utah'},
            {'code': 'VT', 'name': 'Vermont'}, {'code': 'VA', 'name': 'Virginia'},
            {'code': 'WA', 'name': 'Washington'}, {'code': 'WV', 'name': 'West Virginia'},
            {'code': 'WI', 'name': 'Wisconsin'}, {'code': 'WY', 'name': 'Wyoming'}
        ]
        return states
    except Exception as e:
        print(f"Error getting state list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= MARKET PRICE REFRESH ENDPOINTS =============

@router.post("/market-prices/refresh")
async def refresh_market_prices(
    refresh_data: Dict[str, Any] = {},
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Start a background refresh of market prices from TwelveData API
    
    This endpoint returns immediately and the refresh continues in the background.
    Use GET /market-prices/refresh-status to check progress.
    
    Body:
        force: bool - Force refresh all symbols regardless of TTL
    """
    try:
        force = refresh_data.get('force', False) if refresh_data else False
        
        # Get database URL for background task
        db_url = get_async_db_url()
        
        # Start background refresh
        started, message = start_background_refresh(db_url, force=force)
        
        # Get current status
        status = get_refresh_status()
        
        return {
            "started": started,
            "message": message,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except ValueError as e:
        error_msg = str(e)
        if "run out of API credits" in error_msg or "429" in error_msg:
            return {
                "error": "API quota exhausted - automatic refresh disabled until tomorrow",
                "quota_exhausted": True,
                "started": False,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error starting market price refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-prices/refresh-status")
async def get_market_prices_refresh_status() -> Dict[str, Any]:
    """
    Get the current status of the background market price refresh
    
    Returns status including:
    - is_running: Whether refresh is in progress
    - total_symbols: Number of symbols to refresh
    - completed_symbols: Number of symbols already refreshed
    - minutes_remaining: Estimated time remaining
    - progress_percent: Completion percentage
    - status_message: Human-readable status message
    """
    status = get_refresh_status()
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/market-prices/config")
async def get_market_data_config(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get market data service configuration and status"""
    try:
        service = MarketDataService(db)
        return service.get_config_status()
    except Exception as e:
        print(f"Error getting market data config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market-prices/bulk-update")
async def bulk_update_market_prices(
    updates: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Bulk update multiple market prices at once
    
    Expects array of: [{"ticker": "AAPL", "current_price": 150.25}, ...]
    """
    try:
        from decimal import Decimal
        from datetime import datetime
        
        updated_count = 0
        updated_tickers = []
        now = datetime.now()
        
        for update in updates:
            ticker = update.get('ticker')
            price = update.get('current_price')
            
            if not ticker or price is None:
                continue
            
            # Update or insert the price
            await db.execute(text("""
                INSERT INTO market_prices (ticker_symbol, current_price, last_updated)
                VALUES (:ticker, :price, :updated)
                ON CONFLICT (ticker_symbol)
                DO UPDATE SET 
                    current_price = EXCLUDED.current_price,
                    last_updated = EXCLUDED.last_updated
            """), {
                'ticker': ticker.upper(),
                'price': Decimal(str(price)),
                'updated': now
            })
            
            updated_count += 1
            updated_tickers.append(ticker)
        
        await db.commit()
        
        return {
            "success": True,
            "updated_count": updated_count,
            "updated_tickers": updated_tickers,
            "message": f"Successfully updated {updated_count} prices"
        }
    except Exception as e:
        await db.rollback()
        print(f"Error bulk updating prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market-prices/reset-to-portfolio")
async def reset_market_prices_to_portfolio(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Clear all market prices and rebuild from current portfolio holdings.
    
    This removes stale tickers from sold positions and ensures we only
    track prices for stocks currently held across all portfolios.
    
    Process:
    1. Calculate currently held tickers (net buy - sell > 0)
    2. Delete ALL market_prices rows
    3. Insert $0.01 placeholders for held tickers
    4. Return count of cleared/created
    
    Note: Frontend should call /market-prices/refresh after this to get real prices
    """
    try:
        from app.services.transaction_service import TransactionService
        from decimal import Decimal
        
        # Get transaction service
        tx_service = TransactionService(db)
        
        # Step 1: Determine currently held tickers (net quantity > 0)
        tickers = await tx_service.get_currently_held_tickers()
        
        # Step 2: Clear all existing market prices
        result = await db.execute(text("SELECT COUNT(*) FROM market_prices"))
        existing_count = result.scalar_one()
        
        await db.execute(text("DELETE FROM market_prices"))
        await db.commit()
        
        # Step 3: Recreate placeholder entries for held tickers with $0.01
        created = 0
        from datetime import datetime
        now = datetime.now()
        
        for ticker in tickers:
            await db.execute(text("""
                INSERT INTO market_prices (ticker_symbol, current_price, last_updated)
                VALUES (:ticker, :price, :updated)
            """), {
                'ticker': ticker,
                'price': Decimal('0.01'),
                'updated': now
            })
            created += 1
        
        await db.commit()
        
        return {
            "success": True,
            "cleared": existing_count,
            "created": created,
            "tickers": tickers,
            "message": f"Cleared {existing_count} prices, created {created} placeholders for current holdings"
        }
    except Exception as e:
        print(f"Error resetting market prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))
