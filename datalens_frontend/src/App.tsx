import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import Dashboard from './components/Dashboard/Dashboard';
import Navbar from './components/Navbar/Navbar';
import MarketingPage from './pages/MarketingPage';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
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
import DataImportPage from './pages/DataImportPage';

// Import CRM pages
import CustomersPage from './pages/CustomersPage';
import LeadsPage from './pages/LeadsPage';
import OpportunitiesPage from './pages/OpportunitiesPage';

// Componente interno que usa el contexto de autenticación
const AppContent: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  if (isLoading) {
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
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <Dashboard />
                </main>
              </>
            } />
            
            <Route path="/products" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <ProductsPage />
                </main>
              </>
            } />
            <Route path="/categories" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <CategoriesPage />
                </main>
              </>
            } />
            <Route path="/suppliers" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <SuppliersPage />
                </main>
              </>
            } />
            <Route path="/inventory" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <InventoryPage />
                </main>
              </>
            } />
            <Route path="/transactions" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <TransactionsPage />
                </main>
              </>
            } />
            <Route path="/alerts" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <AlertsPage />
                </main>
              </>
            } />
            <Route path="/forecasting" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <ForecastingPage />
                </main>
              </>
            } />
            <Route path="/reports" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <ReportsPage />
                </main>
              </>
            } />
            <Route path="/settings" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <SettingsPage />
                </main>
              </>
            } />
            <Route path="/data-import" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <DataImportPage />
                </main>
              </>
            } />
            
            {/* CRM Routes */}
            <Route path="/customers" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <CustomersPage />
                </main>
              </>
            } />
            <Route path="/leads" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <LeadsPage />
                </main>
              </>
            } />
            <Route path="/opportunities" element={
              <>
                <Navbar user={user} onLogout={logout} />
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
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <div className="app">
          <AppContent />
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
