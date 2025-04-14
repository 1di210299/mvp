// src/components/ProactiveInsights.tsx
import React, { useState, useEffect } from 'react';
import { monitorService } from '../api/monitor-service';
import { Lightbulb, TrendingUp, AlertCircle, Zap, Calendar, ChevronRight, BarChart, PieChart } from 'lucide-react';

interface ProactiveInsightsProps {
  datasetId: number;
}

const ProactiveInsights: React.FC<ProactiveInsightsProps> = ({ datasetId }) => {
  const [insights, setInsights] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInsights();
  }, [datasetId]);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      const response = await monitorService.analyzeDataset(datasetId);
      
      if (response.data.success) {
        setInsights(response.data.analysis_results);
        setError(null);
      }
    } catch (err: any) {
      console.error('Error fetching insights:', err);
      setError(err.response?.data?.error || 'Error al obtener insights');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 animate-pulse">
        <div className="h-6 w-1/2 bg-cyber-detail/30 rounded mb-4"></div>
        <div className="space-y-3">
          <div className="h-32 bg-cyber-detail/20 rounded"></div>
          <div className="h-32 bg-cyber-detail/20 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
        <div className="flex items-center text-red-400 mb-2">
          <AlertCircle size={18} className="mr-2" />
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

  // No hay datos para mostrar
  if (!insights.trends && !insights.opportunities && !insights.forecasts) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
        <div className="flex items-center mb-4">
          <Lightbulb size={20} className="text-cyber-cyan mr-2" />
          <h3 className="text-lg font-semibold text-cyber-text">Insights Proactivos</h3>
        </div>
        <div className="text-center py-6">
          <p className="text-cyber-text/70">No hay suficientes datos para generar insights proactivos.</p>
          <button 
            onClick={fetchInsights}
            className="mt-3 px-4 py-2 bg-cyber-cyan text-cyber-dark rounded"
          >
            Analizar Datos
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
      <div className="flex items-center mb-6">
        <Lightbulb size={20} className="text-cyber-cyan mr-2" />
        <h3 className="text-lg font-semibold text-cyber-text">Insights Proactivos</h3>
      </div>
      
      <div className="space-y-6">
        {/* Tendencias */}
        {insights.trends && insights.trends.sales_trend && (
          <div>
            <h4 className="text-sm font-medium text-cyber-text/90 border-b border-cyber-detail/30 pb-1 mb-3 flex items-center">
              <TrendingUp size={16} className="mr-2 text-cyber-cyan" />
              Tendencia de Ventas
            </h4>
            
            <div className="bg-cyber-detail/20 rounded-lg p-3">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <div className="text-xs text-cyber-text/70">Tendencia Reciente</div>
                  <div className={`text-xl font-bold ${
                    insights.trends.sales_trend.recent_change_pct > 0
                      ? 'text-green-400'
                      : insights.trends.sales_trend.recent_change_pct < 0
                        ? 'text-red-400'
                        : 'text-cyber-text'
                  }`}>
                    {insights.trends.sales_trend.recent_change_pct > 0 ? '+' : ''}
                    {insights.trends.sales_trend.recent_change_pct.toFixed(1)}%
                  </div>
                  <div className="text-sm capitalize mt-1">
                    {insights.trends.sales_trend.label.replace(/_/g, ' ')}
                  </div>
                </div>
                
                <div>
                  <div className="text-xs text-cyber-text/70">Promedio Semanal</div>
                  <div className="text-xl font-bold text-cyber-text">
                    S/ {insights.trends.sales_trend.avg_last_week.toFixed(2)}
                  </div>
                </div>
                
                <div>
                  <div className="text-xs text-cyber-text/70">Promedio Mensual</div>
                  <div className="text-xl font-bold text-cyber-text">
                    S/ {insights.trends.sales_trend.avg_last_month.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Oportunidades */}
        {insights.opportunities && Object.keys(insights.opportunities).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-cyber-text/90 border-b border-cyber-detail/30 pb-1 mb-3 flex items-center">
              <Zap size={16} className="mr-2 text-cyber-cyan" />
              Oportunidades Identificadas
            </h4>
            
            <div className="space-y-3">
              {insights.opportunities.best_day && (
                <div className="bg-cyber-detail/20 rounded-lg p-3">
                  <div className="flex items-start">
                    <div className="bg-cyber-cyan/20 rounded-full p-2 mr-3">
                      <Calendar size={20} className="text-cyber-cyan" />
                    </div>
                    <div>
                      <h5 className="font-medium text-cyber-text">Optimización por Día de Semana</h5>
                      <p className="text-sm text-cyber-text/70 mt-1">
                        {insights.opportunities.best_day.insight}
                      </p>
                      <div className="mt-2 text-xs text-cyber-cyan">
                        Ventas promedio: S/ {insights.opportunities.best_day.avg_sales.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {insights.opportunities.category_insights && (
                <div className="bg-cyber-detail/20 rounded-lg p-3">
                  <div className="flex items-start">
                    <div className="bg-cyber-cyan/20 rounded-full p-2 mr-3">
                      <BarChart size={20} className="text-cyber-cyan" />
                    </div>
                    <div>
                      <h5 className="font-medium text-cyber-text">Rendimiento por Categoría</h5>
                      <p className="text-sm text-cyber-text/70 mt-1">
                        {insights.opportunities.category_insights.insight}
                      </p>
                      <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-cyber-text/70">Mejor categoría: </span>
                          <span className="text-green-400">
                            {insights.opportunities.category_insights.best_category}
                          </span>
                        </div>
                        <div>
                          <span className="text-cyber-text/70">Ventas: </span>
                          <span className="text-cyber-cyan">
                            S/ {insights.opportunities.category_insights.best_category_sales.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {insights.opportunities.region_insights && (
                <div className="bg-cyber-detail/20 rounded-lg p-3">
                  <div className="flex items-start">
                    <div className="bg-cyber-cyan/20 rounded-full p-2 mr-3">
                      <PieChart size={20} className="text-cyber-cyan" />
                    </div>
                    <div>
                      <h5 className="font-medium text-cyber-text">Distribución Regional</h5>
                      <p className="text-sm text-cyber-text/70 mt-1">
                        {insights.opportunities.region_insights.insight}
                      </p>
                      <div className="mt-2 text-xs">
                        <span className="text-cyber-text/70">Oportunidad de expansión en </span>
                        <span className="text-green-400">
                          {insights.opportunities.region_insights.best_region}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Pronósticos */}
        {insights.forecasts && insights.forecasts.sales_next_7_days && (
          <div>
            <h4 className="text-sm font-medium text-cyber-text/90 border-b border-cyber-detail/30 pb-1 mb-3 flex items-center">
              <Calendar size={16} className="mr-2 text-cyber-cyan" />
              Pronóstico de Ventas
            </h4>
            
            <div className="bg-cyber-detail/20 rounded-lg p-3">
              <div className="flex items-center mb-2">
                <h5 className="font-medium text-cyber-text">Próximos 7 días</h5>
                <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                  insights.forecasts.forecast_sentiment.includes('positivo')
                    ? 'bg-green-900/30 text-green-400'
                    : insights.forecasts.forecast_sentiment.includes('negativo')
                      ? 'bg-red-900/30 text-red-400'
                      : 'bg-blue-900/30 text-blue-400'
                }`}>
                  {insights.forecasts.forecast_sentiment.replace(/_/g, ' ')}
                </span>
              </div>
              
              <div className="text-sm">
                <span className="text-cyber-text/70">Cambio esperado: </span>
                <span className={
                  insights.forecasts.expected_change_pct > 0
                    ? 'text-green-400'
                    : insights.forecasts.expected_change_pct < 0
                      ? 'text-red-400'
                      : 'text-cyber-text'
                }>
                  {insights.forecasts.expected_change_pct > 0 ? '+' : ''}
                  {insights.forecasts.expected_change_pct.toFixed(1)}%
                </span>
              </div>
              
              <div className="mt-3">
                <div className="text-xs text-cyber-text/70 mb-1">Proyección diaria:</div>
                <div className="overflow-x-auto pb-1">
                  <div className="flex space-x-3">
                    {insights.forecasts.sales_next_7_days.map((day: any, index: number) => (
                      <div key={index} className="flex-shrink-0 w-20 bg-cyber-dark/50 rounded p-2 text-center">
                        <div className="text-xs text-cyber-text/70">
                          {new Date(day.date).toLocaleDateString('es-ES', { weekday: 'short' })}
                        </div>
                        <div className="text-sm font-medium text-cyber-cyan mt-1">
                          S/ {Math.round(day.predicted_sales)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-4 pt-3 border-t border-cyber-detail/30 flex justify-end">
        <button
          onClick={fetchInsights}
          className="flex items-center text-cyber-cyan hover:text-cyber-cyan/80 transition-colors text-sm"
        >
          Actualizar insights
          <ChevronRight size={16} className="ml-1" />
        </button>
      </div>
    </div>
  );
};

export default ProactiveInsights;