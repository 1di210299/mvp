// src/components/VentasChart.tsx
import React, { useState } from 'react';
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
import { Calendar, Filter, Download, ArrowDown, ArrowUp, TrendingUp, TrendingDown } from 'lucide-react';

// Datos de ejemplo para ventas en soles peruanos
const ventasMensuales = [
  { mes: 'Ene', ventas: 12400, crecimiento: 0, ticket: 85 },
  { mes: 'Feb', ventas: 15600, crecimiento: 25.8, ticket: 92 },
  { mes: 'Mar', ventas: 18700, crecimiento: 19.9, ticket: 98 },
  { mes: 'Abr', ventas: 16500, crecimiento: -11.8, ticket: 90 },
  { mes: 'May', ventas: 21700, crecimiento: 31.5, ticket: 105 },
  { mes: 'Jun', ventas: 25100, crecimiento: 15.7, ticket: 110 },
  { mes: 'Jul', ventas: 23200, crecimiento: -7.6, ticket: 108 },
  { mes: 'Ago', ventas: 28200, crecimiento: 21.6, ticket: 115 },
  { mes: 'Sep', ventas: 32400, crecimiento: 14.9, ticket: 120 },
  { mes: 'Oct', ventas: 35300, crecimiento: 9.0, ticket: 125 },
  { mes: 'Nov', ventas: 42100, crecimiento: 19.3, ticket: 130 },
  { mes: 'Dic', ventas: 48500, crecimiento: 15.2, ticket: 135 },
];

// Datos por campaña (fiestas patrias, navidad, etc)
const ventasCampañas = [
  { campaña: 'San Valentín', ventas: 18200, crecimiento: 15.3, ticket: 95 },
  { campaña: 'Día Madre', ventas: 29800, crecimiento: 22.5, ticket: 125 },
  { campaña: 'Día Padre', ventas: 21400, crecimiento: 5.8, ticket: 115 },
  { campaña: 'Fiestas Patrias', ventas: 32600, crecimiento: 18.9, ticket: 120 },
  { campaña: 'Primavera', ventas: 19500, crecimiento: 8.2, ticket: 90 },
  { campaña: 'Halloween', ventas: 15700, crecimiento: 12.4, ticket: 85 },
  { campaña: 'Navidad', ventas: 48900, crecimiento: 24.8, ticket: 140 },
];

// Datos por región del Perú
const ventasRegionales = [
  { region: 'Lima', ventas: 68500, penetracion: 42, ticket: 125, crecimiento: 12.3 },
  { region: 'Arequipa', ventas: 28400, penetracion: 18, ticket: 110, crecimiento: 9.7 },
  { region: 'Trujillo', ventas: 22300, penetracion: 14, ticket: 105, crecimiento: 8.4 },
  { region: 'Cusco', ventas: 15700, penetracion: 10, ticket: 95, crecimiento: 7.2 },
  { region: 'Piura', ventas: 12600, penetracion: 8, ticket: 90, crecimiento: 6.8 },
  { region: 'Chiclayo', ventas: 10200, penetracion: 6, ticket: 85, crecimiento: 5.3 },
  { region: 'Otros', ventas: 3800, penetracion: 2, ticket: 75, crecimiento: 2.1 }
];

function VentasChart() {
  const [periodo, setPeriodo] = useState('mensual');
  const [tipoGrafico, setTipoGrafico] = useState('linea');
  const [region, setRegion] = useState('todas');

  const obtenerDatosPeriodo = () => {
    switch (periodo) {
      case 'campañas':
        return ventasCampañas;
      case 'regional':
        return ventasRegionales;
      default:
        return ventasMensuales;
    }
  };

  const datos = obtenerDatosPeriodo();
  const ultimoCrecimiento = datos[datos.length - 1].crecimiento;
  const ultimasVentas = datos[datos.length - 1].ventas;
  const ticketPromedio = datos[datos.length - 1].ticket;
  
  // Determina color y flecha para crecimiento
  const colorCrecimiento = ultimoCrecimiento >= 0 ? 'text-green-400' : 'text-red-400';
  const iconoCrecimiento = ultimoCrecimiento >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />;

  // Función para formatear valores en soles
  const formatoSoles = (valor: number) => `S/ ${valor.toLocaleString('es-PE')}`;

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
            <p className="text-xl font-bold text-cyber-text">15.8 días</p>
          </div>
        </div>
      </div>

      {/* Controles y filtros */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex space-x-2">
          {periodo === 'regional' && (
            <select
              className="border rounded px-2 py-1 text-sm bg-cyber-detail/30 text-cyber-text border-cyber-detail"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
            >
              <option value="todas">Todas las regiones</option>
              <option value="costa">Costa</option>
              <option value="sierra">Sierra</option>
              <option value="selva">Selva</option>
            </select>
          )}
        </div>
        
        <div className="flex space-x-2">
          <button className="flex items-center bg-cyber-detail text-cyber-text px-3 py-1 rounded text-sm hover:bg-cyber-detail/90 transition-colors">
            <Filter size={16} className="mr-1" />
            Filtros
          </button>
          
          <button className="flex items-center bg-cyber-detail text-cyber-text px-3 py-1 rounded text-sm hover:bg-cyber-detail/90 transition-colors">
            <Download size={16} className="mr-1" />
            Exportar
          </button>
        </div>
      </div>

      {/* Gráfico principal */}
      <div className="flex-grow relative" style={{ minHeight: '300px', width: '100%' }}>
        {datos.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            {tipoGrafico === 'linea' ? (
              <LineChart data={datos} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                <XAxis 
                  dataKey={periodo === 'mensual' ? 'mes' : periodo === 'campañas' ? 'campaña' : 'region'} 
                  stroke="#E6E6E6" 
                />
                <YAxis stroke="#E6E6E6" tickFormatter={(value) => `S/ ${(value/1000).toFixed(0)}k`} />
                <Tooltip 
                  formatter={(value: number) => [`S/ ${value.toLocaleString('es-PE')}`, 'Ventas']} 
                  labelFormatter={(label) => `${label}`}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }} 
                />
                <Legend />
                <Line
                  type="monotone"
                  name="Ventas (S/)"
                  dataKey="ventas"
                  stroke="#00E6E6"
                  strokeWidth={2}
                  dot={{ r: 4, stroke: '#00E6E6', strokeWidth: 1, fill: '#0A192F' }}
                  activeDot={{ r: 6, stroke: '#00E6E6', strokeWidth: 2, fill: '#00E6E6' }}
                />
                <Line
                  type="monotone"
                  name="Ticket Promedio (S/)"
                  dataKey="ticket"
                  stroke="#4CAF50"
                  strokeWidth={2}
                  dot={{ r: 4, stroke: '#4CAF50', strokeWidth: 1, fill: '#0A192F' }}
                  activeDot={{ r: 6, stroke: '#4CAF50', strokeWidth: 2, fill: '#4CAF50' }}
                />
              </LineChart>
            ) : (
              <BarChart data={datos} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                <XAxis 
                  dataKey={periodo === 'mensual' ? 'mes' : periodo === 'campañas' ? 'campaña' : 'region'} 
                  stroke="#E6E6E6" 
                />
                <YAxis stroke="#E6E6E6" tickFormatter={(value) => `S/ ${(value/1000).toFixed(0)}k`} />
                <Tooltip 
                  formatter={(value: number, name: string) => {
                    if (name === 'Ventas (S/)') return [`S/ ${value.toLocaleString('es-PE')}`, name];
                    if (name === 'Ticket (S/)') return [`S/ ${value.toLocaleString('es-PE')}`, name];
                    return [value, name];
                  }} 
                  labelFormatter={(label) => `${label}`}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }} 
                />
                <Legend />
                <Bar 
                  name="Ventas (S/)" 
                  dataKey="ventas" 
                  fill="#00E6E6"
                  radius={[4, 4, 0, 0]}
                />
                <Bar 
                  name="Ticket (S/)" 
                  dataKey="ticket" 
                  fill="#4CAF50"
                  radius={[4, 4, 0, 0]} 
                />
              </BarChart>
            )}
          </ResponsiveContainer>
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-cyber-text/70 mb-2">No hay datos disponibles para este período</p>
            <button className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors">
              Cargar datos
            </button>
          </div>
        )}
        
        {/* Overlay con insights */}
        <div className="absolute bottom-2 right-2 bg-cyber-dark/80 border border-cyber-cyan/30 p-3 rounded-lg max-w-xs">
          <h5 className="text-xs font-bold text-cyber-cyan mb-1 flex items-center">
            <TrendingUp size={14} className="mr-1" />
            INSIGHTS IA
          </h5>
          <p className="text-xs text-cyber-text">
            {periodo === 'mensual' && 'Las ventas muestran un patrón estacional con picos en Julio (Fiestas Patrias) y Diciembre (Navidad). Considere aumentar inventario 45 días antes.'}
            {periodo === 'campañas' && 'La campaña de Navidad genera 247% más ventas que el promedio. Recomendamos aumentar publicidad en redes sociales 60 días antes.'}
            {periodo === 'regional' && 'Lima representa 42% de las ventas totales. Hay oportunidad de crecimiento en Arequipa y Trujillo con promociones localizadas.'}
          </p>
        </div>
      </div>
      
      {/* Predicción a corto plazo */}
      <div className="mt-6 bg-cyber-detail/20 border border-cyber-cyan/30 rounded-lg p-4">
        <h5 className="text-sm font-bold text-cyber-text mb-2 flex items-center">
          <Calendar size={16} className="mr-2 text-cyber-cyan" />
          Proyección Próximos 30 Días
        </h5>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-cyber-text/70">Ventas Proyectadas</p>
            <p className="text-lg font-bold text-cyber-text">S/ 52,800</p>
            <p className="text-xs text-green-400 flex items-center">
              <ArrowUp size={12} className="mr-1" />
              +9.8% vs período anterior
            </p>
          </div>
          <div>
            <p className="text-xs text-cyber-text/70">Ticket Proyectado</p>
            <p className="text-lg font-bold text-cyber-text">S/ 142</p>
            <p className="text-xs text-green-400 flex items-center">
              <ArrowUp size={12} className="mr-1" />
              +5.2% vs período anterior
            </p>
          </div>
          <div>
            <p className="text-xs text-cyber-text/70">Confianza Predicción</p>
            <div className="w-full bg-cyber-detail/50 h-2 rounded-full mt-2">
              <div className="bg-cyber-cyan h-2 rounded-full" style={{ width: '87%' }}></div>
            </div>
            <p className="text-xs text-cyber-text/70 mt-1">87% de confianza</p>
          </div>
        </div>
      </div>
    </div>
  );
}

import { ShoppingCart, Users } from 'lucide-react';

export default VentasChart;