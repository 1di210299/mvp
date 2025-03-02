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

  const datasetList = Array.from({ length: 5 }, (_, i) => ({
    id: i + 1, // ID único para cada dataset
    name: `Dataset ${i + 1}`,
    metrics: Array.from({ length: 5 }, () => ({
      value: Math.floor(Math.random() * 50) + 10,
    })),
  }));

  const handleDatasetClick = (datasetId: number) => {
    navigate(`/datasets/${datasetId}`);
  };

  return (
    <div className="bg-gray-900 p-6 rounded-lg shadow-md">
      <div className="space-y-4">
        {datasetList.map((ds) => (
          <motion.div
            key={ds.id}
            className="flex items-center justify-between border-b border-gray-700 pb-3 last:border-none cursor-pointer hover:bg-gray-700/30 transition-colors duration-200 p-2 rounded"
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
              <p className="font-semibold text-white text-lg">{ds.name}</p>
              <p className="text-sm text-gray-300">
                Used in {Math.floor(Math.random() * 10) + 1} experiments
              </p>
            </div>
            <div className="w-40 h-16">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ds.metrics}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                  <Tooltip
                    formatter={(value: number) => [`${value}`, 'Metric']}
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
    </div>
  );
}

export default DatasetListWithMetrics;
