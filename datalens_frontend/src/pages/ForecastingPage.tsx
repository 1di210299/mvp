import React, { useState, useEffect } from 'react';
import { TrendingUp, Package, AlertTriangle, Calendar, BarChart3, RefreshCw, LineChart } from '../components/ui/icons';
import { forecastingService } from '../services/api';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useTheme } from '../contexts/ThemeContext';

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
  const { actualTheme } = useTheme();
  const isDarkMode = actualTheme === 'dark';
  
  const [state, setState] = useState({
    forecasts: [] as DemandForecast[],
    loading: true,
    error: null as string | null,
    selectedPeriod: 'month',
    selectedProduct: 'all',
    selectedWarehouse: 'all',
    isGenerating: false,
    forecastData: null as any,
    chartsLoading: false,
    chartsError: null as string | null
  });

  const [recommendations, setRecommendations] = useState<ReorderRecommendation[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);

  // Función para cargar datos de gráficos automáticamente
  const loadForecastCharts = async () => {
    try {
      setState(prev => ({ ...prev, chartsLoading: true, chartsError: null }));
      
      console.log('🔍 Cargando datos para gráficos...');
      const forecastDataRes = await forecastingService.getForecastData({
        days_ahead: 7
      });
      
      console.log('✅ Datos de gráficos obtenidos:', forecastDataRes);
      
      setState(prev => ({
        ...prev,
        forecastData: forecastDataRes,
        chartsLoading: false
      }));
      
    } catch (error: any) {
      console.error('❌ Error loading forecast charts:', error);
      setState(prev => ({
        ...prev,
        chartsError: `Error cargando gráficos: ${error.message || 'Error desconocido'}`,
        chartsLoading: false
      }));
    }
  };

  const fetchForecasts = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const response = await forecastingService.getForecasts();
      const forecastsData = response.results || response || [];
      
      // ELIMINAR DUPLICADOS: Solo un pronóstico por producto-fecha
      const uniqueForecasts = forecastsData.reduce((acc: any[], current: any) => {
        const key = `${current.product_name || current.product}-${current.forecast_date}`;
        const existing = acc.find(item => 
          `${item.product_name || item.product}-${item.forecast_date}` === key
        );
        
        if (!existing) {
          acc.push(current);
        }
        return acc;
      }, []);
      
      console.log(`🔍 Pronósticos: ${forecastsData.length} originales → ${uniqueForecasts.length} únicos`);
      
      setState(prev => ({ 
        ...prev, 
        forecasts: uniqueForecasts,
        loading: false,
        error: uniqueForecasts.length === 0 ? 'No hay pronósticos generados aún. Haz clic en "Generar Pronósticos" para crear datos.' : null
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
      const response = await forecastingService.getReorderRecommendations();
      const recommendationsData = response.results || response || [];
      
      // ELIMINAR DUPLICADOS: Solo una recomendación por producto
      const uniqueRecommendations = recommendationsData.reduce((acc: any[], current: any) => {
        const key = `${current.product_name || current.product}-${current.product_sku || current.sku}`;
        const existing = acc.find(item => 
          `${item.product_name || item.product}-${item.product_sku || item.sku}` === key
        );
        
        if (!existing) {
          acc.push(current);
        }
        return acc;
      }, []);
      
      console.log(`🔍 Recomendaciones: ${recommendationsData.length} originales → ${uniqueRecommendations.length} únicas`);
      
      setRecommendations(uniqueRecommendations);
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
      
      const result = await forecastingService.predictDemand({
        product_ids: state.selectedProduct === 'all' ? [] : [parseInt(state.selectedProduct)],
        forecast_horizon: state.selectedPeriod === 'week' ? 7 : state.selectedPeriod === 'month' ? 30 : 90,
        include_confidence_intervals: true
      });
      
      console.log('Forecast generation result:', result);
      
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
      const result = await forecastingService.generateRecommendations();
      console.log('Recommendations generation result:', result);
      setTimeout(fetchRecommendations, 1500);
    } catch (err: any) {
      console.error('Error generating recommendations:', err);
      setLoadingRecommendations(false);
    }
  };

  useEffect(() => {
    fetchForecasts();
    fetchRecommendations();
    loadForecastCharts();
  }, []);

  // Componente para visualización de datos ML
  const MLVisualization: React.FC<{ data: any }> = ({ data }) => {
    console.log('🔍 MLVisualization recibió datos:', data);
    
    // USAR SIEMPRE los pronósticos reales del estado principal (NO del parámetro data)
    const predictions = state.forecasts || [];
    const stats = data?.stats || {};
    
    // Estado local para el filtro de producto
    const [selectedProductFilter, setSelectedProductFilter] = useState<string>('all');
    
    if (!predictions || predictions.length === 0) {
      console.warn('❌ No hay datos válidos para MLVisualization:', { predictions, forecastsCount: state.forecasts.length });
      return (
        <div className={`text-center py-12 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
          <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-semibold mb-2">No hay pronósticos de demanda disponibles</p>
          <p className={`text-sm mb-6 ${isDarkMode ? 'text-gray-500' : 'text-gray-600'}`}>
            {recommendations.length > 0 
              ? `Tienes ${recommendations.length} recomendaciones basadas en datos históricos, pero necesitas generar pronósticos ML para ver visualizaciones avanzadas.`
              : 'Necesitas generar pronósticos para ver análisis de machine learning.'
            }
          </p>
          <div className="space-y-3">
            <button 
              onClick={generateNewForecasts}
              disabled={state.isGenerating}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 mx-auto disabled:opacity-50 transition-all"
            >
              {state.isGenerating ? (
                <RefreshCw className="h-5 w-5 animate-spin" />
              ) : (
                <TrendingUp className="h-5 w-5" />
              )}
              {state.isGenerating ? 'Generando pronósticos...' : 'Generar Pronósticos ML'}
            </button>
            <p className={`text-xs ${isDarkMode ? 'text-gray-600' : 'text-gray-500'}`}>
              Los pronósticos se generarán usando modelos Prophet, ARIMA y Random Forest
            </p>
          </div>
        </div>
      );
    }

    console.log('✅ Usando pronósticos reales del estado principal:', { 
      totalForecasts: predictions.length,
      sampleForecast: predictions[0],
      stats 
    });

    // Definir tipo para los datos del gráfico
    interface ChartDataPoint {
      date: string;
      demanda_total: number;
      productos_count: number;
      fecha_completa: string;
    }

    // Obtener lista única de productos para el filtro
    const uniqueProducts = Array.from(new Set(predictions.map((p: any) => p.product_name))).filter(Boolean) as string[];
    
    // Procesar datos: Agrupar por fecha y calcular totales
    const groupedByDate: { [key: string]: any[] } = {};
    
    predictions.forEach((item: any) => {
      const dateKey = item.forecast_date || new Date().toISOString().split('T')[0];
      if (!groupedByDate[dateKey]) {
        groupedByDate[dateKey] = [];
      }
      groupedByDate[dateKey].push(item);
    });

    console.log('🔍 Debug agrupamiento por fecha:', {
      totalPredictions: predictions.length,
      groupedKeys: Object.keys(groupedByDate),
      groupSizes: Object.entries(groupedByDate).map(([date, items]) => ({ date, count: items.length }))
    });

    // Crear datos del gráfico
    let chartData: ChartDataPoint[] = [];

    if (selectedProductFilter === 'all') {
      // Mostrar demanda total acumulada por fecha
      chartData = Object.entries(groupedByDate)
        .map(([date, items]) => {
          const totalDemand = items.reduce((sum, item) => sum + (Number(item.predicted_demand) || 0), 0);
          console.log(`📊 Fecha ${date}: ${items.length} items, demanda total: ${totalDemand}`);
          
          return {
            date: new Date(date).toLocaleDateString('es-PE', { 
              day: '2-digit', 
              month: '2-digit' 
            }),
            demanda_total: totalDemand,
            productos_count: items.length,
            fecha_completa: date
          };
        })
        .sort((a, b) => new Date(a.fecha_completa).getTime() - new Date(b.fecha_completa).getTime());
    } else {
      // Mostrar evolución de un producto específico
      const productData = predictions.filter((p: any) => p.product_name === selectedProductFilter);
      const productGrouped: { [key: string]: any[] } = {};
      
      productData.forEach((item: any) => {
        const dateKey = item.forecast_date || new Date().toISOString().split('T')[0];
        if (!productGrouped[dateKey]) {
          productGrouped[dateKey] = [];
        }
        productGrouped[dateKey].push(item);
      });

      chartData = Object.entries(productGrouped)
        .map(([date, items]) => ({
          date: new Date(date).toLocaleDateString('es-PE', { 
            day: '2-digit', 
            month: '2-digit' 
          }),
          demanda_total: items.reduce((sum, item) => sum + (Number(item.predicted_demand) || 0), 0),
          productos_count: items.length,
          fecha_completa: date
        }))
        .sort((a, b) => new Date(a.fecha_completa).getTime() - new Date(b.fecha_completa).getTime());
    }

    console.log('📈 Datos finales del gráfico:', chartData);
    
    return (
      <div className="space-y-6">
        {/* Filtro de productos */}
        <div className={`border rounded-lg p-4 ${
          isDarkMode 
            ? 'bg-gray-700 border-gray-600' 
            : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-center gap-4">
            <label className={`text-sm font-medium ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Filtrar por producto:
            </label>
            <select
              value={selectedProductFilter}
              onChange={(e) => setSelectedProductFilter(e.target.value)}
              className={`px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                isDarkMode 
                  ? 'border-gray-600 bg-gray-800 text-gray-300' 
                  : 'border-gray-300 bg-white text-gray-900'
              }`}
            >
              <option value="all">📊 Demanda Total Acumulada (Todos los productos)</option>
              {uniqueProducts.map((product: string) => (
                <option key={product} value={product}>
                  📦 {product}
                </option>
              ))}
            </select>
          </div>
          <div className={`mt-2 text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
            {selectedProductFilter === 'all' 
              ? `Mostrando suma total de ${uniqueProducts.length} productos por fecha`
              : `Mostrando evolución temporal de "${selectedProductFilter}"`
            }
          </div>
        </div>

        {/* Gráfico REAL con datos de BD */}
        <div className={`border rounded-lg overflow-hidden ${
          isDarkMode 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        }`}>
          <div className={`px-6 py-4 border-b ${
            isDarkMode 
              ? 'border-gray-700 bg-gradient-to-r from-gray-700 to-gray-800' 
              : 'border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100'
          }`}>
            <h4 className={`font-semibold flex items-center gap-2 ${
              isDarkMode ? 'text-gray-100' : 'text-gray-900'
            }`}>
              <LineChart className="h-5 w-5 text-blue-600" />
              {selectedProductFilter === 'all' 
                ? 'Demanda Total Acumulada - Todos los Productos' 
                : `Evolución Temporal - ${selectedProductFilter}`
              }
            </h4>
            <p className={`text-sm mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              {predictions.length} pronósticos reales desde modelos Prophet, ARIMA y Random Forest
            </p>
          </div>
          
          <div className="p-6">
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsLineChart
                  data={chartData}
                  margin={{ top: 20, right: 40, left: 60, bottom: 60 }}
                >
                  <CartesianGrid 
                    strokeDasharray="3 3" 
                    stroke={isDarkMode ? "#4b5563" : "#e5e7eb"} 
                    opacity={0.7} 
                  />
                  <XAxis 
                    dataKey="date" 
                    stroke={isDarkMode ? "#d1d5db" : "#374151"}
                    fontSize={13}
                    fontWeight={500}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    tick={{ fill: isDarkMode ? "#d1d5db" : "#374151" }}
                    axisLine={{ stroke: isDarkMode ? "#6b7280" : "#d1d5db", strokeWidth: 2 }}
                    tickLine={{ stroke: isDarkMode ? "#6b7280" : "#9ca3af", strokeWidth: 1 }}
                  />
                  <YAxis 
                    stroke={isDarkMode ? "#d1d5db" : "#374151"}
                    fontSize={12}
                    fontWeight={500}
                    label={{ 
                      value: selectedProductFilter === 'all' ? 'Demanda Total (unidades)' : 'Demanda (unidades)', 
                      angle: -90, 
                      position: 'insideLeft',
                      style: { 
                        textAnchor: 'middle', 
                        fill: isDarkMode ? "#d1d5db" : "#374151", 
                        fontSize: '14px', 
                        fontWeight: '600' 
                      }
                    }}
                    tick={{ fill: isDarkMode ? "#d1d5db" : "#374151" }}
                    axisLine={{ stroke: isDarkMode ? "#6b7280" : "#d1d5db", strokeWidth: 2 }}
                    tickLine={{ stroke: isDarkMode ? "#6b7280" : "#9ca3af", strokeWidth: 1 }}
                    domain={[
                      (dataMin: number) => Math.max(0, dataMin * 0.95),
                      (dataMax: number) => dataMax * 1.05
                    ]}
                    tickFormatter={(value) => {
                      if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
                      if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
                      return value.toLocaleString();
                    }}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: isDarkMode ? 'rgba(31, 41, 59, 0.98)' : 'rgba(255, 255, 255, 0.98)',
                      border: isDarkMode ? '2px solid #4b5563' : '2px solid #e5e7eb',
                      borderRadius: '12px',
                      boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                      padding: '12px 16px',
                      fontSize: '14px',
                      fontWeight: '500',
                      color: isDarkMode ? '#f8fafc' : '#1f2937'
                    }}
                    labelStyle={{
                      color: isDarkMode ? '#f8fafc' : '#1f2937',
                      fontWeight: '600',
                      marginBottom: '8px'
                    }}
                    formatter={(value: any) => [
                      `${Number(value).toLocaleString('es-PE')} unidades`,
                      selectedProductFilter === 'all' ? 'Demanda Total' : 'Demanda Pronóstico'
                    ]}
                    labelFormatter={(label) => `📅 Fecha: ${label}`}
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className={`backdrop-blur-sm p-4 border-2 rounded-xl shadow-xl ${
                            isDarkMode 
                              ? 'bg-gray-800/98 border-blue-600' 
                              : 'bg-white/98 border-blue-100'
                          }`}>
                            <p className={`font-bold mb-2 flex items-center gap-2 ${
                              isDarkMode ? 'text-gray-100' : 'text-gray-800'
                            }`}>
                              <Calendar className="h-4 w-4 text-blue-600" />
                              {`Fecha: ${label}`}
                            </p>
                            <div className="space-y-2">
                              <p className="text-blue-400 font-semibold flex items-center gap-2">
                                <TrendingUp className="h-4 w-4" />
                                {selectedProductFilter === 'all' 
                                  ? `Demanda Total: ${data.demanda_total.toLocaleString('es-PE')} unidades`
                                  : `Demanda: ${data.demanda_total.toLocaleString('es-PE')} unidades`
                                }
                              </p>
                              {selectedProductFilter === 'all' && (
                                <p className={`text-sm flex items-center gap-2 ${
                                  isDarkMode ? 'text-gray-400' : 'text-gray-600'
                                }`}>
                                  <Package className="h-3 w-3" />
                                  {`${data.productos_count} productos incluidos`}
                                </p>
                              )}
                              <div className={`pt-2 border-t ${isDarkMode ? 'border-gray-600' : 'border-gray-200'}`}>
                                <p className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                                  Generado por modelos Prophet, ARIMA y Random Forest
                                </p>
                              </div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend 
                    wrapperStyle={{
                      paddingTop: '20px',
                      fontSize: '14px',
                      fontWeight: '600',
                      color: isDarkMode ? '#f8fafc' : '#1f2937'
                    }}
                    iconType="line"
                  />
                  
                  <Line
                    type="monotone"
                    dataKey="demanda_total"
                    stroke="#2563eb"
                    strokeWidth={4}
                    dot={{ 
                      fill: '#2563eb', 
                      strokeWidth: 3, 
                      r: 6,
                      stroke: isDarkMode ? '#1f2937' : '#ffffff'
                    }}
                    activeDot={{ 
                      r: 8, 
                      stroke: '#2563eb', 
                      strokeWidth: 3, 
                      fill: isDarkMode ? '#1f2937' : '#ffffff',
                      filter: 'drop-shadow(0 4px 6px rgba(37, 99, 235, 0.3))'
                    }}
                    name={selectedProductFilter === 'all' ? '📊 Demanda Total' : '📈 Demanda Pronóstico'}
                    connectNulls={false}
                    strokeDasharray={chartData.some(d => d.demanda_total > 100000) ? "5 5" : "0"}
                  />
                </RechartsLineChart>
              </ResponsiveContainer>
            </div>
            
            <div className={`mt-6 p-4 rounded-lg border ${
              isDarkMode 
                ? 'bg-gradient-to-r from-blue-900/30 to-indigo-900/30 border-blue-700' 
                : 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200'
            }`}>
              <div className="text-center">
                <p className={`text-sm font-semibold mb-2 flex items-center justify-center gap-2 ${
                  isDarkMode ? 'text-blue-400' : 'text-blue-800'
                }`}>
                  <BarChart3 className="h-4 w-4" />
                  Gráfico generado con {predictions.length} pronósticos REALES de la base de datos
                </p>
                <div className={`flex flex-wrap justify-center gap-4 text-xs ${
                  isDarkMode ? 'text-blue-300' : 'text-blue-700'
                }`}>
                  <span className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                    {selectedProductFilter === 'all' 
                      ? `Rango total: ${Math.min(...chartData.map(d => d.demanda_total)).toLocaleString()} - ${Math.max(...chartData.map(d => d.demanda_total)).toLocaleString()} unidades`
                      : `Rango: ${Math.min(...chartData.map(d => d.demanda_total)).toLocaleString()} - ${Math.max(...chartData.map(d => d.demanda_total)).toLocaleString()} unidades`
                    }
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {chartData.length} días de datos
                  </span>
                  <span className="flex items-center gap-1">
                    <Package className="h-3 w-3" />
                    {selectedProductFilter === 'all' ? `${uniqueProducts.length} productos` : '1 producto seleccionado'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Información técnica del dataset REAL */}
        <div className={`border rounded-lg p-4 ${
          isDarkMode 
            ? 'bg-blue-900/30 border-blue-700' 
            : 'bg-blue-50 border-blue-200'
        }`}>
          <h5 className={`font-medium mb-2 ${
            isDarkMode ? 'text-blue-400' : 'text-blue-900'
          }`}>Información REAL del Dataset ML</h5>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className={isDarkMode ? 'text-blue-300' : 'text-blue-700'}>Pronósticos en BD:</span>
              <div className="font-medium">{state.forecasts.length}</div>
            </div>
            <div>
              <span className={isDarkMode ? 'text-blue-300' : 'text-blue-700'}>Días con datos:</span>
              <div className="font-medium">{chartData.length}</div>
            </div>
            <div>
              <span className={isDarkMode ? 'text-blue-300' : 'text-blue-700'}>Productos únicos:</span>
              <div className="font-medium">{uniqueProducts.length}</div>
            </div>
            <div>
              <span className={isDarkMode ? 'text-blue-300' : 'text-blue-700'}>
                {selectedProductFilter === 'all' ? 'Demanda total promedio:' : 'Demanda promedio:'}
              </span>
              <div className="font-medium">{
                chartData.length > 0 ? 
                (chartData.reduce((sum, item) => sum + item.demanda_total, 0) / chartData.length).toFixed(1) : 
                'N/A'
              } unidades/día</div>
            </div>
          </div>
          <div className={`mt-3 text-xs ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`}>
            ✅ Fechas dinámicas obtenidas automáticamente de la BD - Sin valores hardcodeados
          </div>
        </div>
      </div>
    );
  };

  // ...existing utility functions...
  const getStockAlert = (forecast: DemandForecast) => {
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
      <div className={`flex items-center justify-center min-h-[400px] ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Cargando pronósticos desde Django...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 p-6 min-h-screen ${isDarkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-50 text-gray-900'}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className={`text-3xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
            Pronósticos de Demanda
          </h1>
          <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Sistema ML con análisis visual en tiempo real
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
            className={`px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50 transition-all border ${
              isDarkMode 
                ? 'border-gray-600 hover:bg-gray-700 text-gray-300' 
                : 'border-gray-300 hover:bg-gray-50 text-gray-700'
            }`}
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
      {(state.error || state.chartsError) && (
        <div className={`border rounded-lg p-4 flex items-center gap-2 ${
          isDarkMode 
            ? 'bg-red-900/20 border-red-800' 
            : 'bg-red-50 border-red-200'
        }`}>
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <span className={`${isDarkMode ? 'text-red-400' : 'text-red-800'}`}>
            {state.error || state.chartsError}
          </span>
        </div>
      )}

      {/* Visualización ML siempre visible */}
      {state.forecastData && (
        <div className={`rounded-lg shadow border p-6 ${
          isDarkMode 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        }`}>
          <div className="mb-6">
            <h2 className={`text-xl font-bold flex items-center gap-2 ${
              isDarkMode ? 'text-gray-100' : 'text-gray-900'
            }`}>
              <BarChart3 className="h-6 w-6 text-blue-600" />
              Análisis Visual de Machine Learning
              <span className={`text-sm px-2 py-1 rounded-full ml-2 ${
                isDarkMode 
                  ? 'bg-green-900/50 text-green-400' 
                  : 'bg-green-100 text-green-800'
              }`}>
                En Tiempo Real
              </span>
            </h2>
            <p className={`mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Pronósticos generados con modelos Prophet, ARIMA y Random Forest
            </p>
          </div>
          
          {state.chartsLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
              <span className={`ml-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Procesando modelos ML...
              </span>
            </div>
          ) : (
            <MLVisualization data={state.forecastData} />
          )}
        </div>
      )}

      {/* Grid de pronósticos y recomendaciones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pronósticos por Producto */}
        <div className={`rounded-lg shadow border ${
          isDarkMode 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        }`}>
          <div className={`p-6 border-b ${
            isDarkMode ? 'border-gray-700' : 'border-gray-200'
          }`}>
            <h3 className={`text-lg font-semibold ${
              isDarkMode ? 'text-gray-100' : 'text-gray-900'
            }`}>Pronósticos por Producto</h3>
            <p className={`text-sm ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Datos en tiempo real desde Django ({state.forecasts.length} productos)
            </p>
          </div>
          <div className="p-6">
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {state.forecasts.length === 0 ? (
                <div className="text-center py-8">
                  <Package className={`h-12 w-12 mx-auto mb-4 opacity-50 ${
                    isDarkMode ? 'text-gray-500' : 'text-gray-400'
                  }`} />
                  <p className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                    No hay pronósticos disponibles
                  </p>
                  <p className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                    Genere pronósticos para ver datos aquí
                  </p>
                </div>
              ) : (
                state.forecasts.slice(0, 10).map((forecast) => {
                  const stockAlert = getStockAlert(forecast);
                  return (
                    <div key={forecast.id} className={`p-4 border rounded-lg transition-colors ${
                      isDarkMode 
                        ? 'border-gray-600 hover:bg-gray-700/50' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className={`font-medium ${
                            isDarkMode ? 'text-gray-100' : 'text-gray-900'
                          }`}>{forecast.product_name}</h4>
                          <p className={`text-sm ${
                            isDarkMode ? 'text-gray-400' : 'text-gray-600'
                          }`}>SKU: {forecast.product_sku}</p>
                        </div>
                        <span className={stockAlert.className}>{stockAlert.message}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                            Demanda proyectada:
                          </span>
                          <p className={`font-medium ${
                            isDarkMode ? 'text-gray-100' : 'text-gray-900'
                          }`}>
                            {formatDemand(forecast.predicted_demand)} unidades
                          </p>
                        </div>
                        <div>
                          <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                            Fecha pronóstico:
                          </span>
                          <p className={`font-medium ${
                            isDarkMode ? 'text-gray-100' : 'text-gray-900'
                          }`}>{formatDate(forecast.forecast_date)}</p>
                        </div>
                      </div>
                      {forecast.confidence_level && (
                        <div className="mt-2 text-sm">
                          <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                            Confianza:
                          </span>
                          <span className={`font-medium ml-1 ${
                            isDarkMode ? 'text-gray-100' : 'text-gray-900'
                          }`}>
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
        <div className={`rounded-lg shadow border ${
          isDarkMode 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        }`}>
          <div className={`p-6 border-b ${
            isDarkMode ? 'border-gray-700' : 'border-gray-200'
          }`}>
            <h3 className={`text-lg font-semibold ${
              isDarkMode ? 'text-gray-100' : 'text-gray-900'
            }`}>Recomendaciones de Reorden</h3>
            <p className={`text-sm ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Basadas en pronósticos ML ({recommendations.length} recomendaciones)
            </p>
          </div>
          <div className="p-6">
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {loadingRecommendations ? (
                <div className="text-center py-8">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
                  <p className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                    Cargando recomendaciones...
                  </p>
                </div>
              ) : recommendations.length === 0 ? (
                <div className="text-center py-8">
                  <AlertTriangle className={`h-12 w-12 mx-auto mb-4 opacity-50 ${
                    isDarkMode ? 'text-gray-500' : 'text-gray-400'
                  }`} />
                  <p className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                    No hay recomendaciones disponibles
                  </p>
                  <p className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                    Genere recomendaciones para ver sugerencias aquí
                  </p>
                </div>
              ) : (
                recommendations.slice(0, 10).map((rec) => (
                  <div key={rec.id} className={`p-4 border rounded-lg transition-colors ${
                    isDarkMode 
                      ? 'border-gray-600 hover:bg-gray-700/50' 
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}>
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className={`font-medium ${
                          isDarkMode ? 'text-gray-100' : 'text-gray-900'
                        }`}>{rec.product_name}</h4>
                        <p className={`text-sm ${
                          isDarkMode ? 'text-gray-400' : 'text-gray-600'
                        }`}>SKU: {rec.product_sku}</p>
                      </div>
                      <span className={getPriorityColor(rec.priority)}>{rec.priority_display}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                          Cantidad recomendada:
                        </span>
                        <p className={`font-medium ${
                          isDarkMode ? 'text-gray-100' : 'text-gray-900'
                        }`}>
                          {formatDemand(rec.recommended_quantity)} unidades
                        </p>
                      </div>
                      <div>
                        <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                          Stock actual:
                        </span>
                        <p className={`font-medium ${
                          isDarkMode ? 'text-gray-100' : 'text-gray-900'
                        }`}>
                          {formatDemand(rec.current_stock)} unidades
                        </p>
                      </div>
                    </div>
                    <div className="mt-2 text-sm">
                      <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                        Fecha recomendada:
                      </span>
                      <span className={`font-medium ml-1 ${
                        isDarkMode ? 'text-gray-100' : 'text-gray-900'
                      }`}>
                        {formatDate(rec.recommended_order_date)}
                      </span>
                    </div>
                    {rec.days_until_stockout !== undefined && rec.days_until_stockout !== null && (
                      <div className="mt-1 text-sm">
                        <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                          Días hasta agotamiento:
                        </span>
                        <span className={`font-medium ml-1 ${
                          rec.days_until_stockout <= 7 
                            ? 'text-red-400' 
                            : isDarkMode ? 'text-green-400' : 'text-green-600'
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
        isDarkMode 
          ? 'bg-blue-900/30 border-blue-700 border-l-blue-500' 
          : 'bg-blue-50 border-blue-200 border-l-blue-500'
      }`}>
        <div className={`flex items-center gap-2 text-sm ${
          isDarkMode ? 'text-blue-400' : 'text-blue-800'
        }`}>
          <BarChart3 className="h-4 w-4" />
          <span>
            Sistema ML con visualización automática - 
            Pronósticos: {state.forecasts.length} | 
            Recomendaciones: {recommendations.length} | 
            Datos ML: {state.forecastData?.total_points || 0} puntos | 
            Última actualización: {new Date().toLocaleTimeString('es-PE')}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ForecastingPage;