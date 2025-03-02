// src/layouts/HomeLayout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';

function HomeLayout() {
  return (
    <div className="flex flex-col min-h-screen text-[#E6E6E6]">
      <Header />
      <main className="flex-1 p-4 bg-[#00E6E6]/10">
        <Outlet />
      </main>
    </div>
  );
}

export default HomeLayout;
