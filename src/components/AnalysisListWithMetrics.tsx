// src/components/AnalysisListWithMetrics.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
  YAxis,
  XAxis,
} from 'recharts';
import { BarChart, Users, Package, Calendar, TrendingUp } from 'lucide-react';

function AnalysisListWithMetrics() {
  const navigate = useNavigate();

  // Diferentes análisis basados en el mismo dataset
  const analysisList = [
    {
      id: 1,
      name: 'Ventas Mensuales',
      description: 'Análisis de tus ventas por mes',
      icon: <BarChart size={18} className="text-cyber-cyan" />,
      route: 'ventas-mensuales',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
    {
      id: 2,
      name: 'Segmentación de Clientes',
      description: 'Análisis por distrito y categoría',
      icon: <Users size={18} className="text-blue-400" />,
      route: 'segmentacion-clientes',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
    {
      id: 3,
      name: 'Inventario y Rotación',
      description: 'Stock y rotación de tus productos',
      icon: <Package size={18} className="text-green-400" />,
      route: 'inventario-rotacion',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
    {
      id: 4,
      name: 'Campañas Comerciales',
      description: 'Desempeño de tus campañas',
      icon: <Calendar size={18} className="text-purple-400" />,
      route: 'campanas-comerciales',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
    {
      id: 5,
      name: 'Proyecciones 2025',
      description: 'Estimación de tus ventas futuras',
      icon: <TrendingUp size={18} className="text-yellow-400" />,
      route: 'proyecciones',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
  ];

  const handleAnalysisClick = (route: string) => {
    navigate(`/dashboard/${route}`);
  };

  return (
    <div className="space-y-4">
      {analysisList.map((analysis) => (
        <motion.div
          key={analysis.id}
          className="flex items-center justify-between border-b border-gray-600/30 pb-3 last:border-none cursor-pointer hover:bg-black/30 transition-colors duration-200 p-2 rounded"
          whileHover={{ scale: 1.02 }}
          onClick={() => handleAnalysisClick(analysis.route)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleAnalysisClick(analysis.route);
            }
          }}
        >
          <div className="flex items-center">
            <div className="p-2 rounded-full bg-cyber-detail/30 mr-3">
              {analysis.icon}
            </div>
            <div>
              <p className="font-medium text-white text-base">{analysis.name}</p>
              <p className="text-xs text-gray-300">{analysis.description}</p>
            </div>
          </div>
          <div className="w-40 h-16">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analysis.metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                <Tooltip
                  formatter={(value: number) => [`${value}`, 'Valor']}
                  cursor={{ stroke: '#1C3D5A' }}
                />
                <XAxis hide />
                <YAxis hide />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#00E6E6"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export default AnalysisListWithMetrics;