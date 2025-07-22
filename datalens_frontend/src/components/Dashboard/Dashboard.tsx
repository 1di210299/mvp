import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Alert,
  AlertDescription,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Input
} from '../ui';
import { IntelligentBriefing } from './IntelligentBriefing';
import {
  BarChart3,
  Package,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  Users,
  RefreshCw,
  Eye,
  Bell,
  Calendar,
  Target,
  Zap,
  Activity,
  Filter,
  Search,
  Download,
  Settings
} from '../ui/icons';
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
  ComposedChart
} from 'recharts';
import {
  inventoryService,
  alertService,
  filterService
} from '../../services/api';
import { forecastingService } from '../../services/forecastingService';
import { Transaction, Product, AlertData } from '../../types';
import { useTheme } from '../../contexts/ThemeContext';
import './Dashboard.css';

interface ExtendedDashboardStats {
  total_products: number;
  total_value: number;
  low_stock_alerts: number;
  total_transactions_today: number;
  active_customers: number;
  pipeline_value: number;
  // NUEVO: Métricas de ventas y compras
  sales_value: number;
  sales_count: number;
  purchases_value: number;
  purchases_count: number;
  net_profit: number;
}

interface DashboardAlert {
  id: number;
  title: string;
  message: string;
  severity: string;
  created_at: string;
}

interface DashboardTransaction {
  id: number;
  product_name: string;
  quantity: number;
  transaction_type: string;
  created_at: string;
}

interface DashboardForecast {
  product_name: string;
  predicted_demand: number;
  confidence: number;
  period: string;
}

interface DashboardData {
  stats: ExtendedDashboardStats;
  alerts: DashboardAlert[];
  forecasts: DashboardForecast[];
  transactions: DashboardTransaction[];
  chartData: {
    stockLevels: Array<{ warehouse: string; current_stock: number; min_stock: number; max_stock: number }>;
    salesTrend: Array<{ date: string; sales: number; forecast: number }>;
    categoryDistribution: Array<{ category: string; value: number }>;
    alertTrends: Array<{ date: string; alerts: number }>;
  };
}

// **NUEVO: Hook personalizado para debounce**
const useDebounce = (value: any, delay: number) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

const Dashboard: React.FC = () => {
  const { actualTheme } = useTheme();
  const isDarkMode = actualTheme === 'dark';
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [showSecondaryMetrics, setShowSecondaryMetrics] = useState(false);
  
  // NUEVO: Estados para filtros y fecha
  const [filters, setFilters] = useState({
    dateRange: '7days',
    category: 'all',
    warehouse: 'all',
    status: 'all',
    searchTerm: '',
    customStartDate: '',
    customEndDate: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [originalData, setOriginalData] = useState<DashboardData | null>(null);
  const [filterOptions, setFilterOptions] = useState({
    categories: [],
    locations: [],
    warehouses: [],
    statuses: [],
    transaction_types: [],
    suppliers: []
  });

  // **NUEVO: Cache para evitar llamadas duplicadas**
  const [dataCache, setDataCache] = useState<Map<string, {data: DashboardData, timestamp: number}>>(new Map());
  const [optionsLoaded, setOptionsLoaded] = useState(false);

  // **NUEVO: Debounce para filtros**
  const debouncedFilters = useDebounce(filters, 500);

  // **NUEVO: Memoizar parámetros de filtros para backend**
  const backendFilters = useMemo(() => {
    const today = new Date();
    let startDate = '', endDate = '';

    switch (debouncedFilters.dateRange) {
      case '7days':
        startDate = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        endDate = today.toISOString().split('T')[0];
        break;
      case '30days':
        startDate = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        endDate = today.toISOString().split('T')[0];
        break;
      case '90days':
        startDate = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        endDate = today.toISOString().split('T')[0];
        break;
      case 'all':
        // Para "all", no enviar filtros de fecha al backend
        startDate = '';
        endDate = '';
        break;
      case 'custom':
        if (debouncedFilters.customStartDate && debouncedFilters.customEndDate) {
          startDate = debouncedFilters.customStartDate;
          endDate = debouncedFilters.customEndDate;
        } else {
          // Si no hay fechas personalizadas, usar últimos 7 días por defecto
          startDate = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
          endDate = today.toISOString().split('T')[0];
        }
        break;
      default:
        startDate = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        endDate = today.toISOString().split('T')[0];
    }

    return {
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      category: debouncedFilters.category !== 'all' ? debouncedFilters.category : undefined,
      warehouse: debouncedFilters.warehouse !== 'all' ? debouncedFilters.warehouse : undefined,
      status: debouncedFilters.status !== 'all' ? debouncedFilters.status : undefined,
    };
  }, [debouncedFilters]);

  // **OPTIMIZADO: useEffect inicial solo para filtros**
  useEffect(() => {
    if (!optionsLoaded) {
      loadFilterOptions();
    }
    loadDashboardData();
  }, []);

  // **OPTIMIZADO: useCallback para funciones que se usan en dependencias**
  const loadFilterOptions = useCallback(async () => {
    if (optionsLoaded) return; // Evitar cargas duplicadas

    try {
      console.log('📊 Dashboard: Iniciando carga de opciones de filtros...');
      const options = await filterService.getFilterOptions();
      console.log('📊 Dashboard: Opciones recibidas:', options);
      
      const safeOptions = {
        categories: Array.isArray(options?.categories) ? options.categories : [],
        locations: Array.isArray(options?.locations) ? options.locations : [],
        warehouses: Array.isArray(options?.warehouses) ? options.warehouses : [],
        statuses: Array.isArray(options?.statuses) ? options.statuses : [],
        transaction_types: Array.isArray(options?.transaction_types) ? options.transaction_types : [],
        suppliers: Array.isArray(options?.suppliers) ? options.suppliers : []
      };
      
      setFilterOptions(safeOptions);
      setOptionsLoaded(true);
      console.log('📊 Dashboard: Estado de filtros actualizado con datos seguros');
    } catch (error) {
      console.error('❌ Dashboard: Error cargando opciones de filtros:', error);
      const fallbackOptions = {
        categories: [],
        locations: [],
        warehouses: [],
        statuses: [],
        transaction_types: [],
        suppliers: []
      };
      setFilterOptions(fallbackOptions);
      setOptionsLoaded(true);
    }
  }, [optionsLoaded]);

  const loadDashboardData = useCallback(async () => {
    // **NUEVO: Verificar cache primero (reducir tiempo de cache para filtros de fecha)**
    const cacheKey = JSON.stringify(backendFilters);
    const cached = dataCache.get(cacheKey);
    const now = Date.now();
    
    // Reducir tiempo de cache cuando hay filtros aplicados (10 segundos) vs sin filtros (1 minuto)
    const hasFilters = backendFilters.start_date || backendFilters.end_date || backendFilters.warehouse || backendFilters.category || backendFilters.status;
    const cacheTimeout = hasFilters ? 10000 : 60000;
    
    // Si hay datos en cache y son recientes, usarlos
    if (cached && (now - cached.timestamp) < cacheTimeout) {
      console.log(`📊 Dashboard: Usando datos del cache (${cacheTimeout/1000}s timeout)`);
      setData(cached.data);
      setOriginalData(cached.data);
      setLoading(false);
      return;
    }

    try {
      console.log('🔍 Dashboard Principal: Iniciando carga de datos con filtros:', backendFilters);
      setLoading(true);
      setError('');

      const filterParams = Object.fromEntries(
        Object.entries(backendFilters).filter(([_, value]) => value !== undefined)
      );
      
      console.log('📋 Parámetros de filtro para backend:', filterParams);

      // **OPTIMIZADO: Llamadas paralelas en lugar de secuenciales**
      const [statsData, alertsDashboard, alertsList, forecasts, transactions] = await Promise.all([
        inventoryService.getInventoryDashboard(filterParams),
        alertService.getAlertsDashboard(filterParams),
        alertService.getAlerts(filterParams),
        forecastingService.getForecasts(),
        inventoryService.getTransactions(filterParams)
      ]);
      
      // NUEVO: Log para verificar métricas de ventas/compras
      if (statsData?.sales_value !== undefined || statsData?.purchases_value !== undefined) {
        console.log('💰 Dashboard: Métricas de ventas/compras recibidas:', {
          sales_value: statsData.sales_value,
          sales_count: statsData.sales_count,
          purchases_value: statsData.purchases_value,
          purchases_count: statsData.purchases_count,
          net_profit: statsData.net_profit
        });
      }

      console.log('📊 Dashboard Principal: Stats data:', statsData);
      console.log('� Dashboard Principal: Datos para gráficos recibidos:', {
        stock_by_warehouse: statsData?.stock_by_warehouse?.length || 0,
        sales_trend_data: statsData?.sales_trend_data?.length || 0,
        products_by_category: statsData?.products_by_category?.length || 0,
        stock_by_category: statsData?.stock_by_category?.length || 0
      });
      console.log('�🚨 Dashboard Principal: Alerts dashboard data:', alertsDashboard);
      console.log('📋 Dashboard Principal: Alerts list data:', alertsList);

      const finalStats = {
        total_products: statsData?.total_products || 0,
        total_value: statsData?.total_stock_value || 0,
        low_stock_alerts: statsData?.low_stock_alerts || 0,
        total_transactions_today: statsData?.recent_transactions || 0,
        active_customers: statsData?.active_customers || 0,
        pipeline_value: statsData?.pipeline_value || 0,
        // Usar campos genéricos primero, luego específicos como fallback
        sales_value: statsData?.sales_value || statsData?.sales_last_7_days || 0,
        sales_count: statsData?.sales_count || 0,
        purchases_value: statsData?.purchases_value || statsData?.purchases_last_7_days || 0,
        purchases_count: statsData?.purchases_count || 0,
        net_profit: (statsData?.sales_value || statsData?.sales_last_7_days || 0) - 
                   (statsData?.purchases_value || statsData?.purchases_last_7_days || 0),
      };
      
      console.log('✅ Dashboard: Stats finales con ventas/compras:', {
        sales_value: finalStats.sales_value,
        purchases_value: finalStats.purchases_value,
        net_profit: finalStats.net_profit,
        filtros_aplicados: filterParams
      });

      console.log('✅ Dashboard Principal: Stats finales:', finalStats);

      const processedAlerts = Array.isArray(alertsList?.results) ? alertsList.results : [];
      console.log('🔔 Dashboard Principal: Alertas procesadas:', processedAlerts.length, 'alertas');

      // Actualizar finalStats con el número correcto de alertas
      const alertsCount = alertsDashboard?.active_alerts || processedAlerts.length || 0;

      // **CORREGIDO: Mapear datos de forecasts al formato correcto**
      const processedForecasts: DashboardForecast[] = Array.isArray(forecasts) 
        ? forecasts.slice(0, 10).map((forecast: any) => ({
            product_name: forecast.product_name || forecast.product || 'Producto desconocido',
            predicted_demand: Number(forecast.predicted_demand) || 0,
            confidence: Number(forecast.confidence_level) || Number(forecast.confidence) || 0,
            period: forecast.period || forecast.forecast_date || 'Próximo mes'
          }))
        : [];

      const dashboardData: DashboardData = {
        stats: finalStats,
        alerts: processedAlerts,
        forecasts: processedForecasts,
        transactions: Array.isArray(transactions?.results) ? transactions.results : [],
        chartData: {
          stockLevels: generateStockLevelsChart(statsData),
          salesTrend: generateSalesTrendChart(statsData.sales_trend_data || []),
          categoryDistribution: generateCategoryChart(statsData),
          alertTrends: generateAlertTrendsChart(processedAlerts)
        }
      };

      console.log('📊 Dashboard: Datos de gráficos generados:', {
        stockLevels: dashboardData.chartData.stockLevels?.length || 0,
        salesTrend: dashboardData.chartData.salesTrend?.length || 0,
        categoryDistribution: dashboardData.chartData.categoryDistribution?.length || 0,
        alertTrends: dashboardData.chartData.alertTrends?.length || 0
      });

      // **NUEVO: Guardar en cache**
      const newCache = new Map(dataCache);
      newCache.set(cacheKey, { data: dashboardData, timestamp: now });
      setDataCache(newCache);

      setData(dashboardData);
      setOriginalData(dashboardData);
      setLoading(false);

    } catch (error) {
      console.error('❌ Dashboard Principal: Error cargando datos:', error);
      setError('Error cargando datos del dashboard');
      setLoading(false);
    }
  }, [backendFilters, dataCache]);

  // **OPTIMIZADO: useEffect para cambios en filtros (con debounce)**
  useEffect(() => {
    if (optionsLoaded) {
      loadDashboardData();
    }
  }, [backendFilters, optionsLoaded]); // Cambiar dependencia para evitar loops

  // **OPTIMIZADO: Auto-refresh solo si está habilitado**
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        // Limpiar cache en auto-refresh para obtener datos frescos
        setDataCache(new Map());
        loadDashboardData();
      }, 30000); // 30 segundos
      return () => clearInterval(interval);
    }
  }, [autoRefresh, loadDashboardData]);

  const refreshDashboard = useCallback(async () => {
    setRefreshing(true);
    // **NUEVO: Limpiar cache al hacer refresh manual**
    setDataCache(new Map());
    await loadDashboardData();
    setRefreshing(false);
  }, [loadDashboardData]);

  // Funciones auxiliares para generar datos de gráficos
  const generateStockLevelsChart = (statsData: any) => {
    if (!statsData.stock_by_warehouse || !Array.isArray(statsData.stock_by_warehouse)) return [];
    
    console.log('📊 Generando gráfico de stock por almacén:', statsData.stock_by_warehouse);
    
    return statsData.stock_by_warehouse.map((item: any) => ({
      warehouse: item.warehouse || item.name,
      current_stock: Number(item.current_stock || item.stock || 0),
      min_stock: Number(item.min_stock || 0),
      max_stock: Number(item.max_stock || 0)
    }));
  };

  const generateSalesTrendChart = (salesTrendData: any[]) => {
    if (!salesTrendData || !salesTrendData.length) {
      console.log('📊 No hay datos de ventas para generar gráfico de tendencia');
      return [];
    }
    
    console.log('📊 Generando gráfico de tendencia de ventas con', salesTrendData.length, 'días de datos');
    
    const chartData = salesTrendData.map(item => ({
      date: new Date(item.date).toLocaleDateString('es-ES', { 
        day: '2-digit', 
        month: '2-digit'
      }),
      sales: item.sales,
      forecast: item.sales * 1.1 // Estimación simple
    }));
    
    console.log('📊 Datos del gráfico de ventas generados:', chartData);
    return chartData;
  };

  const generateCategoryChart = (statsData: any) => {
    if (!statsData.products_by_category && !statsData.stock_by_category) return [];
    
    const categoryData = statsData.products_by_category || statsData.stock_by_category || [];
    console.log('📊 Datos de categorías recibidos:', categoryData);
    
    const formattedData = categoryData.map((item: any) => {
      const value = Number(item.count || item.total_products || item.total_stock || item.value || 0);
      const category = (item.category || item.name || 'Sin categoría').toString();
      console.log(`📊 Categoría: ${category}, Valor: ${value}`);
      return {
        category: category,
        value: value
      };
    }).filter((item: any) => item.value > 0); // Filtrar categorías sin productos
    
    console.log('📊 Datos formateados para gráfico:', formattedData);
    return formattedData;
  };

  const generateAlertTrendsChart = (alerts: DashboardAlert[]) => {
    const alertsByDate: Record<string, number> = {};
    
    alerts.forEach(alert => {
      const date = new Date(alert.created_at).toLocaleDateString();
      alertsByDate[date] = (alertsByDate[date] || 0) + 1;
    });

    return Object.entries(alertsByDate).map(([date, alerts]) => ({
      date,
      alerts
    }));
  };

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

  const formatShortNumber = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'secondary';
    }
  };

  const getTransactionTypeColor = (type: string) => {
    switch (type) {
      case 'IN':
      case 'PURCHASE': return 'secondary';
      case 'OUT':
      case 'SALE': return 'outline';
      default: return 'secondary';
    }
  };

  // NUEVO: Manejo de filtros
  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => {
      const newFilters = { ...prev, [key]: value };
      console.log(`🔄 Dashboard: Filtro ${key} = ${value}`);
      return newFilters;
    });
  };

  // NUEVO: Aplicar filtros a los datos
  const applyFilters = (data: DashboardData) => {
    let filteredData = { ...data };

    // Filtrar por rango de fechas
    if (filters.dateRange && filters.dateRange !== 'all') {
      const now = new Date();
      let startDate = new Date();
      let endDate = new Date();

      switch (filters.dateRange) {
        case '7days':
          startDate.setDate(now.getDate() - 7);
          break;
        case '30days':
          startDate.setDate(now.getDate() - 30);
          break;
        case '90days':
          startDate.setDate(now.getDate() - 90);
          break;
        case 'custom':
          if (filters.customStartDate) {
            startDate = new Date(filters.customStartDate);
          }
          if (filters.customEndDate) {
            endDate = new Date(filters.customEndDate);
          }
          break;
        default:
          break;
      }

      filteredData.transactions = data.transactions.filter(transaction => {
        const transactionDate = new Date(transaction.created_at);
        return transactionDate >= startDate && transactionDate <= endDate;
      });

      filteredData.alerts = data.alerts.filter(alert => {
        const alertDate = new Date(alert.created_at);
        return alertDate >= startDate && alertDate <= endDate;
      });
    }

    // Filtrar por término de búsqueda
    if (filters.searchTerm) {
      const searchTerm = filters.searchTerm.toLowerCase();
      filteredData.transactions = filteredData.transactions.filter(transaction => 
        transaction.product_name.toLowerCase().includes(searchTerm)
      );
      filteredData.alerts = filteredData.alerts.filter(alert => 
        alert.message.toLowerCase().includes(searchTerm)
      );
    }

    return filteredData;
  };



  // NUEVO: Aplicar filtro de búsqueda en tiempo real (solo frontend)
  useEffect(() => {
    if (!originalData) return;

    if (filters.searchTerm) {
      const searchTerm = filters.searchTerm.toLowerCase();
      const filteredTransactions = originalData.transactions.filter(transaction => 
        transaction.product_name.toLowerCase().includes(searchTerm)
      );
      const filteredAlerts = originalData.alerts.filter(alert => 
        alert.message.toLowerCase().includes(searchTerm) ||
        alert.title.toLowerCase().includes(searchTerm)
      );
      
      // Actualizar solo los datos que se pueden filtrar localmente
      setData(prev => prev ? {
        ...prev,
        transactions: filteredTransactions,
        alerts: filteredAlerts
      } : null);
    } else {
      // Si no hay término de búsqueda, restaurar datos originales
      setData(originalData);
    }
  }, [filters.searchTerm, originalData]);

  if (loading) {
    return (
      <div className={`min-h-screen bg-gradient-to-br transition-colors duration-300 flex items-center justify-center ${
        isDarkMode 
          ? 'from-slate-900 via-slate-800 to-slate-900' 
          : 'from-slate-50 via-blue-50 to-indigo-50'
      }`}>
        <div className="text-center">
          <div className="relative">
            <div className={`animate-spin rounded-full h-16 w-16 border-4 mx-auto mb-6 ${
              isDarkMode 
                ? 'border-blue-800 border-t-blue-400' 
                : 'border-blue-200 border-t-blue-600'
            }`}></div>
            <div className={`absolute inset-0 rounded-full h-16 w-16 border-4 border-transparent animate-ping mx-auto ${
              isDarkMode 
                ? 'border-t-blue-500' 
                : 'border-t-blue-400'
            }`}></div>
          </div>
          <p className={`text-lg font-medium ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>
            Cargando dashboard...
          </p>
          <p className={`text-sm mt-2 ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>
            Obteniendo datos en tiempo real
          </p>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className={`min-h-screen bg-gradient-to-br flex items-center justify-center transition-colors duration-300 ${
        isDarkMode 
          ? 'from-slate-900 via-red-900/20 to-orange-900/20' 
          : 'from-red-50 via-orange-50 to-yellow-50'
      }`}>
        <div className="text-center max-w-md mx-auto p-8">
          <div className={`rounded-2xl shadow-xl p-8 border ${
            isDarkMode 
              ? 'bg-slate-800 border-red-800/50' 
              : 'bg-white border-red-100'
          }`}>
            <AlertTriangle className={`h-16 w-16 mx-auto mb-6 ${
              isDarkMode ? 'text-red-400' : 'text-red-500'
            }`} />
            <h2 className={`text-xl font-semibold mb-4 ${
              isDarkMode ? 'text-white' : 'text-gray-900'
            }`}>Error de Conexión</h2>
            <p className={`mb-6 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-600'
            }`}>{error}</p>
            <Button 
              onClick={loadDashboardData}
              className={`text-white px-6 py-3 rounded-lg font-medium transition-colors ${
                isDarkMode 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-red-500 hover:bg-red-600'
              }`}
            >
              Reintentar Conexión
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gradient-to-br transition-colors duration-300 ${
      isDarkMode 
        ? 'from-slate-900 via-slate-800 to-slate-900' 
        : 'from-slate-50 via-blue-50 to-indigo-50'
    }`}>
      {/* Header compacto horizontal */}
      <div className={`border-b shadow-sm ${
        isDarkMode 
          ? 'bg-slate-800 border-slate-700' 
          : 'bg-white border-slate-200'
      }`}>
        <div className="max-w-full mx-auto px-4 py-6">
          {/* Todo en una sola fila horizontal */}
          <div className="flex items-center justify-between gap-4">
            {/* Lado izquierdo: Título */}
            <div className="flex-shrink-0">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 via-blue-800 to-indigo-800 dark:from-slate-100 dark:via-blue-200 dark:to-indigo-200 bg-clip-text text-transparent">
                Dashboard Principal
              </h1>
              <div className="text-sm text-slate-600 dark:text-slate-400 flex items-center gap-2 mt-1">
                <span className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full animate-pulse"></span>
                Vista general en tiempo real
              </div>
            </div>

            {/* Centro: Accesos rápidos */}
            <div className="flex-1 max-w-5xl">
              <div className="grid grid-cols-6 gap-2">
                <Button 
                  variant="outline" 
                  className="flex flex-col items-center p-3 h-auto bg-slate-50/50 dark:bg-slate-700/50 hover:bg-blue-50 dark:hover:bg-blue-900/20 border-slate-200 dark:border-slate-600 hover:border-blue-300 dark:hover:border-blue-500 transition-all duration-200 group"
                  onClick={() => window.location.href = '/app/products'}
                >
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg group-hover:bg-blue-200 dark:group-hover:bg-blue-800/70 transition-colors mb-1">
                    <Package className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors">Productos</span>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="flex flex-col items-center p-3 h-auto bg-slate-50/50 dark:bg-slate-700/50 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 border-slate-200 dark:border-slate-600 hover:border-emerald-300 dark:hover:border-emerald-500 transition-all duration-200 group"
                  onClick={() => window.location.href = '/app/inventory'}
                >
                  <div className="p-2 bg-emerald-100 dark:bg-emerald-900/50 rounded-lg group-hover:bg-emerald-200 dark:group-hover:bg-emerald-800/70 transition-colors mb-1">
                    <BarChart3 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300 group-hover:text-emerald-700 dark:group-hover:text-emerald-300 transition-colors">Inventario</span>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="flex flex-col items-center p-3 h-auto bg-slate-50/50 dark:bg-slate-700/50 hover:bg-red-50 dark:hover:bg-red-900/20 border-slate-200 dark:border-slate-600 hover:border-red-300 dark:hover:border-red-500 transition-all duration-200 group"
                  onClick={() => window.location.href = '/app/alerts'}
                >
                  <div className="p-2 bg-red-100 dark:bg-red-900/50 rounded-lg group-hover:bg-red-200 dark:group-hover:bg-red-800/70 transition-colors mb-1">
                    <Bell className="h-4 w-4 text-red-600 dark:text-red-400" />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300 group-hover:text-red-700 dark:group-hover:text-red-300 transition-colors">Alertas</span>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="flex flex-col items-center p-3 h-auto bg-slate-50/50 dark:bg-slate-700/50 hover:bg-purple-50 dark:hover:bg-purple-900/20 border-slate-200 dark:border-slate-600 hover:border-purple-300 dark:hover:border-purple-500 transition-all duration-200 group"
                  onClick={() => window.location.href = '/app/forecasting'}
                >
                  <div className="p-2 bg-purple-100 dark:bg-purple-900/50 rounded-lg group-hover:bg-purple-200 dark:group-hover:bg-purple-800/70 transition-colors mb-1">
                    <TrendingUp className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300 group-hover:text-purple-700 dark:group-hover:text-purple-300 transition-colors">Pronósticos</span>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="flex flex-col items-center p-3 h-auto bg-slate-50/50 dark:bg-slate-700/50 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 border-slate-200 dark:border-slate-600 hover:border-indigo-300 dark:hover:border-indigo-500 transition-all duration-200 group"
                  onClick={() => window.location.href = '/app/customers'}
                >
                  <div className="p-2 bg-indigo-100 dark:bg-indigo-900/50 rounded-lg group-hover:bg-indigo-200 dark:group-hover:bg-indigo-800/70 transition-colors mb-1">
                    <Users className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300 group-hover:text-indigo-700 dark:group-hover:text-indigo-300 transition-colors">Clientes</span>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="flex flex-col items-center p-3 h-auto bg-slate-50/50 dark:bg-slate-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/50 border-slate-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-gray-500 transition-all duration-200 group"
                  onClick={() => window.location.href = '/app/reports'}
                >
                  <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg group-hover:bg-gray-200 dark:group-hover:bg-gray-600 transition-colors mb-1">
                    <Calendar className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300 group-hover:text-gray-700 dark:group-hover:text-gray-300 transition-colors">Reportes</span>
                </Button>
              </div>
            </div>

            {/* Lado derecho: Actualización */}
            <div className="flex-shrink-0 flex items-center gap-4">
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {new Date().toLocaleTimeString('es-PE')}
              </div>
              <Button 
                onClick={refreshDashboard} 
                disabled={refreshing}
                variant="outline"
                className="flex items-center gap-2 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border-slate-300 dark:border-slate-600 hover:border-blue-300 dark:hover:border-blue-500 transition-all duration-200 px-4 py-2"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-400'}`} />
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{refreshing ? 'Actualizando...' : 'Actualizar'}</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-full mx-auto px-4 py-8">
        {/* NUEVO: Panel de filtros avanzado con fechas */}
        <Card 
          className="mb-8 bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm border-slate-200 dark:border-slate-700 shadow-lg card-filters dashboard-filters" 
          style={{ transform: 'none', willChange: 'auto' }}
        >
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Filter className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <CardTitle className="text-lg font-semibold text-slate-800 dark:text-slate-200">
                  Filtros y Controles
                </CardTitle>
              </div>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowFilters(!showFilters)}
                className="text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
              >
                {showFilters ? 'Ocultar' : 'Mostrar'} Filtros
              </Button>
            </div>
          </CardHeader>
          
          {showFilters && (
            <CardContent className="pt-0 dashboard-filters-content" style={{ transform: 'none', willChange: 'auto' }}>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 dashboard-filters-grid" style={{ transform: 'none', willChange: 'auto' }}>
                {/* Rango de fechas */}
                <div className="space-y-2 min-w-0">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Período
                  </label>
                  <Select 
                    value={filters.dateRange} 
                    onValueChange={(value) => handleFilterChange('dateRange', value)}
                  >
                    <SelectTrigger className="w-full min-w-[140px] bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600">
                      <Calendar className="h-4 w-4 mr-2 flex-shrink-0" />
                      <SelectValue placeholder="Seleccionar período" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos los datos</SelectItem>
                      <SelectItem value="7days">Últimos 7 días</SelectItem>
                      <SelectItem value="30days">Últimos 30 días</SelectItem>
                      <SelectItem value="90days">Últimos 90 días</SelectItem>
                      <SelectItem value="custom">Personalizado</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Fechas personalizadas - solo mostrar si está activo */}
                {filters.dateRange === 'custom' && (
                  <>
                    <div className="space-y-2 min-w-0">
                      <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        Fecha inicio
                      </label>
                      <Input
                        type="date"
                        value={filters.customStartDate}
                        onChange={(e) => handleFilterChange('customStartDate', e.target.value)}
                        className="w-full min-w-[140px] bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600"
                      />
                    </div>
                    <div className="space-y-2 min-w-0">
                      <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        Fecha fin
                      </label>
                      <Input
                        type="date"
                        value={filters.customEndDate}
                        onChange={(e) => handleFilterChange('customEndDate', e.target.value)}
                        className="w-full min-w-[140px] bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600"
                      />
                    </div>
                  </>
                )}

                {/* Categoría */}
                <div className="space-y-2 min-w-0">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Categoría
                  </label>
                  <Select 
                    value={filters.category} 
                    onValueChange={(value) => handleFilterChange('category', value)}
                  >
                    <SelectTrigger className="w-full min-w-[140px] bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600">
                      <Package className="h-4 w-4 mr-2 flex-shrink-0" />
                      <SelectValue placeholder="Todas las categorías" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas las categorías</SelectItem>
                      {filterOptions?.categories && Array.isArray(filterOptions.categories) ? 
                        filterOptions.categories.map((category: any) => (
                          <SelectItem key={category.id} value={category.id.toString()}>
                            {category.name}
                          </SelectItem>
                        )) : null
                      }
                    </SelectContent>
                  </Select>
                </div>

                {/* Almacén */}
                <div className="space-y-2 min-w-0">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Almacén
                  </label>
                  <Select 
                    value={filters.warehouse} 
                    onValueChange={(value) => handleFilterChange('warehouse', value)}
                  >
                    <SelectTrigger className="w-full min-w-[140px] bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600">
                      <Package className="h-4 w-4 mr-2 flex-shrink-0" />
                      <SelectValue placeholder="Todos los almacenes" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos los almacenes</SelectItem>
                      {filterOptions?.warehouses && Array.isArray(filterOptions.warehouses) ? 
                        filterOptions.warehouses.map((warehouse: any) => (
                          <SelectItem key={warehouse.id} value={warehouse.id.toString()}>
                            {warehouse.name || warehouse.warehouse}
                          </SelectItem>
                        )) : null
                      }
                    </SelectContent>
                  </Select>
                </div>

                {/* Estado */}
                <div className="space-y-2 min-w-0">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Estado
                  </label>
                  <Select 
                    value={filters.status} 
                    onValueChange={(value) => handleFilterChange('status', value)}
                  >
                    <SelectTrigger className="w-full min-w-[140px] bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600">
                      <Activity className="h-4 w-4 mr-2 flex-shrink-0" />
                      <SelectValue placeholder="Todos los estados" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos los estados</SelectItem>
                      {filterOptions?.statuses && Array.isArray(filterOptions.statuses) ? 
                        filterOptions.statuses.map((status: any) => (
                          <SelectItem key={status.id} value={status.id}>
                            {status.name}
                          </SelectItem>
                        )) : [
                          <SelectItem key="in_stock" value="in_stock">Con stock</SelectItem>,
                          <SelectItem key="low_stock" value="low_stock">Stock bajo</SelectItem>,
                          <SelectItem key="out_of_stock" value="out_of_stock">Sin stock</SelectItem>
                        ]
                      }
                    </SelectContent>
                  </Select>
                </div>

                {/* Búsqueda */}
                <div className="space-y-2 min-w-0">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Buscar
                  </label>
                  <div className="relative">
                    <Search className="h-4 w-4 absolute left-3 top-3 text-slate-400 flex-shrink-0" />
                    <Input
                      placeholder="Buscar productos..."
                      value={filters.searchTerm}
                      onChange={(e) => handleFilterChange('searchTerm', e.target.value)}
                      className="w-full min-w-[140px] pl-10 bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600"
                    />
                  </div>
                </div>
              </div>

              {/* Controles adicionales */}
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between mt-6 pt-4 border-t border-slate-200 dark:border-slate-600 gap-4">
                <div className="flex items-center gap-4 flex-wrap">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setAutoRefresh(!autoRefresh)}
                    className={autoRefresh ? 'bg-green-50 border-green-200 text-green-700' : ''}
                  >
                    <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
                    Auto-actualizar
                  </Button>

                  <div className="text-sm text-slate-600 dark:text-slate-400">
                    {autoRefresh && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></div>
                        Actualizando cada 30s
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setFilters({
                        dateRange: '7days',
                        category: 'all',
                        warehouse: 'all',
                        status: 'all',
                        searchTerm: '',
                        customStartDate: '',
                        customEndDate: ''
                      });
                      // Recargar datos para aplicar los filtros reseteados
                      loadDashboardData();
                    }}
                  >
                    Limpiar filtros
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const csvData = data?.transactions.map(t => ({
                        producto: t.product_name,
                        cantidad: t.quantity,
                        tipo: t.transaction_type,
                        fecha: new Date(t.created_at).toLocaleDateString()
                      }));
                      console.log('Exportar datos:', csvData);
                    }}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Exportar
                  </Button>
                </div>
              </div>
            </CardContent>
          )}
        </Card>

        {/* Error Alert mejorado */}
        {error && (
          <Alert variant="destructive" className="mb-12 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 rounded-xl">
            <AlertTriangle className="h-5 w-5" />
            <AlertDescription className="font-medium text-red-800 dark:text-red-200">{error}</AlertDescription>
          </Alert>
        )}

        {data && (
          <>
            {/* Intelligence Briefing - Conversación Matutina */}
            <div className="mb-8">
              <IntelligentBriefing 
                dashboardData={data} 
                filters={filters}
              />
            </div>

            {/* Métricas Principales con diseño mejorado */}
            <div 
              className="grid gap-8 mb-16" 
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '2rem',
                marginBottom: '3rem'
              }}
            >
              {/* Productos Totales */}
              <Card className="group relative overflow-hidden bg-gradient-to-br from-slate-50 via-indigo-50/40 to-violet-50/30 dark:from-slate-800 dark:via-indigo-900/40 dark:to-violet-900/30 border-slate-200/60 dark:border-slate-700/60 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-violet-500/3 to-purple-500/5 dark:from-indigo-400/10 dark:via-violet-400/6 dark:to-purple-400/10"></div>
                <CardContent className="relative p-8">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-6">
                        <div className="p-3 bg-gradient-to-r from-indigo-500 to-violet-500 dark:from-indigo-400 dark:to-violet-400 rounded-xl group-hover:shadow-lg group-hover:shadow-indigo-500/25 dark:group-hover:shadow-indigo-400/25 transition-all">
                          <Package className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <span className="text-base font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Productos</span>
                          <div className="w-16 h-0.5 bg-gradient-to-r from-indigo-300 to-violet-300 dark:from-indigo-400 dark:to-violet-400 mt-2"></div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-4xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">{data.stats.total_products.toLocaleString()}</p>
                        <p className="text-base text-slate-600 dark:text-slate-400">productos únicos</p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 pt-6 border-t border-slate-200/50 dark:border-slate-700/50">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500 dark:text-slate-400">Total en inventario</span>
                      <span className="text-indigo-600 dark:text-indigo-400 font-medium bg-indigo-50 dark:bg-indigo-900/50 px-3 py-2 rounded-full">100% activos</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Valor Inventario */}
              <Card className="group relative overflow-hidden bg-gradient-to-br from-slate-50 via-teal-50/40 to-cyan-50/30 dark:from-slate-800 dark:via-teal-900/40 dark:to-cyan-900/30 border-slate-200/60 dark:border-slate-700/60 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="absolute inset-0 bg-gradient-to-br from-teal-500/5 via-cyan-500/3 to-emerald-500/5 dark:from-teal-400/10 dark:via-cyan-400/6 dark:to-emerald-400/10"></div>
                <CardContent className="relative p-8">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-6">
                        <div className="p-3 bg-gradient-to-r from-teal-500 to-cyan-500 dark:from-teal-400 dark:to-cyan-400 rounded-xl group-hover:shadow-lg group-hover:shadow-teal-500/25 dark:group-hover:shadow-teal-400/25 transition-all">
                          <DollarSign className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <span className="text-base font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Valor Total</span>
                          <div className="w-16 h-0.5 bg-gradient-to-r from-teal-300 to-cyan-300 dark:from-teal-400 dark:to-cyan-400 mt-2"></div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-4xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">{formatCurrency(data.stats.total_value)}</p>
                        <p className="text-base text-slate-600 dark:text-slate-400">inventario valorizado</p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 pt-6 border-t border-slate-200/50 dark:border-slate-700/50">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500 dark:text-slate-400">Valor de mercado</span>
                      <span className="text-teal-600 dark:text-teal-400 font-medium bg-teal-50 dark:bg-teal-900/50 px-3 py-2 rounded-full flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        +2.5%
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Alertas Activas */}
              <Card className="group relative overflow-hidden bg-gradient-to-br from-slate-50 via-orange-50/40 to-red-50/30 dark:from-slate-800 dark:via-orange-900/40 dark:to-red-900/30 border-slate-200/60 dark:border-slate-700/60 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 via-red-500/3 to-pink-500/5 dark:from-orange-400/10 dark:via-red-400/6 dark:to-pink-400/10"></div>
                <CardContent className="relative p-8">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-6">
                        <div className="p-3 bg-gradient-to-r from-orange-500 to-red-500 dark:from-orange-400 dark:to-red-400 rounded-xl group-hover:shadow-lg group-hover:shadow-orange-500/25 dark:group-hover:shadow-orange-400/25 transition-all">
                          <AlertTriangle className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <span className="text-base font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Alertas</span>
                          <div className="w-16 h-0.5 bg-gradient-to-r from-orange-300 to-red-300 dark:from-orange-400 dark:to-red-400 mt-2"></div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-4xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">{data.alerts.length}</p>
                        <p className="text-base text-slate-600 dark:text-slate-400">requieren atención</p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 pt-6 border-t border-slate-200/50 dark:border-slate-700/50">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500 dark:text-slate-400">Stock bajo</span>
                      <span className={`font-medium px-3 py-2 rounded-full ${
                        data.alerts.length > 0 
                          ? 'text-orange-700 bg-orange-50' 
                          : 'text-emerald-700 bg-emerald-50'
                      }`}>
                        {data.alerts.length > 0 ? 'Crítico' : 'Normal'}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Ventas */}
              <Card className="group relative overflow-hidden bg-gradient-to-br from-green-50 via-emerald-50/40 to-teal-50/30 dark:from-green-900 dark:via-emerald-900/40 dark:to-teal-900/30 border-green-200/60 dark:border-green-700/60 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-emerald-500/3 to-teal-500/5 dark:from-green-400/10 dark:via-emerald-400/6 dark:to-teal-400/10"></div>
                <CardContent className="relative p-8">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-6">
                        <div className="p-3 bg-gradient-to-r from-green-500 to-emerald-500 dark:from-green-400 dark:to-emerald-400 rounded-xl group-hover:shadow-lg group-hover:shadow-green-500/25 dark:group-hover:shadow-green-400/25 transition-all">
                          <TrendingUp className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <span className="text-base font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Ventas</span>
                          <div className="w-16 h-0.5 bg-gradient-to-r from-green-300 to-emerald-300 dark:from-green-400 dark:to-emerald-400 mt-2"></div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-4xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">{formatCurrency(data.stats.sales_value)}</p>
                        <p className="text-base text-slate-600 dark:text-slate-400">{data.stats.sales_count} transacciones</p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 pt-6 border-t border-slate-200/50 dark:border-slate-700/50">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500 dark:text-slate-400">
                        {filters.dateRange === 'all' ? 'Todos los períodos' : 
                         filters.dateRange === '7days' ? 'Últimos 7 días' :
                         filters.dateRange === '30days' ? 'Últimos 30 días' :
                         filters.dateRange === '90days' ? 'Últimos 90 días' :
                         filters.dateRange === 'custom' ? 'Período personalizado' : 'Período filtrado'}
                      </span>
                      <span className="text-green-600 dark:text-green-400 font-medium bg-green-50 dark:bg-green-900/50 px-3 py-2 rounded-full flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        Ingresos
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Compras */}
              <Card className="group relative overflow-hidden bg-gradient-to-br from-blue-50 via-indigo-50/40 to-purple-50/30 dark:from-blue-900 dark:via-indigo-900/40 dark:to-purple-900/30 border-blue-200/60 dark:border-blue-700/60 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-indigo-500/3 to-purple-500/5 dark:from-blue-400/10 dark:via-indigo-400/6 dark:to-purple-400/10"></div>
                <CardContent className="relative p-8">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-6">
                        <div className="p-3 bg-gradient-to-r from-blue-500 to-indigo-500 dark:from-blue-400 dark:to-indigo-400 rounded-xl group-hover:shadow-lg group-hover:shadow-blue-500/25 dark:group-hover:shadow-blue-400/25 transition-all">
                          <Package className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <span className="text-base font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Compras</span>
                          <div className="w-16 h-0.5 bg-gradient-to-r from-blue-300 to-indigo-300 dark:from-blue-400 dark:to-indigo-400 mt-2"></div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-4xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">{formatCurrency(data.stats.purchases_value)}</p>
                        <p className="text-base text-slate-600 dark:text-slate-400">{data.stats.purchases_count} transacciones</p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 pt-6 border-t border-slate-200/50 dark:border-slate-700/50">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500 dark:text-slate-400">
                        {filters.dateRange === 'all' ? 'Todos los períodos' : 
                         filters.dateRange === '7days' ? 'Últimos 7 días' :
                         filters.dateRange === '30days' ? 'Últimos 30 días' :
                         filters.dateRange === '90days' ? 'Últimos 90 días' :
                         filters.dateRange === 'custom' ? 'Período personalizado' : 'Período filtrado'}
                      </span>
                      <span className="text-blue-600 dark:text-blue-400 font-medium bg-blue-50 dark:bg-blue-900/50 px-3 py-2 rounded-full flex items-center gap-2">
                        <Package className="h-4 w-4" />
                        Gastos
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Ganancia Neta */}
              <Card className={`group relative overflow-hidden ${data.stats.net_profit >= 0 
                ? 'bg-gradient-to-br from-emerald-50 via-green-50/40 to-teal-50/30 dark:from-emerald-900 dark:via-green-900/40 dark:to-teal-900/30 border-emerald-200/60 dark:border-emerald-700/60'
                : 'bg-gradient-to-br from-red-50 via-rose-50/40 to-pink-50/30 dark:from-red-900 dark:via-rose-900/40 dark:to-pink-900/30 border-red-200/60 dark:border-red-700/60'
              } hover:shadow-xl transition-all duration-300 hover:-translate-y-1`}>
                <div className={`absolute inset-0 ${data.stats.net_profit >= 0
                  ? 'bg-gradient-to-br from-emerald-500/5 via-green-500/3 to-teal-500/5 dark:from-emerald-400/10 dark:via-green-400/6 dark:to-teal-400/10'
                  : 'bg-gradient-to-br from-red-500/5 via-rose-500/3 to-pink-500/5 dark:from-red-400/10 dark:via-rose-400/6 dark:to-pink-400/10'
                }`}></div>
                <CardContent className="relative p-8">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-6">
                        <div className={`p-3 rounded-xl group-hover:shadow-lg transition-all ${data.stats.net_profit >= 0
                          ? 'bg-gradient-to-r from-emerald-500 to-green-500 dark:from-emerald-400 dark:to-green-400 group-hover:shadow-emerald-500/25 dark:group-hover:shadow-emerald-400/25'
                          : 'bg-gradient-to-r from-red-500 to-rose-500 dark:from-red-400 dark:to-rose-400 group-hover:shadow-red-500/25 dark:group-hover:shadow-red-400/25'
                        }`}>
                          <Target className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <span className="text-base font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Ganancia Neta</span>
                          <div className={`w-16 h-0.5 mt-2 ${data.stats.net_profit >= 0
                            ? 'bg-gradient-to-r from-emerald-300 to-green-300 dark:from-emerald-400 dark:to-green-400'
                            : 'bg-gradient-to-r from-red-300 to-rose-300 dark:from-red-400 dark:to-rose-400'
                          }`}></div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-4xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
                          {formatCurrency(data.stats.net_profit)}
                        </p>
                        <p className="text-base text-slate-600 dark:text-slate-400">
                          {data.stats.net_profit >= 0 ? 'Rentabilidad positiva' : 'Pérdida en período'}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 pt-6 border-t border-slate-200/50 dark:border-slate-700/50">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500 dark:text-slate-400">Período seleccionado</span>
                      <span className={`font-medium px-3 py-2 rounded-full flex items-center gap-2 ${data.stats.net_profit >= 0
                        ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/50'
                        : 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/50'
                      }`}>
                        <Target className="h-4 w-4" />
                        {data.stats.net_profit >= 0 ? 'Ganancia' : 'Pérdida'}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Panel Secundario mejorado */}
            <Card className="mb-8 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-slate-200 dark:border-slate-700 shadow-lg">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-indigo-500 dark:from-blue-400 dark:to-indigo-400 rounded-full"></div>
                    <CardTitle className="text-lg font-semibold text-slate-800 dark:text-slate-200">Métricas Complementarias</CardTitle>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setShowSecondaryMetrics(!showSecondaryMetrics)}
                    className="text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                  >
                    {showSecondaryMetrics ? (
                      <>
                        <span className="mr-2">Ocultar</span>
                        <div className="w-4 h-4 border-2 border-slate-400 dark:border-slate-500 rounded transform rotate-45"></div>
                      </>
                    ) : (
                      <>
                        <span className="mr-2">Mostrar</span>
                        <div className="w-4 h-4 border-2 border-slate-400 dark:border-slate-500 rounded"></div>
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
              {showSecondaryMetrics && (
                <CardContent className="pt-0 pb-4">
                  <div 
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                      gap: '1rem'
                    }}
                  >
                    {/* Clientes Activos */}
                    <div className="group p-6 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900/30 dark:to-blue-900/30 rounded-xl border border-indigo-100 dark:border-indigo-800/50 hover:border-indigo-200 dark:hover:border-indigo-700 hover:shadow-md transition-all duration-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="p-3 bg-indigo-100 dark:bg-indigo-800/50 rounded-xl group-hover:bg-indigo-200 dark:group-hover:bg-indigo-700/70 transition-colors">
                            <Users className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-indigo-900 dark:text-indigo-100">Clientes Activos</h3>
                            <p className="text-sm text-indigo-600 dark:text-indigo-300">Últimos 30 días</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold text-indigo-900 dark:text-indigo-100">{data.stats.active_customers}</p>
                          <p className="text-xs text-indigo-600 dark:text-indigo-400">clientes</p>
                        </div>
                      </div>
                    </div>

                    {/* Pipeline */}
                    <div className="group p-6 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/30 dark:to-pink-900/30 rounded-xl border border-purple-100 dark:border-purple-800/50 hover:border-purple-200 dark:hover:border-purple-700 hover:shadow-md transition-all duration-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="p-3 bg-purple-100 dark:bg-purple-800/50 rounded-xl group-hover:bg-purple-200 dark:group-hover:bg-purple-700/70 transition-colors">
                            <Target className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-purple-900 dark:text-purple-100">Pipeline de Ventas</h3>
                            <p className="text-sm text-purple-600 dark:text-purple-300">Valor estimado</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">{formatCurrency(data.stats.pipeline_value)}</p>
                          <p className="text-xs text-purple-600 dark:text-purple-400">en proceso</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>

            {/* Gráficos Principales mejorados */}
            <div className="charts-grid">
              {/* Tendencia de Ventas */}
              <Card className="chart-container shadow-lg hover:shadow-xl transition-all duration-300 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-3">
                      <div className="p-2 bg-gradient-to-r from-blue-500 to-indigo-500 dark:from-blue-400 dark:to-indigo-400 rounded-lg">
                        <TrendingUp className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <span className="text-lg font-semibold text-slate-800 dark:text-slate-200">Tendencia de Ventas</span>
                        <p className="text-sm text-slate-600 dark:text-slate-400 font-normal">vs Pronósticos IA</p>
                      </div>
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-blue-500 dark:bg-blue-400 rounded-full"></div>
                        <span className="text-xs text-slate-600 dark:text-slate-400">Ventas</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-indigo-400 dark:bg-indigo-300 rounded-full"></div>
                        <span className="text-xs text-slate-600 dark:text-slate-400">Pronóstico</span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="relative">
                    <ResponsiveContainer width="100%" height={320}>
                      <AreaChart 
                        data={data.chartData.salesTrend} 
                        margin={{ top: 20, right: 30, left: 20, bottom: 40 }}
                      >
                        <defs>
                          <linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
                          </linearGradient>
                          <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.6}/>
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0.1}/>
                          </linearGradient>
                        </defs>
                        
                        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.1} />
                        
                        <XAxis 
                          dataKey="date" 
                          stroke="currentColor"
                          fontSize={11}
                          tick={{ fill: 'currentColor' }}
                          axisLine={{ stroke: 'currentColor', opacity: 0.3 }}
                        />
                        
                        <YAxis 
                          stroke="currentColor"
                          fontSize={11}
                          tick={{ fill: 'currentColor' }}
                          axisLine={{ stroke: 'currentColor', opacity: 0.3 }}
                          tickFormatter={(value) => formatCurrency(value)}
                        />
                        
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: 'var(--background)',
                            border: '1px solid var(--border)',
                            borderRadius: '12px',
                            boxShadow: '0 8px 25px -5px rgba(0, 0, 0, 0.3)',
                            fontSize: '12px',
                            color: 'var(--foreground)'
                          }}
                          formatter={(value, name) => [
                            formatCurrency(value as number),
                            name
                          ]}
                          labelFormatter={(label) => `Fecha: ${label}`}
                        />
                        
                        <Legend 
                          wrapperStyle={{
                            paddingTop: '20px',
                            fontSize: '12px'
                          }}
                        />
                        
                        <Area 
                          type="monotone" 
                          dataKey="sales" 
                          stroke="#3b82f6" 
                          fillOpacity={1} 
                          fill="url(#salesGradient)"
                          strokeWidth={2.5}
                          dot={{ 
                            fill: '#3b82f6', 
                            strokeWidth: 1.5, 
                            r: 3,
                            stroke: '#ffffff',
                            filter: 'drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3))'
                          }}
                          activeDot={{ 
                            r: 6, 
                            fill: '#3b82f6', 
                            stroke: '#ffffff', 
                            strokeWidth: 2,
                            filter: 'drop-shadow(0 4px 8px rgba(59, 130, 246, 0.4))'
                          }}
                          name="Ventas Reales"
                        />
                        
                        <Line 
                          type="monotone" 
                          dataKey="forecast" 
                          stroke="#6366f1" 
                          strokeWidth={2}
                          strokeDasharray="8 4"
                          dot={{ 
                            fill: '#6366f1', 
                            strokeWidth: 1, 
                            r: 2.5,
                            stroke: '#ffffff',
                            opacity: 0.8
                          }}
                          activeDot={{ 
                            r: 5, 
                            fill: '#6366f1', 
                            stroke: '#ffffff', 
                            strokeWidth: 2,
                            filter: 'drop-shadow(0 3px 6px rgba(99, 102, 241, 0.4))'
                          }}
                          name="Pronóstico IA"
                        />
                                              </AreaChart>
                    </ResponsiveContainer>
                    <div className="absolute top-2 right-2 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm rounded-lg px-3 py-1 border border-slate-200 dark:border-slate-600">
                      <span className="text-xs font-medium text-slate-700 dark:text-slate-300">Filtrado por: {filters.dateRange}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Distribución por Categorías */}
              <Card className="chart-container shadow-lg hover:shadow-xl transition-all duration-300 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-3">
                      <div className="p-2 bg-gradient-to-r from-emerald-500 to-green-500 dark:from-emerald-400 dark:to-green-400 rounded-lg">
                        <Activity className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <span className="text-lg font-semibold text-slate-800 dark:text-slate-200">Categorías</span>
                        <p className="text-sm text-slate-600 dark:text-slate-400 font-normal">Distribución de inventario</p>
                      </div>
                    </CardTitle>
                    <Button variant="ghost" size="sm" className="text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {data.chartData.categoryDistribution && data.chartData.categoryDistribution.length > 0 && data.chartData.categoryDistribution.some((item: any) => item.value > 0) ? (
                    <ResponsiveContainer width="100%" height={320}>
                      <PieChart>
                        <defs>
                          {data.chartData.categoryDistribution.map((entry, index) => {
                            const colors = [
                              { start: '#3b82f6', end: '#1e40af' },
                              { start: '#10b981', end: '#047857' },
                              { start: '#f59e0b', end: '#d97706' },
                              { start: '#ef4444', end: '#dc2626' },
                              { start: '#8b5cf6', end: '#7c3aed' },
                              { start: '#06b6d4', end: '#0891b2' },
                              { start: '#84cc16', end: '#65a30d' },
                              { start: '#f97316', end: '#ea580c' },
                              { start: '#ec4899', end: '#db2777' },
                              { start: '#6366f1', end: '#4f46e5' },
                            ];
                            const colorSet = colors[index % colors.length];
                            return (
                              <radialGradient key={`gradient-${index}`} id={`categoryGradient-${index}`} cx="50%" cy="50%" r="50%">
                                <stop offset="0%" stopColor={colorSet.start} stopOpacity={0.9} />
                                <stop offset="100%" stopColor={colorSet.end} stopOpacity={0.8} />
                              </radialGradient>
                            );
                          })}
                        </defs>
                        
                        <Pie
                          data={data.chartData.categoryDistribution.sort((a: any, b: any) => b.value - a.value)}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                          nameKey="category"
                          stroke="rgba(255, 255, 255, 0.3)"
                          strokeWidth={2}
                        >
                          {data.chartData.categoryDistribution.map((entry, index) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={`url(#categoryGradient-${index})`}
                              className="hover:brightness-110 transition-all duration-300 cursor-pointer"
                            />
                          ))}
                        </Pie>
                        
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: 'var(--background)',
                            border: '1px solid var(--border)',
                            borderRadius: '12px',
                            boxShadow: '0 8px 25px -5px rgba(0, 0, 0, 0.3)',
                            fontSize: '12px',
                            color: 'var(--foreground)'
                          }}
                          formatter={(value, name) => [
                            `${formatNumber(value as number)} productos`,
                            'Cantidad'
                          ]}
                          labelFormatter={(label) => `Categoría: ${label}`}
                        />
                        
                        <Legend 
                          verticalAlign="bottom" 
                          height={36}
                          iconType="circle"
                          wrapperStyle={{
                            fontSize: '12px',
                            color: 'var(--foreground)'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-[300px] text-slate-500 dark:text-slate-400">
                      <div className="text-center">
                        <Activity className="mx-auto h-12 w-12 mb-4 opacity-50" />
                        <p>No hay datos de categorías disponibles</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Niveles de Stock */}
              <Card className="chart-container shadow-lg hover:shadow-xl transition-all duration-300 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-3">
                      <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 dark:from-purple-400 dark:to-pink-400 rounded-lg">
                        <Package className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <span className="text-lg font-semibold text-slate-800 dark:text-slate-200">Stock por Almacén</span>
                        <p className="text-sm text-slate-600 dark:text-slate-400 font-normal">Niveles actuales vs objetivos</p>
                      </div>
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-purple-500 dark:bg-purple-400 rounded-full"></div>
                        <span className="text-xs text-slate-600 dark:text-slate-400">Actual</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-red-400 dark:bg-red-300 rounded-full"></div>
                        <span className="text-xs text-slate-600 dark:text-slate-400">Mínimo</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-green-400 dark:bg-green-300 rounded-full"></div>
                        <span className="text-xs text-slate-600 dark:text-slate-400">Máximo</span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {data.chartData.stockLevels.length > 0 ? (
                    <ResponsiveContainer width="100%" height={320}>
                      <BarChart 
                        data={data.chartData.stockLevels} 
                        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                        barCategoryGap="20%"
                      >
                        <defs>
                          <linearGradient id="stockActual" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.6}/>
                          </linearGradient>
                          <linearGradient id="stockMin" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#ef4444" stopOpacity={0.6}/>
                          </linearGradient>
                          <linearGradient id="stockMax" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0.6}/>
                          </linearGradient>
                        </defs>
                        
                        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.1} />
                        
                        <XAxis 
                          dataKey="warehouse" 
                          stroke="currentColor"
                          fontSize={11}
                          tick={{ fill: 'currentColor' }}
                          axisLine={{ stroke: 'currentColor', opacity: 0.3 }}
                          angle={-45}
                          textAnchor="end"
                          height={80}
                        />
                        
                        <YAxis 
                          stroke="currentColor"
                          fontSize={11}
                          tick={{ fill: 'currentColor' }}
                          axisLine={{ stroke: 'currentColor', opacity: 0.3 }}
                          tickFormatter={(value) => formatShortNumber(value)}
                        />
                        
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: 'var(--background)',
                            border: '1px solid var(--border)',
                            borderRadius: '12px',
                            boxShadow: '0 8px 25px -5px rgba(0, 0, 0, 0.3)',
                            fontSize: '12px',
                            color: 'var(--foreground)'
                          }}
                          formatter={(value, name) => [
                            `${formatNumber(value as number)} unidades`,
                            name
                          ]}
                          labelFormatter={(label) => `Almacén: ${label}`}
                        />
                        
                        <Legend 
                          wrapperStyle={{
                            paddingTop: '20px',
                            fontSize: '12px'
                          }}
                        />
                        
                        <Bar 
                          dataKey="current_stock" 
                          fill="url(#stockActual)"
                          name="Stock Actual"
                          radius={[4, 4, 0, 0]}
                          stroke="#8b5cf6"
                          strokeWidth={1}
                        />
                        <Bar 
                          dataKey="min_stock" 
                          fill="url(#stockMin)"
                          name="Stock Mínimo"
                          radius={[4, 4, 0, 0]}
                          stroke="#ef4444"
                          strokeWidth={1}
                        />
                        <Bar 
                          dataKey="max_stock" 
                          fill="url(#stockMax)"
                          name="Stock Máximo"
                          radius={[4, 4, 0, 0]}
                          stroke="#10b981"
                          strokeWidth={1}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700 dark:to-slate-600 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-500">
                      <div className="text-center">
                        <Package className="h-12 w-12 text-slate-400 dark:text-slate-500 mx-auto mb-4" />
                        <p className="text-slate-600 dark:text-slate-300 font-medium">No hay datos de stock</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">Configure almacenes para ver estadísticas</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Tendencia de Alertas */}
              <Card className="chart-container shadow-lg hover:shadow-xl transition-all duration-300 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-3">
                      <div className="p-2 bg-gradient-to-r from-amber-500 to-orange-500 dark:from-amber-400 dark:to-orange-400 rounded-lg">
                        <Bell className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <span className="text-lg font-semibold text-slate-800 dark:text-slate-200">Alertas</span>
                        <p className="text-sm text-slate-600 dark:text-slate-400 font-normal">Tendencia últimos 7 días</p>
                      </div>
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        data.stats.low_stock_alerts > 0 
                          ? 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300' 
                          : 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300'
                      }`}>
                        {data.stats.low_stock_alerts > 0 ? 'Alertas activas' : 'Todo normal'}
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={data.chartData.alertTrends} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.1} />
                      <XAxis 
                        dataKey="date" 
                        stroke="currentColor"
                        fontSize={11}
                        tick={{ fill: 'currentColor' }}
                        axisLine={{ stroke: 'currentColor', opacity: 0.3 }}
                      />
                      <YAxis 
                        stroke="currentColor"
                        fontSize={11}
                        tick={{ fill: 'currentColor' }}
                        axisLine={{ stroke: 'currentColor', opacity: 0.3 }}
                      />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: 'var(--background)',
                          border: '1px solid var(--border)',
                          borderRadius: '12px',
                          boxShadow: '0 8px 25px -5px rgba(0, 0, 0, 0.3)',
                          fontSize: '12px',
                          color: 'var(--foreground)'
                        }}
                      />
                      <Legend />
                      <Bar dataKey="alerts" fill="#ef4444" name="Alertas por Día" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Secciones de Información mejoradas */}
            <div 
              className="grid gap-4 mb-6" 
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '1rem',
                marginBottom: '1.5rem'
              }}
            >
              {/* Alertas Recientes */}
              <Card className="relative overflow-hidden bg-gradient-to-br from-white via-red-50/30 to-pink-50/30 dark:from-slate-800 dark:via-red-900/10 dark:to-pink-900/10 border-red-100 dark:border-red-800/30 shadow-lg hover:shadow-xl transition-all duration-300">
                {/* Header con gradiente */}
                <div className="bg-gradient-to-r from-red-500 to-pink-500 dark:from-red-600 dark:to-pink-600 p-4">
                  <div className="flex items-center justify-between text-white">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-white/20 dark:bg-white/30 rounded-lg backdrop-blur-sm">
                        <Bell className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">Alertas</h3>
                        <p className="text-sm text-red-100 dark:text-red-200">Requieren atención</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" className="text-white hover:bg-white/20 dark:hover:bg-white/30 transition-colors">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <CardContent className="p-6">
                  {data.alerts.length > 0 ? (
                    <div className="space-y-4">
                      {data.alerts.slice(0, 4).map((alert) => (
                        <div key={alert.id} className="group relative">
                          {/* Línea conectora */}
                          <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-gradient-to-b from-red-200 dark:from-red-700 to-transparent"></div>
                          
                          <div className="flex items-start gap-4 p-4 bg-white dark:bg-slate-700 rounded-xl border border-red-100 dark:border-red-800/30 hover:border-red-200 dark:hover:border-red-700 hover:shadow-md transition-all duration-200">
                            {/* Indicador de estado */}
                            <div className={`w-3 h-3 rounded-full mt-2 flex-shrink-0 ${
                              alert.severity === 'critical' ? 'bg-red-500 shadow-lg shadow-red-500/50' :
                              alert.severity === 'high' ? 'bg-orange-500 shadow-lg shadow-orange-500/50' :
                              alert.severity === 'medium' ? 'bg-yellow-500 shadow-lg shadow-yellow-500/50' :
                              'bg-blue-500 shadow-lg shadow-blue-500/50'
                            }`}></div>
                            
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <Badge 
                                  variant={getSeverityColor(alert.severity) as any} 
                                  className="text-xs font-medium px-2 py-1"
                                >
                                  {alert.severity.toUpperCase()}
                                </Badge>
                                <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-600 px-2 py-1 rounded-full">
                                  {new Date(alert.created_at).toLocaleDateString('es-PE', {
                                    day: 'numeric',
                                    month: 'short',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                              </div>
                              <h4 className="font-semibold text-gray-800 dark:text-gray-200 text-sm mb-1 group-hover:text-red-700 dark:group-hover:text-red-300 transition-colors">
                                {alert.title}
                              </h4>
                              <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">{alert.message}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="relative mx-auto mb-6">
                        <div className="w-20 h-20 bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-900/50 dark:to-emerald-900/50 rounded-full flex items-center justify-center mx-auto">
                          <Bell className="h-10 w-10 text-green-600 dark:text-green-400" />
                        </div>
                        <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-500 dark:bg-green-400 rounded-full flex items-center justify-center">
                          <span className="text-white text-xs font-bold">✓</span>
                        </div>
                      </div>
                      <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">¡Todo bajo control!</h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">No hay alertas que requieran atención</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Pronósticos AI */}
              <Card className="relative overflow-hidden bg-gradient-to-br from-white via-blue-50/30 to-cyan-50/30 dark:from-slate-800 dark:via-blue-900/10 dark:to-cyan-900/10 border-blue-100 dark:border-blue-800/30 shadow-lg hover:shadow-xl transition-all duration-300">
                {/* Header con gradiente */}
                <div className="bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-600 dark:to-cyan-600 p-4">
                  <div className="flex items-center justify-between text-white">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-white/20 dark:bg-white/30 rounded-lg backdrop-blur-sm">
                        <Zap className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">IA Pronósticos</h3>
                        <p className="text-sm text-blue-100 dark:text-blue-200">Predicciones inteligentes</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" className="text-white hover:bg-white/20 dark:hover:bg-white/30 transition-colors">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <CardContent className="p-6">
                  {data.forecasts.length > 0 ? (
                    <div className="space-y-4">
                      {data.forecasts.map((forecast, index) => (
                        <div key={index} className="group relative">
                          {/* Línea conectora */}
                          <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-gradient-to-b from-blue-200 dark:from-blue-700 to-transparent"></div>
                          
                          <div className="flex items-center gap-4 p-4 bg-white dark:bg-slate-700 rounded-xl border border-blue-100 dark:border-blue-800/30 hover:border-blue-200 dark:hover:border-blue-700 hover:shadow-md transition-all duration-200">
                            {/* Icono de IA */}
                            <div className="w-3 h-3 bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-400 dark:to-cyan-400 rounded-full flex-shrink-0 animate-pulse shadow-lg shadow-blue-500/50"></div>
                            
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="font-semibold text-gray-800 dark:text-gray-200 text-sm group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors truncate">
                                  {forecast.product_name}
                                </h4>
                                <div className="text-right ml-4 flex-shrink-0">
                                  <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{forecast.predicted_demand}</p>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">unidades</p>
                                </div>
                              </div>
                              
                              <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">{forecast.period}</p>
                              
                              {/* Barra de confianza mejorada */}
                              <div className="flex items-center gap-3">
                                <div className="flex-1">
                                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                                    <span>Confianza</span>
                                    <span className="font-medium">{forecast.confidence}%</span>
                                  </div>
                                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2 overflow-hidden">
                                    <div 
                                      className="bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-400 dark:to-cyan-400 h-2 rounded-full transition-all duration-500 shadow-sm"
                                      style={{ width: `${forecast.confidence}%` }}
                                    ></div>
                                  </div>
                                </div>
                                <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  forecast.confidence >= 80 
                                    ? 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300' :
                                  forecast.confidence >= 60 
                                    ? 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300' :
                                    'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300'
                                }`}>
                                  {forecast.confidence >= 80 ? 'Alta' :
                                   forecast.confidence >= 60 ? 'Media' : 'Baja'}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="relative mx-auto mb-6">
                        <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-cyan-100 dark:from-blue-900/50 dark:to-cyan-900/50 rounded-full flex items-center justify-center mx-auto">
                          <Zap className="h-10 w-10 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div className="absolute inset-0 w-20 h-20 border-4 border-blue-200 dark:border-blue-700 rounded-full animate-spin border-t-transparent mx-auto"></div>
                      </div>
                      <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Entrenando IA</h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Los pronósticos aparecerán cuando haya suficientes datos</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Transacciones Recientes */}
              <Card className="relative overflow-hidden bg-gradient-to-br from-white via-green-50/30 to-emerald-50/30 dark:from-slate-800 dark:via-green-900/10 dark:to-emerald-900/10 border-green-100 dark:border-green-800/30 shadow-lg hover:shadow-xl transition-all duration-300">
                {/* Header con gradiente */}
                <div className="bg-gradient-to-r from-green-500 to-emerald-500 dark:from-green-600 dark:to-emerald-600 p-4">
                  <div className="flex items-center justify-between text-white">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-white/20 dark:bg-white/30 rounded-lg backdrop-blur-sm">
                        <Activity className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">Movimientos</h3>
                        <p className="text-sm text-green-100 dark:text-green-200">Actividad reciente</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" className="text-white hover:bg-white/20 dark:hover:bg-white/30 transition-colors">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <CardContent className="p-6">
                  {data.transactions.length > 0 ? (
                    <div className="space-y-4">
                      {data.transactions.slice(0, 6).map((transaction) => (
                        <div key={transaction.id} className="group relative">
                          {/* Línea conectora */}
                          <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-gradient-to-b from-green-200 dark:from-green-700 to-transparent"></div>
                          
                          <div className="flex items-center gap-4 p-4 bg-white dark:bg-slate-700 rounded-xl border border-green-100 dark:border-green-800/30 hover:border-green-200 dark:hover:border-green-700 hover:shadow-md transition-all duration-200">
                            {/* Indicador de tipo de transacción */}
                            <div className={`w-3 h-3 rounded-full flex-shrink-0 shadow-lg ${
                              transaction.transaction_type === 'IN' || transaction.transaction_type === 'PURCHASE' 
                                ? 'bg-green-500 shadow-green-500/50' 
                                : 'bg-red-500 shadow-red-500/50'
                            }`}></div>
                            
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="font-semibold text-gray-800 dark:text-gray-200 text-sm group-hover:text-green-700 dark:group-hover:text-green-300 transition-colors truncate">
                                  {transaction.product_name}
                                </h4>
                                <Badge 
                                  variant={getTransactionTypeColor(transaction.transaction_type) as any}
                                  className={`font-bold text-sm flex-shrink-0 ${
                                    transaction.transaction_type === 'IN' || transaction.transaction_type === 'PURCHASE' 
                                      ? 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 border-green-200 dark:border-green-700' 
                                      : 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 border-red-200 dark:border-red-700'
                                  }`}
                                >
                                  {transaction.transaction_type === 'IN' || transaction.transaction_type === 'PURCHASE' ? '+' : '-'}
                                  {transaction.quantity}
                                </Badge>
                              </div>
                              
                              <div className="flex items-center justify-between">
                                <p className="text-xs text-gray-600 dark:text-gray-400">
                                  {new Date(transaction.created_at).toLocaleDateString('es-PE', {
                                    day: 'numeric',
                                    month: 'short',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </p>
                                <div className="flex items-center gap-2">
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                    transaction.transaction_type === 'IN' || transaction.transaction_type === 'PURCHASE' 
                                      ? 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300' 
                                      : 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300'
                                  }`}>
                                    {transaction.transaction_type === 'IN' || transaction.transaction_type === 'PURCHASE' 
                                      ? 'Entrada' 
                                      : 'Salida'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="w-20 h-20 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Activity className="h-10 w-10 text-gray-500 dark:text-gray-400" />
                      </div>
                      <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Sin movimientos</h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">No hay transacciones recientes</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;