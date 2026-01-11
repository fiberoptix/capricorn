/**
 * Portfolio Manager API Client
 * TypeScript client for interacting with our FastAPI backend
 * Handles all 40+ endpoints with proper error handling and type safety
 */

import { API_V1_URL } from '../../../config/api';

// Base configuration (dynamic based on hostname)
const API_BASE_URL = `${API_V1_URL}/portfolio`

// Response wrapper for consistent error handling
interface ApiResponse<T> {
  data?: T
  error?: string
  status: number
}

// Core data types matching our backend models
export interface Portfolio {
  id: number
  name: string
  description?: string
  type: 'real' | 'tracking' | 'retirement' | '401k' | 'IRA' | 'Taxable' | string  // Allow string for compatibility with backend
  cash_on_hand?: number
  created_at: string
  updated_at: string
}

export interface PortfolioSummary {
  portfolio_id: number
  name: string
  type: string
  description?: string
  total_transactions: number
  buy_transactions: number
  sell_transactions: number
  unique_stocks: number
  created_at: string
  updated_at: string
}

export interface PortfolioMarketValue {
  portfolio_id: number
  investment_value: number
  cash_on_hand: number
  total_market_value: number
  total_cost_basis: number
  total_gain_loss: number
  total_gain_loss_percent: number
}

export interface Transaction {
  id: number
  portfolio_id: number
  ticker: string
  transaction_type: 'buy' | 'sell'
  quantity: number
  price_per_share: number
  transaction_date: string
  created_at: string
  updated_at: string
}

export interface MarketPrice {
  id: number
  ticker: string
  current_price: number
  last_updated: string
}

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

export interface BreakEvenAnalysis {
  transaction_id: number
  current_price: number
  current_value: number
  gain_loss: number
  holding_period_days: number
  is_long_term: boolean
  total_tax_owed: number
  after_tax_proceeds: number
  break_even_price: number
  price_drop_needed: number
  percentage_drop_needed: number
  recommendation: 'hold' | 'monitor_closely' | 'consider_selling'
}

export interface PortfolioBreakEvenSummary {
  total_current_value: number
  total_tax_if_all_sold: number
  total_after_tax_proceeds: number
  average_break_even_percentage: number
  recommendations: {
    hold_count: number
    monitor_count: number
    consider_selling_count: number
  }
}

// Generic API request handler
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    const data = await response.json()

    if (!response.ok) {
      return {
        error: data.detail || `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
      }
    }

    return {
      data,
      status: response.status,
    }
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      status: 0,
    }
  }
}

// Health and System endpoints
export const healthApi = {
  getHealth: () => apiRequest<{
    status: string
    service: string
    database: string
    timestamp: string
    portfolios_count: number
  }>('/health'),
}

// Portfolio endpoints
export const portfolioApi = {
  getAll: async () => {
    const response = await apiRequest<{count: number, portfolios: Portfolio[]}>('/portfolios')
    if (response.error) {
      return { error: response.error, status: response.status }
    }
    // Extract just the portfolios array from the response
    return { data: response.data?.portfolios || [], status: response.status }
  },
  
  getById: (id: number) => 
    apiRequest<Portfolio>(`/portfolios/${id}`),
  
  getSummary: (id: number) =>
    apiRequest<PortfolioSummary>(`/portfolios/${id}/summary`),
  
  getMarketValue: (id: number) =>
    apiRequest<PortfolioMarketValue>(`/portfolios/${id}/market-value`),
  
  create: (portfolio: Omit<Portfolio, 'id' | 'created_at' | 'updated_at'>) =>
    apiRequest<Portfolio>('/portfolios', {
      method: 'POST',
      body: JSON.stringify(portfolio),
    }),
  
  update: (id: number, portfolio: Partial<Portfolio>) =>
    apiRequest<Portfolio>(`/portfolios/${id}`, {
      method: 'PUT',
      body: JSON.stringify(portfolio),
    }),
  
  updateCash: (id: number, cashAmount: number) =>
    apiRequest<{id: number, cash_on_hand: number, message: string}>(`/portfolios/${id}/cash`, {
      method: 'PUT',
      body: JSON.stringify({ cash_on_hand: cashAmount }),
    }),
  
  delete: (id: number) =>
    apiRequest<void>(`/portfolios/${id}`, {
      method: 'DELETE',
    }),
}

// Transaction endpoints
export const transactionApi = {
  getAll: async () => {
    const response = await apiRequest<{count: number, transactions: Transaction[]}>('/transactions')
    if (response.error) {
      return { error: response.error, status: response.status }
    }
    // Extract just the transactions array from the response
    return { data: response.data?.transactions || [], status: response.status }
  },
  
  getById: (id: number) =>
    apiRequest<Transaction>(`/transactions/${id}`),
  
  getByPortfolio: async (portfolioId: number) => {
    const response = await apiRequest<{count: number, transactions: Transaction[]}>(`/transactions?portfolio_id=${portfolioId}`)
    if (response.error) {
      return { error: response.error, status: response.status }
    }
    // Extract just the transactions array from the response
    return { data: response.data?.transactions || [], status: response.status }
  },
  
  create: (transaction: Omit<Transaction, 'id' | 'created_at' | 'updated_at'>) =>
    apiRequest<Transaction>('/transactions', {
      method: 'POST',
      body: JSON.stringify(transaction),
    }),
  
  update: (id: number, transaction: Partial<Transaction>) =>
    apiRequest<Transaction>(`/transactions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(transaction),
    }),
  
  delete: (id: number) =>
    apiRequest<void>(`/transactions/${id}`, {
      method: 'DELETE',
    }),
}

// Market Price endpoints
export const marketPriceApi = {
  getAll: async () => {
    const response = await apiRequest<{count: number, prices: MarketPrice[]}>('/market-prices')
    if (response.error) {
      return { error: response.error, status: response.status }
    }
    // Extract just the prices array from the response
    return { data: response.data?.prices || [], status: response.status }
  },
  
  getByTicker: (ticker: string) =>
    apiRequest<MarketPrice>(`/market-prices/${ticker}`),
  
  update: (ticker: string, price: number) =>
    apiRequest<MarketPrice>(`/market-prices/${ticker}`, {
      method: 'PUT',
      body: JSON.stringify({ current_price: price }),
    }),
  
  bulkUpdate: (updates: { ticker: string; current_price: number }[]) =>
    apiRequest<MarketPrice[]>('/market-prices/bulk-update', {
      method: 'POST',
      body: JSON.stringify(updates),
    }),
  
  refresh: (force: boolean = false) =>
    apiRequest<{
      updated_count: number
      updated_symbols: string[]
      timestamp: string
      market_hours: boolean
    }>('/market-prices/refresh', {
      method: 'POST',
      body: JSON.stringify({ force }),
    }),
  
  getConfig: () =>
    apiRequest<any>('/market-prices/config'),
  
  resetToPortfolioHoldings: () =>
    apiRequest<{
      success: boolean
      cleared: number
      created: number
      tickers: string[]
      message: string
    }>('/market-prices/reset-to-portfolio', {
      method: 'POST',
    }),
}

// Investor Profile endpoints (single-user system)
export const investorProfileApi = {
  getAll: async () => {
    // Single-user system - only one profile with ID=1
    const response = await apiRequest<InvestorProfile>('/investor-profile')
    if (response.error) {
      return { error: response.error, status: response.status }
    }
    // Return as array for compatibility
    const profiles = response.data ? [response.data] : []
    return { data: profiles, status: response.status }
  },

  getById: (id: number) => 
    // Always returns profile ID=1 in single-user system
    apiRequest<InvestorProfile>(`/investor-profile`),
  
  create: (profile: Omit<InvestorProfile, 'id' | 'created_at' | 'updated_at'>) =>
    // Single-user system doesn't really create - it updates the single profile
    apiRequest<InvestorProfile>('/investor-profile', {
      method: 'PUT',
      body: JSON.stringify(profile),
    }),
  
  update: (id: number, profile: Partial<InvestorProfile>) => 
    // Always updates profile ID=1 in single-user system
    apiRequest<InvestorProfile>(`/investor-profile`, {
      method: 'PUT',
      body: JSON.stringify(profile),
    }),

  delete: (id: number) =>
    // Single-user system doesn't support delete
    Promise.resolve({ data: undefined, status: 200 }),
  
  calculateProgressiveTax: (
    profileId: number,
    additionalIncome: number,
    isCapitalGains: boolean = true,
    isLongTerm: boolean = true
  ) =>
    apiRequest<{
      additional_income: number
      is_capital_gains: boolean
      is_long_term: boolean
      federal_tax: number
      effective_rate: number
      marginal_rate: number
      tax_brackets: any[]
    }>(`/investor-profile/calculate-capital-gains-tax`, {
      method: 'POST',
      body: JSON.stringify({
        capital_gains: additionalIncome,
        is_long_term: isLongTerm,
      }),
    }),
  
  getTaxSettings: () =>
    apiRequest<any>('/investor-profile/tax-settings'),
  
  getTaxBrackets: () =>
    apiRequest<any>('/investor-profile/tax-brackets'),
}

// Break-Even Analysis endpoints (Phase 2 crown jewel!)
export const breakEvenApi = {
  analyzeTransaction: (transactionId: number, investorProfileId: number, currentPrice?: number) =>
    apiRequest<BreakEvenAnalysis>(`/break-even/transaction/${transactionId}`, {
      method: 'POST',
      body: JSON.stringify({
        investor_profile_id: investorProfileId,
        current_price: currentPrice,
      }),
    }),
  
  analyzePortfolio: async (portfolioId: number, investorProfileId: number) => {
    // Call backend and normalize to the UI's expected shape
    const resp = await apiRequest<any>(`/break-even/portfolio/${portfolioId}`, {
      method: 'POST',
      body: JSON.stringify({ investor_profile_id: investorProfileId }),
    })
    if (resp.error) return resp as any

    const raw = resp.data || {}
    // Backend returns { analysis: { [ticker]: analysisObj }, portfolio_summary: {...} }
    const transactions: any[] = Array.isArray(raw.transactions)
      ? raw.transactions
      : raw.analysis
        ? Object.values(raw.analysis)
        : []

    // Compute total_current_value for summary if not provided
    const total_current_value = transactions.reduce((sum, t: any) => {
      const current = t?.financial_analysis?.current_value ?? t?.current_value ?? 0
      return sum + (typeof current === 'number' ? current : Number(current) || 0)
    }, 0)

    const portfolio_summary: PortfolioBreakEvenSummary = {
      total_current_value,
      total_tax_if_all_sold: raw?.portfolio_summary?.total_tax_if_all_sold ?? 0,
      total_after_tax_proceeds: raw?.portfolio_summary?.total_after_tax_proceeds ?? 0,
      average_break_even_percentage: raw?.portfolio_summary?.average_break_even_percentage ?? 0,
      recommendations: raw?.portfolio_summary?.recommendations ?? {
        hold_count: 0,
        monitor_count: 0,
        consider_selling_count: 0,
      },
    }

    return {
      data: { portfolio_summary, transactions },
      status: resp.status,
    }
  },
  
  analyzeTicker: (ticker: string, investorProfileId: number) =>
    apiRequest<{
      ticker: string
      ticker_summary: PortfolioBreakEvenSummary
      transactions: BreakEvenAnalysis[]
    }>(`/break-even/ticker/${ticker}`, {
      method: 'POST',
      body: JSON.stringify({
        investor_profile_id: investorProfileId,
      }),
    }),
}

// State Tax endpoints
export const stateTaxApi = {
  // Fetch rates/info for a specific state
  getRatesForState: (stateCode: string) =>
    apiRequest<{
      state_code: string
      name: string
      capital_gains_rate: number
      notes?: string
    }>(`/state-tax/rates/${stateCode}`),
}

// Comprehensive Tax endpoints
export const comprehensiveTaxApi = {
  calculateTotal: (
    investorProfileId: number,
    gainsType: 'short_term' | 'long_term',
    capitalGainsAmount: number
  ) =>
    apiRequest<{
      federal_tax: number
      state_tax: number
      local_tax: number
      total_tax: number
      effective_rate: number
    }>('/comprehensive-tax/calculate', {
      method: 'POST',
      body: JSON.stringify({
        investor_profile_id: investorProfileId,
        gains_type: gainsType,
        capital_gains_amount: capitalGainsAmount,
      }),
    }),
}

// Export all APIs as a single object for convenience
export const api = {
  health: healthApi,
  portfolios: portfolioApi,
  transactions: transactionApi,
  marketPrices: marketPriceApi,
  investorProfiles: investorProfileApi,
  breakEven: breakEvenApi,
  stateTax: stateTaxApi,
  comprehensiveTax: comprehensiveTaxApi,
}

export default api