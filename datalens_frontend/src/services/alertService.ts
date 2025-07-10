import axios, { AxiosInstance } from 'axios';
import { DashboardData, NotificationLog } from '../types';

interface AlertServiceConfig {
  baseUrl: string;
  timeout: number;
}

interface AlertRule {
  id?: number;
  name: string;
  description: string;
  alert_type: string;
  product_id?: number;
  threshold_value: number;
  comparison_operator: string;
  is_active: boolean;
  email_recipients?: string[];
  sms_recipients?: string[];
  created_at?: string;
  updated_at?: string;
}

interface AlertData {
  id: number;
  title: string;
  message: string;
  alert_type: string;
  severity: string;
  status: string;
  is_read: boolean;
  is_resolved: boolean;
  product_data?: any;
  created_at: string;
  updated_at: string;
}

class AlertService {
  private api: AxiosInstance;
  private baseUrl = 'http://localhost:8080/api/alerts';

  constructor(config: AlertServiceConfig) {
    this.api = axios.create({
      baseURL: config.baseUrl,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async getAlertsDashboard(): Promise<DashboardData> {
    try {
      const response = await this.api.get('/dashboard/', {
        headers: this.getAuthHeaders(),
      });
      
      return response.data;
    } catch (error) {
      console.error('Error en getAlertsDashboard:', error);
      // Devolver datos de fallback en caso de error
      return {
        total_alerts: 0,
        active_alerts: 0,
        critical_alerts: 0,
        acknowledged_alerts: 0,
        resolved_alerts: 0,
        alerts_by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
        alerts_by_type: { low_stock: 0, reorder_point: 0, expired: 0, high_stock: 0 },
        recent_alerts: [],
        alert_trends: {}
      };
    }
  }

  async getAlerts(filters?: {
    severity?: string;
    status?: string;
    product?: string;
    location?: string;
  }): Promise<{ results: AlertData[] }> {
    try {
      const params = new URLSearchParams();
      
      if (filters?.severity && filters.severity !== 'all') {
        params.append('severity', filters.severity);
      }
      if (filters?.status && filters.status !== 'all') {
        params.append('status', filters.status);
      }
      if (filters?.product) {
        params.append('product', filters.product);
      }
      if (filters?.location) {
        params.append('location', filters.location);
      }
      
      const response = await this.api.get(`/alerts/?${params}`, {
        headers: this.getAuthHeaders(),
      });
      
      return response.data;
    } catch (error) {
      console.error('Error en getAlerts:', error);
      return { results: [] };
    }
  }

  async acknowledgeAlert(alertId: number, note?: string): Promise<void> {
    try {
      await this.api.post(`/alerts/${alertId}/acknowledge/`, {
        note: note || '',
      }, {
        headers: this.getAuthHeaders(),
      });
    } catch (error) {
      console.error('Error al reconocer la alerta:', error);
      throw new Error('Error al reconocer la alerta');
    }
  }

  async resolveAlert(alertId: number, note?: string): Promise<void> {
    try {
      await this.api.post(`/alerts/${alertId}/resolve/`, {
        note: note || '',
      }, {
        headers: this.getAuthHeaders(),
      });
    } catch (error) {
      console.error('Error al resolver la alerta:', error);
      throw new Error('Error al resolver la alerta');
    }
  }

  async dismissAlert(alertId: number, note?: string): Promise<void> {
    try {
      await this.api.post(`/alerts/${alertId}/dismiss/`, {
        note: note || '',
      }, {
        headers: this.getAuthHeaders(),
      });
    } catch (error) {
      console.error('Error al descartar la alerta:', error);
      throw new Error('Error al descartar la alerta');
    }
  }

  async checkAlerts(): Promise<{ message: string; task_id: string }> {
    try {
      const response = await this.api.post('/check-alerts/', {}, {
        headers: this.getAuthHeaders(),
      });
      
      return response.data;
    } catch (error) {
      console.error('Error al verificar alertas:', error);
      throw new Error('Error al verificar alertas');
    }
  }

  async getAlertRules(): Promise<{ results: AlertRule[] }> {
    try {
      const response = await this.api.get('/rules/', {
        headers: this.getAuthHeaders(),
      });
      
      return response.data;
    } catch (error) {
      console.error('Error al cargar reglas de alerta:', error);
      throw new Error('Error al cargar reglas de alerta');
    }
  }

  async createAlertRule(rule: Partial<AlertRule>): Promise<AlertRule> {
    try {
      const response = await this.api.post('/rules/', rule, {
        headers: this.getAuthHeaders(),
      });
      
      return response.data;
    } catch (error) {
      console.error('Error al crear regla de alerta:', error);
      throw new Error('Error al crear regla de alerta');
    }
  }

  async updateAlertRule(ruleId: number, rule: Partial<AlertRule>): Promise<AlertRule> {
    try {
      const response = await this.api.put(`/rules/${ruleId}/`, rule, {
        headers: this.getAuthHeaders(),
      });
      
      return response.data;
    } catch (error) {
      console.error('Error al actualizar regla de alerta:', error);
      throw new Error('Error al actualizar regla de alerta');
    }
  }

  async deleteAlertRule(ruleId: number): Promise<void> {
    try {
      await this.api.delete(`/rules/${ruleId}/`, {
        headers: this.getAuthHeaders(),
      });
    } catch (error) {
      console.error('Error al eliminar regla de alerta:', error);
      throw new Error('Error al eliminar regla de alerta');
    }
  }

  async testAlertRule(ruleId: number): Promise<{ message: string; task_id: string }> {
    try {
      const response = await this.api.post(`/test-rule/${ruleId}/`, {}, {
        headers: this.getAuthHeaders(),
      });
      
      return response.data;
    } catch (error) {
      console.error('Error al probar regla de alerta:', error);
      throw new Error('Error al probar regla de alerta');
    }
  }

  async toggleAlertRule(ruleId: number): Promise<{ message: string; is_active: boolean }> {
    try {
      const response = await this.api.post(`/rules/${ruleId}/toggle/`, {}, {
        headers: this.getAuthHeaders(),
      });
      
      return response.data;
    } catch (error) {
      console.error('Error al cambiar estado de regla:', error);
      throw new Error('Error al cambiar estado de regla');
    }
  }

  async getNotificationLogs(): Promise<{ results: NotificationLog[] }> {
    try {
      const response = await this.api.get('/notifications/', {
        headers: this.getAuthHeaders(),
      });
      
      return response.data;
    } catch (error) {
      console.error('Error al cargar logs de notificaciones:', error);
      throw new Error('Error al cargar logs de notificaciones');
    }
  }
}

export const alertService = new AlertService({ baseUrl: 'http://localhost:8080/api/alerts', timeout: 10000 });
export type { AlertData, DashboardData, AlertRule, NotificationLog };
