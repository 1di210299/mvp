// src/components/UserMenu.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  User, 
  ChevronDown, 
  LogOut, 
  Settings, 
  HelpCircle, 
  Key, 
  Bell,
  Moon,
  CheckSquare
} from 'lucide-react';

const UserMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  
  // Cerrar el menú al hacer clic fuera de él
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  return (
    <div className="relative" ref={menuRef}>
      <button 
        className="flex items-center space-x-3 bg-cyber-detail/20 hover:bg-cyber-detail/40 text-cyber-text rounded-full pl-1 pr-3 py-1 transition-colors focus:outline-none"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="h-8 w-8 rounded-full bg-cyber-cyan/20 flex items-center justify-center text-cyber-cyan">
          <User size={18} />
        </div>
        <div className="text-sm font-medium hidden lg:block">Juan Diego</div>
        <ChevronDown 
          size={16} 
          className={`text-cyber-text/50 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-cyber-dark/95 backdrop-blur-md border border-cyber-cyan/30 rounded-lg shadow-lg overflow-hidden z-50">
          <div className="p-3 border-b border-cyber-detail/30">
            <div className="flex items-start">
              <div className="mr-3 h-10 w-10 rounded-full bg-cyber-cyan/20 flex items-center justify-center text-cyber-cyan">
                <User size={22} />
              </div>
              <div>
                <div className="font-medium text-cyber-text">Juan Diego</div>
                <div className="text-xs text-cyber-text/70">gjuandiego213@gmail.com</div>
              </div>
            </div>
          </div>
          
          <div className="p-1">
            <Link 
              to="/dashboard/ajustes" 
              className="flex items-center px-3 py-2 text-sm text-cyber-text hover:bg-cyber-detail/30 rounded-md m-1"
              onClick={() => setIsOpen(false)}
            >
              <Settings size={16} className="mr-2 text-cyber-cyan/80" />
              Configuración de cuenta
            </Link>
            
            <Link 
              to="/dashboard/seguridad" 
              className="flex items-center px-3 py-2 text-sm text-cyber-text hover:bg-cyber-detail/30 rounded-md m-1"
              onClick={() => setIsOpen(false)}
            >
              <Key size={16} className="mr-2 text-cyber-cyan/80" />
              Seguridad
            </Link>
            
            <Link 
              to="/dashboard/notificaciones" 
              className="flex items-center px-3 py-2 text-sm text-cyber-text hover:bg-cyber-detail/30 rounded-md m-1"
              onClick={() => setIsOpen(false)}
            >
              <Bell size={16} className="mr-2 text-cyber-cyan/80" />
              Notificaciones
            </Link>
            
            <button 
              className="flex items-center w-full text-left px-3 py-2 text-sm text-cyber-text hover:bg-cyber-detail/30 rounded-md m-1"
              onClick={() => {
                // Lógica para cambiar el tema
                alert('Cambiando tema...');
                setIsOpen(false);
              }}
            >
              <Moon size={16} className="mr-2 text-cyber-cyan/80" />
              Modo oscuro
            </button>
            
            <div className="border-t border-cyber-detail/30 my-1"></div>
            
            <Link 
              to="/ayuda" 
              className="flex items-center px-3 py-2 text-sm text-cyber-text hover:bg-cyber-detail/30 rounded-md m-1"
              onClick={() => setIsOpen(false)}
            >
              <HelpCircle size={16} className="mr-2 text-cyber-cyan/80" />
              Centro de ayuda
            </Link>
            
            <button 
              className="flex items-center w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-red-900/20 rounded-md m-1"
              onClick={() => {
                // Lógica para cerrar sesión
                if (window.confirm('¿Estás seguro de que deseas cerrar sesión?')) {
                  alert('Cerrando sesión...');
                  window.location.href = '/login';
                }
                setIsOpen(false);
              }}
            >
              <LogOut size={16} className="mr-2" />
              Cerrar sesión
            </button>
          </div>
          
          <div className="bg-cyber-detail/10 p-3 text-xs text-cyber-text/60">
            <div className="flex items-center">
              <CheckSquare size={14} className="mr-2 text-cyber-cyan/80" />
              ANNEX AI v2.3.0
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserMenu;