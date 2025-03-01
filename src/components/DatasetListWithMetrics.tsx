// src/components/DatasetListWithMetrics.tsx

import React from 'react';
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
  const datasetList = Array.from({ length: 5 }, (_, i) => ({
    name: `Dataset ${i + 1}`,
    metrics: Array.from({ length: 5 }, () => ({
      value: Math.floor(Math.random() * 50) + 10,
    })),
  }));

  const handleDatasetClick = (datasetName: string) => {
    alert(`Has hecho clic en: ${datasetName}`);
  };

  return (
    <div className="bg-black/70 p-4 rounded shadow border border-gray-600">
      <h4 className="text-lg font-semibold mb-2 text-white">
        Recently Used Datasets
      </h4>
      <div className="space-y-3">
        {datasetList.map((ds, idx) => (
          <div
            key={idx}
            className="
              flex items-center justify-between
              border-b border-gray-600
              pb-2 last:border-none
              cursor-pointer
              hover:bg-gray-700/30
            "
            onClick={() => handleDatasetClick(ds.name)}
          >
            <div>
              <p className="font-medium text-white">{ds.name}</p>
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
          </div>
        ))}
      </div>
    </div>
  );
}

export default DatasetListWithMetrics;
