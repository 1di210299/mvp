// src/components/DataMonitorPanel.tsx
import React, { useState, useEffect } from 'react';
import { monitorService, MonitoringAlert } from '../api/monitor-service';
import { agentService } from '../api/agent-service';
import { AlertTriangle, Clock, CheckCircle, XCircle, TrendingUp, Activity, Eye } from 'lucide-react';

interface DataMonitorPanelProps {
  datasetId: number;
  refreshInterval?: number; // en milisegundos
}

const DataMonitorPanel: React.FC<DataMonitorPanelProps> = ({ 
  datasetId, 
  refreshInterval = 60000 // 1 minuto por defecto
}) => {
  const [alerts, setAlerts] = useState<MonitoringAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastAnalysisTime, setLastAnalysisTime] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Cargar alertas iniciales
  useEffect(() => {
    fetchAlerts();
    
    // Configurar intervalo de refresco
    const intervalId = setInterval(fetchAlerts, refreshInterval);
    
    // Limpiar intervalo al desmontar
    return () => clearInterval(intervalId);
  }, [datasetId, refreshInterval]);

  const fetchAlerts = async () => {
    try {
      const response = await monitorService.getActiveAlerts(datasetId);
      setAlerts(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching alerts:', err);
      setError(err.response?.data?.error || 'Error al cargar alertas');
    } finally {
      setLoading(false);
    }
  };
  
  const handleResolveAlert = async (alertId: number) => {
    try {
      await monitorService.resolveAlert(alertId, 'Resuelta por el usuario');
      // Actualizar la lista de alertas
      setAlerts(alerts.filter(alert => alert.id !== alertId));
    } catch (err: any) {
      console.error('Error resolving alert:', err);
      alert(err.response?.data?.error || 'Error al resolver la alerta');
    }
  };
  
  const handleRunAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      const response = await monitorService.analyzeDataset(datasetId);
      
      if (response.data.success) {
        setLastAnalysisTime(new Date().toLocaleTimeString());
        // Recargar alertas después del análisis
        fetchAlerts();
      }
    } catch (err: any) {
      console.error('Error running analysis:', err);
      setError(err.response?.data?.error || 'Error al ejecutar el análisis');
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  // Función para obtener color según severidad
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-500 bg-red-900/30 border-red-500/30';
      case 'high':
        return 'text-orange-400 bg-orange-900/30 border-orange-400/30';
      case 'medium':
        return 'text-yellow-400 bg-yellow-900/30 border-yellow-400/30';
      default:
        return 'text-blue-400 bg-blue-900/30 border-blue-400/30';
    }
  };
  
  // Función para obtener icono según tipo de alerta
  const getAlertIcon = (logType: string) => {
    switch (logType) {
      case 'anomaly':
        return <AlertTriangle size={18} />;
      case 'opportunity':
        return <TrendingUp size={18} />;
      case 'action':
        return <Activity size={18} />;
      default:
        return <Eye size={18} />;
    }
  };

  if (loading) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 animate-pulse">
        <div className="h-6 w-1/3 bg-cyber-detail/30 rounded mb-4"></div>
        <div className="space-y-2">
          <div className="h-12 bg-cyber-detail/20 rounded"></div>
          <div className="h-12 bg-cyber-detail/20 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <Eye size={20} className="text-cyber-cyan mr-2" />
          <h3 className="text-lg font-semibold text-cyber-text">Monitor de Datos</h3>
        </div>
        
        <div className="flex items-center space-x-2">
          {lastAnalysisTime && (
            <div className="text-xs text-cyber-text/70 flex items-center">
              <Clock size={14} className="mr-1" />
              Último análisis: {lastAnalysisTime}
            </div>
          )}
          
          <button
            onClick={handleRunAnalysis}
            disabled={isAnalyzing}
            className={`px-3 py-1.5 rounded text-sm flex items-center ${
              isAnalyzing 
                ? 'bg-cyber-detail/30 text-cyber-text/50 cursor-not-allowed' 
                : 'bg-cyber-cyan text-cyber-dark hover:bg-cyber-cyan/90'
            }`}
          >
            {isAnalyzing ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-cyber-dark border-t-transparent rounded-full mr-2"></div>
                Analizando...
              </>
            ) : (
              <>
                <Activity size={16} className="mr-1" />
                Analizar Ahora
              </>
            )}
          </button>
        </div>
      </div>
      
      {error && (
        <div className="bg-red-900/30 border border-red-500/30 text-red-400 px-4 py-3 rounded mb-4">
          <div className="flex items-center">
            <AlertTriangle size={18} className="mr-2" />
            <span>{error}</span>
          </div>
        </div>
      )}
      
      {alerts.length === 0 ? (
        <div className="text-center py-8 text-cyber-text/70">
          <div className="flex justify-center mb-2">
            <CheckCircle size={32} className="text-green-400" />
          </div>
          <p>No hay alertas activas en este momento.</p>
          <p className="text-sm mt-1">El sistema monitoreará automáticamente y notificará cuando detecte anomalías.</p>
        </div>
      ) : (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-cyber-text/90 border-b border-cyber-detail/30 pb-1">
            Alertas Activas ({alerts.length})
          </h4>
          
          {alerts.map(alert => (
            <div 
              key={alert.id} 
              className={`p-3 rounded-lg border ${getSeverityColor(alert.severity)}`}
            >
              <div className="flex items-start">
                <div className="mt-1 mr-3">
                  {getAlertIcon(alert.log_type)}
                </div>
                
                <div className="flex-grow">
                  <div className="flex justify-between items-start">
                    <h5 className="font-medium">{alert.description}</h5>
                    <span className="text-xs capitalize px-2 py-0.5 rounded-full bg-cyber-dark/50">
                      {alert.severity}
                    </span>
                  </div>
                  
                  <div className="text-sm mt-1 text-cyber-text/80">
                    {alert.rule_name && <span className="mr-3">Regla: {alert.rule_name}</span>}
                    <span>{new Date(alert.created_at).toLocaleString()}</span>
                  </div>
                  
                  {alert.metrics && Object.keys(alert.metrics).length > 0 && (
                    <div className="mt-2 text-xs bg-cyber-dark/50 p-2 rounded">
                      <div className="font-medium mb-1">Métricas:</div>
                      <ul className="space-y-1">
                        {Object.entries(alert.metrics).map(([key, value]) => (
                          <li key={key}>
                            <span className="text-cyber-text/70">{key}:</span>{' '}
                            <span className="text-cyber-cyan">{String(value)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <div className="mt-3">
                    <button
                      onClick={() => handleResolveAlert(alert.id)}
                      className="flex items-center px-2 py-1 bg-green-900/30 text-green-400 rounded hover:bg-green-900/50 transition-colors text-xs"
                    >
                      <CheckCircle size={14} className="mr-1" />
                      Marcar como resuelta
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DataMonitorPanel;