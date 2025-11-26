'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, MarketPrice } from '../lib/api-client'

export interface MarketPricesResponse {
  count: number
  prices: MarketPrice[]
}

export interface BulkUpdateRequest {
  prices: Record<string, number> // ticker -> price mapping
}

export interface BulkUpdateResponse {
  updated_count: number
  updated_prices: MarketPrice[]
  message: string
}

// Hook to fetch all market prices
export function useMarketPrices() {
  return useQuery({
    queryKey: ['market-prices'],
    queryFn: async (): Promise<MarketPrice[]> => {
      const response = await api.marketPrices.getAll()
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data || []
    },
    // Always pull fresh prices when a page/tab mounts or gains focus
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
  })
}

// Hook to update individual market price
export function useUpdateMarketPrice() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ ticker, price }: { ticker: string; price: number }): Promise<MarketPrice> => {
      const response = await api.marketPrices.update(ticker, price)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data!
    },
    onSuccess: () => {
      // Invalidate and refetch market prices
      queryClient.invalidateQueries({ queryKey: ['market-prices'] })
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      // Also ensure break-even and portfolio market values refresh
      queryClient.invalidateQueries({ queryKey: ['break-even'] })
    },
  })
}

// Hook to bulk update multiple market prices  
export function useBulkUpdateMarketPrices() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (updates: { ticker: string; current_price: number }[]): Promise<MarketPrice[]> => {
      const response = await api.marketPrices.bulkUpdate(updates)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data!
    },
    onSuccess: () => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: ['market-prices'] })
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      queryClient.invalidateQueries({ queryKey: ['break-even'] })
      // Detail views depending on market value will refetch on focus/mount
    },
  })
}