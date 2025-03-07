// src/pages/PrediccionesVentas.tsx
import React, { useState } from 'react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, 
  ResponsiveContainer, CartesianGrid, XAxis, YAxis, 
  Tooltip, Legend, ReferenceLine 
} from 'recharts';
import { 
  TrendingUp, Calendar, AlertTriangle, Download, 
  ArrowUp, ArrowDown, BarChart2, Settings, Filter
} from 'lucide-react';

const PrediccionesVentas = () => {
  const [periodoProyeccion, setPeriodoProyeccion] = useState<'30d' | '90d' | '6m' | '12m'>('90d');
  const [confianzaModelo, setConfianzaModelo] = useState<number>(87);
  const [modeloSeleccionado, setModeloSeleccionado] = useState<string>('ANNEX-TS-87');
  
  // Datos históricos vs predicción - ventas totales
  const datosVentasTotales = [
    // Datos históricos
    { mes: 'Jul', ventas: 23200, prediccion: null, actual: true },
    { mes: 'Ago', ventas: 28200, prediccion: null, actual: true },
    { mes: 'Sep', ventas: 32400, prediccion: null, actual: true },
    { mes: 'Oct', ventas: 35300, prediccion: null, actual: true },
    { mes: 'Nov', ventas: 42100, prediccion: null, actual: true },
    { mes: 'Dic', ventas: 48500, prediccion: null, actual: true },
    { mes: 'Ene', ventas: 39600, prediccion: null, actual: true },
    { mes: 'Feb', ventas: 42800, prediccion: null, actual: true },
    { mes: 'Mar', ventas: 45500, prediccion: null, actual: false, actualEstimado: 45500 },
    // Predicciones
    { mes: 'Abr', ventas: null, prediccion: 48900, actual: false, limiteInferior: 45200, limiteSuperior: 52600 },
    { mes: 'May', ventas: null, prediccion: 54200, actual: false, limiteInferior: 49800, limiteSuperior: 58600 },
    { mes: 'Jun', ventas: null, prediccion: 52500, actual: false, limiteInferior: 47700, limiteSuperior: 57300 },
    { mes: 'Jul', ventas: null, prediccion: 58800, actual: false, limiteInferior: 53100, limiteSuperior: 64500 },
    { mes: 'Ago', ventas: null, prediccion: 65400, actual: false, limiteInferior: 58900, limiteSuperior: 71900 },
    { mes: 'Sep', ventas: null, prediccion: 72000, actual: false, limiteInferior: 64800, limiteSuperior: 79200 },
  ];
  
  // Datos históricos vs predicción - ticket promedio
  const datosTicketPromedio = [
    // Datos históricos
    { mes: 'Jul', ticket: 108, prediccion: null, actual: true },
    { mes: 'Ago', ticket: 115, prediccion: null, actual: true },
    { mes: 'Sep', ticket: 120, prediccion: null, actual: true },
    { mes: 'Oct', ticket: 125, prediccion: null, actual: true },
    { mes: 'Nov', ticket: 130, prediccion: null, actual: true },
    { mes: 'Dic', ticket: 135, prediccion: null, actual: true },
    { mes: 'Ene', ticket: 128, prediccion: null, actual: true },
    { mes: 'Feb', ticket: 132, prediccion: null, actual: true },
    { mes: 'Mar', ticket: 135, prediccion: null, actual: false, actualEstimado: 135 },
    // Predicciones
    { mes: 'Abr', ticket: null, prediccion: 138, actual: false, limiteInferior: 132, limiteSuperior: 144 },
    { mes: 'May', ticket: null, prediccion: 142, actual: false, limiteInferior: 135, limiteSuperior: 149 },
    { mes: 'Jun', ticket: null, prediccion: 144, actual: false, limiteInferior: 137, limiteSuperior: 151 },
    { mes: 'Jul', ticket: null, prediccion: 147, actual: false, limiteInferior: 140, limiteSuperior: 154 },
    { mes: 'Ago', ticket: null, prediccion: 152, actual: false, limiteInferior: 145, limiteSuperior: 159 },
    { mes: 'Sep', ticket: null, prediccion: 156, actual: false, limiteInferior: 148, limiteSuperior: 164 },
  ];
  
  // Predicción por categoría para próximos 3 meses
  const prediccionPorCategoria = [
    { 
      categoria: 'Tecnología', 
      actual: 18500, 
      prediction: 24200,
      crecimiento: 30.8,
      confianza: 92
    },
    { 
      categoria: 'Moda', 
      actual: 12400, 
      prediction: 15800,
      crecimiento: 27.4,
      confianza: 88
    },
    { 
      categoria: 'Hogar', 
      actual: 9300, 
      prediction: 10700,
      crecimiento: 15.1,
      confianza: 86
    },
    { 
      categoria: 'Alimentos', 
      actual: 7600, 
      prediction: 8100,
      crecimiento: 6.6,
      confianza: 90
    },
    { 
      categoria: 'Otros', 
      actual: 4200, 
      prediction: 4900,
      crecimiento: 16.7,
      confianza: 82
    }
  ];
  
  // Predicción de ventas por región
  const prediccionPorRegion = [
    { region: 'Lima', actual: 28500, prediction: 33400, cambio: 17.2 },
    { region: 'Arequipa', actual: 12400, prediction: 16800, cambio: 35.5 },
    { region: 'Trujillo', actual: 9700, prediction: 11900, cambio: 22.7 },
    { region: 'Cusco', actual: 6200, prediction: 8100, cambio: 30.6 },
    { region: 'Piura', actual: 5100, prediction: 6400, cambio: 25.5 },
    { region: 'Chiclayo', actual: 4300, prediction: 5200, cambio: 20.9 },
    { region: 'Otros', actual: 1800, prediction: 2400, cambio: 33.3 },
  ];
  
  // Lista de factores que influyen en las predicciones
  const factoresInfluencia = [
    { 
      factor: 'Fiestas Patrias', 
      impacto: 'Alto', 
      fechaInicio: '15 Jul', 
      fechaFin: '05 Ago',
      descripcion: 'El periodo de Fiestas Patrias históricamente aumenta las ventas en un 32%.'
    },
    { 
      factor: 'Campaña Escolar', 
      impacto: 'Medio', 
      fechaInicio: '15 Feb', 
      fechaFin: '15 Mar',
      descripcion: 'La temporada escolar incrementa ventas de tecnología y moda en 22%.'
    },
    { 
      factor: 'Día de la Madre', 
      impacto: 'Alto', 
      fechaInicio: '01 May', 
      fechaFin: '15 May',
      descripcion: 'Esta campaña suele generar un aumento de 28% en categorías de moda y hogar.'
    },
    { 
      factor: 'Navidad', 
      impacto: 'Muy Alto', 
      fechaInicio: '15 Nov', 
      fechaFin: '31 Dic',
      descripcion: 'El periodo navideño genera 43% más ventas que el promedio anual.'
    },
    { 
      factor: 'Cyber Days', 
      impacto: 'Alto', 
      fechaInicio: '14 Nov', 
      fechaFin: '16 Nov',
      descripcion: 'Los Cyber Days pueden representar hasta 2.5x las ventas de un día normal.'
    }
  ];

  // Métricas de predicción
  const metricas = [
    { 
      titulo: 'Ventas proyectadas (90 días)', 
      valor: 'S/ 155,500', 
      cambio: '+27.4%', 
      icono: <TrendingUp size={20} />, 
      positivo: true 
    },
    { 
      titulo: 'Ticket promedio proyectado', 
      valor: 'S/ 142', 
      cambio: '+5.2%', 
      icono: <BarChart2 size={20} />, 
      positivo: true 
    },
    { 
      titulo: 'Precisión del modelo', 
      valor: `${confianzaModelo}%`, 
      cambio: '+1.5%', 
      icono: <Settings size={20} />, 
      positivo: true 
    },
  ];

  // Filtrar datos según periodo seleccionado
  const filtrarDatosPorPeriodo = (datos: any[]) => {
    const fechaActual = 8; // Índice correspondiente a "Mar" (último mes real)
    
    let periodoMeses;
    switch (periodoProyeccion) {
      case '30d': periodoMeses = 1; break;
      case '90d': periodoMeses = 3; break;
      case '6m': periodoMeses = 6; break;
      case '12m': periodoMeses = 12; break;
      default: periodoMeses = 3;
    }
    
    // Mostrar 6 meses de historia + la predicción según el periodo seleccionado
    const inicioHistoria = Math.max(0, fechaActual - 5);
    const finPrediccion = Math.min(datos.length - 1, fechaActual + periodoMeses);
    
    return datos.slice(inicioHistoria, finPrediccion + 1);
  };
  
  const datosFiltradosVentas = filtrarDatosPorPeriodo(datosVentasTotales);
  const datosFiltradosTicket = filtrarDatosPorPeriodo(datosTicketPromedio);
  
  // Formatear valores de soles peruanos
  const formatoSoles = (valor: number) => `S/ ${valor?.toLocaleString('es-PE') || 0}`;

  return (
    <div className="p-6 space-y-6">
      {/* Encabezado */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-cyber-text">Predicciones de Ventas</h1>
          <p className="text-cyber-text/70">Proyecciones basadas en IA y análisis de tendencias históricas</p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-2">
          <select 
            className="bg-cyber-detail/20 border border-cyber-cyan/30 rounded-md px-3 py-2 text-sm text-cyber-text"
            value={periodoProyeccion}
            onChange={(e) => setPeriodoProyeccion(e.target.value as any)}
          >
            <option value="30d">Próximos 30 días</option>
            <option value="90d">Próximos 90 días</option>
            <option value="6m">Próximos 6 meses</option>
            <option value="12m">Próximos 12 meses</option>
          </select>
          <select 
            className="bg-cyber-detail/20 border border-cyber-cyan/30 rounded-md px-3 py-2 text-sm text-cyber-text"
            value={modeloSeleccionado}
            onChange={(e) => {
              setModeloSeleccionado(e.target.value);
              // Simular cambio en la confianza del modelo según el modelo seleccionado
              if (e.target.value === 'ANNEX-TS-87') setConfianzaModelo(87);
              else if (e.target.value === 'ANNEX-ML-92') setConfianzaModelo(92);
              else setConfianzaModelo(84);
            }}
          >
            <option value="ANNEX-TS-87">ANNEX Time Series (87%)</option>
            <option value="ANNEX-ML-92">ANNEX ML Avanzado (92%)</option>
            <option value="ANNEX-ES-84">ANNEX Estacional (84%)</option>
          </select>
          <button className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded-md text-sm font-medium hover:bg-cyber-cyan/90 transition-colors">
            Exportar
          </button>
        </div>
      </div>
      
      {/* Tarjetas de métricas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {metricas.map((metrica, index) => (
          <div key={index} className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-cyber-text/60 text-sm">{metrica.titulo}</p>
                <h3 className="text-2xl font-bold text-cyber-text mt-1">{metrica.valor}</h3>
                <div className="flex items-center mt-2">
                  <span className={`inline-flex items-center ${metrica.positivo ? 'text-green-400' : 'text-red-400'}`}>
                    {metrica.positivo ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
                    <span className="ml-1">{metrica.cambio}</span>
                  </span>
                  <span className="text-cyber-text/50 text-xs ml-2">vs. último periodo</span>
                </div>
              </div>
              <div className="p-2 rounded-lg bg-cyber-cyan/10 text-cyber-cyan">
                {metrica.icono}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Gráficos de predicción */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico de predicción de ventas totales */}
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-cyber-text">Predicción de Ventas Totales</h3>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-cyber-text/70 bg-cyber-detail/30 px-2 py-1 rounded">
                {datosFiltradosVentas.filter(d => !d.actual).length} meses proyectados
              </span>
              <button className="text-cyber-text/70 hover:text-cyber-cyan">
                <Settings size={16} />
              </button>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={datosFiltradosVentas}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                <XAxis dataKey="mes" stroke="#E6E6E6" />
                <YAxis stroke="#E6E6E6" tickFormatter={(value) => `S/ ${value/1000}k`} />
                <Tooltip 
                  formatter={(value, name) => {
                    if (name === "ventas") return [formatoSoles(value as number), "Ventas reales"];
                    if (name === "prediccion") return [formatoSoles(value as number), "Ventas proyectadas"];
                    return [value, name];
                  }}
                  labelFormatter={(label) => `Mes: ${label}`}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }}
                />
                <Legend />
                <ReferenceLine x="Mar" stroke="#00E6E6" strokeDasharray="3 3" label={{ value: 'Hoy', position: 'insideTop', fill: '#00E6E6' }} />
                
                {/* Área para intervalo de confianza */}
                <Area 
                  type="monotone" 
                  dataKey="limiteInferior" 
                  stackId="1"
                  stroke="none" 
                  fill="#00E6E6" 
                  fillOpacity={0.1} 
                  name="Límite inferior"
                />
                <Area 
                  type="monotone" 
                  dataKey="limiteSuperior" 
                  stackId="2" 
                  stroke="none"
                  fill="#00E6E6" 
                  fillOpacity={0.05}
                  name="Límite superior" 
                />
                
                {/* Líneas de datos reales y predicción */}
                <Line 
                  type="monotone" 
                  dataKey="ventas" 
                  stroke="#00E6E6" 
                  strokeWidth={2}
                  dot={{ r: 5, strokeWidth: 1 }} 
                  activeDot={{ r: 7 }}
                  name="ventas"
                />
                <Line 
                  type="monotone" 
                  dataKey="prediccion" 
                  stroke="#4CAF50" 
                  strokeDasharray="5 5"
                  strokeWidth={2}
                  dot={{ r: 5, strokeWidth: 1 }} 
                  activeDot={{ r: 7 }}
                  name="prediccion"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-between items-center mt-3 text-xs text-cyber-text/70">
            <div className="flex items-center">
              <span className="inline-block h-3 w-3 rounded-full bg-cyber-cyan mr-1"></span>
              <span>Ventas reales</span>
            </div>
            <div className="flex items-center">
              <span className="inline-block h-3 w-3 rounded-full bg-green-500 mr-1"></span>
              <span>Predicción</span>
            </div>
            <div className="flex items-center">
              <span className="inline-block h-3 w-3 rounded-full bg-cyber-cyan/30 mr-1"></span>
              <span>Intervalo de confianza ({confianzaModelo}%)</span>
            </div>
          </div>
        </div>
        
        {/* Gráfico de predicción de ticket promedio */}
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-cyber-text">Predicción de Ticket Promedio</h3>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-cyber-text/70 bg-cyber-detail/30 px-2 py-1 rounded">
                {datosFiltradosTicket.filter(d => !d.actual).length} meses proyectados
              </span>
              <button className="text-cyber-text/70 hover:text-cyber-cyan">
                <Settings size={16} />
              </button>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={datosFiltradosTicket}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                <XAxis dataKey="mes" stroke="#E6E6E6" />
                <YAxis stroke="#E6E6E6" domain={['dataMin - 10', 'dataMax + 10']} tickFormatter={(value) => `S/ ${value}`} />
                <Tooltip 
                  formatter={(value, name) => {
                    if (name === "ticket") return [`S/ ${value}`, "Ticket real"];
                    if (name === "prediccion") return [`S/ ${value}`, "Ticket proyectado"];
                    return [value, name];
                  }}
                  labelFormatter={(label) => `Mes: ${label}`}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }}
                />
                <Legend />
                <ReferenceLine x="Mar" stroke="#00E6E6" strokeDasharray="3 3" label={{ value: 'Hoy', position: 'insideTop', fill: '#00E6E6' }} />
                
                {/* Área para intervalo de confianza */}
                <Area 
                  type="monotone" 
                  dataKey="limiteInferior" 
                  fill="#00E6E6" 
                  fillOpacity={0.1}
                  stroke="none" 
                  name="Límite inferior"
                />
                <Area 
                  type="monotone" 
                  dataKey="limiteSuperior" 
                  fill="#00E6E6" 
                  fillOpacity={0.05}
                  stroke="none" 
                  name="Límite superior"
                />
                
                {/* Líneas de datos reales y predicción */}
                <Line 
                  type="monotone" 
                  dataKey="ticket" 
                  stroke="#00E6E6" 
                  strokeWidth={2}
                  dot={{ r: 5, strokeWidth: 1 }} 
                  activeDot={{ r: 7 }}
                  name="ticket"
                />
                <Line 
                  type="monotone" 
                  dataKey="prediccion" 
                  stroke="#4CAF50" 
                  strokeDasharray="5 5"
                  strokeWidth={2}
                  dot={{ r: 5, strokeWidth: 1 }} 
                  activeDot={{ r: 7 }}
                  name="prediccion"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-between items-center mt-3 text-xs text-cyber-text/70">
            <div className="flex items-center">
              <span className="inline-block h-3 w-3 rounded-full bg-cyber-cyan mr-1"></span>
              <span>Ticket real</span>
            </div>
            <div className="flex items-center">
              <span className="inline-block h-3 w-3 rounded-full bg-green-500 mr-1"></span>
              <span>Predicción</span>
            </div>
            <div className="flex items-center">
              <span className="inline-block h-3 w-3 rounded-full bg-cyber-cyan/30 mr-1"></span>
              <span>Intervalo de confianza ({confianzaModelo}%)</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Predicción por categorías */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-cyber-text">Predicción por Categoría (90 días)</h3>
          <div className="flex space-x-2">
            <button className="flex items-center bg-cyber-detail text-cyber-text px-3 py-1 rounded text-sm hover:bg-cyber-detail/90">
              <Filter size={16} className="mr-1" />
              Filtros
            </button>
            <button className="flex items-center bg-cyber-detail text-cyber-text px-3 py-1 rounded text-sm hover:bg-cyber-detail/90">
              <Download size={16} className="mr-1" />
              Exportar
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Gráfico de barras */}
          <div className="lg:col-span-2 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={prediccionPorCategoria}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" opacity={0.3} />
                <XAxis type="number" stroke="#E6E6E6" tickFormatter={(value) => `S/ ${value/1000}k`} />
                <YAxis dataKey="categoria" type="category" stroke="#E6E6E6" width={80} />
                <Tooltip
                  formatter={(value, name) => {
                    if (name === "actual") return [formatoSoles(value as number), "Ventas actuales"];
                    if (name === "prediction") return [formatoSoles(value as number), "Ventas proyectadas"];
                    return [value, name];
                  }}
                  contentStyle={{ backgroundColor: '#0A192F', borderColor: '#00E6E6', color: '#E6E6E6' }}
                />
                <Legend />
                <Bar dataKey="actual" name="Actual" fill="#00E6E6" barSize={20} />
                <Bar dataKey="prediction" name="Predicción" fill="#4CAF50" barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          
          {/* Tabla de crecimiento */}
          <div className="overflow-hidden">
            <div className="rounded-t bg-cyber-detail/30 px-4 py-2 border-b border-cyber-detail">
              <h4 className="font-medium text-cyber-text">Crecimiento Proyectado</h4>
            </div>
            <div className="overflow-y-auto max-h-60">
              <table className="min-w-full divide-y divide-cyber-detail/30">
                <thead className="bg-cyber-detail/20">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                      Categoría
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                      Crecimiento
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                      Confianza
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cyber-detail/30">
                  {prediccionPorCategoria.map((item, index) => (
                    <tr key={index} className="hover:bg-cyber-detail/10">
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-cyber-text">
                        {item.categoria}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-right">
                        <span className={`font-medium ${item.crecimiento > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {item.crecimiento > 0 ? '+' : ''}{item.crecimiento.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-right">
                        <div className="flex items-center justify-end">
                          <div className="w-16 bg-cyber-detail/50 h-1.5 rounded-full mr-2">
                            <div 
                              className={`h-1.5 rounded-full ${
                                item.confianza > 90 ? 'bg-green-500' : item.confianza > 85 ? 'bg-cyber-cyan' : 'bg-yellow-500'
                              }`}
                              style={{ width: `${item.confianza}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-cyber-text/70">{item.confianza}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      
      {/* Factores de influencia */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex items-center text-cyber-cyan mb-4">
          <Calendar size={18} className="mr-2" />
          <h3 className="text-lg font-semibold text-cyber-text">Factores de Influencia Estacional</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-cyber-detail">
            <thead className="bg-cyber-detail/30">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Factor
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Impacto
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Fecha Inicio
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Fecha Fin
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Detalles
                </th>
              </tr>
            </thead>
            <tbody className="bg-transparent divide-y divide-cyber-detail/30">
              {factoresInfluencia.map((factor, index) => (
                <tr key={index} className="hover:bg-cyber-detail/20">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm font-medium text-cyber-text">{factor.factor}</div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      factor.impacto === 'Muy Alto' 
                        ? 'bg-green-900/30 text-green-400' 
                        : factor.impacto === 'Alto'
                        ? 'bg-blue-900/30 text-blue-400'
                        : factor.impacto === 'Medio'
                        ? 'bg-yellow-900/30 text-yellow-400'
                        : 'bg-gray-800 text-gray-400'
                    }`}>
                      {factor.impacto}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-cyber-text">
                    {factor.fechaInicio}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-cyber-text">
                    {factor.fechaFin}
                  </td>
                  <td className="px-4 py-3 text-sm text-cyber-text">
                    {factor.descripcion}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Recomendaciones IA */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex items-center mb-4">
          <TrendingUp size={18} className="text-cyber-cyan mr-2" />
          <h3 className="text-lg font-semibold text-cyber-text">Recomendaciones Basadas en Predicciones</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
            <h4 className="font-medium text-cyber-cyan mb-2">Inventario</h4>
            <p className="text-sm text-cyber-text mb-3">
              Aumenta stock de la categoría Tecnología en un 30% antes del 15 de junio para prepararte para el incremento de Fiestas Patrias.
            </p>
            <div className="flex justify-between items-center text-xs">
              <span className="text-cyber-text/70">Confianza: 92%</span>
              <button className="text-cyber-cyan hover:underline">Aplicar</button>
            </div>
          </div>
          <div className="p-4 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
            <h4 className="font-medium text-cyber-cyan mb-2">Expansión Regional</h4>
            <p className="text-sm text-cyber-text mb-3">
              Considera ampliar operaciones en Arequipa, donde se proyecta un crecimiento de 35.5% en los próximos 90 días.
            </p>
            <div className="flex justify-between items-center text-xs">
              <span className="text-cyber-text/70">Confianza: 86%</span>
              <button className="text-cyber-cyan hover:underline">Ver plan</button>
            </div>
          </div>
          <div className="p-4 bg-cyber-detail/30 rounded-lg border border-green-500/20">
            <div className="flex items-center mb-2">
              <AlertTriangle size={16} className="text-yellow-500 mr-1" />
              <h4 className="font-medium text-cyber-cyan">Riesgo detectado</h4>
            </div>
            <p className="text-sm text-cyber-text mb-3">
              La categoría Alimentos muestra el menor crecimiento proyectado (6.6%). Considera promociones especiales para impulsar ventas.
            </p>
            <div className="flex justify-between items-center text-xs">
              <span className="text-cyber-text/70">Prioridad: Media</span>
              <button className="text-cyber-cyan hover:underline">Mitigar</button>
            </div>
          </div>
        </div>
        <div className="mt-4 text-right">
          <button className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded text-sm font-medium hover:bg-cyber-cyan/90 transition-colors">
            Generar plan de acción completo
          </button>
        </div>
      </div>
    </div>
  );
};

export default PrediccionesVentas;