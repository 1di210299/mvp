import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { Sun, Moon, Monitor } from '../ui/icons';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
  variant?: 'icon' | 'button' | 'dropdown';
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  className = '', 
  showLabel = false,
  variant = 'icon'
}) => {
  const { theme, actualTheme, setTheme } = useTheme();

  const themes = [
    { value: 'light' as const, label: 'Claro', icon: Sun },
    { value: 'dark' as const, label: 'Oscuro', icon: Moon },
    { value: 'system' as const, label: 'Sistema', icon: Monitor },
  ];

  if (variant === 'dropdown') {
    return (
      <div className={`theme-toggle-dropdown ${className}`}>
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
          Tema de la aplicación
        </label>
        <div className="grid grid-cols-3 gap-2">
          {themes.map((themeOption) => {
            const Icon = themeOption.icon;
            const isActive = theme === themeOption.value;
            
            return (
              <button
                key={themeOption.value}
                onClick={() => setTheme(themeOption.value)}
                className={`
                  flex flex-col items-center gap-2 p-3 rounded-lg border transition-all duration-200
                  ${isActive 
                    ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-400' 
                    : 'border-gray-200 hover:border-gray-300 text-gray-600 dark:border-gray-600 dark:text-gray-400 dark:hover:border-gray-500'
                  }
                `}
              >
                <Icon size={20} />
                <span className="text-xs font-medium">{themeOption.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  if (variant === 'button') {
    const currentTheme = themes.find(t => t.value === theme);
    const Icon = currentTheme?.icon || Sun;
    
    return (
      <button
        onClick={() => {
          const currentIndex = themes.findIndex(t => t.value === theme);
          const nextIndex = (currentIndex + 1) % themes.length;
          setTheme(themes[nextIndex].value);
        }}
        className={`
          theme-toggle-button inline-flex items-center gap-2 px-3 py-2 
          bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 
          rounded-lg shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 
          transition-all duration-200 text-sm font-medium
          text-gray-700 dark:text-gray-300 ${className}
        `}
        title={`Cambiar tema (actual: ${currentTheme?.label})`}
      >
        <Icon size={16} />
        {showLabel && <span>{currentTheme?.label}</span>}
      </button>
    );
  }

  // Variant 'icon' (default)
  const currentIcon = actualTheme === 'dark' ? Moon : Sun;
  const CurrentIcon = currentIcon;

  return (
    <button
      onClick={() => {
        if (theme === 'system') {
          setTheme('light');
        } else if (theme === 'light') {
          setTheme('dark');
        } else {
          setTheme('light');
        }
      }}
      className={`
        theme-toggle-icon relative w-10 h-10 rounded-lg 
        bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700
        border border-gray-200 dark:border-gray-600
        flex items-center justify-center transition-all duration-300 
        text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white
        ${className}
      `}
      title={`Cambiar a modo ${actualTheme === 'dark' ? 'claro' : 'oscuro'}`}
    >
      <CurrentIcon 
        size={18} 
        className={`transition-transform duration-300 ${
          actualTheme === 'dark' ? 'rotate-0' : 'rotate-180'
        }`}
      />
    </button>
  );
};