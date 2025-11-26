'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, InvestorProfile } from '../lib/api-client'

// Additional interface for profile creation/updates
export interface InvestorProfileCreate {
  name: string
  annual_household_income: number
  filing_status: 'single' | 'married_filing_jointly' | 'married_filing_separately' | 'head_of_household'
  state_of_residence: string
  local_tax_rate: number
}

export interface InvestorProfileUpdate extends Partial<InvestorProfileCreate> {}

export interface InvestorProfileResponse {
  count: number
  profiles: InvestorProfile[]
}

// Hook to fetch all investor profiles
export function useInvestorProfiles() {
  return useQuery({
    queryKey: ['investor-profiles'],
    queryFn: async (): Promise<InvestorProfile[]> => {
      const response = await api.investorProfiles.getAll()
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data || []
    },
    staleTime: 300000, // 5 minutes - profile data changes infrequently
  })
}

// Hook to fetch single investor profile by ID
export function useInvestorProfile(profileId: number) {
  return useQuery({
    queryKey: ['investor-profiles', profileId],
    queryFn: async (): Promise<InvestorProfile | null> => {
      const response = await api.investorProfiles.getById(profileId)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data || null
    },
    enabled: !!profileId,
    staleTime: 300000,
  })
}

// Hook to create new investor profile
export function useCreateInvestorProfile() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: InvestorProfileCreate): Promise<InvestorProfile> => {
      const response = await api.investorProfiles.create(data)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data!
    },
    onSuccess: () => {
      // Invalidate and refetch investor profiles
      queryClient.invalidateQueries({ queryKey: ['investor-profiles'] })
    },
  })
}

// Hook to update investor profile (always updates profile ID 1 - single profile system)
export function useUpdateInvestorProfile() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ profileId, data }: { profileId: number; data: InvestorProfileUpdate }): Promise<InvestorProfile> => {
      // Force update to profile ID 1 regardless of parameter
      const response = await api.investorProfiles.update(1, data)
      if (response.error) {
        throw new Error(response.error)
      }
      return response.data!
    },
    onSuccess: () => {
      // Invalidate profile ID 1 specifically
      queryClient.invalidateQueries({ queryKey: ['investor-profiles'] })
      queryClient.invalidateQueries({ queryKey: ['investor-profiles', 1] })
    },
  })
}

// Hook to delete investor profile
export function useDeleteInvestorProfile() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (profileId: number): Promise<void> => {
      const response = await api.investorProfiles.delete(profileId)
      if (response.error) {
        throw new Error(response.error)
      }
    },
    onSuccess: () => {
      // Invalidate and refetch investor profiles
      queryClient.invalidateQueries({ queryKey: ['investor-profiles'] })
    },
  })
}

// Helper hook to get primary investor profile (always uses profile ID 1 - single profile system)
export function usePrimaryInvestorProfile() {
  return useInvestorProfile(1)
}