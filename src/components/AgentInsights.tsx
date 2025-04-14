// src/components/AgentInsights.tsx
import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import {
  Brain,
  BarChart2,
  TrendingUp,
  AlertTriangle,
  Zap,
  Layers,
  RefreshCw,
  CheckCircle
} from 'lucide-react';
import { decisionService, InsightResponse } from '../api/decision-service';

interface AgentInsightsProps {
  userId?: number;
  refreshInterval?: number; // in milliseconds
}

const AgentInsights: React.FC<AgentInsightsProps> = ({
  userId,
  refreshInterval = 0 // 0 means no auto-refresh
}) => {
  const [insights, setInsights] = useState<InsightResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<string>('month');
  const [adaptingParams, setAdaptingParams] = useState(false);

  useEffect(() => {
    fetchInsights();
    
    if (refreshInterval > 0) {
      const intervalId = setInterval(fetchInsights, refreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [period]);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await decisionService.getLearningInsights(period);
      setInsights(response.data);
    } catch (err: any) {
      console.error('Error fetching insights:', err);
      setError(err.response?.data?.error || 'Error al obtener insights del agente');
    } finally {
      setLoading(false);
    }
  };

  const handleAdaptParameters = async () => {
    try {
      setAdaptingParams(true);
      await decisionService.adaptAgentParameters();
      // Reload insights to see the changes
      await fetchInsights();
    } catch (err: any) {
      console.error('Error adapting parameters:', err);
      setError(err.response?.data?.error || 'Error al adaptar parámetros del agente');
    } finally {
      setAdaptingParams(false);
    }
  };

  // Loading state
  if (loading && !insights) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 animate-pulse">
        <div className="h-6 w-1/3 bg-cyber-detail/30 rounded mb-4"></div>
        <div className="space-y-2">
          <div className="h-12 bg-cyber-detail/20 rounded"></div>
          <div className="h-32 bg-cyber-detail/20 rounded"></div>
          <div className="h-12 bg-cyber-detail/20 rounded"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
        <div className="flex items-center text-red-400 mb-2">
          <AlertTriangle size={18} className="mr-2" />
          <h3 className="font-medium">Error</h3>
        </div>
        <p className="text-cyber-text/70">{error}</p>
        <button
          onClick={fetchInsights}
          className="mt-3 px-4 py-2 bg-cyber-cyan text-cyber-dark rounded"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!insights) {
    return null;
  }

  const {
    performance,
    learning_level,
    recommendations
  } = insights;

  return (
    <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <Brain size={20} className="text-cyber-cyan mr-2" />
          <h3 className="text-lg font-semibold text-cyber-text">Insights del Agente IA</h3>
        </div>
        <div className="flex space-x-2">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-2 py-1 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded"
          >
            <option value="week">Última semana</option>
            <option value="month">Último mes</option>
            <option value="quarter">Último trimestre</option>
            <option value="all">Todo el historial</option>
          </select>
          
          <button
            onClick={fetchInsights}
            className="p-1.5 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded hover:bg-cyber-detail/50 transition-colors"
            title="Refrescar datos"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Learning Level */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-cyber-text flex items-center">
            <Layers size={16} className="mr-1.5 text-cyber-cyan" />
            Nivel de Aprendizaje
          </h4>
          <span className="text-xs text-cyber-text/70 capitalize">
            {learning_level.level}
          </span>
        </div>
        <div className="w-full bg-cyber-detail/30 h-2 rounded-full overflow-hidden">
          <div
            className="bg-cyber-cyan h-2 rounded-full"
            style={{ width: `${learning_level.progress}%` }}
          ></div>
        </div>
        <p className="text-xs text-cyber-text/70 mt-1">{learning_level.description}</p>
      </div>

      {/* Performance Summary */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-cyber-text mb-3 flex items-center">
          <BarChart2 size={16} className="mr-1.5 text-cyber-cyan" />
          Rendimiento del Agente
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-cyber-detail/20 p-3 rounded-lg border border-cyber-detail/30">
            <div className="text-xs text-cyber-text/70 mb-1">Acciones Totales</div>
            <div className="text-xl font-bold text-cyber-text">{performance.summary.total_actions}</div>
          </div>
          
          <div className="bg-cyber-detail/20 p-3 rounded-lg border border-cyber-detail/30">
            <div className="text-xs text-cyber-text/70 mb-1">Tasa de Éxito</div>
            <div className="text-xl font-bold text-cyber-text">{performance.summary.success_rate.toFixed(1)}%</div>
          </div>
          
          <div className="bg-cyber-detail/20 p-3 rounded-lg border border-cyber-detail/30">
            <div className="text-xs text-cyber-text/70 mb-1">Puntaje Promedio</div>
            <div className="text-xl font-bold text-cyber-text">{performance.summary.avg_success_score.toFixed(2)}</div>
          </div>
        </div>
        
        {/* Time Series Chart */}
        {performance.time_series && performance.time_series.length > 1 && (
          <div className="bg-cyber-detail/20 p-3 rounded-lg border border-cyber-detail/30 mb-4">
            <div className="text-xs font-medium text-cyber-text mb-2">Rendimiento a lo largo del tiempo</div>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performance.time_series}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                  <XAxis 
                    dataKey="period" 
                    stroke="#E6E6E6" 
                    tick={{ fontSize: 10 }}
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' });
                    }}
                  />
                  <YAxis stroke="#E6E6E6" />
                  <Tooltip
                    formatter={(value: any) => [`${value}%`, 'Tasa de éxito']}
                    labelFormatter={(label) => {
                      const date = new Date(label);
                      return date.toLocaleDateString('es-ES', { year: 'numeric', month: 'long', day: 'numeric' });
                    }}
                    contentStyle={{ backgroundColor: '#001f2e', border: 'none', color: '#E6E6E6' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="success_rate" 
                    name="Tasa de éxito" 
                    stroke="#00E6E6" 
                    strokeWidth={2}
                    dot={{ stroke: '#00E6E6', strokeWidth: 1, r: 3, fill: '#001f2e' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
        
        {/* Action Type Performance */}
        {Object.keys(performance.action_type_performance).length > 0 && (
          <div className="bg-cyber-detail/20 p-3 rounded-lg border border-cyber-detail/30">
            <div className="text-xs font-medium text-cyber-text mb-2">Rendimiento por tipo de acción</div>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={Object.entries(performance.action_type_performance).map(([key, value]: [string, any]) => ({
                    action_type: key,
                    success_rate: value.success_rate,
                    count: value.count
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                  <XAxis dataKey="action_type" stroke="#E6E6E6" />
                  <YAxis stroke="#E6E6E6" />
                  <Tooltip
                    formatter={(value: any, name: string) => {
                      return name === 'success_rate'
                        ? [`${value.toFixed(1)}%`, 'Tasa de éxito']
                        : [`${value}`, 'Cantidad de acciones'];
                    }}
                    contentStyle={{ backgroundColor: '#001f2e', border: 'none', color: '#E6E6E6' }}
                  />
                  <Legend />
                  <Bar dataKey="success_rate" name="Tasa de éxito" fill="#00E6E6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="count" name="Cantidad" fill="#9C66FF" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Insights & Recommendations */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-cyber-text mb-3 flex items-center">
          <Zap size={16} className="mr-1.5 text-cyber-cyan" />
          Recomendaciones para Mejorar
        </h4>
        
        {recommendations.length > 0 ? (
          <div className="space-y-3">
            {recommendations.map((rec, idx) => (
              <div 
                key={idx} 
                className={`p-3 rounded-lg border ${
                  rec.priority === 'alta' 
                    ? 'border-red-500/30 bg-red-900/10' 
                    : rec.priority === 'media'
                    ? 'border-yellow-500/30 bg-yellow-900/10'
                    : 'border-blue-500/30 bg-blue-900/10'
                }`}
              >
                <div className="flex items-start">
                  <div className={`rounded-full p-1.5 mr-2 ${
                    rec.priority === 'alta' 
                      ? 'bg-red-900/30 text-red-400' 
                      : rec.priority === 'media'
                      ? 'bg-yellow-900/30 text-yellow-400'
                      : 'bg-blue-900/30 text-blue-400'
                  }`}>
                    {rec.action === 'optimizar' && <TrendingUp size={16} />}
                    {rec.action === 'revisar' && <Layers size={16} />}
                    {rec.action === 'aumentar' && <BarChart2 size={16} />}
                    {rec.action === 'automatizar' && <Brain size={16} />}
                  </div>
                  <div>
                    <div className="flex items-center">
                      <h5 className="text-sm font-medium">
                        {rec.area === 'reglas_de_negocio' && 'Reglas de Negocio'}
                        {rec.area === 'tipo_accion' && `Acciones de ${rec.action_type}`}
                        {rec.area === 'datos_aprendizaje' && 'Datos de Aprendizaje'}
                        {rec.area === 'automatizacion' && 'Automatización'}
                      </h5>
                      <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${
                        rec.priority === 'alta' 
                          ? 'bg-red-900/30 text-red-400' 
                          : rec.priority === 'media'
                          ? 'bg-yellow-900/30 text-yellow-400'
                          : 'bg-blue-900/30 text-blue-400'
                      }`}>
                        Prioridad {rec.priority}
                      </span>
                    </div>
                    <p className="text-sm text-cyber-text/80 mt-0.5">{rec.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-cyber-detail/20 p-3 rounded-lg border border-cyber-detail/30 text-center">
            <CheckCircle size={24} className="text-green-400 mb-2 mx-auto" />
            <p className="text-cyber-text/70">No hay recomendaciones pendientes. El agente está funcionando correctamente.</p>
          </div>
        )}
      </div>

      {/* Auto-adaptation */}
      <div className="bg-cyber-detail/20 p-4 rounded-lg border border-cyber-detail/30">
        <div className="flex justify-between items-start">
          <div>
            <h4 className="text-sm font-medium text-cyber-text mb-1">Adaptación automática</h4>
            <p className="text-xs text-cyber-text/70">
              El agente IA puede adaptar automáticamente sus parámetros en base al aprendizaje acumulado.
            </p>
          </div>
          <button
            onClick={handleAdaptParameters}
            disabled={adaptingParams}
            className={`px-3 py-1.5 rounded text-sm ${
              adaptingParams
                ? "bg-cyber-detail/30 text-cyber-text/50 cursor-not-allowed"
                : "bg-cyber-cyan text-cyber-dark hover:bg-cyber-cyan/90"
            }`}
          >
            {adaptingParams ? (
              <>
                <span className="animate-pulse">Adaptando...</span>
              </>
            ) : (
              <>
                <Brain size={14} className="inline mr-1" />
                Adaptar ahora
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentInsights;