/**
 * JWT Authentication Service for Cordova
 * 
 * Handles token-based authentication for the mobile app.
 * Stores tokens in localStorage and automatically refreshes them.
 */

const TOKEN_KEY = 'es_access_token';
const REFRESH_KEY = 'es_refresh_token';
const USER_KEY = 'es_user';

// API base URL
let API_BASE_URL = '';

/**
 * Set the API base URL
 */
export function setApiBaseUrl(url) {
    API_BASE_URL = url.replace(/\/$/, '');
}

/**
 * Get the API base URL
 */
export function getApiBaseUrl() {
    return API_BASE_URL;
}

/**
 * Get stored access token
 */
export function getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Get stored refresh token
 */
export function getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
}

/**
 * Get stored user info
 */
export function getStoredUser() {
    const userJson = localStorage.getItem(USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
}

/**
 * Store tokens and user info
 */
function storeAuthData(data) {
    if (data.access) {
        localStorage.setItem(TOKEN_KEY, data.access);
    }
    if (data.refresh) {
        localStorage.setItem(REFRESH_KEY, data.refresh);
    }
    if (data.user) {
        localStorage.setItem(USER_KEY, JSON.stringify({
            ...data.user,
            role: data.role,
            role_display: data.role_display,
            is_dispatcher: data.is_dispatcher,
            is_responder: data.is_responder,
            is_admin: data.is_admin,
        }));
    }
}

/**
 * Clear all auth data (logout)
 */
export function clearAuthData() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated() {
    return !!getAccessToken();
}

/**
 * Login with username and password
 * @returns {Promise<{success: boolean, user?: object, error?: string}>}
 */
export async function login(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/token/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (response.ok) {
            storeAuthData(data);
            return { success: true, user: getStoredUser() };
        } else {
            return { 
                success: false, 
                error: data.detail || 'Invalid credentials' 
            };
        }
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, error: 'Network error. Please check your connection.' };
    }
}

/**
 * Refresh the access token using the refresh token
 * @returns {Promise<boolean>} true if refresh succeeded
 */
export async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        return false;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refreshToken }),
        });

        if (response.ok) {
            const data = await response.json();
            storeAuthData(data);
            return true;
        } else {
            clearAuthData();
            return false;
        }
    } catch (error) {
        console.error('Token refresh error:', error);
        return false;
    }
}

/**
 * Logout
 */
export function logout(redirectUrl = null) {
    clearAuthData();
    if (redirectUrl) {
        window.location.href = redirectUrl;
    }
}

/**
 * Make an authenticated API request
 * @param {string} url - API endpoint
 * @param {object} options - fetch options
 * @returns {Promise<Response>}
 */
export async function authFetch(url, options = {}) {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    
    const token = getAccessToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    let response = await fetch(fullUrl, { ...options, headers });

    // If unauthorized, try to refresh token and retry
    if (response.status === 401 && token) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            headers['Authorization'] = `Bearer ${getAccessToken()}`;
            response = await fetch(fullUrl, { ...options, headers });
        }
    }

    return response;
}

/**
 * Check token expiry and refresh if needed
 */
export async function ensureValidToken() {
    const token = getAccessToken();
    if (!token) {
        return false;
    }

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expiry = payload.exp * 1000;
        const now = Date.now();
        
        // If token expires in less than 5 minutes, refresh it
        if (expiry - now < 5 * 60 * 1000) {
            return await refreshAccessToken();
        }
        return true;
    } catch (error) {
        console.error('Token decode error:', error);
        return false;
    }
}

/**
 * Get current user info from the API
 */
export async function fetchCurrentUser() {
    try {
        const response = await authFetch('/api/auth/me/');
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem(USER_KEY, JSON.stringify({
                ...data.user,
                role: data.role,
                role_display: data.role_display,
                is_dispatcher: data.is_dispatcher,
                is_responder: data.is_responder,
                is_admin: data.is_admin,
            }));
            return data;
        }
        return null;
    } catch (error) {
        console.error('Fetch user error:', error);
        return null;
    }
}
