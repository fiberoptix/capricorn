"""
Portfolio models for Capricorn
These models use Capricorn's database (port 5003), not the reference app
"""

from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Date, 
    DateTime, 
    Boolean, 
    Text, 
    ForeignKey, 
    CheckConstraint,
    UniqueConstraint,
    Index
)
from sqlalchemy.types import Numeric as Decimal
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date

from app.core.database import Base

# Portfolio Models for Capricorn

class InvestorProfile(Base):
    """Investor profile model - user's personal and tax information"""
    __tablename__ = "investor_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    annual_household_income = Column(Decimal(15, 2), nullable=False)
    filing_status = Column(String(50), nullable=False)
    state_of_residence = Column(String(2), nullable=False)
    local_tax_rate = Column(Decimal(5, 4), default=0.00)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="investor_profile")


class Portfolio(Base):
    """Portfolio model - represents a user's stock portfolio"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)
    description = Column(Text)
    cash_on_hand = Column(Decimal(15, 2), default=0.00)
    investor_profile_id = Column(Integer, ForeignKey('investor_profiles.id'), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    transactions = relationship("PortfolioTransaction", back_populates="portfolio", cascade="all, delete-orphan")
    investor_profile = relationship("InvestorProfile", back_populates="portfolios")


class PortfolioTransaction(Base):
    """Transaction model - individual stock buy/sell transactions"""
    __tablename__ = "portfolio_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False)
    stock_name = Column(String(255), nullable=False)
    ticker_symbol = Column(String(10), nullable=False)
    transaction_type = Column(String(10), nullable=False)
    quantity = Column(Decimal(15, 4), nullable=False)
    price_per_share = Column(Decimal(15, 4), nullable=False)
    transaction_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    
    @property
    def total_amount(self):
        """Calculate total transaction amount"""
        return self.quantity * self.price_per_share
    
    @property
    def days_held(self):
        """Calculate days held from transaction date to today"""
        if self.transaction_type == 'sell':
            return 0
        return (date.today() - self.transaction_date).days
    
    @property
    def is_long_term(self):
        """Determine if transaction qualifies for long-term capital gains"""
        return self.days_held > 365


class MarketPrice(Base):
    """Market price model - current stock prices"""
    __tablename__ = "market_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String(10), nullable=False, unique=True)
    current_price = Column(Decimal(15, 4), nullable=False)
    last_updated = Column(DateTime, default=func.current_timestamp())


class TaxRate(Base):
    """Tax rate model - federal tax brackets and rates"""
    __tablename__ = "tax_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    tax_year = Column(Integer, nullable=False)
    filing_status = Column(String(50), nullable=False)
    income_bracket_min = Column(Decimal(15, 2))
    income_bracket_max = Column(Decimal(15, 2))
    short_term_rate = Column(Decimal(5, 4), nullable=False)
    long_term_rate = Column(Decimal(5, 4), nullable=False)
    niit_rate = Column(Decimal(5, 4), default=0.038)
    active = Column(Boolean, default=True)


class StateTaxRate(Base):
    """State tax rate model - state-by-state capital gains and income tax rates"""
    __tablename__ = "state_tax_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    state_code = Column(String(2), nullable=False)
    state_name = Column(String(50), nullable=False)
    tax_year = Column(Integer, nullable=False)
    capital_gains_rate = Column(Decimal(5, 4), nullable=False)
    income_tax_rate = Column(Decimal(5, 4), nullable=False)
    has_capital_gains_tax = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=func.current_timestamp())


# Aliases for compatibility with copied services
Transaction = PortfolioTransaction  # The services expect "Transaction" not "PortfolioTransaction"
