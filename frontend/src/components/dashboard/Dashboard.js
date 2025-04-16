import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Paper
} from '@mui/material';
import {
  BarChart as BarChartIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Warning as WarningIcon,
  Security as SecurityIcon,
  ShoppingCart as ShoppingCartIcon
} from '@mui/icons-material';
import { Line, Bar } from 'react-chartjs-2';
import { Chart as ChartJS, registerables } from 'chart.js';
import { fetchDashboardStats } from '../../store/dashboardSlice';
import { formatCurrency } from '../../utils/formats';

// Registrar componentes de Chart.js
ChartJS.register(...registerables);

const StatCard = ({ title, value, icon, color }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Grid container spacing={3} alignItems="center">
        <Grid item>
          <Box
            sx={{
              backgroundColor: `${color}.light`,
              borderRadius: 2,
              p: 1,
              display: 'flex',
            }}
          >
            {icon}
          </Box>
        </Grid>
        <Grid item xs>
          <Typography variant="h5" component="div">
            {value}
          </Typography>
          <Typography color="text.secondary">
            {title}
          </Typography>
        </Grid>
      </Grid>
    </CardContent>
  </Card>
);

const IncidentSeverityChip = ({ severity }) => {
  const color = {
    low: 'success',
    medium: 'warning',
    high: 'error'
  }[severity] || 'default';

  return <Chip size="small" color={color} label={severity.toUpperCase()} />;
};

export default function Dashboard() {
  const dispatch = useDispatch();
  const { 
    data, 
    isLoading, 
    error 
  } = useSelector((state) => state.dashboard);
  
  useEffect(() => {
    dispatch(fetchDashboardStats());
  }, [dispatch]);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', pt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">Error: {error}</Typography>
      </Box>
    );
  }

  // Datos para el gráfico de ventas por día
  const salesChartData = {
    labels: data?.sales_chart?.map(item => item.date) || [],
    datasets: [
      {
        label: 'Ventas',
        data: data?.sales_chart?.map(item => item.total) || [],
        fill: false,
        backgroundColor: 'rgba(37, 211, 102, 0.2)',
        borderColor: '#25D366',
        tension: 0.2
      }
    ]
  };

  // Datos para el gráfico de productos más vendidos
  const topProductsChartData = {
    labels: data?.top_products?.map(item => item.name) || [],
    datasets: [
      {
        label: 'Unidades vendidas',
        data: data?.top_products?.map(item => item.total_sold) || [],
        backgroundColor: '#128C7E',
      }
    ]
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total Clientes" 
            value={data?.total_customers || 0} 
            icon={<PeopleIcon sx={{ color: 'primary.main' }} />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total Ventas" 
            value={formatCurrency(data?.total_sales || 0)} 
            icon={<TrendingUpIcon sx={{ color: 'success.main' }} />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Órdenes Hoy" 
            value={data?.orders_today || 0} 
            icon={<ShoppingCartIcon sx={{ color: 'info.main' }} />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Incidentes Activos" 
            value={data?.active_incidents || 0} 
            icon={<SecurityIcon sx={{ color: 'warning.main' }} />}
            color="warning"
          />
        </Grid>
      </Grid>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Ventas recientes
              </Typography>
              <Box sx={{ height: 300 }}>
                <Line 
                  data={salesChartData} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'top',
                      },
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Productos más vendidos
              </Typography>
              <Box sx={{ height: 300 }}>
                <Bar 
                  data={topProductsChartData} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                      legend: {
                        display: false,
                      },
                    },
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <WarningIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Incidentes de seguridad recientes
                </Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List>
                {(data?.recent_incidents || []).length > 0 ? (
                  data.recent_incidents.map((incident) => (
                    <ListItem key={incident.id} divider>
                      <ListItemIcon>
                        <SecurityIcon color="error" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="body1">{incident.type}</Typography>
                            <IncidentSeverityChip severity={incident.severity} />
                          </Box>
                        }
                        secondary={`Teléfono: ${incident.phone_number} • ${new Date(incident.timestamp).toLocaleString()}`}
                      />
                    </ListItem>
                  ))
                ) : (
                  <ListItem>
                    <ListItemText primary="No hay incidentes recientes" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Órdenes recientes
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <List>
                {(data?.recent_orders || []).length > 0 ? (
                  data.recent_orders.map((order) => (
                    <ListItem key={order.id} divider>
                      <ListItemIcon>
                        <ShoppingCartIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="body1">Orden #{order.id}</Typography>
                            <Chip 
                              size="small" 
                              color={order.status === 'completed' ? 'success' : 'warning'} 
                              label={order.status.toUpperCase()} 
                            />
                          </Box>
                        }
                        secondary={`Cliente: ${order.customer_name} • Total: ${formatCurrency(order.total_amount)}`}
                      />
                    </ListItem>
                  ))
                ) : (
                  <ListItem>
                    <ListItemText primary="No hay órdenes recientes" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}