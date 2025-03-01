// src/components/ExperimentsSection.tsx
import React from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const monthlyData = [
  { month: 'Jan', successful: 5, failed: 3 },
  { month: 'Feb', successful: 7, failed: 3 },
  { month: 'Mar', successful: 8, failed: 4 },
  { month: 'Apr', successful: 6, failed: 3 },
  { month: 'May', successful: 11, failed: 4 },
  { month: 'Jun', successful: 14, failed: 4 },
  { month: 'Jul', successful: 12, failed: 4 },
  { month: 'Aug', successful: 15, failed: 4 },
  { month: 'Sep', successful: 17, failed: 4 },
  { month: 'Oct', successful: 15, failed: 3 },
  { month: 'Nov', successful: 19, failed: 3 },
  { month: 'Dec', successful: 21, failed: 3 }
];

const ExperimentsSection: React.FC = () => {
  // Calculamos el total y la tasa de éxito para cada mes
  const dataWithRate = monthlyData.map((d) => {
    const total = d.successful + d.failed;
    const successRate = Math.round((d.successful / total) * 1000) / 10; // p.ej. 75.0
    return { ...d, total, successRate };
  });

  return (
    <div className="w-full h-auto flex flex-col">
      {/* Encabezado */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-semibold">Experiments</h4>
        <button className="bg-purple-500 text-white px-3 py-1 rounded text-sm hover:bg-purple-600">
          New Experiment
        </button>
      </div>

      {/* Gráfico Compuesto */}
      <div className="mb-4" style={{ height: '300px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={dataWithRate} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip formatter={(value, name) => {
              if (name === 'successRate') {
                return [`${value}%`, 'Success Rate'];
              }
              return [value, name];
            }} />
            <Legend />
            {/* Barras apiladas: Failed y Successful */}
            <Bar dataKey="failed" stackId="a" fill="#ef4444" name="Failed" />
            <Bar dataKey="successful" stackId="a" fill="#10b981" name="Successful" />
            {/* Línea para la tasa de éxito */}
            <Line
              type="monotone"
              dataKey="successRate"
              stroke="#8884d8"
              strokeWidth={2}
              name="Success Rate"
              dot={{ r: 3 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Tabla de “Recent Experiments” */}
      <div>
        <h5 className="text-sm font-semibold mb-2">Recent Experiments</h5>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead>
              <tr className="bg-gray-100 border-b">
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase">Metrics</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="py-2 px-3 text-sm">Text Classification - BERT</td>
                <td className="py-2 px-3 text-sm">Today, 10:30 AM</td>
                <td className="py-2 px-3 text-sm">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Successful
                  </span>
                </td>
                <td className="py-2 px-3 text-sm">Accuracy: 95.2%</td>
              </tr>
              <tr>
                <td className="py-2 px-3 text-sm">Image Segmentation - U-Net</td>
                <td className="py-2 px-3 text-sm">Yesterday</td>
                <td className="py-2 px-3 text-sm">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                    Failed
                  </span>
                </td>
                <td className="py-2 px-3 text-sm">Out of memory</td>
              </tr>
              <tr>
                <td className="py-2 px-3 text-sm">Time Series - LSTM</td>
                <td className="py-2 px-3 text-sm">2 days ago</td>
                <td className="py-2 px-3 text-sm">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Successful
                  </span>
                </td>
                <td className="py-2 px-3 text-sm">MAE: 0.12, RMSE: 0.18</td>
              </tr>
              {/* etc... */}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ExperimentsSection;
