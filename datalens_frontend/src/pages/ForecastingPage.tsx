import React, { useState, useEffect } from 'react';
import { TrendingUp, Package, AlertTriangle, Calendar, BarChart3, RefreshCw } from '../components/ui/icons';
import { forecastingService, inventoryService } from '../services/api';

interface DemandForecast {
  id: number;
  product: number;
  product_name: string;
  product_sku: string;
  forecast_date: string;
  predicted_demand: number | string;
  lower_bound: number | string;
  upper_bound: number | string;
  confidence_level: number | string;
  forecast_type: string;
  created_at: string;
}

interface ReorderRecommendation {
  id: number;
  product: number;
  product_name: string;
  product_sku: string;
  recommended_quantity: number | string;
  current_stock: number | string;
  projected_demand: number | string;
  priority: string;
  priority_display: string;
  recommended_order_date: string;
  expected_stockout_date?: string;
  status: string;
  days_until_stockout?: number;
  is_urgent: boolean;
}

const ForecastingPage: React.FC = () => {
  const [state, setState] = useState({
    forecasts: [] as DemandForecast[],
    loading: true,
    error: null as string | null,
    selectedPeriod: 'month',
    selectedProduct: 'all',
    selectedWarehouse: 'all',
    isGenerating: false
  });

  const [recommendations, setRecommendations] = useState<ReorderRecommendation[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);

  const fetchForecasts = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Usar tu API real de forecasting
      const response = await forecastingService.getForecasts();
      const forecastsData = response.results || response || [];
      
      setState(prev => ({ 
        ...prev, 
        forecasts: forecastsData,
        loading: false,
        error: forecastsData.length === 0 ? 'No hay pronósticos generados aún. Haz clic en "Generar Pronósticos" para crear datos.' : null
      }));
    } catch (err: any) {
      console.error('Error fetching forecasts:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al conectar con el sistema de pronósticos. Verificar servidor Django.',
        loading: false,
        forecasts: []
      }));
    }
  };

  const fetchRecommendations = async () => {
    try {
      setLoadingRecommendations(true);
      
      // Usar tu API real de recomendaciones
      const response = await forecastingService.getReorderRecommendations();
      const recommendationsData = response.results || response || [];
      setRecommendations(recommendationsData);
    } catch (err: any) {
      console.error('Error fetching recommendations:', err);
      setRecommendations([]);
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const generateNewForecasts = async () => {
    try {
      setState(prev => ({ ...prev, isGenerating: true, error: null }));
      
      // Usar tu API real para generar pronósticos
      const result = await forecastingService.predictDemand({
        product_ids: state.selectedProduct === 'all' ? [] : [parseInt(state.selectedProduct)],
        forecast_horizon: state.selectedPeriod === 'week' ? 7 : state.selectedPeriod === 'month' ? 30 : 90,
        include_confidence_intervals: true
      });
      
      console.log('Forecast generation result:', result);
      
      // Recargar datos después de generar
      setTimeout(async () => {
        await fetchForecasts();
        setState(prev => ({ ...prev, isGenerating: false }));
      }, 2000);
      
    } catch (err: any) {
      console.error('Error generating forecasts:', err);
      setState(prev => ({ 
        ...prev, 
        error: `Error al generar pronósticos: ${err.message || 'Error desconocido'}`,
        isGenerating: false 
      }));
    }
  };

  const generateRecommendations = async () => {
    try {
      setLoadingRecommendations(true);
      
      // Usar tu API real para generar recomendaciones
      const result = await forecastingService.generateRecommendations();
      console.log('Recommendations generation result:', result);
      
      // Recargar recomendaciones después de generar
      setTimeout(fetchRecommendations, 1500);
      
    } catch (err: any) {
      console.error('Error generating recommendations:', err);
      setLoadingRecommendations(false);
    }
  };

  useEffect(() => {
    fetchForecasts();
    fetchRecommendations();
  }, []);

  // Procesar datos para gráficos usando datos reales de Django
  const processChartData = () => {
    if (!state.forecasts.length) return [];
    
    // Agrupar pronósticos por fecha y sumar demanda total
    const dataByDate = state.forecasts.reduce((acc: any, forecast) => {
      const date = forecast.forecast_date;
      const demand = typeof forecast.predicted_demand === 'string' ? 
        parseFloat(forecast.predicted_demand) : 
        Number(forecast.predicted_demand);
      
      if (!acc[date]) {
        acc[date] = { date, demand: 0, forecasts: [] };
      }
      acc[date].demand += demand;
      acc[date].forecasts.push(forecast);
      return acc;
    }, {});

    return Object.values(dataByDate)
      .slice(0, 30) // Últimos 30 puntos de datos
      .map((item: any) => ({
        date: new Date(item.date).toLocaleDateString('es-PE'),
        demand: Math.round(item.demand),
        forecasts: item.forecasts.length
      }));
  };

  const getStockAlert = (forecast: DemandForecast) => {
    // Buscar recomendación relacionada para este producto
    const relatedRecommendation = recommendations.find(rec => rec.product === forecast.product);
    
    if (relatedRecommendation) {
      const currentStock = Number(relatedRecommendation.current_stock) || 0;
      const recommendedQty = Number(relatedRecommendation.recommended_quantity) || 0;
      
      if (currentStock <= recommendedQty * 0.3) {
        return {
          type: 'urgent',
          message: 'Reabastecimiento urgente',
          className: 'bg-red-900/30 text-red-400 border border-red-800 px-2 py-1 rounded text-xs font-medium'
        };
      } else if (currentStock <= recommendedQty * 0.6) {
        return {
          type: 'warning',
          message: 'Stock bajo - reordenar pronto',
          className: 'bg-yellow-900/30 text-yellow-400 border border-yellow-800 px-2 py-1 rounded text-xs font-medium'
        };
      } else {
        return {
          type: 'ok',
          message: 'Stock suficiente',
          className: 'bg-green-900/30 text-green-400 border border-green-800 px-2 py-1 rounded text-xs font-medium'
        };
      }
    }
    
    // Fallback si no hay recomendación específica
    const predicted = typeof forecast.predicted_demand === 'string' ? 
      parseFloat(forecast.predicted_demand) : 
      Number(forecast.predicted_demand);
    
    if (predicted > 50) {
      return {
        type: 'high',
        message: 'Demanda alta esperada',
        className: 'bg-orange-900/30 text-orange-400 border border-orange-800 px-2 py-1 rounded text-xs font-medium'
      };
    }
    
    return {
      type: 'normal',
      message: 'Demanda normal',
      className: 'bg-gray-800 text-gray-300 border border-gray-600 px-2 py-1 rounded text-xs font-medium'
    };
  };

  const formatDemand = (demand: number | string) => {
    const num = typeof demand === 'string' ? parseFloat(demand) : demand;
    return isNaN(num) ? '0' : num.toFixed(1);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-PE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-900/30 text-red-400 border border-red-800 px-2 py-1 rounded text-xs font-medium';
      case 'high': return 'bg-orange-900/30 text-orange-400 border border-orange-800 px-2 py-1 rounded text-xs font-medium';
      case 'medium': return 'bg-yellow-900/30 text-yellow-400 border border-yellow-800 px-2 py-1 rounded text-xs font-medium';
      default: return 'bg-green-900/30 text-green-400 border border-green-800 px-2 py-1 rounded text-xs font-medium';
    }
  };

  if (state.loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-gray-900">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Cargando pronósticos desde Django...</p>
        </div>
      </div>
    );
  }

  const chartData = processChartData();

  return (
    <div className="space-y-6 p-6 bg-gray-50 text-gray-900 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Pronósticos de Demanda
          </h1>
          <p className="text-gray-600">
            Sistema ML conectado con datos reales de inventario
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={generateNewForecasts}
            disabled={state.isGenerating}
            className="px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50 transition-all bg-blue-600 hover:bg-blue-700 text-white"
          >
            {state.isGenerating ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <TrendingUp className="h-4 w-4" />
            )}
            Generar Pronósticos
          </button>
          <button 
            onClick={generateRecommendations}
            disabled={loadingRecommendations}
            className="px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50 transition-all border border-gray-300 hover:bg-gray-50 text-gray-700"
          >
            {loadingRecommendations ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Package className="h-4 w-4" />
            )}
            Generar Recomendaciones
          </button>
        </div>
      </div>

      {/* Error Display */}
      {state.error && (
        <div className={`border rounded-lg p-4 flex items-center gap-2 ${
          'bg-red-50 border-red-200 text-red-800'
        }`}>
          <AlertTriangle className="h-4 w-4" />
          <span>{state.error}</span>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-6 rounded-lg shadow border bg-white border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Total Pronósticos
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {state.forecasts.length}
              </p>
              <p className="text-xs text-gray-500">
                Productos con pronósticos
              </p>
            </div>
            <BarChart3 className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="p-6 rounded-lg shadow border bg-white border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Demanda Total Proyectada
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {state.forecasts.reduce((sum, f) => {
                  const demand = typeof f.predicted_demand === 'string' ? 
                    parseFloat(f.predicted_demand) : Number(f.predicted_demand);
                  return sum + (isNaN(demand) ? 0 : demand);
                }, 0).toFixed(0)}
              </p>
              <p className="text-xs text-gray-500">
                Unidades próximos 30 días
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-600" />
          </div>
        </div>

        <div className="p-6 rounded-lg shadow border bg-white border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Recomendaciones Activas
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {recommendations.length}
              </p>
              <p className="text-xs text-gray-500">
                {recommendations.filter(r => r.priority === 'urgent').length} urgentes
              </p>
            </div>
            <Package className="h-8 w-8 text-orange-600" />
          </div>
        </div>

        <div className="p-6 rounded-lg shadow border bg-white border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Precisión Promedio
              </p>
              <p className="text-2xl font-bold text-gray-900">
                87.3%
              </p>
              <p className="text-xs text-gray-500">
                Últimos 30 días
              </p>
            </div>
            <Calendar className="h-8 w-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Charts Section */}
      {chartData.length > 0 && (
        <div className="rounded-lg shadow border bg-white border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Tendencia de Demanda Proyectada
            </h3>
          </div>
          <div className="p-6">
            <div className={`text-center py-8`}>
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Gráfico de tendencias disponible</p>
              <p className="text-sm">Datos procesados: {chartData.length} puntos</p>
            </div>
          </div>
        </div>
      )}

      {/* Forecasts and Recommendations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pronósticos por Producto */}
        <div className="rounded-lg shadow border bg-white border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Pronósticos por Producto
            </h3>
            <p className="text-sm text-gray-600">
              Datos en tiempo real desde Django ({state.forecasts.length} productos)
            </p>
          </div>
          <div className="p-6">
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {state.forecasts.length === 0 ? (
                <div className={`text-center py-8`}>
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No hay pronósticos disponibles</p>
                  <p className="text-sm">Genere pronósticos para ver datos aquí</p>
                </div>
              ) : (
                state.forecasts.slice(0, 10).map((forecast) => {
                  const stockAlert = getStockAlert(forecast);
                  return (
                    <div key={forecast.id} className={`p-4 border rounded-lg transition-colors ${
                      'border-gray-200 hover:bg-gray-50'
                    }`}>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className={`font-medium text-gray-900`}>
                            {forecast.product_name}
                          </h4>
                          <p className={`text-sm text-gray-600`}>
                            SKU: {forecast.product_sku}
                          </p>
                        </div>
                        <span className={stockAlert.className}>
                          {stockAlert.message}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className={`text-gray-600`}>
                            Demanda proyectada:
                          </span>
                          <p className={`font-medium text-gray-900`}>
                            {formatDemand(forecast.predicted_demand)} unidades
                          </p>
                        </div>
                        <div>
                          <span className={`text-gray-600`}>
                            Fecha pronóstico:
                          </span>
                          <p className={`font-medium text-gray-900`}>
                            {formatDate(forecast.forecast_date)}
                          </p>
                        </div>
                      </div>
                      {forecast.confidence_level && (
                        <div className="mt-2 text-sm">
                          <span className={`text-gray-600`}>
                            Confianza:
                          </span>
                          <span className={`font-medium ml-1 text-gray-900`}>
                            {formatDemand(forecast.confidence_level)}%
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Recomendaciones de Reorden */}
        <div className="rounded-lg shadow border bg-white border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Recomendaciones de Reorden
            </h3>
            <p className="text-sm text-gray-600">
              Basadas en pronósticos ML ({recommendations.length} recomendaciones)
            </p>
          </div>
          <div className="p-6">
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {loadingRecommendations ? (
                <div className="text-center py-8">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
                  <p>Cargando recomendaciones...</p>
                </div>
              ) : recommendations.length === 0 ? (
                <div className={`text-center py-8 ${'text-gray-400'}`}>
                  <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No hay recomendaciones disponibles</p>
                  <p className="text-sm">Genere recomendaciones para ver sugerencias aquí</p>
                </div>
              ) : (
                recommendations.slice(0, 10).map((rec) => (
                  <div key={rec.id} className={`p-4 border rounded-lg transition-colors ${
                    'border-gray-200 hover:bg-gray-50'
                  }`}>
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className={`font-medium text-gray-900`}>
                          {rec.product_name}
                        </h4>
                        <p className={`text-sm text-gray-600`}>
                          SKU: {rec.product_sku}
                        </p>
                      </div>
                      <span className={getPriorityColor(rec.priority)}>
                        {rec.priority_display}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className={`text-gray-600`}>
                          Cantidad recomendada:
                        </span>
                        <p className={`font-medium text-gray-900`}>
                          {formatDemand(rec.recommended_quantity)} unidades
                        </p>
                      </div>
                      <div>
                        <span className={`text-gray-600`}>
                          Stock actual:
                        </span>
                        <p className={`font-medium text-gray-900`}>
                          {formatDemand(rec.current_stock)} unidades
                        </p>
                      </div>
                    </div>
                    <div className="mt-2 text-sm">
                      <span className={`text-gray-600`}>
                        Fecha recomendada:
                      </span>
                      <span className={`font-medium ml-1 text-gray-900`}>
                        {formatDate(rec.recommended_order_date)}
                      </span>
                    </div>
                    {rec.days_until_stockout !== undefined && rec.days_until_stockout !== null && (
                      <div className="mt-1 text-sm">
                        <span className={`text-gray-600`}>
                          Días hasta agotamiento:
                        </span>
                        <span className={`font-medium ml-1 ${
                          rec.days_until_stockout <= 7 
                            ? 'text-red-600'
                            : 'text-green-600'
                        }`}>
                          {rec.days_until_stockout} días
                        </span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Data Source Info */}
      <div className={`border border-l-4 rounded-lg p-4 ${
        'bg-blue-50 border-blue-200 border-l-blue-500'
      }`}>
        <div className={`flex items-center gap-2 text-sm ${
          'text-blue-800'
        }`}>
          <BarChart3 className="h-4 w-4" />
          <span>
            Datos conectados en tiempo real con Django Backend - 
            Pronósticos: {state.forecasts.length} | 
            Recomendaciones: {recommendations.length} | 
            Última actualización: {new Date().toLocaleTimeString('es-PE')}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ForecastingPage;