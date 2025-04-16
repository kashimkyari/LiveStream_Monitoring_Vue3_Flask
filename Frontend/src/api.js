// Create a src/api.js file:
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '',  // Empty base URL
  headers: {
    'Content-Type': 'application/json'
  }
});

export default apiClient;

// Then in your components:
import api from '@/api';

// Use like this:
api.post('/api/login', credentials);