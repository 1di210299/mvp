// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';

// Importar la página de inicio original
import HomePage from './pages/HomePage';

// Importar el layout del dashboard
import DashboardLayout from './layouts/DashboardLayout';

function App() {
  return (
    <Router>
      <Routes>
        {/* La ruta principal muestra directamente tu HomePage.tsx original */}
        <Route path="/" element={<HomePage />} />
        
        {/* Todas las rutas del dashboard están dentro del layout */}
        <Route path="/dashboard/*" element={<DashboardLayout />} />
        
        {/* Redirecciones para URLs más cortas */}
        <Route path="/ventas" element={<Navigate to="/dashboard/ventas" replace />} />
        <Route path="/clientes" element={<Navigate to="/dashboard/clientes" replace />} />
        <Route path="/predicciones" element={<Navigate to="/dashboard/predicciones" replace />} />
        <Route path="/datasets" element={<Navigate to="/dashboard/datasets" replace />} />
        <Route path="/datasets/:id" element={<Navigate to={`/dashboard/datasets/${window.location.pathname.split('/').pop()}`} replace />} />
        <Route path="/reportes" element={<Navigate to="/dashboard/reportes" replace />} />
        <Route path="/calendarios" element={<Navigate to="/dashboard/calendarios" replace />} />
        <Route path="/ajustes" element={<Navigate to="/dashboard/ajustes" replace />} />
        
        {/* Ruta por defecto para manejar URLs no existentes */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;