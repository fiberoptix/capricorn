-- Portfolio Manager Database Schema
-- PostgreSQL initialization script

-- Create investor_profiles table first (referenced by portfolios)
CREATE TABLE investor_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    annual_household_income DECIMAL(15,2) NOT NULL,
    filing_status VARCHAR(20) NOT NULL CHECK (filing_status IN ('single', 'married_joint', 'head_of_household')),
    state_of_residence VARCHAR(2) NOT NULL, -- US state code (NY, CA, TX, etc.)
    local_tax_rate DECIMAL(5,4) DEFAULT 0.00, -- Local/city tax rate as decimal (0.01 = 1%)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT positive_income CHECK (annual_household_income > 0),
    CONSTRAINT valid_local_tax CHECK (local_tax_rate >= 0 AND local_tax_rate <= 0.50)
);

-- Create portfolios table
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('real', 'tracking', 'retirement')),
    description TEXT,
    investor_profile_id INTEGER REFERENCES investor_profiles(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create transactions table
-- IMPORTANT: Each transaction is separate, even for the same stock on different dates
-- This allows precise tax calculations for each individual purchase/sale
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    stock_name VARCHAR(255) NOT NULL,
    ticker_symbol VARCHAR(10) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('buy', 'sell')),
    quantity DECIMAL(15,4) NOT NULL,
    price_per_share DECIMAL(15,4) NOT NULL,
    transaction_date DATE NOT NULL,
    total_amount DECIMAL(15,4) GENERATED ALWAYS AS (quantity * price_per_share) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_price CHECK (price_per_share > 0)
    
    -- NOTE: No unique constraint on (portfolio_id, ticker_symbol, transaction_date)
    -- This allows multiple transactions of the same stock on the same day if needed
    -- Each row represents one individual transaction for separate tax treatment
);

-- Create market_prices table
CREATE TABLE market_prices (
    id SERIAL PRIMARY KEY,
    ticker_symbol VARCHAR(10) NOT NULL UNIQUE,
    current_price DECIMAL(15,4) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT positive_price CHECK (current_price > 0)
);



-- Create tax_rates configuration table (Federal)
CREATE TABLE tax_rates (
    id SERIAL PRIMARY KEY,
    tax_year INTEGER NOT NULL,
    filing_status VARCHAR(20) NOT NULL,
    income_bracket_min DECIMAL(15,2),
    income_bracket_max DECIMAL(15,2),
    short_term_rate DECIMAL(5,4) NOT NULL,
    long_term_rate DECIMAL(5,4) NOT NULL,
    niit_rate DECIMAL(5,4) DEFAULT 0.038,
    active BOOLEAN DEFAULT true,
    
    UNIQUE(tax_year, filing_status, income_bracket_min)
);

-- Create state_tax_rates table
CREATE TABLE state_tax_rates (
    id SERIAL PRIMARY KEY,
    state_code VARCHAR(2) NOT NULL,
    state_name VARCHAR(50) NOT NULL,
    tax_year INTEGER NOT NULL,
    capital_gains_rate DECIMAL(5,4) NOT NULL, -- State capital gains rate
    income_tax_rate DECIMAL(5,4) NOT NULL,    -- State income tax rate
    has_capital_gains_tax BOOLEAN DEFAULT true,
    active BOOLEAN DEFAULT true,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(state_code, tax_year),
    CONSTRAINT valid_state_rates CHECK (capital_gains_rate >= 0 AND income_tax_rate >= 0)
);

-- Create indexes for performance
CREATE INDEX idx_portfolios_type ON portfolios(type);
CREATE INDEX idx_transactions_portfolio_id ON transactions(portfolio_id);
CREATE INDEX idx_transactions_ticker ON transactions(ticker_symbol);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_market_prices_ticker ON market_prices(ticker_symbol);
CREATE INDEX idx_market_prices_updated ON market_prices(last_updated);
CREATE INDEX idx_tax_rates_year_status ON tax_rates(tax_year, filing_status);

-- Investor profile indexes
CREATE INDEX idx_investor_profiles_filing_status ON investor_profiles(filing_status);
CREATE INDEX idx_investor_profiles_state ON investor_profiles(state_of_residence);

-- State tax rate indexes
CREATE INDEX idx_state_tax_rates_state_year ON state_tax_rates(state_code, tax_year);
CREATE INDEX idx_state_tax_rates_active ON state_tax_rates(active);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_portfolios_updated_at 
    BEFORE UPDATE ON portfolios 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at 
    BEFORE UPDATE ON transactions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_investor_profiles_updated_at 
    BEFORE UPDATE ON investor_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();