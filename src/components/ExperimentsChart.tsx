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
  ResponsiveContainer,
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
  { month: 'Dec', successful: 21, failed: 3 },
];

function ExperimentsChart() {
  const dataWithRate = monthlyData.map((d) => {
    const total = d.successful + d.failed;
    const successRate = Math.round((d.successful / total) * 1000) / 10;
    return { ...d, total, successRate };
  });

  return (
    <div className="w-full h-full flex flex-col">
      <h4 className="text-lg font-semibold mb-2">Experiments by Month</h4>
      <div className="flex-grow">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={dataWithRate}
            margin={{ top: 20, right: 20, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis yAxisId="left" domain={[0, 'auto']} />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              formatter={(value, name) => {
                if (name === 'successRate') {
                  return [`${value}%`, 'Success Rate'];
                }
                return [value, name];
              }}
            />
            <Legend />

            {/* Barras apiladas */}
            <Bar
              yAxisId="left"
              dataKey="failed"
              stackId="a"
              fill="#ef4444"
              name="Failed"
            />
            <Bar
              yAxisId="left"
              dataKey="successful"
              stackId="a"
              fill="#10b981"
              name="Successful"
            />

            {/* Línea para successRate */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="successRate"
              stroke="#3b82f6"
              strokeWidth={2}
              name="Success Rate"
              dot={{ r: 3 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default ExperimentsChart;
