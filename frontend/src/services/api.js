import axios from 'axios';
import authService from './auth';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

// Request interceptor for API calls
api.interceptors.request.use(
    (config) => {
        const token = authService.getToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        // Only set default headers if not multipart/form-data
        if (!config.headers['Content-Type']?.includes('multipart/form-data')) {
            config.headers = {
                ...config.headers,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            };
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for API calls
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            authService.logout();
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;

export const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  console.log('File being uploaded:', file); // Debug log
  console.log('FormData entries:', Array.from(formData.entries())); // Debug log
  
  try {
    const response = await api.post('/api/upload/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Upload error:', error.response?.data || error); // More detailed error logging
    throw error;
  }
}; 