// src/components/DatasetsChart.tsx
import React, { useState } from 'react';
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
import { Calendar, Filter, Download, BarChart2, DollarSign } from 'lucide-react';

// Datos de ventas mensuales de la empresa
const monthlyData = [
  { month: 'Ene', ventas: 125000, growth: 0 },
  { month: 'Feb', ventas: 148000, growth: 18.4 },
  { month: 'Mar', ventas: 142000, growth: -4.1 },
  { month: 'Abr', ventas: 168000, growth: 18.3 },
  { month: 'May', ventas: 185000, growth: 10.1 },
  { month: 'Jun', ventas: 192000, growth: 3.8 },
  { month: 'Jul', ventas: 326000, growth: 69.8 }, // Fiestas Patrias
  { month: 'Ago', ventas: 258000, growth: -20.9 },
  { month: 'Sep', ventas: 274000, growth: 6.2 },
  { month: 'Oct', ventas: 298000, growth: 8.8 },
  { month: 'Nov', ventas: 425000, growth: 42.6 }, // Black Friday / Cyber Days
  { month: 'Dic', ventas: 489000, growth: 15.1 }, // Navidad
];

// Datos por categoría de producto
const categoryData = [
  { month: 'Categoría A', ventas: 580000, growth: 0 },
  { month: 'Categoría B', ventas: 420000, growth: -27.6 },
  { month: 'Categoría C', ventas: 360000, growth: -14.3 },
  { month: 'Categoría D', ventas: 180000, growth: -50.0 },
  { month: 'Categoría E', ventas: 90000, growth: -50.0 },
];

// Datos por región
const regionData = [
  { month: 'Lima Norte', ventas: 620000, growth: 0 },
  { month: 'Lima Centro', ventas: 480000, growth: -22.6 },
  { month: 'Lima Sur', ventas: 280000, growth: -41.7 },
  { month: 'Lima Este', ventas: 340000, growth: 21.4 },
  { month: 'Callao', ventas: 120000, growth: -64.7 },
  { month: 'Provincias', ventas: 190000, growth: 58.3 },
];

function DatasetsChart() {
  const [period, setPeriod] = useState('monthly');
  const [chartType, setChartType] = useState('line');

  const getPeriodData = () => {
    switch (period) {
      case 'category':
        return categoryData;
      case 'region':
        return regionData;
      default:
        return monthlyData;
    }
  };

  const data = getPeriodData();
  const currentGrowth = data[data.length - 1].growth;
  const latestValue = data[data.length - 1].ventas;
  
  // Calcular el total de ventas para mostrar en el KPI
  const totalVentas = monthlyData.reduce((sum, item) => sum + item.ventas, 0);

  // Determina color y flecha para crecimiento
  const growthColor = currentGrowth >= 0 ? 'text-green-400' : 'text-red-400';
  const growthIcon = currentGrowth >= 0 ? '↑' : '↓';

  return (
    <div className="w-full h-full flex flex-col bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-cyber-cyan/20 shadow-lg">
      {/* Encabezado */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <h4 className="text-lg font-semibold text-cyber-text">Análisis de Ventas</h4>
          <span className={`ml-2 text-sm font-medium ${growthColor}`}>
            {growthIcon} {Math.abs(currentGrowth).toFixed(1)}%
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
            <p className="text-xs text-cyber-text/70">Ventas Totales</p>
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
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'line' ? (
              <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                <XAxis dataKey="month" stroke="#E6E6E6" />
                <YAxis 
                  stroke="#E6E6E6" 
                  tickFormatter={(value) => `S/ ${(value/1000).toFixed(0)}K`}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0A192F', border: '1px solid #1C3D5A', color: '#E6E6E6' }} 
                  formatter={(value) => [`S/ ${value.toLocaleString()}`, 'Ventas']}
                />
                <Line
                  type="monotone"
                  dataKey="ventas"
                  stroke="#00E6E6"
                  strokeWidth={2}
                  dot={{ r: 4, stroke: '#00E6E6', strokeWidth: 1, fill: '#0A192F' }}
                  activeDot={{ r: 6, stroke: '#00E6E6', strokeWidth: 1, fill: '#00E6E6' }}
                />
              </LineChart>
            ) : (
              <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                <XAxis dataKey="month" stroke="#E6E6E6" />
                <YAxis 
                  stroke="#E6E6E6" 
                  tickFormatter={(value) => `S/ ${(value/1000).toFixed(0)}K`}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0A192F', border: '1px solid #1C3D5A', color: '#E6E6E6' }} 
                  formatter={(value) => [`S/ ${value.toLocaleString()}`, 'Ventas']}
                />
                <Bar 
                  dataKey="ventas" 
                  fill="#00E6E6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            )}
          </ResponsiveContainer>
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-cyber-text/70 mb-2">No hay datos disponibles para este período</p>
            <button className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors">
              Importar datos de ventas
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default DatasetsChart;