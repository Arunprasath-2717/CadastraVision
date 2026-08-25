/**
 * Centralized API Client Wrapper (PRD-CM-04 Section 55 & Section 3.2)
 * All frontend API calls pass through this abstraction layer so Shiva (Backend Core)
 * can attach the real endpoints without touching UI components.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const USE_MOCK = import.meta.env.VITE_USE_MOCK_DATA !== 'false';

/**
 * Standard HTTP fetch client with authorization headers & error normalization
 * @param {string} endpoint 
 * @param {RequestInit} [options] 
 */
export async function apiRequest(endpoint, options = {}) {
  if (!navigator.onLine && USE_MOCK) {
    return null;
  }

  const token = localStorage.getItem('cadastral_jwt');
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const url = `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, { ...options, headers });
    
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw {
        status: response.status,
        title: errorBody.title || 'API Error',
        detail: errorBody.detail || `Request failed with status ${response.status}`,
      };
    }

    return await response.json();
  } catch (err) {
    if (USE_MOCK) {
      // In mock mode, log warning & let service fallback to local fixtures
      console.warn(`[API Client] Real endpoint ${endpoint} unreachable. Falling back to Mock Fixture.`);
      return null;
    }
    throw err;
  }
}

export { BASE_URL, USE_MOCK };
