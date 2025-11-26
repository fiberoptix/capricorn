-- Capricorn Finance Platform - Initial Database Schema
-- Phase 0: Minimal schema for development environment
-- Password: capricorn2025

-- Create database (handled by Docker, but included for reference)
-- CREATE DATABASE capricorn_db;

-- ============================================
-- CORE TABLES
-- ============================================

-- NOTE: user_profile table is created by 002_user_profile_complete.sql
-- with full schema matching Python model (50 columns)

-- Categories (from Finance Manager)
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_type VARCHAR(20) NOT NULL,  -- 'expense' or 'income'
    parent_id INTEGER REFERENCES categories(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts (Banking accounts from Finance Manager)
-- NOTE: user_id FK will be added after user_profile table is created
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,  -- Single-user system
    name VARCHAR(200) NOT NULL,
    account_type VARCHAR(50) NOT NULL,  -- 'checking', 'savings', 'credit_card'
    account_number VARCHAR(100),
    bank_name VARCHAR(100),
    balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    credit_limit DECIMAL(12,2),
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions (Finance Manager banking transactions)
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,  -- Single-user system
    account_id INTEGER NOT NULL,
    category_id INTEGER,
    
    description VARCHAR(500) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,  -- 'debit' or 'credit'
    is_processed BOOLEAN NOT NULL DEFAULT false,  -- True if auto-tagged
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    CONSTRAINT fk_transactions_account FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    CONSTRAINT fk_transactions_category FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Create indexes for transactions
CREATE INDEX IF NOT EXISTS idx_transaction_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transaction_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transaction_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transaction_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transaction_type ON transactions(transaction_type);

-- Budgets (Finance Manager budget tracking by category)
CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,  -- Single-user system
    category_id INTEGER NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    period VARCHAR(20) NOT NULL DEFAULT 'monthly',  -- 'monthly' or 'yearly'
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys (added after user_profile and categories exist)
    CONSTRAINT fk_budgets_category FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Create indexes for budgets
CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_budgets_category ON budgets(category_id);

-- ============================================
-- SEED DATA
-- ============================================

-- NOTE: User profile is created by 002_user_profile_complete.sql

-- Insert default categories
INSERT INTO categories (name, category_type, is_active) VALUES
    ('Salary', 'income', true),
    ('Investment Income', 'income', true),
    ('Groceries', 'expense', true),
    ('Dining', 'expense', true),
    ('Transportation', 'expense', true),
    ('Housing', 'expense', true),
    ('Utilities', 'expense', true),
    ('Healthcare', 'expense', true),
    ('Entertainment', 'expense', true),
    ('Shopping', 'expense', true),
    ('Transfer', 'expense', true),
    ('Uncategorized', 'expense', true)
ON CONFLICT DO NOTHING;

-- Create indexes for categories and accounts
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);
CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(category_type);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active);
CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_active ON accounts(is_active);

-- ============================================
-- VIEWS
-- ============================================

-- Create view for active accounts
CREATE OR REPLACE VIEW active_accounts AS
SELECT * FROM accounts WHERE is_active = true;

-- Create view for active categories  
CREATE OR REPLACE VIEW active_categories AS
SELECT * FROM categories WHERE is_active = true;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at (user_profile trigger is in 002_user_profile_complete.sql)

CREATE TRIGGER update_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- GRANTS (if needed)
-- ============================================

-- Grant permissions to capricorn user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO capricorn;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO capricorn;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Capricorn database schema initialized successfully!';
    RAISE NOTICE '   - 5 core tables created (categories, accounts, transactions, budgets, user_profile)';
    RAISE NOTICE '   - 12 default categories seeded';
    RAISE NOTICE '   - Indexes and triggers configured';
END $$;

