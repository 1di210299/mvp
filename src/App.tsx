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
          {/* Agrega más rutas con sidebar si lo requieres */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
