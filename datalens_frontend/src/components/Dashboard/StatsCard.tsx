import React from 'react';

interface StatsCardProps {
  title: string;
  value: string;
  icon: string;
  color: 'primary' | 'success' | 'warning' | 'info';
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color }) => {
  return (
    <div className={`stats-card stats-card-${color} hover-lift animate-fade-in`}>
      <div className="stats-card-icon icon-with-bg">
        <span style={{ fontSize: '1.5rem' }}>{icon}</span>
      </div>
      <div className="stats-card-content">
        <h3 className="stats-value">{value}</h3>
        <p className="stats-label">{title}</p>
      </div>
    </div>
  );
};

export default StatsCard;
