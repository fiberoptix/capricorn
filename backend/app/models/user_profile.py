"""
User Profile Model
Unified profile for Finance, Portfolio, and Retirement modules
Single-user system (id=1 always)
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean
from .base import Base, TimestampMixin

class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profile"
    
    # Original Finance Manager fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Section 1: Personal Information
    user = Column(String(100), default='User')
    partner = Column(String(100), default='Partner')
    user_age = Column(Integer, default=30)
    partner_age = Column(Integer, default=30)
    years_of_retirement = Column(Integer, default=30)
    user_years_to_retirement = Column(Integer, default=35)
    partner_years_to_retirement = Column(Integer, default=35)
    
    # Section 2: Income Parameters (single person defaults - partner values are 0)
    user_salary = Column(Numeric(15, 2), default=100000.00)
    user_bonus_rate = Column(Numeric(5, 4), default=0.0500)
    user_raise_rate = Column(Numeric(5, 4), default=0.0500)
    partner_salary = Column(Numeric(15, 2), default=0.00)
    partner_bonus_rate = Column(Numeric(5, 4), default=0.0500)
    partner_raise_rate = Column(Numeric(5, 4), default=0.0500)
    
    # Section 3: Expense Parameters
    monthly_living_expenses = Column(Numeric(15, 2), default=5000.00)
    annual_discretionary_spending = Column(Numeric(15, 2), default=10000.00)
    annual_inflation_rate = Column(Numeric(5, 4), default=0.0400)
    
    # Section 4: 401K Parameters
    user_401k_contribution = Column(Numeric(15, 2), default=24000.00)
    partner_401k_contribution = Column(Numeric(15, 2), default=0.00)
    user_employer_match = Column(Numeric(15, 2), default=5000.00)
    partner_employer_match = Column(Numeric(15, 2), default=0.00)
    user_current_401k_balance = Column(Numeric(15, 2), default=100000.00)
    partner_current_401k_balance = Column(Numeric(15, 2), default=0.00)
    user_401k_growth_rate = Column(Numeric(5, 4), default=0.1000)
    partner_401k_growth_rate = Column(Numeric(5, 4), default=0.1000)
    
    # Section 5: Investment Accounts
    current_ira_balance = Column(Numeric(15, 2), default=0.00)
    ira_return_rate = Column(Numeric(5, 4), default=0.1000)
    current_trading_balance = Column(Numeric(15, 2), default=0.00)
    trading_return_rate = Column(Numeric(5, 4), default=0.1000)
    current_savings_balance = Column(Numeric(15, 2), default=0.00)
    savings_return_rate = Column(Numeric(5, 4), default=0.0000)
    expected_inheritance = Column(Numeric(15, 2), default=0.00)
    inheritance_year = Column(Integer, default=20)
    
    # Section 6: Tax Parameters
    state = Column(String(50), default='NY')  # 2-letter state code
    local_tax_rate = Column(Numeric(5, 4), default=0.0100)
    filing_status = Column(String(50), default='single')  # Must match Tax API format
    calculated_federal_rate = Column(Numeric(5, 4))
    calculated_state_rate = Column(Numeric(5, 4))
    calculated_total_rate = Column(Numeric(5, 4))
    
    # Section 7: Retirement Parameters
    retirement_growth_rate = Column(Numeric(5, 4), default=0.0500)
    withdrawal_rate = Column(Numeric(5, 4), default=0.0400)
    
    # Section 8: Savings Strategy
    fixed_monthly_savings = Column(Numeric(15, 2), default=1000.00)
    percentage_of_leftover = Column(Numeric(5, 4), default=0.5000)
    savings_destination = Column(String(20), default='trading')  # 'savings' or 'trading'
    
    # Section 9: App Settings (shared across all clients)
    realtime_pricing_enabled = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, user='{self.user}', partner='{self.partner}')>"

