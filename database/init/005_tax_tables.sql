-- Migration: Create comprehensive tax tables for Tax Service API
-- Created: 2025-11-23
-- Purpose: Store all tax brackets, deductions, and rates for accurate tax calculations

-- Federal income tax brackets
CREATE TABLE IF NOT EXISTS federal_tax_brackets (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    filing_status VARCHAR(50) NOT NULL,
    bracket_min DECIMAL(12, 2) NOT NULL,
    bracket_max DECIMAL(12, 2),  -- NULL for highest bracket
    rate DECIMAL(5, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, filing_status, bracket_min)
);

-- State income tax brackets  
CREATE TABLE IF NOT EXISTS state_tax_brackets (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    filing_status VARCHAR(50) NOT NULL,
    bracket_min DECIMAL(12, 2) NOT NULL,
    bracket_max DECIMAL(12, 2),  -- NULL for highest bracket
    rate DECIMAL(5, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, state_code, filing_status, bracket_min)
);

-- Standard deductions
CREATE TABLE IF NOT EXISTS standard_deductions (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    filing_status VARCHAR(50) NOT NULL,
    federal_amount DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, filing_status)
);

-- State standard deductions
CREATE TABLE IF NOT EXISTS state_standard_deductions (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    filing_status VARCHAR(50) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, state_code, filing_status)
);

-- Long-term capital gains brackets
CREATE TABLE IF NOT EXISTS capital_gains_brackets (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    filing_status VARCHAR(50) NOT NULL,
    bracket_min DECIMAL(12, 2) NOT NULL,
    bracket_max DECIMAL(12, 2),  -- NULL for highest bracket
    rate DECIMAL(5, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, filing_status, bracket_min)
);

-- NIIT thresholds
CREATE TABLE IF NOT EXISTS niit_thresholds (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    filing_status VARCHAR(50) NOT NULL,
    threshold DECIMAL(12, 2) NOT NULL,
    rate DECIMAL(5, 4) NOT NULL DEFAULT 0.038,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, filing_status)
);

-- Create indexes for performance
CREATE INDEX idx_federal_brackets_lookup ON federal_tax_brackets(year, filing_status);
CREATE INDEX idx_state_brackets_lookup ON state_tax_brackets(year, state_code, filing_status);
CREATE INDEX idx_capital_gains_lookup ON capital_gains_brackets(year, filing_status);

-- ============================================================================
-- LOAD 2025 TAX DATA
-- ============================================================================

-- Clear existing 2025 data (if any)
DELETE FROM federal_tax_brackets WHERE year = 2025;
DELETE FROM state_tax_brackets WHERE year = 2025;
DELETE FROM standard_deductions WHERE year = 2025;
DELETE FROM state_standard_deductions WHERE year = 2025;
DELETE FROM capital_gains_brackets WHERE year = 2025;
DELETE FROM niit_thresholds WHERE year = 2025;

-- ============================================================================
-- FEDERAL TAX BRACKETS 2025
-- Source: IRS.gov Rev. Proc. 2024-40
-- ============================================================================

-- Married Filing Jointly
INSERT INTO federal_tax_brackets (year, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'married_filing_jointly', 0, 23200, 0.10),
(2025, 'married_filing_jointly', 23200, 94300, 0.12),
(2025, 'married_filing_jointly', 94300, 201050, 0.22),
(2025, 'married_filing_jointly', 201050, 383900, 0.24),
(2025, 'married_filing_jointly', 383900, 487450, 0.32),
(2025, 'married_filing_jointly', 487450, 731200, 0.35),
(2025, 'married_filing_jointly', 731200, NULL, 0.37);

-- Single
INSERT INTO federal_tax_brackets (year, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'single', 0, 11600, 0.10),
(2025, 'single', 11600, 47150, 0.12),
(2025, 'single', 47150, 100525, 0.22),
(2025, 'single', 100525, 191950, 0.24),
(2025, 'single', 191950, 243725, 0.32),
(2025, 'single', 243725, 609350, 0.35),
(2025, 'single', 609350, NULL, 0.37);

-- Head of Household
INSERT INTO federal_tax_brackets (year, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'head_of_household', 0, 17000, 0.10),
(2025, 'head_of_household', 17000, 64850, 0.12),
(2025, 'head_of_household', 64850, 103350, 0.22),
(2025, 'head_of_household', 103350, 197300, 0.24),
(2025, 'head_of_household', 197300, 243700, 0.32),
(2025, 'head_of_household', 243700, 609350, 0.35),
(2025, 'head_of_household', 609350, NULL, 0.37);

-- Married Filing Separately
INSERT INTO federal_tax_brackets (year, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'married_filing_separately', 0, 11600, 0.10),
(2025, 'married_filing_separately', 11600, 47150, 0.12),
(2025, 'married_filing_separately', 47150, 100525, 0.22),
(2025, 'married_filing_separately', 100525, 191950, 0.24),
(2025, 'married_filing_separately', 191950, 243725, 0.32),
(2025, 'married_filing_separately', 243725, 365600, 0.35),
(2025, 'married_filing_separately', 365600, NULL, 0.37);

-- ============================================================================
-- STANDARD DEDUCTIONS 2025
-- Source: IRS.gov Rev. Proc. 2024-40
-- ============================================================================

INSERT INTO standard_deductions (year, filing_status, federal_amount) VALUES
(2025, 'married_filing_jointly', 29200),
(2025, 'single', 14600),
(2025, 'head_of_household', 21900),
(2025, 'married_filing_separately', 14600);

-- ============================================================================
-- LONG-TERM CAPITAL GAINS BRACKETS 2025
-- Source: IRS.gov
-- ============================================================================

-- Married Filing Jointly
INSERT INTO capital_gains_brackets (year, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'married_filing_jointly', 0, 94050, 0.00),
(2025, 'married_filing_jointly', 94050, 583750, 0.15),
(2025, 'married_filing_jointly', 583750, NULL, 0.20);

-- Single
INSERT INTO capital_gains_brackets (year, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'single', 0, 47025, 0.00),
(2025, 'single', 47025, 518900, 0.15),
(2025, 'single', 518900, NULL, 0.20);

-- Head of Household
INSERT INTO capital_gains_brackets (year, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'head_of_household', 0, 63000, 0.00),
(2025, 'head_of_household', 63000, 551350, 0.15),
(2025, 'head_of_household', 551350, NULL, 0.20);

-- Married Filing Separately
INSERT INTO capital_gains_brackets (year, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'married_filing_separately', 0, 47025, 0.00),
(2025, 'married_filing_separately', 47025, 291850, 0.15),
(2025, 'married_filing_separately', 291850, NULL, 0.20);

-- ============================================================================
-- NIIT THRESHOLDS 2025
-- Source: IRS.gov (unchanged since 2013)
-- ============================================================================

INSERT INTO niit_thresholds (year, filing_status, threshold, rate) VALUES
(2025, 'married_filing_jointly', 250000, 0.038),
(2025, 'single', 200000, 0.038),
(2025, 'head_of_household', 200000, 0.038),
(2025, 'married_filing_separately', 125000, 0.038);

-- ============================================================================
-- NEW YORK STATE TAX BRACKETS 2025
-- Source: NY Department of Taxation and Finance
-- ============================================================================

-- Married Filing Jointly
INSERT INTO state_tax_brackets (year, state_code, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'NY', 'married_filing_jointly', 0, 17150, 0.04),
(2025, 'NY', 'married_filing_jointly', 17150, 23600, 0.045),
(2025, 'NY', 'married_filing_jointly', 23600, 27900, 0.0525),
(2025, 'NY', 'married_filing_jointly', 27900, 161550, 0.0585),
(2025, 'NY', 'married_filing_jointly', 161550, 323200, 0.0625),
(2025, 'NY', 'married_filing_jointly', 323200, 2155350, 0.0685),
(2025, 'NY', 'married_filing_jointly', 2155350, 5000000, 0.0965),
(2025, 'NY', 'married_filing_jointly', 5000000, 25000000, 0.103),
(2025, 'NY', 'married_filing_jointly', 25000000, NULL, 0.109);

-- Single
INSERT INTO state_tax_brackets (year, state_code, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'NY', 'single', 0, 8500, 0.04),
(2025, 'NY', 'single', 8500, 11700, 0.045),
(2025, 'NY', 'single', 11700, 13900, 0.0525),
(2025, 'NY', 'single', 13900, 80650, 0.0585),
(2025, 'NY', 'single', 80650, 215400, 0.0625),
(2025, 'NY', 'single', 215400, 1077550, 0.0685),
(2025, 'NY', 'single', 1077550, 5000000, 0.0965),
(2025, 'NY', 'single', 5000000, 25000000, 0.103),
(2025, 'NY', 'single', 25000000, NULL, 0.109);

-- Head of Household
INSERT INTO state_tax_brackets (year, state_code, filing_status, bracket_min, bracket_max, rate) VALUES
(2025, 'NY', 'head_of_household', 0, 12800, 0.04),
(2025, 'NY', 'head_of_household', 12800, 17650, 0.045),
(2025, 'NY', 'head_of_household', 17650, 20900, 0.0525),
(2025, 'NY', 'head_of_household', 20900, 107650, 0.0585),
(2025, 'NY', 'head_of_household', 107650, 269300, 0.0625),
(2025, 'NY', 'head_of_household', 269300, 1616450, 0.0685),
(2025, 'NY', 'head_of_household', 1616450, 5000000, 0.0965),
(2025, 'NY', 'head_of_household', 5000000, 25000000, 0.103),
(2025, 'NY', 'head_of_household', 25000000, NULL, 0.109);

-- NY State Standard Deductions
INSERT INTO state_standard_deductions (year, state_code, filing_status, amount) VALUES
(2025, 'NY', 'married_filing_jointly', 16050),
(2025, 'NY', 'single', 8000),
(2025, 'NY', 'head_of_household', 11200),
(2025, 'NY', 'married_filing_separately', 8000);

-- ============================================================================
-- Add trigger to update 'updated_at' timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_federal_tax_brackets_updated_at BEFORE UPDATE ON federal_tax_brackets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_state_tax_brackets_updated_at BEFORE UPDATE ON state_tax_brackets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_standard_deductions_updated_at BEFORE UPDATE ON standard_deductions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_state_standard_deductions_updated_at BEFORE UPDATE ON state_standard_deductions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_capital_gains_brackets_updated_at BEFORE UPDATE ON capital_gains_brackets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_niit_thresholds_updated_at BEFORE UPDATE ON niit_thresholds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
