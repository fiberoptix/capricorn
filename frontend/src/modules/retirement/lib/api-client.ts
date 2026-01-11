/**
 * Retirement API Client
 */
import { RetirementSummary } from '../types/retirement.types';
import { API_V1_URL } from '../../../config/api';

// Dynamic API URL based on hostname
const API_BASE = API_V1_URL;

export const retirementApi = {
  /**
   * Get complete retirement summary
   */
  async getSummary(): Promise<RetirementSummary> {
    const response = await fetch(`${API_BASE}/retirement/summary`);
    if (!response.ok) {
      throw new Error(`Failed to fetch retirement summary: ${response.statusText}`);
    }
    const data = await response.json();
    return data.data;
  },

  /**
   * Get yearly projections only
   */
  async getProjections() {
    const response = await fetch(`${API_BASE}/retirement/projections`);
    if (!response.ok) {
      throw new Error(`Failed to fetch projections: ${response.statusText}`);
    }
    const data = await response.json();
    return data;
  },

  /**
   * Get asset growth only
   */
  async getAssetGrowth() {
    const response = await fetch(`${API_BASE}/retirement/assets`);
    if (!response.ok) {
      throw new Error(`Failed to fetch asset growth: ${response.statusText}`);
    }
    const data = await response.json();
    return data;
  },

  /**
   * Get retirement analysis only
   */
  async getAnalysis() {
    const response = await fetch(`${API_BASE}/retirement/analysis`);
    if (!response.ok) {
      throw new Error(`Failed to fetch analysis: ${response.statusText}`);
    }
    const data = await response.json();
    return data.analysis;
  },

  /**
   * Get transition analysis only
   */
  async getTransition() {
    const response = await fetch(`${API_BASE}/retirement/transition`);
    if (!response.ok) {
      throw new Error(`Failed to fetch transition: ${response.statusText}`);
    }
    const data = await response.json();
    return data.transition;
  },
};

