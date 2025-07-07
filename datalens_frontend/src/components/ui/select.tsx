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
    <div className="relative select-container">
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
              selectedValue
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
        ${isOpen ? 'border-indigo-400 bg-white shadow-md ring-4 ring-indigo-100' : ''}
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
  return (
    <div className={`
      absolute top-full left-0 z-50 w-full min-w-[12rem] 
      mt-2 overflow-hidden rounded-xl border-2 border-slate-200 
      bg-white shadow-2xl backdrop-blur-sm
      animate-in fade-in-0 zoom-in-95 duration-200
      ${className}
    `}>
      <div className="max-h-[300px] overflow-auto p-2">
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
        ${isSelected ? 'bg-indigo-100 text-indigo-800 shadow-sm' : ''}
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
  return <span className="text-slate-500 font-normal">{placeholder}</span>;
};
