// src/components/Header.tsx
import React from 'react';
import { Bell, Search, Menu, User, ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-cyber-dark/90 backdrop-blur-sm border-b border-cyber-cyan/30 py-2 px-4 flex justify-between items-center">
      {/* Logo y título */}
      <div className="flex items-center">
        <div className="block lg:hidden mr-3">
          <button className="p-1 text-cyber-text/80 hover:text-cyber-cyan rounded">
            <Menu size={20} />
          </button>
        </div>
        <Link to="/" className="text-cyber-cyan font-bold text-xl hidden md:block">ANNEX AI</Link>
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
        <button className="p-1.5 text-cyber-text/80 hover:text-cyber-cyan rounded-full relative">
          <Bell size={18} />
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
        
        <div className="hidden md:block ml-3 relative">
          <button className="flex items-center space-x-3 bg-cyber-detail/20 hover:bg-cyber-detail/40 text-cyber-text rounded-full pl-1 pr-3 py-1 transition-colors focus:outline-none">
            <div className="h-8 w-8 rounded-full bg-cyber-cyan/20 flex items-center justify-center text-cyber-cyan">
              <User size={18} />
            </div>
            <div className="text-sm font-medium hidden lg:block">Juan Diego</div>
            <ChevronDown size={16} className="text-cyber-text/50" />
          </button>
        </div>
        
        <button className="p-1.5 text-cyber-text/80 hover:text-cyber-cyan rounded-full md:hidden">
          <Search size={18} />
        </button>
      </div>
    </header>
  );
};

export default Header;