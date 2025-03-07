// src/pages/SegmentacionClientes.tsx
import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Users, Filter, Download, Map, CreditCard, ShoppingBag, Clock, DollarSign } from 'lucide-react';

const SegmentacionClientes = () => {
  const [filtroSegmento, setFiltroSegmento] = useState<string>('todos');
  const [filtroRegion, setFiltroRegion] = useState<string>('todas');
  
  // Datos para gráfico de segmentación RFM (Recencia, Frecuencia, Monto)
  const segmentosRFM = [
    { nombre: 'Campeones', valor: 22, clientes: 165, ventas: 'S/ 68,400', color: '#00E6E6' },
    { nombre: 'Leales', valor: 28, clientes: 210, ventas: 'S/ 45,200', color: '#4CAF50' },
    { nombre: 'Potenciales', valor: 18, clientes: 135, ventas: 'S/ 28,500', color: '#2196F3' },
    { nombre: 'Necesitan Atención', valor: 15, clientes: 112, ventas: 'S/ 16,800', color: '#FFC107' },
    { nombre: 'En Riesgo', valor: 10, clientes: 75, ventas: 'S/ 8,400', color: '#FF5722' },
    { nombre: 'Inactivos', valor: 7, clientes: 53, ventas: 'S/ 0', color: '#757575' }
  ];
  
  // Datos demográficos por edad
  const demografiaEdad = [
    { grupo: '18-24', porcentaje: 12, ventas: 'S/ 15,200' },
    { grupo: '25-34', porcentaje: 28, ventas: 'S/ 35,400' },
    { grupo: '35-44', porcentaje: 32, ventas: 'S/ 40,500' },
    { grupo: '45-54', porcentaje: 18, ventas: 'S/ 22,800' },
    { grupo: '55+', porcentaje: 10, ventas: 'S/ 12,600' }
  ];
  
  // Datos frecuencia de compra
  const frecuenciaCompra = [
    { periodo: 'Diario', clientes: 5, valor: 5 },
    { periodo: 'Semanal', clientes: 22, valor: 22 },
    { periodo: 'Quincenal', clientes: 35, valor: 35 },
    { periodo: 'Mensual', clientes: 25, valor: 25 },
    { periodo: 'Trimestral', clientes: 8, valor: 8 },
    { periodo: 'Semestral', clientes: 3, valor: 3 },
    { periodo: 'Anual', clientes: 2, valor: 2 }
  ];
  
  // Datos para tabla de clientes más valiosos
  const clientesValiosos = [
    { id: 1, nombre: 'Empresa Comercial ABC', tipo: 'Empresa', ticket: 'S/ 850', compras: 24, total: 'S/ 20,400', region: 'Lima' },
    { id: 2, nombre: 'Juan Carlos Mendoza', tipo: 'Persona', ticket: 'S/ 380', compras: 42, total: 'S/ 15,960', region: 'Lima' },
    { id: 3, nombre: 'Distribuidora Sur E.I.R.L.', tipo: 'Empresa', ticket: 'S/ 720', compras: 18, total: 'S/ 12,960', region: 'Arequipa' },
    { id: 4, nombre: 'María Fernández López', tipo: 'Persona', ticket: 'S/ 250', compras: 36, total: 'S/ 9,000', region: 'Trujillo' },
    { id: 5, nombre: 'MiTienda Online S.A.C.', tipo: 'Empresa', ticket: 'S/ 630', compras: 14, total: 'S/ 8,820', region: 'Lima' }
  ];
  
  // Métricas por segmento
  const metricasSegmento = (segmento: string) => {
    switch (segmento) {
      case 'Campeones':
        return {
          recencia: '5 días',
          frecuencia: '3.8 compras/mes',
          ticket: 'S/ 415',
          ltv: 'S/ 12,450'
        };
      case 'Leales':
        return {
          recencia: '12 días',
          frecuencia: '2.2 compras/mes',
          ticket: 'S/ 215',
          ltv: 'S/ 6,450'
        };
      case 'Potenciales':
        return {
          recencia: '18 días',
          frecuencia: '1.5 compras/mes',
          ticket: 'S/ 280',
          ltv: 'S/ 5,040'
        };
      case 'Necesitan Atención':
        return {
          recencia: '30 días',
          frecuencia: '0.9 compras/mes',
          ticket: 'S/ 150',
          ltv: 'S/ 1,620'
        };
      case 'En Riesgo':
        return {
          recencia: '60 días',
          frecuencia: '0.3 compras/mes',
          ticket: 'S/ 112',
          ltv: 'S/ 806'
        };
      case 'Inactivos':
        return {
          recencia: '+90 días',
          frecuencia: '0 compras/mes',
          ticket: 'S/ 0',
          ltv: 'S/ 680'
        };
      default:
        return {
          recencia: '15 días',
          frecuencia: '1.8 compras/mes',
          ticket: 'S/ 195',
          ltv: 'S/ 4,680'
        };
    }
  };
  
  const segmentoActual = filtroSegmento !== 'todos' ? 
    segmentosRFM.find(s => s.nombre === filtroSegmento) : 
    { nombre: 'Todos los segmentos', valor: 100, clientes: 750, ventas: 'S/ 167,300', color: '#00E6E6' };
  
  const metricas = metricasSegmento(filtroSegmento !== 'todos' ? filtroSegmento : 'Todos');

  return (
    <div className="p-6 space-y-6">
      {/* Encabezado */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-cyber-text">Segmentación de Clientes</h1>
          <p className="text-cyber-text/70">Análisis basado en modelo RFM (Recencia, Frecuencia, Monto)</p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-2">
          <select 
            className="bg-cyber-detail/20 border border-cyber-cyan/30 rounded-md px-3 py-2 text-sm text-cyber-text"
            value={filtroRegion}
            onChange={(e) => setFiltroRegion(e.target.value)}
          >
            <option value="todas">Todas las regiones</option>
            <option value="lima">Lima</option>
            <option value="arequipa">Arequipa</option>
            <option value="trujillo">Trujillo</option>
            <option value="cusco">Cusco</option>
            <option value="piura">Piura</option>
          </select>
          <button className="flex items-center bg-cyber-detail text-cyber-text px-3 py-2 rounded-md text-sm hover:bg-cyber-detail/90">
            <Filter size={16} className="mr-1" />
            Filtros
          </button>
          <button className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded-md text-sm font-medium hover:bg-cyber-cyan/90 transition-colors">
            Exportar
          </button>
        </div>
      </div>
      
      {/* Resumen y selección de segmento */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Gráfico de distribución */}
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg lg:col-span-2">
          <h3 className="text-lg font-semibold text-cyber-text mb-2">Distribución de Segmentos</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={segmentosRFM}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="valor"
                  label={({ nombre, valor }) => `${nombre}: ${valor}%`}
                >
                  {segmentosRFM.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name, props) => [`${value}%`, 'Porcentaje']}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }}
                />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        {/* Selector de segmento y métricas */}
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
          <h3 className="text-lg font-semibold text-cyber-text mb-3">Filtrar por Segmento</h3>
          <select 
            className="w-full bg-cyber-detail/20 border border-cyber-cyan/30 rounded-md px-3 py-2 text-sm text-cyber-text mb-4"
            value={filtroSegmento}
            onChange={(e) => setFiltroSegmento(e.target.value)}
          >
            <option value="todos">Todos los segmentos</option>
            {segmentosRFM.map((segmento, index) => (
              <option key={index} value={segmento.nombre}>{segmento.nombre}</option>
            ))}
          </select>
          
          <div className="p-3 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10 mb-3">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-cyber-cyan">{segmentoActual?.nombre}</h4>
              <span className="text-xs bg-cyber-cyan/20 px-2 py-1 rounded text-cyber-cyan">
                {segmentoActual?.clientes} clientes
              </span>
            </div>
            <p className="text-sm text-cyber-text/80 mb-2">
              Ventas totales: <span className="font-medium text-cyber-text">{segmentoActual?.ventas}</span>
            </p>
            {filtroSegmento !== 'todos' && (
              <button className="text-xs text-cyber-cyan hover:underline">
                Ver lista completa de clientes →
              </button>
            )}
          </div>
          
          <h4 className="font-medium text-cyber-text mb-2">Métricas clave</h4>
          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 bg-cyber-detail/20 rounded border border-cyber-cyan/10">
              <div className="flex items-center text-cyber-cyan mb-1">
                <Clock size={14} className="mr-1" />
                <span className="text-xs">Recencia</span>
              </div>
              <p className="text-sm font-medium text-cyber-text">{metricas.recencia}</p>
            </div>
            <div className="p-2 bg-cyber-detail/20 rounded border border-cyber-cyan/10">
              <div className="flex items-center text-cyber-cyan mb-1">
                <ShoppingBag size={14} className="mr-1" />
                <span className="text-xs">Frecuencia</span>
              </div>
              <p className="text-sm font-medium text-cyber-text">{metricas.frecuencia}</p>
            </div>
            <div className="p-2 bg-cyber-detail/20 rounded border border-cyber-cyan/10">
              <div className="flex items-center text-cyber-cyan mb-1">
                <CreditCard size={14} className="mr-1" />
                <span className="text-xs">Ticket medio</span>
              </div>
              <p className="text-sm font-medium text-cyber-text">{metricas.ticket}</p>
            </div>
            <div className="p-2 bg-cyber-detail/20 rounded border border-cyber-cyan/10">
              <div className="flex items-center text-cyber-cyan mb-1">
                <DollarSign size={14} className="mr-1" />
                <span className="text-xs">Valor vida (LTV)</span>
              </div>
              <p className="text-sm font-medium text-cyber-text">{metricas.ltv}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Gráficos adicionales */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Demografía por edad */}
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-cyber-text">Demografía por Edad</h3>
            <Users size={18} className="text-cyber-cyan" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={demografiaEdad}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                <XAxis dataKey="grupo" stroke="#E6E6E6" />
                <YAxis stroke="#E6E6E6" tickFormatter={(value) => `${value}%`} />
                <Tooltip 
                  formatter={(value, name) => [`${value}%`, 'Porcentaje']}
                  labelFormatter={(label) => `Edad: ${label}`}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }}
                />
                <Bar dataKey="porcentaje" fill="#00E6E6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        {/* Frecuencia de compra */}
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-cyber-text">Frecuencia de Compra</h3>
            <ShoppingBag size={18} className="text-cyber-cyan" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={frecuenciaCompra}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                <XAxis dataKey="periodo" stroke="#E6E6E6" />
                <YAxis stroke="#E6E6E6" tickFormatter={(value) => `${value}%`} />
                <Tooltip 
                  formatter={(value, name) => [`${value}%`, 'Porcentaje']}
                  labelFormatter={(label) => `Frecuencia: ${label}`}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }}
                />
                <Bar dataKey="valor" fill="#4CAF50" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      
      {/* Tabla de clientes más valiosos */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-cyber-text">Top Clientes por Valor</h3>
          <div className="flex items-center space-x-2">
            <button className="text-cyber-text/70 hover:text-cyber-cyan">
              <Download size={18} />
            </button>
            <button className="text-cyber-text/70 hover:text-cyber-cyan">
              <Filter size={18} />
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-cyber-detail">
            <thead>
              <tr className="bg-cyber-detail/30">
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Cliente
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Ticket Promedio
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Compras
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Total Gastado
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Región
                </th>
              </tr>
            </thead>
            <tbody className="bg-cyber-dark/30 divide-y divide-cyber-detail/30">
              {clientesValiosos
                .filter(c => filtroRegion === 'todas' || c.region.toLowerCase() === filtroRegion.toLowerCase())
                .map((cliente, index) => (
                <tr key={index} className="hover:bg-cyber-detail/20">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm font-medium text-cyber-text">{cliente.nombre}</div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      cliente.tipo === 'Empresa' 
                        ? 'bg-blue-900/30 text-blue-400' 
                        : 'bg-purple-900/30 text-purple-400'
                    }`}>
                      {cliente.tipo}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-cyber-text">
                    {cliente.ticket}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-cyber-text">
                    {cliente.compras}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm font-medium text-cyber-text">{cliente.total}</div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm text-cyber-text flex items-center">
                      <Map size={14} className="mr-1 text-cyber-cyan/70" />
                      {cliente.region}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 text-right">
          <button className="text-sm text-cyber-cyan hover:underline">
            Ver todos los clientes →
          </button>
        </div>
      </div>
      
      {/* Recomendaciones IA */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex items-center text-cyber-cyan mb-4">
          <Users size={18} className="mr-2" />
          <h3 className="text-lg font-semibold text-cyber-text">Recomendaciones para tus Segmentos</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
            <h4 className="font-medium text-cyber-cyan mb-2">Para clientes "Campeones"</h4>
            <ul className="space-y-2 text-sm text-cyber-text">
              <li className="flex items-start">
                <span className="inline-block h-5 w-5 rounded-full bg-cyber-cyan/20 text-cyber-cyan flex items-center justify-center text-xs mr-2">1</span>
                <span>Implementar programa de embajadores de marca con incentivos especiales</span>
              </li>
              <li className="flex items-start">
                <span className="inline-block h-5 w-5 rounded-full bg-cyber-cyan/20 text-cyber-cyan flex items-center justify-center text-xs mr-2">2</span>
                <span>Ofrecer acceso prioritario a nuevos productos/servicios</span>
              </li>
              <li className="flex items-start">
                <span className="inline-block h-5 w-5 rounded-full bg-cyber-cyan/20 text-cyber-cyan flex items-center justify-center text-xs mr-2">3</span>
                <span>Desarrollar programa de referidos con alta recompensa</span>
              </li>
            </ul>
          </div>
          <div className="p-4 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
            <h4 className="font-medium text-cyber-cyan mb-2">Para clientes "En Riesgo"</h4>
            <ul className="space-y-2 text-sm text-cyber-text">
              <li className="flex items-start">
                <span className="inline-block h-5 w-5 rounded-full bg-cyber-cyan/20 text-cyber-cyan flex items-center justify-center text-xs mr-2">1</span>
                <span>Enviar campaña de reactivación con descuento del 25% en próxima compra</span>
              </li>
              <li className="flex items-start">
                <span className="inline-block h-5 w-5 rounded-full bg-cyber-cyan/20 text-cyber-cyan flex items-center justify-center text-xs mr-2">2</span>
                <span>Realizar encuesta de satisfacción para identificar problemas</span>
              </li>
              <li className="flex items-start">
                <span className="inline-block h-5 w-5 rounded-full bg-cyber-cyan/20 text-cyber-cyan flex items-center justify-center text-xs mr-2">3</span>
                <span>Asignar un asesor personalizado para seguimiento</span>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-4 text-right">
          <button className="text-sm bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors">
            Generar plan de acción completo
          </button>
        </div>
      </div>
    </div>
  );
};

export default SegmentacionClientes;