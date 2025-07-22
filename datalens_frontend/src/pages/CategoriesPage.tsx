import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Badge,
  Alert,
  AlertDescription,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '../components/ui';
import {
  FolderOpen,
  Plus,
  Search,
  Edit,
  Trash2,
  Package,
  TrendingUp,
  BarChart3,
  AlertTriangle,
  Target,
  DollarSign
} from '../components/ui/icons';
import { Category } from '../types';
import { inventoryService } from '../services/api';

interface CategoryAnalytics {
  strategic_metrics: {
    top_sales_category: {
      name: string;
      change: string;
      icon: string;
    };
    most_alerts_category: {
      name: string;
      critical_count: number;
      total_alerts: number;
      icon: string;
    };
    average_margin: {
      value: string;
      description: string;
      icon: string;
    };
    opportunity_category: {
      name: string;
      growth: string;
      icon: string;
    };
  };
  executive_summary: string;
  quick_actions: Array<{
    category_id: number;
    action: string;
    title: string;
    description: string;
    priority: string;
  }>;
}

interface CategoryPerformance {
  category_id: number;
  category_name: string;
  sales_current_period: number;
  sales_previous_period: number;
  sales_change_percentage: number;
  avg_margin_percentage: number;
  products_with_alerts: number;
  critical_products: number;
  trend: string;
  trend_icon: string;
  operational_status: string;
  status_color: string;
}

interface CategoriesPageState {
  categories: Category[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  isDialogOpen: boolean;
  selectedCategory: Category | null;
  formData: Partial<Category>;
  // 🎯 NUEVOS ESTADOS PARA FUNCIONALIDAD ESTRATÉGICA
  analytics: CategoryAnalytics | null;
  analyticsLoading: boolean;
  analyticsError: string | null;
  // 🎯 PERFORMANCE DATA POR CATEGORÍA
  categoriesPerformance: CategoryPerformance[];
  performanceLoading: boolean;
}

const CategoriesPage: React.FC = () => {
  const [state, setState] = useState<CategoriesPageState>({
    categories: [],
    loading: true,
    error: null,
    searchTerm: '',
    isDialogOpen: false,
    selectedCategory: null,
    formData: {},
    // 🎯 INICIALIZAR NUEVOS ESTADOS ESTRATÉGICOS
    analytics: null,
    analyticsLoading: true,
    analyticsError: null,
    // 🎯 PERFORMANCE DATA
    categoriesPerformance: [],
    performanceLoading: true
  });

  const fetchCategories = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const response = await inventoryService.getCategories();
      setState(prev => ({ 
        ...prev, 
        categories: response.results || response,
        loading: false 
      }));
    } catch (err) {
      console.error('Error fetching categories:', err);
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al cargar categorías',
        loading: false 
      }));
    }
  };

  // 🎯 NUEVA FUNCIÓN: Cargar analytics estratégicos REAL del backend
  const fetchCategoryAnalytics = async () => {
    try {
      setState(prev => ({ ...prev, analyticsLoading: true, analyticsError: null }));
      
      console.log('🎯 Cargando analytics estratégicos REALES desde el backend...');
      
      // CONECTAR AL ENDPOINT REAL DEL BACKEND
      const analyticsData = await inventoryService.getCategoryAnalytics();
      
      console.log('✅ Analytics recibidos del backend:', analyticsData);
      
      // Mapear datos del backend a la estructura del frontend
      const mappedAnalytics = {
        strategic_metrics: analyticsData.strategic_metrics,
        executive_summary: analyticsData.executive_summary,
        quick_actions: analyticsData.quick_actions || []
      };
      
      // Mapear categorías performance
      const categoriesPerformance = analyticsData.categories.map((cat: any) => ({
        category_id: cat.category_id,
        category_name: cat.category_name,
        sales_current_period: cat.sales_current_period,
        sales_previous_period: cat.sales_previous_period,
        sales_change_percentage: cat.sales_change_percentage,
        avg_margin_percentage: cat.avg_margin_percentage,
        products_count: cat.products_count,
        products_with_alerts: cat.products_with_alerts,
        critical_products: cat.critical_products,
        trend: cat.trend,
        trend_icon: cat.trend_icon,
        operational_status: cat.operational_status,
        status_color: cat.status_color
      }));
      
      setState(prev => ({ 
        ...prev, 
        analytics: mappedAnalytics,
        categoriesPerformance: categoriesPerformance,
        analyticsLoading: false,
        performanceLoading: false
      }));
      
    } catch (err) {
      console.error('❌ Error cargando analytics de categorías:', err);
      setState(prev => ({ 
        ...prev, 
        analyticsError: err instanceof Error ? err.message : 'Error al cargar analytics del backend',
        analyticsLoading: false,
        analytics: {
          strategic_metrics: {
            top_sales_category: {
              name: 'Error de conexión',
              change: '0.0% vs mes anterior',
              icon: '❌'
            },
            most_alerts_category: {
              name: 'Sin conexión al backend',
              critical_count: 0,
              total_alerts: 0,
              icon: '⚠️'
            },
            average_margin: {
              value: 'N/A',
              description: 'No disponible',
              icon: '💰'
            },
            opportunity_category: {
              name: 'Datos no disponibles',
              growth: 'Conecta al backend',
              icon: '�'
            }
          },
          executive_summary: `❌ **Error de Conexión al Backend**\n\nNo se pudieron cargar los analytics desde el servidor.\nVerifica que Django esté corriendo en puerto 8080.`,
          quick_actions: []
        },
        categoriesPerformance: [],
        performanceLoading: false
      }));
    }
  };

  const handleSaveCategory = async () => {
    try {
      if (!state.formData.name?.trim()) {
        setState(prev => ({ ...prev, error: 'El nombre es requerido' }));
        return;
      }

      setState(prev => ({ ...prev, loading: true, error: null }));
      
      if (state.selectedCategory) {
        // Actualizar categoría existente
        await inventoryService.updateCategory(state.selectedCategory.id, state.formData);
      } else {
        // Crear nueva categoría
        await inventoryService.createCategory({
          ...state.formData,
          is_active: state.formData.is_active !== undefined ? state.formData.is_active : true
        });
      }
      
      await fetchCategories();
      handleCloseDialog();
    } catch (err) {
      console.error('Error saving category:', err);
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al guardar categoría',
        loading: false 
      }));
    }
  };

  const handleDeleteCategory = async (id: number) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta categoría?')) {
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      await inventoryService.deleteCategory(id);
      await fetchCategories();
    } catch (err) {
      console.error('Error deleting category:', err);
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al eliminar categoría',
        loading: false 
      }));
    }
  };

  const handleCloseDialog = () => {
    setState(prev => ({
      ...prev,
      isDialogOpen: false,
      selectedCategory: null,
      formData: {},
      error: null
    }));
  };

  const openEditDialog = (category: Category) => {
    setState(prev => ({
      ...prev,
      selectedCategory: category,
      formData: { ...category },
      isDialogOpen: true
    }));
  };

  const openCreateDialog = () => {
    setState(prev => ({
      ...prev,
      selectedCategory: null,
      formData: {
        name: '',
        description: '',
        is_active: true
      },
      isDialogOpen: true
    }));
  };

  useEffect(() => {
    // 🎯 CARGAR DATOS EN PARALELO para mejor performance
    const loadAllData = async () => {
      await Promise.all([
        fetchCategories(),
        fetchCategoryAnalytics()
      ]);
    };
    
    loadAllData();
  }, []);

  const filteredCategories = state.categories.filter(category =>
    category.name.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
    (category.description && category.description.toLowerCase().includes(state.searchTerm.toLowerCase()))
  );

  if (state.loading && state.categories.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const activeCategories = state.categories.filter(cat => cat.is_active);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Categorías</h1>
          <p className="text-gray-600">Organiza y administra las categorías de productos</p>
        </div>
        <Button onClick={openCreateDialog} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Nueva Categoría
        </Button>
      </div>

      {/* 🎯 MÉTRICAS ESTRATÉGICAS - Reutilizando patrón del Dashboard */}
      <div 
        className="grid gap-6 mb-8"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.5rem'
        }}
      >
        {/* 🏆 Categoría #1 en Ventas */}
        <Card className="group relative overflow-hidden bg-gradient-to-br from-slate-50 via-green-50/40 to-emerald-50/30 dark:from-slate-800 dark:via-green-900/40 dark:to-emerald-900/30 border-slate-200/60 dark:border-slate-700/60 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-emerald-500/3 to-teal-500/5 dark:from-green-400/10 dark:via-emerald-400/6 dark:to-teal-400/10"></div>
          <CardContent className="relative p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-gradient-to-r from-green-500 to-emerald-500 dark:from-green-400 dark:to-emerald-400 rounded-xl group-hover:shadow-lg group-hover:shadow-green-500/25 dark:group-hover:shadow-green-400/25 transition-all">
                    <TrendingUp className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Categoría #1 en Ventas</span>
                  </div>
                </div>
                <div className="space-y-1">
                  {state.analyticsLoading ? (
                    <div className="animate-pulse">
                      <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  ) : (
                    <>
                      <p className="text-xl font-bold text-slate-800 dark:text-slate-100">
                        {state.analytics?.strategic_metrics.top_sales_category.name || 'Sin datos'}
                      </p>
                      <p className="text-sm text-green-600 dark:text-green-400 font-medium">
                        {state.analytics?.strategic_metrics.top_sales_category.change || 'Calculando...'}
                      </p>
                    </>
                  )}
                </div>
              </div>
              <span className="text-2xl">{state.analytics?.strategic_metrics.top_sales_category.icon || '🏆'}</span>
            </div>
          </CardContent>
        </Card>

        {/* 🚨 Categoría con Más Alertas */}
        <Card className="group relative overflow-hidden bg-gradient-to-br from-slate-50 via-orange-50/40 to-red-50/30 dark:from-slate-800 dark:via-orange-900/40 dark:to-red-900/30 border-slate-200/60 dark:border-slate-700/60 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 via-red-500/3 to-pink-500/5 dark:from-orange-400/10 dark:via-red-400/6 dark:to-pink-400/10"></div>
          <CardContent className="relative p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-gradient-to-r from-orange-500 to-red-500 dark:from-orange-400 dark:to-red-400 rounded-xl group-hover:shadow-lg group-hover:shadow-orange-500/25 dark:group-hover:shadow-orange-400/25 transition-all">
                    <AlertTriangle className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Categoría con Más Alertas</span>
                  </div>
                </div>
                <div className="space-y-1">
                  {state.analyticsLoading ? (
                    <div className="animate-pulse">
                      <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  ) : (
                    <>
                      <p className="text-xl font-bold text-slate-800 dark:text-slate-100">
                        {state.analytics?.strategic_metrics.most_alerts_category.name || 'Sin alertas'}
                      </p>
                      <p className="text-sm text-orange-600 dark:text-orange-400 font-medium">
                        {state.analytics?.strategic_metrics.most_alerts_category.critical_count || 0} productos críticos
                      </p>
                    </>
                  )}
                </div>
              </div>
              <span className="text-2xl">{state.analytics?.strategic_metrics.most_alerts_category.icon || '🚨'}</span>
            </div>
          </CardContent>
        </Card>

        {/* 💰 Margen Promedio */}
        <Card className="group relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50/40 to-indigo-50/30 dark:from-slate-800 dark:via-blue-900/40 dark:to-indigo-900/30 border-slate-200/60 dark:border-slate-700/60 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-indigo-500/3 to-purple-500/5 dark:from-blue-400/10 dark:via-indigo-400/6 dark:to-purple-400/10"></div>
          <CardContent className="relative p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-gradient-to-r from-blue-500 to-indigo-500 dark:from-blue-400 dark:to-indigo-400 rounded-xl group-hover:shadow-lg group-hover:shadow-blue-500/25 dark:group-hover:shadow-blue-400/25 transition-all">
                    <DollarSign className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Margen Promedio</span>
                  </div>
                </div>
                <div className="space-y-1">
                  {state.analyticsLoading ? (
                    <div className="animate-pulse">
                      <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  ) : (
                    <>
                      <p className="text-xl font-bold text-slate-800 dark:text-slate-100">
                        {state.analytics?.strategic_metrics.average_margin.value || '0%'}
                      </p>
                      <p className="text-sm text-blue-600 dark:text-blue-400 font-medium">
                        {state.analytics?.strategic_metrics.average_margin.description || 'general'}
                      </p>
                    </>
                  )}
                </div>
              </div>
              <span className="text-2xl">{state.analytics?.strategic_metrics.average_margin.icon || '💰'}</span>
            </div>
          </CardContent>
        </Card>

        {/* 🚀 Oportunidad del Mes */}
        <Card className="group relative overflow-hidden bg-gradient-to-br from-slate-50 via-purple-50/40 to-pink-50/30 dark:from-slate-800 dark:via-purple-900/40 dark:to-pink-900/30 border-slate-200/60 dark:border-slate-700/60 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-pink-500/3 to-rose-500/5 dark:from-purple-400/10 dark:via-pink-400/6 dark:to-rose-400/10"></div>
          <CardContent className="relative p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 dark:from-purple-400 dark:to-pink-400 rounded-xl group-hover:shadow-lg group-hover:shadow-purple-500/25 dark:group-hover:shadow-purple-400/25 transition-all">
                    <Target className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">Oportunidad del Mes</span>
                  </div>
                </div>
                <div className="space-y-1">
                  {state.analyticsLoading ? (
                    <div className="animate-pulse">
                      <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  ) : (
                    <>
                      <p className="text-xl font-bold text-slate-800 dark:text-slate-100">
                        {state.analytics?.strategic_metrics.opportunity_category.name || 'Analizando...'}
                      </p>
                      <p className="text-sm text-purple-600 dark:text-purple-400 font-medium">
                        {state.analytics?.strategic_metrics.opportunity_category.growth || 'demanda estable'}
                      </p>
                    </>
                  )}
                </div>
              </div>
              <span className="text-2xl">{state.analytics?.strategic_metrics.opportunity_category.icon || '🚀'}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 🎯 Widget de Resumen Ejecutivo */}
      {state.analytics && !state.analyticsLoading && (
        <Card className="mb-6 bg-gradient-to-r from-slate-50 to-indigo-50 dark:from-slate-800 dark:to-indigo-900 border-indigo-200 dark:border-indigo-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-indigo-800 dark:text-indigo-200">
              <BarChart3 className="h-5 w-5" />
              Resumen Ejecutivo
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <div className="whitespace-pre-line text-slate-700 dark:text-slate-300">
                {state.analytics.executive_summary}
              </div>
            </div>
            {state.analytics.quick_actions.length > 0 && (
              <div className="mt-4 pt-4 border-t border-indigo-200 dark:border-indigo-700">
                <h4 className="font-semibold text-indigo-800 dark:text-indigo-200 mb-2">Acciones Recomendadas:</h4>
                <div className="space-y-2">
                  {state.analytics.quick_actions.slice(0, 3).map((action, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <span className={`w-2 h-2 rounded-full ${
                        action.priority === 'high' ? 'bg-red-500' : 
                        action.priority === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                      }`}></span>
                      <span className="text-slate-600 dark:text-slate-400">{action.title}:</span>
                      <span className="text-slate-800 dark:text-slate-200">{action.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error de Analytics */}
      {state.analyticsError && (
        <Alert className="mb-6">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Error cargando analytics estratégicos: {state.analyticsError}
            <Button 
              variant="outline" 
              size="sm" 
              className="ml-2"
              onClick={fetchCategoryAnalytics}
            >
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Search */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Buscar categorías..."
                  value={state.searchTerm}
                  onChange={(e) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
                  className="pl-10"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {state.error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{state.error}</AlertDescription>
        </Alert>
      )}

      {/* 🎯 TABLA EXPANDIDA CON PERFORMANCE FINANCIERO */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Performance por Categorías
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Categoría</TableHead>
                <TableHead>Ventas del Mes</TableHead>
                <TableHead>Cambio vs Anterior</TableHead>
                <TableHead>Margen Promedio</TableHead>
                <TableHead>Estado Operacional</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCategories.map((category) => {
                // Buscar datos de performance para esta categoría
                const performance = state.categoriesPerformance.find(
                  p => p.category_id === category.id
                );
                
                return (
                  <TableRow key={category.id}>
                    {/* Nombre de Categoría */}
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{category.name}</span>
                        <span className="text-sm text-gray-500">{category.description || 'Sin descripción'}</span>
                      </div>
                    </TableCell>

                    {/* Ventas del Mes */}
                    <TableCell>
                      {state.performanceLoading ? (
                        <div className="animate-pulse h-4 bg-gray-200 rounded w-16"></div>
                      ) : performance ? (
                        <div className="flex flex-col">
                          <span className="font-medium">
                            S/{performance.sales_current_period.toLocaleString()}
                          </span>
                          <span className="text-xs text-gray-500">
                            vs S/{performance.sales_previous_period.toLocaleString()}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">Sin datos</span>
                      )}
                    </TableCell>

                    {/* Cambio vs Anterior con Tendencia Visual */}
                    <TableCell>
                      {state.performanceLoading ? (
                        <div className="animate-pulse h-4 bg-gray-200 rounded w-12"></div>
                      ) : performance ? (
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{performance.trend_icon}</span>
                          <div className="flex flex-col">
                            <span className={`font-medium ${
                              performance.sales_change_percentage > 0 ? 'text-green-600' :
                              performance.sales_change_percentage < 0 ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {performance.sales_change_percentage > 0 ? '+' : ''}
                              {performance.sales_change_percentage.toFixed(1)}%
                            </span>
                            <span className="text-xs text-gray-500 capitalize">
                              {performance.trend}
                            </span>
                          </div>
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </TableCell>

                    {/* Margen Promedio */}
                    <TableCell>
                      {state.performanceLoading ? (
                        <div className="animate-pulse h-4 bg-gray-200 rounded w-12"></div>
                      ) : performance ? (
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-blue-600">
                            {performance.avg_margin_percentage.toFixed(1)}%
                          </span>
                          <Badge variant="outline" className="text-xs">
                            Margen
                          </Badge>
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </TableCell>

                    {/* Estado Operacional */}
                    <TableCell>
                      {state.performanceLoading ? (
                        <div className="animate-pulse h-6 bg-gray-200 rounded w-20"></div>
                      ) : performance ? (
                        <div className="flex flex-col gap-1">
                          <Badge 
                            variant={
                              performance.operational_status === 'critical' ? 'destructive' :
                              performance.operational_status === 'warning' ? 'warning' : 'success'
                            }
                            className="w-fit"
                          >
                            {performance.operational_status === 'critical' ? '🚨 Crítico' :
                             performance.operational_status === 'warning' ? '⚠️ Atención' : '✅ Normal'}
                          </Badge>
                          {performance.critical_products > 0 && (
                            <span className="text-xs text-red-600">
                              {performance.critical_products} productos críticos
                            </span>
                          )}
                          {performance.products_with_alerts > 0 && performance.critical_products === 0 && (
                            <span className="text-xs text-orange-600">
                              {performance.products_with_alerts} alertas
                            </span>
                          )}
                        </div>
                      ) : (
                        <Badge variant="secondary">
                          {category.is_active ? 'Activa' : 'Inactiva'}
                        </Badge>
                      )}
                    </TableCell>

                    {/* Acciones */}
                    <TableCell>
                      <div className="flex gap-2">
                        {/* Botón Ver Análisis (nuevo) */}
                        {performance && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-blue-600"
                            onClick={() => {
                              // TODO: Abrir modal de análisis detallado
                              console.log('Ver análisis de', category.name);
                            }}
                          >
                            <BarChart3 className="h-4 w-4" />
                          </Button>
                        )}
                        
                        {/* Acciones existentes */}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(category)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteCategory(category.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>

          {/* Información adicional */}
          <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">
                📊 Mostrando {filteredCategories.length} categorías con datos de performance
              </span>
              <span className="text-gray-500 dark:text-gray-500">
                🔄 Datos actualizados hace {state.performanceLoading ? 'cargando...' : 'unos momentos'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Category Dialog */}
      <Dialog open={state.isDialogOpen} onOpenChange={(open) => {
        if (!open) handleCloseDialog();
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {state.selectedCategory ? 'Editar Categoría' : 'Nueva Categoría'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Nombre *</label>
              <Input
                value={state.formData.name || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, name: e.target.value }
                }))}
                placeholder="Nombre de la categoría"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Descripción</label>
              <Input
                value={state.formData.description || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, description: e.target.value }
                }))}
                placeholder="Descripción de la categoría"
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active"
                checked={state.formData.is_active !== false}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, is_active: e.target.checked }
                }))}
              />
              <label htmlFor="is_active" className="text-sm font-medium">
                Categoría activa
              </label>
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="ghost" onClick={handleCloseDialog}>
                Cancelar
              </Button>
              <Button onClick={handleSaveCategory} disabled={state.loading}>
                {state.loading ? 'Guardando...' : 'Guardar'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CategoriesPage;
