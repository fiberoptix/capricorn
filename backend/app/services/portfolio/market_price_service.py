"""
MarketPrice Service for Portfolio Manager Application

Handles all CRUD operations for market price management including:
- Current stock price storage and retrieval
- Bulk price updates for multiple stocks
- Price history tracking
- Market data validation
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.portfolio_models import MarketPrice


class MarketPriceService:
    """Service class for market price operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_price(self, ticker: str) -> Optional[MarketPrice]:
        """
        Get current market price for a ticker
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            
        Returns:
            MarketPrice object or None if not found
        """
        return self.db.query(MarketPrice).filter(
            MarketPrice.ticker_symbol == ticker.upper()
        ).first()
    
    def get_all_prices(self, order_by: str = 'ticker') -> List[MarketPrice]:
        """
        Get all current market prices
        
        Args:
            order_by: 'ticker', 'price', 'updated' 
            
        Returns:
            List of MarketPrice objects
        """
        query = self.db.query(MarketPrice)
        
        if order_by == 'ticker':
            query = query.order_by(asc(MarketPrice.ticker_symbol))
        elif order_by == 'price':
            query = query.order_by(desc(MarketPrice.current_price))
        elif order_by == 'updated':
            query = query.order_by(desc(MarketPrice.last_updated))
        
        return query.all()
    
    def get_prices_for_tickers(self, tickers: List[str]) -> Dict[str, MarketPrice]:
        """
        Get market prices for multiple tickers
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker to MarketPrice object
        """
        tickers_upper = [ticker.upper() for ticker in tickers]
        prices = self.db.query(MarketPrice).filter(
            MarketPrice.ticker_symbol.in_(tickers_upper)
        ).all()
        
        return {price.ticker_symbol: price for price in prices}
    
    def update_price(
        self, 
        ticker: str, 
        current_price: Decimal,
        last_updated: datetime = None
    ) -> MarketPrice:
        """
        Update or create market price for a ticker
        
        Args:
            ticker: Stock ticker symbol
            current_price: Current market price
            last_updated: When price was updated (defaults to now)
            
        Returns:
            Updated or created MarketPrice object
        """
        if last_updated is None:
            last_updated = datetime.utcnow()
        
        # Check if price already exists
        existing_price = self.get_price(ticker)
        
        if existing_price:
            # Update existing price
            existing_price.current_price = current_price
            existing_price.last_updated = last_updated
            self.db.commit()
            self.db.refresh(existing_price)
            return existing_price
        else:
            # Create new price entry
            new_price = MarketPrice(
                ticker_symbol=ticker.upper(),
                current_price=current_price,
                last_updated=last_updated
            )
            self.db.add(new_price)
            self.db.commit()
            self.db.refresh(new_price)
            return new_price
    
    def bulk_update_prices(self, price_data: Dict[str, Decimal]) -> List[MarketPrice]:
        """
        Update multiple stock prices in a single operation
        
        Args:
            price_data: Dictionary mapping ticker to price
                       e.g., {'AAPL': Decimal('150.25'), 'TSLA': Decimal('225.50')}
            
        Returns:
            List of updated MarketPrice objects
        """
        updated_prices = []
        update_time = datetime.utcnow()
        
        for ticker, price in price_data.items():
            updated_price = self.update_price(ticker, price, update_time)
            updated_prices.append(updated_price)
        
        return updated_prices
    
    def delete_price(self, ticker: str) -> bool:
        """
        Delete market price for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            True if deleted, False if not found
        """
        price = self.get_price(ticker)
        if price:
            self.db.delete(price)
            self.db.commit()
            return True
        return False
    
    def get_stale_prices(self, hours_old: int = 24) -> List[MarketPrice]:
        """
        Get market prices that haven't been updated recently
        
        Args:
            hours_old: Consider prices stale if older than this many hours
            
        Returns:
            List of MarketPrice objects that need updating
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        
        return self.db.query(MarketPrice).filter(
            MarketPrice.last_updated < cutoff_time
        ).order_by(asc(MarketPrice.last_updated)).all()
    
    def calculate_portfolio_value(
        self, 
        holdings: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate current market value for portfolio holdings
        
        Args:
            holdings: Portfolio holdings from TransactionService.get_portfolio_holdings()
                     Format: {'AAPL': {'quantity': 100, 'avg_cost_basis': 150.0, ...}, ...}
            
        Returns:
            Dictionary with market values and gains/losses
            {
                'total_market_value': Decimal,
                'total_cost_basis': Decimal, 
                'total_gain_loss': Decimal,
                'total_gain_loss_percent': float,
                'holdings_with_prices': {...}
            }
        """
        if not holdings:
            return {
                'total_market_value': Decimal('0'),
                'total_cost_basis': Decimal('0'),
                'total_gain_loss': Decimal('0'),
                'total_gain_loss_percent': 0.0,
                'holdings_with_prices': {}
            }
        
        # Get current prices for all tickers
        tickers = list(holdings.keys())
        current_prices = self.get_prices_for_tickers(tickers)
        
        total_market_value = Decimal('0')
        total_cost_basis = Decimal('0')
        holdings_with_prices = {}
        
        for ticker, holding in holdings.items():
            quantity = Decimal(str(holding['quantity']))
            avg_cost_basis = Decimal(str(holding['avg_cost_basis']))
            cost_basis = Decimal(str(holding['total_invested']))
            
            # Get current market price
            current_price_obj = current_prices.get(ticker)
            if current_price_obj:
                current_price = current_price_obj.current_price
                market_value = quantity * current_price
                gain_loss = market_value - cost_basis
                gain_loss_percent = float((gain_loss / cost_basis) * 100) if cost_basis > 0 else 0.0
                
                holdings_with_prices[ticker] = {
                    'quantity': float(quantity),
                    'avg_cost_basis': float(avg_cost_basis),
                    'current_price': float(current_price),
                    'market_value': float(market_value),
                    'cost_basis': float(cost_basis),
                    'gain_loss': float(gain_loss),
                    'gain_loss_percent': gain_loss_percent,
                    'last_updated': current_price_obj.last_updated.isoformat(),
                    'transaction_count': holding.get('transaction_count', 0)
                }
                
                total_market_value += market_value
                total_cost_basis += cost_basis
            else:
                # No current price available
                holdings_with_prices[ticker] = {
                    'quantity': float(quantity),
                    'avg_cost_basis': float(avg_cost_basis),
                    'current_price': None,
                    'market_value': None,
                    'cost_basis': float(cost_basis),
                    'gain_loss': None,
                    'gain_loss_percent': None,
                    'last_updated': None,
                    'transaction_count': holding.get('transaction_count', 0),
                    'error': 'No current price available'
                }
                total_cost_basis += cost_basis
        
        total_gain_loss = total_market_value - total_cost_basis
        total_gain_loss_percent = float((total_gain_loss / total_cost_basis) * 100) if total_cost_basis > 0 else 0.0
        
        return {
            'total_market_value': total_market_value,
            'total_cost_basis': total_cost_basis,
            'total_gain_loss': total_gain_loss,
            'total_gain_loss_percent': total_gain_loss_percent,
            'holdings_with_prices': holdings_with_prices
        }


def get_market_price_service(db: Session) -> MarketPriceService:
    """Dependency injection helper for Flask"""
    return MarketPriceService(db)