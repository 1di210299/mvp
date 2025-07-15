import React, { useState, useEffect } from 'react';
import { apiConfig } from '../../config/api';

interface Alert {
  id: number;
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  status: string;
}

const AlertsList: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${apiConfig.baseURL}/alerts/alerts/?limit=5&status=active`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const alertsData = data.results || data;
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError('No se pudieron cargar las alertas');
      // Fallback: mostrar vacío en lugar de datos mock
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const formatTime = (dateString: string) => {
    const now = new Date();
    const alertDate = new Date(dateString);
    const diffMs = now.getTime() - alertDate.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Ahora';
    if (diffMins < 60) return `${diffMins} min`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} h`;
    return `${Math.floor(diffMins / 1440)} días`;
  };

  if (loading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3>Alertas Recientes</h3>
        </div>
        <div className="card-body">
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Cargando alertas...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>Alertas Recientes</h3>
      </div>
      <div className="card-body">
        {error ? (
          <div className="text-center py-4">
            <p className="text-red-500">{error}</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-4">
            <p className="text-gray-500">No hay alertas activas</p>
          </div>
        ) : (
          <div className="alerts-list">
            {alerts.map(alert => (
              <div key={alert.id} className={`alert-item severity-${alert.severity}`}>
                <div className="alert-content">
                  <h4 className="alert-title">{alert.title}</h4>
                  <p className="alert-message">{alert.message}</p>
                </div>
                <div className="alert-time">
                  {formatTime(alert.created_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsList;
