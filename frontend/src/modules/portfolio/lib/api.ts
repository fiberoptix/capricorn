/**
 * API utilities for Portfolio Manager frontend
 * Handles communication with FastAPI backend
 */

import { API_V1_URL } from '../../../config/api';

// Dynamic API URL based on hostname (no more hardcoded localhost!)
const API_BASE_URL = `${API_V1_URL}/portfolio`

// API response wrapper interface
interface ApiResponse<T = any> {
  data?: T
  error?: string
  status: number
}

// API client class
class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      const data = await response.json()

      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.detail || data.message || 'API Error',
        status: response.status,
      }
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network Error',
        status: 0,
      }
    }
  }

  // Health check
  async checkHealth() {
    return this.request<{
      status: string
      service: string
      database: string
      portfolios_count: number
    }>('/health')
  }

  // Portfolio endpoints
  async getPortfolios() {
    return this.request('/api/portfolios')
  }

  async createPortfolio(portfolio: any) {
    return this.request('/api/portfolios', {
      method: 'POST',
      body: JSON.stringify(portfolio),
    })
  }

  // Transaction endpoints
  async getTransactions(portfolioId?: number) {
    const url = portfolioId ? `/api/transactions?portfolio_id=${portfolioId}` : '/api/transactions'
    return this.request(url)
  }

  async createTransaction(transaction: any) {
    return this.request('/api/transactions', {
      method: 'POST',
      body: JSON.stringify(transaction),
    })
  }

  // Market price endpoints
  async getMarketPrices() {
    return this.request('/api/market-prices')
  }

  async updateMarketPrice(ticker: string, price: number) {
    return this.request(`/api/market-prices/${ticker}`, {
      method: 'PUT',
      body: JSON.stringify({ current_price: price }),
    })
  }

  // Investor profile endpoints
  async getInvestorProfile() {
    return this.request('/api/investor-profile')
  }

  async updateInvestorProfile(profile: any) {
    return this.request('/api/investor-profile', {
      method: 'PUT',
      body: JSON.stringify(profile),
    })
  }

  // Tax calculation endpoints
  async calculateTaxes(transactionId: number) {
    return this.request(`/api/tax-calculation/${transactionId}`)
  }
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export types
export type { ApiResponse }