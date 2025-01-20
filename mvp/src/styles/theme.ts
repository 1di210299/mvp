// src/types/theme.ts
export interface Theme {
    primary: string;
    accent1: string;
    accent2: string;
    surface: string;
    text: string;
    gradientMain: string;
    gradientAccent: string;
    gradientSurface: string;
  }
  
  // src/styles/theme.ts
  import { Theme } from '../types/theme';
  
  export const lightTheme: Theme = {
    primary: '#1A1B4B',
    accent1: '#00F0FF',
    accent2: '#B94FFF',
    surface: '#FFFFFF',
    text: '#0D0D2B',
    gradientMain: 'linear-gradient(135deg, #1A1B4B, #0D0D2B)',
    gradientAccent: 'linear-gradient(45deg, #00F0FF, #B94FFF)',
    gradientSurface: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.95))'
  };
  
  // src/components/Layout/Sidebar/styles.ts
  import styled from 'styled-components';
  
  export const SidebarContainer = styled.aside`
    background: ${({ theme }) => theme.gradientMain};
    width: 280px;
    height: 100vh;
    padding: 2rem;
    transition: all 0.3s ease;
    
    .logo {
      margin-bottom: 2rem;
      h1 {
        color: ${({ theme }) => theme.accent1};
      }
    }
  `;
  
  // src/components/Layout/Sidebar/index.tsx
  import React from 'react';
  import { useNavigate } from 'react-router-dom';
  import { SidebarContainer } from './styles';
  import { MenuItem } from '../../../types/menu';
  
  const menuItems: MenuItem[] = [
    { id: 'dashboard', icon: '📊', label: 'Dashboard', path: '/' },
    { id: 'analysis', icon: '📈', label: 'Análisis Exploratorio', path: '/analysis' },
    { id: 'predictions', icon: '🔮', label: 'Predicciones', path: '/predictions' },
    { id: 'ml', icon: '🤖', label: 'Machine Learning', path: '/ml' },
    { id: 'reports', icon: '📑', label: 'Reportes', path: '/reports' },
    { id: 'settings', icon: '⚙️', label: 'Configuración', path: '/settings' }
  ];
  
  // src/components/Dashboard/index.tsx
  import React from 'react';
  import { DashboardContainer, MetricCard } from './styles';
  import { motion } from 'framer-motion';
  
  export const Dashboard: React.FC = () => {
    return (
      <DashboardContainer>
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="metrics-grid"
        >
          <MetricCard>
            <h3>Ventas Totales</h3>
            <h2>$1.2M</h2>
            <p className="trend positive">↑ 12%</p>
          </MetricCard>
          {/* Más métricas */}
        </motion.div>
      </DashboardContainer>
    );
  };
  
  // src/hooks/useData.ts
  import { useQuery } from '@tanstack/react-query';
  import { fetchDashboardData } from '../services/api';
  
  export const useDashboardData = () => {
    return useQuery({
      queryKey: ['dashboardData'],
      queryFn: fetchDashboardData,
    });
  };
  
  // src/services/api.ts
  import axios from 'axios';
  
  const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL
  });
  
  export const fetchDashboardData = async () => {
    const response = await api.get('/dashboard');
    return response.data;
  };