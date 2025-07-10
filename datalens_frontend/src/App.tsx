import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage'; // Cambiado para usar LoginPage
import Dashboard from './components/Dashboard/Dashboard';
import Navbar from './components/Navbar/Navbar';
import MarketingPage from './pages/MarketingPage';
import { User } from './types';
import { authService } from './services/api';
import { ThemeProvider } from './contexts/ThemeContext';
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

// Import CRM pages
import CustomersPage from './pages/CustomersPage';
import LeadsPage from './pages/LeadsPage';
import OpportunitiesPage from './pages/OpportunitiesPage';

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
        // Get user profile from API
        const userData = await authService.getProfile();
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Error checking auth:', error);
        // If token is invalid, clear it and show login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_info');
        setIsAuthenticated(false);
      }
    }
    setLoading(false);
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
      localStorage.removeItem('user_info');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando aplicación...</p>
        </div>
      </div>
    );
  }

  return (
    <ThemeProvider>
      <div className="app">
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            {/* Public routes */}
            <Route path="/marketing" element={<MarketingPage />} />
            <Route path="/login" element={<LoginPage />} />
            
            {/* Protected routes */}
            {isAuthenticated ? (
              <>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <Dashboard />
                    </main>
                  </>
                } />
                
                {/* ...existing protected routes... */}
                <Route path="/products" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <ProductsPage />
                    </main>
                  </>
                } />
                <Route path="/categories" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <CategoriesPage />
                    </main>
                  </>
                } />
                <Route path="/suppliers" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <SuppliersPage />
                    </main>
                  </>
                } />
                <Route path="/inventory" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <InventoryPage />
                    </main>
                  </>
                } />
                <Route path="/transactions" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <TransactionsPage />
                    </main>
                  </>
                } />
                <Route path="/alerts" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <AlertsPage />
                    </main>
                  </>
                } />
                <Route path="/forecasting" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <ForecastingPage />
                    </main>
                  </>
                } />
                <Route path="/reports" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <ReportsPage />
                    </main>
                  </>
                } />
                <Route path="/settings" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <SettingsPage />
                    </main>
                  </>
                } />
                
                {/* CRM Routes */}
                <Route path="/customers" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <CustomersPage />
                    </main>
                  </>
                } />
                <Route path="/leads" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <LeadsPage />
                    </main>
                  </>
                } />
                <Route path="/opportunities" element={
                  <>
                    <Navbar user={user} onLogout={handleLogout} />
                    <main className="app-main">
                      <OpportunitiesPage />
                    </main>
                  </>
                } />
                
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </>
            ) : (
              <>
                {/* Redirect to login if not authenticated */}
                <Route path="/" element={<Navigate to="/login" replace />} />
                <Route path="*" element={<Navigate to="/login" replace />} />
              </>
            )}
          </Routes>
        </Router>
      </div>
    </ThemeProvider>
  );
};

export default App;
