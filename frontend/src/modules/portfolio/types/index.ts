/**
 * TypeScript type definitions for Portfolio Manager application
 */

// Portfolio types
export interface Portfolio {
  id: number
  name: string
  type: 'real' | 'tracking' | 'retirement'
  description?: string
  created_at: string
  updated_at: string
}

// Transaction types
export interface Transaction {
  id: number
  portfolio_id: number
  stock_name: string
  ticker_symbol: string
  transaction_type: 'buy' | 'sell'
  quantity: number
  price_per_share: number
  transaction_date: string
  created_at: string
  updated_at: string
  
  // Calculated properties
  total_amount: number
  days_held: number
  is_long_term: boolean
}

// Market price types
export interface MarketPrice {
  id: number
  ticker_symbol: string
  current_price: number
  last_updated: string
}

// Investor profile types
export interface InvestorProfile {
  id: number
  name: string
  annual_household_income: number
  filing_status: 'single' | 'married_joint' | 'head_of_household'
  state_of_residence: string
  local_tax_rate: number
  created_at: string
  updated_at: string
}

// Tax rate types
export interface TaxRate {
  id: number
  tax_year: number
  filing_status: string
  income_bracket_min?: number
  income_bracket_max?: number
  short_term_rate: number
  long_term_rate: number
  niit_rate: number
  active: boolean
}

export interface StateTaxRate {
  id: number
  state_code: string
  state_name: string
  tax_year: number
  capital_gains_rate: number
  income_tax_rate: number
  has_capital_gains_tax: boolean
  active: boolean
  last_updated: string
}

// Tax calculation types
export interface TaxCalculation {
  transaction_id: number
  current_value: number
  cost_basis: number
  capital_gain: number
  holding_period_days: number
  is_long_term: boolean
  
  // Tax breakdown
  federal_tax: number
  state_tax: number
  local_tax: number
  niit_tax: number
  total_tax: number
  
  // Decision support
  after_tax_proceeds: number
  break_even_loss_amount: number
  break_even_loss_percentage: number
}

// API response types
export interface ApiHealthResponse {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  service: string
  version: string
  database?: string
  portfolios_count?: number
}

// Form types for creating/updating entities
export interface CreatePortfolioForm {
  name: string
  type: 'real' | 'tracking' | 'retirement'
  description?: string
}

export interface CreateTransactionForm {
  portfolio_id: number
  stock_name: string
  ticker_symbol: string
  transaction_type: 'buy' | 'sell'
  quantity: number
  price_per_share: number
  transaction_date: string
}

export interface UpdateMarketPriceForm {
  ticker_symbol: string
  current_price: number
}

export interface UpdateInvestorProfileForm {
  name: string
  annual_household_income: number
  filing_status: 'single' | 'married_joint'
  state_of_residence: string
  local_tax_rate: number
}

// Component prop types
export interface TabComponentProps {
  isActive: boolean
  onActivate: () => void
}

// Utility types
export type SortDirection = 'asc' | 'desc'
export type TransactionType = 'buy' | 'sell'
export type PortfolioType = 'real' | 'tracking' | 'retirement'
export type FilingStatus = 'single' | 'married_joint'