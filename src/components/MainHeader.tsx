// src/components/MainHeader.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Search, Menu } from 'lucide-react';
import UserMenu from './UserMenu';
import NotificationsMenu from './NotificationsMenu';

interface MainHeaderProps {
  onToggleSidebar?: () => void;
  showSidebarToggle?: boolean;
}

const MainHeader: React.FC<MainHeaderProps> = ({ 
  onToggleSidebar, 
  showSidebarToggle = false 
}) => {
  return (
    <header className="bg-cyber-dark/90 backdrop-blur-sm border-b border-cyber-cyan/30 py-2 px-4 flex justify-between items-center sticky top-0 z-50">
      {/* Logo y título */}
      <div className="flex items-center">
        {showSidebarToggle && (
          <div className="block lg:hidden mr-3">
            <button 
              className="p-1 text-cyber-text/80 hover:text-cyber-cyan rounded"
              onClick={onToggleSidebar}
            >
              <Menu size={20} />
            </button>
          </div>
        )}
        <Link 
          to="/"
          className="text-cyber-cyan font-bold text-xl cursor-pointer"
        >
          ANNEX AI
        </Link>
      </div>
      
      {/* Búsqueda */}
      <div className="hidden md:block flex-1 max-w-md mx-4">
        <div className="relative">
          <input 
            type="text" 
            placeholder="Buscar..." 
            className="w-full px-4 py-1.5 pl-9 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded-full focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
          />
          <div className="absolute left-3 top-2 text-cyber-text/50">
            <Search size={16} />
          </div>
        </div>
      </div>
      
      {/* Menú de usuario y notificaciones */}
      <div className="flex items-center space-x-2">
        {/* Componente de Notificaciones */}
        <NotificationsMenu />
        
        {/* Componente de Menú de Usuario */}
        <div className="hidden md:block">
          <UserMenu />
        </div>
        
        <button className="p-1.5 text-cyber-text/80 hover:text-cyber-cyan rounded-full md:hidden">
          <Search size={18} />
        </button>
      </div>
    </header>
  );
};

export default MainHeader;