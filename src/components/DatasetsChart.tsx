// src/components/DatasetsChart.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
} from 'recharts';
import { Calendar, Filter, Download, DollarSign } from 'lucide-react';
import { chartService } from '../api/services';
import Plot from 'react-plotly.js';

interface DatasetsChartProps {
  datasetId: string | number;
}

function DatasetsChart({ datasetId }: DatasetsChartProps) {
  const [period, setPeriod] = useState('monthly');
  const [chartType, setChartType] = useState('line');
  const [data, setData] = useState<any[]>([]);
  const [plotlyData, setPlotlyData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);

  // Cargar datos del dataset
  const loadData = useCallback(async () => {
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
      
      // Generar visualización según el período seleccionado
      const chartType = 
        period === 'monthly' ? 'sales' : 
        period === 'category' ? 'category' : 'regional';
      
      const chartResponse = await chartService.generateChart(jsonData, chartType);
      
      // Actualizar estados con los datos del backend
      setPlotlyData(chartResponse.data.chart);
      setAnalysis(chartResponse.data.analysis);
      setData(chartResponse.data.raw_data || []);
    } catch (err: any) {
      console.error('Error cargando datos:', err);
      setError(err.message || 'Error al cargar los datos');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [period, datasetId]);

  // Cargar datos cuando cambia el período o el datasetId
  useEffect(() => {
    loadData();
  }, [loadData, period, datasetId]);

  // Formatear totales para KPI (de manera segura)
  const totalVentas = analysis?.total_sales || 0;
  const growthRate = analysis?.growth_rate || 0;
  
  // Determinar color para el crecimiento
  const growthColor = growthRate >= 0 ? 'text-green-400' : 'text-red-400';
  const growthIcon = growthRate >= 0 ? '↑' : '↓';

  // Renderizar estado de carga
  if (loading) {
    return (
      <div className="w-full h-full flex flex-col bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-cyber-cyan"></div>
        </div>
      </div>
    );
  }

  // Renderizar estado de error
  if (error) {
    return (
      <div className="w-full h-full flex flex-col bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex flex-col items-center justify-center h-64">
          <p className="text-cyber-text/70 mb-4">{error}</p>
          <button 
            onClick={loadData}
            className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-cyber-cyan/20 shadow-lg">
      {/* Encabezado */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <h4 className="text-lg font-semibold text-cyber-text">Análisis de Datos</h4>
          <span className={`ml-2 text-sm font-medium ${growthColor}`}>
            {growthIcon} {Math.abs(growthRate).toFixed(1)}%
          </span>
        </div>
        <div className="flex space-x-2">
          <select
            className="border rounded px-2 py-1 text-sm bg-cyber-cyan/10 text-cyber-text border-cyber-cyan/30"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
          >
            <option value="monthly">Por Mes</option>
            <option value="category">Por Categoría</option>
            <option value="region">Por Región</option>
          </select>
          <select
            className="border rounded px-2 py-1 text-sm bg-cyber-cyan/10 text-cyber-text border-cyber-cyan/30"
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
          >
            <option value="line">Línea</option>
            <option value="bar">Barras</option>
            {plotlyData && <option value="advanced">Avanzado</option>}
          </select>
        </div>
      </div>

      {/* KPI: Total Ventas */}
      <div className="flex flex-col md:flex-row md:justify-between mb-4">
        <div className="bg-cyber-cyan/10 border border-cyber-cyan/30 rounded-lg p-3 mb-2 md:mb-0 flex items-center">
          <div className="bg-cyber-cyan rounded-full p-2 mr-3 text-cyber-dark">
            <DollarSign size={20} />
          </div>
          <div>
            <p className="text-xs text-cyber-text/70">Total</p>
            <p className="text-xl font-bold text-cyber-text">S/ {(totalVentas / 1000).toFixed(0)}K</p>
          </div>
        </div>
        <div className="flex space-x-2">
          <button className="flex items-center px-3 py-1.5 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded hover:bg-cyber-detail/50 transition-colors">
            <Filter size={16} className="mr-1" />
            Filtros
          </button>
          <button className="flex items-center px-3 py-1.5 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded hover:bg-cyber-detail/50 transition-colors">
            <Download size={16} className="mr-1" />
            Exportar
          </button>
        </div>
      </div>

      {/* Gráfico principal */}
      <div className="flex-grow" style={{ minHeight: '250px', width: '100%' }}>
        {data.length > 0 ? (
          chartType === 'advanced' && plotlyData ? (
            <Plot
              data={plotlyData.data}
              layout={{...plotlyData.layout, autosize: true}}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler={true}
            />
          ) : chartType === 'line' ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                <XAxis dataKey={
                  period === 'monthly' ? 'formatted_date' : 
                  period === 'category' ? 'category' : 'region'
                } stroke="#E6E6E6" />
                <YAxis 
                  stroke="#E6E6E6" 
                  tickFormatter={(value) => `S/ ${(value/1000).toFixed(0)}K`}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0A192F', border: '1px solid #1C3D5A', color: '#E6E6E6' }} 
                  formatter={(value: any) => [`S/ ${Number(value).toLocaleString()}`, 'Valor']}
                />
                <Line
                  type="monotone"
                  dataKey={period === 'monthly' ? 'sales' : 'value'}
                  stroke="#00E6E6"
                  strokeWidth={2}
                  dot={{ r: 4, stroke: '#00E6E6', strokeWidth: 1, fill: '#0A192F' }}
                  activeDot={{ r: 6, stroke: '#00E6E6', strokeWidth: 1, fill: '#00E6E6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                <XAxis dataKey={
                  period === 'monthly' ? 'formatted_date' : 
                  period === 'category' ? 'category' : 'region'
                } stroke="#E6E6E6" />
                <YAxis 
                  stroke="#E6E6E6" 
                  tickFormatter={(value) => `S/ ${(value/1000).toFixed(0)}K`}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0A192F', border: '1px solid #1C3D5A', color: '#E6E6E6' }} 
                  formatter={(value: any) => [`S/ ${Number(value).toLocaleString()}`, 'Valor']}
                />
                <Bar 
                  dataKey={period === 'monthly' ? 'sales' : 'value'}
                  fill="#00E6E6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-cyber-text/70 mb-2">No hay datos disponibles para este período</p>
            <button 
              onClick={loadData}
              className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors"
            >
              Actualizar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default DatasetsChart;