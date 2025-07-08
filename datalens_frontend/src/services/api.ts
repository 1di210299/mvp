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

const API_BASE_URL = 'http://localhost:8081/api';

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

// Interceptor para manejar errores de autenticación con refresh automático
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await api.post('/auth/refresh/', { refresh: refreshToken });
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Si el refresh falla, limpiar tokens y redirigir
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
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
  // Productos
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

  // Categorías
  getCategories: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/inventory/categories/');
    return response.data;
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

  // Proveedores
  getSuppliers: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/inventory/suppliers/');
    return response.data;
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

  // Ubicaciones
  getLocations: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/inventory/locations/');
    return response.data;
  },

  // Inventario/Items
  getInventoryItems: async (): Promise<ApiResponse<Inventory>> => {
    const response = await api.get('/inventory/inventory-items/');
    return response.data;
  },

  createInventoryItem: async (item: any): Promise<any> => {
    const response = await api.post('/inventory/inventory-items/', item);
    return response.data;
  },

  updateInventoryItem: async (id: number, item: any): Promise<any> => {
    const response = await api.put(`/inventory/inventory-items/${id}/`, item);
    return response.data;
  },

  // Stock endpoints
  getProductStock: async (productId: number): Promise<any> => {
    const response = await api.get(`/inventory/products/${productId}/stock/`);
    return response.data;
  },

  getLowStock: async (): Promise<any> => {
    const response = await api.get('/inventory/low-stock/');
    return response.data;
  },

  getStockMovements: async (): Promise<any> => {
    const response = await api.get('/inventory/stock-movements/');
    return response.data;
  },

  // Transacciones
  getTransactions: async (): Promise<ApiResponse<Transaction>> => {
    const response = await api.get('/inventory/transactions/');
    return response.data;
  },

  createTransaction: async (transaction: Partial<Transaction>): Promise<Transaction> => {
    const response = await api.post('/inventory/transactions/', transaction);
    return response.data;
  },

  // Dashboard de inventario
  getInventoryDashboard: async (): Promise<any> => {
    try {
      const response = await api.get('/inventory/dashboard/');
      return response.data;
    } catch (error: any) {
      console.error('Error loading inventory dashboard:', error);
      // Intentar endpoint alternativo
      try {
        const fallbackResponse = await api.get('/dashboard/stats/');
        return fallbackResponse.data;
      } catch (fallbackError) {
        console.error('Fallback dashboard endpoint also failed:', fallbackError);
        // Devolver estructura mínima para evitar crashes
        return {
          total_products: 0,
          total_stock_value: 0,
          low_stock_alerts: 0,
          recent_transactions: 0,
          active_customers: 0,
          pipeline_value: 0,
          stock_levels: [],
          top_products: []
        };
      }
    }
  },

  // Upload
  uploadFile: async (file: FormData): Promise<any> => {
    const response = await api.post('/inventory/upload/', file, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // ===== CRM SERVICES =====
  // Customers
  getCustomers: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/inventory/customers/');
    return response.data;
  },

  createCustomer: async (customer: any): Promise<any> => {
    const response = await api.post('/inventory/customers/', customer);
    return response.data;
  },

  updateCustomer: async (id: number, customer: any): Promise<any> => {
    const response = await api.put(`/inventory/customers/${id}/`, customer);
    return response.data;
  },

  deleteCustomer: async (id: number): Promise<void> => {
    await api.delete(`/inventory/customers/${id}/`);
  },

  getCustomerInsights: async (id: number): Promise<any> => {
    const response = await api.get(`/inventory/customers/${id}/insights/`);
    return response.data;
  },

  // Leads
  getLeads: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/inventory/leads/');
    return response.data;
  },

  createLead: async (lead: any): Promise<any> => {
    const response = await api.post('/inventory/leads/', lead);
    return response.data;
  },

  updateLead: async (id: number, lead: any): Promise<any> => {
    const response = await api.put(`/inventory/leads/${id}/`, lead);
    return response.data;
  },

  deleteLead: async (id: number): Promise<void> => {
    await api.delete(`/inventory/leads/${id}/`);
  },

  convertLeadToCustomer: async (id: number, data: any): Promise<any> => {
    const response = await api.post(`/inventory/leads/${id}/convert_to_customer/`, data);
    return response.data;
  },

  // Opportunities
  getOpportunities: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/inventory/opportunities/');
    return response.data;
  },

  createOpportunity: async (opportunity: any): Promise<any> => {
    const response = await api.post('/inventory/opportunities/', opportunity);
    return response.data;
  },

  updateOpportunity: async (id: number, opportunity: any): Promise<any> => {
    const response = await api.put(`/inventory/opportunities/${id}/`, opportunity);
    return response.data;
  },

  deleteOpportunity: async (id: number): Promise<void> => {
    await api.delete(`/inventory/opportunities/${id}/`);
  },

  addOpportunityProduct: async (id: number, product: any): Promise<any> => {
    const response = await api.post(`/inventory/opportunities/${id}/add_product/`, product);
    return response.data;
  },

  getOpportunityProducts: async (id: number): Promise<any> => {
    const response = await api.get(`/inventory/opportunities/${id}/products/`);
    return response.data;
  },

  // Contacts
  getContacts: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/inventory/contacts/');
    return response.data;
  },

  createContact: async (contact: any): Promise<any> => {
    const response = await api.post('/inventory/contacts/', contact);
    return response.data;
  },

  updateContact: async (id: number, contact: any): Promise<any> => {
    const response = await api.put(`/inventory/contacts/${id}/`, contact);
    return response.data;
  },

  deleteContact: async (id: number): Promise<void> => {
    await api.delete(`/inventory/contacts/${id}/`);
  },

  // Activities
  getActivities: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/inventory/activities/');
    return response.data;
  },

  createActivity: async (activity: any): Promise<any> => {
    const response = await api.post('/inventory/activities/', activity);
    return response.data;
  },

  updateActivity: async (id: number, activity: any): Promise<any> => {
    const response = await api.put(`/inventory/activities/${id}/`, activity);
    return response.data;
  },

  deleteActivity: async (id: number): Promise<void> => {
    await api.delete(`/inventory/activities/${id}/`);
  },

  // CRM Dashboard
  getCRMDashboard: async (): Promise<any> => {
    const response = await api.get('/inventory/crm/dashboard/');
    return response.data;
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
      return { results: [] };
    }
  },

  getForecastSummary: async (): Promise<any> => {
    try {
      const response = await api.get('/forecasting/forecasts/');
      return response.data;
    } catch (error) {
      return { results: [] };
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
      return { results: [] };
    }
  },

  getRecentTransactions: async (): Promise<any> => {
    try {
      const response = await api.get('/inventory/transactions/', {
        params: { limit: 8, ordering: '-created_at' }
      });
      return response.data;
    } catch (error) {
      return { results: [] };
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
