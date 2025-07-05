import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { User } from '../../types';
import './Navbar.css';

interface NavbarProps {
  user: User | null;
  onLogout: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
  const location = useLocation();

  const isActiveLink = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <h2>DataLens</h2>
          <span className="navbar-subtitle">Gestión de Inventarios</span>
        </div>
        
        <div className="navbar-menu">
          <div className="navbar-links">
            <Link 
              to="/dashboard" 
              className={`navbar-link ${isActiveLink('/dashboard') ? 'active' : ''}`}
            >
              Dashboard
            </Link>
            <Link 
              to="/inventory" 
              className={`navbar-link ${isActiveLink('/inventory') ? 'active' : ''}`}
            >
              Inventario
            </Link>
            <Link 
              to="/products" 
              className={`navbar-link ${isActiveLink('/products') ? 'active' : ''}`}
            >
              Productos
            </Link>
            <Link 
              to="/categories" 
              className={`navbar-link ${isActiveLink('/categories') ? 'active' : ''}`}
            >
              Categorías
            </Link>
            <Link 
              to="/suppliers" 
              className={`navbar-link ${isActiveLink('/suppliers') ? 'active' : ''}`}
            >
              Proveedores
            </Link>
            <Link 
              to="/transactions" 
              className={`navbar-link ${isActiveLink('/transactions') ? 'active' : ''}`}
            >
              Transacciones
            </Link>
            <Link 
              to="/alerts" 
              className={`navbar-link ${isActiveLink('/alerts') ? 'active' : ''}`}
            >
              Alertas
            </Link>
            <Link 
              to="/forecasting" 
              className={`navbar-link ${isActiveLink('/forecasting') ? 'active' : ''}`}
            >
              Pronósticos
            </Link>
            <Link 
              to="/reports" 
              className={`navbar-link ${isActiveLink('/reports') ? 'active' : ''}`}
            >
              Reportes
            </Link>
            <Link 
              to="/settings" 
              className={`navbar-link ${isActiveLink('/settings') ? 'active' : ''}`}
            >
              Configuración
            </Link>
          </div>
          
          <div className="navbar-user">
            {user && (
              <div className="user-info">
                <div className="user-avatar">
                  {user.first_name.charAt(0) || user.username.charAt(0)}
                </div>
                <div className="user-details">
                  <span className="user-name">
                    {user.first_name} {user.last_name} 
                  </span>
                  <span className="user-company">{user.company.name}</span>
                </div>
                <button onClick={onLogout} className="btn btn-secondary btn-sm">
                  Salir
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
