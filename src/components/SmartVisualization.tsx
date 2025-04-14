// src/components/SmartVisualization.tsx
import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, ScatterChart, Scatter,
  CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer,
  Cell
} from 'recharts';
import axios from 'axios';

interface SmartVisualizationProps {
  data: any[];
  columns: string[];
  height?: number;
  width?: number;
  title?: string;
  colorScheme?: 'default' | 'business' | 'vibrant';
}

const SmartVisualization: React.FC<SmartVisualizationProps> = ({ 
  data,
  columns,
  height = 400,
  width = '100%',
  title,
  colorScheme = 'default'
}) => {
  const [recommendedViz, setRecommendedViz] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [insights, setInsights] = useState<string[]>([]);
  
  // Color schemes tailored for Peruvian businesses
  const colorSchemes = {
    default: ['#00E6E6', '#0094FF', '#6B66FF', '#9C66FF', '#FF66D9'],
    business: ['#005F73', '#0A9396', '#94D2BD', '#E9D8A6', '#EE9B00', '#CA6702', '#BB3E03'],
    vibrant: ['#FF006E', '#FB5607', '#FFBE0B', '#8338EC', '#3A86FF']
  };
  
  const colors = colorSchemes[colorScheme];
  
  useEffect(() => {
    const determineVisualization = async () => {
      setLoading(true);
      
      try {
        // Either call API for smart recommendation or use local logic
        if (data.length > 100) {
          // Call API for more sophisticated analysis
          const response = await axios.post('/api/visualize/recommend', {
            data: data.slice(0, 100), // Send sample for performance
            columns,
            fullDataSize: data.length
          });
          
          setRecommendedViz(response.data.recommendedType);
          setInsights(response.data.insights || []);
        } else {
          // Use local logic for smaller datasets
          const viz = determineVisualizationLocally(data, columns);
          setRecommendedViz(viz.type);
          setInsights(viz.insights);
        }
      } catch (err) {
        console.error("Error determining visualization:", err);
        setError("Error analyzing data for visualization");
        // Fallback to a safe default
        setRecommendedViz('bar');
      } finally {
        setLoading(false);
      }
    };
    
    determineVisualization();
  }, [data, columns]);
  
  // Local logic for determining visualization type
  const determineVisualizationLocally = (data: any[], columns: string[]) => {
    // Simple logic based on data characteristics
    const numericColumns = columns.filter(col => 
      typeof data[0][col] === 'number'
    );
    
    const categoricalColumns = columns.filter(col => 
      !numericColumns.includes(col)
    );
    
    // Check for time series
    const dateColumns = categoricalColumns.filter(col => 
      !isNaN(Date.parse(data[0][col]))
    );
    
    const insights = [];
    
    // Simple logic to determine visualization type
    if (dateColumns.length > 0 && numericColumns.length > 0) {
      insights.push("Los datos muestran una tendencia temporal que es mejor visualizada con un gráfico de líneas.");
      return { type: 'line', insights };
    } else if (categoricalColumns.length === 1 && numericColumns.length === 1) {
      const uniqueCategories = new Set(data.map(item => item[categoricalColumns[0]]));
      if (uniqueCategories.size <= 10) {
        insights.push(`Comparación ideal entre ${uniqueCategories.size} categorías diferentes.`);
        return { type: 'bar', insights };
      } else {
        insights.push("Demasiadas categorías para un gráfico de barras efectivo.");
        return { type: 'scatter', insights };
      }
    } else if (numericColumns.length >= 2) {
      insights.push("Explorando relación entre variables numéricas.");
      return { type: 'scatter', insights };
    } else if (categoricalColumns.length === 1 && data.length <= 10) {
      insights.push("Distribución proporcional entre pocas categorías.");
      return { type: 'pie', insights };
    }
    
    // Default fallback
    insights.push("Visualización de barras como opción versátil para este conjunto de datos.");
    return { type: 'bar', insights };
  };
  
  // Render loading state
  if (loading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-cyber-cyan"></div>
    </div>;
  }
  
  // Render error state
  if (error) {
    return <div className="text-red-400 p-4">{error}</div>;
  }
  
  // Determine actual data to visualize
  let xKey, yKey;
  
  if (columns.length >= 2) {
    const numericColumns = columns.filter(col => 
      typeof data[0][col] === 'number'
    );
    
    const categoricalColumns = columns.filter(col => 
      !numericColumns.includes(col)
    );
    
    xKey = categoricalColumns[0] || columns[0];
    yKey = numericColumns[0] || columns[1];
  } else {
    xKey = 'name';
    yKey = 'value';
  }
  
  // Render the appropriate visualization
  return (
    <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
      {title && <h3 className="text-lg font-semibold text-cyber-text mb-4">{title}</h3>}
      
      <ResponsiveContainer width={width} height={height}>
        {recommendedViz === 'line' ? (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
            <XAxis dataKey={xKey} stroke="#E6E6E6" />
            <YAxis stroke="#E6E6E6" />
            <Tooltip contentStyle={{ backgroundColor: '#1E2A38', borderColor: '#00E6E6' }} />
            <Legend />
            <Line type="monotone" dataKey={yKey} stroke="#00E6E6" strokeWidth={2} />
          </LineChart>
        ) : recommendedViz === 'bar' ? (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
            <XAxis dataKey={xKey} stroke="#E6E6E6" />
            <YAxis stroke="#E6E6E6" />
            <Tooltip contentStyle={{ backgroundColor: '#1E2A38', borderColor: '#00E6E6' }} />
            <Legend />
            <Bar dataKey={yKey} fill="#00E6E6" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Bar>
          </BarChart>
        ) : recommendedViz === 'pie' ? (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={height / 3}
              fill="#8884d8"
              dataKey={yKey}
              nameKey={xKey}
              label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ backgroundColor: '#1E2A38', borderColor: '#00E6E6' }} />
            <Legend />
          </PieChart>
        ) : (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
            <XAxis dataKey={xKey} stroke="#E6E6E6" />
            <YAxis dataKey={yKey} stroke="#E6E6E6" />
            <Tooltip contentStyle={{ backgroundColor: '#1E2A38', borderColor: '#00E6E6' }} />
            <Legend />
            <Scatter name="Datos" data={data} fill="#00E6E6" />
          </ScatterChart>
        )}
      </ResponsiveContainer>
      
      {insights.length > 0 && (
        <div className="mt-4 p-3 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
          <h4 className="text-sm font-medium text-cyber-cyan mb-2">Insights</h4>
          <ul className="text-sm space-y-1">
            {insights.map((insight, index) => (
              <li key={index} className="text-cyber-text flex items-start">
                <span className="inline-block h-5 w-5 rounded-full bg-cyber-cyan/20 text-cyber-cyan flex items-center justify-center text-xs mr-2">•</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SmartVisualization;