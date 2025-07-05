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
  FolderOpen
} from '../components/ui/icons';
import { inventoryService } from '../services/api';
import { Product, Category, ApiResponse } from '../types';

interface ProductsPageState {
  products: Product[];
  categories: Category[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  selectedCategory: string;
  sortField: string;
  sortDirection: 'asc' | 'desc';
  isDialogOpen: boolean;
  isUploadDialogOpen: boolean;
  selectedProduct: Product | null;
  formData: Partial<Product>;
}

const ProductsPage: React.FC = () => {
  const [state, setState] = useState<ProductsPageState>({
    products: [],
    categories: [],
    loading: true,
    error: null,
    searchTerm: '',
    selectedCategory: 'all',
    sortField: 'name',
    sortDirection: 'asc',
    isDialogOpen: false,
    isUploadDialogOpen: false,
    selectedProduct: null,
    formData: {}
  });

  const fetchProducts = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      const response: ApiResponse<Product> = await inventoryService.getProducts();
      setState(prev => ({ 
        ...prev, 
        products: response.results || [],
        loading: false 
      }));
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
      // Simulated category data - replace with actual API call
      const mockCategories: Category[] = [
        { id: 1, name: 'Electrónicos', description: 'Productos electrónicos', is_active: true },
        { id: 2, name: 'Ropa', description: 'Prendas de vestir', is_active: true },
        { id: 3, name: 'Hogar', description: 'Artículos para el hogar', is_active: true },
        { id: 4, name: 'Deportes', description: 'Artículos deportivos', is_active: true },
      ];
      setState(prev => ({ ...prev, categories: mockCategories }));
    } catch (err) {
      console.error('Error loading categories:', err);
    }
  };

  const handleCreateProduct = async () => {
    try {
      await inventoryService.createProduct(state.formData);
      await fetchProducts();
      setState(prev => ({ 
        ...prev, 
        isDialogOpen: false, 
        formData: {},
        selectedProduct: null 
      }));
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al crear producto' 
      }));
    }
  };

  const handleUpdateProduct = async () => {
    if (!state.selectedProduct) return;
    
    try {
      await inventoryService.updateProduct(state.selectedProduct.id, state.formData);
      await fetchProducts();
      setState(prev => ({ 
        ...prev, 
        isDialogOpen: false, 
        formData: {},
        selectedProduct: null 
      }));
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al actualizar producto' 
      }));
    }
  };

  const handleDeleteProduct = async (id: number) => {
    try {
      await inventoryService.deleteProduct(id);
      await fetchProducts();
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al eliminar producto' 
      }));
    }
  };

  const handleCSVUpload = async (csvData: any[]) => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      
      // Process CSV data and create products
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
    const matchesSearch = product.name.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
                         product.sku.toLowerCase().includes(state.searchTerm.toLowerCase());
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

  const getStockStatus = (product: Product) => {
    // This would typically come from inventory data
    const currentStock = Math.floor(Math.random() * 100); // Mock data
    const minStock = typeof product.min_stock === 'string' ? parseFloat(product.min_stock) : product.min_stock;
    const maxStock = typeof product.max_stock === 'string' ? parseFloat(product.max_stock) : product.max_stock;
    if (currentStock <= minStock) return { status: 'Bajo', color: 'destructive' };
    if (currentStock >= maxStock) return { status: 'Alto', color: 'warning' };
    return { status: 'Normal', color: 'success' };
  };

  useEffect(() => {
    fetchProducts();
    fetchCategories();
  }, []);

  if (state.loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Productos</h1>
          <p className="text-gray-600">Administra tu catálogo de productos</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => setState(prev => ({ ...prev, isUploadDialogOpen: true }))} 
            className="flex items-center gap-2"
          >
            <FolderOpen className="h-4 w-4" />
            Subir CSV
          </Button>
          <Button onClick={openCreateDialog} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Nuevo Producto
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Package className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Productos</p>
                <p className="text-2xl font-bold text-gray-900">{state.products.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Stock Bajo</p>
                <p className="text-2xl font-bold text-gray-900">
                  {state.products.filter(p => getStockStatus(p).status === 'Bajo').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Productos Activos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {state.products.filter(p => p.is_active).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <DollarSign className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Valor Promedio</p>
                <p className="text-2xl font-bold text-gray-900">
                  S/ {(state.products.reduce((sum, p) => {
                    const price = parseFloat(p.sale_price as string) || parseFloat(p.cost_price as string) || 0;
                    return sum + price;
                  }, 0) / state.products.length || 0).toFixed(0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Buscar productos..."
                  value={state.searchTerm}
                  onChange={(e) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
                  className="pl-10"
                />
              </div>
            </div>
            <Select 
              value={state.selectedCategory} 
              onValueChange={(value) => setState(prev => ({ ...prev, selectedCategory: value }))}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filtrar por categoría" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las categorías</SelectItem>
                {state.categories.map(category => (
                  <SelectItem key={category.id} value={category.id.toString()}>
                    {category.name}
                  </SelectItem>
                ))}
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

      {/* Products Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Productos</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead>SKU</TableHead>
                <TableHead>Categoría</TableHead>
                <TableHead>Precio</TableHead>
                <TableHead>Stock</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedProducts.map((product) => {
                const stockStatus = getStockStatus(product);
                return (
                  <TableRow key={product.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{product.name}</div>
                        <div className="text-sm text-gray-500">{product.description}</div>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono">{product.sku}</TableCell>
                    <TableCell>{product.category_name || 'Sin categoría'}</TableCell>
                    <TableCell>${(parseFloat(product.sale_price as string) || parseFloat(product.cost_price as string) || 0).toFixed(2)}</TableCell>
                    <TableCell>
                      <Badge variant={stockStatus.color as any}>
                        {stockStatus.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={product.is_active ? 'success' : 'secondary'}>
                        {product.is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(product)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteProduct(product.id)}
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
        </CardContent>
      </Card>

      {/* Product Dialog */}
      <Dialog open={state.isDialogOpen} onOpenChange={(open) => setState(prev => ({ ...prev, isDialogOpen: open }))}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {state.selectedProduct ? 'Editar Producto' : 'Nuevo Producto'}
            </DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Nombre</label>
                <Input
                  value={state.formData.name || ''}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, name: e.target.value }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">SKU</label>
                <Input
                  value={state.formData.sku || ''}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, sku: e.target.value }
                  }))}
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
                />
              </div>
              <div>
                <label className="text-sm font-medium">Unidad</label>
                <Input
                  value={state.formData.unit || ''}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, unit: e.target.value }
                  }))}
                />
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Precio Unitario</label>
                <Input
                  type="number"
                  value={state.formData.unit_price || 0}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, unit_price: parseFloat(e.target.value) }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Precio Costo</label>
                <Input
                  type="number"
                  value={state.formData.cost_price || 0}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, cost_price: parseFloat(e.target.value) }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Stock Mínimo</label>
                <Input
                  type="number"
                  value={state.formData.min_stock || 0}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, min_stock: parseInt(e.target.value) }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Stock Máximo</label>
                <Input
                  type="number"
                  value={state.formData.max_stock || 0}
                  onChange={(e) => setState(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, max_stock: parseInt(e.target.value) }
                  }))}
                />
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Button 
              variant="outline" 
              onClick={() => setState(prev => ({ ...prev, isDialogOpen: false }))}
            >
              Cancelar
            </Button>
            <Button onClick={state.selectedProduct ? handleUpdateProduct : handleCreateProduct}>
              {state.selectedProduct ? 'Actualizar' : 'Crear'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* CSV Upload Dialog */}
      <Dialog open={state.isUploadDialogOpen} onOpenChange={(open) => setState(prev => ({ ...prev, isUploadDialogOpen: open }))}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Subir Productos desde CSV/Excel</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              <p>Sube un archivo CSV o Excel con los siguientes campos:</p>
              <ul className="mt-2 list-disc list-inside space-y-1">
                <li><strong>nombre</strong> o <strong>name</strong> - Nombre del producto (requerido)</li>
                <li><strong>sku</strong> o <strong>codigo</strong> - Código del producto (requerido)</li>
                <li><strong>descripcion</strong> o <strong>description</strong> - Descripción del producto</li>
                <li><strong>precio</strong> o <strong>price</strong> - Precio de venta</li>
                <li><strong>costo</strong> o <strong>cost</strong> - Precio de costo</li>
                <li><strong>stock_minimo</strong> o <strong>min_stock</strong> - Stock mínimo</li>
                <li><strong>stock_maximo</strong> o <strong>max_stock</strong> - Stock máximo</li>
                <li><strong>unidad</strong> o <strong>unit</strong> - Unidad de medida</li>
              </ul>
            </div>
            
            <CSVUploader
              onDataLoaded={handleCSVUpload}
              maxFileSize={10}
              downloadTemplate={true}
              templateColumns={[
                { key: 'nombre', label: 'Nombre', type: 'string', required: true },
                { key: 'sku', label: 'SKU', type: 'string', required: true },
                { key: 'descripcion', label: 'Descripción', type: 'string' },
                { key: 'precio', label: 'Precio', type: 'number' },
                { key: 'costo', label: 'Costo', type: 'number' },
                { key: 'stock_minimo', label: 'Stock Mínimo', type: 'number' },
                { key: 'stock_maximo', label: 'Stock Máximo', type: 'number' },
                { key: 'unidad', label: 'Unidad', type: 'string' }
              ]}
            />
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Button 
              variant="outline" 
              onClick={() => setState(prev => ({ ...prev, isUploadDialogOpen: false }))}
            >
              Cancelar
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProductsPage;
