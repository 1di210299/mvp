import React from 'react';

interface AlertProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'destructive' | 'warning' | 'success';
}

export const Alert: React.FC<AlertProps> = ({
  children,
  className = '',
  variant = 'default'
}) => {
  const baseClasses = 'relative w-full rounded-lg border p-4';
  
  const variantClasses = {
    default: 'bg-white border-gray-200 text-gray-900 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
    destructive: 'bg-red-50 border-red-200 text-red-900 dark:bg-red-900/20 dark:border-red-800 dark:text-red-100',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-900 dark:bg-yellow-900/20 dark:border-yellow-700 dark:text-yellow-100',
    success: 'bg-green-50 border-green-200 text-green-900 dark:bg-green-900/20 dark:border-green-700 dark:text-green-100'
  };
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${className}`;
  
  return (
    <div className={classes} role="alert">
      {children}
    </div>
  );
};

interface AlertDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const AlertDescription: React.FC<AlertDescriptionProps> = ({
  children,
  className = ''
}) => {
  return (
    <div className={`text-sm [&_p]:leading-relaxed ${className}`}>
      {children}
    </div>
  );
};
