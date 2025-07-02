import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Badge,
  Alert,
  AlertDescription
} from '../components/ui';
import {
  Bell,
  AlertTriangle,
  CheckCircle,
  Clock,
  X,
  RefreshCw,
  Settings,
  TrendingUp
} from '../components/ui/icons';
import { alertService, AlertData, DashboardData } from '../services/alertService';
import './AlertsPage.css';

const AlertsPage: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  const fetchDashboardData = async () => {
    try {
      const data = await alertService.getDashboard();
      setDashboardData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    }
  };

  const fetchAlerts = async () => {
    try {
      const data = await alertService.getAlerts({
        severity: selectedSeverity,
        status: selectedStatus
      });
      setAlerts(data.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    }
  };

  const handleAlertAction = async (alertId: number, action: 'acknowledge' | 'resolve' | 'dismiss', note?: string) => {
    try {
      switch (action) {
        case 'acknowledge':
          await alertService.acknowledgeAlert(alertId, note);
          break;
        case 'resolve':
          await alertService.resolveAlert(alertId, note);
          break;
        case 'dismiss':
          await alertService.dismissAlert(alertId, note);
          break;
      }
      
      // Actualizar datos
      await Promise.all([fetchDashboardData(), fetchAlerts()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    }
  };

  const checkAlerts = async () => {
    try {
      setLoading(true);
      await alertService.checkAlerts();
      
      // Esperar un momento para que se procesen las alertas
      setTimeout(() => {
        fetchDashboardData();
        fetchAlerts();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchDashboardData(), fetchAlerts()]);
      setLoading(false);
    };
    
    loadData();
    
    // Actualizar cada 30 segundos
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchAlerts();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [selectedSeverity, selectedStatus]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <Bell className="w-4 h-4" />;
      case 'acknowledged': return <Clock className="w-4 h-4" />;
      case 'resolved': return <CheckCircle className="w-4 h-4" />;
      case 'dismissed': return <X className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-red-600';
      case 'acknowledged': return 'text-yellow-600';
      case 'resolved': return 'text-green-600';
      case 'dismissed': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  if (loading && !dashboardData) {
    return (
      <div className="alerts-page loading">
        <div className="loading-spinner">Cargando dashboard de alertas...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alerts-page error">
        <Alert className="error-alert">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="alerts-page">
      <div className="alerts-header">
        <h1 className="alerts-title">
          <Bell className="w-6 h-6" />
          Centro de Alertas
        </h1>
        <div className="alerts-actions">
          <Button 
            onClick={checkAlerts} 
            disabled={loading}
            className="check-alerts-btn"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Verificar Alertas
          </Button>
          <Button variant="outline" className="settings-btn">
            <Settings className="w-4 h-4" />
            Configurar
          </Button>
        </div>
      </div>

      {/* Dashboard Cards */}
      <div className="dashboard-cards">
        <Card className="stat-card total">
          <CardHeader>
            <CardTitle className="stat-title">
              <Bell className="w-5 h-5" />
              Total Alertas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value">{dashboardData?.total_alerts || 0}</div>
          </CardContent>
        </Card>

        <Card className="stat-card active">
          <CardHeader>
            <CardTitle className="stat-title">
              <AlertTriangle className="w-5 h-5" />
              Alertas Activas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value">{dashboardData?.active_alerts || 0}</div>
          </CardContent>
        </Card>

        <Card className="stat-card critical">
          <CardHeader>
            <CardTitle className="stat-title">
              <TrendingUp className="w-5 h-5" />
              Críticas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value">{dashboardData?.critical_alerts || 0}</div>
          </CardContent>
        </Card>

        <Card className="stat-card resolved">
          <CardHeader>
            <CardTitle className="stat-title">
              <CheckCircle className="w-5 h-5" />
              Resueltas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value">{dashboardData?.resolved_alerts || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="alerts-filters">
        <div className="filter-group">
          <label>Severidad:</label>
          <select 
            value={selectedSeverity} 
            onChange={(e) => setSelectedSeverity(e.target.value)}
          >
            <option value="all">Todas</option>
            <option value="critical">Crítica</option>
            <option value="high">Alta</option>
            <option value="medium">Media</option>
            <option value="low">Baja</option>
          </select>
        </div>
        
        <div className="filter-group">
          <label>Estado:</label>
          <select 
            value={selectedStatus} 
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option value="all">Todos</option>
            <option value="active">Activas</option>
            <option value="acknowledged">Reconocidas</option>
            <option value="resolved">Resueltas</option>
            <option value="dismissed">Descartadas</option>
          </select>
        </div>
      </div>

      {/* Alerts List */}
      <div className="alerts-list">
        {alerts.length === 0 ? (
          <Card className="no-alerts">
            <CardContent>
              <div className="no-alerts-content">
                <CheckCircle className="w-12 h-12" />
                <h3>No hay alertas</h3>
                <p>No se encontraron alertas con los filtros seleccionados.</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          alerts.map((alert) => (
            <Card key={alert.id} className={`alert-card ${alert.severity} ${alert.status}`}>
              <CardHeader>
                <div className="alert-header">
                  <div className="alert-title-section">
                    <div className="alert-status">
                      {getStatusIcon(alert.status)}
                    </div>
                    <div>
                      <CardTitle className="alert-title">{alert.title}</CardTitle>
                      <div className="alert-meta">
                        <Badge className={`severity-badge ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </Badge>
                        <span className={`status-text ${getStatusColor(alert.status)}`}>
                          {alert.status}
                        </span>
                        <span className="alert-time">
                          {new Date(alert.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="alert-actions">
                    {alert.status === 'active' && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleAlertAction(alert.id, 'acknowledge')}
                        >
                          <Clock className="w-4 h-4" />
                          Reconocer
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleAlertAction(alert.id, 'resolve')}
                        >
                          <CheckCircle className="w-4 h-4" />
                          Resolver
                        </Button>
                      </>
                    )}
                    
                    {alert.status === 'acknowledged' && (
                      <Button
                        size="sm"
                        onClick={() => handleAlertAction(alert.id, 'resolve')}
                      >
                        <CheckCircle className="w-4 h-4" />
                        Resolver
                      </Button>
                    )}
                    
                    {(alert.status === 'active' || alert.status === 'acknowledged') && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleAlertAction(alert.id, 'dismiss')}
                      >
                        <X className="w-4 h-4" />
                        Descartar
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <p className="alert-message">{alert.message}</p>
                
                <div className="alert-details">
                  {alert.product_data && (
                    <div className="detail-item">
                      <strong>Producto:</strong> {alert.product_data.name} ({alert.product_data.sku})
                    </div>
                  )}
                  
                  {alert.location_data && (
                    <div className="detail-item">
                      <strong>Ubicación:</strong> {alert.location_data.name}
                    </div>
                  )}
                  
                  {alert.current_value !== null && (
                    <div className="detail-item">
                      <strong>Valor actual:</strong> {alert.current_value}
                    </div>
                  )}
                  
                  {alert.threshold_value !== null && (
                    <div className="detail-item">
                      <strong>Umbral:</strong> {alert.threshold_value}
                    </div>
                  )}
                  
                  {alert.rule_data && (
                    <div className="detail-item">
                      <strong>Regla:</strong> {alert.rule_data.name}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default AlertsPage;
