import axios from 'axios';

// Determine API base URL
const getApiBaseUrl = () => {
  // Check environment variable first
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // If running in browser, try to detect the backend URL
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // If frontend is on a different port (typical dev setup)
    if (port && port !== '8000') {
      return `http://${hostname}:8000/api`;
    }
    
    // Production or same origin
    return `${window.location.origin}/api`;
  }
  
  // Fallback
  return 'http://localhost:8000/api';
};

const API_BASE_URL = getApiBaseUrl();

const API = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Log API base URL in development
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE_URL);
}

API.interceptors.request.use((req) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    req.headers.Authorization = `Bearer ${token}`;
  }
  return req;
});

API.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config;

    // Handle network errors
    if (!err.response) {
      console.error('Network error:', err.message);
      return Promise.reject({
        ...err,
        message: 'Network error. Please check your connection and try again.',
        response: { data: { error: 'Network error. Please check your connection.' } }
      });
    }

    // Handle 401 Unauthorized - Token expired or invalid
    if (err.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = localStorage.getItem('refresh_token');

      // Don't retry for login/register endpoints
      if (originalRequest.url?.includes('/login/') || originalRequest.url?.includes('/register/')) {
        return Promise.reject(err);
      }

      if (refresh) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/accounts/token/refresh/`, { refresh });
          localStorage.setItem('access_token', data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return axios(originalRequest);
        } catch (refreshError) {
          // Refresh token is also invalid, clear storage and redirect
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          if (!originalRequest.url?.includes('/login/')) {
            window.location.href = '/login';
          }
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token available
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        if (!originalRequest.url?.includes('/login/')) {
          window.location.href = '/login';
        }
      }
    }

    // Log errors in development
    if (import.meta.env.DEV) {
      console.error('API Error:', {
        url: err.config?.url,
        method: err.config?.method,
        status: err.response?.status,
        data: err.response?.data,
        message: err.message,
      });
    }

    return Promise.reject(err);
  }
);

export default API;
