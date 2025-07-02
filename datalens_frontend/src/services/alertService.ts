interface AlertData {
  id: number;
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved' | 'dismissed';
  current_value: number;
  threshold_value: number;
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  product_data?: {
    id: number;
    name: string;
    sku: string;
  };
  location_data?: {
    id: number;
    name: string;
  };
  rule_data?: {
    id: number;
    name: string;
    alert_type: string;
  };
}

interface DashboardData {
  total_alerts: number;
  active_alerts: number;
  critical_alerts: number;
  acknowledged_alerts: number;
  resolved_alerts: number;
  alerts_by_severity: Record<string, number>;
  alerts_by_type: Record<string, number>;
  recent_alerts: AlertData[];
  alert_trends: Record<string, number>;
}

interface AlertRule {
  id: number;
  name: string;
  description: string;
  alert_type: string;
  threshold_value?: number;
  threshold_percentage?: number;
  days_before_expiration?: number;
  send_email: boolean;
  send_notification: boolean;
  frequency: string;
  additional_emails: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface NotificationLog {
  id: number;
  notification_type: string;
  recipient: string;
  subject: string;
  content: string;
  status: string;
  sent_at?: string;
  delivered_at?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

class AlertService {
  private baseUrl = '/api/alerts';
  
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async getDashboard(): Promise<DashboardData> {
    const response = await fetch(`${this.baseUrl}/dashboard/`, {
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Error al cargar datos del dashboard');
    }
    
    return response.json();
  }

  async getAlerts(filters?: {
    severity?: string;
    status?: string;
    product?: string;
    location?: string;
  }): Promise<{ results: AlertData[] }> {
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
    
    return response.json();
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
    const response = await fetch(`${this.baseUrl}/rules/${ruleId}/test_rule/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Error al probar regla de alerta');
    }
    
    return response.json();
  }

  async toggleAlertRule(ruleId: number): Promise<{ message: string; is_active: boolean }> {
    const response = await fetch(`${this.baseUrl}/rules/${ruleId}/toggle_active/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Error al cambiar estado de regla de alerta');
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
