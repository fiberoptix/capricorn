-- Portfolio tables for Capricorn database (port 5003)
-- This creates portfolio functionality within Capricorn, not connecting to reference app

-- 1. Investor Profiles table
CREATE TABLE IF NOT EXISTS investor_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    annual_household_income DECIMAL(15, 2) NOT NULL,
    filing_status VARCHAR(50) NOT NULL CHECK (filing_status IN ('single', 'married_filing_jointly', 'married_filing_separately', 'head_of_household')),
    state_of_residence VARCHAR(2) NOT NULL,
    local_tax_rate DECIMAL(5, 4) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT check_positive_income CHECK (annual_household_income > 0),
    CONSTRAINT check_valid_local_tax CHECK (local_tax_rate >= 0 AND local_tax_rate <= 0.50)
);

-- 2. Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('real', 'tracking', 'retirement', '401k', 'IRA', 'Taxable', 'Roth IRA', 'SEP IRA', 'Brokerage')),
    description TEXT,
    cash_on_hand DECIMAL(15, 2) DEFAULT 0.00,
    investor_profile_id INTEGER REFERENCES investor_profiles(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Transactions table (renamed to portfolio_transactions to avoid conflict with finance transactions)
CREATE TABLE IF NOT EXISTS portfolio_transactions (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    stock_name VARCHAR(255) NOT NULL,
    ticker_symbol VARCHAR(10) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('buy', 'sell')),
    quantity DECIMAL(15, 4) NOT NULL CHECK (quantity > 0),
    price_per_share DECIMAL(15, 4) NOT NULL CHECK (price_per_share > 0),
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Market Prices table
CREATE TABLE IF NOT EXISTS market_prices (
    id SERIAL PRIMARY KEY,
    ticker_symbol VARCHAR(10) NOT NULL UNIQUE,
    current_price DECIMAL(15, 4) NOT NULL CHECK (current_price > 0),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tax Rates table
CREATE TABLE IF NOT EXISTS tax_rates (
    id SERIAL PRIMARY KEY,
    tax_year INTEGER NOT NULL,
    filing_status VARCHAR(50) NOT NULL,
    income_bracket_min DECIMAL(15, 2),
    income_bracket_max DECIMAL(15, 2),
    short_term_rate DECIMAL(5, 4) NOT NULL,
    long_term_rate DECIMAL(5, 4) NOT NULL,
    niit_rate DECIMAL(5, 4) DEFAULT 0.038,
    active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT uq_tax_rate_bracket UNIQUE(tax_year, filing_status, income_bracket_min)
);

-- 6. State Tax Rates table
CREATE TABLE IF NOT EXISTS state_tax_rates (
    id SERIAL PRIMARY KEY,
    state_code VARCHAR(2) NOT NULL,
    state_name VARCHAR(50) NOT NULL,
    tax_year INTEGER NOT NULL,
    capital_gains_rate DECIMAL(5, 4) NOT NULL CHECK (capital_gains_rate >= 0),
    income_tax_rate DECIMAL(5, 4) NOT NULL CHECK (income_tax_rate >= 0),
    has_capital_gains_tax BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_state_tax_year UNIQUE(state_code, tax_year)
);

-- Create indexes for better performance
CREATE INDEX idx_portfolios_name ON portfolios(name);
CREATE INDEX idx_portfolios_type ON portfolios(type);
CREATE INDEX idx_portfolios_investor ON portfolios(investor_profile_id);

CREATE INDEX idx_portfolio_transactions_portfolio ON portfolio_transactions(portfolio_id);
CREATE INDEX idx_portfolio_transactions_ticker ON portfolio_transactions(ticker_symbol);
CREATE INDEX idx_portfolio_transactions_date ON portfolio_transactions(transaction_date);
CREATE INDEX idx_portfolio_transactions_type ON portfolio_transactions(transaction_type);

CREATE INDEX idx_market_prices_ticker ON market_prices(ticker_symbol);
CREATE INDEX idx_market_prices_updated ON market_prices(last_updated);

CREATE INDEX idx_investor_profiles_state ON investor_profiles(state_of_residence);
CREATE INDEX idx_investor_profiles_filing ON investor_profiles(filing_status);

CREATE INDEX idx_tax_rates_year_filing ON tax_rates(tax_year, filing_status);
CREATE INDEX idx_tax_rates_active ON tax_rates(active);

CREATE INDEX idx_state_tax_rates_code ON state_tax_rates(state_code);
CREATE INDEX idx_state_tax_rates_year ON state_tax_rates(tax_year);
CREATE INDEX idx_state_tax_rates_active ON state_tax_rates(active);

-- Add update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolio_transactions_updated_at BEFORE UPDATE ON portfolio_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_investor_profiles_updated_at BEFORE UPDATE ON investor_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
