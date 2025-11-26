"""
Retirement API Endpoints
Provides retirement calculation services
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.services.retirement_calculator import RetirementCalculator
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/retirement", tags=["retirement"])


@router.get("/summary")
async def get_retirement_summary(db: AsyncSession = Depends(get_async_db)):
    """
    Get complete retirement calculation summary
    Includes: projections, asset growth, retirement analysis, transition analysis
    """
    try:
        # Get profile from user_profile table
        profile = await ProfileService.get_profile(db)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Calculate all retirement data
        calculator = RetirementCalculator(db)
        results = await calculator.calculate_all(profile)
        
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projections")
async def get_yearly_projections(db: AsyncSession = Depends(get_async_db)):
    """
    Get 30-year financial projections
    Returns year-by-year breakdown of income, expenses, taxes, savings
    """
    try:
        profile = await ProfileService.get_profile(db)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        calculator = RetirementCalculator(db)
        
        # Calculate retirement years
        user_retirement_year = 2025 + profile.get('user_years_to_retirement', 25)
        partner_retirement_year = 2025 + profile.get('partner_years_to_retirement', 30)
        total_years = max(
            profile.get('user_years_to_retirement', 25),
            profile.get('partner_years_to_retirement', 30),
            30
        )
        
        projections = await calculator.calculate_yearly_projections(
            profile, user_retirement_year, partner_retirement_year, total_years
        )
        
        return {
            "success": True,
            "projections": projections,
            "metadata": {
                "total_years": total_years,
                "user_retirement_year": user_retirement_year,
                "partner_retirement_year": partner_retirement_year,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets")
async def get_asset_growth(db: AsyncSession = Depends(get_async_db)):
    """
    Get asset growth projections
    Returns asset balances over time for all accounts
    """
    try:
        profile = await ProfileService.get_profile(db)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        calculator = RetirementCalculator(db)
        
        # Need projections first to calculate assets
        user_retirement_year = 2025 + profile.get('user_years_to_retirement', 25)
        partner_retirement_year = 2025 + profile.get('partner_years_to_retirement', 30)
        total_years = max(
            profile.get('user_years_to_retirement', 25),
            profile.get('partner_years_to_retirement', 30),
            30
        )
        
        projections = await calculator.calculate_yearly_projections(
            profile, user_retirement_year, partner_retirement_year, total_years
        )
        
        assets = await calculator.calculate_asset_growth(
            profile, projections, user_retirement_year, partner_retirement_year
        )
        
        return {
            "success": True,
            "asset_growth": assets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis")
async def get_retirement_analysis(db: AsyncSession = Depends(get_async_db)):
    """
    Get retirement sustainability analysis
    Returns withdrawal calculations and lifestyle metrics
    """
    try:
        profile = await ProfileService.get_profile(db)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        calculator = RetirementCalculator(db)
        
        # Calculate full model to get final assets
        results = await calculator.calculate_all(profile)
        
        return {
            "success": True,
            "analysis": results['retirement_analysis']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transition")
async def get_transition_analysis(db: AsyncSession = Depends(get_async_db)):
    """
    Get transition period analysis
    Analyzes the period when one partner retires before the other
    """
    try:
        profile = await ProfileService.get_profile(db)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        calculator = RetirementCalculator(db)
        
        # Calculate full model to get transition data
        results = await calculator.calculate_all(profile)
        
        return {
            "success": True,
            "transition": results['transition_analysis']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

