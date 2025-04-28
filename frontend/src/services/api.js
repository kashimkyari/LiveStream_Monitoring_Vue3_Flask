// api.js - Updated configuration with proper error handling
import axios from 'axios'

const API_BASE_URL = 'https://54.86.99.85:8080';

// Create axios instance with better error handling
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,               // Include cookies/credentials
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor for additional headers if needed
api.interceptors.request.use(
  config => {
    // You could add auth tokens here if using token-based auth
    return config;
  },
  error => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    // Handle CORS and network errors specifically
    if (error.message === 'Network Error') {
      console.error('Network Error - Possibly CORS related:', error);
      // You might want to display a user-friendly message here
    }
    
    // Log all API errors with details
    console.error('API Error Response:', {
      message: error.message,
      endpoint: error.config?.url,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    });
    
    return Promise.reject(error);
  }
);

// Password reset methods
export const requestPasswordReset = (email) => {
  return api.post('/api/forgot-password', { email });
};

// Verify token from email link is valid
export const verifyResetToken = (token) => {
  return api.post('/api/verify-reset-token', { token });
};

// Reset password with token and new password
export const resetPassword = (token, password) => {
  return api.post('/api/reset-password', { token, password });
};

// General purpose API functions
export const login = (username, password) => {
  return api.post('/api/login', { username, password });
};

export const logout = () => {
  return api.post('/api/logout');
};

export const register = (username, email, password, receiveUpdates = false) => {
  return api.post('/api/register', { username, email, password, receiveUpdates });
};

export const checkSession = () => {
  return api.get('/api/session');
};

export default api;