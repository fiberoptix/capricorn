"""
Portfolio Service for Capricorn
Simple async service that handles portfolio operations in Capricorn's database
This is a clean implementation, not copying from reference app
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload

from app.models.portfolio_models import (
    Portfolio, 
    PortfolioTransaction, 
    MarketPrice, 
    InvestorProfile,
    TaxRate,
    StateTaxRate
)
from app.core.constants import SINGLE_USER_ID


class PortfolioService:
    """Service for portfolio-related operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============= Portfolio CRUD =============
    
    async def get_all_portfolios(self) -> List[Portfolio]:
        """Get all portfolios with their transactions"""
        result = await self.db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.transactions))
            .options(selectinload(Portfolio.investor_profile))
            .order_by(Portfolio.id)
        )
        return result.scalars().all()
    
    async def get_portfolio_by_id(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get a specific portfolio by ID"""
        result = await self.db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.transactions))
            .options(selectinload(Portfolio.investor_profile))
            .where(Portfolio.id == portfolio_id)
        )
        return result.scalar_one_or_none()
    
    async def create_portfolio(
        self, 
        name: str, 
        type: str, 
        description: str = None,
        cash_on_hand: float = 0.0,
        investor_profile_id: int = None
    ) -> Portfolio:
        """Create a new portfolio"""
        portfolio = Portfolio(
            name=name,
            type=type,
            description=description,
            cash_on_hand=Decimal(str(cash_on_hand)),
            investor_profile_id=investor_profile_id
        )
        self.db.add(portfolio)
        await self.db.commit()
        await self.db.refresh(portfolio)
        return portfolio
    
    async def update_portfolio(
        self, 
        portfolio_id: int,
        **kwargs
    ) -> Optional[Portfolio]:
        """Update portfolio details"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return None
        
        for key, value in kwargs.items():
            if hasattr(portfolio, key):
                # Convert float to Decimal for cash_on_hand
                if key == 'cash_on_hand' and value is not None:
                    value = Decimal(str(value))
                setattr(portfolio, key, value)
        
        await self.db.commit()
        await self.db.refresh(portfolio)
        return portfolio
    
    async def delete_portfolio(self, portfolio_id: int) -> bool:
        """Delete a portfolio and all its transactions"""
        result = await self.db.execute(
            delete(Portfolio).where(Portfolio.id == portfolio_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    # ============= Portfolio Calculations =============
    
    async def calculate_portfolio_value(self, portfolio_id: int) -> Dict[str, Any]:
        """Calculate the current market value of a portfolio"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return None
        
        # Get current holdings (aggregate buy/sell transactions)
        holdings = await self.calculate_holdings(portfolio_id)
        
        # Calculate total values
        securities_value = Decimal('0')
        total_cost_basis = Decimal('0')
        unrealized_gains = Decimal('0')
        
        for ticker, data in holdings.items():
            if data['shares'] > 0:
                # Always add to total cost basis
                total_cost_basis += data['cost_basis']
                
                # Get current market price
                market_price = await self.get_market_price(ticker)
                if market_price:
                    # Use market price if available
                    current_value = data['shares'] * market_price.current_price
                    securities_value += current_value
                    unrealized_gains += (current_value - data['cost_basis'])
                else:
                    # If no market price, use cost basis as value
                    securities_value += data['cost_basis']
                    # No unrealized gains when using cost basis
        
        total_value = securities_value + portfolio.cash_on_hand
        
        return {
            'portfolio_id': portfolio_id,
            'investment_value': float(securities_value),
            'cash_on_hand': float(portfolio.cash_on_hand),
            'total_market_value': float(total_value),
            'total_cost_basis': float(total_cost_basis),
            'total_gain_loss': float(unrealized_gains),
            'total_gain_loss_percent': float(
                (unrealized_gains / total_cost_basis * 100) if total_cost_basis > 0 else 0
            )
        }
    
    async def calculate_holdings(self, portfolio_id: int) -> Dict[str, Any]:
        """Calculate current holdings from transactions"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return {}
        
        holdings = {}
        
        # Process all transactions to calculate current holdings
        for transaction in portfolio.transactions:
            ticker = transaction.ticker_symbol
            if ticker not in holdings:
                holdings[ticker] = {
                    'shares': Decimal('0'),
                    'cost_basis': Decimal('0')
                }
            
            if transaction.transaction_type == 'buy':
                holdings[ticker]['shares'] += transaction.quantity
                holdings[ticker]['cost_basis'] += (transaction.quantity * transaction.price_per_share)
            elif transaction.transaction_type == 'sell':
                # Reduce shares and adjust cost basis proportionally
                if holdings[ticker]['shares'] > 0:
                    ratio = transaction.quantity / holdings[ticker]['shares']
                    holdings[ticker]['shares'] -= transaction.quantity
                    holdings[ticker]['cost_basis'] -= (holdings[ticker]['cost_basis'] * ratio)
        
        # Remove tickers with 0 shares
        return {k: v for k, v in holdings.items() if v['shares'] > 0}
    
    async def calculate_portfolio_summary(self) -> Dict[str, Any]:
        """Calculate summary across all portfolios"""
        portfolios = await self.get_all_portfolios()
        
        total_value = Decimal('0')
        securities_value = Decimal('0')
        cash_on_hand = Decimal('0')
        unrealized_gains = Decimal('0')
        
        for portfolio in portfolios:
            portfolio_value = await self.calculate_portfolio_value(portfolio.id)
            if portfolio_value:
                total_value += Decimal(str(portfolio_value['total_market_value']))
                securities_value += Decimal(str(portfolio_value['investment_value']))
                cash_on_hand += Decimal(str(portfolio_value['cash_on_hand']))
                unrealized_gains += Decimal(str(portfolio_value['total_gain_loss']))
        
        # Calculate tax liability using Tax API
        from app.services.tax_calculation_service import TaxCalculationService
        from app.services.investor_profile_service import InvestorProfileService
        
        tax_service = TaxCalculationService(self.db)
        investor_service = InvestorProfileService(self.db)
        
        tax_liability = Decimal('0')
        if unrealized_gains > 0:
            try:
                investor_profile = await investor_service.get_or_create_profile()
                
                # Use short-term calculation for conservative estimate
                tax_result = await tax_service.calculate_short_term_capital_gains_tax(
                    gains=float(unrealized_gains),
                    base_income=float(investor_profile.annual_household_income),
                    filing_status=investor_profile.filing_status,
                    state=investor_profile.state_of_residence,
                    local_tax_rate=float(investor_profile.local_tax_rate),
                    year=2025
                )
                tax_liability = Decimal(str(tax_result['total_tax']))
            except Exception as e:
                print(f"Warning: Could not calculate tax via Tax API: {e}")
                # Fallback to conservative estimate
                tax_liability = unrealized_gains * Decimal('0.35')
        
        return {
            'total_value': float(total_value),
            'securities_value': float(securities_value),
            'cash_on_hand': float(cash_on_hand),
            'unrealized_gains': float(unrealized_gains),
            'tax_liability': float(tax_liability),
            'after_tax_value': float(total_value - tax_liability),
            'portfolio_count': len(portfolios)
        }
    
    # ============= Transaction Methods =============
    
    async def get_portfolio_transactions(self, portfolio_id: int) -> List[PortfolioTransaction]:
        """Get all transactions for a portfolio"""
        result = await self.db.execute(
            select(PortfolioTransaction)
            .where(PortfolioTransaction.portfolio_id == portfolio_id)
            .order_by(PortfolioTransaction.transaction_date.desc())
        )
        return result.scalars().all()
    
    async def get_transaction_by_id(self, transaction_id: int) -> Optional[PortfolioTransaction]:
        """Get a specific transaction"""
        result = await self.db.execute(
            select(PortfolioTransaction)
            .where(PortfolioTransaction.id == transaction_id)
        )
        return result.scalar_one_or_none()
    
    async def create_transaction(
        self,
        portfolio_id: int,
        ticker_symbol: str,
        stock_name: str,
        transaction_type: str,
        quantity: float,
        price_per_share: float,
        transaction_date: str
    ) -> PortfolioTransaction:
        """Create a new transaction"""
        # Parse date if string
        if isinstance(transaction_date, str):
            transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()
        
        transaction = PortfolioTransaction(
            portfolio_id=portfolio_id,
            ticker_symbol=ticker_symbol.upper(),
            stock_name=stock_name or ticker_symbol.upper(),
            transaction_type=transaction_type.lower(),
            quantity=Decimal(str(quantity)),
            price_per_share=Decimal(str(price_per_share)),
            transaction_date=transaction_date
        )
        
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction
    
    async def update_transaction(self, transaction_id: int, **kwargs) -> Optional[PortfolioTransaction]:
        """Update a transaction"""
        transaction = await self.get_transaction_by_id(transaction_id)
        if not transaction:
            return None
        
        for key, value in kwargs.items():
            if hasattr(transaction, key):
                # Convert numeric fields to Decimal
                if key in ['quantity', 'price_per_share'] and value is not None:
                    value = Decimal(str(value))
                # Parse date if string
                if key == 'transaction_date' and isinstance(value, str):
                    value = datetime.strptime(value, '%Y-%m-%d').date()
                setattr(transaction, key, value)
        
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction
    
    async def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction"""
        result = await self.db.execute(
            delete(PortfolioTransaction)
            .where(PortfolioTransaction.id == transaction_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    # ============= Market Price Methods =============
    
    async def get_market_price(self, ticker: str) -> Optional[MarketPrice]:
        """Get current market price for a ticker"""
        result = await self.db.execute(
            select(MarketPrice)
            .where(MarketPrice.ticker_symbol == ticker.upper())
        )
        return result.scalar_one_or_none()
    
    async def get_all_market_prices(self) -> List[MarketPrice]:
        """Get all market prices"""
        result = await self.db.execute(
            select(MarketPrice).order_by(MarketPrice.ticker_symbol)
        )
        return result.scalars().all()
    
    async def update_market_price(self, ticker: str, price: float) -> MarketPrice:
        """Update or create market price"""
        market_price = await self.get_market_price(ticker)
        
        if market_price:
            market_price.current_price = Decimal(str(price))
            market_price.last_updated = datetime.now()
        else:
            market_price = MarketPrice(
                ticker_symbol=ticker.upper(),
                current_price=Decimal(str(price)),
                last_updated=datetime.now()
            )
            self.db.add(market_price)
        
        await self.db.commit()
        await self.db.refresh(market_price)
        return market_price
    
    # ============= Investor Profile Methods =============
    
    async def get_investor_profiles(self) -> List[InvestorProfile]:
        """Get all investor profiles"""
        result = await self.db.execute(
            select(InvestorProfile)
            .options(selectinload(InvestorProfile.portfolios))
        )
        return result.scalars().all()
    
    async def get_investor_profile(self, profile_id: int) -> Optional[InvestorProfile]:
        """Get investor profile by ID"""
        result = await self.db.execute(
            select(InvestorProfile)
            .where(InvestorProfile.id == profile_id)
        )
        return result.scalar_one_or_none()
    
    async def create_investor_profile(
        self,
        name: str,
        annual_household_income: float,
        filing_status: str,
        state_of_residence: str,
        local_tax_rate: float = 0.0
    ) -> InvestorProfile:
        """Create new investor profile"""
        profile = InvestorProfile(
            name=name,
            annual_household_income=Decimal(str(annual_household_income)),
            filing_status=filing_status,
            state_of_residence=state_of_residence,
            local_tax_rate=Decimal(str(local_tax_rate))
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
    
    async def update_investor_profile(self, profile_id: int, **kwargs) -> Optional[InvestorProfile]:
        """Update investor profile"""
        profile = await self.get_investor_profile(profile_id)
        if not profile:
            return None
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                # Convert numeric fields to Decimal
                if key in ['annual_household_income', 'local_tax_rate'] and value is not None:
                    value = Decimal(str(value))
                setattr(profile, key, value)
        
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
