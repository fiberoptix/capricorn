// API Configuration with Runtime Environment Detection
// Uses central config for dynamic hostname detection

import { API_V1_URL, API_HOST } from '../../../config/api';

// Finance-specific API URL (banking endpoints)
export const API_BASE_URL = `${API_V1_URL}/banking`;

// Debug logging (remove in production)
console.log('🔧 Finance API Configuration:', {
  hostname: API_HOST,
  apiBaseUrl: API_BASE_URL
});
