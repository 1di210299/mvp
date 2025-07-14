import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  DialogTrigger,
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
  TableRow,
  CSVUploader
} from '../components/ui';
import {
  Package,
  Plus,
  Search,
  Edit,
  Trash2,
  Eye,
  Filter,
  Download,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  BarChart3,
  FolderOpen,
  RefreshCw,
  Activity,
  Settings,
  ChevronDown,
  X,
  Check
} from '../components/ui/icons';
import { inventoryService } from '../services/api';
import { Product, Category, Supplier, ApiResponse } from '../types';
import { useTheme } from '../contexts/ThemeContext';

interface ProductsPageState {
  products: Product[];
  categories: Category[];
  suppliers: Supplier[]; // FIX: Agregar suppliers al state
  loading: boolean;
  error: string | null;
  searchTerm: string;
  selectedCategory: string;
  sortField: string;
  sortDirection: 'asc' | 'desc';
  isDialogOpen: boolean;
  isUploadDialogOpen: boolean;
  isCategoryDialogOpen: boolean; // FIX: Dialog para crear categoría
  isSupplierDialogOpen: boolean; // FIX: Dialog para crear proveedor
  selectedProduct: Product | null;
  formData: Partial<Product>;
  categoryFormData: { name: string; description: string }; // FIX: Form data para categoría
  supplierFormData: { name: string; contact_name: string; email: string; phone: string }; // FIX: Form data para proveedor
  selectedProducts: number[];
  showAdvancedFilters: boolean;
  visibleColumns: {
    sku: boolean;
    category: boolean;
    price: boolean;
    stock: boolean;
    status: boolean;
    actions: boolean;
  };
  notification: string | null;
}

const ProductsPage: React.FC = () => {
  const navigate = useNavigate();
  const { actualTheme } = useTheme();
  const isDarkMode = actualTheme === 'dark';
  const [state, setState] = useState<ProductsPageState>({
    products: [],
    categories: [],
    suppliers: [], // FIX: Inicializar suppliers
    loading: true,
    error: null,
    searchTerm: '',
    selectedCategory: 'all',
    sortField: 'name',
    sortDirection: 'asc',
    isDialogOpen: false,
    isUploadDialogOpen: false,
    isCategoryDialogOpen: false, // FIX: Inicializar dialog de categoría
    isSupplierDialogOpen: false, // FIX: Inicializar dialog de proveedor
    selectedProduct: null,
    formData: {},
    categoryFormData: { name: '', description: '' }, // FIX: Inicializar formData de categoría
    supplierFormData: { name: '', contact_name: '', email: '', phone: '' }, // FIX: Inicializar formData de proveedor
    selectedProducts: [],
    showAdvancedFilters: false,
    visibleColumns: {
      sku: true,
      category: true,
      price: true,
      stock: true,
      status: true,
      actions: true
    },
    notification: null
  });

  const fetchProducts = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      const response: ApiResponse<Product> = await inventoryService.getProducts();
      setState(prev => ({ 
        ...prev, 
        products: response.results || [],
        loading: false,
        notification: 'Productos actualizados'
      }));
      
      // Auto-hide notification
      setTimeout(() => {
        setState(prev => ({ ...prev, notification: null }));
      }, 3000);
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al cargar productos',
        loading: false 
      }));
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await inventoryService.getCategories();
      const categories = response.results || response || [];
      setState(prev => ({ ...prev, categories }));
    } catch (err) {
      console.error('Error loading categories:', err);
      const fallbackCategories: Category[] = [
        { id: 1, name: 'Alimentos y Bebidas', description: 'Productos alimenticios', is_active: true },
        { id: 2, name: 'Textiles', description: 'Productos textiles', is_active: true },
        { id: 3, name: 'Artesanías', description: 'Productos artesanales', is_active: true },
      ];
      setState(prev => ({ ...prev, categories: fallbackCategories }));
    }
  };

  const fetchSuppliers = async () => {
    try {
      const response = await inventoryService.getSuppliers();
      const suppliers = response.results || response || [];
      setState(prev => ({ ...prev, suppliers }));
    } catch (err) {
      console.error('Error loading suppliers:', err);
      const fallbackSuppliers: Supplier[] = [
        { id: 1, name: 'Proveedor 1', contact_name: 'Contacto 1', email: 'contacto1@ejemplo.com', phone: '123456789', is_active: true },
        { id: 2, name: 'Proveedor 2', contact_name: 'Contacto 2', email: 'contacto2@ejemplo.com', phone: '987654321', is_active: true },
      ];
      setState(prev => ({ ...prev, suppliers: fallbackSuppliers }));
    }
  };

  const handleDeleteProduct = async (id: number) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar este producto? Esta acción no se puede deshacer.')) {
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true }));
      await inventoryService.deleteProduct(id);
      await fetchProducts();
      setState(prev => ({ ...prev, loading: false }));
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al eliminar producto',
        loading: false 
      }));
    }
  };

  const handleCreateProduct = async () => {
    if (!state.formData.name?.trim()) {
      setState(prev => ({ ...prev, error: 'El nombre del producto es requerido' }));
      return;
    }
    
    if (!state.formData.sku?.trim()) {
      setState(prev => ({ ...prev, error: 'El SKU del producto es requerido' }));
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      await inventoryService.createProduct(state.formData);
      await fetchProducts();
      setState(prev => ({ 
        ...prev, 
        isDialogOpen: false, 
        formData: {},
        selectedProduct: null,
        loading: false 
      }));
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al crear producto',
        loading: false 
      }));
    }
  };

  const handleUpdateProduct = async () => {
    if (!state.selectedProduct) return;
    
    if (!state.formData.name?.trim()) {
      setState(prev => ({ ...prev, error: 'El nombre del producto es requerido' }));
      return;
    }
    
    if (!state.formData.sku?.trim()) {
      setState(prev => ({ ...prev, error: 'El SKU del producto es requerido' }));
      return;
    }
    
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      await inventoryService.updateProduct(state.selectedProduct.id, state.formData);
      await fetchProducts();
      setState(prev => ({ 
        ...prev, 
        isDialogOpen: false, 
        formData: {},
        selectedProduct: null,
        loading: false 
      }));
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al actualizar producto',
        loading: false 
      }));
    }
  };

  const handleExportData = () => {
    try {
      const headers = ['Nombre', 'SKU', 'Descripción', 'Precio Venta', 'Precio Costo', 'Stock Mín', 'Stock Máx', 'Unidad', 'Estado'];
      const csvData = [
        headers.join(','),
        ...sortedProducts.map(product => [
          `"${product.name}"`,
          `"${product.sku}"`,
          `"${product.description || ''}"`,
          parseFloat(product.sale_price as string) || parseFloat(product.cost_price as string) || 0,
          parseFloat(product.cost_price as string) || 0,
          product.min_stock,
          product.max_stock,
          `"${product.unit || ''}"`,
          product.is_active ? 'Activo' : 'Inactivo'
        ].join(','))
      ].join('\n');

      const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `productos_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: 'Error al exportar datos' 
      }));
    }
  };

  const handleCSVUpload = async (csvData: any[]) => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      
      for (const row of csvData) {
        const productData = {
          name: row.nombre || row.name || '',
          sku: row.sku || row.codigo || '',
          description: row.descripcion || row.description || '',
          unit_price: parseFloat(row.precio || row.price || 0),
          cost_price: parseFloat(row.costo || row.cost || 0),
          min_stock: parseInt(row.stock_minimo || row.min_stock || 0),
          max_stock: parseInt(row.stock_maximo || row.max_stock || 0),
          unit: row.unidad || row.unit || 'unit',
          is_active: true
        };
        
        if (productData.name && productData.sku) {
          await inventoryService.createProduct(productData);
        }
      }
      
      await fetchProducts();
      setState(prev => ({ 
        ...prev, 
        isUploadDialogOpen: false,
        loading: false 
      }));
      
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al procesar archivo CSV',
        loading: false 
      }));
    }
  };

  const filteredProducts = state.products.filter(product => {
    const matchesSearch = (product.name || '').toLowerCase().includes(state.searchTerm.toLowerCase()) ||
                         (product.sku || '').toLowerCase().includes(state.searchTerm.toLowerCase());
    const matchesCategory = state.selectedCategory === 'all' || 
                           product.category.toString() === state.selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const sortedProducts = [...filteredProducts].sort((a, b) => {
    const aValue = a[state.sortField as keyof Product];
    const bValue = b[state.sortField as keyof Product];
    const direction = state.sortDirection === 'asc' ? 1 : -1;
    
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return aValue.localeCompare(bValue) * direction;
    }
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return (aValue - bValue) * direction;
    }
    return 0;
  });

  const openEditDialog = (product: Product) => {
    setState(prev => ({
      ...prev,
      selectedProduct: product,
      formData: { ...product },
      isDialogOpen: true
    }));
  };

  const openCreateDialog = () => {
    setState(prev => ({
      ...prev,
      selectedProduct: null,
      formData: {
        name: '',
        sku: '',
        description: '',
        unit_price: 0,
        cost_price: 0,
        min_stock: 0,
        max_stock: 0,
        reorder_point: 0,
        unit: '',
        is_active: true
      },
      isDialogOpen: true
    }));
  };

  const openCategoryDialog = () => {
    setState(prev => ({
      ...prev,
      categoryFormData: { name: '', description: '' },
      isCategoryDialogOpen: true
    }));
  };

  const openSupplierDialog = () => {
    setState(prev => ({
      ...prev,
      supplierFormData: { name: '', contact_name: '', email: '', phone: '' },
      isSupplierDialogOpen: true
    }));
  };

  const getStockStatus = (product: Product) => {
    // CORREGIDO: Usar 'stock' en lugar de 'current_stock' para coincidir con la API
    const currentStock = product.stock || product.current_stock || 0;
    const minStock = typeof product.min_stock === 'string' ? parseFloat(product.min_stock) : (product.min_stock || 0);
    const maxStock = typeof product.max_stock === 'string' ? parseFloat(product.max_stock) : (product.max_stock || 100);
    
    console.log(`🔍 Stock Status Debug - ${product.name}: stock=${currentStock}, min=${minStock}, max=${maxStock}`);
    
    if (currentStock <= 0) return { status: 'Sin Stock', color: 'red', severity: 'critical' };
    if (currentStock <= minStock) return { status: 'Bajo', color: 'orange', severity: 'warning' };
    if (currentStock >= maxStock) return { status: 'Alto', color: 'yellow', severity: 'info' };
    return { status: 'Normal', color: 'green', severity: 'success' };
  };

  const handleSelectProduct = (productId: number) => {
    setState(prev => ({
      ...prev,
      selectedProducts: prev.selectedProducts.includes(productId)
        ? prev.selectedProducts.filter(id => id !== productId)
        : [...prev.selectedProducts, productId]
    }));
  };

  const handleSelectAll = () => {
    setState(prev => ({
      ...prev,
      selectedProducts: prev.selectedProducts.length === sortedProducts.length
        ? []
        : sortedProducts.map(p => p.id)
    }));
  };

  const toggleColumn = (column: keyof typeof state.visibleColumns) => {
    setState(prev => ({
      ...prev,
      visibleColumns: {
        ...prev.visibleColumns,
        [column]: !prev.visibleColumns[column]
      }
    }));
  };

  const truncateDescription = (text: string, maxLength: number = 80) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  const handleBulkStatusChange = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      // Implementar cambio masivo de estado
      setState(prev => ({ ...prev, selectedProducts: [], loading: false }));
    } catch (err) {
      setState(prev => ({ ...prev, error: 'Error al cambiar estado', loading: false }));
    }
  };

  const handleBulkDelete = async () => {
    if (!window.confirm(`¿Estás seguro de que quieres eliminar ${state.selectedProducts.length} productos? Esta acción no se puede deshacer.`)) {
      return;
    }
    
    try {
      setState(prev => ({ ...prev, loading: true }));
      for (const id of state.selectedProducts) {
        await inventoryService.deleteProduct(id);
      }
      await fetchProducts();
      setState(prev => ({ ...prev, selectedProducts: [], loading: false }));
    } catch (err) {
      setState(prev => ({ ...prev, error: 'Error al eliminar productos', loading: false }));
    }
  };

  const handleCreateCategory = async () => {
    if (!state.categoryFormData.name?.trim()) {
      setState(prev => ({ ...prev, error: 'El nombre de la categoría es requerido' }));
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      await inventoryService.createCategory(state.categoryFormData);
      await fetchCategories();
      setState(prev => ({ 
        ...prev, 
        isCategoryDialogOpen: false, 
        categoryFormData: { name: '', description: '' },
        loading: false 
      }));
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al crear categoría',
        loading: false 
      }));
    }
  };

  const handleCreateSupplier = async () => {
    if (!state.supplierFormData.name?.trim()) {
      setState(prev => ({ ...prev, error: 'El nombre del proveedor es requerido' }));
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      await inventoryService.createSupplier(state.supplierFormData);
      await fetchSuppliers();
      setState(prev => ({ 
        ...prev, 
        isSupplierDialogOpen: false, 
        supplierFormData: { name: '', contact_name: '', email: '', phone: '' },
        loading: false 
      }));
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al crear proveedor',
        loading: false 
      }));
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchCategories();
    fetchSuppliers(); // FIX: Cargar proveedores al iniciar
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      if (!state.loading) {
        fetchProducts();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [state.loading]);

  const handleRefresh = async () => {
    await fetchProducts();
    await fetchCategories();
    await fetchSuppliers(); // FIX: Refrescar proveedores
  };

  useEffect(() => {
    if (state.error) {
      const timer = setTimeout(() => {
        setState(prev => ({ ...prev, error: null }));
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [state.error]);

  const columnConfig = [
    { key: 'sku', label: 'SKU', icon: '🏷️' },
    { key: 'category', label: 'Categoría', icon: '📁' },
    { key: 'price', label: 'Precio', icon: '💰' },
    { key: 'stock', label: 'Stock', icon: '📦' },
    { key: 'status', label: 'Estado', icon: '✅' },
    { key: 'actions', label: 'Acciones', icon: '⚡' },
  ];

  const activeFiltersCount = (state.searchTerm ? 1 : 0) + (state.selectedCategory !== 'all' ? 1 : 0);

  if (state.loading && state.products.length === 0) {
    return (
      <div className={`flex items-center justify-center min-h-[400px] ${isDarkMode ? 'bg-gray-900' : 'bg-slate-50'}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className={`font-medium ${isDarkMode ? 'text-gray-300' : 'text-slate-600'}`}>Cargando productos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-gray-900' : 'bg-slate-50'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* ENCABEZADO CON ACCIONES DESTACADAS */}
        <div className={`rounded-xl shadow-sm border mb-8 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-slate-200'}`}>
          <div className="flex items-center justify-between p-6">
            <div>
              <h1 className={`text-3xl font-bold mb-2 ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>Gestión de Productos</h1>
              <p className={isDarkMode ? 'text-gray-300' : 'text-slate-600'}>
                <span className={`font-semibold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>{state.products.length}</span> productos registrados
                {state.notification && (
                  <span className="ml-3 text-sm text-emerald-600 font-medium">
                    ✓ {state.notification}
                  </span>
                )}
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <Button 
                variant="outline" 
                onClick={handleRefresh}
                disabled={state.loading}
                className={`flex items-center gap-2 px-4 py-2 border ${isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}
              >
                <RefreshCw className={`h-4 w-4 ${state.loading ? 'animate-spin' : ''}`} />
                Actualizar
              </Button>
              
              <Button 
                variant="outline" 
                onClick={() => setState(prev => ({ ...prev, isUploadDialogOpen: true }))}
                className={`flex items-center gap-2 px-4 py-2 border ${isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}
              >
                <FolderOpen className="h-4 w-4" />
                Subir CSV
              </Button>
              
              <Button 
                onClick={openCreateDialog} 
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 font-semibold shadow-sm"
              >
                <Plus className="h-4 w-4" />
                Nuevo Producto
              </Button>
            </div>
          </div>
        </div>

        {/* MÉTRICAS EN GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className={`border hover:shadow-lg transition-all duration-200 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-slate-200'}`}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-3 bg-indigo-100 rounded-xl">
                      <Package className="h-6 w-6 text-indigo-600" />
                    </div>
                    <div>
                      <p className={`text-sm font-semibold uppercase tracking-wider ${isDarkMode ? 'text-gray-400' : 'text-slate-600'}`}>Total Productos</p>
                      <p className={`text-3xl font-bold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>{state.products.length}</p>
                    </div>
                  </div>
                  <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>productos únicos registrados</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={`border hover:shadow-lg transition-all duration-200 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-slate-200'}`}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-3 bg-red-100 rounded-xl">
                      <AlertTriangle className="h-6 w-6 text-red-600" />
                    </div>
                    <div>
                      <p className={`text-sm font-semibold uppercase tracking-wider ${isDarkMode ? 'text-gray-400' : 'text-slate-600'}`}>Stock Crítico</p>
                      <p className="text-3xl font-bold text-red-600">
                        {state.products.filter(p => getStockStatus(p).severity === 'critical' || getStockStatus(p).severity === 'warning').length}
                      </p>
                    </div>
                  </div>
                  <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>productos requieren atención</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={`border hover:shadow-lg transition-all duration-200 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-slate-50 border-slate-200'}`}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-3 bg-emerald-100 rounded-xl">
                      <TrendingUp className="h-6 w-6 text-emerald-600" />
                    </div>
                    <div>
                      <p className={`text-sm font-semibold uppercase tracking-wider ${isDarkMode ? 'text-gray-400' : 'text-slate-600'}`}>Productos Activos</p>
                      <p className="text-3xl font-bold text-emerald-600">
                        {state.products.filter(p => p.is_active).length}
                      </p>
                    </div>
                  </div>
                  <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>disponibles para venta</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={`border hover:shadow-lg transition-all duration-200 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-slate-50 border-slate-200'}`}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-3 bg-purple-100 rounded-xl">
                      <DollarSign className="h-6 w-6 text-purple-600" />
                    </div>
                    <div>
                      <p className={`text-sm font-semibold uppercase tracking-wider ${isDarkMode ? 'text-gray-400' : 'text-slate-600'}`}>Precio Promedio</p>
                      <p className="text-3xl font-bold text-purple-600">
                        S/ {(state.products.reduce((sum, p) => {
                          const price = parseFloat(p.sale_price as string) || parseFloat(p.cost_price as string) || 0;
                          return sum + price;
                        }, 0) / state.products.length || 0).toFixed(0)}
                      </p>
                    </div>
                  </div>
                  <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>valor unitario promedio</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* SECCIÓN DE FILTROS PROFESIONAL */}
        <div className="space-y-4 mb-8">
          {/* Barra principal de búsqueda y acciones */}
          <div className={`rounded-xl shadow-sm border p-4 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'}`}>
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Búsqueda */}
              <div className="flex-1">
                <div className="relative">
                  <Search className={`absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 ${isDarkMode ? 'text-gray-400' : 'text-gray-400'}`} />
                  <input
                    type="text"
                    placeholder="Buscar productos..."
                    value={state.searchTerm}
                    onChange={(e) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
                    className={`w-full pl-12 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm ${
                      isDarkMode 
                        ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:bg-gray-600' 
                        : 'bg-gray-50 border-gray-200 focus:bg-white'
                    }`}
                  />
                  {state.searchTerm && (
                    <button
                      onClick={() => setState(prev => ({ ...prev, searchTerm: '' }))}
                      className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-lg transition-colors ${
                        isDarkMode ? 'hover:bg-gray-600' : 'hover:bg-gray-100'
                      }`}
                    >
                      <X className={`h-4 w-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                    </button>
                  )}
                </div>
              </div>

              {/* Acciones rápidas */}
              <div className="flex gap-2">
                {/* Filtros avanzados */}
                <button
                  onClick={() => setState(prev => ({ ...prev, showAdvancedFilters: !prev.showAdvancedFilters }))}
                  className={`
                    flex items-center gap-2 px-4 py-3 rounded-xl border transition-all text-sm font-medium
                    ${state.showAdvancedFilters 
                      ? 'bg-indigo-50 border-indigo-200 text-indigo-700' 
                      : isDarkMode 
                        ? 'bg-gray-800 border-gray-600 text-gray-300 hover:bg-gray-700'
                        : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'}
                  `}
                >
                  <Settings className="h-4 w-4" />
                  <span className="hidden sm:inline">Filtros</span>
                  {activeFiltersCount > 0 && (
                    <span className="ml-1 px-2 py-0.5 bg-indigo-600 text-white text-xs rounded-full">
                      {activeFiltersCount}
                    </span>
                  )}
                </button>

                {/* Exportar */}
                <button 
                  onClick={handleExportData}
                  className={`flex items-center gap-2 px-4 py-3 border rounded-xl transition-colors text-sm font-medium ${
                    isDarkMode 
                      ? 'bg-gray-800 border-gray-600 text-gray-300 hover:bg-gray-700'
                      : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Download className="h-4 w-4" />
                  <span className="hidden sm:inline">Exportar</span>
                </button>

                {/* Actualizar */}
                <button
                  onClick={handleRefresh}
                  disabled={state.loading}
                  className="flex items-center gap-2 px-4 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors text-sm font-medium disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${state.loading ? 'animate-spin' : ''}`} />
                  <span className="hidden sm:inline">{state.loading ? 'Cargando' : 'Actualizar'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Panel de filtros avanzados */}
          {state.showAdvancedFilters && (
            <div className={`rounded-xl shadow-sm border p-6 animate-in slide-in-from-top-2 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'}`}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Categorías */}
                <div>
                  <h3 className={`text-sm font-semibold mb-3 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Categorías</h3>
                  <div className="space-y-2">
                    <button
                      onClick={() => setState(prev => ({ ...prev, selectedCategory: 'all' }))}
                      className={`
                        w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all
                        ${state.selectedCategory === 'all' 
                          ? 'bg-indigo-50 text-indigo-700 font-medium' 
                          : isDarkMode 
                            ? 'hover:bg-gray-700 text-gray-300'
                            : 'hover:bg-gray-50 text-gray-700'}
                      `}
                    >
                      <span>Todas las categorías</span>
                      <span className={`
                        px-2 py-0.5 rounded-full text-xs
                        ${state.selectedCategory === 'all' ? 'bg-indigo-200' : isDarkMode ? 'bg-gray-600' : 'bg-gray-100'}
                      `}>
                        {state.products.length}
                      </span>
                    </button>
                    {state.categories.map(cat => (
                      <button
                        key={cat.id}
                        onClick={() => setState(prev => ({ ...prev, selectedCategory: cat.id.toString() }))}
                        className={`
                          w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all
                          ${state.selectedCategory === cat.id.toString() 
                            ? 'bg-indigo-50 text-indigo-700 font-medium' 
                            : isDarkMode 
                              ? 'hover:bg-gray-700 text-gray-300'
                              : 'hover:bg-gray-50 text-gray-700'}
                        `}
                      >
                        <span>{cat.name}</span>
                        <span className={`
                          px-2 py-0.5 rounded-full text-xs
                          ${state.selectedCategory === cat.id.toString() ? 'bg-indigo-200' : isDarkMode ? 'bg-gray-600' : 'bg-gray-100'}
                        `}>
                          {state.products.filter(p => p.category === cat.id).length}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Columnas visibles */}
                <div className="md:col-span-2">
                  <h3 className={`text-sm font-semibold mb-3 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Columnas visibles</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {columnConfig.map(col => (
                      <button
                        key={col.key}
                        onClick={() => toggleColumn(col.key as keyof typeof state.visibleColumns)}
                        className={`
                          flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all
                          ${state.visibleColumns[col.key as keyof typeof state.visibleColumns] 
                            ? isDarkMode 
                              ? 'bg-gray-700 text-white border border-gray-600' 
                              : 'bg-gray-50 text-gray-900 border border-gray-200'
                            : isDarkMode 
                              ? 'bg-gray-800 text-gray-400 border border-transparent'
                              : 'bg-gray-100 text-gray-400 border border-transparent'}
                        `}
                      >
                        <span className="text-base">{col.icon}</span>
                        <span className="flex-1 text-left">{col.label}</span>
                        {state.visibleColumns[col.key as keyof typeof state.visibleColumns] && (
                          <Check className="h-4 w-4 text-indigo-600" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Limpiar filtros */}
              {activeFiltersCount > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <button
                    onClick={() => {
                      setState(prev => ({ 
                        ...prev, 
                        searchTerm: '',
                        selectedCategory: 'all'
                      }));
                    }}
                    className={`text-sm font-medium ${isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}
                  >
                    Limpiar todos los filtros
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Resumen de resultados */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                Mostrando <span className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{sortedProducts.length} productos</span>
              </span>
              
              {/* Chips de filtros activos */}
              {activeFiltersCount > 0 && (
                <div className="flex items-center gap-2">
                  {state.searchTerm && (
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs ${isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'}`}>
                      Búsqueda: "{state.searchTerm}"
                      <button
                        onClick={() => setState(prev => ({ ...prev, searchTerm: '' }))}
                        className={`ml-1 ${isDarkMode ? 'hover:text-white' : 'hover:text-gray-900'}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  )}
                  
                  {state.selectedCategory !== 'all' && (
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs ${isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'}`}>
                      {state.categories.find(c => c.id.toString() === state.selectedCategory)?.name}
                      <button
                        onClick={() => setState(prev => ({ ...prev, selectedCategory: 'all' }))}
                        className={`ml-1 ${isDarkMode ? 'hover:text-white' : 'hover:text-gray-900'}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Acciones masivas */}
            {state.selectedProducts.length > 0 && (
              <div className="flex items-center gap-2">
                <span className={`mr-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  {state.selectedProducts.length} seleccionados
                </span>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleBulkStatusChange}
                  className="text-xs"
                >
                  <Edit className="h-3 w-3 mr-1" />
                  Cambiar Estado
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleBulkDelete}
                  className="text-xs text-red-600 border-red-200 hover:bg-red-50"
                >
                  <Trash2 className="h-3 w-3 mr-1" />
                  Eliminar
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* ALERTAS DE ERROR */}
        {state.error && (
          <Alert variant="destructive" className="border-red-200 bg-red-50 mb-6">
            <AlertTriangle className="h-5 w-5" />
            <AlertDescription className="text-red-800 font-medium">{state.error}</AlertDescription>
          </Alert>
        )}

        {/* TABLA DE PRODUCTOS */}
        <Card className={`border shadow-sm ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-slate-200'}`}>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className={`border-b-2 ${isDarkMode ? 'border-gray-600 bg-gray-700' : 'border-slate-200 bg-slate-50'}`}>
                    <TableHead className="w-12 pl-6 py-4">
                      <input
                        type="checkbox"
                        checked={state.selectedProducts.length === sortedProducts.length && sortedProducts.length > 0}
                        onChange={handleSelectAll}
                        className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </TableHead>
                    
                    <TableHead className={`font-bold text-sm py-4 min-w-[350px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                      Producto
                    </TableHead>
                    
                    {state.visibleColumns.sku && (
                      <TableHead className={`font-bold text-sm py-4 min-w-[120px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>SKU</TableHead>
                    )}
                    
                    {state.visibleColumns.category && (
                      <TableHead className={`font-bold text-sm py-4 min-w-[140px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>Categoría</TableHead>
                    )}
                    
                    {state.visibleColumns.price && (
                      <TableHead className={`font-bold text-sm py-4 text-right min-w-[120px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>Precio</TableHead>
                    )}
                    
                    {state.visibleColumns.stock && (
                      <TableHead className={`font-bold text-sm py-4 min-w-[180px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>Stock & Estado</TableHead>
                    )}
                    
                    {state.visibleColumns.actions && (
                      <TableHead className={`font-bold text-sm py-4 w-32 pr-6 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>Acciones</TableHead>
                    )}
                  </TableRow>
                </TableHeader>
                
                <TableBody>
                  {sortedProducts.map((product, index) => {
                    const stockStatus = getStockStatus(product);
                    const isSelected = state.selectedProducts.includes(product.id);
                    const isEven = index % 2 === 0;
                    
                    return (
                      <TableRow 
                        key={product.id} 
                        className={`
                          border-b transition-colors duration-150
                          ${isSelected 
                            ? 'bg-indigo-50 border-indigo-200' 
                            : isDarkMode 
                              ? (isEven ? 'bg-gray-800 border-gray-700 hover:bg-gray-750' : 'bg-gray-750 border-gray-700 hover:bg-gray-700')
                              : (isEven ? 'bg-white border-slate-100 hover:bg-indigo-25' : 'bg-slate-25 border-slate-100 hover:bg-indigo-25')
                          }
                        `}
                      >
                        <TableCell className="pl-6 py-3">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleSelectProduct(product.id)}
                            className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                          />
                        </TableCell>
                        
                        <TableCell className="py-3">
                          <div className="max-w-[320px]">
                            <div className={`font-semibold text-base leading-tight mb-1 ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                              {product.name}
                            </div>
                            {product.description && (
                              <div className={`text-sm leading-relaxed ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>
                                {truncateDescription(product.description, 90)}
                                {product.description.length > 90 && (
                                  <button 
                                    className="text-indigo-600 hover:text-indigo-800 ml-1 text-sm underline"
                                    title={product.description}
                                  >
                                    ver más
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        </TableCell>
                        
                        {state.visibleColumns.sku && (
                          <TableCell className="py-3">
                            <span className={`font-mono text-sm px-3 py-1.5 rounded-md border ${isDarkMode ? 'bg-gray-700 text-gray-300 border-gray-600' : 'bg-slate-100 text-slate-700 border-slate-300'}`}>
                              {product.sku}
                            </span>
                          </TableCell>
                        )}
                        
                        {state.visibleColumns.category && (
                          <TableCell className="py-3">
                            <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-semibold bg-blue-100 text-blue-800 border border-blue-200">
                              {product.category_name || 'Sin categoría'}
                            </span>
                          </TableCell>
                        )}
                        
                        {state.visibleColumns.price && (
                          <TableCell className="py-3 text-right">
                            <div className={`font-bold text-lg ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                              S/ {(parseFloat(product.sale_price as string) || parseFloat(product.cost_price as string) || 0).toFixed(2)}
                            </div>
                            <div className={`text-xs font-medium ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>por unidad</div>
                          </TableCell>
                        )}
                        
                        {state.visibleColumns.stock && (
                          <TableCell className="py-3">
                            <div className="space-y-2">
                              <div className="flex items-center gap-3">
                                <span 
                                  className={`inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-bold border ${
                                    stockStatus.severity === 'critical' ? 'bg-red-100 text-red-800 border-red-200' :
                                    stockStatus.severity === 'warning' ? 'bg-orange-100 text-orange-800 border-orange-200' :
                                    stockStatus.severity === 'info' ? 'bg-yellow-100 text-yellow-800 border-yellow-200' :
                                    'bg-green-100 text-green-800 border-green-200'
                                  }`}
                                >
                                  {stockStatus.status}
                                </span>
                                <span className={`text-sm font-mono font-semibold ${isDarkMode ? 'text-gray-300' : 'text-slate-600'}`}>
                                  {(product.stock || product.current_stock || 0).toFixed(1)}
                                </span>
                              </div>
                              
                              <span 
                                className={`inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold border ${
                                  product.is_active 
                                    ? 'bg-emerald-100 text-emerald-800 border-emerald-200' 
                                    : 'bg-gray-100 text-gray-800 border-gray-200'
                                }`}
                              >
                                {product.is_active ? 'ACTIVO' : 'INACTIVO'}
                              </span>
                            </div>
                          </TableCell>
                        )}
                        
                        {state.visibleColumns.actions && (
                          <TableCell className="py-3 pr-6">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => openEditDialog(product)}
                                className={`p-2.5 rounded-lg transition-all duration-150 ${isDarkMode ? 'text-gray-400 hover:text-indigo-400 hover:bg-gray-700' : 'text-slate-400 hover:text-indigo-600 hover:bg-indigo-50'}`}
                                title="Editar producto"
                              >
                                <Edit className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteProduct(product.id)}
                                className={`p-2.5 rounded-lg transition-all duration-150 ${isDarkMode ? 'text-gray-400 hover:text-red-400 hover:bg-gray-700' : 'text-slate-400 hover:text-red-600 hover:bg-red-50'}`}
                                title="Eliminar producto"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              
              {sortedProducts.length === 0 && (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                  <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 ${isDarkMode ? 'bg-gray-700' : 'bg-slate-100'}`}>
                    <Package className={`h-10 w-10 ${isDarkMode ? 'text-gray-400' : 'text-slate-400'}`} />
                  </div>
                  <h3 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-gray-300' : 'text-slate-600'}`}>No se encontraron productos</h3>
                  <p className={`text-base max-w-md ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>
                    {state.searchTerm ? 'Intenta ajustar los filtros de búsqueda' : 'Comienza creando tu primer producto'}
                  </p>
                  {!state.searchTerm && (
                    <Button onClick={openCreateDialog} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
                      <Plus className="h-4 w-4 mr-2" />
                      Crear Producto
                    </Button>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Navegación rápida flotante */}
        <div className="fixed bottom-6 right-6 flex flex-col gap-3">
          <button 
            onClick={() => navigate('/inventory')}
            className="p-4 bg-cyan-500 hover:bg-cyan-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
            title="Ir a Inventario"
          >
            <BarChart3 className="h-5 w-5" />
          </button>
          <button 
            onClick={() => navigate('/categories')}
            className="p-4 bg-emerald-500 hover:bg-emerald-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
            title="Ir a Categorías"
          >
            <Package className="h-5 w-5" />
          </button>
        </div>

        {/* Product Dialog */}
        <Dialog open={state.isDialogOpen} onOpenChange={(open) => setState(prev => ({ ...prev, isDialogOpen: open, error: null }))}>
          <DialogContent className={`max-w-4xl max-h-[90vh] overflow-y-auto ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'}`}>
            <div className="pb-6">
              <DialogHeader>
                <DialogTitle>
                  <span className={isDarkMode ? 'text-white' : 'text-gray-900'}>
                    {state.selectedProduct ? 'Editar Producto' : 'Crear Nuevo Producto'}
                  </span>
                </DialogTitle>
              </DialogHeader>
            </div>
            
            {state.error && (
              <Alert variant="destructive" className="mb-6">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="font-medium">{state.error}</AlertDescription>
              </Alert>
            )}
            
            <div className="grid grid-cols-2 gap-8">
              <div className="space-y-6">
                <div>
                  <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                    Nombre del Producto *
                  </label>
                  <Input
                    value={state.formData.name || ''}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, name: e.target.value },
                      error: null
                    }))}
                    placeholder="Ingresa el nombre del producto"
                    className={`h-12 ${!state.formData.name?.trim() ? 'border-red-300 focus:border-red-400' : isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                  />
                </div>
                
                <div>
                  <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                    SKU / Código *
                  </label>
                  <Input
                    value={state.formData.sku || ''}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, sku: e.target.value },
                      error: null
                    }))}
                    placeholder="Código único del producto"
                    className={`h-12 ${!state.formData.sku?.trim() ? 'border-red-300 focus:border-red-400' : isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                  />
                </div>

                {/* FIX: Agregar dropdown de categorías con opción de crear nueva */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className={`text-sm font-semibold ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                      Categoría
                    </label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={openCategoryDialog}
                      className={`text-xs ${isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      Nueva
                    </Button>
                  </div>
                  {/* Temporary native select for debugging */}
                  <select
                    value={state.formData.category?.toString() || ''}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, category: e.target.value ? parseInt(e.target.value) : undefined }
                    }))}
                    className={`h-12 w-full px-4 border rounded-xl ${isDarkMode ? 'border-gray-600 bg-gray-700 text-white' : 'border-slate-300 bg-white'}`}
                  >
                    <option value="">Selecciona una categoría...</option>
                    {state.categories.map(category => (
                      <option key={category.id} value={category.id.toString()}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                  {/* Debug info */}
                  {state.categories.length === 0 && (
                    <div className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      ⚠️ No hay categorías cargadas. Total: {state.categories.length}
                    </div>
                  )}
                  {state.categories.length > 0 && (
                    <div className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      ✅ {state.categories.length} categorías cargadas
                    </div>
                  )}
                </div>

                {/* FIX: Agregar dropdown de proveedores con opción de crear nuevo */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className={`text-sm font-semibold ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                      Proveedor
                    </label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={openSupplierDialog}
                      className={`text-xs ${isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      Nuevo
                    </Button>
                  </div>
                  {/* Temporary native select for debugging */}
                  <select
                    value={state.formData.supplier?.toString() || ''}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, supplier: e.target.value ? parseInt(e.target.value) : undefined }
                    }))}
                    className={`h-12 w-full px-4 border rounded-xl ${isDarkMode ? 'border-gray-600 bg-gray-700 text-white' : 'border-slate-300 bg-white'}`}
                  >
                    <option value="">Selecciona un proveedor...</option>
                    {state.suppliers.map(supplier => (
                      <option key={supplier.id} value={supplier.id.toString()}>
                        {supplier.name}
                      </option>
                    ))}
                  </select>
                  {/* Debug info */}
                  {state.suppliers.length === 0 && (
                    <div className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      ⚠️ No hay proveedores cargados. Total: {state.suppliers.length}
                    </div>
                  )}
                  {state.suppliers.length > 0 && (
                    <div className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      ✅ {state.suppliers.length} proveedores cargados
                    </div>
                  )}
                </div>
                
                <div>
                  <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                    Descripción
                  </label>
                  <textarea
                    value={state.formData.description || ''}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, description: e.target.value }
                    }))}
                    placeholder="Descripción detallada del producto"
                    rows={4}
                    className={`w-full p-3 border rounded-lg focus:ring-indigo-400 resize-none ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white placeholder-gray-400' : 'border-slate-300 focus:border-indigo-400'}`}
                  />
                </div>
                
                <div>
                  <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                    Unidad de Medida
                  </label>
                  <Input
                    value={state.formData.unit || ''}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, unit: e.target.value }
                    }))}
                    placeholder="ej: unidad, kg, litro, caja"
                    className={`h-12 ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                  />
                </div>
              </div>
              
              <div className="space-y-6">
                <div>
                  <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                    Precio de Venta
                  </label>
                  <div className="relative">
                    <span className={`absolute left-3 top-1/2 transform -translate-y-1/2 font-medium ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>S/</span>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      value={state.formData.unit_price || ''}
                      onChange={(e) => setState(prev => ({ 
                        ...prev, 
                        formData: { ...prev.formData, unit_price: parseFloat(e.target.value) || 0 }
                      }))}
                      placeholder="0.00"
                      className={`h-12 pl-12 ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                    />
                  </div>
                </div>
                
                <div>
                  <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                    Precio de Costo
                  </label>
                  <div className="relative">
                    <span className={`absolute left-3 top-1/2 transform -translate-y-1/2 font-medium ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>S/</span>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      value={state.formData.cost_price || ''}
                      onChange={(e) => setState(prev => ({ 
                        ...prev, 
                        formData: { ...prev.formData, cost_price: parseFloat(e.target.value) || 0 }
                      }))}
                      placeholder="0.00"
                      className={`h-12 pl-12 ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                      Stock Mínimo
                    </label>
                    <Input
                      type="number"
                      min="0"
                      value={state.formData.min_stock || ''}
                      onChange={(e) => setState(prev => ({ 
                        ...prev, 
                        formData: { ...prev.formData, min_stock: parseInt(e.target.value) || 0 }
                      }))}
                      placeholder="0"
                      className={`h-12 ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                    />
                  </div>
                  
                  <div>
                    <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                      Stock Máximo
                    </label>
                    <Input
                      type="number"
                      min="0"
                      value={state.formData.max_stock || ''}
                      onChange={(e) => setState(prev => ({ 
                        ...prev, 
                        formData: { ...prev.formData, max_stock: parseInt(e.target.value) || 0 }
                      }))}
                      placeholder="0"
                      className={`h-12 ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                    />
                  </div>
                </div>
                
                <div className={`flex items-center gap-3 p-4 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-slate-50'}`}>
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={state.formData.is_active !== false}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, is_active: e.target.checked }
                    }))}
                    className="w-5 h-5 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
                  />
                  <label htmlFor="is_active" className={`text-sm font-semibold ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                    Producto activo (disponible para venta)
                  </label>
                </div>
              </div>
            </div>
            
            <div className={`flex justify-end gap-4 mt-8 pt-6 border-t ${isDarkMode ? 'border-gray-600' : 'border-slate-200'}`}>
              <Button 
                variant="outline" 
                onClick={() => setState(prev => ({ ...prev, isDialogOpen: false, error: null }))}
                className={`px-6 py-2.5 ${isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}
              >
                Cancelar
              </Button>
              <Button 
                onClick={state.selectedProduct ? handleUpdateProduct : handleCreateProduct}
                disabled={state.loading}
                className="px-8 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold min-w-[120px]"
              >
                {state.loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  state.selectedProduct ? 'Actualizar' : 'Crear Producto'
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Category Dialog */}
        <Dialog open={state.isCategoryDialogOpen} onOpenChange={(open) => setState(prev => ({ ...prev, isCategoryDialogOpen: open, error: null }))}>
          <DialogContent className={`max-w-2xl ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'}`}>
            <div className="pb-6">
              <DialogHeader>
                <DialogTitle>
                  <span className={isDarkMode ? 'text-white' : 'text-gray-900'}>
                    Crear Nueva Categoría
                  </span>
                </DialogTitle>
              </DialogHeader>
            </div>
            
            {state.error && (
              <Alert variant="destructive" className="mb-6">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="font-medium">{state.error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                  Nombre de la Categoría *
                </label>
                <Input
                  value={state.categoryFormData.name}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    categoryFormData: { ...prev.categoryFormData, name: e.target.value },
                    error: null
                  }))}
                  placeholder="Ingresa el nombre de la categoría"
                  className={`h-12 ${!state.categoryFormData.name?.trim() ? 'border-red-300 focus:border-red-400' : isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                />
              </div>
              
              <div>
                <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                  Descripción
                </label>
                <textarea
                  value={state.categoryFormData.description}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    categoryFormData: { ...prev.categoryFormData, description: e.target.value }
                  }))}
                  placeholder="Descripción de la categoría"
                  rows={4}
                  className={`w-full p-3 border rounded-lg focus:ring-indigo-400 resize-none ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white placeholder-gray-400' : 'border-slate-300 focus:border-indigo-400'}`}
                />
              </div>
            </div>
            
            <div className={`flex justify-end gap-4 mt-6 pt-4 border-t ${isDarkMode ? 'border-gray-600' : 'border-slate-200'}`}>
              <Button 
                variant="outline" 
                onClick={() => setState(prev => ({ ...prev, isCategoryDialogOpen: false }))}
                className={`px-6 py-2.5 ${isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}
              >
                Cancelar
              </Button>
              <Button 
                onClick={handleCreateCategory}
                disabled={state.loading}
                className="px-8 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold min-w-[120px]"
              >
                {state.loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  'Crear Categoría'
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Supplier Dialog */}
        <Dialog open={state.isSupplierDialogOpen} onOpenChange={(open) => setState(prev => ({ ...prev, isSupplierDialogOpen: open, error: null }))}>
          <DialogContent className={`max-w-2xl ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'}`}>
            <div className="pb-6">
              <DialogHeader>
                <DialogTitle>
                  <span className={isDarkMode ? 'text-white' : 'text-gray-900'}>
                    Crear Nuevo Proveedor
                  </span>
                </DialogTitle>
              </DialogHeader>
            </div>
            
            {state.error && (
              <Alert variant="destructive" className="mb-6">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="font-medium">{state.error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                  Nombre del Proveedor *
                </label>
                <Input
                  value={state.supplierFormData.name}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    supplierFormData: { ...prev.supplierFormData, name: e.target.value },
                    error: null
                  }))}
                  placeholder="Ingresa el nombre del proveedor"
                  className={`h-12 ${!state.supplierFormData.name?.trim() ? 'border-red-300 focus:border-red-400' : isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                />
              </div>
              
              <div>
                <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                  Persona de Contacto
                </label>
                <Input
                  value={state.supplierFormData.contact_name}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    supplierFormData: { ...prev.supplierFormData, contact_name: e.target.value }
                  }))}
                  placeholder="Nombre del contacto"
                  className={`h-12 ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                />
              </div>
              
              <div>
                <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                  Email
                </label>
                <Input
                  value={state.supplierFormData.email}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    supplierFormData: { ...prev.supplierFormData, email: e.target.value }
                  }))}
                  placeholder="Email de contacto"
                  className={`h-12 ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                />
              </div>
              
              <div>
                <label className={`block text-sm font-semibold mb-2 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                  Teléfono
                </label>
                <Input
                  value={state.supplierFormData.phone}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    supplierFormData: { ...prev.supplierFormData, phone: e.target.value }
                  }))}
                  placeholder="Teléfono de contacto"
                  className={`h-12 ${isDarkMode ? 'border-gray-600 focus:border-indigo-400 bg-gray-700 text-white' : 'border-slate-300 focus:border-indigo-400'}`}
                />
              </div>
            </div>
            
            <div className={`flex justify-end gap-4 mt-6 pt-4 border-t ${isDarkMode ? 'border-gray-600' : 'border-slate-200'}`}>
              <Button 
                variant="outline" 
                onClick={() => setState(prev => ({ ...prev, isSupplierDialogOpen: false }))}
                className={`px-6 py-2.5 ${isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}
              >
                Cancelar
              </Button>
              <Button 
                onClick={handleCreateSupplier}
                disabled={state.loading}
                className="px-8 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold min-w-[120px]"
              >
                {state.loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  'Crear Proveedor'
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default ProductsPage;