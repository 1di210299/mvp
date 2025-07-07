import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Package, 
  Users, 
  FileText, 
  Settings, 
  TrendingUp, 
  AlertTriangle,
  Target,
  Warehouse,
  UserCheck,
  ChevronDown
} from './ui/icons';

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
  onClick?: () => void;
}

interface DropdownNavItemProps {
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
  children: React.ReactNode;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, label, isActive, onClick }) => (
  <Link
    to={to}
    className={`nav-item ${isActive ? 'active' : ''}`}
    onClick={onClick}
  >
    <span className="nav-icon">{icon}</span>
    <span className="nav-label">{label}</span>
  </Link>
);

const DropdownNavItem: React.FC<DropdownNavItemProps> = ({ icon, label, isActive, children }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={`nav-dropdown ${isActive ? 'active' : ''}`}>
      <button
        className="nav-dropdown-trigger"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="nav-icon">{icon}</span>
        <span className="nav-label">{label}</span>
        <ChevronDown className={`nav-chevron ${isOpen ? 'open' : ''}`} size={16} />
      </button>
      {isOpen && (
        <div className="nav-dropdown-content">
          {children}
        </div>
      )}
    </div>
  );
};

const Navbar: React.FC = () => {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const isActive = (path: string) => location.pathname === path;
  const isInventoryActive = () => {
    const inventoryPaths = ['/inventory', '/products', '/categories', '/suppliers'];
    return inventoryPaths.some(path => location.pathname.startsWith(path));
  };
  const isCrmActive = () => {
    const crmPaths = ['/clients', '/leads', '/opportunities'];
    return crmPaths.some(path => location.pathname.startsWith(path));
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <div className="navbar-brand">
          <Link to="/" className="brand-link">
            <div className="brand-icon">
              <TrendingUp size={24} color="#3b82f6" />
            </div>
            <span className="brand-text">DataLens</span>
          </Link>
        </div>

        {/* Desktop Navigation */}
        <div className="navbar-nav">
          <NavItem
            to="/"
            icon={<Home size={18} />}
            label="Dashboard"
            isActive={isActive('/')}
          />

          <DropdownNavItem
            icon={<Warehouse size={18} />}
            label="Inventario"
            isActive={isInventoryActive()}
          >
            <NavItem
              to="/inventory"
              icon={<Package size={16} />}
              label="Inventario"
              isActive={isActive('/inventory')}
            />
            <NavItem
              to="/products"
              icon={<Package size={16} />}
              label="Productos"
              isActive={isActive('/products')}
            />
            <NavItem
              to="/categories"
              icon={<FileText size={16} />}
              label="Categorías"
              isActive={isActive('/categories')}
            />
            <NavItem
              to="/suppliers"
              icon={<Users size={16} />}
              label="Proveedores"
              isActive={isActive('/suppliers')}
            />
          </DropdownNavItem>

          <DropdownNavItem
            icon={<UserCheck size={18} />}
            label="CRM"
            isActive={isCrmActive()}
          >
            <NavItem
              to="/clients"
              icon={<Users size={16} />}
              label="Clientes"
              isActive={isActive('/clients')}
            />
            <NavItem
              to="/leads"
              icon={<Target size={16} />}
              label="Leads"
              isActive={isActive('/leads')}
            />
            <NavItem
              to="/opportunities"
              icon={<TrendingUp size={16} />}
              label="Oportunidades"
              isActive={isActive('/opportunities')}
            />
          </DropdownNavItem>

          <NavItem
            to="/forecasting"
            icon={<TrendingUp size={18} />}
            label="Pronósticos"
            isActive={isActive('/forecasting')}
          />

          <NavItem
            to="/reports"
            icon={<FileText size={18} />}
            label="Reportes"
            isActive={isActive('/reports')}
          />

          <NavItem
            to="/alerts"
            icon={<AlertTriangle size={18} />}
            label="Alertas"
            isActive={isActive('/alerts')}
          />

          <NavItem
            to="/settings"
            icon={<Settings size={18} />}
            label="Configuración"
            isActive={isActive('/settings')}
          />
        </div>

        {/* Mobile Menu Button */}
        <button
          className="mobile-menu-button"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="mobile-menu">
          <div className="mobile-nav">
            <NavItem
              to="/"
              icon={<Home size={18} />}
              label="Dashboard"
              isActive={isActive('/')}
              onClick={() => setIsMobileMenuOpen(false)}
            />
            
            <div className="mobile-section">
              <h4 className="mobile-section-title">Inventario</h4>
              <NavItem
                to="/inventory"
                icon={<Package size={16} />}
                label="Inventario"
                isActive={isActive('/inventory')}
                onClick={() => setIsMobileMenuOpen(false)}
              />
              <NavItem
                to="/products"
                icon={<Package size={16} />}
                label="Productos"
                isActive={isActive('/products')}
                onClick={() => setIsMobileMenuOpen(false)}
              />
              <NavItem
                to="/categories"
                icon={<FileText size={16} />}
                label="Categorías"
                isActive={isActive('/categories')}
                onClick={() => setIsMobileMenuOpen(false)}
              />
              <NavItem
                to="/suppliers"
                icon={<Users size={16} />}
                label="Proveedores"
                isActive={isActive('/suppliers')}
                onClick={() => setIsMobileMenuOpen(false)}
              />
            </div>

            <div className="mobile-section">
              <h4 className="mobile-section-title">CRM</h4>
              <NavItem
                to="/clients"
                icon={<Users size={16} />}
                label="Clientes"
                isActive={isActive('/clients')}
                onClick={() => setIsMobileMenuOpen(false)}
              />
              <NavItem
                to="/leads"
                icon={<Target size={16} />}
                label="Leads"
                isActive={isActive('/leads')}
                onClick={() => setIsMobileMenuOpen(false)}
              />
              <NavItem
                to="/opportunities"
                icon={<TrendingUp size={16} />}
                label="Oportunidades"
                isActive={isActive('/opportunities')}
                onClick={() => setIsMobileMenuOpen(false)}
              />
            </div>

            <NavItem
              to="/forecasting"
              icon={<TrendingUp size={18} />}
              label="Pronósticos"
              isActive={isActive('/forecasting')}
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <NavItem
              to="/reports"
              icon={<FileText size={18} />}
              label="Reportes"
              isActive={isActive('/reports')}
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <NavItem
              to="/alerts"
              icon={<AlertTriangle size={18} />}
              label="Alertas"
              isActive={isActive('/alerts')}
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <NavItem
              to="/settings"
              icon={<Settings size={18} />}
              label="Configuración"
              isActive={isActive('/settings')}
              onClick={() => setIsMobileMenuOpen(false)}
            />
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;