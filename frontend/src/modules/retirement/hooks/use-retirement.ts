/**
 * Retirement Hooks
 * React Query hooks for retirement data
 */
import { useQuery } from '@tanstack/react-query';
import { retirementApi } from '../lib/api-client';

const RETIREMENT_QUERY_KEY = ['retirement'];

/**
 * Hook to fetch complete retirement summary
 * Short cache time since it depends on Profile data that can change
 */
export function useRetirementSummary() {
  return useQuery({
    queryKey: [...RETIREMENT_QUERY_KEY, 'summary'],
    queryFn: () => retirementApi.getSummary(),
    staleTime: 30 * 1000, // 30 seconds (short cache - depends on Profile)
    refetchOnWindowFocus: true, // Refetch when user returns to tab
  });
}

/**
 * Hook to fetch yearly projections
 */
export function useProjections() {
  return useQuery({
    queryKey: [...RETIREMENT_QUERY_KEY, 'projections'],
    queryFn: () => retirementApi.getProjections(),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: true,
  });
}

/**
 * Hook to fetch asset growth
 */
export function useAssetGrowth() {
  return useQuery({
    queryKey: [...RETIREMENT_QUERY_KEY, 'assets'],
    queryFn: () => retirementApi.getAssetGrowth(),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: true,
  });
}

/**
 * Hook to fetch retirement analysis
 */
export function useRetirementAnalysis() {
  return useQuery({
    queryKey: [...RETIREMENT_QUERY_KEY, 'analysis'],
    queryFn: () => retirementApi.getAnalysis(),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: true,
  });
}

/**
 * Hook to fetch transition analysis
 */
export function useTransitionAnalysis() {
  return useQuery({
    queryKey: [...RETIREMENT_QUERY_KEY, 'transition'],
    queryFn: () => retirementApi.getTransition(),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: true,
  });
}

