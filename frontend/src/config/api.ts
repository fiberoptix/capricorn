/**
 * Central API Configuration
 * 
 * Dynamically determines the API base URL based on where the browser
 * loaded the page from. This allows the app to work from any machine:
 * - localhost (development)
 * - 192.168.x.x (LAN IP)
 * - hostname (server name)
 * - domain.com (production)
 * 
 * The browser knows what hostname it used to reach the frontend,
 * so we use that same hostname for API calls (just different port).
 */

// Get the hostname the browser used to load this page
const getApiHost = (): string => {
  // In browser environment, use the same hostname that served the page
  if (typeof window !== 'undefined') {
    return window.location.hostname;
  }
  // Fallback for SSR or non-browser environments
  return 'localhost';
};

// API port (backend runs on 5002)
const API_PORT = 5002;

// Build the full API base URL dynamically
export const API_HOST = getApiHost();
export const API_BASE_URL = `http://${API_HOST}:${API_PORT}`;
export const API_V1_URL = `${API_BASE_URL}/api/v1`;

// Convenience exports for different API sections
export const getApiUrl = (path: string): string => {
  return `${API_V1_URL}${path.startsWith('/') ? path : '/' + path}`;
};

// For debugging - log the API URL on first load
if (typeof window !== 'undefined') {
  console.log(`🔗 API Base URL: ${API_BASE_URL}`);
}

