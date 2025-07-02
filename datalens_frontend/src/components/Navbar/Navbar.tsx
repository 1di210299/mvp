import React from 'react';
import { User } from '../../types';
import './Navbar.css';

interface NavbarProps {
  user: User | null;
  onLogout: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <h2>DataLens</h2>
          <span className="navbar-subtitle">Gestión de Inventarios</span>
        </div>
        
        <div className="navbar-menu">
          <div className="navbar-links">
            <a href="#dashboard" className="navbar-link active">Dashboard</a>
            <a href="#inventory" className="navbar-link">Inventario</a>
            <a href="#products" className="navbar-link">Productos</a>
            <a href="#reports" className="navbar-link">Reportes</a>
            <a href="#alerts" className="navbar-link">Alertas</a>
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
