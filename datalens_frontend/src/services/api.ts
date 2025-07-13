import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
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

const API_BASE_URL = 'http://localhost:8080/api';  // REVERT: Volver a 8080 como estaba originalmente

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

// **NUEVO: Variables para controlar la renovación de tokens**
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (error?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  
  failedQueue = [];
};

// **NUEVO: Función para renovar el token automáticamente**
const refreshAuthToken = async (): Promise<string | null> => {
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    console.log('🔄 Renovando token automáticamente...');
    
    const response = await axios.post('http://localhost:8080/api/auth/refresh/', {
      refresh: refreshToken
    });

    const { tokens, user } = response.data;
    const newAccessToken = tokens.access;
    
    // Actualizar tokens en localStorage
    localStorage.setItem('access_token', newAccessToken);
    if (tokens.refresh) {
      localStorage.setItem('refresh_token', tokens.refresh);
    }
    
    // Actualizar información del usuario si viene en la respuesta
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    }
    
    console.log('✅ Token renovado exitosamente');
    return newAccessToken;
    
  } catch (error) {
    console.error('❌ Error renovando token:', error);
    
    // Si falla la renovación, limpiar todo y redirigir al login
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    // Redirigir al login solo si no estamos ya en la página de login
    if (!window.location.pathname.includes('/login')) {
      console.log('🔄 Redirigiendo al login...');
      window.location.href = '/login';
    }
    
    return null;
  }
};

// **MEJORADO: Interceptor de respuesta con renovación automática**
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // Si es error 401 (token expirado) y no hemos intentado renovar aún
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Si ya se está renovando, esperar en cola
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          if (originalRequest.headers && token) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshAuthToken();
        
        if (newToken) {
          processQueue(null, newToken);
          
          // Actualizar el header de la petición original
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          
          return api(originalRequest);
        } else {
          processQueue(error, null);
          return Promise.reject(error);
        }
      } catch (refreshError) {
        processQueue(refreshError, null);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
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
  // Real API endpoints para pronósticos
  getForecasts: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/forecasting/forecasts/');
      return response.data;
    } catch (error) {
      console.error('Error fetching forecasts:', error);
      throw error;
    }
  },

  // Real API para recomendaciones de reorden
  getReorderRecommendations: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/forecasting/reorder-recommendations/');
      return response.data;
    } catch (error) {
      console.error('Error fetching reorder recommendations:', error);
      throw error;
    }
  },

  // Real API para productos
  getProducts: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/inventory/products/');
      return response.data;
    } catch (error) {
      console.error('Error fetching products:', error);
      throw error;
    }
  },

  // CRUD Operations for Products
  createProduct: async (product: any): Promise<any> => {
    const response = await api.post('/inventory/products/', product);
    return response.data;
  },

  updateProduct: async (id: number, product: any): Promise<any> => {
    const response = await api.put(`/inventory/products/${id}/`, product);
    return response.data;
  },

  deleteProduct: async (id: number): Promise<void> => {
    await api.delete(`/inventory/products/${id}/`);
  },

  // Categories
  getCategories: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/inventory/categories/');
      return response.data;
    } catch (error) {
      console.error('Error fetching categories:', error);
      throw error;
    }
  },

  createCategory: async (category: any): Promise<any> => {
    const response = await api.post('/inventory/categories/', category);
    return response.data;
  },

  updateCategory: async (id: number, category: any): Promise<any> => {
    const response = await api.put(`/inventory/categories/${id}/`, category);
    return response.data;
  },

  deleteCategory: async (id: number): Promise<void> => {
    await api.delete(`/inventory/categories/${id}/`);
  },

  // Suppliers
  getSuppliers: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/inventory/suppliers/');
      return response.data;
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      throw error;
    }
  },

  createSupplier: async (supplier: any): Promise<any> => {
    const response = await api.post('/inventory/suppliers/', supplier);
    return response.data;
  },

  updateSupplier: async (id: number, supplier: any): Promise<any> => {
    const response = await api.put(`/inventory/suppliers/${id}/`, supplier);
    return response.data;
  },

  deleteSupplier: async (id: number): Promise<void> => {
    await api.delete(`/inventory/suppliers/${id}/`);
  },

  // Locations
  getLocations: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/inventory/locations/');
      return response.data;
    } catch (error) {
      console.error('Error fetching locations:', error);
      throw error;
    }
  },

  createLocation: async (location: any): Promise<any> => {
    const response = await api.post('/inventory/locations/', location);
    return response.data;
  },

  updateLocation: async (id: number, location: any): Promise<any> => {
    const response = await api.put(`/inventory/locations/${id}/`, location);
    return response.data;
  },

  deleteLocation: async (id: number): Promise<void> => {
    await api.delete(`/inventory/locations/${id}/`);
  },

  // Inventory Items
  getInventoryItems: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/inventory/inventory-items/');
      return response.data;
    } catch (error) {
      console.error('Error fetching inventory items:', error);
      throw error;
    }
  },

  createInventoryItem: async (item: any): Promise<any> => {
    const response = await api.post('/inventory/inventory-items/', item);
    return response.data;
  },

  updateInventoryItem: async (id: number, item: any): Promise<any> => {
    const response = await api.put(`/inventory/inventory-items/${id}/`, item);
    return response.data;
  },

  deleteInventoryItem: async (id: number): Promise<void> => {
    await api.delete(`/inventory/inventory-items/${id}/`);
  },

  // Real API para transacciones con manejo de errores mejorado
  getTransactions: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/inventory/transactions/');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching transactions:', error);
      // Si el endpoint principal falla, devolver estructura vacía
      if (error.response?.status === 404) {
        console.warn('Endpoint de transacciones no encontrado, devolviendo datos vacíos');
        return { results: [], count: 0, next: undefined, previous: undefined };
      }
      throw error;
    }
  },

  // Transacciones
  createTransaction: async (transaction: Partial<Transaction>): Promise<Transaction> => {
    const response = await api.post('/inventory/transactions/', transaction);
    return response.data;
  },

  // Real API para generar pronósticos
  predictDemand: async (data: {
    product_ids?: number[];
    forecast_horizon?: number;
    include_confidence_intervals?: boolean;
  }): Promise<any> => {
    try {
      const response = await api.post('/forecasting/predict/', data);
      return response.data;
    } catch (error) {
      console.error('Error predicting demand:', error);
      throw error;
    }
  },

  // Real API para generar recomendaciones
  generateRecommendations: async (data: {
    product_ids?: number[];
  }): Promise<any> => {
    try {
      const response = await api.post('/forecasting/generate-recommendations/', data);
      return response.data;
    } catch (error) {
      console.error('Error generating recommendations:', error);
      throw error;
    }
  },

  // ===== MÉTODOS PARA DASHBOARD =====
  
  // Dashboard de inventario
  getInventoryDashboard: async (): Promise<any> => {
    try {
      const response = await api.get('/inventory/dashboard/');
      return response.data;
    } catch (error) {
      console.error('Error fetching inventory dashboard:', error);
      // Fallback con datos mínimos
      return {
        total_products: 0,
        total_categories: 0,
        total_suppliers: 0,
        total_locations: 0,
        low_stock_alerts: 0,
        out_of_stock: 0,
        total_value: 0,
        recent_transactions: []
      };
    }
  },

  // ===== MÉTODOS PARA CRM =====
  
  // Customers
  getCustomers: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/inventory/customers/');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching customers:', error);
      // Si el endpoint principal falla, devolver estructura vacía
      if (error.response?.status === 404) {
        console.warn('Endpoint de customers no encontrado, devolviendo datos vacíos');
        return { results: [], count: 0, next: undefined, previous: undefined };
      }
      throw error;
    }
  },

  createCustomer: async (customer: any): Promise<any> => {
    try {
      const response = await api.post('/inventory/customers/', customer);
      return response.data;
    } catch (error) {
      console.error('Error creating customer:', error);
      throw error;
    }
  },

  updateCustomer: async (id: number, customer: any): Promise<any> => {
    try {
      const response = await api.put(`/inventory/customers/${id}/`, customer);
      return response.data;
    } catch (error) {
      console.error('Error updating customer:', error);
      throw error;
    }
  },

  deleteCustomer: async (id: number): Promise<void> => {
    try {
      await api.delete(`/inventory/customers/${id}/`);
    } catch (error) {
      console.error('Error deleting customer:', error);
      throw error;
    }
  },

  // Leads
  getLeads: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/inventory/leads/');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching leads:', error);
      // Si el endpoint principal falla, devolver estructura vacía
      if (error.response?.status === 404) {
        console.warn('Endpoint de leads no encontrado, devolviendo datos vacíos');
        return { results: [], count: 0, next: undefined, previous: undefined };
      }
      throw error;
    }
  },

  createLead: async (lead: any): Promise<any> => {
    try {
      const response = await api.post('/inventory/leads/', lead);
      return response.data;
    } catch (error) {
      console.error('Error creating lead:', error);
      throw error;
    }
  },

  updateLead: async (id: number, lead: any): Promise<any> => {
    try {
      const response = await api.put(`/inventory/leads/${id}/`, lead);
      return response.data;
    } catch (error) {
      console.error('Error updating lead:', error);
      throw error;
    }
  },

  deleteLead: async (id: number): Promise<void> => {
    try {
      await api.delete(`/inventory/leads/${id}/`);
    } catch (error) {
      console.error('Error deleting lead:', error);
      throw error;
    }
  },

  convertLeadToCustomer: async (leadId: number, customerData: any): Promise<any> => {
    try {
      const response = await api.post(`/inventory/leads/${leadId}/convert/`, customerData);
      return response.data;
    } catch (error) {
      console.error('Error converting lead to customer:', error);
      throw error;
    }
  },

  // Opportunities
  getOpportunities: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await api.get('/inventory/opportunities/');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching opportunities:', error);
      // Si el endpoint principal falla, devolver estructura vacía
      if (error.response?.status === 404) {
        console.warn('Endpoint de opportunities no encontrado, devolviendo datos vacíos');
        return { results: [], count: 0, next: undefined, previous: undefined };
      }
      throw error;
    }
  },

  createOpportunity: async (opportunity: any): Promise<any> => {
    try {
      const response = await api.post('/inventory/opportunities/', opportunity);
      return response.data;
    } catch (error) {
      console.error('Error creating opportunity:', error);
      throw error;
    }
  },

  updateOpportunity: async (id: number, opportunity: any): Promise<any> => {
    try {
      const response = await api.put(`/inventory/opportunities/${id}/`, opportunity);
      return response.data;
    } catch (error) {
      console.error('Error updating opportunity:', error);
      throw error;
    }
  },

  deleteOpportunity: async (id: number): Promise<void> => {
    try {
      await api.delete(`/inventory/opportunities/${id}/`);
    } catch (error) {
      console.error('Error deleting opportunity:', error);
      throw error;
    }
  },

  // ===== NUEVOS SERVICIOS PARA GRÁFICOS =====
  
  // Obtener datos de pronósticos para gráficos
  getForecastData: async (params?: {
    days_ahead?: number;
    product_ids?: string;
    location_ids?: string;
  }): Promise<any> => {
    const response = await api.get('/forecasting/data/', { params });
    return response.data;
  },

  // Generar gráfico de demanda
  getDemandChart: async (params?: {
    chart_type?: 'line' | 'bar' | 'area';
    days_ahead?: number;
    product_ids?: string;
    location_ids?: string;
  }): Promise<any> => {
    try {
      const response = await api.get('/forecasting/charts/demand/', { params });
      return response.data;
    } catch (error: any) {
      console.warn('Endpoint de gráfico de demanda no disponible, generando desde datos:', error);
      // Fallback: usar datos para generar un gráfico en el frontend
      const forecastData = await forecastingService.getForecastData(params);  // FIX: usar forecastingService en lugar de this
      return {
        chart_image: null,
        chart_data: forecastData,
        fallback: true,
        message: 'Gráfico generado desde datos JSON'
      };
    }
  },

  // Generar gráfico de comparación de modelos ML
  getModelComparisonChart: async (): Promise<any> => {
    try {
      const response = await api.get('/forecasting/charts/models/');
      return response.data;
    } catch (error: any) {
      console.warn('Endpoint de gráfico de modelos no disponible:', error);
      return {
        chart_image: null,
        chart_data: null,
        fallback: true,
        message: 'Endpoint de comparación de modelos no implementado aún'
      };
    }
  },

  // NUEVO: Método para generar gráficos desde el frontend usando los datos
  generateClientChart: async (data: any, chartType: 'line' | 'bar' | 'area' = 'line'): Promise<string> => {
    // Este método podría usar una librería como Chart.js o Recharts
    // Por ahora retornamos un placeholder
    return Promise.resolve('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzM3NDE1MSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkdyw6FmaWNvIGdlbmVyYWRvIGVuIGZyb250ZW5kPC90ZXh0Pgo8L3N2Zz4K');
  },
};

// Servicios de configuraciones (Settings)
export const settingsService = {
  // Configuraciones de usuario
  getUserSettings: async (): Promise<any> => {
    const response = await api.get('/auth/settings/');
    return response.data;
  },

  updateUserSettings: async (settings: any): Promise<any> => {
    const response = await api.patch('/auth/settings/', settings);
    return response.data;
  },

  // Información del sistema
  getSystemInfo: async (): Promise<any> => {
    const response = await api.get('/auth/system-info/');
    return response.data;
  },

  // Cambio de contraseña
  changePassword: async (passwords: { current_password: string; new_password: string; confirm_password: string }): Promise<any> => {
    const response = await api.post('/auth/change-password/', passwords);
    return response.data;
  },
};

// Servicios de alertas
export const alertService = {
  getAlerts: async (): Promise<ApiResponse<Alert>> => {
    const response = await api.get('/alerts/alerts/');
    return response.data;
  },

  createAlert: async (alert: any): Promise<Alert> => {
    const response = await api.post('/alerts/alerts/', alert);
    return response.data;
  },

  updateAlert: async (id: number, alert: any): Promise<Alert> => {
    const response = await api.patch(`/alerts/alerts/${id}/`, alert);
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

  acknowledgeAlert: async (id: number, note?: string): Promise<Alert> => {
    const response = await api.post(`/alerts/alerts/${id}/acknowledge/`, { note });
    return response.data;
  },

  dismissAlert: async (id: number, note?: string): Promise<Alert> => {
    const response = await api.post(`/alerts/alerts/${id}/dismiss/`, { note });
    return response.data;
  },

  // Reglas de alertas
  getAlertRules: async (): Promise<any> => {
    const response = await api.get('/alerts/rules/');
    return response.data;
  },

  createAlertRule: async (rule: any): Promise<any> => {
    const response = await api.post('/alerts/rules/', rule);
    return response.data;
  },

  updateAlertRule: async (id: number, rule: any): Promise<any> => {
    const response = await api.put(`/alerts/rules/${id}/`, rule);
    return response.data;
  },

  deleteAlertRule: async (id: number): Promise<void> => {
    await api.delete(`/alerts/rules/${id}/`);
  },

  testAlertRule: async (id: number): Promise<any> => {
    const response = await api.post(`/alerts/test-rule/${id}/`);
    return response.data;
  },

  // Dashboard y verificación
  getAlertsDashboard: async (): Promise<any> => {
    const response = await api.get('/alerts/dashboard/');
    return response.data;
  },

  checkAlerts: async (): Promise<any> => {
    const response = await api.post('/alerts/check-alerts/');
    return response.data;
  },

  // Notificaciones
  getNotifications: async (): Promise<any> => {
    const response = await api.get('/alerts/notifications/');
    return response.data;
  },
};

// Servicios de forecasting/ML
export const forecastingService = {
  // Modelos
  getModels: async (): Promise<any> => {
    const response = await api.get('/forecasting/models/');
    return response.data;
  },

  createModel: async (model: any): Promise<any> => {
    const response = await api.post('/forecasting/models/', model);
    return response.data;
  },

  updateModel: async (id: number, model: any): Promise<any> => {
    const response = await api.put(`/forecasting/models/${id}/`, model);
    return response.data;
  },

  deleteModel: async (id: number): Promise<void> => {
    await api.delete(`/forecasting/models/${id}/`);
  },

  getModelAccuracy: async (id: number): Promise<any> => {
    const response = await api.get(`/forecasting/models/${id}/accuracy/`);
    return response.data;
  },

  // Pronósticos
  getForecasts: async (): Promise<any> => {
    const response = await api.get('/forecasting/forecasts/');
    return response.data;
  },

  createForecast: async (forecast: any): Promise<any> => {
    const response = await api.post('/forecasting/forecasts/', forecast);
    return response.data;
  },

  getProductForecast: async (productId: number): Promise<any> => {
    const response = await api.get(`/forecasting/products/${productId}/forecast/`);
    return response.data;
  },

  // Predicciones
  predictDemand: async (data: any): Promise<any> => {
    const response = await api.post('/forecasting/predict/', data);
    return response.data;
  },

  trainModel: async (data: any): Promise<any> => {
    const response = await api.post('/forecasting/train-model/', data);
    return response.data;
  },

  // Recomendaciones
  getReorderRecommendations: async (): Promise<any> => {
    const response = await api.get('/forecasting/reorder-recommendations/');
    return response.data;
  },

  generateRecommendations: async (): Promise<any> => {
    const response = await api.post('/forecasting/generate-recommendations/');
    return response.data;
  },

  // ===== SERVICIOS PARA GRÁFICOS CORREGIDOS =====
  
  // Obtener datos de pronósticos para gráficos (funciona - confirmado con curl)
  getForecastData: async (params?: {
    days_ahead?: number;
    product_ids?: string;
    location_ids?: string;
  }): Promise<any> => {
    const response = await api.get('/forecasting/data/', { params });
    return response.data;
  },

  // Generar gráfico de demanda - CORREGIDO para manejar tanto imágenes como datos
  getDemandChart: async (params?: {
    chart_type?: 'line' | 'bar' | 'area';
    days_ahead?: number;
    product_ids?: string;
    location_ids?: string;
  }): Promise<any> => {
    try {
      const response = await api.get('/forecasting/charts/demand/', { params });
      return response.data;
    } catch (error: any) {
      console.warn('Endpoint de gráfico de demanda no disponible, generando desde datos:', error);
      // Fallback: usar datos para generar un gráfico en el frontend
      const forecastData = await forecastingService.getForecastData(params);
      return {
        chart_image: null,
        chart_data: forecastData,
        fallback: true,
        message: 'Gráfico generado desde datos JSON'
      };
    }
  },

  // Generar gráfico de comparación de modelos ML - CORREGIDO
  getModelComparisonChart: async (): Promise<any> => {
    try {
      const response = await api.get('/forecasting/charts/models/');
      return response.data;
    } catch (error: any) {
      console.warn('Endpoint de gráfico de modelos no disponible:', error);
      return {
        chart_image: null,
        chart_data: null,
        fallback: true,
        message: 'Endpoint de comparación de modelos no implementado aún'
      };
    }
  },

  // NUEVO: Método para generar gráficos desde el frontend usando los datos
  generateClientChart: async (data: any, chartType: 'line' | 'bar' | 'area' = 'line'): Promise<string> => {
    // Este método podría usar una librería como Chart.js o Recharts
    // Por ahora retornamos un placeholder
    return Promise.resolve('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzM3NDE1MSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkdyw6FmaWNvIGdlbmVyYWRvIGVuIGZyb250ZW5kPC90ZXh0Pgo8L3N2Zz4K');
  },
};

// Servicios de reportes
export const reportService = {
  // Reportes
  getReports: async (): Promise<ApiResponse<Report>> => {
    const response = await api.get('/reports/reports/');
    return response.data;
  },

  createReport: async (report: any): Promise<Report> => {
    const response = await api.post('/reports/reports/', report);
    return response.data;
  },

  updateReport: async (id: number, report: any): Promise<Report> => {
    const response = await api.put(`/reports/reports/${id}/`, report);
    return response.data;
  },

  deleteReport: async (id: number): Promise<void> => {
    await api.delete(`/reports/reports/${id}/`);
  },

  getReport: async (id: number): Promise<Report> => {
    const response = await api.get(`/reports/reports/${id}/`);
    return response.data;
  },

  generateReport: async (reportData: any): Promise<any> => {
    const response = await api.post('/reports/generate/', reportData);
    return response.data;
  },

  downloadReport: async (id: number): Promise<Blob> => {
    const response = await api.get(`/reports/reports/${id}/download/`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Templates
  getReportTemplates: async (): Promise<any> => {
    const response = await api.get('/reports/templates/');
    return response.data;
  },

  createReportTemplate: async (template: any): Promise<any> => {
    const response = await api.post('/reports/templates/', template);
    return response.data;
  },

  updateReportTemplate: async (id: number, template: any): Promise<any> => {
    const response = await api.put(`/reports/templates/${id}/`, template);
    return response.data;
  },

  deleteReportTemplate: async (id: number): Promise<void> => {
    await api.delete(`/reports/templates/${id}/`);
  },

  // KPIs
  getKPIDefinitions: async (): Promise<any> => {
    const response = await api.get('/reports/kpis/');
    return response.data;
  },

  createKPIDefinition: async (kpi: any): Promise<any> => {
    const response = await api.post('/reports/kpis/', kpi);
    return response.data;
  },

  updateKPIDefinition: async (id: number, kpi: any): Promise<any> => {
    const response = await api.put(`/reports/kpis/${id}/`, kpi);
    return response.data;
  },

  deleteKPIDefinition: async (id: number): Promise<void> => {
    await api.delete(`/reports/kpis/${id}/`);
  },

  getKPIValues: async (): Promise<any> => {
    const response = await api.get('/reports/kpi-values/');
    return response.data;
  },

  calculateKPIs: async (): Promise<any> => {
    const response = await api.post('/reports/kpis/calculate/');
    return response.data;
  },

  // Programación
  getReportSchedules: async (): Promise<any> => {
    const response = await api.get('/reports/schedules/');
    return response.data;
  },

  createReportSchedule: async (schedule: any): Promise<any> => {
    const response = await api.post('/reports/schedules/', schedule);
    return response.data;
  },

  updateReportSchedule: async (id: number, schedule: any): Promise<any> => {
    const response = await api.put(`/reports/schedules/${id}/`, schedule);
    return response.data;
  },

  deleteReportSchedule: async (id: number): Promise<void> => {
    await api.delete(`/reports/schedules/${id}/`);
  },

  // Dashboard y exportación
  getReportsDashboard: async (): Promise<any> => {
    const response = await api.get('/reports/dashboard/');
    return response.data;
  },

  exportData: async (exportConfig: any): Promise<Blob> => {
    const response = await api.post('/reports/export/', exportConfig, {
      responseType: 'blob'
    });
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

// Servicios extendidos para el dashboard mejorado
export const enhancedDashboardService = {
  getCompleteStats: async (): Promise<any> => {
    try {
      // Intentar obtener estadísticas del endpoint principal
      const response = await api.get('/dashboard/stats/');
      return response.data;
    } catch (error) {
      // Fallback a estadísticas básicas del inventario
      const inventoryStats = await api.get('/inventory/dashboard/');
      return inventoryStats.data;
    }
  },

  getRecentActivity: async (): Promise<any> => {
    const response = await api.get('/inventory/transactions/', {
      params: { limit: 10, ordering: '-created_at' }
    });
    return response.data;
  },

  getTopProducts: async (): Promise<any> => {
    const response = await api.get('/inventory/products/', {
      params: { limit: 5, ordering: '-current_stock' }
    });
    return response.data;
  },

  getStockLevels: async (): Promise<any> => {
    const response = await api.get('/inventory/stock-movements/');
    return response.data;
  }
};

// Extender alertService con métodos faltantes
export const extendedAlertService = {
  ...alertService,
  
  getDashboardData: async (): Promise<any> => {
    try {
      const response = await api.get('/alerts/dashboard/');
      return response.data;
    } catch (error) {
      // Fallback en caso de error
      return {
        total_alerts: 0,
        active_alerts: 0,
        critical_alerts: 0,
        acknowledged_alerts: 0,
        resolved_alerts: 0,
        alerts_by_severity: {},
        alerts_by_type: {},
        recent_alerts: [],
        alert_trends: {}
      };
    }
  }
};

// Extender forecastingService con métodos faltantes
export const extendedForecastingService = {
  ...forecastingService,
  
  getRecentForecasts: async (): Promise<any> => {
    try {
      const response = await api.get('/forecasting/forecasts/', {
        params: { limit: 10, ordering: '-created_at' }
      });
      return response.data;
    } catch (error) {
      return { results: [], count: 0, next: undefined, previous: undefined };
    }
  },

  getForecastSummary: async (): Promise<any> => {
    try {
      const response = await api.get('/forecasting/forecasts/');
      return response.data;
    } catch (error) {
      return { results: [], count: 0, next: undefined, previous: undefined };
    }
  }
};

// Extender inventoryService con métodos para transacciones
export const extendedInventoryService = {
  ...inventoryService,
  
  getTransactions: async (params?: any): Promise<any> => {
    try {
      const response = await api.get('/inventory/transactions/', { params });
      return response.data;
    } catch (error) {
      return { results: [], count: 0, next: undefined, previous: undefined };
    }
  },

  getRecentTransactions: async (): Promise<any> => {
    try {
      const response = await api.get('/inventory/transactions/', {
        params: { limit: 8, ordering: '-created_at' }
      });
      return response.data;
    } catch (error) {
      return { results: [], count: 0, next: undefined, previous: undefined };
    }
  },

  getTransactionSummary: async (): Promise<any> => {
    try {
      const response = await api.get('/inventory/transactions/');
      const data = response.data;
      
      // Procesar datos para el dashboard
      const today = new Date().toISOString().split('T')[0];
      const todayTransactions = (data.results || []).filter((t: any) => 
        t.created_at?.startsWith(today)
      );
      
      return {
        total_today: todayTransactions.length,
        total_week: (data.results || []).length,
        recent: (data.results || []).slice(0, 5)
      };
    } catch (error) {
      return {
        total_today: 0,
        total_week: 0,
        recent: []
      };
    }
  }
};

export default api;
