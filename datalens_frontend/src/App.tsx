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
import AlertRecipientsPage from './pages/AlertRecipientsPage';
import ForecastingPage from './pages/ForecastingPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';
import InventoryPage from './pages/InventoryPage';
import DataImportPage from './pages/DataImportPage';

// Import CRM pages
import CustomersPage from './pages/CustomersPage';
import LeadsPage from './pages/LeadsPage';
import OpportunitiesPage from './pages/OpportunitiesPage';

// Import WhatsApp Configuration page
import WhatsAppSettingsPage from './pages/WhatsAppSettingsPage';

// Componente interno que usa el contexto de autenticación
const AppContent: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  // Debug logging
  console.log('🔍 App State:', { 
    isAuthenticated, 
    isLoading, 
    user: user?.email || 'null',
    token: localStorage.getItem('access_token') ? 'exists' : 'none'
  });

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
        {/* Public routes - Marketing page as default */}
        <Route path="/" element={<MarketingPage />} />
        <Route path="/marketing" element={<MarketingPage />} />
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        {isAuthenticated ? (
          <>
            <Route path="/app" element={<Navigate to="/app/dashboard" replace />} />
            <Route path="/app/dashboard" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <Dashboard />
                </main>
              </>
            } />
            
            <Route path="/app/products" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <ProductsPage />
                </main>
              </>
            } />
            <Route path="/app/categories" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <CategoriesPage />
                </main>
              </>
            } />
            <Route path="/app/suppliers" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <SuppliersPage />
                </main>
              </>
            } />
            <Route path="/app/inventory" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <InventoryPage />
                </main>
              </>
            } />
            <Route path="/app/transactions" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <TransactionsPage />
                </main>
              </>
            } />
            <Route path="/app/alerts" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <AlertsPage />
                </main>
              </>
            } />
            <Route path="/app/alerts/recipients" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <AlertRecipientsPage />
                </main>
              </>
            } />
            <Route path="/app/forecasting" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <ForecastingPage />
                </main>
              </>
            } />
            <Route path="/app/reports" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <ReportsPage />
                </main>
              </>
            } />
            <Route path="/app/settings" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <SettingsPage />
                </main>
              </>
            } />
            <Route path="/app/data-import" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <DataImportPage />
                </main>
              </>
            } />
            
            {/* CRM Routes */}
            <Route path="/app/customers" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <CustomersPage />
                </main>
              </>
            } />
            <Route path="/app/leads" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <LeadsPage />
                </main>
              </>
            } />
            <Route path="/app/opportunities" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <OpportunitiesPage />
                </main>
              </>
            } />
            
            {/* WhatsApp Configuration Route */}
            <Route path="/app/whatsapp" element={
              <>
                <Navbar user={user} onLogout={logout} />
                <main className="app-main">
                  <WhatsAppSettingsPage />
                </main>
              </>
            } />
          </>
        ) : (
          <>
            {/* Redirect authenticated routes to marketing if not logged in */}
            <Route path="/app/*" element={<Navigate to="/marketing" replace />} />
            <Route path="/dashboard" element={<Navigate to="/marketing" replace />} />
            <Route path="/products" element={<Navigate to="/marketing" replace />} />
            <Route path="/categories" element={<Navigate to="/marketing" replace />} />
            <Route path="/suppliers" element={<Navigate to="/marketing" replace />} />
            <Route path="/inventory" element={<Navigate to="/marketing" replace />} />
            <Route path="/transactions" element={<Navigate to="/marketing" replace />} />
            <Route path="/alerts" element={<Navigate to="/marketing" replace />} />
            <Route path="/forecasting" element={<Navigate to="/marketing" replace />} />
            <Route path="/reports" element={<Navigate to="/marketing" replace />} />
            <Route path="/settings" element={<Navigate to="/marketing" replace />} />
            <Route path="/data-import" element={<Navigate to="/marketing" replace />} />
            <Route path="/customers" element={<Navigate to="/marketing" replace />} />
            <Route path="/leads" element={<Navigate to="/marketing" replace />} />
            <Route path="/opportunities" element={<Navigate to="/marketing" replace />} />
            <Route path="/whatsapp" element={<Navigate to="/marketing" replace />} />
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
