// HomeLayout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';

function HomeLayout() {
  return (
    <div className="flex flex-col min-h-screen bg-transparent">
      <Header />
      <main className="flex-1 p-4 bg-transparent">
        <Outlet />
      </main>
    </div>
  );
}

export default HomeLayout;
