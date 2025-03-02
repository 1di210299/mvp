// src/layouts/DashboardLayout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';

function DashboardLayout() {
  return (
    <div className="flex flex-col min-h-screen text-[#E6E6E6]">
      <Header />
      <div className="flex flex-1">
        {/* SIDEBAR */}
        <aside className="w-64 p-4 bg-[#00E6E6]/10 border-r border-[#00E6E6]/50">
          <nav className="space-y-2">
            <a
              href="/datasets"
              className="
                block 
                px-2 
                py-1 
                rounded 
                transition-colors 
                hover:bg-[#00E6E6]/20
              "
            >
              Datasets
            </a>
            {/* Agrega más enlaces de navegación aquí */}
          </nav>
        </aside>

        {/* CONTENIDO PRINCIPAL */}
        <main className="flex-1 p-4 bg-transparent">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
