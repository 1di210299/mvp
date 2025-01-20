// src/context/AppContext.tsx
import React, { createContext, useContext, useState } from 'react';
import { Theme } from '../types/theme';
import { lightTheme, darkTheme } from '../styles/theme';

interface AppContextType {
  theme: Theme;
  toggleTheme: () => void;
  sidebarExpanded: boolean;
  toggleSidebar: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [sidebarExpanded, setSidebarExpanded] = useState(true);

  const toggleTheme = () => setIsDarkMode(!isDarkMode);
  const toggleSidebar = () => setSidebarExpanded(!sidebarExpanded);

  const value = {
    theme: isDarkMode ? darkTheme : lightTheme,
    toggleTheme,
    sidebarExpanded,
    toggleSidebar,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};