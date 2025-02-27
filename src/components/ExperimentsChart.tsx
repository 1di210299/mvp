import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Beaker, Filter, PlusCircle, CheckCircle, XCircle } from 'lucide-react';

// Datos de ejemplo
const monthlyData = [
  { month: 'Jan', total: 8, successful: 5, failed: 3, success_rate: 62.5 },
  { month: 'Feb', total: 10, successful: 7, failed: 3, success_rate: 70 },
  { month: 'Mar', total: 12, successful: 8, failed: 4, success_rate: 66.7 },
  { month: 'Apr', total: 9, successful: 6, failed: 3, success_rate: 66.7 },
  { month: 'May', total: 15, successful: 11, failed: 4, success_rate: 73.3 },
  { month: 'Jun', total: 18, successful: 14, failed: 4, success_rate: 77.8 },
  { month: 'Jul', total: 16, successful: 12, failed: 4, success_rate: 75 },
  { month: 'Aug', total: 19, successful: 15, failed: 4, success_rate: 78.9 },
  { month: 'Sep', total: 21, successful: 17, failed: 4, success_rate: 81 },
  { month: 'Oct', total: 18, successful: 15, failed: 3, success_rate: 83.3 },
  { month: 'Nov', total: 22, successful: 19, failed: 3, success_rate: 86.4 },
  { month: 'Dec', total: 24, successful: 21, failed: 3, success_rate: 87.5 }
];

// Datos de ejemplo para diferentes periodos
const weeklyData = [
  { month: 'Week 1', total: 5, successful: 3, failed: 2, success_rate: 60 },
  { month: 'Week 2', total: 7, successful: 5, failed: 2, success_rate: 71.4 },
  { month: 'Week 3', total: 8, successful: 7, failed: 1, success_rate: 87.5 },
  { month: 'Week 4', total: 4, successful: 3, failed: 1, success_rate: 75 }
];

const yearlyData = [
  { month: '2021', total: 76, successful: 54, failed: 22, success_rate: 71.1 },
  { month: '2022', total: 120, successful: 92, failed: 28, success_rate: 76.7 },
  { month: '2023', total: 180, successful: 146, failed: 34, success_rate: 81.1 },
  { month: '2024', total: 192, successful: 163, failed: 29, success_rate: 84.9 }
];

const ExperimentsChart = () => {
  const [period, setPeriod] = useState('monthly');
  const [chartType, setChartType] = useState('bar');
  const [dataView, setDataView] = useState('counts'); // 'counts' or 'rate'
  
  const getPeriodData = () => {
    switch(period) {
      case 'weekly':
        return weeklyData;
      case 'yearly':
        return yearlyData;
      case 'monthly':
      default:
        return monthlyData;
    }
  };
  
  const data = getPeriodData();
  const latestData = data[data.length - 1];
  const previousData = data[data.length - 2];
  
  // Calcular el cambio en la tasa de éxito
  const successRateChange = latestData.success_rate - previousData.success_rate;
  const successRateColor = successRateChange >= 0 ? 'text-green-500' : 'text-red-500';
  const successRateIcon = successRateChange >= 0 ? '↑' : '↓';
  
  // Calcular el cambio en el total de experimentos
  const totalChange = ((latestData.total - previousData.total) / previousData.total) * 100;
  const totalColor = totalChange >= 0 ? 'text-green-500' : 'text-red-500';
  const totalIcon = totalChange >= 0 ? '↑' : '↓';
  
  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <h4 className="text-lg font-semibold">Experiments by Month</h4>
          <span className={`ml-2 text-sm font-medium ${totalColor}`}>
            {totalIcon} {Math.abs(totalChange).toFixed(1)}%
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
          
          <select 
            className="border rounded px-2 py-1 text-sm bg-white"
            value={dataView}
            onChange={(e) => setDataView(e.target.value)}
          >
            <option value="counts">Counts</option>
            <option value="rate">Success Rate</option>
          </select>
        </div>
      </div>
      
      <div className="flex flex-col md:flex-row md:justify-between mb-4">
        <div className="flex space-x-4">
          <div className="bg-green-50 border border-green-100 rounded-lg p-3 mb-2 md:mb-0 flex items-center">
            <div className="bg-green-500 rounded-full p-2 mr-3">
              <CheckCircle size={20} className="text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Success Rate</p>
              <p className="text-xl font-bold">{latestData.success_rate.toFixed(1)}%</p>
              <p className={`text-xs ${successRateColor}`}>
                {successRateIcon} {Math.abs(successRateChange).toFixed(1)}% vs previous
              </p>
            </div>
          </div>
          
          <div className="bg-purple-50 border border-purple-100 rounded-lg p-3 mb-2 md:mb-0 flex items-center">
            <div className="bg-purple-500 rounded-full p-2 mr-3">
              <Beaker size={20} className="text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Experiments</p>
              <p className="text-xl font-bold">{latestData.total}</p>
            </div>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <button className="flex items-center bg-purple-500 text-white px-3 py-1 rounded text-sm hover:bg-purple-600 transition-colors">
            <PlusCircle size={16} className="mr-1" />
            New Experiment
          </button>
          <button className="flex items-center bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-300 transition-colors">
            <Filter size={16} className="mr-1" />
            Filter
          </button>
        </div>
      </div>
      
      <div className="flex-grow" style={{ height: "400px", minHeight: "400px" }}>
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            {dataView === 'counts' ? (
              chartType === 'bar' ? (
                <BarChart data={data} margin={{ top: 5, right: 30, left: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="successful" stackId="a" fill="#10b981" name="Successful" />
                  <Bar dataKey="failed" stackId="a" fill="#ef4444" name="Failed" />
                </BarChart>
              ) : (
                <LineChart data={data} margin={{ top: 5, right: 30, left: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="total" stroke="#8884d8" name="Total" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="successful" stroke="#10b981" name="Successful" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="failed" stroke="#ef4444" name="Failed" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              )
            ) : (
              <LineChart data={data} margin={{ top: 5, right: 30, left: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => [`${value}%`, 'Success Rate']} />
                <Legend />
                <Line type="monotone" dataKey="success_rate" stroke="#8884d8" name="Success Rate %" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            )}
          </ResponsiveContainer>
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-gray-500 mb-2">No experiments run in this period</p>
            <button className="bg-purple-500 text-white px-4 py-2 rounded">
              Run your first experiment
            </button>
          </div>
        )}
      </div>
      
      {/* Recent Experiments Table */}
      <div className="mt-4 border-t pt-4">
        <h5 className="text-sm font-semibold mb-2">Recent Experiments</h5>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead>
              <tr className="bg-gray-100 border-b">
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Metrics</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="py-2 px-3 text-sm">Text Classification - BERT</td>
                <td className="py-2 px-3 text-sm">Today, 10:30 AM</td>
                <td className="py-2 px-3 text-sm">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Successful</span>
                </td>
                <td className="py-2 px-3 text-sm">Accuracy: 95.2%</td>
              </tr>
              <tr>
                <td className="py-2 px-3 text-sm">Image Segmentation - U-Net</td>
                <td className="py-2 px-3 text-sm">Yesterday</td>
                <td className="py-2 px-3 text-sm">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Failed</span>
                </td>
                <td className="py-2 px-3 text-sm">Error: Out of memory</td>
              </tr>
              <tr>
                <td className="py-2 px-3 text-sm">Time Series - LSTM</td>
                <td className="py-2 px-3 text-sm">2 days ago</td>
                <td className="py-2 px-3 text-sm">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Successful</span>
                </td>
                <td className="py-2 px-3 text-sm">MAE: 0.12, RMSE: 0.18</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ExperimentsChart;