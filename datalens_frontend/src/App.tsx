import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login/Login';
import Dashboard from './components/Dashboard/Dashboard';
import Navbar from './components/Navbar/Navbar';
import { User } from './types';
import { authService } from './services/api';
import './styles/global.css';

// Import all pages
import ProductsPage from './pages/ProductsPage';
import CategoriesPage from './pages/CategoriesPage';
import SuppliersPage from './pages/SuppliersPage';
import TransactionsPage from './pages/TransactionsPage';
import AlertsPage from './pages/AlertsPage';
import ForecastingPage from './pages/ForecastingPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';
import InventoryPage from './pages/InventoryPage';

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        // Mock user data for MVP
        const mockUser: User = {
          id: 1,
          username: 'juan',
          email: 'juan@gmail.com',
          first_name: 'Juan',
          last_name: 'Pérez',
          role: 'superadmin',
          company: {
            id: 1,
            name: 'Mi Empresa',
            ruc: '20123456789',
            address: 'Lima, Perú',
            email: 'contacto@miempresa.com',
            subscription_type: 'premium',
            is_active: true
          },
          phone: '+51 999 888 777',
          position: 'Administrador',
          department: 'Sistemas',
          is_active: true,
          created_at: '2024-01-01T10:00:00Z'
        };
        
        setUser(mockUser);
        setIsAuthenticated(true);
      } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    }
    setLoading(false);
  };

  const handleLogin = (token: string) => {
    localStorage.setItem('access_token', token);
    setIsAuthenticated(true);
    checkAuth();
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Cargando aplicación...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="app">
        <Navbar user={user} onLogout={handleLogout} />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/categories" element={<CategoriesPage />} />
            <Route path="/suppliers" element={<SuppliersPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/forecasting" element={<ForecastingPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;
