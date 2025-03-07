// src/components/DatasetListWithMetrics.tsx
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

function DatasetListWithMetrics() {
  const navigate = useNavigate();

  // Datos actualizados con nombres relevantes para ventas de MYPES peruanas
  const datasetList = [
    {
      id: 1,
      name: 'Ventas Mensuales 2025',
      description: 'Análisis de ventas por mes',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
    {
      id: 2,
      name: 'Segmentación Clientes Lima',
      description: 'Clientes por distrito y categoría',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
    {
      id: 3,
      name: 'Inventario Productos Q1',
      description: 'Stock y rotación de productos',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
    {
      id: 4,
      name: 'Campañas Fiestas Patrias',
      description: 'Resultados de campañas 2024',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
    {
      id: 5,
      name: 'Proyección Ventas 2025',
      description: 'Estimación de ventas por trimestre',
      metrics: Array.from({ length: 5 }, () => ({
        value: Math.floor(Math.random() * 50) + 10,
      })),
    },
  ];

  const handleDatasetClick = (datasetId: number) => {
    navigate(`/dashboard/datasets/${datasetId}`);
  };

  return (
    <div className="space-y-4">
      {datasetList.map((ds) => (
        <motion.div
          key={ds.id}
          className="flex items-center justify-between border-b border-gray-600/30 pb-3 last:border-none cursor-pointer hover:bg-black/30 transition-colors duration-200 p-2 rounded"
          whileHover={{ scale: 1.02 }}
          onClick={() => handleDatasetClick(ds.id)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleDatasetClick(ds.id);
            }
          }}
        >
          <div>
            <p className="font-medium text-white text-base">{ds.name}</p>
            <p className="text-xs text-gray-300">{ds.description}</p>
          </div>
          <div className="w-40 h-16">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={ds.metrics}>
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

export default DatasetListWithMetrics;