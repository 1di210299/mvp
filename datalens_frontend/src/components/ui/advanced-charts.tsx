import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

interface ChartData {
  [key: string]: any;
}

interface ChartProps {
  data: ChartData[];
  width?: number | string;
  height?: number | string;
  className?: string;
}

interface BarChartProps extends ChartProps {
  xAxisKey: string;
  yAxisKey: string;
  color?: string;
  stacked?: boolean;
  multiple?: string[]; // Para múltiples barras
}

interface LineChartProps extends ChartProps {
  xAxisKey: string;
  yAxisKey: string;
  color?: string;
  multiple?: string[]; // Para múltiples líneas
  curved?: boolean;
}

interface PieChartProps extends ChartProps {
  nameKey: string;
  valueKey: string;
  colors?: string[];
  showLabels?: boolean;
  innerRadius?: number;
}

interface AreaChartProps extends ChartProps {
  xAxisKey: string;
  yAxisKey: string;
  color?: string;
  multiple?: string[];
  stacked?: boolean;
}

interface ScatterChartProps extends ChartProps {
  xAxisKey: string;
  yAxisKey: string;
  color?: string;
}

interface RadarChartProps extends ChartProps {
  subjectKey: string;
  valueKey: string;
  color?: string;
}

// Paleta de colores predefinida
const DEFAULT_COLORS = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
  '#06B6D4', '#F97316', '#84CC16', '#EC4899', '#6366F1'
];

// Componente de Gráfico de Barras
export const AdvancedBarChart: React.FC<BarChartProps> = ({
  data,
  xAxisKey,
  yAxisKey,
  color = '#3B82F6',
  stacked = false,
  multiple = [],
  width = '100%',
  height = 400,
  className = ''
}) => {
  return (
    <div className={`bg-white p-4 rounded-lg shadow ${className}`}>
      <ResponsiveContainer width={width} height={height}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xAxisKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          
          {multiple.length > 0 ? (
            multiple.map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                fill={DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
                stackId={stacked ? 'stack' : undefined}
              />
            ))
          ) : (
            <Bar dataKey={yAxisKey} fill={color} />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// Componente de Gráfico de Líneas
export const AdvancedLineChart: React.FC<LineChartProps> = ({
  data,
  xAxisKey,
  yAxisKey,
  color = '#3B82F6',
  multiple = [],
  curved = false,
  width = '100%',
  height = 400,
  className = ''
}) => {
  return (
    <div className={`bg-white p-4 rounded-lg shadow ${className}`}>
      <ResponsiveContainer width={width} height={height}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xAxisKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          
          {multiple.length > 0 ? (
            multiple.map((key, index) => (
              <Line
                key={key}
                type={curved ? 'monotone' : 'linear'}
                dataKey={key}
                stroke={DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
                strokeWidth={2}
                dot={{ fill: DEFAULT_COLORS[index % DEFAULT_COLORS.length], strokeWidth: 2, r: 4 }}
              />
            ))
          ) : (
            <Line
              type={curved ? 'monotone' : 'linear'}
              dataKey={yAxisKey}
              stroke={color}
              strokeWidth={2}
              dot={{ fill: color, strokeWidth: 2, r: 4 }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// Componente de Gráfico de Torta
export const AdvancedPieChart: React.FC<PieChartProps> = ({
  data,
  nameKey,
  valueKey,
  colors = DEFAULT_COLORS,
  showLabels = true,
  innerRadius = 0,
  width = '100%',
  height = 400,
  className = ''
}) => {
  const renderLabel = (entry: any) => {
    return showLabels ? `${entry[nameKey]}: ${entry[valueKey]}` : '';
  };

  return (
    <div className={`bg-white p-4 rounded-lg shadow ${className}`}>
      <ResponsiveContainer width={width} height={height}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={showLabels ? renderLabel : false}
            outerRadius={80}
            innerRadius={innerRadius}
            fill="#8884d8"
            dataKey={valueKey}
          >
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

// Componente de Gráfico de Área
export const AdvancedAreaChart: React.FC<AreaChartProps> = ({
  data,
  xAxisKey,
  yAxisKey,
  color = '#3B82F6',
  multiple = [],
  stacked = false,
  width = '100%',
  height = 400,
  className = ''
}) => {
  return (
    <div className={`bg-white p-4 rounded-lg shadow ${className}`}>
      <ResponsiveContainer width={width} height={height}>
        <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xAxisKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          
          {multiple.length > 0 ? (
            multiple.map((key, index) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stackId={stacked ? 'stack' : index}
                stroke={DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
                fill={DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
                fillOpacity={0.6}
              />
            ))
          ) : (
            <Area
              type="monotone"
              dataKey={yAxisKey}
              stroke={color}
              fill={color}
              fillOpacity={0.6}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// Componente de Gráfico de Dispersión
export const AdvancedScatterChart: React.FC<ScatterChartProps> = ({
  data,
  xAxisKey,
  yAxisKey,
  color = '#3B82F6',
  width = '100%',
  height = 400,
  className = ''
}) => {
  return (
    <div className={`bg-white p-4 rounded-lg shadow ${className}`}>
      <ResponsiveContainer width={width} height={height}>
        <ScatterChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xAxisKey} name={xAxisKey} />
          <YAxis dataKey={yAxisKey} name={yAxisKey} />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <Scatter name="Datos" data={data} fill={color} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

// Componente de Gráfico Radar
export const AdvancedRadarChart: React.FC<RadarChartProps> = ({
  data,
  subjectKey,
  valueKey,
  color = '#3B82F6',
  width = '100%',
  height = 400,
  className = ''
}) => {
  return (
    <div className={`bg-white p-4 rounded-lg shadow ${className}`}>
      <ResponsiveContainer width={width} height={height}>
        <RadarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <PolarGrid />
          <PolarAngleAxis dataKey={subjectKey} />
          <PolarRadiusAxis />
          <Radar
            name="Valor"
            dataKey={valueKey}
            stroke={color}
            fill={color}
            fillOpacity={0.6}
          />
          <Tooltip />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

// Componente de Dashboard con múltiples gráficos
interface DashboardProps {
  title?: string;
  charts: Array<{
    type: 'bar' | 'line' | 'pie' | 'area' | 'scatter' | 'radar';
    title: string;
    props: any;
    gridSize?: 'sm' | 'md' | 'lg' | 'xl';
  }>;
  className?: string;
}

export const ChartDashboard: React.FC<DashboardProps> = ({
  title,
  charts,
  className = ''
}) => {
  const getGridClass = (size: string = 'md') => {
    switch (size) {
      case 'sm': return 'col-span-1';
      case 'md': return 'col-span-1 md:col-span-2';
      case 'lg': return 'col-span-1 md:col-span-2 lg:col-span-3';
      case 'xl': return 'col-span-1 md:col-span-2 lg:col-span-4';
      default: return 'col-span-1 md:col-span-2';
    }
  };

  const renderChart = (chart: any) => {
    const { type, props } = chart;
    
    switch (type) {
      case 'bar':
        return <AdvancedBarChart {...props} />;
      case 'line':
        return <AdvancedLineChart {...props} />;
      case 'pie':
        return <AdvancedPieChart {...props} />;
      case 'area':
        return <AdvancedAreaChart {...props} />;
      case 'scatter':
        return <AdvancedScatterChart {...props} />;
      case 'radar':
        return <AdvancedRadarChart {...props} />;
      default:
        return <div className="p-4 bg-gray-100 rounded">Tipo de gráfico no soportado</div>;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {title && (
        <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {charts.map((chart, index) => (
          <div key={index} className={getGridClass(chart.gridSize)}>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-800">{chart.title}</h3>
              {renderChart(chart)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
