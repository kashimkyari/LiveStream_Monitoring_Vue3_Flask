// Centralized Axios instance for all API calls
import axios from 'axios'

const api = axios.create({
  baseURL: 'https://54.86.99.85:5000',
  withCredentials: true,               // Include cookies/credentials
  headers: {
    'Content-Type': 'application/json'
  }
})

// services/api.js - Add these methods to your existing API service

// Request password reset (sends email with token)
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

export default api
