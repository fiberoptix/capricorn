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
  
  // Priority 2: Auto-detect based on page protocol (HTTPS = Traefik proxy, HTTP = direct)
  if (typeof window !== 'undefined') {
    // If served over HTTPS, use relative /api path (Traefik routes it to backend)
    if (window.location.protocol === 'https:') {
      const relativeUrl = `${window.location.protocol}//${window.location.host}`;
      console.log('🔒 Using HTTPS with Traefik proxy:', relativeUrl);
      return relativeUrl;
    }
    
    // If served over HTTP, use direct backend port (DEV/QA environments)
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

