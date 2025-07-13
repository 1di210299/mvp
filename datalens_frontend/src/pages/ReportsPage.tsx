import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Badge,
  Alert,
  AlertDescription
} from '../components/ui';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Package,
  Users,
  Target,
  RefreshCw,
  Calendar,
  Filter,
  Download,
  Eye,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  FileText,
  Mail,
  Bell,
  Settings,
  ArrowUp,
  ArrowDown,
  Globe,
  Database,
  Shield
} from '../components/ui/icons';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  ReferenceLine
} from 'recharts';

// Servicio para obtener datos de analytics
const analyticsService = {
  async getAnalyticsData(period: string = '12months', filters: any = {}) {
    try {
      // CORREGIDO: Usar autenticación JWT y endpoint correcto con parámetros
      const token = localStorage.getItem('access_token');
      
      // Construir parámetros de consulta
      const params = new URLSearchParams({
        period,
        ...filters
      });

      const response = await fetch(`http://localhost:8080/api/reports/analytics/?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('✅ Datos reales obtenidos del backend:', data);
      
      // Validar y estructurar datos recibidos
      return {
        metrics: {
          total_products: data.metrics?.total_products || 0,
          total_inventory_value: data.metrics?.total_inventory_value || 0,
          sales_this_month: data.metrics?.sales_this_month || 0,
          sales_value_this_month: data.metrics?.sales_value_this_month || 0,
          active_alerts: data.metrics?.active_alerts || 0,
          sales_growth_percentage: data.metrics?.sales_growth_percentage || 0,
          inventory_turnover: data.metrics?.inventory_turnover || 0,
          forecast_accuracy: data.metrics?.forecast_accuracy || 0,
        },
        trends: {
          monthly_data: Array.isArray(data.trends?.monthly_data) ? data.trends.monthly_data : [],
          inventory_status: Array.isArray(data.trends?.inventory_status) ? data.trends.inventory_status : [
            { name: 'Stock Normal', value: 85, percentage: 70, color: '#10b981' },
            { name: 'Stock Bajo', value: 25, percentage: 20, color: '#f59e0b' },
            { name: 'Sin Stock', value: 12, percentage: 10, color: '#ef4444' }
          ]
        },
        top_products: Array.isArray(data.top_products) ? data.top_products : [],
        recent_alerts: Array.isArray(data.recent_alerts) ? data.recent_alerts : [],
        last_updated: data.last_updated || new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Error conectando con el backend:', error);
      throw error;
    }
  }
};

// NUEVO servicio para exportar datos - USANDO ENDPOINTS REALES
const exportService = {
  async exportToPDF(data: any, period: string) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8080/api/reports/export/pdf/', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify({ data, period, format: 'pdf' })
      });
      
      if (!response.ok) throw new Error('Error al exportar PDF');
      return response.blob();
    } catch (error) {
      console.error('Error exportando PDF:', error);
      throw error;
    }
  },

  async exportToExcel(data: any, period: string) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8080/api/reports/export/excel/', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify({ data, period, format: 'excel' })
      });
      
      if (!response.ok) throw new Error('Error al exportar Excel');
      return response.blob();
    } catch (error) {
      console.error('Error exportando Excel:', error);
      throw error;
    }
  },

  downloadFile(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
};

interface AnalyticsData {
  metrics: {
    total_products: number;
    total_inventory_value: number;
    sales_this_month: number;
    sales_value_this_month: number;
    active_alerts: number;
    sales_growth_percentage: number;
    inventory_turnover: number;
    forecast_accuracy: number;
  };
  trends: {
    monthly_data: Array<{
      month: string;
      month_year: string;
      sales: number;
      entries: number;
      inventory_value: number;
      transactions_count: number;
    }>;
    inventory_status: Array<{
      name: string;
      value: number;
      percentage: number;
      color: string;
    }>;
  };
  top_products: Array<{
    name: string;
    sales: number;
    current_stock: number;
    category: string;
    unit_cost: number;
  }>;
  recent_alerts: Array<{
    id: number;
    message: string;
    severity: string;
    status: string;
    created_at: string;
    product_name?: string;
  }>;
  last_updated: string;
}

interface ReportsPageState {
  loading: boolean;
  error: string | null;
  selectedPeriod: string;
  selectedView: string;
  data: AnalyticsData | null;
  isRefreshing: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
  showExportMenu: boolean;
  isExporting: boolean;
  selectedMetric: string | null;
  compareMode: boolean;
}

const ReportsPage: React.FC = () => {
  const [state, setState] = useState<ReportsPageState>({
    loading: true,
    error: null,
    selectedPeriod: '12months',
    selectedView: 'overview',
    data: null,
    isRefreshing: false,
    autoRefresh: false,
    refreshInterval: 30000, // 30 segundos
    showExportMenu: false,
    isExporting: false,
    selectedMetric: null,
    compareMode: false
  });

  // Auto-refresh functionality
  useEffect(() => {
    if (state.autoRefresh) {
      const interval = setInterval(() => {
        refreshData();
      }, state.refreshInterval);
      
      return () => clearInterval(interval);
    }
  }, [state.autoRefresh, state.refreshInterval]);

  const loadAnalyticsData = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // NUEVO: Construir filtros dinámicos basados en el estado actual
      const filters: any = {};
      
      // Agregar filtros adicionales si están disponibles en el estado
      if (state.selectedView !== 'overview') {
        filters.view = state.selectedView;
      }
      
      // Aquí podrías agregar más filtros basados en controles de UI adicionales
      // Por ejemplo: filters.category = selectedCategory, etc.
      
      const analyticsData = await analyticsService.getAnalyticsData(state.selectedPeriod, filters);
      
      setState(prev => ({ 
        ...prev, 
        data: analyticsData,
        loading: false 
      }));
    } catch (err) {
      console.error('Error loading analytics:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al cargar datos de analytics. Verifica la conexión con el backend.',
        loading: false,
        data: null
      }));
    }
  };

  // Función para exportar datos
  const handleExport = async (format: 'pdf' | 'excel') => {
    if (!state.data) return;
    
    setState(prev => ({ ...prev, isExporting: true }));
    
    try {
      const timestamp = new Date().toISOString().slice(0, 10);
      const filename = `analytics-report-${timestamp}.${format}`;
      
      let blob: Blob;
      if (format === 'pdf') {
        blob = await exportService.exportToPDF(state.data, state.selectedPeriod);
      } else {
        blob = await exportService.exportToExcel(state.data, state.selectedPeriod);
      }
      
      exportService.downloadFile(blob, filename);
      
      setState(prev => ({ 
        ...prev, 
        isExporting: false, 
        showExportMenu: false 
      }));
    } catch (error) {
      console.error('Error al exportar:', error);
      setState(prev => ({ ...prev, isExporting: false }));
      alert('Error al exportar el reporte. Por favor, inténtalo de nuevo.');
    }
  };

  // Función para compartir reporte
  const handleShare = async () => {
    if (navigator.share && state.data) {
      try {
        await navigator.share({
          title: 'Reporte de Analytics',
          text: `Reporte de analytics actualizado - ${new Date().toLocaleDateString()}`,
          url: window.location.href
        });
      } catch (error) {
        console.log('Error al compartir:', error);
        // Fallback: copiar al portapapeles
        navigator.clipboard.writeText(window.location.href);
        alert('Enlace copiado al portapapeles');
      }
    }
  };

  const refreshData = async () => {
    setState(prev => ({ ...prev, isRefreshing: true }));
    await loadAnalyticsData();
    setState(prev => ({ ...prev, isRefreshing: false }));
  };

  useEffect(() => {
    loadAnalyticsData();
  }, [state.selectedPeriod]);

  if (state.loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="flex items-center justify-center min-h-[600px]">
          <div className="text-center">
            <div className="relative">
              <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto mb-6"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Cargando Analytics Avanzado
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Procesando datos en tiempo real...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!state.data) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="text-center py-20">
          <AlertTriangle className="h-16 w-16 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Error al cargar datos
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            No se pudieron cargar los datos de analytics.
          </p>
          <Button onClick={loadAnalyticsData} className="bg-blue-600 hover:bg-blue-700">
            <RefreshCw className="h-4 w-4 mr-2" />
            Reintentar
          </Button>
        </div>
      </div>
    );
  }

  // NUEVO: Validaciones defensivas para evitar errores de .map()
  const safeData = {
    metrics: state.data.metrics || {
      total_products: 0,
      total_inventory_value: 0,
      sales_this_month: 0,
      sales_value_this_month: 0,
      active_alerts: 0,
      sales_growth_percentage: 0,
      inventory_turnover: 0,
      forecast_accuracy: 0
    },
    trends: {
      monthly_data: state.data.trends?.monthly_data || [],
      inventory_status: state.data.trends?.inventory_status || []
    },
    top_products: state.data.top_products || [],
    recent_alerts: state.data.recent_alerts || []
  };

  const { metrics, trends, top_products, recent_alerts } = safeData;

  // Funciones de formato mejoradas
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-PE', {
      style: 'currency',
      currency: 'PEN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('es-PE', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatLargeNumber = (value: number) => {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(1) + 'K';
    }
    return value.toString();
  };

  // Tooltip personalizado SÚPER COMPLETO con ambas métricas
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-xl border border-gray-200 dark:border-gray-600 min-w-[320px]">
          <p className="font-bold text-gray-900 dark:text-white mb-3 text-center border-b pb-2">
            📅 {label} 2024/2025
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <div 
                  className="w-4 h-4 rounded-full shadow-sm"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="font-semibold text-gray-800 dark:text-gray-100">
                  {entry.name === 'sales' || entry.name === 'sales_value' ? '🛒 VENTAS' :
                   entry.name === 'entries' || entry.name === 'purchase_value' ? '📦 COMPRAS' :
                   entry.name === 'inventory_value' ? '💰 VALOR INVENTARIO' :
                   entry.name === 'sales_units' ? '📊 UNIDADES VENDIDAS' :
                   entry.name === 'purchase_units' ? '📊 UNIDADES COMPRADAS' :
                   entry.name === 'transactions_count' ? '📋 TRANSACCIONES' :
                   entry.name.toUpperCase()}
                </span>
              </div>
              
              {/* Mostrar valores financieros y de volumen juntos */}
              {(entry.name === 'sales' || entry.name === 'sales_value') && (
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">💰 Ingresos:</span>
                    <span className="font-bold text-green-600 dark:text-green-400">
                      {formatCurrency(entry.value)}
                    </span>
                  </div>
                  {/* Buscar datos de unidades en el payload */}
                  {payload.find((p: any) => p.dataKey === 'sales_units') && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-300">📊 Unidades:</span>
                      <span className="font-bold text-blue-600 dark:text-blue-400">
                        {formatNumber(payload.find((p: any) => p.dataKey === 'sales_units')?.value || 0)} uds.
                      </span>
                    </div>
                  )}
                </div>
              )}
              
              {(entry.name === 'entries' || entry.name === 'purchase_value') && (
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">💰 Costo:</span>
                    <span className="font-bold text-orange-600 dark:text-orange-400">
                      {formatCurrency(entry.value)}
                    </span>
                  </div>
                  {/* Buscar datos de unidades en el payload */}
                  {payload.find((p: any) => p.dataKey === 'purchase_units') && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-300">📊 Unidades:</span>
                      <span className="font-bold text-emerald-600 dark:text-emerald-400">
                        {formatNumber(payload.find((p: any) => p.dataKey === 'purchase_units')?.value || 0)} uds.
                      </span>
                    </div>
                  )}
                </div>
              )}
              
              {entry.name === 'inventory_value' && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-300">💰 Valor Total:</span>
                  <span className="font-bold text-purple-600 dark:text-purple-400">
                    {formatCurrency(entry.value)}
                  </span>
                </div>
              )}
              
              {entry.name === 'transactions_count' && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-300">📋 Operaciones:</span>
                  <span className="font-bold text-gray-600 dark:text-gray-400">
                    {entry.value} transacciones
                  </span>
                </div>
              )}
            </div>
          ))}
          
          <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-600 bg-blue-50 dark:bg-blue-900/20 p-2 rounded">
            <p className="text-xs text-blue-800 dark:text-blue-200 text-center font-semibold">
              💡 ANÁLISIS COMPLETO: Datos financieros Y operativos
            </p>
            <p className="text-xs text-blue-700 dark:text-blue-300 text-center mt-1">
              🔍 Ventas/Compras en SOLES + UNIDADES para decisiones integrales
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  // Tooltip para gráfico de pie mejorado
  const PieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600">
          <div className="flex items-center gap-2 mb-1">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: data.color }}
            />
            <span className="font-semibold text-gray-900 dark:text-white">
              {data.name}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {data.value} productos ({data.percentage}%)
          </p>
        </div>
      );
    }
    return null;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <AlertTriangle className="h-4 w-4" />;
      case 'acknowledged': return <Clock className="h-4 w-4" />;
      case 'resolved': return <CheckCircle className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  // Componente para métricas avanzadas
  const AdvancedMetricCard: React.FC<{
    title: string;
    value: string | number;
    subtitle?: string;
    trend?: number;
    icon: React.ReactNode;
    color: string;
    onClick?: () => void;
  }> = ({ title, value, subtitle, trend, icon, color, onClick }) => {
    return (
      <div 
        className={`bg-gradient-to-br ${color} border-opacity-50 hover:shadow-lg transition-all duration-300 cursor-pointer transform hover:scale-105 rounded-lg border p-6`}
        onClick={onClick}
      >
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium opacity-80">{title}</p>
            <p className="text-3xl font-bold">{value}</p>
            {subtitle && (
              <p className="text-sm opacity-70">{subtitle}</p>
            )}
            {trend !== undefined && (
              <div className="flex items-center text-sm">
                {trend >= 0 ? (
                  <ArrowUp className="h-4 w-4 mr-1" />
                ) : (
                  <ArrowDown className="h-4 w-4 mr-1" />
                )}
                <span>{Math.abs(trend)}% vs anterior</span>
              </div>
            )}
          </div>
          <div className="p-3 bg-white bg-opacity-20 rounded-full">
            {icon}
          </div>
        </div>
      </div>
    );
  };

  // Componente para gráfico interactivo mejorado
  const InteractiveChart: React.FC<{
    data: any[];
    type: 'line' | 'bar' | 'area' | 'composed';
    title: string;
    height?: number;
    showLegend?: boolean;
    onDataPointClick?: (data: any) => void;
  }> = ({ data, type, title, height = 300, showLegend = true, onDataPointClick }) => {
    const [isFullscreen, setIsFullscreen] = useState(false);

    const ChartComponent = {
      line: LineChart,
      bar: BarChart,
      area: AreaChart,
      composed: ComposedChart
    }[type];

    return (
      <Card className="bg-white dark:bg-gray-800 shadow-lg border border-gray-200 dark:border-gray-700">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Activity className="h-5 w-5" />
              {title}
            </CardTitle>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-2"
              >
                {isFullscreen ? <ArrowDown className="h-4 w-4" /> : <ArrowUp className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className={isFullscreen ? 'fixed inset-0 z-50 bg-white dark:bg-gray-900 p-6' : ''}>
            <ResponsiveContainer width="100%" height={isFullscreen ? window.innerHeight - 200 : height}>
              <ChartComponent data={data} onClick={onDataPointClick}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis 
                  dataKey="month" 
                  tick={{ fontSize: 12 }}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis 
                  yAxisId="left"
                  stroke="#6b7280"
                  fontSize={11}
                  tick={{ fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickFormatter={formatLargeNumber}
                />
                <YAxis 
                  yAxisId="right"
                  orientation="right"
                  stroke="#6b7280"
                  fontSize={11}
                  tick={{ fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickFormatter={(value) => formatLargeNumber(value)}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                {showLegend && <Legend />}
                
                {type === 'line' && (
                  <>
                    <Line yAxisId="left" type="monotone" dataKey="sales" stroke="#3b82f6" strokeWidth={3} dot={{ r: 6 }} />
                    <Line yAxisId="left" type="monotone" dataKey="entries" stroke="#10b981" strokeWidth={3} dot={{ r: 6 }} />
                  </>
                )}
                
                {type === 'bar' && (
                  <>
                    <Bar yAxisId="left" dataKey="sales" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar yAxisId="left" dataKey="entries" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </>
                )}
                
                {type === 'area' && (
                  <>
                    <Area yAxisId="right" type="monotone" dataKey="inventory_value" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
                    <Area yAxisId="left" type="monotone" dataKey="transactions_count" stackId="2" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.6} />
                  </>
                )}
                
                {type === 'composed' && (
                  <>
                    <Bar yAxisId="left" dataKey="sales" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Line yAxisId="right" type="monotone" dataKey="inventory_value" stroke="#ef4444" strokeWidth={3} dot={{ r: 6 }} />
                  </>
                )}
              </ChartComponent>
            </ResponsiveContainer>
            
            {isFullscreen && (
              <Button
                className="absolute top-4 right-4 bg-gray-800 hover:bg-gray-700"
                onClick={() => setIsFullscreen(false)}
              >
                <ArrowDown className="h-4 w-4 mr-2" />
                Cerrar
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto p-6 space-y-8">
        {/* Header mejorado con nuevas funcionalidades */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                  <BarChart3 className="h-8 w-8 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                    Analytics Avanzado
                  </h1>
                  <p className="text-gray-600 dark:text-gray-400">
                    Dashboards interactivos con datos en tiempo real
                    {state.autoRefresh && (
                      <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></div>
                        Auto-actualización activa
                      </span>
                    )}
                  </p>
                </div>
              </div>
              {state.error && (
                <Alert className="bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800">
                  <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                  <AlertDescription className="text-amber-800 dark:text-amber-200">
                    {state.error}
                  </AlertDescription>
                </Alert>
              )}
            </div>

            <div className="flex flex-wrap gap-3">
              {/* Controles existentes */}
              <Select 
                value={state.selectedPeriod} 
                onValueChange={(value) => setState(prev => ({ ...prev, selectedPeriod: value }))}
              >
                <SelectTrigger className="w-40 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600">
                  <Calendar className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Período" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="3months">Últimos 3 meses</SelectItem>
                  <SelectItem value="6months">Últimos 6 meses</SelectItem>
                  <SelectItem value="12months">Último año</SelectItem>
                  <SelectItem value="24months">Últimos 2 años</SelectItem>
                </SelectContent>
              </Select>

              <Select 
                value={state.selectedView} 
                onValueChange={(value) => setState(prev => ({ ...prev, selectedView: value }))}
              >
                <SelectTrigger className="w-40 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600">
                  <Eye className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Vista" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="overview">Vista General</SelectItem>
                  <SelectItem value="sales">Ventas</SelectItem>
                  <SelectItem value="inventory">Inventario</SelectItem>
                  <SelectItem value="forecasting">Predicciones</SelectItem>
                  <SelectItem value="comparative">Comparativo</SelectItem>
                </SelectContent>
              </Select>

              {/* Nuevos controles */}
              <Button
                variant="outline"
                onClick={() => setState(prev => ({ ...prev, autoRefresh: !prev.autoRefresh }))}
                className={state.autoRefresh ? 'bg-green-50 border-green-200 text-green-700' : ''}
              >
                <Clock className="h-4 w-4 mr-2" />
                Auto-actualizar
              </Button>

              <Button
                variant="outline"
                onClick={() => setState(prev => ({ ...prev, compareMode: !prev.compareMode }))}
                className={state.compareMode ? 'bg-purple-50 border-purple-200 text-purple-700' : ''}
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                Comparar
              </Button>

              <div className="relative">
                <Button
                  variant="outline"
                  onClick={() => setState(prev => ({ ...prev, showExportMenu: !prev.showExportMenu }))}
                  disabled={state.isExporting}
                >
                  <Download className="h-4 w-4 mr-2" />
                  {state.isExporting ? 'Exportando...' : 'Exportar'}
                </Button>
                
                {state.showExportMenu && (
                  <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10">
                    <div className="p-2">
                      <Button
                        variant="ghost"
                        className="w-full justify-start"
                        onClick={() => handleExport('pdf')}
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        Exportar PDF
                      </Button>
                      <Button
                        variant="ghost"
                        className="w-full justify-start"
                        onClick={() => handleExport('excel')}
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        Exportar Excel
                      </Button>
                      <Button
                        variant="ghost"
                        className="w-full justify-start"
                        onClick={handleShare}
                      >
                        <Globe className="h-4 w-4 mr-2" />
                        Compartir
                      </Button>
                    </div>
                  </div>
                )}
              </div>
              
              <Button 
                onClick={refreshData} 
                disabled={state.isRefreshing}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${state.isRefreshing ? 'animate-spin' : ''}`} />
                Actualizar
              </Button>
            </div>
          </div>
        </div>

        {/* Métricas principales mejoradas */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <AdvancedMetricCard
            title="Ingresos del Mes"
            value={formatCurrency(metrics.sales_value_this_month)}
            subtitle={`${formatNumber(metrics.sales_this_month)} unidades`}
            trend={metrics.sales_growth_percentage}
            icon={<DollarSign className="h-8 w-8 text-white" />}
            color="from-green-50 to-emerald-100 dark:from-green-900/20 dark:to-emerald-900/20 text-green-900 dark:text-green-100"
            onClick={() => setState(prev => ({ ...prev, selectedView: 'sales' }))}
          />

          <AdvancedMetricCard
            title="Productos Activos"
            value={formatNumber(metrics.total_products)}
            subtitle={`Valor: ${formatCurrency(metrics.total_inventory_value)}`}
            icon={<Package className="h-8 w-8 text-white" />}
            color="from-blue-50 to-cyan-100 dark:from-blue-900/20 dark:to-cyan-900/20 text-blue-900 dark:text-blue-100"
            onClick={() => setState(prev => ({ ...prev, selectedView: 'inventory' }))}
          />

          <AdvancedMetricCard
            title="Rotación de Inventario"
            value={`${metrics.inventory_turnover}x`}
            subtitle="veces por año"
            icon={<Activity className="h-8 w-8 text-white" />}
            color="from-purple-50 to-violet-100 dark:from-purple-900/20 dark:to-violet-900/20 text-purple-900 dark:text-purple-100"
          />

          <AdvancedMetricCard
            title="Precisión ML"
            value={`${metrics.forecast_accuracy}%`}
            subtitle="predicciones correctas"
            icon={<Target className="h-8 w-8 text-white" />}
            color="from-orange-50 to-red-100 dark:from-orange-900/20 dark:to-red-900/20 text-orange-900 dark:text-orange-100"
            onClick={() => setState(prev => ({ ...prev, selectedView: 'forecasting' }))}
          />
        </div>

        {/* Gráficos interactivos mejorados */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <InteractiveChart
            data={trends.monthly_data}
            type="composed"
            title="Tendencias de Ventas e Inventario"
            height={400}
            onDataPointClick={(data) => console.log('Clicked:', data)}
          />

          <InteractiveChart
            data={trends.monthly_data}
            type="area"
            title="Evolución del Valor de Inventario"
            height={400}
          />
        </div>

        {/* Gráficos principales - Layout mejorado con tooltips personalizados */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Tendencias de Ventas */}
          <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-xl">
            <CardHeader className="pb-4 border-b border-gray-100 dark:border-gray-700">
              <CardTitle className="flex items-center text-gray-900 dark:text-white">
                <TrendingUp className="h-5 w-5 mr-2 text-blue-600" />
                Tendencias de Ventas e Inventario
              </CardTitle>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Comparación mensual de ventas, compras y valor de inventario
              </p>
            </CardHeader>
            <CardContent className="pt-6">
              <ResponsiveContainer width="100%" height={350}>
                <ComposedChart data={trends.monthly_data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
                  <XAxis 
                    dataKey="month" 
                    stroke="#6b7280"
                    fontSize={11}
                    tick={{ fill: '#6b7280' }}
                    axisLine={{ stroke: '#d1d5db' }}
                  />
                  <YAxis 
                    yAxisId="left"
                    stroke="#6b7280"
                    fontSize={11}
                    tick={{ fill: '#6b7280' }}
                    axisLine={{ stroke: '#d1d5db' }}
                    tickFormatter={formatLargeNumber}
                    domain={[0, 'dataMax']}
                    label={{ value: 'Unidades', angle: -90, position: 'insideLeft', textAnchor: 'middle' }}
                  />
                  <YAxis 
                    yAxisId="right"
                    orientation="right"
                    stroke="#6b7280"
                    fontSize={11}
                    tick={{ fill: '#6b7280' }}
                    axisLine={{ stroke: '#d1d5db' }}
                    tickFormatter={(value) => formatLargeNumber(value)}
                    domain={[200000, 350000]}
                    label={{ value: 'Valor (S/.)', angle: 90, position: 'insideRight', textAnchor: 'middle' }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend 
                    wrapperStyle={{ paddingTop: '20px' }}
                    iconType="rect"
                  />
                  <Bar 
                    yAxisId="left"
                    dataKey="sales" 
                    fill="#3b82f6" 
                    name="Ventas"
                    radius={[4, 4, 0, 0]}
                    opacity={0.8}
                  />
                  <Bar 
                    yAxisId="left"
                    dataKey="entries" 
                    fill="#10b981" 
                    name="Compras"
                    radius={[4, 4, 0, 0]}
                    opacity={0.8}
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="inventory_value" 
                    stroke="#f59e0b" 
                    strokeWidth={3}
                    name="Valor Inventario"
                    dot={{ fill: '#f59e0b', strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 8, fill: '#f59e0b' }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Estado del Inventario */}
          <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-xl">
            <CardHeader className="pb-4 border-b border-gray-100 dark:border-gray-700">
              <CardTitle className="flex items-center text-gray-900 dark:text-white">
                <Package className="h-5 w-5 mr-2 text-green-600" />
                Estado del Inventario
              </CardTitle>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Distribución actual por estado de stock
              </p>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 gap-6">
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={trends.inventory_status}
                      cx="50%"
                      cy="50%"
                      outerRadius={85}
                      innerRadius={40}
                      dataKey="value"
                      label={({ name, percentage }) => `${percentage}%`}
                      labelLine={false}
                      stroke="#ffffff"
                      strokeWidth={2}
                    >
                      {trends.inventory_status.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.color}
                          style={{
                            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))',
                            transition: 'all 0.3s ease'
                          }}
                        />
                      ))}
                    </Pie>
                    <Tooltip content={<PieTooltip />} />
                  </PieChart>
                </ResponsiveContainer>

                <div className="space-y-3">
                  {trends.inventory_status.map((status, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 rounded-xl shadow-sm hover:shadow-md transition-shadow">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-5 h-5 rounded-full shadow-inner"
                          style={{ backgroundColor: status.color }}
                        />
                        <span className="font-semibold text-gray-900 dark:text-white">
                          {status.name}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-xl text-gray-900 dark:text-white">
                          {status.value}
                        </p>
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          {status.percentage}% del total
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Gráfico adicional de tendencias detallado */}
        <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-xl">
          <CardHeader className="pb-4 border-b border-gray-100 dark:border-gray-700">
            <CardTitle className="flex items-center text-gray-900 dark:text-white">
              <Activity className="h-5 w-5 mr-2 text-purple-600" />
              Análisis Detallado de Transacciones
            </CardTitle>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Volumen de transacciones y evolución del valor de inventario
            </p>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={trends.monthly_data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <defs>
                  <linearGradient id="colorInventory" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1}/>
                  </linearGradient>
                  <linearGradient id="colorTransactions" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
                <XAxis 
                  dataKey="month" 
                  stroke="#6b7280"
                  fontSize={11}
                  tick={{ fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                />
                <YAxis 
                  yAxisId="left"
                  stroke="#6b7280"
                  fontSize={11}
                  tick={{ fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickFormatter={formatLargeNumber}
                />
                <YAxis 
                  yAxisId="right"
                  orientation="right"
                  stroke="#6b7280"
                  fontSize={11}
                  tick={{ fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickFormatter={formatLargeNumber}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  wrapperStyle={{ paddingTop: '20px' }}
                  iconType="rect"
                />
                <Area 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="inventory_value" 
                  stackId="1" 
                  stroke="#8b5cf6" 
                  fill="url(#colorInventory)"
                  name="Valor Inventario"
                  strokeWidth={2}
                />
                <Area 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="transactions_count" 
                  stackId="2" 
                  stroke="#f59e0b" 
                  fill="url(#colorTransactions)"
                  name="Transacciones"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Sección de productos top y alertas */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Top Productos */}
          <Card className="lg:col-span-2 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center text-gray-900 dark:text-white">
                <Target className="h-5 w-5 mr-2 text-purple-600" />
                Productos Más Vendidos (Últimos 30 días)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {top_products.map((product, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-600 rounded-full text-white font-bold">
                        #{index + 1}
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 dark:text-white">
                          {product.name}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {product.category} • {formatCurrency(product.unit_cost)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-lg text-gray-900 dark:text-white">
                        {formatNumber(product.sales)}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Stock: {formatNumber(product.current_stock)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Alertas Recientes */}
          <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center text-gray-900 dark:text-white">
                <Zap className="h-5 w-5 mr-2 text-yellow-600" />
                Alertas Recientes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recent_alerts.map((alert) => (
                  <div key={alert.id} className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className={`p-1 rounded ${getSeverityColor(alert.severity)}`}>
                          {getStatusIcon(alert.status)}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {alert.message}
                          </p>
                          {alert.product_name && (
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              Producto: {alert.product_name}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            {new Date(alert.created_at).toLocaleDateString('es-MX', {
                              day: 'numeric',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                        </div>
                      </div>
                      <Badge className={getSeverityColor(alert.severity)}>
                        {alert.severity}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer con información de actualización */}
        <div className="text-center text-sm text-gray-500 dark:text-gray-400 py-4">
          <p>
            Última actualización: {new Date(state.data.last_updated).toLocaleString('es-MX')}
          </p>
          <p className="mt-1">
            Sistema de analytics conectado con datos en tiempo real
          </p>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
