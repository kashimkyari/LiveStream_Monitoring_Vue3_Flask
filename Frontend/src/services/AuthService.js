import axios from 'axios';

const API_URL = '/api';

class AuthService {
  async login(username, password) {
    try {
      const response = await axios.post(`${API_URL}/login`, {
        username, 
        password
      });
      
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('userId', response.data.user.id);
        localStorage.setItem('userRole', response.data.user.role);
      }
      
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async logout() {
    try {
      // Call the server logout endpoint
      await axios.post(`${API_URL}/logout`);
    } catch (error) {
      console.error('Logout error:', error);
      // Even if server logout fails, clear local storage
    } finally {
      // Always clear local storage
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      localStorage.removeItem('userRole');
    }
  }

  async register(username, email, password) {
    return axios.post(`${API_URL}/register`, {
      username,
      email,
      password
    });
  }

  async forgotPassword(email) {
    return axios.post(`${API_URL}/forgot-password`, { email });
  }

  async resetPassword(token, password) {
    return axios.post(`${API_URL}/reset-password`, {
      token,
      password
    });
  }

  async updateProfile(userData) {
    return axios.post(`${API_URL}/update-profile`, userData);
  }

  async checkSession() {
    try {
      const response = await axios.get(`${API_URL}/check-session`);
      return response.data;
    } catch (error) {
      this.logout();
      throw error;
    }
  }

  getCurrentUser() {
    return {
      id: localStorage.getItem('userId'),
      role: localStorage.getItem('userRole')
    };
  }

  isAuthenticated() {
    return !!localStorage.getItem('token');
  }
}

export default new AuthService();