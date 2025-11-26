"""
Tax Calculation API Endpoints
Provides centralized tax calculation services for the entire application
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from datetime import date
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.services.tax_calculation_service import TaxCalculationService

router = APIRouter(prefix="/tax", tags=["tax"])


class IncomeTaxRequest(BaseModel):
    """Request model for income tax calculation"""
    income: float = Field(..., gt=0, description="Gross income")
    filing_status: str = Field(..., description="Filing status: single, married_filing_jointly, etc.")
    state: str = Field(..., description="Two-letter state code (e.g., NY)")
    local_tax_rate: float = Field(default=0.0, ge=0, le=0.2, description="Local tax rate as decimal")
    year: int = Field(default=2025, description="Tax year")


class CapitalGainsRequest(BaseModel):
    """Request model for capital gains tax calculation"""
    gains: float = Field(..., description="Capital gains amount")
    base_income: float = Field(..., ge=0, description="Income before gains")
    filing_status: str = Field(..., description="Filing status")
    state: str = Field(..., description="Two-letter state code")
    local_tax_rate: float = Field(default=0.0, ge=0, le=0.2, description="Local tax rate")
    purchase_date: Optional[date] = Field(None, description="Date asset was purchased")
    sale_date: Optional[date] = Field(None, description="Date asset was sold")
    year: int = Field(default=2025, description="Tax year")


@router.post("/income")
async def calculate_income_tax(
    request: IncomeTaxRequest,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Calculate total tax on ordinary income
    
    Returns comprehensive breakdown of federal, state, and local taxes
    """
    service = TaxCalculationService(db)
    
    try:
        result = await service.calculate_income_tax(
            income=request.income,
            filing_status=request.filing_status,
            state=request.state,
            local_tax_rate=request.local_tax_rate,
            year=request.year
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capital-gains/short-term")
async def calculate_short_term_capital_gains(
    request: CapitalGainsRequest,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Calculate tax on short-term capital gains (held ≤365 days)
    
    Short-term gains are taxed as ordinary income at marginal rates
    """
    service = TaxCalculationService(db)
    
    # Validate holding period if dates provided
    if request.purchase_date and request.sale_date:
        holding_days = (request.sale_date - request.purchase_date).days
        if holding_days > 365:
            raise HTTPException(
                status_code=400,
                detail=f"Holding period of {holding_days} days exceeds 365 days. Use long-term endpoint."
            )
    
    try:
        result = await service.calculate_short_term_capital_gains_tax(
            gains=request.gains,
            base_income=request.base_income,
            filing_status=request.filing_status,
            state=request.state,
            local_tax_rate=request.local_tax_rate,
            purchase_date=request.purchase_date,
            sale_date=request.sale_date,
            year=request.year
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capital-gains/long-term")
async def calculate_long_term_capital_gains(
    request: CapitalGainsRequest,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Calculate tax on long-term capital gains (held >365 days)
    
    Long-term gains receive preferential tax rates (0%, 15%, or 20%)
    """
    service = TaxCalculationService(db)
    
    # Validate holding period if dates provided
    if request.purchase_date and request.sale_date:
        holding_days = (request.sale_date - request.purchase_date).days
        if holding_days <= 365:
            raise HTTPException(
                status_code=400,
                detail=f"Holding period of {holding_days} days is 365 days or less. Use short-term endpoint."
            )
    
    try:
        result = await service.calculate_long_term_capital_gains_tax(
            gains=request.gains,
            base_income=request.base_income,
            filing_status=request.filing_status,
            state=request.state,
            local_tax_rate=request.local_tax_rate,
            purchase_date=request.purchase_date,
            sale_date=request.sale_date,
            year=request.year
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TaxBreakdownRequest(BaseModel):
    """Request model for generic tax breakdown"""
    scenario_type: str = Field(..., description="Type: income, short_term_gains, long_term_gains")
    income: Optional[float] = None
    gains: Optional[float] = None
    base_income: Optional[float] = None
    filing_status: str
    state: str
    local_tax_rate: float = 0.0
    purchase_date: Optional[date] = None
    sale_date: Optional[date] = None
    year: int = 2025


@router.post("/breakdown")
async def get_tax_breakdown(
    request: TaxBreakdownRequest,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get detailed tax breakdown for any scenario
    
    Flexible endpoint that can calculate taxes for various scenarios
    """
    service = TaxCalculationService(db)
    
    # Build kwargs based on scenario type
    kwargs = {
        "filing_status": request.filing_status,
        "state": request.state,
        "local_tax_rate": request.local_tax_rate,
        "year": request.year
    }
    
    if request.scenario_type == "income":
        if not request.income:
            raise HTTPException(status_code=400, detail="Income required for income scenario")
        kwargs["income"] = request.income
    elif request.scenario_type in ["short_term_gains", "long_term_gains"]:
        if not request.gains or request.base_income is None:
            raise HTTPException(status_code=400, detail="Gains and base_income required for capital gains scenario")
        kwargs["gains"] = request.gains
        kwargs["base_income"] = request.base_income
        kwargs["purchase_date"] = request.purchase_date
        kwargs["sale_date"] = request.sale_date
    
    try:
        result = await service.get_tax_breakdown(
            scenario_type=request.scenario_type,
            **kwargs
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_tax_api(db: AsyncSession = Depends(get_async_db)) -> Dict[str, Any]:
    """
    Test endpoint to verify tax API is working
    
    Tests with sample data: $300K income, married filing jointly, NY resident
    """
    service = TaxCalculationService(db)
    
    # Test income tax
    income_result = await service.calculate_income_tax(
        income=300000,
        filing_status="married_filing_jointly",
        state="NY",
        local_tax_rate=0.01,
        year=2025
    )
    
    # Test short-term gains
    short_term_result = await service.calculate_short_term_capital_gains_tax(
        gains=17500,
        base_income=300000,
        filing_status="married_filing_jointly",
        state="NY",
        local_tax_rate=0.01,
        year=2025
    )
    
    # Test long-term gains
    long_term_result = await service.calculate_long_term_capital_gains_tax(
        gains=17500,
        base_income=300000,
        filing_status="married_filing_jointly",
        state="NY",
        local_tax_rate=0.01,
        year=2025
    )
    
    return {
        "status": "Tax API is working",
        "test_results": {
            "income_tax": {
                "total_tax": income_result["total_tax"],
                "effective_rate": income_result["effective_rate"]
            },
            "short_term_gains": {
                "total_tax": short_term_result["total_tax"],
                "effective_rate": short_term_result["effective_rate"]
            },
            "long_term_gains": {
                "total_tax": long_term_result["total_tax"],
                "effective_rate": long_term_result["effective_rate"]
            }
        }
    }
