import React from 'react';

interface StatsCardProps {
  title: string;
  value: string;
  icon: string;
  color: 'primary' | 'success' | 'warning' | 'info';
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color }) => {
  return (
    <div className={`stats-card stats-card-${color}`}>
      <div className="stats-card-icon">
        {icon}
      </div>
      <div className="stats-card-content">
        <h3 className="stats-card-value">{value}</h3>
        <p className="stats-card-title">{title}</p>
      </div>
    </div>
  );
};

export default StatsCard;
