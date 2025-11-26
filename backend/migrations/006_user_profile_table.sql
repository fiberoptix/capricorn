-- Migration: Create user_profile table for centralized profile data
-- Created: 2025-11-24
-- Purpose: Single source of truth for all user financial/personal data
-- Used by: Portfolio, Retirement, Finance modules

CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY DEFAULT 1,
    
    -- Section 1: Personal Information
    user VARCHAR(100) DEFAULT 'User',
    partner VARCHAR(100) DEFAULT 'Partner',
    user_age INTEGER DEFAULT 40,
    partner_age INTEGER DEFAULT 35,
    years_of_retirement INTEGER DEFAULT 30,
    user_years_to_retirement INTEGER DEFAULT 25,
    partner_years_to_retirement INTEGER DEFAULT 30,
    
    -- Section 2: Income Parameters
    user_salary DECIMAL(15,2) DEFAULT 100000.00,
    user_bonus_rate DECIMAL(5,4) DEFAULT 0.0500,
    user_raise_rate DECIMAL(5,4) DEFAULT 0.0500,
    partner_salary DECIMAL(15,2) DEFAULT 80000.00,
    partner_bonus_rate DECIMAL(5,4) DEFAULT 0.0500,
    partner_raise_rate DECIMAL(5,4) DEFAULT 0.0500,
    
    -- Section 3: Expense Parameters
    monthly_living_expenses DECIMAL(15,2) DEFAULT 6000.00,
    annual_discretionary_spending DECIMAL(15,2) DEFAULT 24000.00,
    annual_inflation_rate DECIMAL(5,4) DEFAULT 0.0400,
    
    -- Section 4: 401K Parameters
    user_401k_contribution DECIMAL(15,2) DEFAULT 12000.00,
    partner_401k_contribution DECIMAL(15,2) DEFAULT 0.00,
    user_employer_match DECIMAL(15,2) DEFAULT 1000.00,
    partner_employer_match DECIMAL(15,2) DEFAULT 0.00,
    user_current_401k_balance DECIMAL(15,2) DEFAULT 0.00,
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
    
    -- Section 6: Tax Parameters (includes Portfolio investor_profile fields)
    state VARCHAR(50) DEFAULT 'NY',
    local_tax_rate DECIMAL(5,4) DEFAULT 0.0100,
    filing_status VARCHAR(50) DEFAULT 'married_filing_jointly',
    -- Calculated rates (stored for display/reference)
    calculated_federal_rate DECIMAL(5,4),
    calculated_state_rate DECIMAL(5,4),
    calculated_total_rate DECIMAL(5,4),
    
    -- Section 7: Retirement Parameters
    retirement_growth_rate DECIMAL(5,4) DEFAULT 0.0500,
    withdrawal_rate DECIMAL(5,4) DEFAULT 0.0400,
    
    -- Section 8: Savings Strategy
    fixed_monthly_savings DECIMAL(15,2) DEFAULT 1000.00,
    percentage_of_leftover DECIMAL(5,4) DEFAULT 0.5000,
    savings_destination VARCHAR(20) DEFAULT 'trading', -- 'savings' or 'trading'
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Enforce single-user system
    CONSTRAINT single_user_profile CHECK (id = 1)
);

-- Create index for quick lookups (though only one row will ever exist)
CREATE INDEX IF NOT EXISTS idx_user_profile_id ON user_profile(id);

-- Insert default profile (single user system)
INSERT INTO user_profile (id) VALUES (1)
ON CONFLICT (id) DO NOTHING;

-- Add comment
COMMENT ON TABLE user_profile IS 'Single-user profile containing all financial and personal data for Portfolio, Retirement, and Finance modules';

