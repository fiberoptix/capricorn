/**
 * Profile Hooks
 * React Query hooks for profile data management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { profileApi } from '../lib/api-client';
import { Profile, ProfileUpdateRequest, ProfileSection } from '../types/profile.types';

const PROFILE_QUERY_KEY = ['profile'];

/**
 * Hook to fetch profile data
 */
export function useProfile() {
  return useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: () => profileApi.getProfile(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to update profile
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProfileUpdateRequest) => profileApi.updateProfile(data),
    onSuccess: (updatedProfile) => {
      // Update profile cache
      queryClient.setQueryData(PROFILE_QUERY_KEY, updatedProfile);
      
      // CRITICAL: Invalidate retirement and portfolio caches
      // This forces them to recalculate with new profile data
      queryClient.invalidateQueries({ queryKey: ['retirement'] });
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      
      console.log('Profile updated - invalidated retirement and portfolio caches');
    },
  });
}

/**
 * Hook to update specific section
 */
export function useUpdateSection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ section, data }: { section: ProfileSection; data: Record<string, any> }) =>
      profileApi.updateSection(section, data),
    onSuccess: (updatedProfile) => {
      // Update cache with new profile data
      queryClient.setQueryData(PROFILE_QUERY_KEY, updatedProfile);
    },
  });
}

