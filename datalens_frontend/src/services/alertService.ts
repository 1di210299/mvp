import { AlertData, DashboardData } from '../types';

interface AlertRule {
  id: number;
  name: string;
  alert_type: string;
  condition: string;
  threshold: number;
  severity: string;
  is_active: boolean;
  product?: number;
  location?: number;
  created_at: string;
}

interface NotificationLog {
  id: number;
  alert: number;
  notification_type: string;
  recipient: string;
  status: string;
  sent_at: string;
}

class AlertService {
  private baseUrl = 'http://localhost:8081/api/alerts';
  
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async getAlertsDashboard(): Promise<DashboardData> {
    try {
      const response = await fetch(`${this.baseUrl}/dashboard/`, {
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Token de autenticación expirado');
        }
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
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
      
      const response = await fetch(`${this.baseUrl}/alerts/?${params}`, {
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar alertas');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error en getAlerts:', error);
      return { results: [] };
    }
  }

  async acknowledgeAlert(alertId: number, note?: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/alerts/${alertId}/acknowledge/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ note: note || '' }),
    });
    
    if (!response.ok) {
      throw new Error('Error al reconocer la alerta');
    }
  }

  async resolveAlert(alertId: number, note?: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/alerts/${alertId}/resolve/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ note: note || '' }),
    });
    
    if (!response.ok) {
      throw new Error('Error al resolver la alerta');
    }
  }

  async dismissAlert(alertId: number, note?: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/alerts/${alertId}/dismiss/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ note: note || '' }),
    });
    
    if (!response.ok) {
      throw new Error('Error al descartar la alerta');
    }
  }

  async checkAlerts(): Promise<{ message: string; task_id: string }> {
    const response = await fetch(`${this.baseUrl}/check-alerts/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Error al verificar alertas');
    }
    
    return response.json();
  }

  async getAlertRules(): Promise<{ results: AlertRule[] }> {
    const response = await fetch(`${this.baseUrl}/rules/`, {
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Error al cargar reglas de alerta');
    }
    
    return response.json();
  }

  async createAlertRule(rule: Partial<AlertRule>): Promise<AlertRule> {
    const response = await fetch(`${this.baseUrl}/rules/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(rule),
    });
    
    if (!response.ok) {
      throw new Error('Error al crear regla de alerta');
    }
    
    return response.json();
  }

  async updateAlertRule(ruleId: number, rule: Partial<AlertRule>): Promise<AlertRule> {
    const response = await fetch(`${this.baseUrl}/rules/${ruleId}/`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(rule),
    });
    
    if (!response.ok) {
      throw new Error('Error al actualizar regla de alerta');
    }
    
    return response.json();
  }

  async deleteAlertRule(ruleId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/rules/${ruleId}/`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Error al eliminar regla de alerta');
    }
  }

  async testAlertRule(ruleId: number): Promise<{ message: string; task_id: string }> {
    const response = await fetch(`${this.baseUrl}/test-rule/${ruleId}/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Error al probar regla de alerta');
    }
    
    return response.json();
  }

  async toggleAlertRule(ruleId: number): Promise<{ message: string; is_active: boolean }> {
    const response = await fetch(`${this.baseUrl}/rules/${ruleId}/toggle/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Error al cambiar estado de regla');
    }
    
    return response.json();
  }

  async getNotificationLogs(): Promise<{ results: NotificationLog[] }> {
    const response = await fetch(`${this.baseUrl}/notifications/`, {
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Error al cargar logs de notificaciones');
    }
    
    return response.json();
  }
}

export const alertService = new AlertService();
export type { AlertData, DashboardData, AlertRule, NotificationLog };
