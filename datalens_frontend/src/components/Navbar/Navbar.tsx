import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { User } from '../../types';
import {
  BarChart3,
  Package,
  Layers,
  Truck,
  ArrowUpDown,
  AlertTriangle,
  TrendingUp,
  FileText,
  Settings,
  LogOut,
  Home,
  Users,
  Target,
  Briefcase,
  Menu,
  X
} from '../ui/icons';

interface NavbarProps {
  user: User | null;
  onLogout: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isActive = (path: string) => {
    if (path === '/dashboard' && location.pathname === '/') return true;
    return location.pathname === path;
  };

  const navigationItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/products', label: 'Productos', icon: Package },
    { path: '/categories', label: 'Categorías', icon: Layers },
    { path: '/suppliers', label: 'Proveedores', icon: Truck },
    { path: '/inventory', label: 'Inventario', icon: BarChart3 },
    { path: '/transactions', label: 'Movimientos', icon: ArrowUpDown },
    { path: '/alerts', label: 'Alertas', icon: AlertTriangle },
    { path: '/forecasting', label: 'Pronósticos', icon: TrendingUp },
    { path: '/reports', label: 'Reportes', icon: FileText },
    // CRM Section
    { path: '/customers', label: 'Clientes', icon: Users },
    { path: '/leads', label: 'Leads', icon: Target },
    { path: '/opportunities', label: 'Oportunidades', icon: Briefcase },
    { path: '/settings', label: 'Configuraciones', icon: Settings },
  ];

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link 
              to="/dashboard" 
              className="flex items-center space-x-2 text-xl font-bold text-blue-600"
            >
              <BarChart3 className="h-8 w-8" />
              <span>DataLens</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive(item.path)
                      ? 'text-blue-600 bg-blue-50'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* User menu */}
          <div className="flex items-center space-x-4">
            {user && (
              <div className="hidden md:flex items-center space-x-3">
                <div className="text-sm">
                  <div className="font-medium text-gray-900">
                    {user.first_name} {user.last_name}
                  </div>
                  <div className="text-gray-500">{user.role}</div>
                </div>
              </div>
            )}
            
            <button
              onClick={onLogout}
              className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden md:block">Cerrar Sesión</span>
            </button>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
            >
              {isMobileMenuOpen ? (
                <X className="block h-6 w-6" />
              ) : (
                <Menu className="block h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 border-t border-gray-200">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium transition-colors ${
                      isActive(item.path)
                        ? 'text-blue-600 bg-blue-50'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
              
              {user && (
                <div className="pt-4 pb-3 border-t border-gray-200">
                  <div className="px-3 py-2">
                    <div className="text-base font-medium text-gray-800">
                      {user.first_name} {user.last_name}
                    </div>
                    <div className="text-sm text-gray-500">{user.email}</div>
                    <div className="text-sm text-gray-500">{user.role}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
