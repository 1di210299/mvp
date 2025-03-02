// src/components/Header.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import UserMenu from './UserMenu';

function Header() {
  const navigate = useNavigate();

  return (
    <header className="w-full bg-transparent shadow flex items-center justify-between px-4 py-2">
      {/* LOGO O TÍTULO */}
      <div className="flex items-center">
        <h1
          className="text-xl font-bold text-black cursor-pointer hover:text-blue-600 transition-colors"
          onClick={() => navigate('/')}
        >
          ANNEX AI
        </h1>
      </div>

      {/* SECCIÓN DERECHA (UserMenu) */}
      <div className="flex items-center space-x-4">
        <UserMenu name="Juan Diego" />
      </div>
    </header>
  );
}

export default Header;
