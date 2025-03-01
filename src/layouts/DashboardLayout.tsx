// DashboardLayout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';

function DashboardLayout() {
  return (
    <div className="flex flex-col min-h-screen bg-transparent">
      <Header />
      <div className="flex flex-1">
        {/* SIDEBAR */}
        <aside className="w-64 p-4 bg-transparent">
          <nav className="space-y-2">
            <a className="block px-2 py-1 hover:bg-gray-300" href="/datasets">
              Datasets
            </a>
            {/* ... */}
          </nav>
        </aside>

        <main className="flex-1 p-4 bg-transparent">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
