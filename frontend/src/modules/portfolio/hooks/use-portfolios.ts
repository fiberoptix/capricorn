/**
 * Portfolios Data Hooks
 * React Query hooks for portfolio management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, Portfolio } from '../lib/api-client'

// Query keys for consistent cache management
export const portfolioKeys = {
  all: ['portfolios'] as const,
  detail: (id: number) => ['portfolios', id] as const,
  transactions: (id: number) => ['portfolios', id, 'transactions'] as const,
}

// Get all portfolios
export function usePortfolios() {
  return useQuery({
    queryKey: portfolioKeys.all,
    queryFn: async () => {
      const response = await api.portfolios.getAll()
      if (response.error) {
        throw new Error(response.error)
      }
      const base = response.data || []
      // hydrate each portfolio with summary, market value, and break-even data for card display
      const enriched = await Promise.all(
        base.map(async (p: any) => {
          try {
            const [summaryResp, marketResp, breakEvenResp] = await Promise.all([
              api.portfolios.getSummary(p.id),
              api.portfolios.getMarketValue(p.id),
              api.breakEven.analyzePortfolio(p.id, 1), // Default to investor profile 1
            ])
            return {
              ...p,
              summary: summaryResp.data,
              market: marketResp.data,
              breakEven: breakEvenResp.data,
            }
          } catch {
            return p
          }
        })
      )
      return enriched
    },
    // Always pull fresh data when page/tab mounts or gains focus
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
  })
}

// Get portfolio by ID
export function usePortfolio(id: number) {
  return useQuery({
    queryKey: portfolioKeys.detail(id),
    queryFn: async () => {
      const response = await api.portfolios.getById(id)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
    enabled: id > 0,
    // ensure fresh data whenever viewing a portfolio
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
    staleTime: 0,
  })
}

// Get transactions for a portfolio
export function usePortfolioTransactions(portfolioId: number) {
  return useQuery({
    queryKey: portfolioKeys.transactions(portfolioId),
    queryFn: async () => {
      const response = await api.transactions.getByPortfolio(portfolioId)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data || []
    },
    enabled: portfolioId > 0,
    // Always pull fresh data when page/tab mounts or gains focus
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
  })
}

// Create portfolio mutation
export function useCreatePortfolio() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (portfolio: Omit<Portfolio, 'id' | 'created_at' | 'updated_at'>) => {
      const response = await api.portfolios.create(portfolio)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
    onSuccess: () => {
      // Invalidate portfolios list to refetch
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all })
    },
  })
}

// Update portfolio mutation
export function useUpdatePortfolio() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, ...portfolio }: { id: number } & Partial<Portfolio>) => {
      const response = await api.portfolios.update(id, portfolio)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
    onSuccess: (data) => {
      // Update the specific portfolio in cache
      if (data) {
        queryClient.setQueryData(portfolioKeys.detail(data.id), data)
        // Also invalidate the list to ensure consistency
        queryClient.invalidateQueries({ queryKey: portfolioKeys.all })
      }
    },
  })
}

// Delete portfolio mutation
export function useDeletePortfolio() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.portfolios.delete(id)
      if (response.error) {
        throw new Error(response.error)
      }
      return id
    },
    onSuccess: (deletedId) => {
      // Remove from cache and invalidate list
      queryClient.removeQueries({ queryKey: portfolioKeys.detail(deletedId) })
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all })
    },
  })
}