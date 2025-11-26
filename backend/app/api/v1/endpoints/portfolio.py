"""
Portfolio API endpoints for Capricorn
Clean implementation using Capricorn's database directly
No proxying to reference apps - fully self-contained
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime

from app.api import deps
from app.services.portfolio_service import PortfolioService
from app.models.portfolio_models import Portfolio, PortfolioTransaction, MarketPrice, InvestorProfile

router = APIRouter()

# ============= Request/Response Models =============

class PortfolioCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    cash_on_hand: float = 0.0
    investor_profile_id: Optional[int] = None

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    cash_on_hand: Optional[float] = None
    investor_profile_id: Optional[int] = None

class TransactionCreate(BaseModel):
    portfolio_id: int
    ticker_symbol: str
    stock_name: Optional[str] = None
    transaction_type: str
    quantity: float
    price_per_share: float
    transaction_date: str

class TransactionUpdate(BaseModel):
    ticker_symbol: Optional[str] = None
    stock_name: Optional[str] = None
    transaction_type: Optional[str] = None
    quantity: Optional[float] = None
    price_per_share: Optional[float] = None
    transaction_date: Optional[str] = None

class MarketPriceUpdate(BaseModel):
    ticker: str
    price: float

class InvestorProfileCreate(BaseModel):
    name: str
    annual_household_income: float
    filing_status: str
    state_of_residence: str
    local_tax_rate: float = 0.0

# ============= Health Check =============

@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "portfolio"}

# ============= Portfolio Endpoints =============

@router.get("/portfolios")
async def get_portfolios(
    db: AsyncSession = Depends(deps.get_async_db)
) -> List[Dict[str, Any]]:
    """Get all portfolios with their current values"""
    service = PortfolioService(db)
    portfolios = await service.get_all_portfolios()
    
    # Calculate values for each portfolio
    result = []
    for portfolio in portfolios:
        portfolio_value = await service.calculate_portfolio_value(portfolio.id)
        
        # Include basic portfolio info with calculated values
        result.append({
            "id": portfolio.id,
            "name": portfolio.name,
            "type": portfolio.type,
            "description": portfolio.description,
            "cash_on_hand": float(portfolio.cash_on_hand),
            "investor_profile_id": portfolio.investor_profile_id,
            "transaction_count": len(portfolio.transactions),
            **portfolio_value if portfolio_value else {
                "investment_value": 0.0,
                "total_market_value": float(portfolio.cash_on_hand),
                "total_cost_basis": 0.0,
                "total_gain_loss": 0.0,
                "total_gain_loss_percent": 0.0
            }
        })
    
    return result

@router.get("/portfolios/{portfolio_id}")
async def get_portfolio(
    portfolio_id: int,
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Get a specific portfolio with details"""
    service = PortfolioService(db)
    portfolio = await service.get_portfolio_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get calculated values
    portfolio_value = await service.calculate_portfolio_value(portfolio_id)
    holdings = await service.calculate_holdings(portfolio_id)
    
    # Get transactions
    transactions = []
    for t in portfolio.transactions:
        transactions.append({
            "id": t.id,
            "ticker_symbol": t.ticker_symbol,
            "stock_name": t.stock_name,
            "transaction_type": t.transaction_type,
            "quantity": float(t.quantity),
            "price_per_share": float(t.price_per_share),
            "transaction_date": t.transaction_date.isoformat(),
            "total_value": float(t.quantity * t.price_per_share)
        })
    
    # Format holdings with market data
    formatted_holdings = {}
    for ticker, data in holdings.items():
        market_price = await service.get_market_price(ticker)
        if market_price:
            current_value = data['shares'] * market_price.current_price
            gain_loss = current_value - data['cost_basis']
            formatted_holdings[ticker] = {
                "shares": float(data['shares']),
                "cost_basis": float(data['cost_basis']),
                "current_price": float(market_price.current_price),
                "current_value": float(current_value),
                "gain_loss": float(gain_loss),
                "gain_loss_percent": float((gain_loss / data['cost_basis'] * 100) if data['cost_basis'] > 0 else 0)
            }
    
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "type": portfolio.type,
        "description": portfolio.description,
        "cash_on_hand": float(portfolio.cash_on_hand),
        "investor_profile_id": portfolio.investor_profile_id,
        "transactions": transactions,
        "holdings": formatted_holdings,
        **portfolio_value if portfolio_value else {}
    }

@router.post("/portfolios")
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Create a new portfolio"""
    service = PortfolioService(db)
    new_portfolio = await service.create_portfolio(
        name=portfolio_data.name,
        type=portfolio_data.type,
        description=portfolio_data.description,
        cash_on_hand=portfolio_data.cash_on_hand,
        investor_profile_id=portfolio_data.investor_profile_id
    )
    
    return {
        "id": new_portfolio.id,
        "name": new_portfolio.name,
        "type": new_portfolio.type,
        "description": new_portfolio.description,
        "cash_on_hand": float(new_portfolio.cash_on_hand),
        "investor_profile_id": new_portfolio.investor_profile_id
    }

@router.put("/portfolios/{portfolio_id}")
async def update_portfolio(
    portfolio_id: int,
    portfolio: PortfolioUpdate,
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Update portfolio details"""
    service = PortfolioService(db)
    
    # Filter out None values
    update_data = {k: v for k, v in portfolio.dict().items() if v is not None}
    
    updated_portfolio = await service.update_portfolio(portfolio_id, **update_data)
    if not updated_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "id": updated_portfolio.id,
        "name": updated_portfolio.name,
        "type": updated_portfolio.type,
        "description": updated_portfolio.description,
        "cash_on_hand": float(updated_portfolio.cash_on_hand),
        "investor_profile_id": updated_portfolio.investor_profile_id
    }

@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    db: AsyncSession = Depends(deps.get_async_db)
):
    """Delete a portfolio"""
    service = PortfolioService(db)
    success = await service.delete_portfolio(portfolio_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {"message": "Portfolio deleted successfully"}

# ============= Transaction Endpoints =============

@router.get("/transactions")
async def get_transactions(
    portfolio_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(deps.get_async_db)
) -> List[Dict[str, Any]]:
    """Get transactions, optionally filtered by portfolio"""
    service = PortfolioService(db)
    
    if portfolio_id:
        transactions = await service.get_portfolio_transactions(portfolio_id)
    else:
        # Get all transactions from all portfolios
        portfolios = await service.get_all_portfolios()
        transactions = []
        for portfolio in portfolios:
            transactions.extend(portfolio.transactions)
    
    result = []
    for t in transactions:
        result.append({
            "id": t.id,
            "portfolio_id": t.portfolio_id,
            "ticker_symbol": t.ticker_symbol,
            "stock_name": t.stock_name,
            "transaction_type": t.transaction_type,
            "quantity": float(t.quantity),
            "price_per_share": float(t.price_per_share),
            "transaction_date": t.transaction_date.isoformat(),
            "total_value": float(t.quantity * t.price_per_share)
        })
    
    return result

@router.get("/transactions/{transaction_id}")
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Get a specific transaction"""
    service = PortfolioService(db)
    transaction = await service.get_transaction_by_id(transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "id": transaction.id,
        "portfolio_id": transaction.portfolio_id,
        "ticker_symbol": transaction.ticker_symbol,
        "stock_name": transaction.stock_name,
        "transaction_type": transaction.transaction_type,
        "quantity": float(transaction.quantity),
        "price_per_share": float(transaction.price_per_share),
        "transaction_date": transaction.transaction_date.isoformat(),
        "total_value": float(transaction.quantity * transaction.price_per_share)
    }

@router.post("/transactions")
async def create_transaction(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Create a new transaction"""
    service = PortfolioService(db)
    
    # Verify portfolio exists
    portfolio = await service.get_portfolio_by_id(transaction.portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    new_transaction = await service.create_transaction(
        portfolio_id=transaction.portfolio_id,
        ticker_symbol=transaction.ticker_symbol,
        stock_name=transaction.stock_name,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        price_per_share=transaction.price_per_share,
        transaction_date=transaction.transaction_date
    )
    
    return {
        "id": new_transaction.id,
        "portfolio_id": new_transaction.portfolio_id,
        "ticker_symbol": new_transaction.ticker_symbol,
        "stock_name": new_transaction.stock_name,
        "transaction_type": new_transaction.transaction_type,
        "quantity": float(new_transaction.quantity),
        "price_per_share": float(new_transaction.price_per_share),
        "transaction_date": new_transaction.transaction_date.isoformat(),
        "total_value": float(new_transaction.quantity * new_transaction.price_per_share)
    }

@router.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Update a transaction"""
    service = PortfolioService(db)
    
    # Filter out None values
    update_data = {k: v for k, v in transaction.dict().items() if v is not None}
    
    updated_transaction = await service.update_transaction(transaction_id, **update_data)
    if not updated_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "id": updated_transaction.id,
        "portfolio_id": updated_transaction.portfolio_id,
        "ticker_symbol": updated_transaction.ticker_symbol,
        "stock_name": updated_transaction.stock_name,
        "transaction_type": updated_transaction.transaction_type,
        "quantity": float(updated_transaction.quantity),
        "price_per_share": float(updated_transaction.price_per_share),
        "transaction_date": updated_transaction.transaction_date.isoformat(),
        "total_value": float(updated_transaction.quantity * updated_transaction.price_per_share)
    }

@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(deps.get_async_db)
):
    """Delete a transaction"""
    service = PortfolioService(db)
    success = await service.delete_transaction(transaction_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"message": "Transaction deleted successfully"}

# ============= Market Price Endpoints =============

@router.get("/market-prices")
async def get_market_prices(
    db: AsyncSession = Depends(deps.get_async_db)
) -> List[Dict[str, Any]]:
    """Get all market prices"""
    service = PortfolioService(db)
    prices = await service.get_all_market_prices()
    
    result = []
    for price in prices:
        result.append({
            "ticker_symbol": price.ticker_symbol,
            "current_price": float(price.current_price),
            "last_updated": price.last_updated.isoformat() if price.last_updated else None
        })
    
    return result

@router.get("/market-prices/{ticker}")
async def get_market_price(
    ticker: str,
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Get market price for a specific ticker"""
    service = PortfolioService(db)
    price = await service.get_market_price(ticker)
    
    if not price:
        raise HTTPException(status_code=404, detail="Market price not found")
    
    return {
        "ticker_symbol": price.ticker_symbol,
        "current_price": float(price.current_price),
        "last_updated": price.last_updated.isoformat() if price.last_updated else None
    }

@router.post("/market-prices")
async def update_market_prices(
    prices: List[MarketPriceUpdate],
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Update multiple market prices"""
    service = PortfolioService(db)
    updated = []
    
    for price_update in prices:
        price = await service.update_market_price(price_update.ticker, price_update.price)
        updated.append({
            "ticker_symbol": price.ticker_symbol,
            "current_price": float(price.current_price)
        })
    
    return {"updated": updated, "count": len(updated)}

# ============= Summary Endpoints =============

@router.get("/summary")
async def get_portfolio_summary(
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Get summary of all portfolios"""
    service = PortfolioService(db)
    summary = await service.calculate_portfolio_summary()
    return summary

@router.get("/market-value")
async def get_market_value(
    portfolio_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Get market value calculations"""
    service = PortfolioService(db)
    
    if portfolio_id:
        # Single portfolio value
        value = await service.calculate_portfolio_value(portfolio_id)
        if not value:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return value
    else:
        # All portfolios summary
        return await service.calculate_portfolio_summary()

@router.get("/break-even")
async def calculate_break_even(
    portfolio_id: int = Query(...),
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Calculate tax-aware break-even analysis"""
    service = PortfolioService(db)
    
    # Get portfolio and holdings
    portfolio = await service.get_portfolio_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    holdings = await service.calculate_holdings(portfolio_id)
    
    # Calculate break-even for each holding
    # This is a simplified version - the full implementation would use tax tables
    result = []
    for ticker, data in holdings.items():
        market_price = await service.get_market_price(ticker)
        if market_price:
            current_value = data['shares'] * market_price.current_price
            gain_loss = current_value - data['cost_basis']
            
            # Simplified tax calculation (25% rate)
            estimated_tax = gain_loss * Decimal('0.25') if gain_loss > 0 else Decimal('0')
            after_tax_gain = gain_loss - estimated_tax
            
            result.append({
                "ticker": ticker,
                "shares": float(data['shares']),
                "cost_basis": float(data['cost_basis']),
                "current_value": float(current_value),
                "gain_loss": float(gain_loss),
                "estimated_tax": float(estimated_tax),
                "after_tax_gain": float(after_tax_gain),
                "recommendation": "HOLD" if after_tax_gain > 0 else "MONITOR"
            })
    
    return {
        "portfolio_id": portfolio_id,
        "portfolio_name": portfolio.name,
        "holdings": result
    }

# ============= Investor Profile Endpoints =============

@router.get("/investor-profiles")
async def get_investor_profiles(
    db: AsyncSession = Depends(deps.get_async_db)
) -> List[Dict[str, Any]]:
    """Get all investor profiles"""
    service = PortfolioService(db)
    profiles = await service.get_investor_profiles()
    
    result = []
    for profile in profiles:
        result.append({
            "id": profile.id,
            "name": profile.name,
            "annual_household_income": float(profile.annual_household_income),
            "filing_status": profile.filing_status,
            "state_of_residence": profile.state_of_residence,
            "local_tax_rate": float(profile.local_tax_rate),
            "portfolio_count": len(profile.portfolios)
        })
    
    return result

@router.post("/investor-profiles")
async def create_investor_profile(
    profile: InvestorProfileCreate,
    db: AsyncSession = Depends(deps.get_async_db)
) -> Dict[str, Any]:
    """Create a new investor profile"""
    service = PortfolioService(db)
    new_profile = await service.create_investor_profile(
        name=profile.name,
        annual_household_income=profile.annual_household_income,
        filing_status=profile.filing_status,
        state_of_residence=profile.state_of_residence,
        local_tax_rate=profile.local_tax_rate
    )
    
    return {
        "id": new_profile.id,
        "name": new_profile.name,
        "annual_household_income": float(new_profile.annual_household_income),
        "filing_status": new_profile.filing_status,
        "state_of_residence": new_profile.state_of_residence,
        "local_tax_rate": float(new_profile.local_tax_rate)
    }