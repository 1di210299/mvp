// src/components/DashboardVentas.tsx
import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  ShoppingBag, 
  Calendar, 
  ArrowUp, 
  ArrowDown, 
  DollarSign,
  Download,
  Filter
} from 'lucide-react';
import VentasChart from './VentasChart';

const DashboardVentas = () => {
  const [periodoSeleccionado, setPeriodoSeleccionado] = useState('mes');

  // Métricas principales
  const metricas = [
    { 
      titulo: 'Ventas Totales', 
      valor: 'S/ 124,580', 
      cambio: '+15.8%', 
      icono: <DollarSign size={20} />, 
      positivo: true,
      periodo: 'vs. mes anterior'
    },
    { 
      titulo: 'Ticket Promedio', 
      valor: 'S/ 105.40', 
      cambio: '+7.2%', 
      icono: <ShoppingBag size={20} />, 
      positivo: true,
      periodo: 'vs. mes anterior'
    },
    { 
      titulo: 'Clientes Activos', 
      valor: '325', 
      cambio: '+12.3%', 
      icono: <Users size={20} />, 
      positivo: true,
      periodo: 'vs. mes anterior'
    },
    { 
      titulo: 'Tasa de Conversión', 
      valor: '24.8%', 
      cambio: '-2.1%', 
      icono: <TrendingUp size={20} />, 
      positivo: false,
      periodo: 'vs. mes anterior'
    }
  ];

  // Campañas destacadas
  const campanias = [
    { nombre: 'Fiestas Patrias', fecha: '28 Jul', monto: 'S/ 32,600', incremento: '+18.9%' },
    { nombre: 'Navidad', fecha: '25 Dic', monto: 'S/ 48,900', incremento: '+24.8%' },
    { nombre: 'Cyber Days', fecha: '15 Nov', monto: 'S/ 23,400', incremento: '+12.7%' },
  ];

  // Ventas por región
  const regionesPrincipales = [
    { region: 'Lima', valor: 42, ventas: 'S/ 68,500' },
    { region: 'Arequipa', valor: 18, ventas: 'S/ 28,400' },
    { region: 'Trujillo', valor: 14, ventas: 'S/ 22,300' },
    { region: 'Otras', valor: 26, ventas: 'S/ 42,300' },
  ];

  // Insights generados por IA
  const insights = [
    {
      titulo: 'Oportunidad detectada',
      texto: 'Tus clientes de Lima Norte tienen un 28% más de ticket promedio que Lima Sur. Considera campañas específicas para Lima Sur.',
      tipo: 'oportunidad'
    },
    {
      titulo: 'Riesgo identificado',
      texto: 'El 18% de tus clientes frecuentes no han comprado en los últimos 30 días, mostrando signos de deserción.',
      tipo: 'riesgo'
    },
    {
      titulo: 'Proyección',
      texto: 'Con base en patrones históricos, se espera un incremento del 22% en ventas para el siguiente evento Cyber Days (15 Nov).',
      tipo: 'proyeccion'
    }
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Encabezado */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-cyber-text">Dashboard de Ventas</h1>
          <p className="text-cyber-text/70">Análisis actualizado al 07 de marzo, 2025</p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-2">
          <select 
            className="bg-cyber-detail/20 border border-cyber-cyan/30 rounded-md px-3 py-2 text-sm text-cyber-text focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
            value={periodoSeleccionado}
            onChange={(e) => setPeriodoSeleccionado(e.target.value)}
          >
            <option value="mes">Últimos 30 días</option>
            <option value="trimestre">Último trimestre</option>
            <option value="año">Este año</option>
            <option value="personalizado">Personalizado</option>
          </select>
          <button className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded-md text-sm font-medium hover:bg-cyber-cyan/90 transition-colors flex items-center">
            <Download size={16} className="mr-1" />
            Exportar
          </button>
        </div>
      </div>

      {/* Tarjetas de métricas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
                  <span className="text-cyber-text/50 text-xs ml-2">{metrica.periodo}</span>
                </div>
              </div>
              <div className="p-2 rounded-lg bg-cyber-cyan/10 text-cyber-cyan">
                {metrica.icono}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Sección de Análisis de Ventas */}
      <div className="h-[500px]">
        <VentasChart />
      </div>

      {/* Sección inferior: Campañas y Regiones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Campañas destacadas */}
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-cyber-cyan/20 shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-cyber-text">Campañas Destacadas</h3>
            <div className="p-2 rounded-full bg-cyber-cyan/10">
              <Calendar size={18} className="text-cyber-cyan" />
            </div>
          </div>
          <div className="space-y-5">
            {campanias.map((campania, index) => (
              <div key={index} className="flex justify-between items-center border-b border-cyber-detail/30 pb-4 last:border-0 last:pb-0">
                <div>
                  <h4 className="font-medium text-cyber-text">{campania.nombre}</h4>
                  <p className="text-xs text-cyber-text/60">{campania.fecha}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-cyber-text">{campania.monto}</p>
                  <p className="text-xs text-green-400">{campania.incremento}</p>
                </div>
              </div>
            ))}
          </div>
          <button className="mt-5 w-full text-center text-cyber-cyan text-sm hover:text-cyber-cyan/80 transition-colors font-medium flex items-center justify-center">
            <span>Ver todas las campañas</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Ventas por región */}
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-cyber-cyan/20 shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-cyber-text">Ventas por Región</h3>
            <div className="p-2 rounded-full bg-cyber-cyan/10">
              <BarChart3 size={18} className="text-cyber-cyan" />
            </div>
          </div>
          <div className="space-y-5">
            {regionesPrincipales.map((region, index) => (
              <div key={index} className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-medium text-cyber-text">{region.region}</h4>
                  <span className="text-sm text-cyber-text">{region.ventas}</span>
                </div>
                <div className="w-full bg-cyber-detail/30 h-2 rounded-full overflow-hidden">
                  <div 
                    className="bg-cyber-cyan h-2 rounded-full" 
                    style={{ width: `${region.valor}%` }}
                  ></div>
                </div>
                <p className="text-xs text-cyber-text/60">{region.valor}% del total</p>
              </div>
            ))}
          </div>
          <button className="mt-5 w-full text-center text-cyber-cyan text-sm hover:text-cyber-cyan/80 transition-colors font-medium flex items-center justify-center">
            <span>Ver mapa detallado</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      {/* Insights IA */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-cyber-text flex items-center">
            <div className="p-2 rounded-full bg-cyber-cyan/10 mr-2">
              <TrendingUp size={16} className="text-cyber-cyan" />
            </div>
            Insights IA
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {insights.map((insight, index) => (
            <div key={index} className="p-4 bg-cyber-detail/20 rounded-lg border border-cyber-cyan/10">
              <h4 className="font-medium text-cyber-cyan mb-2">{insight.titulo}</h4>
              <p className="text-sm text-cyber-text">{insight.texto}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardVentas;