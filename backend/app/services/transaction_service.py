"""
Transaction service for Capricorn
Uses Capricorn's own database (port 5003)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.models.portfolio_models import PortfolioTransaction, Portfolio


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_transactions(self) -> List[PortfolioTransaction]:
        """Get all transactions from Capricorn's database"""
        result = await self.db.execute(
            select(PortfolioTransaction).order_by(PortfolioTransaction.transaction_date.desc())
        )
        return result.scalars().all()
    
    async def get_portfolio_transactions(self, portfolio_id: int) -> List[PortfolioTransaction]:
        """Get transactions for a specific portfolio"""
        result = await self.db.execute(
            select(PortfolioTransaction)
            .where(PortfolioTransaction.portfolio_id == portfolio_id)
            .order_by(PortfolioTransaction.transaction_date.desc())
        )
        return result.scalars().all()
    
    async def get_transaction_by_id(self, transaction_id: int) -> Optional[PortfolioTransaction]:
        """Get transaction by ID"""
        result = await self.db.execute(
            select(PortfolioTransaction)
            .where(PortfolioTransaction.id == transaction_id)
        )
        return result.scalar_one_or_none()
    
    async def create_transaction(
        self,
        portfolio_id: int,
        ticker: str,
        transaction_type: str,
        quantity: Decimal,
        price_per_share: Decimal,
        transaction_date: date,
        stock_name: Optional[str] = None
    ) -> PortfolioTransaction:
        """Create new transaction in Capricorn's database"""
        # Note: ticker_symbol field in database, not ticker
        # Use ticker as stock_name if not provided
        transaction = PortfolioTransaction(
            portfolio_id=portfolio_id,
            stock_name=stock_name or ticker.upper(),  # Use ticker as name if not provided
            ticker_symbol=ticker.upper(),
            transaction_type=transaction_type,
            quantity=quantity,
            price_per_share=price_per_share,
            transaction_date=transaction_date
        )
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction
    
    async def update_transaction(self, transaction_id: int, **kwargs) -> Optional[PortfolioTransaction]:
        """Update transaction"""
        transaction = await self.get_transaction_by_id(transaction_id)
        if not transaction:
            return None
        
        # Handle ticker -> ticker_symbol mapping
        if 'ticker' in kwargs:
            kwargs['ticker_symbol'] = kwargs.pop('ticker')
        
        for key, value in kwargs.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)
        
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction
    
    async def delete_transaction(self, transaction_id: int) -> bool:
        """Delete transaction from Capricorn's database"""
        result = await self.db.execute(
            delete(PortfolioTransaction)
            .where(PortfolioTransaction.id == transaction_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_portfolio_holdings(self, portfolio_id: int) -> dict:
        """Calculate current holdings for a portfolio"""
        transactions = await self.get_portfolio_transactions(portfolio_id)
        
        holdings = {}
        for transaction in transactions:
            ticker = transaction.ticker_symbol
            if ticker not in holdings:
                holdings[ticker] = {
                    'ticker': ticker,
                    'total_shares': 0,
                    'cost_basis': 0,
                    'avg_price': 0
                }
            
            if transaction.transaction_type == 'Buy':
                holdings[ticker]['total_shares'] += float(transaction.quantity)
                holdings[ticker]['cost_basis'] += float(transaction.quantity * transaction.price_per_share)
            else:  # Sell
                holdings[ticker]['total_shares'] -= float(transaction.quantity)
                # Adjust cost basis proportionally
                if holdings[ticker]['total_shares'] > 0:
                    holdings[ticker]['cost_basis'] *= (holdings[ticker]['total_shares'] / 
                                                       (holdings[ticker]['total_shares'] + float(transaction.quantity)))
        
        # Calculate average price and remove zero holdings
        result = {}
        for ticker, data in holdings.items():
            if data['total_shares'] > 0:
                data['avg_price'] = data['cost_basis'] / data['total_shares']
                result[ticker] = data
        
        return result
    
    async def get_currently_held_tickers(self) -> List[str]:
        """
        Get list of all ticker symbols with positive net quantity across all portfolios
        Used by market data service to determine which tickers need price updates
        
        Returns:
            List of ticker symbols (e.g., ['AAPL', 'MSFT', 'GOOGL'])
        """
        result = await self.db.execute(
            text("""
                SELECT ticker_symbol, 
                       SUM(CASE 
                           WHEN transaction_type = 'buy' THEN quantity 
                           ELSE -quantity 
                       END) as net_quantity
                FROM portfolio_transactions
                GROUP BY ticker_symbol
                HAVING SUM(CASE 
                           WHEN transaction_type = 'buy' THEN quantity 
                           ELSE -quantity 
                       END) > 0
                ORDER BY ticker_symbol
            """)
        )
        rows = result.all()
        return [row[0].upper() for row in rows]
