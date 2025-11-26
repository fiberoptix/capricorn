"""
Portfolio Manager Database Models

Direct port from the original Portfolio Manager application.
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class InvestorProfile(Base):
    __tablename__ = 'investor_profiles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    annual_household_income = Column(Numeric(12, 2))
    filing_status = Column(String(50))
    state_of_residence = Column(String(2))
    local_tax_rate = Column(Numeric(5, 4), default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolios = relationship("Portfolio", back_populates="investor_profile")


class Portfolio(Base):
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50))
    description = Column(Text)
    cash_on_hand = Column(Numeric(12, 2), default=0.0)
    investor_profile_id = Column(Integer, ForeignKey('investor_profiles.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    investor_profile = relationship("InvestorProfile", back_populates="portfolios")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = 'portfolio_transactions'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    stock_name = Column(String(255))
    ticker_symbol = Column(String(10))
    transaction_type = Column(String(10))  # 'Buy' or 'Sell'
    quantity = Column(Numeric(12, 4))
    price_per_share = Column(Numeric(12, 2))
    transaction_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolio = relationship("Portfolio", back_populates="transactions")


class MarketPrice(Base):
    __tablename__ = 'market_prices'
    
    id = Column(Integer, primary_key=True)
    ticker_symbol = Column(String(10), unique=True, nullable=False)
    current_price = Column(Numeric(12, 2))
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaxRate(Base):
    __tablename__ = 'tax_rates'
    
    id = Column(Integer, primary_key=True)
    tax_year = Column(Integer, nullable=False)
    filing_status = Column(String(50), nullable=False)
    income_bracket_min = Column(Numeric(12, 2))
    income_bracket_max = Column(Numeric(12, 2))
    short_term_rate = Column(Numeric(5, 4))
    long_term_rate = Column(Numeric(5, 4))
    niit_rate = Column(Numeric(5, 4))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StateTaxRate(Base):
    __tablename__ = 'state_tax_rates'
    
    id = Column(Integer, primary_key=True)
    state_code = Column(String(2), nullable=False)
    state_name = Column(String(100))
    tax_year = Column(Integer, nullable=False)
    capital_gains_rate = Column(Numeric(5, 4))
    income_tax_rate = Column(Numeric(5, 4))
    has_capital_gains_tax = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)