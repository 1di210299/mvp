// src/components/NotificationsMenu.tsx
import React, { useState, useRef, useEffect } from 'react';
import { 
  Bell,
  X,
  Settings,
  BarChart,
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react';

// Ejemplo de notificaciones
const sampleNotifications = [
  {
    id: 1,
    type: 'success',
    title: 'Dataset actualizado',
    message: 'El dataset "Ventas Q1 2025" ha sido actualizado correctamente.',
    time: '5 minutos',
    read: false
  },
  {
    id: 2,
    type: 'warning',
    title: 'Procesamiento lento',
    message: 'El análisis del dataset "Clientes 2024" está tardando más de lo esperado.',
    time: '20 minutos',
    read: false
  },
  {
    id: 3,
    type: 'info',
    title: 'Nuevo reporte disponible',
    message: 'El reporte mensual de ventas ya está disponible para revisión.',
    time: '1 hora',
    read: true
  },
  {
    id: 4,
    type: 'alert',
    title: 'Error de sincronización',
    message: 'No se pudieron sincronizar los datos de inventario. Intente nuevamente.',
    time: '2 horas',
    read: true
  }
];

const NotificationsMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState(sampleNotifications);
  const [unreadCount, setUnreadCount] = useState(
    sampleNotifications.filter(n => !n.read).length
  );
  const menuRef = useRef<HTMLDivElement>(null);
  
  // Cerrar el menú al hacer clic fuera de él
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  // Marcar una notificación como leída
  const markAsRead = (id: number) => {
    setNotifications(
      notifications.map(notification => 
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };
  
  // Marcar todas como leídas
  const markAllAsRead = () => {
    setNotifications(
      notifications.map(notification => ({ ...notification, read: true }))
    );
    setUnreadCount(0);
  };
  
  // Eliminar una notificación
  const removeNotification = (id: number) => {
    const notificationToRemove = notifications.find(n => n.id === id);
    setNotifications(notifications.filter(n => n.id !== id));
    
    // Si la notificación que se elimina no estaba leída, actualizar contador
    if (notificationToRemove && !notificationToRemove.read) {
      setUnreadCount(prev => prev - 1);
    }
  };
  
  // Obtener el icono según el tipo de notificación
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle size={18} className="text-green-400" />;
      case 'warning':
        return <AlertTriangle size={18} className="text-yellow-400" />;
      case 'info':
        return <Info size={18} className="text-blue-400" />;
      case 'alert':
        return <AlertTriangle size={18} className="text-red-400" />;
      default:
        return <Info size={18} className="text-cyber-cyan" />;
    }
  };
  
  return (
    <div className="relative" ref={menuRef}>
      <button 
        className="p-1.5 text-cyber-text/80 hover:text-cyber-cyan rounded-full relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 w-4 h-4 bg-red-500 rounded-full text-white text-xs flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-cyber-dark/95 backdrop-blur-md border border-cyber-cyan/30 rounded-lg shadow-lg overflow-hidden z-50">
          <div className="flex justify-between items-center p-3 border-b border-cyber-detail/30">
            <h3 className="font-medium text-cyber-text">Notificaciones</h3>
            <div className="flex space-x-2">
              <button 
                className="text-xs text-cyber-text/70 hover:text-cyber-cyan"
                onClick={markAllAsRead}
              >
                Marcar todo como leído
              </button>
              <button className="text-cyber-text/70 hover:text-cyber-cyan">
                <Settings size={14} />
              </button>
            </div>
          </div>
          
          <div className="max-h-80 overflow-y-auto">
            {notifications.length > 0 ? (
              notifications.map(notification => (
                <div 
                  key={notification.id} 
                  className={`p-3 border-b border-cyber-detail/30 hover:bg-cyber-detail/10 relative ${!notification.read ? 'bg-cyber-detail/20' : ''}`}
                >
                  <div className="flex">
                    <div className="mt-0.5 mr-3">
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className="flex-grow">
                      <div className="flex justify-between">
                        <h4 className="text-sm font-medium text-cyber-text">{notification.title}</h4>
                        <span className="text-xs text-cyber-text/50">{notification.time}</span>
                      </div>
                      <p className="text-xs text-cyber-text/70 mt-1">{notification.message}</p>
                      {!notification.read && (
                        <button 
                          className="text-xs text-cyber-cyan hover:underline mt-1"
                          onClick={() => markAsRead(notification.id)}
                        >
                          Marcar como leído
                        </button>
                      )}
                    </div>
                    <button 
                      className="ml-2 text-cyber-text/50 hover:text-cyber-text"
                      onClick={() => removeNotification(notification.id)}
                    >
                      <X size={14} />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 text-center">
                <div className="inline-flex items-center justify-center p-3 rounded-full bg-cyber-detail/20 text-cyber-text/50 mb-2">
                  <BarChart size={24} />
                </div>
                <p className="text-sm text-cyber-text/70">No tienes notificaciones</p>
              </div>
            )}
          </div>
          
          <div className="p-3 border-t border-cyber-detail/30 text-center">
            <button className="text-xs text-cyber-cyan hover:underline">
              Ver todas las notificaciones
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationsMenu;