"""
Transaction Service for Portfolio Manager Application

Handles all CRUD operations for transaction management including:
- Individual transaction tracking (critical for tax calculations)  
- Multiple transactions per stock with different dates/prices
- Buy/Sell transaction types with proper accounting
- Integration with Portfolio and MarketPrice models
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func, case
from datetime import datetime, date
from decimal import Decimal

from app.models.portfolio_models import Transaction, Portfolio, MarketPrice
from .portfolio_service import PortfolioService
from .market_price_service import MarketPriceService


class TransactionService:
    """Service class for transaction operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
    
    def create_transaction(
        self, 
        portfolio_id: int,
        ticker: str,
        transaction_type: str,  # 'buy' or 'sell'
        quantity: Decimal,
        price_per_share: Decimal,
        transaction_date: date,
        stock_name: str = None,
        notes: str = None
    ) -> Transaction:
        """
        Create a new transaction
        
        Args:
            portfolio_id: ID of the portfolio this transaction belongs to
            ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            transaction_type: 'buy' or 'sell'
            quantity: Number of shares
            price_per_share: Price per share at transaction time
            transaction_date: Date when transaction occurred
            notes: Optional notes about the transaction
            
        Returns:
            Created Transaction object
        """
        # Validate portfolio exists
        portfolio = self.portfolio_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio with ID {portfolio_id} not found")
        
        # Validate transaction type
        if transaction_type.lower() not in ['buy', 'sell']:
            raise ValueError("Transaction type must be 'buy' or 'sell'")
        
        # Create transaction
        transaction = Transaction(
            portfolio_id=portfolio_id,
            ticker_symbol=ticker.upper(),
            stock_name=stock_name or ticker.upper(),  # Use ticker as stock name if not provided
            transaction_type=transaction_type.lower(),
            quantity=quantity,
            price_per_share=price_per_share,
            transaction_date=transaction_date
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        # Ensure a MarketPrice placeholder exists for new tickers (improves UX)
        try:
            if transaction.transaction_type == 'buy':
                mp_service = MarketPriceService(self.db)
                existing = mp_service.get_price(transaction.ticker_symbol)
                if not existing:
                    mp_service.update_price(
                        transaction.ticker_symbol,
                        transaction.price_per_share
                    )
        except Exception:
            # Non-fatal; downstream refresh endpoints will fill real quotes
            pass

        return transaction
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    def get_transactions_by_portfolio(
        self, 
        portfolio_id: int,
        ticker: str = None,
        transaction_type: str = None,
        start_date: date = None,
        end_date: date = None,
        order_by: str = 'date_desc'
    ) -> List[Transaction]:
        """
        Get all transactions for a portfolio with optional filtering
        
        Args:
            portfolio_id: Portfolio ID to filter by
            ticker: Optional ticker filter
            transaction_type: Optional 'buy' or 'sell' filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            order_by: 'date_desc', 'date_asc', 'ticker', 'quantity'
            
        Returns:
            List of Transaction objects
        """
        query = self.db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id)
        
        # Apply filters
        if ticker:
            query = query.filter(Transaction.ticker_symbol == ticker.upper())
        
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type.lower())
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        # Apply ordering
        if order_by == 'date_desc':
            query = query.order_by(desc(Transaction.transaction_date))
        elif order_by == 'date_asc':
            query = query.order_by(asc(Transaction.transaction_date))
        elif order_by == 'ticker':
            query = query.order_by(asc(Transaction.ticker_symbol), desc(Transaction.transaction_date))
        elif order_by == 'quantity':
            query = query.order_by(desc(Transaction.quantity))
        
        return query.all()
    
    def get_transactions_by_ticker(
        self, 
        ticker: str,
        portfolio_id: int = None
    ) -> List[Transaction]:
        """
        Get all transactions for a specific ticker
        Critical for tax calculations - need transaction history per stock
        """
        query = self.db.query(Transaction).filter(Transaction.ticker_symbol == ticker.upper())
        
        if portfolio_id:
            query = query.filter(Transaction.portfolio_id == portfolio_id)
        
        return query.order_by(asc(Transaction.transaction_date)).all()
    
    def get_portfolio_holdings(self, portfolio_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Calculate current holdings for a portfolio
        
        Returns:
            Dict with ticker as key and holding info as value:
            {
                'AAPL': {
                    'quantity': 150.0,
                    'avg_cost_basis': 145.50,
                    'total_invested': 21825.00,
                    'transactions': [list of transactions]
                }
            }
        """
        transactions = self.get_transactions_by_portfolio(portfolio_id, order_by='ticker')
        holdings = {}
        
        for transaction in transactions:
            ticker = transaction.ticker_symbol
            
            if ticker not in holdings:
                holdings[ticker] = {
                    'quantity': Decimal('0'),
                    'total_invested': Decimal('0'),
                    'transactions': []
                }
            
            holdings[ticker]['transactions'].append(transaction)
            
            if transaction.transaction_type == 'buy':
                holdings[ticker]['quantity'] += transaction.quantity
                holdings[ticker]['total_invested'] += (transaction.quantity * transaction.price_per_share)
            elif transaction.transaction_type == 'sell':
                holdings[ticker]['quantity'] -= transaction.quantity
                # For sells, we reduce total invested proportionally
                if holdings[ticker]['quantity'] > 0:
                    sell_value = transaction.quantity * transaction.price_per_share
                    # This is simplified - real tax calculation needs FIFO/LIFO
                    proportion_sold = transaction.quantity / (holdings[ticker]['quantity'] + transaction.quantity)
                    holdings[ticker]['total_invested'] -= (holdings[ticker]['total_invested'] * proportion_sold)
        
        # Calculate average cost basis for remaining holdings
        for ticker, holding in holdings.items():
            if holding['quantity'] > 0:
                holding['avg_cost_basis'] = holding['total_invested'] / holding['quantity']
            else:
                holding['avg_cost_basis'] = Decimal('0')
        
        # Filter out positions with zero quantity
        holdings = {ticker: holding for ticker, holding in holdings.items() if holding['quantity'] > 0}
        
        return holdings
    
    def update_transaction(
        self,
        transaction_id: int,
        **updates
    ) -> Optional[Transaction]:
        """
        Update transaction fields
        
        Args:
            transaction_id: Transaction ID to update
            **updates: Fields to update (ticker_symbol, transaction_type, quantity, price_per_share, transaction_date, notes)
            
        Returns:
            Updated Transaction object or None if not found
        """
        transaction = self.get_transaction_by_id(transaction_id)
        if not transaction:
            return None
        
        # Update allowed fields - expanded to support stock splits and corrections
        allowed_fields = [
            'ticker_symbol',      # Support ticker changes
            'transaction_type',   # Support type corrections
            'quantity', 
            'price_per_share', 
            'transaction_date', 
            'notes'
        ]
        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                setattr(transaction, field, value)
        
        # Update timestamp
        transaction.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete a transaction
        
        Args:
            transaction_id: Transaction ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        transaction = self.get_transaction_by_id(transaction_id)
        if not transaction:
            return False
        
        self.db.delete(transaction)
        self.db.commit()
        
        return True
    
    def get_all_unique_tickers(self, portfolio_id: int = None) -> List[str]:
        """
        Get all unique ticker symbols
        Useful for market price updates
        """
        query = self.db.query(Transaction.ticker_symbol).distinct()
        
        if portfolio_id:
            query = query.filter(Transaction.portfolio_id == portfolio_id)
        
        tickers = query.all()
        return [ticker[0] for ticker in tickers]

    def get_currently_held_tickers(self) -> List[str]:
        """
        Return tickers with positive net quantity across all portfolios.
        Net quantity is SUM(buy quantity) - SUM(sell quantity) per ticker.
        """
        net_expr = func.sum(
            case(
                (Transaction.transaction_type == 'buy', Transaction.quantity),
                else_=-Transaction.quantity,
            )
        )
        rows = (
            self.db.query(Transaction.ticker_symbol, net_expr.label('net_qty'))
            .group_by(Transaction.ticker_symbol)
            .having(net_expr > 0)
            .all()
        )
        return [r[0] for r in rows]


def get_transaction_service(db: Session) -> TransactionService:
    """Dependency injection helper for FastAPI"""
    return TransactionService(db)