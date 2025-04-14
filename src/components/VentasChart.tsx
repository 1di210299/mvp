// src/components/VentasChart.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts';
import { Calendar, Filter, Download, TrendingUp, TrendingDown, ShoppingCart, Users } from 'lucide-react';
import { chartService } from '../api/services';
import Plot from 'react-plotly.js';

interface VentasChartProps {
  datasetId: string | number;
}

function VentasChart({ datasetId }: VentasChartProps) {
  const [periodo, setPeriodo] = useState('mensual');
  const [tipoGrafico, setTipoGrafico] = useState('linea');
  const [region, setRegion] = useState('todas');
  const [datos, setDatos] = useState<any[]>([]);
  const [plotlyData, setPlotlyData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analisis, setAnalisis] = useState<any>(null);
  const [predicciones, setPredicciones] = useState<any[]>([]);
  const [recomendaciones, setRecomendaciones] = useState<string[]>([]);

  // Cargar datos de ventas
  const cargarDatos = useCallback(async () => {
    if (!datasetId) {
      setError("Se requiere un ID de dataset");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Cargar datos del dataset desde el backend
      const response = await fetch(`/api/datasets/${datasetId}/data`);
      if (!response.ok) throw new Error('Error al cargar los datos del dataset');
      
      const jsonData = await response.json();
      
      // Generar visualización con el backend según el período seleccionado
      const chartType = 
        periodo === 'mensual' ? 'sales' : 
        periodo === 'campañas' ? 'category' : 'regional';
        
      const categoryField = periodo === 'campañas' ? 'campaña' : undefined;
      const regionField = periodo === 'regional' ? 'region' : undefined;
      
      const chartResponse = await chartService.generateSalesVisualization(
        jsonData,
        chartType,
        categoryField,
        regionField
      );
      
      // Actualizar los estados con los datos recibidos del backend
      setPlotlyData(chartResponse.data.chart);
      setAnalisis(chartResponse.data.analysis);
      setPredicciones(chartResponse.data.predictions || []);
      setRecomendaciones(chartResponse.data.recommendations || []);
      setDatos(chartResponse.data.raw_data || []);
    } catch (err: any) {
      console.error('Error cargando datos:', err);
      setError(err.message || 'Error al cargar los datos');
      setDatos([]);
    } finally {
      setLoading(false);
    }
  }, [periodo, datasetId]);

  // Cargar datos cuando cambia el período o el datasetId
  useEffect(() => {
    cargarDatos();
  }, [cargarDatos, periodo, datasetId]);

  // Obtener valores para KPIs (de manera segura)
  const ultimoCrecimiento = analisis?.growth_rate || 0;
  const ultimasVentas = analisis?.total_sales || 0;
  const ticketPromedio = analisis?.average_sale || 0;
  
  // Determina color y flecha para crecimiento
  const colorCrecimiento = ultimoCrecimiento >= 0 ? 'text-green-400' : 'text-red-400';
  const iconoCrecimiento = ultimoCrecimiento >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />;

  // Función para formatear valores en soles
  const formatoSoles = (valor: number) => `S/ ${valor.toLocaleString('es-PE')}`;

  // Renderizar estado de carga
  if (loading) {
    return (
      <div className="w-full h-full flex flex-col bg-cyber-dark p-6 rounded-lg shadow-lg border border-cyber-cyan/20">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-cyber-cyan"></div>
        </div>
      </div>
    );
  }

  // Renderizar estado de error
  if (error) {
    return (
      <div className="w-full h-full flex flex-col bg-cyber-dark p-6 rounded-lg shadow-lg border border-cyber-cyan/20">
        <div className="flex flex-col items-center justify-center h-64">
          <p className="text-cyber-text/70 mb-4">{error}</p>
          <button 
            onClick={cargarDatos}
            className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col bg-cyber-dark p-6 rounded-lg shadow-lg border border-cyber-cyan/20">
      {/* Encabezado */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <h4 className="text-lg font-semibold text-cyber-text">
            Análisis de Ventas
            {periodo === 'mensual' && ' Mensuales'}
            {periodo === 'campañas' && ' por Campaña'}
            {periodo === 'regional' && ' por Región'}
          </h4>
          <span className={`ml-2 text-sm font-medium flex items-center ${colorCrecimiento}`}>
            {iconoCrecimiento}
            <span className="ml-1">{Math.abs(ultimoCrecimiento).toFixed(1)}%</span>
          </span>
        </div>
        <div className="flex space-x-2">
          <select
            className="border rounded px-2 py-1 text-sm bg-cyber-detail/30 text-cyber-text border-cyber-detail"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
          >
            <option value="mensual">Mensual</option>
            <option value="campañas">Por Campaña</option>
            <option value="regional">Por Región</option>
          </select>
          
          <select
            className="border rounded px-2 py-1 text-sm bg-cyber-detail/30 text-cyber-text border-cyber-detail"
            value={tipoGrafico}
            onChange={(e) => setTipoGrafico(e.target.value)}
          >
            <option value="linea">Línea</option>
            <option value="barra">Barras</option>
            {plotlyData && <option value="avanzado">Avanzado</option>}
          </select>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-cyber-detail/20 border border-cyber-cyan/30 rounded-lg p-3 flex items-center">
          <div className="bg-cyber-cyan/20 rounded-full p-2 mr-3">
            <ShoppingCart size={20} className="text-cyber-cyan" />
          </div>
          <div>
            <p className="text-xs text-cyber-text/70">Ventas Totales</p>
            <p className="text-xl font-bold text-cyber-text">{formatoSoles(ultimasVentas)}</p>
          </div>
        </div>
        
        <div className="bg-cyber-detail/20 border border-cyber-cyan/30 rounded-lg p-3 flex items-center">
          <div className="bg-cyber-cyan/20 rounded-full p-2 mr-3">
            <TrendingUp size={20} className="text-cyber-cyan" />
          </div>
          <div>
            <p className="text-xs text-cyber-text/70">Ticket Promedio</p>
            <p className="text-xl font-bold text-cyber-text">{formatoSoles(ticketPromedio)}</p>
          </div>
        </div>
        
        <div className="bg-cyber-detail/20 border border-cyber-cyan/30 rounded-lg p-3 flex items-center">
          <div className="bg-cyber-cyan/20 rounded-full p-2 mr-3">
            <Users size={20} className="text-cyber-cyan" />
          </div>
          <div>
            <p className="text-xs text-cyber-text/70">Frecuencia Compra</p>
            <p className="text-xl font-bold text-cyber-text">
              {analisis?.purchase_frequency || "N/A"}
            </p>
          </div>
        </div>
      </div>

      {/* Gráfico principal */}
      <div className="flex-grow relative" style={{ minHeight: '300px', width: '100%' }}>
        {datos.length > 0 ? (
          tipoGrafico === 'avanzado' && plotlyData ? (
            <Plot
              data={plotlyData.data}
              layout={{...plotlyData.layout, autosize: true}}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler={true}
            />
          ) : tipoGrafico === 'linea' ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={datos} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                <XAxis 
                  dataKey={periodo === 'mensual' ? 'formatted_date' : periodo === 'campañas' ? 'category' : 'region'} 
                  stroke="#E6E6E6" 
                />
                <YAxis 
                  stroke="#E6E6E6" 
                  tickFormatter={(value) => `S/ ${(value/1000).toFixed(0)}k`} 
                />
                <Tooltip 
                  formatter={(value: number) => [`S/ ${value.toLocaleString('es-PE')}`, 'Ventas']} 
                  labelFormatter={(label) => `${label}`}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }} 
                />
                <Legend />
                <Line
                  type="monotone"
                  name="Ventas (S/)"
                  dataKey="sales"
                  stroke="#00E6E6"
                  strokeWidth={2}
                  dot={{ r: 4, stroke: '#00E6E6', strokeWidth: 1, fill: '#0A192F' }}
                  activeDot={{ r: 6, stroke: '#00E6E6', strokeWidth: 2, fill: '#00E6E6' }}
                />
                {datos[0]?.ticket && (
                  <Line
                    type="monotone"
                    name="Ticket Promedio (S/)"
                    dataKey="ticket"
                    stroke="#4CAF50"
                    strokeWidth={2}
                    dot={{ r: 4, stroke: '#4CAF50', strokeWidth: 1, fill: '#0A192F' }}
                    activeDot={{ r: 6, stroke: '#4CAF50', strokeWidth: 2, fill: '#4CAF50' }}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={datos} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                <XAxis 
                  dataKey={periodo === 'mensual' ? 'formatted_date' : periodo === 'campañas' ? 'category' : 'region'} 
                  stroke="#E6E6E6" 
                />
                <YAxis 
                  stroke="#E6E6E6" 
                  tickFormatter={(value) => `S/ ${(value/1000).toFixed(0)}k`} 
                />
                <Tooltip 
                  formatter={(value: number, name: string) => {
                    return [`S/ ${value.toLocaleString('es-PE')}`, name];
                  }} 
                  labelFormatter={(label) => `${label}`}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }} 
                />
                <Legend />
                <Bar 
                  name="Ventas (S/)" 
                  dataKey="sales" 
                  fill="#00E6E6"
                  radius={[4, 4, 0, 0]}
                />
                {datos[0]?.ticket && (
                  <Bar 
                    name="Ticket (S/)" 
                    dataKey="ticket" 
                    fill="#4CAF50"
                    radius={[4, 4, 0, 0]} 
                  />
                )}
              </BarChart>
            </ResponsiveContainer>
          )
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-cyber-text/70 mb-2">No hay datos disponibles para este período</p>
            <button 
              onClick={cargarDatos}
              className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors"
            >
              Actualizar
            </button>
          </div>
        )}
        
        {/* Overlay con insights */}
        {recomendaciones.length > 0 && (
          <div className="absolute bottom-2 right-2 bg-cyber-dark/80 border border-cyber-cyan/30 p-3 rounded-lg max-w-xs">
            <h5 className="text-xs font-bold text-cyber-cyan mb-1 flex items-center">
              <TrendingUp size={14} className="mr-1" />
              INSIGHTS IA
            </h5>
            <p className="text-xs text-cyber-text">
              {recomendaciones[0]}
            </p>
          </div>
        )}
      </div>
      
      {/* Predicción */}
      {predicciones.length > 0 && (
        <div className="mt-6 bg-cyber-detail/20 border border-cyber-cyan/30 rounded-lg p-4">
          <h5 className="text-sm font-bold text-cyber-text mb-2 flex items-center">
            <Calendar size={16} className="mr-2 text-cyber-cyan" />
            Proyección Próximos 30 Días
          </h5>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-cyber-text/70">Ventas Proyectadas</p>
              <p className="text-lg font-bold text-cyber-text">
                {formatoSoles(predicciones[0]?.sales || 0)}
              </p>
              <p className="text-xs text-green-400 flex items-center">
                {analisis?.prediction?.growth_rate >= 0 ? 
                  <TrendingUp size={12} className="mr-1" /> : 
                  <TrendingDown size={12} className="mr-1" />
                }
                {analisis?.prediction?.growth_rate >= 0 ? '+' : ''}
                {analisis?.prediction?.growth_rate?.toFixed(1) || 0}% vs período anterior
              </p>
            </div>
            <div>
              <p className="text-xs text-cyber-text/70">Ticket Proyectado</p>
              <p className="text-lg font-bold text-cyber-text">
                {formatoSoles(analisis?.prediction?.average_sale || 0)}
              </p>
              <p className="text-xs text-green-400 flex items-center">
                {(analisis?.prediction?.average_sale > ticketPromedio) ? 
                  <TrendingUp size={12} className="mr-1" /> : 
                  <TrendingDown size={12} className="mr-1" />
                }
                {((analisis?.prediction?.average_sale / (ticketPromedio || 1) - 1) * 100).toFixed(1)}% 
                vs actual
              </p>
            </div>
            <div>
              <p className="text-xs text-cyber-text/70">Confianza Predicción</p>
              <div className="w-full bg-cyber-detail/50 h-2 rounded-full mt-2">
                <div 
                  className="bg-cyber-cyan h-2 rounded-full" 
                  style={{ width: `${analisis?.prediction?.confidence || 0}%` }}
                ></div>
              </div>
              <p className="text-xs text-cyber-text/70 mt-1">{analisis?.prediction?.confidence || 0}% de confianza</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default VentasChart;