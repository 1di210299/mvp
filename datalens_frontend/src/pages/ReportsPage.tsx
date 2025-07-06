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
  FileText,
  Plus,
  Search,
  Download,
  Eye,
  Calendar,
  BarChart3,
  TrendingUp,
  DollarSign,
  Package,
  Clock,
  Filter,
  AlertTriangle
} from '../components/ui/icons';
import { Report, User } from '../types';
import { reportService } from '../services/api';

interface ReportsPageState {
  reports: Report[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  selectedType: string;
  selectedPeriod: string;
  isGenerating: boolean;
}

const ReportsPage: React.FC = () => {
  const [state, setState] = useState<ReportsPageState>({
    reports: [],
    loading: true,
    error: null,
    searchTerm: '',
    selectedType: 'all',
    selectedPeriod: 'all',
    isGenerating: false
  });

  const fetchReports = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      // Usar API real del sistema de reportes
      const response = await reportService.getReports();
      const reportsData = response.results || response || [];
      setState(prev => ({ 
        ...prev, 
        reports: reportsData,
        loading: false 
      }));
    } catch (err) {
      console.error('Error fetching reports:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al conectar con el sistema de reportes. Usando datos simulados.',
        loading: false 
      }));
      
      // Fallback a datos simulados solo si falla la API
      const mockReports: Report[] = [
        {
          id: 1,
          title: 'Reporte de Inventario Mensual',
          report_type: 'inventory',
          filters: {
            period: 'monthly',
            warehouse: 'all',
            category: 'electronics'
          },
          data: {
            total_products: 245,
            total_value: 125000,
            low_stock_items: 12,
            out_of_stock: 3
          },
          created_by: {
            id: 1,
            username: 'admin',
            email: 'admin@company.com',
            first_name: 'Admin',
            last_name: 'User',
            role: 'admin',
            company: {
              id: 1,
              name: 'Mi Empresa',
              ruc: '20123456789',
              address: 'Lima, Perú',
              email: 'info@empresa.com',
              subscription_type: 'premium',
              is_active: true
            },
            is_active: true,
            created_at: '2024-01-01T00:00:00Z'
          },
          created_at: '2024-07-01T14:30:00Z'
        }
      ];
      setState(prev => ({ ...prev, reports: mockReports }));
    }
  };

  const generateNewReport = async (type: string) => {
    try {
      setState(prev => ({ ...prev, isGenerating: true, error: null }));
      
      // Configurar datos para el reporte según el tipo
      const reportData = {
        report_type: type,
        title: `Reporte ${getReportTypeName(type)} - ${new Date().toLocaleDateString()}`,
        filters: { 
          period: 'current',
          generated_at: new Date().toISOString()
        }
      };
      
      // Usar API real para generar reporte
      await reportService.generateReport(reportData);
      
      // Recargar lista de reportes
      await fetchReports();
      setState(prev => ({ ...prev, isGenerating: false }));
      
    } catch (err) {
      console.error('Error generating report:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al generar reporte. Verifique la conexión.',
        isGenerating: false 
      }));
    }
  };

  const downloadReport = async (reportId: number) => {
    try {
      // Usar API real para descargar reporte
      const blob = await reportService.downloadReport(reportId);
      
      // Crear enlace de descarga
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `reporte_${reportId}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      console.error('Error downloading report:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al descargar reporte. Verifique la conexión.' 
      }));
    }
  };

  const filteredReports = state.reports.filter(report => {
    const matchesSearch = report.title.toLowerCase().includes(state.searchTerm.toLowerCase());
    const matchesType = state.selectedType === 'all' || report.report_type === state.selectedType;
    
    let matchesPeriod = true;
    if (state.selectedPeriod !== 'all') {
      const reportDate = new Date(report.created_at);
      const now = new Date();
      
      if (state.selectedPeriod === 'week') {
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        matchesPeriod = reportDate >= weekAgo;
      } else if (state.selectedPeriod === 'month') {
        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        matchesPeriod = reportDate >= monthAgo;
      }
    }
    
    return matchesSearch && matchesType && matchesPeriod;
  });

  const getReportIcon = (type: string) => {
    switch (type) {
      case 'inventory':
        return <Package className="h-4 w-4 text-blue-600" />;
      case 'sales':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'financial':
        return <DollarSign className="h-4 w-4 text-purple-600" />;
      case 'movement':
        return <BarChart3 className="h-4 w-4 text-orange-600" />;
      case 'forecast':
        return <TrendingUp className="h-4 w-4 text-indigo-600" />;
      default:
        return <FileText className="h-4 w-4 text-gray-600" />;
    }
  };

  const getReportTypeName = (type: string) => {
    const types: Record<string, string> = {
      inventory: 'Inventario',
      sales: 'Ventas',
      financial: 'Financiero',
      movement: 'Movimientos',
      forecast: 'Pronósticos'
    };
    return types[type] || 'Otro';
  };

  const getReportStats = () => {
    const totalReports = state.reports.length;
    const recentReports = state.reports.filter(r => {
      const reportDate = new Date(r.created_at);
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      return reportDate >= weekAgo;
    }).length;
    
    const reportsByType = state.reports.reduce((acc, report) => {
      acc[report.report_type] = (acc[report.report_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const mostCommonType = Object.entries(reportsByType).sort(([,a], [,b]) => b - a)[0];
    
    return {
      totalReports,
      recentReports,
      mostCommonType: mostCommonType ? mostCommonType[0] : 'inventory'
    };
  };

  useEffect(() => {
    fetchReports();
  }, []);

  if (state.loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const stats = getReportStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Generación de Reportes</h1>
          <p className="text-gray-600">Crea y gestiona reportes detallados de tu negocio</p>
        </div>
        <div className="flex gap-2">
          <Select onValueChange={(value) => generateNewReport(value)}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Generar nuevo reporte" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="inventory">Reporte de Inventario</SelectItem>
              <SelectItem value="sales">Reporte de Ventas</SelectItem>
              <SelectItem value="financial">Reporte Financiero</SelectItem>
              <SelectItem value="movement">Reporte de Movimientos</SelectItem>
              <SelectItem value="forecast">Reporte de Pronósticos</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Reportes</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalReports}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Esta Semana</p>
                <p className="text-2xl font-bold text-gray-900">{stats.recentReports}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              {getReportIcon(stats.mostCommonType)}
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Tipo Más Común</p>
                <p className="text-2xl font-bold text-gray-900">{getReportTypeName(stats.mostCommonType)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Download className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Descargas</p>
                <p className="text-2xl font-bold text-gray-900">42</p>
                <p className="text-xs text-gray-500">este mes</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Report Templates */}
      <Card>
        <CardHeader>
          <CardTitle>Plantillas de Reportes Rápidos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div 
              className="p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => generateNewReport('inventory')}
            >
              <div className="flex items-center gap-3">
                <Package className="h-8 w-8 text-blue-600" />
                <div>
                  <h3 className="font-semibold">Inventario Actual</h3>
                  <p className="text-sm text-gray-600">Stock, valores y alertas</p>
                </div>
              </div>
            </div>
            
            <div 
              className="p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => generateNewReport('movement')}
            >
              <div className="flex items-center gap-3">
                <BarChart3 className="h-8 w-8 text-orange-600" />
                <div>
                  <h3 className="font-semibold">Movimientos</h3>
                  <p className="text-sm text-gray-600">Entradas, salidas y ajustes</p>
                </div>
              </div>
            </div>
            
            <div 
              className="p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => generateNewReport('financial')}
            >
              <div className="flex items-center gap-3">
                <DollarSign className="h-8 w-8 text-purple-600" />
                <div>
                  <h3 className="font-semibold">Financiero</h3>
                  <p className="text-sm text-gray-600">Costos, márgenes y ROI</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Buscar reportes..."
                  value={state.searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
                  className="pl-10"
                />
              </div>
            </div>
            <Select 
              value={state.selectedType} 
              onValueChange={(value) => setState(prev => ({ ...prev, selectedType: value }))}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Tipo de reporte" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los tipos</SelectItem>
                <SelectItem value="inventory">Inventario</SelectItem>
                <SelectItem value="sales">Ventas</SelectItem>
                <SelectItem value="financial">Financiero</SelectItem>
                <SelectItem value="movement">Movimientos</SelectItem>
                <SelectItem value="forecast">Pronósticos</SelectItem>
              </SelectContent>
            </Select>
            <Select 
              value={state.selectedPeriod} 
              onValueChange={(value) => setState(prev => ({ ...prev, selectedPeriod: value }))}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Período" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los períodos</SelectItem>
                <SelectItem value="week">Última semana</SelectItem>
                <SelectItem value="month">Último mes</SelectItem>
              </SelectContent>
            </Select>
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

      {/* Reports Table */}
      <Card>
        <CardHeader>
          <CardTitle>Historial de Reportes</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reporte</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Creado por</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Datos Clave</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredReports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getReportIcon(report.report_type)}
                      <div>
                        <div className="font-medium">{report.title}</div>
                        <div className="text-sm text-gray-500">
                          ID: {report.id}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">
                      {getReportTypeName(report.report_type)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">
                        {report.created_by.first_name} {report.created_by.last_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {report.created_by.role}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <Calendar className="h-3 w-3 text-gray-400" />
                      <div>
                        <div>{new Date(report.created_at).toLocaleDateString()}</div>
                        <div className="text-gray-500">{new Date(report.created_at).toLocaleTimeString()}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {report.report_type === 'inventory' && (
                        <div>
                          <div>Productos: {report.data.total_products}</div>
                          <div className="text-gray-500">Valor: ${report.data.total_value?.toLocaleString()}</div>
                        </div>
                      )}
                      {report.report_type === 'movement' && (
                        <div>
                          <div>Movimientos: {report.data.total_movements}</div>
                          <div className="text-gray-500">Entradas: {report.data.inbound}</div>
                        </div>
                      )}
                      {report.report_type === 'financial' && (
                        <div>
                          <div>Valor: ${report.data.total_inventory_value?.toLocaleString()}</div>
                          <div className="text-gray-500">Margen: {report.data.profit_margin}%</div>
                        </div>
                      )}
                      {report.report_type === 'forecast' && (
                        <div>
                          <div>Productos: {report.data.products_analyzed}</div>
                          <div className="text-gray-500">Precisión: {report.data.avg_accuracy}%</div>
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => console.log(`Ver reporte ${report.id}`)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => downloadReport(report.id)}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Loading indicator */}
      {state.isGenerating && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span>Generando reporte...</span>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ReportsPage;
