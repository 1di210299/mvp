import axios from 'axios';
import { 
  User, 
  LoginData, 
  AuthResponse, 
  Product, 
  Inventory, 
  Transaction, 
  Alert, 
  Report, 
  DashboardStats,
  ApiResponse 
} from '../types';

const API_BASE_URL = 'http://localhost:8080/api';

// Configuración de axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token a las requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para manejar errores de autenticación
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Servicios de autenticación
export const authService = {
  login: async (credentials: LoginData): Promise<AuthResponse> => {
    const response = await api.post('/auth/login/', credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout/');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getProfile: async (): Promise<User> => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  refreshToken: async (): Promise<{ access: string }> => {
    const refresh = localStorage.getItem('refresh_token');
    const response = await api.post('/auth/refresh/', { refresh });
    return response.data;
  },
};

// Servicios de inventario
export const inventoryService = {
  getProducts: async (): Promise<ApiResponse<Product>> => {
    const response = await api.get('/inventory/products/');
    return response.data;
  },

  getProduct: async (id: number): Promise<Product> => {
    const response = await api.get(`/inventory/products/${id}/`);
    return response.data;
  },

  createProduct: async (product: Partial<Product>): Promise<Product> => {
    const response = await api.post('/inventory/products/', product);
    return response.data;
  },

  updateProduct: async (id: number, product: Partial<Product>): Promise<Product> => {
    const response = await api.put(`/inventory/products/${id}/`, product);
    return response.data;
  },

  deleteProduct: async (id: number): Promise<void> => {
    await api.delete(`/inventory/products/${id}/`);
  },

  getInventory: async (): Promise<ApiResponse<Inventory>> => {
    const response = await api.get('/inventory/inventory/');
    return response.data;
  },

  getTransactions: async (): Promise<ApiResponse<Transaction>> => {
    const response = await api.get('/inventory/transactions/');
    return response.data;
  },

  createTransaction: async (transaction: Partial<Transaction>): Promise<Transaction> => {
    const response = await api.post('/inventory/transactions/', transaction);
    return response.data;
  },
};

// Servicios de alertas
export const alertService = {
  getAlerts: async (): Promise<ApiResponse<Alert>> => {
    const response = await api.get('/alerts/alerts/');
    return response.data;
  },

  markAsRead: async (id: number): Promise<Alert> => {
    const response = await api.patch(`/alerts/alerts/${id}/`, { is_read: true });
    return response.data;
  },

  resolveAlert: async (id: number): Promise<Alert> => {
    const response = await api.patch(`/alerts/alerts/${id}/`, { is_resolved: true });
    return response.data;
  },
};

// Servicios de reportes
export const reportService = {
  getReports: async (): Promise<ApiResponse<Report>> => {
    const response = await api.get('/reports/reports/');
    return response.data;
  },

  generateReport: async (reportData: Partial<Report>): Promise<Report> => {
    const response = await api.post('/reports/reports/', reportData);
    return response.data;
  },

  getReport: async (id: number): Promise<Report> => {
    const response = await api.get(`/reports/reports/${id}/`);
    return response.data;
  },
};

// Servicios de dashboard
export const dashboardService = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/dashboard/stats/');
    return response.data;
  },

  getChartData: async (chartType: string): Promise<any> => {
    const response = await api.get(`/dashboard/charts/${chartType}/`);
    return response.data;
  },
};

export default api;
