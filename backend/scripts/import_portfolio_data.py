#!/usr/bin/env python3
"""
Import sample portfolio data into Capricorn's database
This script populates the portfolio tables with test data
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.models.portfolio_models import (
    InvestorProfile, 
    Portfolio, 
    PortfolioTransaction, 
    MarketPrice,
    TaxRate,
    StateTaxRate
)

# Database connection
# When running inside container, use container name; outside use localhost:5003
import os
if os.environ.get('DOCKER_CONTAINER'):
    DATABASE_URL = "postgresql+asyncpg://capricorn:capricorn2025@capricorn-postgres:5432/capricorn_db"
else:
    DATABASE_URL = "postgresql+asyncpg://capricorn:capricorn2025@localhost:5003/capricorn_db"

async def clear_existing_data(session: AsyncSession):
    """Clear existing portfolio data"""
    print("Clearing existing portfolio data...")
    
    # Delete in order of dependencies
    await session.execute(text("DELETE FROM portfolio_transactions"))
    await session.execute(text("DELETE FROM portfolios"))
    await session.execute(text("DELETE FROM investor_profiles"))
    await session.execute(text("DELETE FROM market_prices"))
    await session.execute(text("DELETE FROM tax_rates"))
    await session.execute(text("DELETE FROM state_tax_rates"))
    await session.commit()
    print("✓ Existing data cleared")

async def create_investor_profiles(session: AsyncSession):
    """Create sample investor profiles"""
    print("Creating investor profiles...")
    
    profiles = [
        InvestorProfile(
            name="John & Jane Smith",
            annual_household_income=Decimal("175000"),
            filing_status="married_filing_jointly",
            state_of_residence="CA",
            local_tax_rate=Decimal("0.015")  # 1.5%
        ),
        InvestorProfile(
            name="Robert Johnson",
            annual_household_income=Decimal("95000"),
            filing_status="single",
            state_of_residence="TX",
            local_tax_rate=Decimal("0")
        )
    ]
    
    for profile in profiles:
        session.add(profile)
    
    await session.commit()
    print(f"✓ Created {len(profiles)} investor profiles")
    return profiles

async def create_portfolios(session: AsyncSession, profiles):
    """Create sample portfolios"""
    print("Creating portfolios...")
    
    portfolios = [
        Portfolio(
            name="Retirement 401k",
            type="401k",
            description="Company 401k retirement account",
            cash_on_hand=Decimal("15000"),
            investor_profile_id=profiles[0].id
        ),
        Portfolio(
            name="IRA Traditional",
            type="IRA",
            description="Traditional Individual Retirement Account",
            cash_on_hand=Decimal("5000"),
            investor_profile_id=profiles[0].id
        ),
        Portfolio(
            name="Brokerage Account",
            type="Taxable",
            description="Personal investment account",
            cash_on_hand=Decimal("25000"),
            investor_profile_id=profiles[0].id
        ),
        Portfolio(
            name="Tech Growth Portfolio",
            type="Taxable",
            description="Technology focused growth portfolio",
            cash_on_hand=Decimal("10000"),
            investor_profile_id=profiles[1].id
        )
    ]
    
    for portfolio in portfolios:
        session.add(portfolio)
    
    await session.commit()
    print(f"✓ Created {len(portfolios)} portfolios")
    return portfolios

async def create_market_prices(session: AsyncSession):
    """Create current market prices for stocks"""
    print("Creating market prices...")
    
    prices = [
        ("AAPL", "185.50"),
        ("GOOGL", "140.25"),
        ("MSFT", "378.90"),
        ("AMZN", "155.75"),
        ("NVDA", "495.60"),
        ("META", "345.20"),
        ("TSLA", "242.50"),
        ("BRK.B", "365.80"),
        ("JPM", "158.40"),
        ("V", "265.30"),
        ("MA", "425.60"),
        ("PG", "152.75"),
        ("JNJ", "155.90"),
        ("UNH", "525.40"),
        ("HD", "345.60"),
        ("DIS", "92.45"),
        ("VZ", "38.50"),
        ("NFLX", "445.80"),
        ("ADBE", "598.20"),
        ("CRM", "265.40"),
        ("SPY", "450.25"),
        ("QQQ", "385.60"),
        ("VTI", "235.80"),
        ("VOO", "415.30")
    ]
    
    for ticker, price in prices:
        market_price = MarketPrice(
            ticker_symbol=ticker,
            current_price=Decimal(price),
            last_updated=datetime.now()
        )
        session.add(market_price)
    
    await session.commit()
    print(f"✓ Created {len(prices)} market prices")

async def create_transactions(session: AsyncSession, portfolios):
    """Create sample transactions for portfolios"""
    print("Creating transactions...")
    
    # Helper function to create transaction date
    def days_ago(days):
        return (datetime.now() - timedelta(days=days)).date()
    
    transactions = [
        # Retirement 401k transactions
        {"portfolio": portfolios[0], "ticker": "SPY", "name": "SPDR S&P 500 ETF", "type": "buy", "qty": 100, "price": "425.00", "date": days_ago(180)},
        {"portfolio": portfolios[0], "ticker": "QQQ", "name": "Invesco QQQ Trust", "type": "buy", "qty": 50, "price": "360.00", "date": days_ago(150)},
        {"portfolio": portfolios[0], "ticker": "VTI", "name": "Vanguard Total Stock", "type": "buy", "qty": 75, "price": "220.00", "date": days_ago(120)},
        {"portfolio": portfolios[0], "ticker": "MSFT", "name": "Microsoft Corp", "type": "buy", "qty": 25, "price": "340.00", "date": days_ago(90)},
        {"portfolio": portfolios[0], "ticker": "AAPL", "name": "Apple Inc", "type": "buy", "qty": 50, "price": "170.00", "date": days_ago(60)},
        
        # IRA transactions
        {"portfolio": portfolios[1], "ticker": "VOO", "name": "Vanguard S&P 500 ETF", "type": "buy", "qty": 30, "price": "390.00", "date": days_ago(200)},
        {"portfolio": portfolios[1], "ticker": "BRK.B", "name": "Berkshire Hathaway B", "type": "buy", "qty": 20, "price": "340.00", "date": days_ago(180)},
        {"portfolio": portfolios[1], "ticker": "JNJ", "name": "Johnson & Johnson", "type": "buy", "qty": 40, "price": "145.00", "date": days_ago(150)},
        {"portfolio": portfolios[1], "ticker": "PG", "name": "Procter & Gamble", "type": "buy", "qty": 35, "price": "140.00", "date": days_ago(120)},
        
        # Brokerage Account transactions (with some sells)
        {"portfolio": portfolios[2], "ticker": "NVDA", "name": "NVIDIA Corp", "type": "buy", "qty": 30, "price": "250.00", "date": days_ago(365)},
        {"portfolio": portfolios[2], "ticker": "NVDA", "name": "NVIDIA Corp", "type": "sell", "qty": 10, "price": "450.00", "date": days_ago(30)},
        {"portfolio": portfolios[2], "ticker": "TSLA", "name": "Tesla Inc", "type": "buy", "qty": 50, "price": "180.00", "date": days_ago(300)},
        {"portfolio": portfolios[2], "ticker": "META", "name": "Meta Platforms", "type": "buy", "qty": 40, "price": "280.00", "date": days_ago(250)},
        {"portfolio": portfolios[2], "ticker": "GOOGL", "name": "Alphabet Inc", "type": "buy", "qty": 60, "price": "120.00", "date": days_ago(200)},
        {"portfolio": portfolios[2], "ticker": "AMZN", "name": "Amazon.com Inc", "type": "buy", "qty": 45, "price": "130.00", "date": days_ago(150)},
        {"portfolio": portfolios[2], "ticker": "AMZN", "name": "Amazon.com Inc", "type": "buy", "qty": 25, "price": "145.00", "date": days_ago(60)},
        
        # Tech Growth Portfolio transactions
        {"portfolio": portfolios[3], "ticker": "NVDA", "name": "NVIDIA Corp", "type": "buy", "qty": 20, "price": "380.00", "date": days_ago(90)},
        {"portfolio": portfolios[3], "ticker": "MSFT", "name": "Microsoft Corp", "type": "buy", "qty": 15, "price": "350.00", "date": days_ago(75)},
        {"portfolio": portfolios[3], "ticker": "AAPL", "name": "Apple Inc", "type": "buy", "qty": 25, "price": "175.00", "date": days_ago(60)},
        {"portfolio": portfolios[3], "ticker": "CRM", "name": "Salesforce Inc", "type": "buy", "qty": 30, "price": "240.00", "date": days_ago(45)},
        {"portfolio": portfolios[3], "ticker": "ADBE", "name": "Adobe Inc", "type": "buy", "qty": 10, "price": "550.00", "date": days_ago(30)},
        {"portfolio": portfolios[3], "ticker": "NFLX", "name": "Netflix Inc", "type": "buy", "qty": 15, "price": "420.00", "date": days_ago(15)},
    ]
    
    for t in transactions:
        transaction = PortfolioTransaction(
            portfolio_id=t["portfolio"].id,
            ticker_symbol=t["ticker"],
            stock_name=t["name"],
            transaction_type=t["type"],
            quantity=Decimal(t["qty"]),
            price_per_share=Decimal(t["price"]),
            transaction_date=t["date"]
        )
        session.add(transaction)
    
    await session.commit()
    print(f"✓ Created {len(transactions)} transactions")

async def create_tax_tables(session: AsyncSession):
    """Create federal and state tax rate tables"""
    print("Creating tax tables...")
    
    # Federal tax rates for 2024
    federal_rates = [
        # Single filers
        {"filing_status": "single", "min_income": 0, "max_income": 11000, "rate": 10, "year": 2024},
        {"filing_status": "single", "min_income": 11000, "max_income": 44725, "rate": 12, "year": 2024},
        {"filing_status": "single", "min_income": 44725, "max_income": 95375, "rate": 22, "year": 2024},
        {"filing_status": "single", "min_income": 95375, "max_income": 182150, "rate": 24, "year": 2024},
        {"filing_status": "single", "min_income": 182150, "max_income": 231250, "rate": 32, "year": 2024},
        {"filing_status": "single", "min_income": 231250, "max_income": 578125, "rate": 35, "year": 2024},
        {"filing_status": "single", "min_income": 578125, "max_income": 999999999, "rate": 37, "year": 2024},
        
        # Married filing jointly
        {"filing_status": "married_filing_jointly", "min_income": 0, "max_income": 22000, "rate": 10, "year": 2024},
        {"filing_status": "married_filing_jointly", "min_income": 22000, "max_income": 89450, "rate": 12, "year": 2024},
        {"filing_status": "married_filing_jointly", "min_income": 89450, "max_income": 190750, "rate": 22, "year": 2024},
        {"filing_status": "married_filing_jointly", "min_income": 190750, "max_income": 364200, "rate": 24, "year": 2024},
        {"filing_status": "married_filing_jointly", "min_income": 364200, "max_income": 462500, "rate": 32, "year": 2024},
        {"filing_status": "married_filing_jointly", "min_income": 462500, "max_income": 693750, "rate": 35, "year": 2024},
        {"filing_status": "married_filing_jointly", "min_income": 693750, "max_income": 999999999, "rate": 37, "year": 2024},
    ]
    
    for rate in federal_rates:
        # For tax rates, we'll set both short and long term to the same federal rate for simplicity
        # In real app, these would be different
        tax_rate = TaxRate(
            tax_year=rate["year"],
            filing_status=rate["filing_status"],
            income_bracket_min=Decimal(str(rate["min_income"])),
            income_bracket_max=Decimal(str(rate["max_income"])),
            short_term_rate=Decimal(str(rate["rate"] / 100)),  # Convert percentage to decimal
            long_term_rate=Decimal(str(rate["rate"] / 100 * 0.6))  # Long term is lower
        )
        session.add(tax_rate)
    
    # State tax rates (simplified - using maximum state rates)
    state_rates = [
        {"state_code": "CA", "state_name": "California", "capital_gains": 13.3, "income_tax": 13.3},
        {"state_code": "TX", "state_name": "Texas", "capital_gains": 0, "income_tax": 0},
        {"state_code": "NY", "state_name": "New York", "capital_gains": 10.9, "income_tax": 10.9},
        {"state_code": "FL", "state_name": "Florida", "capital_gains": 0, "income_tax": 0},
        {"state_code": "WA", "state_name": "Washington", "capital_gains": 7.0, "income_tax": 0},
        {"state_code": "IL", "state_name": "Illinois", "capital_gains": 4.95, "income_tax": 4.95},
    ]
    
    for rate in state_rates:
        state_rate = StateTaxRate(
            state_code=rate["state_code"],
            state_name=rate["state_name"],
            tax_year=2024,
            capital_gains_rate=Decimal(str(rate["capital_gains"] / 100)),  # Convert percentage to decimal
            income_tax_rate=Decimal(str(rate["income_tax"] / 100)),
            has_capital_gains_tax=rate["capital_gains"] > 0
        )
        session.add(state_rate)
    
    await session.commit()
    print(f"✓ Created {len(federal_rates)} federal tax rates and {len(state_rates)} state tax rates")

async def verify_import(session: AsyncSession):
    """Verify the import was successful"""
    print("\nVerifying import...")
    
    # Count records
    profile_count = await session.execute(text("SELECT COUNT(*) FROM investor_profiles"))
    portfolio_count = await session.execute(text("SELECT COUNT(*) FROM portfolios"))
    transaction_count = await session.execute(text("SELECT COUNT(*) FROM portfolio_transactions"))
    price_count = await session.execute(text("SELECT COUNT(*) FROM market_prices"))
    
    print(f"  Investor Profiles: {profile_count.scalar()}")
    print(f"  Portfolios: {portfolio_count.scalar()}")
    print(f"  Transactions: {transaction_count.scalar()}")
    print(f"  Market Prices: {price_count.scalar()}")

async def main():
    """Main import function"""
    print("=" * 60)
    print("Portfolio Data Import for Capricorn")
    print("Database: Capricorn (port 5003)")
    print("=" * 60)
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Clear existing data
            await clear_existing_data(session)
            
            # Create data in order
            profiles = await create_investor_profiles(session)
            portfolios = await create_portfolios(session, profiles)
            await create_market_prices(session)
            await create_transactions(session, portfolios)
            await create_tax_tables(session)
            
            # Verify
            await verify_import(session)
            
            print("\n✅ Portfolio data import completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Error during import: {e}")
            await session.rollback()
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
