import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Layouts
import HomeLayout from './layouts/HomeLayout';
import DashboardLayout from './layouts/DashboardLayout';

// Páginas
import HomePage from './pages/HomePage';
import DatasetsPage from './pages/DatasetsPage';
import DatasetDetailPage from './pages/DatasetDetailPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Sección SIN sidebar */}
        <Route element={<HomeLayout />}>
          <Route path="/" element={<HomePage />} />
          {/* Si quisieras más rutas sin sidebar, agrégalas aquí */}
        </Route>

        {/* Sección CON sidebar */}
        <Route element={<DashboardLayout />}>
          <Route path="/datasets" element={<DatasetsPage />} />
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
          {/* Rutas adicionales del dashboard */}
          <Route path="/experiments" element={<div className="p-4 text-white">Experiments Page</div>} />
          <Route path="/models" element={<div className="p-4 text-white">Models Page</div>} />
          <Route path="/settings" element={<div className="p-4 text-white">Settings Page</div>} />
        </Route>

        {/* Ruta para manejar páginas no encontradas */}
        <Route path="*" element={
          <div className="flex items-center justify-center h-screen bg-cyber-dark">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-cyber-cyan mb-4">404</h1>
              <p className="text-white mb-6">Página no encontrada</p>
              <a href="/" className="px-4 py-2 bg-cyber-cyan text-cyber-dark rounded hover:bg-cyan-300">
                Volver al inicio
              </a>
            </div>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;