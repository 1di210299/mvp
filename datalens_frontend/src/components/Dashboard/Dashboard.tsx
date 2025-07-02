import React, { useState, useEffect } from 'react';
import { DashboardStats } from '../../types';
import { dashboardService } from '../../services/api';
import StatsCard from './StatsCard';
import InventoryChart from './InventoryChart';
import RecentTransactions from './RecentTransactions';
import AlertsList from './AlertsList';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Cargar datos reales desde la API
      const dashboardData = await dashboardService.getStats();
      setStats(dashboardData);
      
    } catch (err: any) {
      setError('Error al cargar los datos del dashboard');
      console.error(err);
      
      // En caso de error, mostrar datos básicos
      const fallbackStats: DashboardStats = {
        total_products: 0,
        total_value: 0,
        low_stock_alerts: 0,
        total_transactions_today: 0,
        top_products: [],
        stock_levels: []
      };
      setStats(fallbackStats);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Cargando dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <p>{error}</p>
        <button onClick={loadDashboardData} className="btn btn-primary">
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Dashboard</h1>
        <p className="dashboard-subtitle">
          Resumen general de tu inventario
        </p>
      </div>

      {stats && (
        <>
          {/* Stats Cards */}
          <div className="stats-grid">
            <StatsCard
              title="Total Productos"
              value={stats.total_products.toLocaleString()}
              icon="📦"
              color="primary"
            />
            <StatsCard
              title="Valor Total"
              value={`S/ ${stats.total_value.toLocaleString()}`}
              icon="💰"
              color="success"
            />
            <StatsCard
              title="Alertas de Stock"
              value={stats.low_stock_alerts.toString()}
              icon="⚠️"
              color="warning"
            />
            <StatsCard
              title="Transacciones Hoy"
              value={stats.total_transactions_today.toString()}
              icon="📊"
              color="info"
            />
          </div>

          {/* Charts and Lists */}
          <div className="dashboard-content">
            <div className="dashboard-left">
              <InventoryChart data={stats.stock_levels} />
              <RecentTransactions />
            </div>
            
            <div className="dashboard-right">
              <AlertsList />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
