/**
 * Central API Configuration
 * 
 * Priority:
 * 1. VITE_API_URL environment variable (for cloud deployments like GKE)
 * 2. Same hostname as the page (for local dev/prod where FE & BE share host)
 * 
 * In GKE, frontend and backend have different LoadBalancer IPs,
 * so we must set VITE_API_URL at build time.
 */

// Check for build-time API URL (used in GCP/cloud deployments)
const getApiBaseUrl = (): string => {
  // Priority 1: Build-time environment variable
  const envApiUrl = import.meta.env.VITE_API_URL;
  if (envApiUrl) {
    console.log('🌐 Using build-time API URL:', envApiUrl);
    return envApiUrl;
  }
  
  // Priority 2: Same hostname as the page (local deployments)
  if (typeof window !== 'undefined') {
    const dynamicUrl = `http://${window.location.hostname}:5002`;
    console.log('🏠 Using dynamic API URL:', dynamicUrl);
    return dynamicUrl;
  }
  
  // Fallback
  return 'http://localhost:5002';
};

// Build the full API base URL
export const API_BASE_URL = getApiBaseUrl();
export const API_HOST = new URL(API_BASE_URL).hostname;
export const API_V1_URL = `${API_BASE_URL}/api/v1`;

// Convenience exports for different API sections
export const getApiUrl = (path: string): string => {
  return `${API_V1_URL}${path.startsWith('/') ? path : '/' + path}`;
};

// For debugging - log the API URL on first load
if (typeof window !== 'undefined') {
  console.log(`🔗 API Base URL: ${API_BASE_URL}`);
}

