"""
Profile API Endpoints
Single source of truth for user profile data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.services.profile_service import ProfileService
from pydantic import BaseModel
from typing import Dict, Any, Optional
from decimal import Decimal

router = APIRouter(prefix="/profile", tags=["profile"])


# Request/Response Models
class ProfileUpdateRequest(BaseModel):
    """Request model for profile updates"""
    # Section 1: Personal
    user: Optional[str] = None
    partner: Optional[str] = None
    user_age: Optional[int] = None
    partner_age: Optional[int] = None
    years_of_retirement: Optional[int] = None
    user_years_to_retirement: Optional[int] = None
    partner_years_to_retirement: Optional[int] = None
    
    # Section 2: Income
    user_salary: Optional[float] = None
    user_bonus_rate: Optional[float] = None
    user_raise_rate: Optional[float] = None
    partner_salary: Optional[float] = None
    partner_bonus_rate: Optional[float] = None
    partner_raise_rate: Optional[float] = None
    
    # Section 3: Expenses
    monthly_living_expenses: Optional[float] = None
    annual_discretionary_spending: Optional[float] = None
    annual_inflation_rate: Optional[float] = None
    
    # Section 4: 401K
    user_401k_contribution: Optional[float] = None
    partner_401k_contribution: Optional[float] = None
    user_employer_match: Optional[float] = None
    partner_employer_match: Optional[float] = None
    user_current_401k_balance: Optional[float] = None
    partner_current_401k_balance: Optional[float] = None
    user_401k_growth_rate: Optional[float] = None
    partner_401k_growth_rate: Optional[float] = None
    
    # Section 5: Investments
    current_ira_balance: Optional[float] = None
    ira_return_rate: Optional[float] = None
    current_trading_balance: Optional[float] = None
    trading_return_rate: Optional[float] = None
    current_savings_balance: Optional[float] = None
    savings_return_rate: Optional[float] = None
    expected_inheritance: Optional[float] = None
    inheritance_year: Optional[int] = None
    
    # Section 6: Tax
    state: Optional[str] = None
    local_tax_rate: Optional[float] = None
    filing_status: Optional[str] = None
    
    # Section 7: Retirement
    retirement_growth_rate: Optional[float] = None
    withdrawal_rate: Optional[float] = None
    
    # Section 8: Savings
    fixed_monthly_savings: Optional[float] = None
    percentage_of_leftover: Optional[float] = None
    savings_destination: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": "Andrew",
                "partner": "Jackie",
                "user_age": 46,
                "partner_age": 36,
                "user_salary": 205000,
                "partner_salary": 150000,
                "state": "NY",
                "filing_status": "married_filing_jointly"
            }
        }


@router.get("")
async def get_profile(db: AsyncSession = Depends(get_async_db)):
    """
    Get user profile (single-user system, id=1)
    Auto-creates with defaults if doesn't exist
    """
    try:
        profile = await ProfileService.get_profile(db)
        return {
            "success": True,
            "profile": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("")
async def update_profile(
    data: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update user profile
    Only updates fields that are provided (partial updates)
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = {
            k: v for k, v in data.model_dump().items() 
            if v is not None
        }
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")
        
        profile = await ProfileService.update_profile(db, update_data)
        return {
            "success": True,
            "message": f"Profile updated ({len(update_data)} fields)",
            "profile": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{section}")
async def update_profile_section(
    section: str,
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a specific section of the profile
    Sections: personal, income, expenses, 401k, investments, tax, retirement, savings
    """
    try:
        profile = await ProfileService.update_section(db, section, data)
        return {
            "success": True,
            "message": f"Section '{section}' updated",
            "profile": profile
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sections")
async def get_profile_sections():
    """
    Get available profile sections for reference
    """
    return {
        "success": True,
        "sections": {
            "personal": ["user", "partner", "ages", "retirement timelines"],
            "income": ["salaries", "bonuses", "raise rates"],
            "expenses": ["living expenses", "discretionary", "inflation"],
            "401k": ["contributions", "matches", "balances", "growth rates"],
            "investments": ["IRA", "trading", "savings", "inheritance"],
            "tax": ["state", "local rate", "filing status"],
            "retirement": ["growth rate", "withdrawal rate"],
            "savings": ["fixed monthly", "percentage", "destination"]
        }
    }

