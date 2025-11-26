-- Capricorn User Profile - Complete Schema
-- This replaces/extends the basic user_profile from 001_schema.sql
-- Must match Python model: backend/app/models/user_profile.py

-- Drop the old basic table and recreate with full schema
DROP TABLE IF EXISTS user_profile CASCADE;

CREATE TABLE user_profile (
    id SERIAL PRIMARY KEY,
    
    -- Original Finance Manager fields (required by model)
    email VARCHAR(255) NOT NULL DEFAULT 'user@capricorn.local',
    first_name VARCHAR(100) NOT NULL DEFAULT 'Capricorn',
    last_name VARCHAR(100) NOT NULL DEFAULT 'User',
    
    -- Section 1: Personal Information
    "user" VARCHAR(100) DEFAULT 'User',
    partner VARCHAR(100) DEFAULT 'Partner',
    user_age INTEGER DEFAULT 30,
    partner_age INTEGER DEFAULT 30,
    years_of_retirement INTEGER DEFAULT 30,
    user_years_to_retirement INTEGER DEFAULT 35,
    partner_years_to_retirement INTEGER DEFAULT 35,
    
    -- Section 2: Income Parameters (single person defaults)
    user_salary DECIMAL(15,2) DEFAULT 100000.00,
    user_bonus_rate DECIMAL(5,4) DEFAULT 0.0500,
    user_raise_rate DECIMAL(5,4) DEFAULT 0.0500,
    partner_salary DECIMAL(15,2) DEFAULT 0.00,
    partner_bonus_rate DECIMAL(5,4) DEFAULT 0.0500,
    partner_raise_rate DECIMAL(5,4) DEFAULT 0.0500,
    
    -- Section 3: Expense Parameters
    monthly_living_expenses DECIMAL(15,2) DEFAULT 5000.00,
    annual_discretionary_spending DECIMAL(15,2) DEFAULT 10000.00,
    annual_inflation_rate DECIMAL(5,4) DEFAULT 0.0400,
    
    -- Section 4: 401K Parameters
    user_401k_contribution DECIMAL(15,2) DEFAULT 24000.00,
    partner_401k_contribution DECIMAL(15,2) DEFAULT 0.00,
    user_employer_match DECIMAL(15,2) DEFAULT 5000.00,
    partner_employer_match DECIMAL(15,2) DEFAULT 0.00,
    user_current_401k_balance DECIMAL(15,2) DEFAULT 100000.00,
    partner_current_401k_balance DECIMAL(15,2) DEFAULT 0.00,
    user_401k_growth_rate DECIMAL(5,4) DEFAULT 0.1000,
    partner_401k_growth_rate DECIMAL(5,4) DEFAULT 0.1000,
    
    -- Section 5: Investment Accounts
    current_ira_balance DECIMAL(15,2) DEFAULT 0.00,
    ira_return_rate DECIMAL(5,4) DEFAULT 0.1000,
    current_trading_balance DECIMAL(15,2) DEFAULT 0.00,
    trading_return_rate DECIMAL(5,4) DEFAULT 0.1000,
    current_savings_balance DECIMAL(15,2) DEFAULT 0.00,
    savings_return_rate DECIMAL(5,4) DEFAULT 0.0000,
    expected_inheritance DECIMAL(15,2) DEFAULT 0.00,
    inheritance_year INTEGER DEFAULT 20,
    
    -- Section 6: Tax Parameters
    state VARCHAR(50) DEFAULT 'NY',
    local_tax_rate DECIMAL(5,4) DEFAULT 0.0100,
    filing_status VARCHAR(50) DEFAULT 'single',
    calculated_federal_rate DECIMAL(5,4),
    calculated_state_rate DECIMAL(5,4),
    calculated_total_rate DECIMAL(5,4),
    
    -- Section 7: Retirement Parameters
    retirement_growth_rate DECIMAL(5,4) DEFAULT 0.0500,
    withdrawal_rate DECIMAL(5,4) DEFAULT 0.0400,
    
    -- Section 8: Savings Strategy
    fixed_monthly_savings DECIMAL(15,2) DEFAULT 1000.00,
    percentage_of_leftover DECIMAL(5,4) DEFAULT 0.5000,
    savings_destination VARCHAR(20) DEFAULT 'trading',
    
    -- Section 9: App Settings
    realtime_pricing_enabled BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create unique index on email
CREATE UNIQUE INDEX idx_user_profile_email ON user_profile(email);

-- Insert bootstrap user (single-user system, id=1)
INSERT INTO user_profile (id, email, first_name, last_name)
VALUES (1, 'user@capricorn.local', 'Capricorn', 'User')
ON CONFLICT (id) DO NOTHING;

-- Add update trigger
CREATE OR REPLACE FUNCTION update_user_profile_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_user_profile_updated_at ON user_profile;
CREATE TRIGGER trigger_user_profile_updated_at
    BEFORE UPDATE ON user_profile
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profile_timestamp();

-- Add foreign key constraints to tables created in 001_schema.sql
-- (now that user_profile exists)
ALTER TABLE accounts 
    ADD CONSTRAINT fk_accounts_user 
    FOREIGN KEY (user_id) REFERENCES user_profile(id);

ALTER TABLE transactions 
    ADD CONSTRAINT fk_transactions_user 
    FOREIGN KEY (user_id) REFERENCES user_profile(id);

ALTER TABLE budgets 
    ADD CONSTRAINT fk_budgets_user 
    FOREIGN KEY (user_id) REFERENCES user_profile(id);

-- Add trigger for budgets updated_at
CREATE TRIGGER update_budgets_updated_at
    BEFORE UPDATE ON budgets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ User profile table created with all 50 columns';
    RAISE NOTICE '   - Bootstrap user (id=1) inserted';
    RAISE NOTICE '   - FK constraints added to accounts, transactions, and budgets';
    RAISE NOTICE '   - Ready for Finance, Portfolio, Retirement modules';
END $$;

