import React, { useState, useEffect, useRef } from 'react';
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
  X,
  Warehouse,
  UserCheck,
  ChevronDown,
  Bell,
  Search,
  Upload  // Agregamos el icono para importación
} from '../ui/icons';
import { ThemeToggle } from '../theme/ThemeToggle';
import './Navbar.css';

interface NavbarProps {
  user: User | null;
  onLogout: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showInventoryDropdown, setShowInventoryDropdown] = useState(false);
  const [showCRMDropdown, setShowCRMDropdown] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  
  const inventoryRef = useRef<HTMLDivElement>(null);
  const crmRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  // Handle scroll effect
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Handle click outside to close dropdowns
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (inventoryRef.current && !inventoryRef.current.contains(event.target as Node)) {
        setShowInventoryDropdown(false);
      }
      if (crmRef.current && !crmRef.current.contains(event.target as Node)) {
        setShowCRMDropdown(false);
      }
      if (userRef.current && !userRef.current.contains(event.target as Node)) {
        setShowUserDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isActive = (path: string) => {
    if (path === '/dashboard' && location.pathname === '/') return true;
    return location.pathname === path;
  };

  const inventoryItems = [
    { path: '/products', label: 'Productos', icon: Package, description: 'Gestión de productos' },
    { path: '/categories', label: 'Categorías', icon: Layers, description: 'Organización por categorías' },
    { path: '/suppliers', label: 'Proveedores', icon: Truck, description: 'Gestión de proveedores' },
    { path: '/inventory', label: 'Stock', icon: BarChart3, description: 'Control de inventario' },
    { path: '/transactions', label: 'Movimientos', icon: ArrowUpDown, description: 'Historial de movimientos' },
    { path: '/alerts', label: 'Alertas', icon: AlertTriangle, description: 'Notificaciones de stock' },
    { path: '/forecasting', label: 'Pronósticos', icon: TrendingUp, description: 'Predicciones AI' },
    { path: '/reports', label: 'Reportes', icon: FileText, description: 'Informes y análisis' },
    { path: '/data-import', label: 'Importar Datos', icon: Upload, description: 'Importar desde Excel/CSV' }, // Corregida la ruta
  ];

  const crmItems = [
    { path: '/customers', label: 'Clientes', icon: Users, description: 'Base de clientes' },
    { path: '/leads', label: 'Leads', icon: Target, description: 'Prospectos y contactos' },
    { path: '/opportunities', label: 'Oportunidades', icon: Briefcase, description: 'Negocios en proceso' },
  ];

  const isInventoryActive = inventoryItems.some(item => location.pathname === item.path);
  const isCRMActive = crmItems.some(item => location.pathname === item.path);

  return (
    <nav className={`navbar ${isScrolled ? 'navbar-scrolled' : ''}`}>
      <div className="navbar-container">
        {/* Brand Section */}
        <div className="navbar-brand">
          <Link to="/dashboard" className="brand-link">
            <div className="brand-icon">
              <BarChart3 className="brand-icon-svg" />
            </div>
            <span className="brand-text">DataLens</span>
          </Link>
        </div>

        {/* Desktop Navigation */}
        <div className="navbar-nav">
          {/* Dashboard */}
          <Link
            to="/dashboard"
            className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}
          >
            <div className="nav-icon">
              <Home size={18} />
            </div>
            <span className="nav-label">Dashboard</span>
          </Link>

          {/* Inventario Dropdown */}
          <div className={`nav-dropdown ${isInventoryActive ? 'active' : ''}`} ref={inventoryRef}>
            <button
              onClick={() => setShowInventoryDropdown(!showInventoryDropdown)}
              className="nav-dropdown-trigger"
            >
              <div className="nav-icon">
                <Warehouse size={18} />
              </div>
              <span className="nav-label">Inventario</span>
              <ChevronDown 
                size={16} 
                className={`nav-chevron ${showInventoryDropdown ? 'open' : ''}`} 
              />
            </button>
            
            {showInventoryDropdown && (
              <div className="nav-dropdown-content">
                <div className="dropdown-section">
                  <div className="dropdown-section-title">Gestión de Inventario</div>
                  <div className="dropdown-grid">
                    {inventoryItems.map((item) => {
                      const Icon = item.icon;
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={() => setShowInventoryDropdown(false)}
                          className={`dropdown-item ${isActive(item.path) ? 'active' : ''}`}
                        >
                          <div className="dropdown-item-icon">
                            <Icon size={20} />
                          </div>
                          <div className="dropdown-item-content">
                            <div className="dropdown-item-label">{item.label}</div>
                            <div className="dropdown-item-description">{item.description}</div>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* CRM Dropdown */}
          <div className={`nav-dropdown ${isCRMActive ? 'active' : ''}`} ref={crmRef}>
            <button
              onClick={() => setShowCRMDropdown(!showCRMDropdown)}
              className="nav-dropdown-trigger"
            >
              <div className="nav-icon">
                <UserCheck size={18} />
              </div>
              <span className="nav-label">CRM</span>
              <ChevronDown 
                size={16} 
                className={`nav-chevron ${showCRMDropdown ? 'open' : ''}`} 
              />
            </button>
            
            {showCRMDropdown && (
              <div className="nav-dropdown-content">
                <div className="dropdown-section">
                  <div className="dropdown-section-title">Gestión de Clientes</div>
                  <div className="dropdown-grid">
                    {crmItems.map((item) => {
                      const Icon = item.icon;
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={() => setShowCRMDropdown(false)}
                          className={`dropdown-item ${isActive(item.path) ? 'active' : ''}`}
                        >
                          <div className="dropdown-item-icon">
                            <Icon size={20} />
                          </div>
                          <div className="dropdown-item-content">
                            <div className="dropdown-item-label">{item.label}</div>
                            <div className="dropdown-item-description">{item.description}</div>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Configuraciones */}
          <Link
            to="/settings"
            className={`nav-item ${isActive('/settings') ? 'active' : ''}`}
          >
            <div className="nav-icon">
              <Settings size={18} />
            </div>
            <span className="nav-label">Configuración</span>
          </Link>
        </div>

        {/* Right Section */}
        <div className="navbar-actions">
          {/* Theme Toggle */}
          <ThemeToggle />
          
          {/* Search Button */}
          <button className="action-button">
            <Search size={18} />
          </button>

          {/* Notifications */}
          <button className="action-button notification-button">
            <Bell size={18} />
            <span className="notification-badge">3</span>
          </button>

          {/* User Menu */}
          {user && (
            <div className="user-menu" ref={userRef}>
              <button
                onClick={() => setShowUserDropdown(!showUserDropdown)}
                className="user-menu-trigger"
              >
                <div className="user-avatar">
                  <span className="user-initials">
                    {user.first_name?.[0]}{user.last_name?.[0]}
                  </span>
                </div>
                <div className="user-info">
                  <div className="user-name">
                    {user.first_name} {user.last_name}
                  </div>
                  <div className="user-role">{user.role}</div>
                </div>
                <ChevronDown 
                  size={16} 
                  className={`user-chevron ${showUserDropdown ? 'open' : ''}`} 
                />
              </button>

              {showUserDropdown && (
                <div className="user-dropdown">
                  <div className="user-dropdown-header">
                    <div className="user-avatar-large">
                      <span className="user-initials-large">
                        {user.first_name?.[0]}{user.last_name?.[0]}
                      </span>
                    </div>
                    <div className="user-details">
                      <div className="user-name-large">{user.first_name} {user.last_name}</div>
                      <div className="user-email">{user.email}</div>
                      <div className="user-role-badge">{user.role}</div>
                    </div>
                  </div>
                  <div className="user-dropdown-divider"></div>
                  <div className="user-dropdown-actions">
                    <Link to="/profile" className="user-action">
                      <Settings size={16} />
                      <span>Mi Perfil</span>
                    </Link>
                    <button onClick={onLogout} className="user-action logout">
                      <LogOut size={16} />
                      <span>Cerrar Sesión</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="mobile-menu-button"
          >
            {isMobileMenuOpen ? (
              <X size={24} />
            ) : (
              <Menu size={24} />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMobileMenuOpen && (
        <div className="mobile-menu">
          <div className="mobile-nav">
            {/* Dashboard Principal */}
            <Link
              to="/dashboard"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}
            >
              <div className="nav-icon">
                <Home size={20} />
              </div>
              <span className="nav-label">Dashboard</span>
            </Link>

            {/* Inventario Section */}
            <div className="mobile-section">
              <div className="mobile-section-title">
                <Warehouse size={16} />
                <span>Inventario</span>
              </div>
              {inventoryItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
                  >
                    <div className="nav-icon">
                      <Icon size={20} />
                    </div>
                    <span className="nav-label">{item.label}</span>
                  </Link>
                );
              })}
            </div>

            {/* CRM Section */}
            <div className="mobile-section">
              <div className="mobile-section-title">
                <UserCheck size={16} />
                <span>CRM</span>
              </div>
              {crmItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
                  >
                    <div className="nav-icon">
                      <Icon size={20} />
                    </div>
                    <span className="nav-label">{item.label}</span>
                  </Link>
                );
              })}
            </div>

            {/* Configuraciones */}
            <Link
              to="/settings"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`nav-item ${isActive('/settings') ? 'active' : ''}`}
            >
              <div className="nav-icon">
                <Settings size={20} />
              </div>
              <span className="nav-label">Configuración</span>
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
