// src/layouts/DashboardLayout.tsx
import React, { useState } from 'react';
import { Link, useLocation, Route, Routes, Navigate } from 'react-router-dom';
import { 
  BarChart3, 
  ShoppingCart, 
  Users, 
  TrendingUp, 
  Database, 
  PieChart,
  Calendar,
  Settings,
  Bot,
  X,
  Home
} from 'lucide-react';
import MainHeader from '../components/MainHeader';

// Importamos los componentes para cada sección
import DashboardVentas from '../components/DashboardVentas';
import VentasChart from '../components/VentasChart';
import SegmentacionClientes from '../components/SegmentacionClientes';
import PrediccionesVentas from '../components/PrediccionesVentas';
import ReportesVentas from '../components/ReportesVentas';
import AsistenteVentas from '../components/AsistenteVentas';

// Importar los componentes de datasets desde las carpetas correctas
import DatasetsPage from '../pages/DatasetsPage';  // La página principal de datasets
import DatasetDetail from '../components/DatasetDetail'; // Componente para ver detalles de un dataset

// Componente principal del layout
const DashboardLayout = () => {
  const location = useLocation();
  
  // Estado para controlar la visibilidad del chatbot
  const [chatbotAbierto, setChatbotAbierto] = useState(false);
  
  // Estado para controlar sidebar en móviles
  const [sidebarAbierto, setSidebarAbierto] = useState(false);
  
  // Función para alternar la visibilidad del chatbot
  const toggleChatbot = () => {
    setChatbotAbierto(!chatbotAbierto);
  };
  
  // Determinar la sección activa basada en la URL
  const getSeccionActiva = () => {
    const path = location.pathname;
    if (path.includes('/ventas')) return 'ventas';
    if (path.includes('/clientes')) return 'clientes';
    if (path.includes('/predicciones')) return 'predicciones';
    if (path.includes('/datasets')) return 'datasets';
    if (path.includes('/reportes')) return 'reportes';
    if (path.includes('/calendarios')) return 'calendarios';
    if (path.includes('/ajustes')) return 'ajustes';
    return 'dashboard';
  };
  
  const seccionActiva = getSeccionActiva();
  
  return (
    <div className="flex flex-col min-h-screen text-cyber-text">
      {/* Usar el componente MainHeader con la opción para mostrar el toggle del sidebar */}
      <MainHeader 
        onToggleSidebar={() => setSidebarAbierto(!sidebarAbierto)} 
        showSidebarToggle={true} 
      />
            
      <div className="flex flex-1 relative">
        {/* Sidebar */}
        <aside 
          className={`
            ${sidebarAbierto ? 'translate-x-0' : '-translate-x-full'} 
            lg:translate-x-0 
            w-64 bg-cyber-dark/80 backdrop-blur-sm border-r border-cyber-cyan/30 
            p-4 fixed top-[52px] bottom-0 z-40 transition-transform duration-300 ease-in-out
            lg:sticky
          `}
        >
          <div className="mb-6">
            <h3 className="font-semibold text-cyber-cyan mb-2 px-2">ANNEX IA</h3>
            <p className="text-xs text-cyber-text/70 px-2 mb-4">Analítica de Ventas para MYPES</p>
          </div>

          <nav className="space-y-1">
            <div className="mb-2 px-2 text-xs font-medium uppercase text-cyber-text/50">
              Principal
            </div>
            
            <Link
              to="/"
              className="flex items-center px-2 py-2 rounded transition-colors cursor-pointer group hover:bg-cyber-cyan/10 text-cyber-text hover:text-cyber-cyan"
              onClick={() => setSidebarAbierto(false)}
            >
              <Home size={18} className="mr-2 text-cyber-cyan/80 group-hover:text-cyber-cyan" />
              Inicio
            </Link>
            
            <div className="mb-2 px-2 text-xs font-medium uppercase text-cyber-text/50">
              Análisis
            </div>
            
            <Link
              to="/dashboard"
              className={`flex items-center px-2 py-2 rounded transition-colors cursor-pointer group ${
                seccionActiva === 'dashboard' ? "bg-cyber-cyan/20 text-cyber-cyan border-l-2 border-cyber-cyan pl-1" : "hover:bg-cyber-cyan/10 text-cyber-text hover:text-cyber-cyan"
              }`}
              onClick={() => setSidebarAbierto(false)}
            >
              <BarChart3 size={18} className="mr-2 text-cyber-cyan/80 group-hover:text-cyber-cyan" />
              Dashboard Ventas
            </Link>

            <Link
              to="/dashboard/ventas"
              className={`flex items-center px-2 py-2 rounded transition-colors cursor-pointer group ${
                seccionActiva === 'ventas' ? "bg-cyber-cyan/20 text-cyber-cyan border-l-2 border-cyber-cyan pl-1" : "hover:bg-cyber-cyan/10 text-cyber-text hover:text-cyber-cyan"
              }`}
              onClick={() => setSidebarAbierto(false)}
            >
              <ShoppingCart size={18} className="mr-2 text-cyber-cyan/80 group-hover:text-cyber-cyan" />
              Análisis de Ventas
            </Link>

            <Link
              to="/dashboard/clientes"
              className={`flex items-center px-2 py-2 rounded transition-colors cursor-pointer group ${
                seccionActiva === 'clientes' ? "bg-cyber-cyan/20 text-cyber-cyan border-l-2 border-cyber-cyan pl-1" : "hover:bg-cyber-cyan/10 text-cyber-text hover:text-cyber-cyan"
              }`}
              onClick={() => setSidebarAbierto(false)}
            >
              <Users size={18} className="mr-2 text-cyber-cyan/80 group-hover:text-cyber-cyan" />
              Segmentación Clientes
            </Link>

            <Link
              to="/dashboard/predicciones"
              className={`flex items-center px-2 py-2 rounded transition-colors cursor-pointer group ${
                seccionActiva === 'predicciones' ? "bg-cyber-cyan/20 text-cyber-cyan border-l-2 border-cyber-cyan pl-1" : "hover:bg-cyber-cyan/10 text-cyber-text hover:text-cyber-cyan"
              }`}
              onClick={() => setSidebarAbierto(false)}
            >
              <TrendingUp size={18} className="mr-2 text-cyber-cyan/80 group-hover:text-cyber-cyan" />
              Predicciones
            </Link>

            <div className="pt-4 mb-2 px-2 text-xs font-medium uppercase text-cyber-text/50">
              Datos
            </div>

            <Link
              to="/dashboard/datasets"
              className={`flex items-center px-2 py-2 rounded transition-colors cursor-pointer group ${
                seccionActiva === 'datasets' ? "bg-cyber-cyan/20 text-cyber-cyan border-l-2 border-cyber-cyan pl-1" : "hover:bg-cyber-cyan/10 text-cyber-text hover:text-cyber-cyan"
              }`}
              onClick={() => setSidebarAbierto(false)}
            >
              <Database size={18} className="mr-2 text-cyber-cyan/80 group-hover:text-cyber-cyan" />
              Datasets
            </Link>

            <Link
              to="/dashboard/reportes"
              className={`flex items-center px-2 py-2 rounded transition-colors cursor-pointer group ${
                seccionActiva === 'reportes' ? "bg-cyber-cyan/20 text-cyber-cyan border-l-2 border-cyber-cyan pl-1" : "hover:bg-cyber-cyan/10 text-cyber-text hover:text-cyber-cyan"
              }`}
              onClick={() => setSidebarAbierto(false)}
            >
              <PieChart size={18} className="mr-2 text-cyber-cyan/80 group-hover:text-cyber-cyan" />
              Reportes
            </Link>

            <Link
              to="/dashboard/calendarios"
              className={`flex items-center px-2 py-2 rounded transition-colors cursor-pointer group ${
                seccionActiva === 'calendarios' ? "bg-cyber-cyan/20 text-cyber-cyan border-l-2 border-cyber-cyan pl-1" : "hover:bg-cyber-cyan/10 text-cyber-text hover:text-cyber-cyan"
              }`}
              onClick={() => setSidebarAbierto(false)}
            >
              <Calendar size={18} className="mr-2 text-cyber-cyan/80 group-hover:text-cyber-cyan" />
              Calendarios
            </Link>

            <div className="pt-4 mb-2 px-2 text-xs font-medium uppercase text-cyber-text/50">
              Configuración
            </div>

            <Link
              to="/dashboard/ajustes"
              className={`flex items-center px-2 py-2 rounded transition-colors cursor-pointer group ${
                seccionActiva === 'ajustes' ? "bg-cyber-cyan/20 text-cyber-cyan border-l-2 border-cyber-cyan pl-1" : "hover:bg-cyber-cyan/10 text-cyber-text hover:text-cyber-cyan"
              }`}
              onClick={() => setSidebarAbierto(false)}
            >
              <Settings size={18} className="mr-2 text-cyber-cyan/80 group-hover:text-cyber-cyan" />
              Ajustes
            </Link>
          </nav>

          <div className="mt-auto pt-6">
            <div className="bg-cyber-cyan/10 rounded-lg p-3 border border-cyber-cyan/20">
              <h4 className="text-sm font-medium text-cyber-cyan mb-2">¿Necesitas ayuda?</h4>
              <p className="text-xs text-cyber-text/70 mb-3">Contáctanos para soporte técnico o consultas de negocio.</p>
              <button 
                className="text-xs text-cyber-cyan hover:text-cyber-cyan/80 underline"
                onClick={toggleChatbot}
              >
                Abrir asistente ANNEX
              </button>
            </div>
          </div>
        </aside>

        {/* Sombra para sidebar en móviles */}
        {sidebarAbierto && (
          <div 
            className="fixed inset-0 bg-black/50 lg:hidden z-30"
            onClick={() => setSidebarAbierto(false)}
          ></div>
        )}

        {/* Contenido principal con rutas */}
        <div className="flex-1 bg-cyber-dark">
          <Routes>
            {/* Dashboard principal - solo debe mostrar DashboardVentas */}
            <Route path="/" element={<DashboardVentas />} />
            
            {/* Rutas para análisis y visualización */}
            <Route path="/ventas" element={<VentasChart />} />
            <Route path="/clientes" element={<SegmentacionClientes />} />
            <Route path="/predicciones" element={<PrediccionesVentas />} />
            
            {/* Rutas para datasets - páginas independientes */}
            <Route path="/datasets" element={<DatasetsPage />} />
            <Route path="/datasets/:id" element={<DatasetDetail />} />
            
            {/* Otras secciones */}
            <Route path="/reportes" element={<ReportesVentas />} />
            <Route path="/calendarios" element={<div>Calendario de Ventas</div>} />
            <Route path="/ajustes" element={<div>Ajustes</div>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
        
        {/* Botón flotante para abrir el asistente */}
        {!chatbotAbierto && (
          <button 
            className="fixed bottom-6 right-6 p-3 rounded-full bg-cyber-cyan text-cyber-dark shadow-lg hover:bg-cyber-cyan/90 transition-colors z-40 flex items-center group"
            onClick={toggleChatbot}
          >
            <Bot size={24} />
            <span className="max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-500 ease-out whitespace-nowrap">
              <span className="pl-2">Asistente ANNEX</span>
            </span>
          </button>
        )}
        
        {/* Panel del chatbot */}
        <div 
          className={`
            fixed right-0 top-0 bottom-0
            w-full sm:w-96 
            bg-cyber-dark/95 backdrop-blur-md border-l border-cyber-cyan/30
            shadow-2xl
            transition-transform duration-300 ease-in-out
            z-50
            ${chatbotAbierto ? 'translate-x-0' : 'translate-x-full'}
          `}
        >
          <div className="flex justify-between items-center p-4 border-b border-cyber-detail">
            <div className="flex items-center">
              <div className="bg-cyber-cyan/20 p-2 rounded-full mr-3">
                <Bot size={20} className="text-cyber-cyan" />
              </div>
              <h3 className="text-lg font-semibold text-cyber-text">Asistente ANNEX</h3>
            </div>
            <button 
              className="text-cyber-text/80 hover:text-cyber-cyan"
              onClick={toggleChatbot}
            >
              <X size={20} />
            </button>
          </div>
          
          <div className="h-full py-2">
            <AsistenteVentas />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardLayout;