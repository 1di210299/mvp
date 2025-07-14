import React from 'react';

interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
}

interface SelectTriggerProps {
  className?: string;
  children: React.ReactNode;
}

interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

interface SelectValueProps {
  placeholder?: string;
}

export const Select: React.FC<SelectProps> = ({ value, onValueChange, children }) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [selectedValue, setSelectedValue] = React.useState(value);

  React.useEffect(() => {
    setSelectedValue(value);
  }, [value]);

  const handleValueChange = (newValue: string) => {
    setSelectedValue(newValue);
    onValueChange?.(newValue);
    setIsOpen(false);
  };

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (isOpen && !target.closest('.select-container')) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div 
      className="relative select-container" 
      style={{ 
        zIndex: isOpen ? 999998 : 'auto',
        overflow: 'visible'
      }}
    >
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          if (child.type === SelectTrigger) {
            return React.cloneElement(child as any, {
              onClick: () => setIsOpen(!isOpen),
              'aria-expanded': isOpen,
              isOpen
            });
          }
          if (child.type === SelectContent && isOpen) {
            return React.cloneElement(child as any, {
              onValueChange: handleValueChange,
              selectedValue,
              key: 'select-content' // Forzar re-render cuando se abre
            });
          }
        }
        return null;
      })}
    </div>
  );
};

export const SelectTrigger: React.FC<SelectTriggerProps & { onClick?: () => void; isOpen?: boolean }> = ({ 
  className = '', 
  children, 
  onClick,
  isOpen = false
}) => {
  return (
    <button
      type="button"
      className={`
        flex h-12 w-full items-center justify-between 
        rounded-xl border-2 border-slate-200 bg-slate-50 
        px-4 py-3 text-sm font-medium text-slate-700
        shadow-sm transition-all duration-200
        hover:border-indigo-300 hover:bg-white hover:shadow-md
        focus:outline-none focus:ring-4 focus:ring-indigo-100 focus:border-indigo-400 focus:bg-white
        disabled:cursor-not-allowed disabled:opacity-50
        dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200
        dark:hover:border-indigo-400 dark:hover:bg-gray-600 dark:hover:shadow-md
        dark:focus:ring-indigo-500/20 dark:focus:border-indigo-400 dark:focus:bg-gray-600
        ${isOpen ? 'border-indigo-400 bg-white shadow-md ring-4 ring-indigo-100 dark:border-indigo-400 dark:bg-gray-600 dark:ring-indigo-500/20' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      <div className="flex items-center gap-2 flex-1 text-left">
        {children}
      </div>
      <svg 
        className={`h-5 w-5 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
};

export const SelectContent: React.FC<SelectContentProps & { 
  onValueChange?: (value: string) => void;
  selectedValue?: string;
}> = ({ children, onValueChange, selectedValue, className = '' }) => {
  const [position, setPosition] = React.useState<'bottom' | 'top'>('bottom');
  const contentRef = React.useRef<HTMLDivElement>(null);
  const [triggerRect, setTriggerRect] = React.useState<DOMRect | null>(null);
  
  React.useEffect(() => {
    // Recalcular la posición del trigger cada vez que se abre el dropdown
    const updateTriggerPosition = () => {
      const triggerElement = contentRef.current?.parentElement?.querySelector('button');
      if (triggerElement) {
        const rect = triggerElement.getBoundingClientRect();
        setTriggerRect(rect);
        
        const viewportHeight = window.innerHeight;
        const spaceBelow = viewportHeight - rect.bottom;
        const spaceAbove = rect.top;
        
        // Si hay más espacio arriba que abajo y no hay suficiente espacio abajo
        if (spaceBelow < 300 && spaceAbove > spaceBelow) {
          setPosition('top');
        } else {
          setPosition('bottom');
        }
      }
    };

    // Actualizar inmediatamente
    updateTriggerPosition();
    
    // También actualizar cuando se haga scroll o resize
    window.addEventListener('scroll', updateTriggerPosition);
    window.addEventListener('resize', updateTriggerPosition);
    
    return () => {
      window.removeEventListener('scroll', updateTriggerPosition);
      window.removeEventListener('resize', updateTriggerPosition);
    };
  }, []);

  // CORREGIDO: Calcular posición fija basada en la posición del trigger
  const getFixedPosition = () => {
    if (!triggerRect) return {};
    
    return {
      position: 'fixed' as const,
      top: position === 'bottom' ? triggerRect.bottom + 4 : 'auto',
      bottom: position === 'top' ? window.innerHeight - triggerRect.top + 4 : 'auto',
      left: triggerRect.left,
      width: triggerRect.width,
      zIndex: 999999,
      maxHeight: position === 'top' ? 
        Math.min(triggerRect.top - 16, 300) + 'px' : 
        Math.min(window.innerHeight - triggerRect.bottom - 16, 300) + 'px'
    };
  };

  return (
    <div 
      ref={contentRef}
      className={`
        min-w-[12rem] 
        overflow-visible rounded-xl border-2 border-slate-200 
        bg-white shadow-2xl backdrop-blur-sm
        ${position === 'bottom' ? 'select-content-bottom' : 'select-content-top'}
        dark:border-gray-600 dark:bg-gray-700 dark:shadow-2xl
        ${className}
      `}
      style={getFixedPosition()}
    >
      <div className="select-content-scroll max-h-full p-2" style={{ maxHeight: 'inherit' }}>
        {React.Children.map(children, child => {
          if (React.isValidElement(child) && child.type === SelectItem) {
            return React.cloneElement(child as any, {
              onSelect: onValueChange,
              isSelected: child.props.value === selectedValue
            });
          }
          return child;
        })}
      </div>
    </div>
  );
};

export const SelectItem: React.FC<SelectItemProps & { 
  onSelect?: (value: string) => void;
  isSelected?: boolean;
}> = ({ value, children, onSelect, isSelected, className = '' }) => {
  return (
    <div
      className={`
        relative flex w-full cursor-pointer select-none items-center 
        rounded-lg px-4 py-3 text-sm font-medium text-slate-700
        transition-all duration-150
        hover:bg-indigo-50 hover:text-indigo-700 hover:shadow-sm
        focus:bg-indigo-50 focus:text-indigo-700 focus:outline-none
        dark:text-gray-200 dark:hover:bg-indigo-900/30 dark:hover:text-indigo-300
        dark:focus:bg-indigo-900/30 dark:focus:text-indigo-300
        ${isSelected ? 'bg-indigo-100 text-indigo-800 shadow-sm dark:bg-indigo-900/40 dark:text-indigo-200' : ''}
        ${className}
      `}
      onClick={() => onSelect?.(value)}
    >
      {isSelected && (
        <span className="absolute left-2 flex h-4 w-4 items-center justify-center">
          <svg className="h-4 w-4 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
            <path 
              fillRule="evenodd" 
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" 
              clipRule="evenodd" 
            />
          </svg>
        </span>
      )}
      <div className={`flex items-center gap-2 ${isSelected ? 'ml-6' : ''}`}>
        {children}
      </div>
    </div>
  );
};

export const SelectValue: React.FC<SelectValueProps> = ({ placeholder }) => {
  return <span className="text-slate-500 font-normal dark:text-gray-400">{placeholder}</span>;
};
