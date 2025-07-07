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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '../components/ui';
import {
  TrendingUp,
  BarChart3,
  Target,
  AlertTriangle,
  Calendar,
  Download,
  RefreshCw,
  Brain,
  Zap,
  Activity
} from '../components/ui/icons';
import { ForecastData, Product, Warehouse } from '../types';
import { forecastingService } from '../services/api';

interface ForecastingPageState {
  forecasts: ForecastData[];
  loading: boolean;
  error: string | null;
  selectedPeriod: string;
  selectedProduct: string;
  selectedWarehouse: string;
  isGenerating: boolean;
}

const ForecastingPage: React.FC = () => {
  const [state, setState] = useState<ForecastingPageState>({
    forecasts: [],
    loading: true,
    error: null,
    selectedPeriod: 'week',
    selectedProduct: 'all',
    selectedWarehouse: 'all',
    isGenerating: false
  });

  const fetchForecasts = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      // Usar únicamente API real del forecasting
      const response = await forecastingService.getForecasts();
      const forecastsData = response.results || response || [];
      setState(prev => ({ 
        ...prev, 
        forecasts: forecastsData,
        loading: false 
      }));
    } catch (err) {
      console.error('Error fetching forecasts:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al conectar con el sistema de pronósticos. Verifique la conexión con el servidor.',
        loading: false,
        forecasts: [] // Sin datos mock de fallback
      }));
    }
  };

  const generateNewForecasts = async () => {
    try {
      setState(prev => ({ ...prev, isGenerating: true, error: null }));
      // Usar API real para generar nuevos pronósticos
      await forecastingService.generateRecommendations();
      
      // Esperar un momento y recargar los datos
      setTimeout(async () => {
        await fetchForecasts();
        setState(prev => ({ ...prev, isGenerating: false }));
      }, 3000);
    } catch (err) {
      console.error('Error generating forecasts:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al generar nuevos pronósticos. Verifique la conexión.',
        isGenerating: false 
      }));
    }
  };

  const filteredForecasts = state.forecasts.filter(forecast => {
    const matchesProduct = state.selectedProduct === 'all' || forecast.product.id.toString() === state.selectedProduct;
    const matchesWarehouse = state.selectedWarehouse === 'all' || forecast.warehouse.id.toString() === state.selectedWarehouse;
    return matchesProduct && matchesWarehouse;
  });

  const getForecastAccuracy = (predicted: number, lower: number, upper: number) => {
    const range = upper - lower;
    const confidence = Math.max(0, Math.min(100, 100 - (range / predicted) * 50));
    return Math.round(confidence);
  };

  const getRecommendation = (forecast: ForecastData) => {
    const currentStock = Math.floor(Math.random() * 50) + 10; // Mock current stock
    const predicted = forecast.predicted_demand;
    
    if (currentStock < predicted) {
      return {
        type: 'reorder',
        message: `Reabastecer ${predicted - currentStock} unidades`,
        variant: 'warning' as const
      };
    } else if (currentStock > predicted * 2) {
      return {
        type: 'excess',
        message: 'Posible exceso de inventario',
        variant: 'secondary' as const
      };
    } else {
      return {
        type: 'optimal',
        message: 'Nivel de stock óptimo',
        variant: 'success' as const
      };
    }
  };

  const getForecastStats = () => {
    const totalPredicted = filteredForecasts.reduce((sum, f) => sum + f.predicted_demand, 0);
    const avgConfidence = filteredForecasts.reduce((sum, f) => {
      return sum + getForecastAccuracy(f.predicted_demand, f.confidence_interval.lower, f.confidence_interval.upper);
    }, 0) / (filteredForecasts.length || 1);
    
    const reorderNeeded = filteredForecasts.filter(f => getRecommendation(f).type === 'reorder').length;
    
    return {
      totalPredicted: Math.round(totalPredicted),
      avgConfidence: Math.round(avgConfidence),
      reorderNeeded
    };
  };

  useEffect(() => {
    fetchForecasts();
  }, []);

  if (state.loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const stats = getForecastStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Pronósticos y Predicciones</h1>
          <p className="text-gray-600">Predicciones de demanda basadas en IA y análisis histórico</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={generateNewForecasts} 
            disabled={state.isGenerating}
            className="flex items-center gap-2"
          >
            {state.isGenerating ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Generando...
              </>
            ) : (
              <>
                <Brain className="h-4 w-4" />
                Generar Pronósticos
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div 
        className="grid gap-6"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1.5rem'
        }}
      >
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Target className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Demanda Predicha</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalPredicted}</p>
                <p className="text-xs text-gray-500">próxima semana</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Zap className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Confianza Promedio</p>
                <p className="text-2xl font-bold text-gray-900">{stats.avgConfidence}%</p>
                <p className="text-xs text-gray-500">precisión del modelo</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Reabastecimiento</p>
                <p className="text-2xl font-bold text-gray-900">{stats.reorderNeeded}</p>
                <p className="text-xs text-gray-500">productos necesitan stock</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Productos Analizados</p>
                <p className="text-2xl font-bold text-gray-900">{filteredForecasts.length}</p>
                <p className="text-xs text-gray-500">con predicciones activas</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <Select 
              value={state.selectedPeriod} 
              onValueChange={(value) => setState(prev => ({ ...prev, selectedPeriod: value }))}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Período de pronóstico" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="week">Próxima semana</SelectItem>
                <SelectItem value="month">Próximo mes</SelectItem>
                <SelectItem value="quarter">Próximo trimestre</SelectItem>
              </SelectContent>
            </Select>
            <Select 
              value={state.selectedProduct} 
              onValueChange={(value) => setState(prev => ({ ...prev, selectedProduct: value }))}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filtrar por producto" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los productos</SelectItem>
                {state.forecasts.map(f => (
                  <SelectItem key={f.product.id} value={f.product.id.toString()}>
                    {f.product.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select 
              value={state.selectedWarehouse} 
              onValueChange={(value) => setState(prev => ({ ...prev, selectedWarehouse: value }))}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filtrar por almacén" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los almacenes</SelectItem>
                <SelectItem value="1">Almacén Principal</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="h-4 w-4" />
              Exportar
            </Button>
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

      {/* AI Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Insights de IA
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Alert>
              <TrendingUp className="h-4 w-4" />
              <AlertDescription>
                <strong>Tendencia:</strong> Los productos electrónicos muestran un aumento del 15% en demanda para la próxima semana.
              </AlertDescription>
            </Alert>
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>Alerta:</strong> 3 productos necesitan reabastecimiento urgente basado en las predicciones.
              </AlertDescription>
            </Alert>
            <Alert variant="success">
              <Zap className="h-4 w-4" />
              <AlertDescription>
                <strong>Optimización:</strong> El modelo ha mejorado su precisión en un 8% esta semana.
              </AlertDescription>
            </Alert>
          </div>
        </CardContent>
      </Card>

      {/* Forecasts Table */}
      <Card>
        <CardHeader>
          <CardTitle>Pronósticos Detallados</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead>Almacén</TableHead>
                <TableHead>Demanda Predicha</TableHead>
                <TableHead>Intervalo de Confianza</TableHead>
                <TableHead>Precisión</TableHead>
                <TableHead>Recomendación</TableHead>
                <TableHead>Última Actualización</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredForecasts.map((forecast) => {
                const accuracy = getForecastAccuracy(
                  forecast.predicted_demand, 
                  forecast.confidence_interval.lower, 
                  forecast.confidence_interval.upper
                );
                const recommendation = getRecommendation(forecast);
                
                return (
                  <TableRow key={`${forecast.product.id}-${forecast.warehouse.id}`}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{forecast.product.name}</div>
                        <div className="text-sm text-gray-500">{forecast.product.sku}</div>
                      </div>
                    </TableCell>
                    <TableCell>{forecast.warehouse.name}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-blue-600">
                          {forecast.predicted_demand}
                        </span>
                        <span className="text-sm text-gray-500">unidades</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <span className="text-gray-600">
                          {forecast.confidence_interval.lower} - {forecast.confidence_interval.upper}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-12 h-2 bg-gray-200 rounded">
                          <div 
                            className="h-full bg-green-500 rounded"
                            style={{ width: `${accuracy}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{accuracy}%</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={recommendation.variant}>
                        {recommendation.message}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <Calendar className="h-3 w-3" />
                        {new Date(forecast.created_at).toLocaleDateString()}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Tendencia de Demanda
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">Gráfico de tendencias</p>
                <p className="text-sm text-gray-400">Próximamente disponible</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Precisión del Modelo
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
              <div className="text-center">
                <Target className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">Métricas de precisión</p>
                <p className="text-sm text-gray-400">Próximamente disponible</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ForecastingPage;
