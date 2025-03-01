import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import { Calendar, Filter, PlusCircle } from 'lucide-react';

const monthlyData = [
  { month: 'Jan', datasets: 12, growth: 0 },
  { month: 'Feb', datasets: 15, growth: 25 },
  { month: 'Mar', datasets: 18, growth: 20 },
  { month: 'Apr', datasets: 16, growth: -11.1 },
  { month: 'May', datasets: 21, growth: 31.3 },
  { month: 'Jun', datasets: 25, growth: 19 },
  { month: 'Jul', datasets: 23, growth: -8 },
  { month: 'Aug', datasets: 28, growth: 21.7 },
  { month: 'Sep', datasets: 32, growth: 14.3 },
  { month: 'Oct', datasets: 35, growth: 9.4 },
  { month: 'Nov', datasets: 42, growth: 20 },
  { month: 'Dec', datasets: 45, growth: 7.1 },
];

const weeklyData = [
  { month: 'Week 1', datasets: 8, growth: 0 },
  { month: 'Week 2', datasets: 12, growth: 50 },
  { month: 'Week 3', datasets: 15, growth: 25 },
  { month: 'Week 4', datasets: 10, growth: -33.3 },
];

const yearlyData = [
  { month: '2021', datasets: 120, growth: 0 },
  { month: '2022', datasets: 180, growth: 50 },
  { month: '2023', datasets: 260, growth: 44.4 },
  { month: '2024', datasets: 350, growth: 34.6 },
];

function DatasetsChart() {
  const [period, setPeriod] = useState('monthly');
  const [chartType, setChartType] = useState('bar');

  const getPeriodData = () => {
    switch (period) {
      case 'weekly':
        return weeklyData;
      case 'yearly':
        return yearlyData;
      default:
        return monthlyData;
    }
  };

  const data = getPeriodData();
  const currentGrowth = data[data.length - 1].growth;
  const latestValue = data[data.length - 1].datasets;

  // Determinar color y flecha
  const growthColor = currentGrowth >= 0 ? 'text-green-500' : 'text-red-500';
  const growthIcon = currentGrowth >= 0 ? '↑' : '↓';

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <h4 className="text-lg font-semibold">Datasets by Month</h4>
          <span className={`ml-2 text-sm font-medium ${growthColor}`}>
            {growthIcon} {Math.abs(currentGrowth).toFixed(1)}%
          </span>
        </div>

        <div className="flex space-x-2">
          <select
            className="border rounded px-2 py-1 text-sm bg-white"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
          >
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>

          <select
            className="border rounded px-2 py-1 text-sm bg-white"
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
          >
            <option value="bar">Bar Chart</option>
            <option value="line">Line Chart</option>
          </select>
        </div>
      </div>

      {/* KPI: total datasets */}
      <div className="flex flex-col md:flex-row md:justify-between mb-4">
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 mb-2 md:mb-0 flex items-center">
          <div className="bg-blue-500 rounded-full p-2 mr-3">
            <Calendar size={20} className="text-white" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Total Datasets</p>
            <p className="text-xl font-bold">{latestValue}</p>
          </div>
        </div>

        <div className="flex space-x-2">
          <button className="flex items-center bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 transition-colors">
            <PlusCircle size={16} className="mr-1" />
            Add Dataset
          </button>
          <button className="flex items-center bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-300 transition-colors">
            <Filter size={16} className="mr-1" />
            Filter
          </button>
        </div>
      </div>

      {/* Gráfico principal */}
      <div className="flex-grow" style={{ minHeight: '250px', width: '100%' }}>
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'bar' ? (
              <BarChart data={data} margin={{ top: 5, right: 30, left: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="datasets" fill="#4e63d9" name="Datasets" />
              </BarChart>
            ) : (
              <LineChart data={data} margin={{ top: 5, right: 30, left: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="datasets"
                  stroke="#4e63d9"
                  name="Datasets"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-gray-500 mb-2">No data available for this period</p>
            <button className="bg-blue-500 text-white px-4 py-2 rounded">
              Upload your first dataset
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default DatasetsChart;
