/**
 * Profile API Client
 * Handles all API calls for profile data
 */
import { Profile, ProfileUpdateRequest, ProfileSection } from '../types/profile.types';
import { API_V1_URL } from '../../../config/api';

// Dynamic API URL based on hostname
const API_BASE = API_V1_URL;

export const profileApi = {
  /**
   * Get user profile (single-user system)
   */
  async getProfile(): Promise<Profile> {
    const response = await fetch(`${API_BASE}/profile`);
    if (!response.ok) {
      throw new Error(`Failed to fetch profile: ${response.statusText}`);
    }
    const data = await response.json();
    return data.profile;
  },

  /**
   * Update user profile (partial updates supported)
   */
  async updateProfile(data: ProfileUpdateRequest): Promise<Profile> {
    const response = await fetch(`${API_BASE}/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update profile: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result.profile;
  },

  /**
   * Update specific section of profile
   */
  async updateSection(section: ProfileSection, data: Record<string, any>): Promise<Profile> {
    const response = await fetch(`${API_BASE}/profile/${section}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update section ${section}: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result.profile;
  },

  /**
   * Get available profile sections
   */
  async getSections(): Promise<Record<string, string[]>> {
    const response = await fetch(`${API_BASE}/profile/sections`);
    if (!response.ok) {
      throw new Error(`Failed to fetch sections: ${response.statusText}`);
    }
    const data = await response.json();
    return data.sections;
  },
};

