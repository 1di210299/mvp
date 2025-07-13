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
  TrendingUp,
  TrendingDown,
  Package,
  Calendar,
  BarChart3,
  Target,
  Zap
} from '../components/ui/icons';
import { alertService } from '../services/api';
import { AlertData, DashboardData } from '../types';
import './AlertsPage.css';

const AlertsPage: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<AlertData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');

  const fetchDashboardData = async () => {
    try {
      console.log('🔍 Iniciando fetchDashboardData...');
      const dashboardData = await alertService.getAlertsDashboard();
      console.log('✅ Dashboard data recibida:', dashboardData);
      setDashboardData(dashboardData);
    } catch (err) {
      console.error('❌ Error fetching alerts dashboard:', err);
      console.error('❌ Error completo:', JSON.stringify(err, null, 2));
      const fallbackData: DashboardData = {
        total_alerts: 0,
        active_alerts: 0,
        critical_alerts: 0,
        acknowledged_alerts: 0,
        resolved_alerts: 0,
        alerts_by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
        alerts_by_type: { 
          low_stock: 0, 
          high_stock: 0,
          high_demand: 0,
          reorder_urgent: 0,
          expired: 0,
          expiration: 0,
          negative_stock: 0,
          stockout_risk: 0,
          demand_vs_stock: 0,
          forecast_accuracy: 0
        },
        notification_stats: {},
        recent_alerts: [],
        alert_trends: {}
      };
      setDashboardData(fallbackData);
      setError('Error al conectar con las alertas. Usando modo offline.');
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await alertService.getAlerts();
      const alertsData = response.results || response || [];
      
      const transformedAlerts: AlertData[] = alertsData.map((alert: any) => ({
        ...alert,
        status: alert.status || 'active',
        current_value: alert.current_value || null,
        threshold_value: alert.threshold_value || null,
        priority_score: alert.priority_score || 50,
        source: alert.source || 'rule',
        context_data: alert.context_data || {},
        recommended_actions: alert.recommended_actions || [],
        demand_forecast: alert.demand_forecast || null,
        reorder_recommendation: alert.reorder_recommendation || null,
        forecast_model: alert.forecast_model || null
      }));
      
      // Ordenar por prioridad y fecha
      transformedAlerts.sort((a, b) => {
        if (a.priority_score !== b.priority_score) {
          return (b.priority_score || 50) - (a.priority_score || 50);
        }
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      
      setAlerts(transformedAlerts);
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setAlerts([]);
      setError('Error al cargar alertas. Verificar conexión con API.');
    }
  };

  // Aplicar filtros localmente
  const applyFilters = () => {
    let filtered = alerts;

    if (selectedSeverity !== 'all') {
      filtered = filtered.filter(alert => alert.severity === selectedSeverity);
    }

    if (selectedStatus !== 'all') {
      filtered = filtered.filter(alert => alert.status === selectedStatus);
    }

    if (selectedType !== 'all') {
      filtered = filtered.filter(alert => 
        alert.rule_data?.alert_type === selectedType || 
        alert.title.toLowerCase().includes(selectedType.toLowerCase())
      );
    }

    if (selectedSource !== 'all') {
      filtered = filtered.filter(alert => alert.source === selectedSource);
    }

    setFilteredAlerts(filtered);
  };

  useEffect(() => {
    applyFilters();
  }, [alerts, selectedSeverity, selectedStatus, selectedType, selectedSource]);

  const checkAlerts = async () => {
    try {
      setLoading(true);
      await alertService.checkAlerts();
      
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

  const handleAlertAction = async (alertId: number, action: 'acknowledge' | 'resolve' | 'dismiss') => {
    try {
      switch (action) {
        case 'acknowledge':
          await alertService.acknowledgeAlert(alertId);
          break;
        case 'resolve':
          await alertService.resolveAlert(alertId);
          break;
        case 'dismiss':
          await alertService.dismissAlert(alertId);
          break;
      }
      
      // Refrescar alertas después de la acción
      fetchAlerts();
    } catch (err) {
      console.error(`Error executing ${action} on alert ${alertId}:`, err);
      setError(`Error al ${action} la alerta`);
    }
  };

  const getAlertTypeIcon = (alertType: string, source: string) => {
    if (source === 'forecast') {
      return <BarChart3 className="w-4 h-4" />;
    }
    
    switch (alertType) {
      case 'low_stock':
      case 'negative_stock':
        return <TrendingDown className="w-4 h-4" />;
      case 'high_stock':
        return <TrendingUp className="w-4 h-4" />;
      case 'high_demand':
      case 'demand_vs_stock':
      case 'stockout_risk':
        return <Target className="w-4 h-4" />;
      case 'expiration':
      case 'expired':
        return <Calendar className="w-4 h-4" />;
      case 'reorder_urgent':
        return <Zap className="w-4 h-4" />;
      default:
        return <Package className="w-4 h-4" />;
    }
  };

  const getAlertTypeDisplay = (alertType: string) => {
    const typeMap: Record<string, string> = {
      'low_stock': 'Stock Bajo',
      'high_stock': 'Stock Alto',
      'high_demand': 'Demanda Alta',
      'demand_vs_stock': 'Demanda vs Stock',
      'stockout_risk': 'Riesgo Agotamiento',
      'reorder_urgent': 'Reorden Urgente',
      'expiration': 'Próximo Vencimiento',
      'expired': 'Vencido',
      'negative_stock': 'Stock Negativo',
      'forecast_accuracy': 'Precisión Pronóstico',
      'seasonal_demand': 'Demanda Estacional',
      'no_movement': 'Sin Movimiento'
    };
    return typeMap[alertType] || alertType;
  };

  const getPriorityColor = (priorityScore: number) => {
    if (priorityScore >= 80) return 'text-red-600 bg-red-50';
    if (priorityScore >= 60) return 'text-orange-600 bg-orange-50';
    if (priorityScore >= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500 text-white';
      case 'high': return 'bg-orange-500 text-white';
      case 'medium': return 'bg-yellow-500 text-black';
      case 'low': return 'bg-green-500 text-white';
      default: return 'bg-gray-500 text-white';
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <AlertTriangle className="w-4 h-4" />;
      case 'acknowledged': return <Clock className="w-4 h-4" />;
      case 'resolved': return <CheckCircle className="w-4 h-4" />;
      case 'dismissed': return <X className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchDashboardData(), fetchAlerts()]);
      setLoading(false);
    };
    
    loadData();
    
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchAlerts();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

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
          Centro de Alertas Inteligente
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

      {/* Enhanced Dashboard Cards */}
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
            <div className="stat-trend">
              {dashboardData?.alerts_by_type && Object.values(dashboardData.alerts_by_type).length > 0 && (
                <span className="text-sm text-gray-500">
                  {Object.keys(dashboardData.alerts_by_type).length} tipos diferentes
                </span>
              )}
            </div>
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
            <div className="stat-trend">
              <span className="text-sm text-gray-500">
                Requieren atención
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card critical">
          <CardHeader>
            <CardTitle className="stat-title">
              <Zap className="w-5 h-5" />
              Críticas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value">{dashboardData?.critical_alerts || 0}</div>
            <div className="stat-trend">
              <span className="text-sm text-red-500">
                Acción inmediata
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card forecasting">
          <CardHeader>
            <CardTitle className="stat-title">
              <BarChart3 className="w-5 h-5" />
              Predicciones
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value">
              {filteredAlerts.filter(a => a.source === 'forecast' || a.demand_forecast || a.reorder_recommendation).length}
            </div>
            <div className="stat-trend">
              <span className="text-sm text-blue-500">
                Basadas en IA
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Enhanced Filters */}
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

        <div className="filter-group">
          <label>Tipo:</label>
          <select 
            value={selectedType} 
            onChange={(e) => setSelectedType(e.target.value)}
          >
            <option value="all">Todos</option>
            <option value="low_stock">Stock Bajo</option>
            <option value="high_demand">Demanda Alta</option>
            <option value="reorder_urgent">Reorden Urgente</option>
            <option value="expiration">Vencimientos</option>
            <option value="stockout_risk">Riesgo Agotamiento</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Origen:</label>
          <select 
            value={selectedSource} 
            onChange={(e) => setSelectedSource(e.target.value)}
          >
            <option value="all">Todos</option>
            <option value="rule">Reglas</option>
            <option value="forecast">Predicciones</option>
            <option value="system">Sistema</option>
            <option value="manual">Manual</option>
          </select>
        </div>
      </div>

      {/* Enhanced Alerts List */}
      <div className="alerts-list">
        {filteredAlerts.length === 0 ? (
          <Card className="no-alerts">
            <CardContent>
              <div className="no-alerts-content">
                <CheckCircle className="w-12 h-12" />
                <h3>No hay alertas</h3>
                <p>No se encontraron alertas con los filtros seleccionados.</p>
                <Button onClick={checkAlerts} className="mt-4">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Verificar Nuevas Alertas
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredAlerts.map((alert) => (
            <Card key={alert.id} className={`alert-card ${alert.severity} ${alert.status} ${alert.source}`}>
              <CardHeader>
                <div className="alert-header">
                  <div className="alert-title-section">
                    <div className="alert-status">
                      {getAlertTypeIcon(alert.rule_data?.alert_type || '', alert.source)}
                    </div>
                    <div>
                      <CardTitle className="alert-title">
                        {alert.title}
                        {alert.source === 'forecast' && (
                          <Badge className="ml-2 bg-blue-100 text-blue-800">
                            <BarChart3 className="w-3 h-3 mr-1" />
                            IA
                          </Badge>
                        )}
                      </CardTitle>
                      <div className="alert-meta">
                        <Badge className={`severity-badge ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </Badge>
                        <Badge className={`priority-badge ${getPriorityColor(alert.priority_score || 50)}`}>
                          Prioridad: {alert.priority_score || 50}/100
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

                  {/* Forecasting Information */}
                  {alert.demand_forecast && (
                    <div className="forecast-info">
                      <div className="detail-item forecast-item">
                        <strong>📈 Demanda proyectada:</strong> {alert.demand_forecast.predicted_demand}
                        <span className="forecast-confidence">
                          (Confianza: {alert.demand_forecast.confidence_level}%)
                        </span>
                      </div>
                      <div className="detail-item">
                        <strong>Rango:</strong> {alert.demand_forecast.lower_bound} - {alert.demand_forecast.upper_bound}
                      </div>
                    </div>
                  )}

                  {alert.reorder_recommendation && (
                    <div className="reorder-info">
                      <div className="detail-item reorder-item">
                        <strong>📋 Recomendación:</strong> Ordenar {alert.reorder_recommendation.recommended_quantity} unidades
                      </div>
                      <div className="detail-item">
                        <strong>Fecha recomendada:</strong> {new Date(alert.reorder_recommendation.recommended_order_date).toLocaleDateString()}
                      </div>
                      {alert.reorder_recommendation.estimated_cost && (
                        <div className="detail-item">
                          <strong>Costo estimado:</strong> S/ {alert.reorder_recommendation.estimated_cost}
                        </div>
                      )}
                    </div>
                  )}

                  {alert.forecast_model && (
                    <div className="detail-item model-info">
                      <strong>🤖 Modelo:</strong> {alert.forecast_model.name}
                      {alert.forecast_model.accuracy_score && (
                        <span className="model-accuracy">
                          (Precisión: {alert.forecast_model.accuracy_score}%)
                        </span>
                      )}
                    </div>
                  )}
                  
                  {alert.rule_data && (
                    <div className="detail-item">
                      <strong>Regla:</strong> {alert.rule_data.name}
                    </div>
                  )}

                  {/* Context Data */}
                  {alert.context_data && Object.keys(alert.context_data).length > 0 && (
                    <div className="context-data">
                      <strong>Información adicional:</strong>
                      <ul className="context-list">
                        {Object.entries(alert.context_data).map(([key, value]) => (
                          <li key={key}>
                            <strong>{key}:</strong> {String(value)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recommended Actions */}
                  {alert.recommended_actions && alert.recommended_actions.length > 0 && (
                    <div className="recommended-actions">
                      <strong>🎯 Acciones recomendadas:</strong>
                      <ul className="actions-list">
                        {alert.recommended_actions.map((action, index) => (
                          <li key={index}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Quick Links */}
                {(alert.demand_forecast || alert.reorder_recommendation) && (
                  <div className="alert-quick-links">
                    <a href="/app/forecasting" target="_blank" rel="noopener noreferrer">
                      <Button size="sm" variant="outline">
                        <BarChart3 className="w-4 h-4 mr-1" />
                        Ver Predicciones
                      </Button>
                    </a>
                    {alert.product_data && (
                      <a href={`/app/inventory?product=${alert.product_data.id}`} target="_blank" rel="noopener noreferrer">
                        <Button size="sm" variant="outline">
                          <Package className="w-4 h-4 mr-1" />
                          Ver Producto
                        </Button>
                      </a>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default AlertsPage;
