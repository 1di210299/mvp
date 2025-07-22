import React, { useState, useEffect } from 'react';
import { Product, Inventory } from '../types';
import { inventoryService } from '../services/api';
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '../components/ui';
import {
  Package,
  Search,
  Filter,
  Download,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  Eye,
  Edit,
  BarChart3,
  Activity,
  DollarSign,
  Warehouse,
  Settings,
  Plus,
  ArrowUpDown,
  Menu,
  Layers,
  X,
  Save
} from '../components/ui/icons';
import { useTheme } from '../contexts/ThemeContext';
import './InventoryPage.css';

const InventoryPage: React.FC = () => {
  const { actualTheme } = useTheme();
  const isDarkMode = actualTheme === 'dark';
  const [products, setProducts] = useState<Product[]>([]);
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<Product>>({
    name: '',
    sku: '',
    description: '',
    unit_price: 0,
    cost_price: 0,
    min_stock: 0,
    max_stock: 100,
    unit: 'unidad',
    is_active: true
  });
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    loadInventoryData();
  }, []);

  const loadInventoryData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const productsResponse = await inventoryService.getProducts();
      const productsData = productsResponse.results || productsResponse;
      setProducts(productsData);
      
      try {
        const inventoryResponse = await inventoryService.getInventoryItems();
        const inventoryData = inventoryResponse.results || inventoryResponse;
        setInventory(inventoryData);
      } catch (invErr) {
        console.warn('Error loading inventory items:', invErr);
        setInventory([]);
      }
      
    } catch (err) {
      console.error('Error loading inventory data:', err);
      setError('Error al cargar datos del inventario. Verificar conexión con API.');
      setProducts([]);
      setInventory([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProduct = async () => {
    try {
      setFormLoading(true);
      setError('');

      // Validación básica
      if (!formData.name?.trim() || !formData.sku?.trim()) {
        setError('El nombre y SKU son campos obligatorios');
        return;
      }

      // Crear el producto
      const newProduct = await inventoryService.createProduct(formData);
      
      // Actualizar la lista de productos
      setProducts(prev => [...prev, newProduct]);
      
      // Limpiar el formulario y cerrar el diálogo
      setFormData({
        name: '',
        sku: '',
        description: '',
        unit_price: 0,
        cost_price: 0,
        min_stock: 0,
        max_stock: 100,
        unit: 'unidad',
        is_active: true
      });
      setIsCreateDialogOpen(false);
      
      // Mostrar mensaje de éxito (opcional)
      console.log('Producto creado exitosamente:', newProduct);
      
    } catch (err) {
      console.error('Error creating product:', err);
      setError('Error al crear el producto. Verifique los datos e intente nuevamente.');
    } finally {
      setFormLoading(false);
    }
  };

  const handleNavigateToProducts = () => {
    // Navegar a la página de productos para una gestión más completa
    window.location.href = '/products';
  };

  const getInventoryForProduct = (productId: number) => {
    return inventory.find(inv => {
      const invProductId = typeof inv.product === 'number' ? inv.product : inv.product?.id;
      return invProductId === productId;
    });
  };

  const getStockStatus = (product: Product) => {
    const currentStock = product.current_stock || 0;
    const minStock = typeof product.min_stock === 'string' ? parseFloat(product.min_stock) : product.min_stock;
    const maxStock = typeof product.max_stock === 'string' ? parseFloat(product.max_stock) : product.max_stock;
    
    if (currentStock <= 0) return { 
      status: 'out-of-stock', 
      label: 'Sin Stock', 
      color: isDarkMode ? 'bg-red-900/20 text-red-300 border-red-800' : 'bg-red-100 text-red-800 border-red-200', 
      severity: 'high' 
    };
    if (currentStock <= minStock) return { 
      status: 'low-stock', 
      label: 'Stock Bajo', 
      color: isDarkMode ? 'bg-orange-900/20 text-orange-300 border-orange-800' : 'bg-orange-100 text-orange-800 border-orange-200', 
      severity: 'medium' 
    };
    if (currentStock >= maxStock) return { 
      status: 'high-stock', 
      label: 'Stock Alto', 
      color: isDarkMode ? 'bg-blue-900/20 text-blue-300 border-blue-800' : 'bg-blue-100 text-blue-800 border-blue-200', 
      severity: 'low' 
    };
    return { 
      status: 'normal', 
      label: 'Normal', 
      color: isDarkMode ? 'bg-green-900/20 text-green-300 border-green-800' : 'bg-green-100 text-green-800 border-green-200', 
      severity: 'none' 
    };
  };

  const getCategories = () => {
    const categoryNames = products.map(p => p.category_name).filter(Boolean) as string[];
    const categories = Array.from(new Set(categoryNames));
    console.log('Total productos:', products.length); // Debug
    console.log('Productos con categorías:', categoryNames.length); // Debug
    console.log('Categorías disponibles:', categories); // Debug
    return categories;
  };

  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.sku.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = filterCategory === 'all' || product.category_name === filterCategory;
    const stockStatus = getStockStatus(product);
    const matchesStatus = filterStatus === 'all' || stockStatus.status === filterStatus;

    return matchesSearch && matchesCategory && matchesStatus;
  });

  // Debug: mostrar información de filtrado
  useEffect(() => {
    console.log('Filtros actuales:', { searchTerm, filterCategory, filterStatus, sortBy });
    console.log('Productos filtrados:', filteredProducts.length, 'de', products.length);
  }, [searchTerm, filterCategory, filterStatus, sortBy, filteredProducts.length, products.length]);  const sortedProducts = [...filteredProducts].sort((a, b) => {
    let aValue, bValue;
    
    switch (sortBy) {
      case 'name':
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
        break;
      case 'stock':
        aValue = a.current_stock || 0;
        bValue = b.current_stock || 0;
        break;
      case 'value':
        aValue = (a.current_stock || 0) * (typeof a.cost_price === 'string' ? parseFloat(a.cost_price) : a.cost_price || 0);
        bValue = (b.current_stock || 0) * (typeof b.cost_price === 'string' ? parseFloat(b.cost_price) : b.cost_price || 0);
        break;
      default:
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
    }
    
    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const getStockPercentage = (product: Product) => {
    const currentStock = product.current_stock || 0;
    const maxStock = typeof product.max_stock === 'string' ? parseFloat(product.max_stock) : product.max_stock || 100;
    return Math.min((currentStock / maxStock) * 100, 100);
  };

  const getTotalValue = () => {
    return products.reduce((total, p) => {
      const currentStock = p.current_stock || 0;
      const costPrice = typeof p.cost_price === 'string' ? parseFloat(p.cost_price) : p.cost_price || 0;
      return total + (currentStock * costPrice);
    }, 0);
  };

  const getStockAlerts = () => {
    return products.filter(p => {
      const currentStock = p.current_stock || 0;
      const minStock = typeof p.min_stock === 'string' ? parseFloat(p.min_stock) : p.min_stock || 0;
      return currentStock <= minStock;
    }).length;
  };

  const getOutOfStockCount = () => {
    return products.filter(p => (p.current_stock || 0) <= 0).length;
  };

  if (loading) {
    return (
      <div className={`min-h-screen ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'} flex items-center justify-center`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className={`font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Cargando inventario...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`inventory-page min-h-screen ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <div className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-sm border-b`}>
        <div className="w-full px-2 sm:px-4 lg:px-6">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'} flex items-center gap-3`}>
                <div className={`p-2 ${isDarkMode ? 'bg-indigo-900/50' : 'bg-indigo-100'} rounded-lg`}>
                  <Package className={`h-6 w-6 ${isDarkMode ? 'text-indigo-400' : 'text-indigo-600'}`} />
                </div>
                Gestión de Inventario
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={loadInventoryData}
                disabled={loading}
                className={`flex items-center gap-2 ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200' : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-700'} z-10`}
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Actualizar
              </Button>
              
              <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button 
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg border-0 font-medium z-10 min-w-[140px]"
                  >
                    <Plus className="h-4 w-4" />
                    Nuevo Producto
                  </Button>
                </DialogTrigger>
                <DialogContent className={`sm:max-w-[500px] ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'}`}>
                  <DialogHeader>
                    <DialogTitle>
                      <div className={`flex items-center gap-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                        <Package className="h-5 w-5" />
                        Crear Nuevo Producto
                      </div>
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>Nombre *</label>
                        <Input
                          placeholder="Nombre del producto"
                          value={formData.name || ''}
                          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                          className={`${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''} ${!formData.name?.trim() ? 'border-red-300' : ''}`}
                        />
                      </div>
                      <div>
                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>SKU *</label>
                        <Input
                          placeholder="Código único"
                          value={formData.sku || ''}
                          onChange={(e) => setFormData(prev => ({ ...prev, sku: e.target.value }))}
                          className={`${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''} ${!formData.sku?.trim() ? 'border-red-300' : ''}`}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>Descripción</label>
                      <textarea
                        className={`w-full px-3 py-2 border rounded-md resize-none ${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'border-gray-300'}`}
                        rows={3}
                        placeholder="Descripción del producto"
                        value={formData.description || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>Precio de Venta (S/)</label>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="0.00"
                          value={formData.unit_price || ''}
                          onChange={(e) => setFormData(prev => ({ ...prev, unit_price: parseFloat(e.target.value) || 0 }))}
                          className={isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''}
                        />
                      </div>
                      <div>
                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>Precio de Costo (S/)</label>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="0.00"
                          value={formData.cost_price || ''}
                          onChange={(e) => setFormData(prev => ({ ...prev, cost_price: parseFloat(e.target.value) || 0 }))}
                          className={isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''}
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>Stock Mínimo</label>
                        <Input
                          type="number"
                          min="0"
                          placeholder="0"
                          value={formData.min_stock || ''}
                          onChange={(e) => setFormData(prev => ({ ...prev, min_stock: parseInt(e.target.value) || 0 }))}
                          className={isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''}
                        />
                      </div>
                      <div>
                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>Stock Máximo</label>
                        <Input
                          type="number"
                          min="0"
                          placeholder="100"
                          value={formData.max_stock || ''}
                          onChange={(e) => setFormData(prev => ({ ...prev, max_stock: parseInt(e.target.value) || 100 }))}
                          className={isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''}
                        />
                      </div>
                      <div>
                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>Unidad</label>
                        <Input
                          placeholder="unidad"
                          value={formData.unit || ''}
                          onChange={(e) => setFormData(prev => ({ ...prev, unit: e.target.value }))}
                          className={isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''}
                        />
                      </div>
                    </div>

                    {error && (
                      <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                      </Alert>
                    )}
                    
                    <div className="flex justify-between pt-4">
                      <Button
                        variant="outline"
                        onClick={handleNavigateToProducts}
                        className={`flex items-center gap-2 ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200' : ''}`}
                      >
                        <Settings className="h-4 w-4" />
                        Gestión Avanzada
                      </Button>
                      
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          onClick={() => setIsCreateDialogOpen(false)}
                          className={isDarkMode ? 'bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200' : ''}
                        >
                          Cancelar
                        </Button>
                        <Button
                          onClick={handleCreateProduct}
                          disabled={formLoading || !formData.name?.trim() || !formData.sku?.trim()}
                          className="flex items-center gap-2"
                        >
                          {formLoading ? (
                            <RefreshCw className="h-4 w-4 animate-spin" />
                          ) : (
                            <Save className="h-4 w-4" />
                          )}
                          {formLoading ? 'Creando...' : 'Crear Producto'}
                        </Button>
                      </div>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full px-3 sm:px-5 lg:px-7 py-5">
        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <Card className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-indigo-100 text-sm font-medium">Total Productos</p>
                  <p className="text-3xl font-bold">{products.length}</p>
                </div>
                <div className="p-3 bg-white/20 rounded-full">
                  <Package className="h-8 w-8" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-r from-green-500 to-emerald-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm font-medium">Valor Total</p>
                  <p className="text-3xl font-bold">S/ {getTotalValue().toLocaleString()}</p>
                </div>
                <div className="p-3 bg-white/20 rounded-full">
                  <DollarSign className="h-8 w-8" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-r from-orange-500 to-red-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100 text-sm font-medium">Stock Bajo</p>
                  <p className="text-3xl font-bold">{getStockAlerts()}</p>
                </div>
                <div className="p-3 bg-white/20 rounded-full">
                  <AlertTriangle className="h-8 w-8" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-r from-red-500 to-pink-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-red-100 text-sm font-medium">Sin Stock</p>
                  <p className="text-3xl font-bold">{getOutOfStockCount()}</p>
                </div>
                <div className="p-3 bg-white/20 rounded-full">
                  <Activity className="h-8 w-8" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Controls */}
        <Card className={isDarkMode ? 'bg-gray-800 border-gray-700' : ''}>
          <CardContent className="p-6">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-400'}`} />
                <Input
                  placeholder="Buscar productos por nombre o SKU..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className={`pl-10 ${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''}`}
                />
              </div>

              {/* Filters */}
              <div className="flex gap-4 relative">
                <div className="relative">
                  <select 
                    value={filterCategory} 
                    onChange={(e) => {
                      console.log('Cambiando categoría a:', e.target.value);
                      setFilterCategory(e.target.value);
                    }}
                    className={`w-48 h-12 px-4 py-3 rounded-xl border-2 text-sm font-medium appearance-none cursor-pointer transition-all duration-200 ${
                      isDarkMode 
                        ? 'bg-gray-700 border-gray-600 text-white hover:border-indigo-400 focus:border-indigo-400 focus:ring-indigo-500/20' 
                        : 'bg-white border-slate-200 text-slate-700 hover:border-indigo-300 focus:border-indigo-400 focus:ring-indigo-100'
                    } focus:outline-none focus:ring-4`}
                    style={{
                      backgroundImage: isDarkMode 
                        ? `url("data:image/svg+xml;charset=US-ASCII,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 4 5'><path fill='%23d1d5db' d='m2 0-2 2h4zm0 5 2-2h-4z'/></svg>")` 
                        : `url("data:image/svg+xml;charset=US-ASCII,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 4 5'><path fill='%23666' d='m2 0-2 2h4zm0 5 2-2h-4z'/></svg>")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 12px center',
                      backgroundSize: '12px'
                    }}
                  >
                    <option value="all">Todas las categorías</option>
                    {getCategories().map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>

                <div className="relative">
                  <select 
                    value={filterStatus} 
                    onChange={(e) => {
                      console.log('Cambiando estado a:', e.target.value);
                      setFilterStatus(e.target.value);
                    }}
                    className={`w-40 h-12 px-4 py-3 rounded-xl border-2 text-sm font-medium appearance-none cursor-pointer transition-all duration-200 ${
                      isDarkMode 
                        ? 'bg-gray-700 border-gray-600 text-white hover:border-indigo-400 focus:border-indigo-400 focus:ring-indigo-500/20' 
                        : 'bg-white border-slate-200 text-slate-700 hover:border-indigo-300 focus:border-indigo-400 focus:ring-indigo-100'
                    } focus:outline-none focus:ring-4`}
                    style={{
                      backgroundImage: isDarkMode 
                        ? `url("data:image/svg+xml;charset=US-ASCII,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 4 5'><path fill='%23d1d5db' d='m2 0-2 2h4zm0 5 2-2h-4z'/></svg>")` 
                        : `url("data:image/svg+xml;charset=US-ASCII,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 4 5'><path fill='%23666' d='m2 0-2 2h4zm0 5 2-2h-4z'/></svg>")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 12px center',
                      backgroundSize: '12px'
                    }}
                  >
                    <option value="all">Todos</option>
                    <option value="normal">Normal</option>
                    <option value="low-stock">Stock Bajo</option>
                    <option value="out-of-stock">Sin Stock</option>
                    <option value="high-stock">Stock Alto</option>
                  </select>
                </div>

                <div className="relative">
                  <select 
                    value={sortBy} 
                    onChange={(e) => {
                      console.log('Cambiando orden a:', e.target.value);
                      setSortBy(e.target.value);
                    }}
                    className={`w-40 h-12 px-4 py-3 rounded-xl border-2 text-sm font-medium appearance-none cursor-pointer transition-all duration-200 ${
                      isDarkMode 
                        ? 'bg-gray-700 border-gray-600 text-white hover:border-indigo-400 focus:border-indigo-400 focus:ring-indigo-500/20' 
                        : 'bg-white border-slate-200 text-slate-700 hover:border-indigo-300 focus:border-indigo-400 focus:ring-indigo-100'
                    } focus:outline-none focus:ring-4`}
                    style={{
                      backgroundImage: isDarkMode 
                        ? `url("data:image/svg+xml;charset=US-ASCII,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 4 5'><path fill='%23d1d5db' d='m2 0-2 2h4zm0 5 2-2h-4z'/></svg>")` 
                        : `url("data:image/svg+xml;charset=US-ASCII,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 4 5'><path fill='%23666' d='m2 0-2 2h4zm0 5 2-2h-4z'/></svg>")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 12px center',
                      backgroundSize: '12px'
                    }}
                  >
                    <option value="name">Nombre</option>
                    <option value="stock">Stock</option>
                    <option value="value">Valor</option>
                  </select>
                </div>

                <Button
                  variant="outline"
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className={`flex items-center gap-2 ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200' : ''}`}
                >
                  <ArrowUpDown className="h-4 w-4" />
                  {sortOrder === 'asc' ? 'Asc' : 'Desc'}
                </Button>
              </div>

              {/* View Toggle */}
              <div className={`flex border rounded-lg overflow-hidden ${isDarkMode ? 'border-gray-600' : ''}`}>
                <Button
                  variant={viewMode === 'grid' ? 'primary' : 'ghost'}
                  onClick={() => setViewMode('grid')}
                  className={`rounded-none ${viewMode !== 'grid' && isDarkMode ? 'text-gray-300 hover:bg-gray-700' : ''}`}
                >
                  <BarChart3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'table' ? 'primary' : 'ghost'}
                  onClick={() => setViewMode('table')}
                  className={`rounded-none ${viewMode !== 'table' && isDarkMode ? 'text-gray-300 hover:bg-gray-700' : ''}`}
                >
                  <Menu className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Products Display */}
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-5">
            {sortedProducts.map(product => {
              const stockStatus = getStockStatus(product);
              const currentStock = product.current_stock || 0;
              const costPrice = typeof product.cost_price === 'string' ? parseFloat(product.cost_price) : product.cost_price || 0;
              const stockValue = currentStock * costPrice;
              const stockPercentage = getStockPercentage(product);
              const inv = getInventoryForProduct(product.id);

              return (
                <Card key={product.id} className={`hover:shadow-lg transition-shadow duration-200 ${isDarkMode ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className={`text-lg font-semibold truncate ${isDarkMode ? 'text-white' : ''}`}>{product.name}</CardTitle>
                        <p className={`text-sm mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>{product.sku}</p>
                      </div>
                      <Badge className={`${stockStatus.color} font-medium`}>
                        {stockStatus.label}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Stock Progress */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : ''}`}>Stock Actual</span>
                          <span className={`text-lg font-bold ${isDarkMode ? 'text-white' : ''}`}>{currentStock}</span>
                        </div>
                        <div className={`w-full rounded-full h-2 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
                          <div 
                            className={`h-2 rounded-full transition-all duration-300 ${
                              stockStatus.severity === 'high' ? 'bg-red-500' :
                              stockStatus.severity === 'medium' ? 'bg-orange-500' :
                              'bg-green-500'
                            }`}
                            style={{ width: `${stockPercentage}%` }}
                          />
                        </div>
                        <div className={`flex justify-between text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                          <span>Mín: {product.min_stock}</span>
                          <span>Máx: {product.max_stock}</span>
                        </div>
                      </div>

                      {/* Product Details */}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>Categoría</p>
                          <p className={`font-medium ${isDarkMode ? 'text-gray-200' : ''}`}>{product.category_name || 'Sin categoría'}</p>
                        </div>
                        <div>
                          <p className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>Valor Stock</p>
                          <p className={`font-medium ${isDarkMode ? 'text-gray-200' : ''}`}>S/ {stockValue.toFixed(2)}</p>
                        </div>
                      </div>

                      {/* Description */}
                      {product.description && (
                        <p className={`text-sm line-clamp-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{product.description}</p>
                      )}

                      {/* Location */}
                      <div className={`flex items-center gap-2 text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        <Warehouse className="h-4 w-4" />
                        <span>{inv?.location?.name || 'Sin ubicación'}</span>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 pt-2">
                        <Button variant="outline" size="sm" className={`flex-1 ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200' : ''}`}>
                          <Eye className="h-4 w-4 mr-2" />
                          Ver
                        </Button>
                        <Button variant="outline" size="sm" className={`flex-1 ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200' : ''}`}>
                          <Edit className="h-4 w-4 mr-2" />
                          Editar
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card className={isDarkMode ? 'bg-gray-800 border-gray-700' : ''}>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className={`border-b ${isDarkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50'}`}>
                    <tr>
                      <th className={`text-left p-4 font-semibold ${isDarkMode ? 'text-gray-200' : ''}`}>Producto</th>
                      <th className={`text-left p-4 font-semibold ${isDarkMode ? 'text-gray-200' : ''}`}>SKU</th>
                      <th className={`text-left p-4 font-semibold ${isDarkMode ? 'text-gray-200' : ''}`}>Categoría</th>
                      <th className={`text-center p-4 font-semibold ${isDarkMode ? 'text-gray-200' : ''}`}>Stock</th>
                      <th className={`text-left p-4 font-semibold ${isDarkMode ? 'text-gray-200' : ''}`}>Estado</th>
                      <th className={`text-right p-4 font-semibold ${isDarkMode ? 'text-gray-200' : ''}`}>Valor</th>
                      <th className={`text-left p-4 font-semibold ${isDarkMode ? 'text-gray-200' : ''}`}>Ubicación</th>
                      <th className={`text-center p-4 font-semibold ${isDarkMode ? 'text-gray-200' : ''}`}>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedProducts.map(product => {
                      const stockStatus = getStockStatus(product);
                      const currentStock = product.current_stock || 0;
                      const costPrice = typeof product.cost_price === 'string' ? parseFloat(product.cost_price) : product.cost_price || 0;
                      const stockValue = currentStock * costPrice;
                      const inv = getInventoryForProduct(product.id);

                      return (
                        <tr key={product.id} className={`border-b ${isDarkMode ? 'border-gray-700 hover:bg-gray-700/50' : 'hover:bg-gray-50'}`}>
                          <td className="p-4">
                            <div>
                              <div className={`font-medium ${isDarkMode ? 'text-white' : ''}`}>{product.name}</div>
                              {product.description && (
                                <div className={`text-sm truncate ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>{product.description}</div>
                              )}
                            </div>
                          </td>
                          <td className={`p-4 font-mono text-sm ${isDarkMode ? 'text-gray-300' : ''}`}>{product.sku}</td>
                          <td className={`p-4 ${isDarkMode ? 'text-gray-300' : ''}`}>{product.category_name || 'Sin categoría'}</td>
                          <td className="p-4 text-center">
                            <div className="flex flex-col items-center">
                              <span className={`font-bold text-lg ${isDarkMode ? 'text-white' : ''}`}>{currentStock}</span>
                              <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                                {product.min_stock} - {product.max_stock}
                              </span>
                            </div>
                          </td>
                          <td className="p-4">
                            <Badge className={`${stockStatus.color} font-medium`}>
                              {stockStatus.label}
                            </Badge>
                          </td>
                          <td className={`p-4 text-right font-mono ${isDarkMode ? 'text-gray-300' : ''}`}>S/ {stockValue.toFixed(2)}</td>
                          <td className={`p-4 ${isDarkMode ? 'text-gray-300' : ''}`}>{inv?.location?.name || 'Sin ubicación'}</td>
                          <td className="p-4">
                            <div className="flex gap-2 justify-center">
                              <Button variant="outline" size="sm" className={isDarkMode ? 'bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200' : ''}>
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button variant="outline" size="sm" className={isDarkMode ? 'bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200' : ''}>
                                <Edit className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* No Results */}
        {sortedProducts.length === 0 && !loading && (
          <Card className={isDarkMode ? 'bg-gray-800 border-gray-700' : ''}>
            <CardContent className="p-12 text-center">
              <Package className={`h-16 w-16 mx-auto mb-4 ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`} />
              <h3 className={`text-lg font-medium mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>No se encontraron productos</h3>
              <p className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>
                {searchTerm ? 'Intenta ajustar tus filtros de búsqueda' : 'No hay productos en el inventario'}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default InventoryPage;
