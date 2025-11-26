/**
 * Transactions Data Hooks
 * React Query hooks for transaction management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, Transaction } from '../lib/api-client'

// Cross-feature keys for invalidations
const breakEvenRootKey = ['break-even'] as const
const marketPricesRootKey = ['market-prices'] as const
const portfoliosRootKey = ['portfolios'] as const

// Query keys for consistent cache management
export const transactionKeys = {
  all: ['transactions'] as const,
  byPortfolio: (portfolioId: number) => ['transactions', 'portfolio', portfolioId] as const,
  detail: (id: number) => ['transactions', id] as const,
}

// Get all transactions
export function useTransactions() {
  return useQuery({
    queryKey: transactionKeys.all,
    queryFn: async () => {
      const response = await api.transactions.getAll()
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data || []
    },
  })
}

// Get transactions for a specific portfolio
export function usePortfolioTransactions(portfolioId: number) {
  return useQuery({
    queryKey: transactionKeys.byPortfolio(portfolioId),
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

// Get transaction by ID
export function useTransaction(id: number) {
  return useQuery({
    queryKey: transactionKeys.detail(id),
    queryFn: async () => {
      const response = await api.transactions.getById(id)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
    enabled: id > 0,
  })
}

// Create transaction mutation
export function useCreateTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (transaction: Omit<Transaction, 'id' | 'created_at' | 'updated_at'>) => {
      const response = await api.transactions.create(transaction)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
    onSuccess: (data) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: transactionKeys.all })
      if (data) {
        queryClient.invalidateQueries({ 
          queryKey: transactionKeys.byPortfolio(data.portfolio_id) 
        })
      }
      // Also invalidate portfolio queries since transaction counts may change
      queryClient.invalidateQueries({ queryKey: portfoliosRootKey as any })
      // Recompute analytics dependent on holdings/prices
      queryClient.invalidateQueries({ queryKey: breakEvenRootKey as any })
      queryClient.invalidateQueries({ queryKey: marketPricesRootKey as any })
    },
  })
}

// Update transaction mutation
export function useUpdateTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, ...transaction }: { id: number } & Partial<Transaction>) => {
      const response = await api.transactions.update(id, transaction)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data
    },
    onSuccess: (data) => {
      if (data) {
        // Update the specific transaction in cache
        queryClient.setQueryData(transactionKeys.detail(data.id), data)
        // Invalidate portfolio transactions
        queryClient.invalidateQueries({ 
          queryKey: transactionKeys.byPortfolio(data.portfolio_id) 
        })
        // Invalidate all transactions list
        queryClient.invalidateQueries({ queryKey: transactionKeys.all })
        // Invalidate dependent analytics/values
        queryClient.invalidateQueries({ queryKey: portfoliosRootKey as any })
        queryClient.invalidateQueries({ queryKey: breakEvenRootKey as any })
        queryClient.invalidateQueries({ queryKey: marketPricesRootKey as any })
      }
    },
  })
}

// Delete transaction mutation
export function useDeleteTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.transactions.delete(id)
      if (response.error) {
        throw new Error(response.error)
      }
      return id
    },
    onSuccess: (deletedId) => {
      // Remove from cache and invalidate related queries
      queryClient.removeQueries({ queryKey: transactionKeys.detail(deletedId) })
      queryClient.invalidateQueries({ queryKey: transactionKeys.all })
      queryClient.invalidateQueries({ queryKey: portfoliosRootKey as any })
      // Note: We can't easily invalidate the specific portfolio transactions 
      // without knowing the portfolio_id, so we invalidate all transaction queries
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      // Invalidate dependent analytics/values
      queryClient.invalidateQueries({ queryKey: breakEvenRootKey as any })
      queryClient.invalidateQueries({ queryKey: marketPricesRootKey as any })
    },
  })
}