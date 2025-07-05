import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'destructive';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  className = '',
  variant = 'primary'
}) => {
  const baseClasses = 'badge animate-fade-in';
  
  const variantClasses = {
    primary: 'badge-primary',
    secondary: 'badge-secondary',
    success: 'badge-success',
    warning: 'badge-warning',
    danger: 'badge-destructive',
    destructive: 'badge-destructive'
  };
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${className}`;
  
  return (
    <span className={classes}>
      {children}
    </span>
  );
};
