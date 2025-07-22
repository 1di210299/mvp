import { useState, useEffect } from 'react';
import { alertService } from '../services/api';

export interface Notification {
  id: number;
  title: string;
  message: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  type: string;
  created_at: string;
  is_read: boolean;
}

export const useNotifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await alertService.getAlerts();
      const alertsData = response.results || response || [];
      
      // Transformar alertas a notificaciones
      const notificationsData: Notification[] = alertsData
        .filter((alert: any) => alert.status === 'active')
        .slice(0, 10) // Mostrar solo las 10 más recientes
        .map((alert: any) => ({
          id: alert.id,
          title: getAlertTitle(alert.alert_type),
          message: alert.message || getDefaultMessage(alert),
          severity: alert.severity || 'medium',
          type: alert.alert_type,
          created_at: alert.created_at,
          is_read: false // Por ahora, todas son no leídas
        }));
      
      setNotifications(notificationsData);
      setUnreadCount(notificationsData.length);
    } catch (error) {
      console.error('Error loading notifications:', error);
      setNotifications([]);
      setUnreadCount(0);
    } finally {
      setLoading(false);
    }
  };

  const getAlertTitle = (alertType: string): string => {
    const titles: { [key: string]: string } = {
      'low_stock': 'Stock Bajo',
      'high_stock': 'Stock Alto',
      'reorder_urgent': 'Reorden Urgente',
      'expired': 'Producto Vencido',
      'expiration': 'Próximo a Vencer',
      'negative_stock': 'Stock Negativo',
      'stockout_risk': 'Riesgo de Agotamiento',
      'high_demand': 'Demanda Alta',
      'demand_vs_stock': 'Desbalance Demanda/Stock',
      'forecast_accuracy': 'Precisión de Pronóstico'
    };
    return titles[alertType] || 'Alerta';
  };

  const getDefaultMessage = (alert: any): string => {
    if (alert.product_name) {
      switch (alert.alert_type) {
        case 'low_stock':
          return `${alert.product_name} tiene stock bajo`;
        case 'high_stock':
          return `${alert.product_name} tiene stock alto`;
        case 'reorder_urgent':
          return `Se necesita reordenar ${alert.product_name} urgentemente`;
        case 'expired':
          return `${alert.product_name} ha expirado`;
        case 'expiration':
          return `${alert.product_name} expira pronto`;
        default:
          return `Alerta para ${alert.product_name}`;
      }
    }
    return alert.message || 'Nueva alerta de inventario';
  };

  const markAsRead = (notificationId: number) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === notificationId 
          ? { ...notif, is_read: true }
          : notif
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, is_read: true }))
    );
    setUnreadCount(0);
  };

  useEffect(() => {
    loadNotifications();
    
    // Actualizar notificaciones cada 30 segundos
    const interval = setInterval(loadNotifications, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    notifications,
    unreadCount,
    loading,
    loadNotifications,
    markAsRead,
    markAllAsRead
  };
};
