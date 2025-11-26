"""
Portfolio Manager Database Setup

This script creates the Portfolio Manager tables in the Capricorn database.
Run this once to set up all required tables.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.portfolio.database import Base, Portfolio, Transaction, MarketPrice, InvestorProfile, TaxRate, StateTaxRate

# Use sync engine for table creation
DATABASE_URL = str(settings.DATABASE_URL).replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(DATABASE_URL)

def create_portfolio_tables():
    """Create all Portfolio Manager tables"""
    print("Creating Portfolio Manager tables...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Portfolio Manager tables created successfully!")
    
    # Verify tables
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public' 
            AND table_name IN ('portfolios', 'transactions', 'market_prices', 
                              'investor_profiles', 'tax_rates', 'state_tax_rates')
            ORDER BY table_name
        """))
        tables = result.fetchall()
        
        print("\nCreated tables:")
        for table in tables:
            print(f"  - {table[0]}")
    
    # Create default investor profile
    with engine.connect() as conn:
        # Check if profile exists
        result = conn.execute(text("SELECT COUNT(*) FROM investor_profiles"))
        count = result.scalar()
        
        if count == 0:
            print("\nCreating default investor profile...")
            conn.execute(text("""
                INSERT INTO investor_profiles 
                (name, annual_household_income, filing_status, state_of_residence, local_tax_rate)
                VALUES ('Default Investor', 100000, 'single', 'NY', 0.01)
            """))
            conn.commit()
            print("✅ Default investor profile created")

if __name__ == "__main__":
    create_portfolio_tables()
