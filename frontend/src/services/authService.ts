import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token a las requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para manejar errores de autenticación
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_premium: boolean;
  created_at: string;
}

export class AuthService {
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await apiClient.post('/api/auth/login', {
      email,
      password,
    });
    return response.data;
  }

  async register(email: string, password: string, fullName: string): Promise<User> {
    const response = await apiClient.post('/api/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  }

  async getCurrentUser(token: string): Promise<User> {
    const response = await apiClient.get('/api/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }

  async upgradeToPremium(): Promise<void> {
    await apiClient.put('/api/auth/upgrade-premium');
  }
}

export const authService = new AuthService();