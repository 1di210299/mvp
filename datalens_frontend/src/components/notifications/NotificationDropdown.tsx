import React from 'react';
import { Link } from 'react-router-dom';
import { Bell, AlertTriangle, Clock, CheckCircle } from '../ui/icons';
import { Notification } from '../../hooks/useNotifications';

interface NotificationDropdownProps {
  notifications: Notification[];
  unreadCount: number;
  onMarkAsRead: (id: number) => void;
  onMarkAllAsRead: () => void;
  onClose: () => void;
}

export const NotificationDropdown: React.FC<NotificationDropdownProps> = ({
  notifications,
  unreadCount,
  onMarkAsRead,
  onMarkAllAsRead,
  onClose
}) => {
  const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Ahora';
    if (diffInMinutes < 60) return `${diffInMinutes}m`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h`;
    return `${Math.floor(diffInMinutes / 1440)}d`;
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return 'text-red-500';
      case 'high': return 'text-orange-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-blue-500';
      default: return 'text-gray-500';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <Bell className="w-4 h-4" />;
    }
  };

  return (
    <div className="notification-dropdown">
      <div className="notification-header">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Notificaciones
          </h3>
          {unreadCount > 0 && (
            <button
              onClick={onMarkAllAsRead}
              className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
            >
              Marcar todas como leídas
            </button>
          )}
        </div>
        {unreadCount > 0 && (
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {unreadCount} nueva{unreadCount !== 1 ? 's' : ''}
          </p>
        )}
      </div>

      <div className="notification-list">
        {notifications.length === 0 ? (
          <div className="notification-empty">
            <div className="flex flex-col items-center justify-center py-8">
              <CheckCircle className="w-12 h-12 text-green-500 mb-2" />
              <p className="text-gray-600 dark:text-gray-400">
                No hay notificaciones
              </p>
            </div>
          </div>
        ) : (
          notifications.map((notification) => (
            <div
              key={notification.id}
              className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
              onClick={() => !notification.is_read && onMarkAsRead(notification.id)}
            >
              <div className="notification-icon">
                <div className={getSeverityColor(notification.severity)}>
                  {getSeverityIcon(notification.severity)}
                </div>
              </div>
              
              <div className="notification-content">
                <div className="notification-title">
                  {notification.title}
                </div>
                <div className="notification-message">
                  {notification.message}
                </div>
                <div className="notification-time">
                  <Clock className="w-3 h-3" />
                  {formatTimeAgo(notification.created_at)}
                </div>
              </div>
              
              {!notification.is_read && (
                <div className="notification-unread-dot"></div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="notification-footer">
        <Link
          to="/app/alerts"
          className="notification-view-all"
          onClick={onClose}
        >
          Ver todas las alertas
        </Link>
      </div>
    </div>
  );
};
