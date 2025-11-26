"""
Portfolio Service for Portfolio Manager Application

Handles all CRUD operations for portfolio management including:
- Portfolio creation, reading, updating, deletion
- Portfolio type management (Real vs Tracking)
- Portfolio-transaction relationships
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, case

from app.models.portfolio_models import Portfolio, Transaction
from datetime import datetime


class PortfolioService:
    """Service class for portfolio operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_portfolio(self, name: str, portfolio_type: str, description: str = None, cash_on_hand: float = 0.00) -> Portfolio:
        """
        Create a new portfolio
        
        Args:
            name: Portfolio name
            portfolio_type: 'real' or 'tracking' or 'retirement'
            description: Optional portfolio description
            cash_on_hand: Optional cash on hand amount (default 0.00)
            
        Returns:
            Created Portfolio object
            
        Raises:
            ValueError: If portfolio_type is invalid or cash_on_hand is negative
        """
        if portfolio_type not in ['real', 'tracking', 'retirement']:
            raise ValueError("Portfolio type must be 'real', 'tracking', or 'retirement'")
        
        if cash_on_hand < 0:
            raise ValueError("Cash on hand cannot be negative")
            
        portfolio = Portfolio(
            name=name,
            type=portfolio_type,
            description=description,
            cash_on_hand=cash_on_hand
        )
        
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        
        return portfolio
    
    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """
        Get portfolio by ID
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio object or None if not found
        """
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    def get_all_portfolios(self) -> List[Portfolio]:
        """
        Get all portfolios ordered by custom sequence: Trading, Tracking, 401k
        
        Returns:
            List of all Portfolio objects in desired UI order
        """
        # Custom ordering: Trading (1), Tracking (2), 401k (3), then any others by creation date
        custom_order = case(
            (Portfolio.name == 'Trading', 1),
            (Portfolio.name == 'Tracking', 2),
            (Portfolio.name == '401k', 3),
            else_=4
        )
        return self.db.query(Portfolio).order_by(custom_order, Portfolio.created_at.asc()).all()
    
    def get_portfolios_by_type(self, portfolio_type: str) -> List[Portfolio]:
        """
        Get portfolios by type
        
        Args:
            portfolio_type: 'real' or 'tracking'
            
        Returns:
            List of Portfolio objects of specified type
        """
        return self.db.query(Portfolio).filter(Portfolio.type == portfolio_type).order_by(Portfolio.created_at.desc()).all()
    
    def update_portfolio(self, portfolio_id: int, name: str = None, description: str = None, portfolio_type: str = None, cash_on_hand: float = None) -> Optional[Portfolio]:
        """
        Update portfolio information
        
        Args:
            portfolio_id: Portfolio ID
            name: New name (optional)
            description: New description (optional)
            portfolio_type: New type (optional)
            cash_on_hand: New cash on hand amount (optional)
            
        Returns:
            Updated Portfolio object or None if not found
            
        Raises:
            ValueError: If portfolio_type is invalid or cash_on_hand is negative
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
            
        if name is not None:
            portfolio.name = name
        if description is not None:
            portfolio.description = description
        if portfolio_type is not None:
            if portfolio_type not in ['real', 'tracking', 'retirement']:
                raise ValueError("Portfolio type must be 'real', 'tracking', or 'retirement'")
            portfolio.type = portfolio_type
        if cash_on_hand is not None:
            if cash_on_hand < 0:
                raise ValueError("Cash on hand cannot be negative")
            portfolio.cash_on_hand = cash_on_hand
            
        portfolio.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(portfolio)
        
        return portfolio
    
    def delete_portfolio(self, portfolio_id: int) -> bool:
        """
        Delete portfolio and all associated transactions
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            True if deleted, False if not found
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return False
            
        # Delete all associated transactions first (cascade should handle this, but being explicit)
        self.db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).delete()
        
        # Delete the portfolio
        self.db.delete(portfolio)
        self.db.commit()
        
        return True
    
    def get_portfolio_with_transactions(self, portfolio_id: int) -> Optional[Portfolio]:
        """
        Get portfolio with all its transactions loaded
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio object with transactions loaded or None if not found
        """
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if portfolio:
            # Explicitly load transactions to avoid lazy loading issues
            portfolio.transactions  # This triggers the lazy load
        return portfolio
    
    def get_portfolio_summary(self, portfolio_id: int) -> Optional[dict]:
        """
        Get portfolio summary with basic statistics
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Dictionary with portfolio summary or None if not found
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
            
        # Count transactions by type
        total_transactions = self.db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).count()
        buy_transactions = self.db.query(Transaction).filter(
            and_(Transaction.portfolio_id == portfolio_id, Transaction.transaction_type == 'buy')
        ).count()
        sell_transactions = self.db.query(Transaction).filter(
            and_(Transaction.portfolio_id == portfolio_id, Transaction.transaction_type == 'sell')
        ).count()
        
        # Get unique stocks count
        unique_stocks = self.db.query(Transaction.ticker_symbol).filter(
            Transaction.portfolio_id == portfolio_id
        ).distinct().count()
        
        return {
            'portfolio_id': portfolio.id,
            'name': portfolio.name,
            'type': portfolio.type,
            'description': portfolio.description,
            'total_transactions': total_transactions,
            'buy_transactions': buy_transactions,
            'sell_transactions': sell_transactions,
            'unique_stocks': unique_stocks,
            'created_at': portfolio.created_at,
            'updated_at': portfolio.updated_at
        }


def get_portfolio_service(db: Session) -> PortfolioService:
    """
    Dependency function to get PortfolioService instance
    
    Args:
        db: Database session
        
    Returns:
        PortfolioService instance
    """
    return PortfolioService(db)