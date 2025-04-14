// src/api/client.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// Crear instancia de axios con configuración base
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: true, // Importante para cookies/autenticación
});

// Interceptor para agregar token de autenticación
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig): AxiosRequestConfig => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError): Promise<AxiosError> => Promise.reject(error)
);

// Interceptor para manejar errores de autenticación
apiClient.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => response,
  async (error: AxiosError): Promise<any> => {
    // Token expirado (401)
    if (error.response && error.response.status === 401) {
      const refreshToken = localStorage.getItem('refreshToken');
      
      // Si hay refresh token y no estamos ya intentando renovar
      if (refreshToken && error.config && !error.config.url?.includes('auth/refresh')) {
        try {
          const response = await apiClient.post('/auth/refresh/', { refresh: refreshToken });
          localStorage.setItem('token', response.data.access);
          
          // Reintentar la solicitud original con el nuevo token
          const originalRequest = error.config;
          if (originalRequest.headers) {
            originalRequest.headers['Authorization'] = `Bearer ${response.data.access}`;
          }
          return apiClient(originalRequest);
        } catch (refreshError) {
          // Si falla el refresh, logout
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // Sin token de refresco, logout
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;