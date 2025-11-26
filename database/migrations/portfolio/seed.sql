-- Portfolio Manager Database Seed Data
-- Policy: Seed ONLY configuration/reference data needed for calculations.
-- Do NOT insert any user/sample data (investor profiles, portfolios, transactions, market prices).

-- Insert 2025 federal tax rates (based on current tax law)
INSERT INTO tax_rates (tax_year, filing_status, income_bracket_min, income_bracket_max, short_term_rate, long_term_rate, niit_rate) VALUES
-- Single filers - Short-term rates (ordinary income)
(2025, 'single', 0, 11600, 0.10, 0.00, 0.038),
(2025, 'single', 11601, 47150, 0.12, 0.00, 0.038),
(2025, 'single', 47151, 100525, 0.22, 0.15, 0.038),
(2025, 'single', 100526, 191950, 0.24, 0.15, 0.038),
(2025, 'single', 191951, 243725, 0.32, 0.15, 0.038),
(2025, 'single', 243726, 533400, 0.35, 0.15, 0.038),
(2025, 'single', 533401, null, 0.37, 0.20, 0.038),

-- Married Filing Jointly - Short-term rates (ordinary income)
(2025, 'married_joint', 0, 23200, 0.10, 0.00, 0.038),
(2025, 'married_joint', 23201, 94300, 0.12, 0.00, 0.038),  
(2025, 'married_joint', 94301, 201050, 0.22, 0.15, 0.038),
(2025, 'married_joint', 201051, 383900, 0.24, 0.15, 0.038),
(2025, 'married_joint', 383901, 487450, 0.32, 0.15, 0.038),
(2025, 'married_joint', 487451, 600050, 0.35, 0.15, 0.038),
(2025, 'married_joint', 600051, null, 0.37, 0.20, 0.038),

-- Head of Household - Short-term rates (ordinary income)
(2025, 'head_of_household', 0, 16550, 0.10, 0.00, 0.038),
(2025, 'head_of_household', 16551, 63100, 0.12, 0.00, 0.038),
(2025, 'head_of_household', 63101, 100500, 0.22, 0.15, 0.038),
(2025, 'head_of_household', 100501, 191950, 0.24, 0.15, 0.038),
(2025, 'head_of_household', 191951, 243700, 0.32, 0.15, 0.038),
(2025, 'head_of_household', 243701, 566700, 0.35, 0.15, 0.038),
(2025, 'head_of_household', 566701, null, 0.37, 0.20, 0.038);

-- Insert 2025 state tax rates (sample of major states)
INSERT INTO state_tax_rates (state_code, state_name, tax_year, capital_gains_rate, income_tax_rate, has_capital_gains_tax) VALUES
-- High-tax states
('NY', 'New York', 2025, 0.133, 0.133, true),           -- 13.3% top rate
('CA', 'California', 2025, 0.133, 0.133, true),         -- 13.3% top rate
('NJ', 'New Jersey', 2025, 0.1075, 0.1075, true),       -- 10.75% top rate
('CT', 'Connecticut', 2025, 0.0699, 0.0699, true),      -- 6.99% top rate
('MA', 'Massachusetts', 2025, 0.05, 0.05, true),        -- 5% flat rate
('IL', 'Illinois', 2025, 0.0495, 0.0495, true),         -- 4.95% flat rate

-- No state income tax states
('FL', 'Florida', 2025, 0.00, 0.00, false),             -- No state tax
('TX', 'Texas', 2025, 0.00, 0.00, false),               -- No state tax
('NV', 'Nevada', 2025, 0.00, 0.00, false),              -- No state tax
('WA', 'Washington', 2025, 0.00, 0.00, false),          -- No state tax
('TN', 'Tennessee', 2025, 0.00, 0.00, false),           -- No state tax
('WY', 'Wyoming', 2025, 0.00, 0.00, false),             -- No state tax
('SD', 'South Dakota', 2025, 0.00, 0.00, false),        -- No state tax
('AK', 'Alaska', 2025, 0.00, 0.00, false),              -- No state tax
('NH', 'New Hampshire', 2025, 0.00, 0.00, false),       -- No state tax

-- Medium-tax states
('PA', 'Pennsylvania', 2025, 0.0307, 0.0307, true),     -- 3.07% flat rate
('OH', 'Ohio', 2025, 0.0385, 0.0385, true),             -- 3.85% top rate
('MI', 'Michigan', 2025, 0.0425, 0.0425, true),         -- 4.25% flat rate
('CO', 'Colorado', 2025, 0.044, 0.044, true),           -- 4.4% flat rate
('NC', 'North Carolina', 2025, 0.0475, 0.0475, true),   -- 4.75% flat rate
('GA', 'Georgia', 2025, 0.0575, 0.0575, true);          -- 5.75% top rate
