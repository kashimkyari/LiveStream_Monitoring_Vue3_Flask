// Centralized Axios instance for all API calls
import axios from 'axios'

const api = axios.create({
  baseURL: 'https://54.86.99.85:5000',
  withCredentials: true,               // Include cookies/credentials
  headers: {
    'Content-Type': 'application/json'
  }
})

export default api
