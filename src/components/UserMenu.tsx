// src/components/UserMenu.tsx

import React, { useState, useRef, useEffect } from 'react';
import { LogOut, Settings, User } from 'lucide-react'; 
// ↑ Instala lucide-react si no lo tienes: npm install lucide-react

interface UserMenuProps {
  /** Nombre completo, por ejemplo "Juan Diego" */
  name?: string;  
  /** Si quieres pasarle iniciales directamente, p.e. "JD" */
  initials?: string;
}

/** Función para extraer iniciales de un nombre, p.e. "Juan Diego" => "JD" */
function getInitialsFromName(name: string): string {
  const parts = name.split(' ');
  const initials = parts.map(p => p[0].toUpperCase()).join('');
  return initials;
}

const UserMenu: React.FC<UserMenuProps> = ({ name, initials }) => {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Cerrar el menú si hacemos clic fuera
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Si no pasan "initials", calculamos desde el "name"
  const displayInitials = initials || (name ? getInitialsFromName(name) : 'JD');

  return (
    <div className="relative" ref={menuRef}>
      {/* Avatar circular */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white hover:bg-blue-700 focus:outline-none"
      >
        {displayInitials}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded shadow-md overflow-hidden z-50">
          <button className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center">
            <Settings size={16} className="mr-2" />
            Settings
          </button>
          <button className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center">
            <User size={16} className="mr-2" />
            Profile
          </button>
          <div className="border-t my-1"></div>
          <button
            className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center text-red-600"
            onClick={() => alert('Logging out...')}
          >
            <LogOut size={16} className="mr-2" />
            Logout
          </button>
        </div>
      )}
    </div>
  );
};

export default UserMenu;
