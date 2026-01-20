// API Configuration
// Uses environment variables to configure base URL
// Development (npm run dev): http://10.42.0.1:8000
// Production (npm run build): http://brainmove.g1:8000

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://10.42.0.1:8000';

// Helper function to construct full API URLs
export function getApiUrl(path) {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
}

// Export environment info for debugging
export const ENV_INFO = {
  mode: import.meta.env.MODE,
  apiBaseUrl: API_BASE_URL,
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
};
