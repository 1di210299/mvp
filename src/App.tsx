// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DatasetDetailPage from './pages/DatasetDetailPage';
import DatasetsPage from './pages/DatasetsPage';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardVentas from './components/DashboardVentas';
import VentasChart from './components/VentasChart';
import SegmentacionClientes from './components/SegmentacionClientes';
import PrediccionesVentas from './components/PrediccionesVentas';
import ReportesVentas from './components/ReportesVentas';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Rutas públicas */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Rutas protegidas */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            <Route index element={<HomePage />} />
            <Route path="datasets" element={<DatasetsPage />} />
            <Route path="datasets/:id" element={<DatasetDetailPage />} />
            <Route path="ventas" element={<DashboardVentas />} />
            <Route path="charts" element={<VentasChart />} />
            <Route path="clientes" element={<SegmentacionClientes />} />
            <Route path="predicciones" element={<PrediccionesVentas />} />
            <Route path="reportes" element={<ReportesVentas />} />
          </Route>
          
          {/* Redirecciones */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;