// src/components/UserMenu.tsx
import React, { useState, useRef, useEffect } from 'react';
import { LogOut, Settings, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface UserMenuProps {
  /** Nombre completo, por ejemplo "Juan Diego" */
  name?: string;
  /** Si quieres pasarle iniciales directamente, p.e. "JD" */
  initials?: string;
}

/** Función para extraer iniciales de un nombre, p.e. "Juan Diego" => "JD" */
function getInitialsFromName(name: string): string {
  const parts = name.split(' ');
  const initials = parts.map((p) => p[0].toUpperCase()).join('');
  return initials;
}

const UserMenu: React.FC<UserMenuProps> = ({ name, initials }) => {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Cierra el menú si se hace clic fuera
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Calcula las iniciales
  const displayInitials = initials || (name ? getInitialsFromName(name) : 'JD');

  return (
    <div className="relative" ref={menuRef}>
      {/* Avatar circular con marco y sombra */}
      <button
        onClick={() => setOpen(!open)}
        className="
          flex items-center justify-center 
          w-10 h-10 
          rounded-full 
          bg-[#00E6E6]/80 
          text-[#E6E6E6] 
          border border-[#E6E6E6]/60 
          shadow-md 
          hover:bg-[#00E6E6]/90 
          focus:outline-none 
          focus:ring-2 
          focus:ring-[#00E6E6]/50 
          cursor-pointer
        "
        aria-label="Open user menu"
      >
        {displayInitials}
      </button>

      {/* Dropdown con animación */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute right-0 mt-2 w-48 bg-[#003737] rounded shadow-md overflow-hidden z-50"
          >
            <button className="w-full text-left px-4 py-2 text-sm flex items-center transition-colors hover:bg-[#004f5f] text-[#E6E6E6]">
              <Settings size={16} className="mr-2" />
              Settings
            </button>
            <button className="w-full text-left px-4 py-2 text-sm flex items-center transition-colors hover:bg-[#004f5f] text-[#E6E6E6]">
              <User size={16} className="mr-2" />
              Profile
            </button>
            <div className="border-t border-gray-700 my-1" />
            <button
              onClick={() => alert('Logging out...')}
              className="w-full text-left px-4 py-2 text-sm flex items-center text-red-400 transition-colors hover:bg-[#004f5f]"
            >
              <LogOut size={16} className="mr-2" />
              Logout
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default UserMenu;
