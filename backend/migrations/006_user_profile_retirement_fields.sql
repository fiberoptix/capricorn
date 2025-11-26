-- Migration: Add retirement/portfolio fields to existing user_profile table
-- Created: 2025-11-24
-- Purpose: Extend user_profile to be single source of truth for all modules
-- Strategy: Add new columns to existing Finance Manager user_profile table

-- Section 1: Personal Information
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS "user" VARCHAR(100) DEFAULT 'User';
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner VARCHAR(100) DEFAULT 'Partner';
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_age INTEGER DEFAULT 40;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner_age INTEGER DEFAULT 35;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS years_of_retirement INTEGER DEFAULT 30;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_years_to_retirement INTEGER DEFAULT 25;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner_years_to_retirement INTEGER DEFAULT 30;

-- Section 2: Income Parameters
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_salary DECIMAL(15,2) DEFAULT 100000.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_bonus_rate DECIMAL(5,4) DEFAULT 0.0500;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_raise_rate DECIMAL(5,4) DEFAULT 0.0500;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner_salary DECIMAL(15,2) DEFAULT 80000.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner_bonus_rate DECIMAL(5,4) DEFAULT 0.0500;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner_raise_rate DECIMAL(5,4) DEFAULT 0.0500;

-- Section 3: Expense Parameters
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS monthly_living_expenses DECIMAL(15,2) DEFAULT 6000.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS annual_discretionary_spending DECIMAL(15,2) DEFAULT 24000.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS annual_inflation_rate DECIMAL(5,4) DEFAULT 0.0400;

-- Section 4: 401K Parameters
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_401k_contribution DECIMAL(15,2) DEFAULT 12000.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner_401k_contribution DECIMAL(15,2) DEFAULT 0.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_employer_match DECIMAL(15,2) DEFAULT 1000.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner_employer_match DECIMAL(15,2) DEFAULT 0.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_current_401k_balance DECIMAL(15,2) DEFAULT 0.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner_current_401k_balance DECIMAL(15,2) DEFAULT 0.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_401k_growth_rate DECIMAL(5,4) DEFAULT 0.1000;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS partner_401k_growth_rate DECIMAL(5,4) DEFAULT 0.1000;

-- Section 5: Investment Accounts
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS current_ira_balance DECIMAL(15,2) DEFAULT 0.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS ira_return_rate DECIMAL(5,4) DEFAULT 0.1000;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS current_trading_balance DECIMAL(15,2) DEFAULT 0.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS trading_return_rate DECIMAL(5,4) DEFAULT 0.1000;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS current_savings_balance DECIMAL(15,2) DEFAULT 0.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS savings_return_rate DECIMAL(5,4) DEFAULT 0.0000;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS expected_inheritance DECIMAL(15,2) DEFAULT 0.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS inheritance_year INTEGER DEFAULT 20;

-- Section 6: Tax Parameters (includes Portfolio investor_profile fields)
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS state VARCHAR(50) DEFAULT 'NY';
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS local_tax_rate DECIMAL(5,4) DEFAULT 0.0100;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS filing_status VARCHAR(50) DEFAULT 'married_filing_jointly';
-- Calculated rates (stored for display/reference)
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS calculated_federal_rate DECIMAL(5,4);
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS calculated_state_rate DECIMAL(5,4);
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS calculated_total_rate DECIMAL(5,4);

-- Section 7: Retirement Parameters
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS retirement_growth_rate DECIMAL(5,4) DEFAULT 0.0500;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS withdrawal_rate DECIMAL(5,4) DEFAULT 0.0400;

-- Section 8: Savings Strategy
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS fixed_monthly_savings DECIMAL(15,2) DEFAULT 1000.00;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS percentage_of_leftover DECIMAL(5,4) DEFAULT 0.5000;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS savings_destination VARCHAR(20) DEFAULT 'trading'; -- 'savings' or 'trading'

-- Update existing row with defaults (Finance Manager created user_id=1)
UPDATE user_profile 
SET 
    "user" = COALESCE("user", 'User'),
    partner = COALESCE(partner, 'Partner'),
    user_age = COALESCE(user_age, 40),
    partner_age = COALESCE(partner_age, 35),
    state = COALESCE(state, 'NY'),
    filing_status = COALESCE(filing_status, 'married_filing_jointly')
WHERE id = 1;

-- Add comment
COMMENT ON TABLE user_profile IS 'Unified profile containing all financial and personal data for Finance, Portfolio, and Retirement modules';

