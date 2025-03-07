// src/pages/ReportesVentas.tsx
import React, { useState } from 'react';
import { 
  FileText, Download, Calendar, Filter, Eye, PieChart,
  FilePlus, BarChart, Share2, Star, AlertTriangle, Clock
} from 'lucide-react';

interface ReporteProps {
  id: string;
  titulo: string;
  descripcion: string;
  fecha: string;
  tipo: 'ventas' | 'inventario' | 'clientes' | 'marketing' | 'fiscal';
  formato: 'pdf' | 'excel' | 'csv';
  programado: boolean;
  destacado: boolean;
  icono: React.ReactNode;
}

const ReportesVentas = () => {
  const [filtroTipo, setFiltroTipo] = useState<string>('todos');
  const [filtroFormato, setFiltroFormato] = useState<string>('todos');
  const [ordenarPor, setOrdenarPor] = useState<string>('fecha');
  const [busqueda, setBusqueda] = useState<string>('');
  
  // Lista de plantillas predefinidas
  const plantillasReportes = [
    {
      id: 'venta-mensual',
      titulo: 'Reporte Mensual de Ventas',
      descripcion: 'Ventas totales, por producto, por vendedor y comparativo con meses anteriores',
      categoria: 'ventas',
      destacado: true,
      icono: <BarChart size={32} />
    },
    {
      id: 'venta-producto',
      titulo: 'Ventas por Producto',
      descripcion: 'Análisis detallado de ventas por producto, categoría y variación temporal',
      categoria: 'ventas',
      destacado: false,
      icono: <BarChart size={32} />
    },
    {
      id: 'venta-client',
      titulo: 'Análisis por Cliente',
      descripcion: 'Compras totales, frecuencia y ticket promedio por cliente',
      categoria: 'clientes',
      destacado: false,
      icono: <PieChart size={32} />
    },
    {
      id: 'igv-mensual',
      titulo: 'Declaración IGV Mensual',
      descripcion: 'Reporte listo para declaración de IGV con resumen por tipo de comprobante',
      categoria: 'fiscal',
      destacado: true,
      icono: <FileText size={32} />
    },
    {
      id: 'stock-critico',
      titulo: 'Alerta de Stock Crítico',
      descripcion: 'Productos con nivel de inventario por debajo del mínimo recomendado',
      categoria: 'inventario',
      destacado: false,
      icono: <AlertTriangle size={32} />
    },
    {
      id: 'marketing-roi',
      titulo: 'ROI de Campañas de Marketing',
      descripcion: 'Análisis de retorno de inversión por campaña de marketing',
      categoria: 'marketing',
      destacado: false,
      icono: <Star size={32} />
    },
  ];
  
  // Lista de reportes generados/programados
  const reportes: ReporteProps[] = [
    {
      id: 'rep-001',
      titulo: 'Ventas Mensuales Febrero 2025',
      descripcion: 'Reporte detallado de ventas del mes de Febrero 2025 por región, categoría y vendedor',
      fecha: '01/03/2025',
      tipo: 'ventas',
      formato: 'pdf',
      programado: false,
      destacado: true,
      icono: <BarChart size={20} className="text-cyber-cyan" />
    },
    {
      id: 'rep-002',
      titulo: 'Proyección Q2 2025',
      descripcion: 'Estimación de ventas para el segundo trimestre basada en datos históricos y tendencias',
      fecha: '15/02/2025',
      tipo: 'ventas',
      formato: 'excel',
      programado: false,
      destacado: true,
      icono: <BarChart size={20} className="text-green-400" />
    },
    {
      id: 'rep-003',
      titulo: 'Segmentación Clientes Enero',
      descripcion: 'Análisis de segmentación RFM (Recencia, Frecuencia, Monto) actualizado',
      fecha: '05/02/2025',
      tipo: 'clientes',
      formato: 'pdf',
      programado: false,
      destacado: false,
      icono: <PieChart size={20} className="text-blue-400" />
    },
    {
      id: 'rep-004',
      titulo: 'Declaración IGV Febrero 2025',
      descripcion: 'Informe para presentación de IGV mensual a SUNAT con detalle de facturas y boletas',
      fecha: '28/02/2025',
      tipo: 'fiscal',
      formato: 'excel',
      programado: true,
      destacado: false,
      icono: <FileText size={20} className="text-yellow-400" />
    },
    {
      id: 'rep-005',
      titulo: 'Reporte de Inventario',
      descripcion: 'Estado actual del inventario con productos de baja rotación y stock crítico',
      fecha: '25/02/2025',
      tipo: 'inventario',
      formato: 'excel',
      programado: false,
      destacado: false,
      icono: <BarChart size={20} className="text-cyber-cyan" />
    },
    {
      id: 'rep-006',
      titulo: 'Análisis Campaña Día de la Madre',
      descripcion: 'Resultados de la campaña con métricas de conversión y ROI por canal',
      fecha: '20/02/2025',
      tipo: 'marketing',
      formato: 'pdf',
      programado: false,
      destacado: false,
      icono: <Star size={20} className="text-purple-400" />
    },
    {
      id: 'rep-007',
      titulo: 'Ventas Diarias Marzo 2025',
      descripcion: 'Actualización automática diaria de ventas con comparativo vs. objetivo',
      fecha: 'Diario',
      tipo: 'ventas',
      formato: 'csv',
      programado: true,
      destacado: false,
      icono: <Clock size={20} className="text-green-400" />
    },
    {
      id: 'rep-008',
      titulo: 'Exportación de Ventas Ene-Feb 2025',
      descripcion: 'Datos crudos de ventas para el primer bimestre del año en formato CSV',
      fecha: '01/03/2025',
      tipo: 'ventas',
      formato: 'csv',
      programado: false,
      destacado: false,
      icono: <BarChart size={20} className="text-cyber-cyan" />
    },
  ];
  
  // Filtrar reportes según criterios seleccionados
  const reportesFiltrados = reportes.filter(reporte => {
    // Filtro por tipo
    if (filtroTipo !== 'todos' && reporte.tipo !== filtroTipo) return false;
    
    // Filtro por formato
    if (filtroFormato !== 'todos' && reporte.formato !== filtroFormato) return false;
    
    // Filtro por búsqueda
    if (busqueda && !reporte.titulo.toLowerCase().includes(busqueda.toLowerCase()) &&
        !reporte.descripcion.toLowerCase().includes(busqueda.toLowerCase())) {
      return false;
    }
    
    return true;
  }).sort((a, b) => {
    // Ordenar según criterio seleccionado
    if (ordenarPor === 'fecha') {
      return new Date(b.fecha).getTime() - new Date(a.fecha).getTime();
    } else if (ordenarPor === 'titulo') {
      return a.titulo.localeCompare(b.titulo);
    } else if (ordenarPor === 'tipo') {
      return a.tipo.localeCompare(b.tipo);
    }
    return 0;
  });
  
  // Filtrar plantillas según búsqueda
  const plantillasFiltradas = plantillasReportes.filter(plantilla => {
    if (busqueda && !plantilla.titulo.toLowerCase().includes(busqueda.toLowerCase()) &&
        !plantilla.descripcion.toLowerCase().includes(busqueda.toLowerCase())) {
      return false;
    }
    return true;
  });

  // Color según tipo de reporte
  const colorTipo = (tipo: string) => {
    switch (tipo) {
      case 'ventas': return 'bg-cyan-900/30 text-cyan-400';
      case 'clientes': return 'bg-blue-900/30 text-blue-400';
      case 'inventario': return 'bg-teal-900/30 text-teal-400';
      case 'marketing': return 'bg-purple-900/30 text-purple-400';
      case 'fiscal': return 'bg-yellow-900/30 text-yellow-400';
      default: return 'bg-gray-800 text-gray-400';
    }
  };
  
  // Color según formato
  const colorFormato = (formato: string) => {
    switch (formato) {
      case 'pdf': return 'bg-red-900/30 text-red-400';
      case 'excel': return 'bg-green-900/30 text-green-400';
      case 'csv': return 'bg-blue-900/30 text-blue-400';
      default: return 'bg-gray-800 text-gray-400';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Encabezado */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-cyber-text">Reportes de Ventas</h1>
          <p className="text-cyber-text/70">Generación y programación de reportes para tu negocio</p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-2">
          <button className="flex items-center bg-cyber-cyan text-cyber-dark px-4 py-2 rounded-md text-sm font-medium hover:bg-cyber-cyan/90 transition-colors">
            <FilePlus size={16} className="mr-2" />
            Crear Reporte
          </button>
        </div>
      </div>
      
      {/* Búsqueda y filtros */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <div className="flex-grow">
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar reportes..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                className="w-full px-4 py-2 pl-10 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
              />
              <div className="absolute left-3 top-2.5 text-cyber-text/50">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2">
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              className="px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
            >
              <option value="todos">Todos los tipos</option>
              <option value="ventas">Ventas</option>
              <option value="clientes">Clientes</option>
              <option value="inventario">Inventario</option>
              <option value="marketing">Marketing</option>
              <option value="fiscal">Fiscal</option>
            </select>
            
            <select
              value={filtroFormato}
              onChange={(e) => setFiltroFormato(e.target.value)}
              className="px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
            >
              <option value="todos">Todos los formatos</option>
              <option value="pdf">PDF</option>
              <option value="excel">Excel</option>
              <option value="csv">CSV</option>
            </select>
            
            <select
              value={ordenarPor}
              onChange={(e) => setOrdenarPor(e.target.value)}
              className="px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
            >
              <option value="fecha">Ordenar por fecha</option>
              <option value="titulo">Ordenar por título</option>
              <option value="tipo">Ordenar por tipo</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Reportes destacados */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex items-center mb-4">
          <Star size={18} className="text-cyber-cyan mr-2" />
          <h2 className="text-lg font-semibold text-cyber-text">Reportes Destacados</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {reportes
            .filter(r => r.destacado)
            .slice(0, 3)
            .map((reporte) => (
            <div 
              key={reporte.id} 
              className="p-4 bg-cyber-detail/20 border border-cyber-cyan/10 rounded-lg hover:bg-cyber-detail/30 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-cyber-text">{reporte.titulo}</h3>
                  <p className="text-xs text-cyber-text/70 mt-1">{reporte.descripcion}</p>
                  
                  <div className="flex items-center mt-3 space-x-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${colorTipo(reporte.tipo)}`}>
                      {reporte.tipo.charAt(0).toUpperCase() + reporte.tipo.slice(1)}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full ${colorFormato(reporte.formato)}`}>
                      {reporte.formato.toUpperCase()}
                    </span>
                    <span className="text-xs text-cyber-text/70">
                      {reporte.fecha}
                    </span>
                  </div>
                </div>
                <div className="p-2 rounded-lg bg-cyber-detail/40">
                  {reporte.icono}
                </div>
              </div>
              
              <div className="flex mt-4 space-x-2">
                <button className="flex items-center text-xs px-3 py-1.5 rounded bg-cyber-cyan text-cyber-dark hover:bg-cyber-cyan/90 transition-colors">
                  <Download size={14} className="mr-1" />
                  Descargar
                </button>
                <button className="flex items-center text-xs px-3 py-1.5 rounded bg-cyber-detail/50 text-cyber-text hover:bg-cyber-detail/70 transition-colors">
                  <Eye size={14} className="mr-1" />
                  Ver
                </button>
                <button className="flex items-center text-xs px-3 py-1.5 rounded bg-cyber-detail/50 text-cyber-text hover:bg-cyber-detail/70 transition-colors">
                  <Share2 size={14} className="mr-1" />
                  Compartir
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Plantillas predefinidas */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex items-center mb-4">
          <FileText size={18} className="text-cyber-cyan mr-2" />
          <h2 className="text-lg font-semibold text-cyber-text">Plantillas de Reportes</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plantillasFiltradas.map((plantilla) => (
            <div 
              key={plantilla.id} 
              className="p-4 bg-cyber-detail/20 border border-cyber-cyan/10 rounded-lg hover:border-cyber-cyan/30 transition-colors cursor-pointer"
            >
              <div className="flex items-center mb-2">
                <div className="p-2 mr-3 rounded-lg bg-cyber-detail/40 text-cyber-cyan">
                  {plantilla.icono}
                </div>
                <div>
                  <h3 className="font-medium text-cyber-text">{plantilla.titulo}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${colorTipo(plantilla.categoria)}`}>
                    {plantilla.categoria.charAt(0).toUpperCase() + plantilla.categoria.slice(1)}
                  </span>
                </div>
              </div>
              <p className="text-xs text-cyber-text/70 mt-1">{plantilla.descripcion}</p>
              
              <div className="flex justify-end mt-3">
                <button className="text-xs text-cyber-cyan hover:underline">
                  Usar plantilla →
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Lista de reportes */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center">
            <Calendar size={18} className="text-cyber-cyan mr-2" />
            <h2 className="text-lg font-semibold text-cyber-text">Todos los Reportes</h2>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-cyber-text/70">{reportesFiltrados.length} reportes</span>
            <button className="text-cyber-text/70 hover:text-cyber-cyan">
              <Filter size={16} />
            </button>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-cyber-detail">
            <thead className="bg-cyber-detail/30">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Reporte
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Tipo
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Formato
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Fecha
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Estado
                </th>
                <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-transparent divide-y divide-cyber-detail/30">
              {reportesFiltrados.map((reporte) => (
                <tr key={reporte.id} className="hover:bg-cyber-detail/20">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-lg bg-cyber-detail/40">
                        {reporte.icono}
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-cyber-text">{reporte.titulo}</div>
                        <div className="text-xs text-cyber-text/70 max-w-md truncate">{reporte.descripcion}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorTipo(reporte.tipo)}`}>
                      {reporte.tipo.charAt(0).toUpperCase() + reporte.tipo.slice(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorFormato(reporte.formato)}`}>
                      {reporte.formato.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-cyber-text">
                    {reporte.fecha}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {reporte.programado ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-900/30 text-blue-400">
                        <Clock size={12} className="mr-1" />
                        Programado
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-900/30 text-green-400">
                        Completado
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      <button className="p-1 text-cyber-text/70 hover:text-cyber-cyan rounded" title="Ver">
                        <Eye size={16} />
                      </button>
                      <button className="p-1 text-cyber-text/70 hover:text-cyber-cyan rounded" title="Descargar">
                        <Download size={16} />
                      </button>
                      <button className="p-1 text-cyber-text/70 hover:text-cyber-cyan rounded" title="Compartir">
                        <Share2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {reportesFiltrados.length === 0 && (
          <div className="py-8 text-center">
            <div className="inline-flex items-center justify-center p-4 rounded-full bg-cyber-detail/30 text-cyber-text/70 mb-4">
              <FileText size={32} />
            </div>
            <p className="text-sm text-cyber-text/70">No se encontraron reportes que coincidan con los criterios de búsqueda.</p>
            <button className="mt-4 text-cyber-cyan hover:underline">
              Limpiar filtros
            </button>
          </div>
        )}
      </div>
      
      {/* Reportes programados */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex items-center mb-4">
          <Clock size={18} className="text-cyber-cyan mr-2" />
          <h2 className="text-lg font-semibold text-cyber-text">Reportes Programados</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-cyber-detail">
            <thead className="bg-cyber-detail/30">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Reporte
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Frecuencia
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Próxima ejecución
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Destinatarios
                </th>
                <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-cyber-text/70 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-transparent divide-y divide-cyber-detail/30">
              {reportes.filter(r => r.programado).map((reporte) => (
                <tr key={reporte.id} className="hover:bg-cyber-detail/20">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-lg bg-cyber-detail/40">
                        {reporte.icono}
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-cyber-text">{reporte.titulo}</div>
                        <div className="text-xs text-cyber-text/70">{reporte.tipo} - {reporte.formato.toUpperCase()}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-cyber-text">
                    {reporte.fecha === 'Diario' ? 'Diario' : 'Mensual'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-cyber-text">
                    {reporte.fecha === 'Diario' ? 'Mañana 08:00 AM' : '01/04/2025 08:00 AM'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-cyber-text">
                    <div className="flex -space-x-1">
                      <div className="h-6 w-6 rounded-full bg-blue-500 flex items-center justify-center text-xs text-white">JM</div>
                      <div className="h-6 w-6 rounded-full bg-green-500 flex items-center justify-center text-xs text-white">AL</div>
                      <div className="h-6 w-6 rounded-full bg-cyber-detail flex items-center justify-center text-xs text-white">+2</div>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      <button className="p-1 text-cyber-text/70 hover:text-cyber-cyan rounded" title="Editar">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </button>
                      <button className="p-1 text-cyber-text/70 hover:text-cyber-cyan rounded" title="Pausar">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </button>
                      <button className="p-1 text-red-400 hover:text-red-300 rounded" title="Eliminar">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="mt-4 text-right">
          <button className="text-cyber-cyan hover:underline text-sm">
            Programar nuevo reporte →
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportesVentas;