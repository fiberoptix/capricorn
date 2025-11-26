/**
 * Break-Even Analysis Hooks
 * React Query hooks for our Phase 2 crown jewel feature
 */

import { useQuery, useMutation } from '@tanstack/react-query'
import { api, BreakEvenAnalysis, PortfolioBreakEvenSummary } from '../lib/api-client'

// Query keys for break-even analysis
export const breakEvenKeys = {
  transaction: (transactionId: number, profileId: number) => 
    ['break-even', 'transaction', transactionId, profileId] as const,
  portfolio: (portfolioId: number, profileId: number) => 
    ['break-even', 'portfolio', portfolioId, profileId] as const,
  ticker: (ticker: string, profileId: number) => 
    ['break-even', 'ticker', ticker, profileId] as const,
}

// Analyze single transaction break-even
export function useTransactionBreakEven(
  transactionId: number,
  investorProfileId: number,
  currentPrice?: number
) {
  return useQuery({
    queryKey: breakEvenKeys.transaction(transactionId, investorProfileId),
    queryFn: async () => {
      const response = await api.breakEven.analyzeTransaction(
        transactionId,
        investorProfileId,
        currentPrice
      )
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
    enabled: transactionId > 0 && investorProfileId > 0,
    // Always refresh price-sensitive analysis when page/tab opens
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
    staleTime: 0,
  })
}

// Analyze portfolio break-even
export function usePortfolioBreakEven(portfolioId: number, investorProfileId: number) {
  return useQuery({
    queryKey: breakEvenKeys.portfolio(portfolioId, investorProfileId),
    queryFn: async () => {
      const response = await api.breakEven.analyzePortfolio(portfolioId, investorProfileId)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
    enabled: portfolioId > 0 && investorProfileId > 0,
    // Ensure analytics reflect latest market prices on open/focus
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
    staleTime: 0,
  })
}

// Analyze ticker break-even across all portfolios
export function useTickerBreakEven(ticker: string, investorProfileId: number) {
  return useQuery({
    queryKey: breakEvenKeys.ticker(ticker, investorProfileId),
    queryFn: async () => {
      const response = await api.breakEven.analyzeTicker(ticker, investorProfileId)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
    enabled: !!ticker && investorProfileId > 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
    staleTime: 0,
  })
}

// Mutation for triggering break-even analysis with custom parameters
export function useBreakEvenAnalysis() {
  return useMutation({
    mutationFn: async ({
      type,
      id,
      investorProfileId,
      currentPrice,
    }: {
      type: 'transaction' | 'portfolio' | 'ticker'
      id: number | string
      investorProfileId: number
      currentPrice?: number
    }) => {
      let response
      switch (type) {
        case 'transaction':
          response = await api.breakEven.analyzeTransaction(
            id as number,
            investorProfileId,
            currentPrice
          )
          break
        case 'portfolio':
          response = await api.breakEven.analyzePortfolio(id as number, investorProfileId)
          break
        case 'ticker':
          response = await api.breakEven.analyzeTicker(id as string, investorProfileId)
          break
        default:
          throw new Error('Invalid analysis type')
      }

      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
  })
}

// Helper function to get recommendation color
export function getRecommendationColor(recommendation: string): string {
  switch (recommendation) {
    case 'hold':
      return 'text-green-600 bg-green-50'
    case 'monitor_closely':
      return 'text-yellow-600 bg-yellow-50'
    case 'consider_selling':
      return 'text-red-600 bg-red-50'
    default:
      return 'text-gray-600 bg-gray-50'
  }
}

// Helper function to format recommendation display
export function formatRecommendation(recommendation: string): string {
  switch (recommendation) {
    case 'hold':
      return 'Hold'
    case 'monitor_closely':
      return 'Monitor Closely'
    case 'consider_selling':
      return 'Consider Selling'
    default:
      return 'Unknown'
  }
}