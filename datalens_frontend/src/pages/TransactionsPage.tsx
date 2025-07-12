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
  ArrowUpDown,
  Plus,
  Search,
  Filter,
  Download,
  ArrowUp,
  ArrowDown,
  RotateCcw,
  Package,
  TrendingUp,
  AlertTriangle,
  Calendar,
  ArrowRight
} from '../components/ui/icons';
import { Transaction } from '../types';
import { inventoryService } from '../services/api';

interface TransactionsPageState {
  transactions: Transaction[];
  products: any[];
  locations: any[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  filterType: string;
  filterProduct: string;
  filterDateFrom: string;
  filterDateTo: string;
  isDialogOpen: boolean;
  formData: Partial<Transaction>;
  // Nuevos campos para paginación
  currentPage: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

const TransactionsPage: React.FC = () => {
  const [state, setState] = useState<TransactionsPageState>({
    transactions: [],
    products: [],
    locations: [],
    loading: true,
    error: null,
    searchTerm: '',
    filterType: 'all',
    filterProduct: 'all',
    filterDateFrom: '',
    filterDateTo: '',
    isDialogOpen: false,
    formData: {},
    // Inicializar paginación
    currentPage: 1,
    pageSize: 20,
    totalCount: 0,
    totalPages: 0,
    hasNext: false,
    hasPrevious: false
  });

  const fetchTransactions = async (page: number = 1, pageSize: number = 20) => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Llamar al API con parámetros de paginación
      const response = await fetch(`http://localhost:8080/api/inventory/transactions/?page=${page}&page_size=${pageSize}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) throw new Error('Error al cargar transacciones');
      
      const data = await response.json();
      
      setState(prev => ({ 
        ...prev, 
        transactions: data.results || [],
        totalCount: data.count || 0,
        currentPage: data.pagination?.page || page,
        totalPages: data.pagination?.total_pages || 0,
        hasNext: data.pagination?.has_next || false,
        hasPrevious: data.pagination?.has_previous || false,
        loading: false 
      }));
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al cargar transacciones',
        loading: false 
      }));
    }
  };

  // Funciones de navegación de páginas
  const goToPage = (page: number) => {
    if (page >= 1 && page <= state.totalPages) {
      fetchTransactions(page, state.pageSize);
    }
  };

  const goToFirstPage = () => goToPage(1);
  const goToLastPage = () => goToPage(state.totalPages);
  const goToNextPage = () => goToPage(state.currentPage + 1);
  const goToPreviousPage = () => goToPage(state.currentPage - 1);

  const changePageSize = (newPageSize: number) => {
    setState(prev => ({ ...prev, pageSize: newPageSize }));
    fetchTransactions(1, newPageSize);
  };

  const fetchProducts = async () => {
    try {
      const response = await inventoryService.getProducts();
      setState(prev => ({ 
        ...prev, 
        products: response.results || response
      }));
    } catch (err) {
      console.error('Error fetching products:', err);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await inventoryService.getLocations();
      setState(prev => ({ 
        ...prev, 
        locations: response.results || response
      }));
    } catch (err) {
      console.error('Error fetching locations:', err);
    }
  };

  const handleCreateTransaction = async () => {
    try {
      if (!state.formData.product || !state.formData.quantity || !state.formData.transaction_type) {
        setState(prev => ({ ...prev, error: 'Todos los campos obligatorios son requeridos' }));
        return;
      }

      setState(prev => ({ ...prev, loading: true, error: null }));
      
      await inventoryService.createTransaction({
        ...state.formData,
        quantity: Number(state.formData.quantity),
        unit_cost: state.formData.unit_cost ? Number(state.formData.unit_cost) : undefined
      });
      
      await fetchTransactions();
      handleCloseDialog();
    } catch (err) {
      console.error('Error creating transaction:', err);
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al crear transacción',
        loading: false 
      }));
    }
  };

  const handleCloseDialog = () => {
    setState(prev => ({
      ...prev,
      isDialogOpen: false,
      formData: {},
      error: null
    }));
  };

  const openCreateDialog = () => {
    setState(prev => ({
      ...prev,
      formData: {
        transaction_type: 'IN' as const,
        quantity: 0,
        notes: ''
      },
      isDialogOpen: true
    }));
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'IN':
      case 'PURCHASE':
      case 'RETURN':
        return 'success';
      case 'OUT':
      case 'SALE':
        return 'danger';
      case 'TRANSFER':
      case 'ADJUSTMENT':
        return 'warning';
      default:
        return 'secondary';
    }
  };

  const getTypeName = (type: string) => {
    const types: Record<string, string> = {
      'IN': 'Entrada',
      'OUT': 'Salida',
      'PURCHASE': 'Compra',
      'SALE': 'Venta',
      'TRANSFER': 'Transferencia',
      'ADJUSTMENT': 'Ajuste',
      'RETURN': 'Devolución'
    };
    return types[type] || type;
  };

  useEffect(() => {
    fetchTransactions();
    fetchProducts();
    fetchLocations();
  }, []);

  const filteredTransactions = state.transactions.filter(transaction => {
    const matchesSearch = (transaction.notes || '').toLowerCase().includes(state.searchTerm.toLowerCase()) ||
                         transaction.transaction_type.toLowerCase().includes(state.searchTerm.toLowerCase());
    
    const matchesType = state.filterType === 'all' || transaction.transaction_type === state.filterType;
    
    const matchesProduct = state.filterProduct === 'all' || 
                          transaction.product?.id?.toString() === state.filterProduct;

    const matchesDateFrom = !state.filterDateFrom || 
                           new Date(transaction.created_at) >= new Date(state.filterDateFrom);
    
    const matchesDateTo = !state.filterDateTo || 
                         new Date(transaction.created_at) <= new Date(state.filterDateTo);

    return matchesSearch && matchesType && matchesProduct && matchesDateFrom && matchesDateTo;
  });

  if (state.loading && state.transactions.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const totalTransactions = state.transactions.length;
  const inTransactions = state.transactions.filter(t => ['IN', 'PURCHASE', 'RETURN'].includes(t.transaction_type)).length;
  const outTransactions = state.transactions.filter(t => ['OUT', 'SALE'].includes(t.transaction_type)).length;
  const todayTransactions = state.transactions.filter(t => 
    new Date(t.created_at).toDateString() === new Date().toDateString()
  ).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Transacciones de Inventario</h1>
          <p className="text-gray-600">Gestiona y rastrea todos los movimientos de inventario</p>
        </div>
        <Button onClick={openCreateDialog} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Nueva Transacción
        </Button>
      </div>

      {/* Stats Cards - Actualizar con datos reales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ArrowUpDown className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Transacciones</p>
                <p className="text-2xl font-bold text-gray-900">{state.totalCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ArrowUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Entradas</p>
                <p className="text-2xl font-bold text-gray-900">
                  {state.transactions.filter(t => ['PURCHASE', 'purchase', 'adjustment'].includes(t.transaction_type) && Number(t.quantity) > 0).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ArrowDown className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Salidas</p>
                <p className="text-2xl font-bold text-gray-900">
                  {state.transactions.filter(t => ['SALE', 'sale'].includes(t.transaction_type) || Number(t.quantity) < 0).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">En esta página</p>
                <p className="text-2xl font-bold text-gray-900">{state.transactions.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
              <Input
                placeholder="Buscar transacciones..."
                value={state.searchTerm}
                onChange={(e) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
                className="pl-10"
              />
            </div>
            
            <Select value={state.filterType} onValueChange={(value) => setState(prev => ({ ...prev, filterType: value }))}>
              <SelectTrigger>
                <SelectValue placeholder="Tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los tipos</SelectItem>
                <SelectItem value="IN">Entrada</SelectItem>
                <SelectItem value="OUT">Salida</SelectItem>
                <SelectItem value="PURCHASE">Compra</SelectItem>
                <SelectItem value="SALE">Venta</SelectItem>
                <SelectItem value="TRANSFER">Transferencia</SelectItem>
                <SelectItem value="ADJUSTMENT">Ajuste</SelectItem>
              </SelectContent>
            </Select>

            <Select value={state.filterProduct} onValueChange={(value) => setState(prev => ({ ...prev, filterProduct: value }))}>
              <SelectTrigger>
                <SelectValue placeholder="Producto" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los productos</SelectItem>
                {state.products.map((product) => (
                  <SelectItem key={product.id} value={product.id.toString()}>
                    {product.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Input
              type="date"
              value={state.filterDateFrom}
              onChange={(e) => setState(prev => ({ ...prev, filterDateFrom: e.target.value }))}
              placeholder="Fecha desde"
            />

            <Input
              type="date"
              value={state.filterDateTo}
              onChange={(e) => setState(prev => ({ ...prev, filterDateTo: e.target.value }))}
              placeholder="Fecha hasta"
            />
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

      {/* Transactions Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>
            Lista de Transacciones 
            <span className="text-sm font-normal text-gray-500 ml-2">
              (Mostrando {((state.currentPage - 1) * state.pageSize) + 1}-{Math.min(state.currentPage * state.pageSize, state.totalCount)} de {state.totalCount})
            </span>
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Mostrar:</span>
            <Select value={state.pageSize.toString()} onValueChange={(value) => changePageSize(parseInt(value))}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="20">20</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Fecha</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Producto</TableHead>
                <TableHead>Cantidad</TableHead>
                <TableHead>Costo Unitario</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Ubicación</TableHead>
                <TableHead>Notas</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {state.transactions.map((transaction: any) => (
                <TableRow key={transaction.id}>
                  <TableCell>
                    {new Date(transaction.transaction_date || transaction.created_at).toLocaleDateString('es-ES', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </TableCell>
                  <TableCell>
                    <Badge variant={
                      ['purchase', 'PURCHASE'].includes(transaction.transaction_type) ? 'secondary' :
                      ['sale', 'SALE'].includes(transaction.transaction_type) ? 'destructive' :
                      'outline'
                    }>
                      {transaction.transaction_type.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {transaction.product_name || 'Producto desconocido'}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {Number(transaction.quantity) > 0 ? (
                        <ArrowUp className="h-3 w-3 text-green-600" />
                      ) : (
                        <ArrowDown className="h-3 w-3 text-red-600" />
                      )}
                      {Math.abs(Number(transaction.quantity))}
                    </div>
                  </TableCell>
                  <TableCell>
                    {transaction.unit_cost ? `S/ ${parseFloat(transaction.unit_cost.toString()).toFixed(2)}` : '-'}
                  </TableCell>
                  <TableCell className="font-semibold">
                    {transaction.unit_cost ? `S/ ${(Math.abs(Number(transaction.quantity)) * parseFloat(transaction.unit_cost.toString())).toFixed(2)}` : '-'}
                  </TableCell>
                  <TableCell>
                    {transaction.location_name || 'No especificada'}
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {transaction.notes || '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Componente de Paginación con iconos disponibles */}
          <div className="flex items-center justify-between px-2 py-4">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>
                Página {state.currentPage} de {state.totalPages}
              </span>
            </div>
            
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                onClick={goToFirstPage}
                disabled={!state.hasPrevious}
                className="h-8 px-2"
              >
                Primera
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={goToPreviousPage}
                disabled={!state.hasPrevious}
                className="h-8 px-2"
              >
                Anterior
              </Button>

              {/* Números de página */}
              {Array.from({ length: Math.min(5, state.totalPages) }, (_, i) => {
                const pageStart = Math.max(1, state.currentPage - 2);
                const pageNum = pageStart + i;
                if (pageNum > state.totalPages) return null;
                return (
                  <Button
                    key={pageNum}
                    variant={pageNum === state.currentPage ? "primary" : "outline"}
                    size="sm"
                    onClick={() => goToPage(pageNum)}
                    className="h-8 w-8 p-0"
                  >
                    {pageNum}
                  </Button>
                );
              })}

              <Button
                variant="outline"
                size="sm"
                onClick={goToNextPage}
                disabled={!state.hasNext}
                className="h-8 w-8 p-0"
              >
                <ArrowRight className="h-4 w-4" />
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={goToLastPage}
                disabled={!state.hasNext}
                className="h-8 px-2"
              >
                Última
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transaction Dialog */}
      <Dialog open={state.isDialogOpen} onOpenChange={(open) => {
        if (!open) handleCloseDialog();
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Nueva Transacción</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Tipo de Transacción *</label>
              <Select
                value={state.formData.transaction_type || ''}
                onValueChange={(value) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, transaction_type: value as 'IN' | 'OUT' | 'PURCHASE' | 'SALE' | 'TRANSFER' | 'ADJUSTMENT' | 'RETURN' }
                }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="IN">Entrada</SelectItem>
                  <SelectItem value="OUT">Salida</SelectItem>
                  <SelectItem value="PURCHASE">Compra</SelectItem>
                  <SelectItem value="SALE">Venta</SelectItem>
                  <SelectItem value="TRANSFER">Transferencia</SelectItem>
                  <SelectItem value="ADJUSTMENT">Ajuste</SelectItem>
                  <SelectItem value="RETURN">Devolución</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">Producto *</label>
              <Select
                value={state.formData.product?.toString() || ''}
                onValueChange={(value) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, product: parseInt(value) as any }
                }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar producto" />
                </SelectTrigger>
                <SelectContent>
                  {state.products.map((product) => (
                    <SelectItem key={product.id} value={product.id.toString()}>
                      {product.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">Cantidad *</label>
              <Input
                type="number"
                value={state.formData.quantity || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, quantity: parseInt(e.target.value) || 0 }
                }))}
                placeholder="0"
                min="1"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Costo Unitario</label>
              <Input
                type="number"
                step="0.01"
                value={state.formData.unit_cost || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, unit_cost: parseFloat(e.target.value) || undefined }
                }))}
                placeholder="0.00"
                min="0"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Ubicación</label>
              <Select
                value={(state.formData as any).location?.toString() || ''}
                onValueChange={(value) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, location: parseInt(value) } as any
                }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar ubicación" />
                </SelectTrigger>
                <SelectContent>
                  {state.locations.map((location) => (
                    <SelectItem key={location.id} value={location.id.toString()}>
                      {location.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">Notas</label>
              <Input
                value={state.formData.notes || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, notes: e.target.value }
                }))}
                placeholder="Descripción opcional"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="ghost" onClick={handleCloseDialog}>
                Cancelar
              </Button>
              <Button onClick={handleCreateTransaction} disabled={state.loading}>
                {state.loading ? 'Guardando...' : 'Crear Transacción'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TransactionsPage;
