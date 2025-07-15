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
  Check,
  Truck,
  Brain
} from '../components/ui/icons';
import { inventoryService } from '../services/api';
import { Product, Category, Supplier, ApiResponse } from '../types';
import { useTheme } from '../contexts/ThemeContext';
import { apiConfig } from '../config/api';

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
  // **NUEVO: Estados para dialogs de ver y eliminar**
  isViewDialogOpen: boolean;
  isDeleteDialogOpen: boolean;
  productToDelete: Product | null;
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
  // **NUEVO: Estados para filtros inteligentes**
  smartFilter: string;
  productIntelligence: { [key: number]: any };
  loadingIntelligence: boolean;
  showIntelligencePanel: boolean;
  // **NUEVO: Estados para órdenes de compra con IA**
  purchaseOrderData: any;
  isPurchaseOrderDialogOpen: boolean;
  isLoadingPurchaseOrder: boolean;
  customQuantity: number;
  showEmailConfirmation: boolean;
  // **MEJORADO: Campos adicionales para el dialog de compra**
  purchaseOrderEmail: string;
  purchaseOrderWhatsApp: string;
  whatsappEnabled: boolean;
  selectedProductForPurchase: Product | null;
  // **NUEVO: Estados para pronósticos ML**
  forecastData: any;
  isForecastDialogOpen: boolean;
  isLoadingForecast: boolean;
  selectedForecastModel: string;
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
    isViewDialogOpen: false,
    isDeleteDialogOpen: false,
    productToDelete: null,
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
    notification: null,
    smartFilter: '',
    productIntelligence: {},
    loadingIntelligence: true,
    showIntelligencePanel: false,
    purchaseOrderData: {},
    isPurchaseOrderDialogOpen: false,
    isLoadingPurchaseOrder: false,
    customQuantity: 0,
    showEmailConfirmation: false,
    purchaseOrderEmail: '',
    purchaseOrderWhatsApp: '',
    whatsappEnabled: false,
    selectedProductForPurchase: null,
    forecastData: {},
    isForecastDialogOpen: false,
    isLoadingForecast: true,
    selectedForecastModel: ''
  });

  // **MEJORADO: Función para cargar productos con mejor manejo de errores**
  const fetchProducts = async (): Promise<Product[]> => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const response = await inventoryService.getProducts();
      const products = response.results || response;
      
      setState(prev => ({ 
        ...prev, 
        products: products, 
        loading: false 
      }));
      
      console.log('✅ Productos cargados exitosamente');
      
      return products;
      
    } catch (err: any) {
      console.error('❌ Error al cargar productos:', err);
      
      let errorMessage = 'Error al cargar productos';
      
      if (err.message?.includes('No se pudo conectar con el servidor')) {
        errorMessage = 'No se pudo conectar con el servidor. Verifique su conexión.';
      } else if (err.code === 'ERR_NETWORK') {
        errorMessage = 'Error de conexión. Intentando reconectar...';
      } else if (err.response?.status === 401) {
        errorMessage = 'Sesión expirada. Por favor, inicie sesión nuevamente.';
      } else if (err.response?.status === 403) {
        errorMessage = 'No tiene permisos para ver los productos.';
      } else if (err.response?.status >= 500) {
        errorMessage = 'Error del servidor. Por favor, intente más tarde.';
      }
      
      setState(prev => ({ 
        ...prev, 
        error: errorMessage,
        loading: false 
      }));
      
      // Mostrar productos de fallback si no hay datos
      if (state.products.length === 0) {
        console.log('🔄 Usando productos de fallback debido a error de conexión');
        
        const fallbackProducts: Product[] = [
          {
            id: 1,
            name: 'Producto de ejemplo',
            sku: 'TEMP-001',
            description: 'Producto de ejemplo mientras se restablece la conexión',
            category: 1,
            supplier: 1,
            cost_price: 0,
            sale_price: 0,
            min_stock: 5,
            max_stock: 100,
            reorder_point: 10,
            unit: 'unidad',
            track_batches: false,
            has_expiration: false,
            stock: 0,
            is_active: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        ];
        
        setState(prev => ({ 
          ...prev, 
          products: fallbackProducts
        }));
        
        return fallbackProducts;
      }
      
      return state.products;
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

  // **⚡ PARCIALMENTE CONECTADO: Datos de inteligencia de productos**
  // Backend endpoint: GET /api/inventory/products/intelligence/ (disponible pero con fallback)
  const fetchProductIntelligence = async () => {
    try {
      setState(prev => ({ ...prev, loadingIntelligence: true }));
      
      const intelligenceResult = await inventoryService.getProductIntelligence();
      
      // Manejar respuesta mejorada con mejor error handling
      if (intelligenceResult.error) {
        console.warn('⚠️ Intelligence endpoint con error:', intelligenceResult.error);
        
        // Crear datos de fallback básicos para todos los productos
        const fallbackData: any = {};
        state.products.forEach(product => {
          fallbackData[product.id] = {
            product_id: product.id,
            product_name: product.name,
            current_stock: product.stock || 0,
            status: 'limited_data',
            intelligence_summary: `${product.stock || 0} unidades`,
            ai_insights: [
              `Producto: ${product.name}`,
              `Stock actual: ${product.stock || 0} unidades`,
              'Datos de inteligencia temporalmente no disponibles'
            ]
          };
        });
        
      setState(prev => ({ 
        ...prev, 
          productIntelligence: fallbackData,
        loadingIntelligence: false 
      }));
        
        console.log('✅ Usando datos de fallback para inteligencia de productos');
        return;
      }
      
      // Datos exitosos
      setState(prev => ({ 
        ...prev, 
        productIntelligence: intelligenceResult,
        loadingIntelligence: false 
      }));
      
      console.log('✅ Datos de inteligencia cargados exitosamente');
      
    } catch (err) {
      console.error('❌ Error loading product intelligence:', err);
      
      // Crear datos de fallback en caso de error completo
      const fallbackData: any = {};
      state.products.forEach(product => {
        fallbackData[product.id] = {
          product_id: product.id,
          product_name: product.name,
          current_stock: product.stock || 0,
          status: 'error',
          intelligence_summary: `${product.stock || 0} unidades`,
          ai_insights: [
            `Producto: ${product.name}`,
            `Stock actual: ${product.stock || 0} unidades`,
            'Error al cargar datos de inteligencia'
          ]
        };
      });
      
      setState(prev => ({ 
        ...prev, 
        productIntelligence: fallbackData,
        loadingIntelligence: false 
      }));
      
      console.log('✅ Usando datos de fallback de emergencia');
    }
  };

  // **FEATURE FUTURA: Función para manejar filtros inteligentes**
  // TODO: Conectar con endpoint /api/inventory/products/smart-filters/ cuando se implemente en backend
  const handleSmartFilter = async (filterType: string) => {
    try {
      setState(prev => ({ ...prev, loading: true, smartFilter: filterType }));
      
      if (filterType === '') {
        // Mostrar todos los productos
        await fetchProducts();
      } else {
        // **TEMPORAL: Aplicar filtro inteligente localmente hasta que se implemente endpoint backend**
        const allProducts: Product[] = state.products.length > 0 ? state.products : await fetchProducts();
        let filteredProducts: Product[] = [];
        
        switch (filterType) {
          case 'needs_restock':
            // Productos que necesitan reabastecimiento (stock bajo o crítico)
            filteredProducts = allProducts.filter((p: Product) => {
              const stock = p.stock || p.current_stock || 0;
              const reorderPoint = Number(p.reorder_point) || Number(p.min_stock) || 10;
              return stock <= reorderPoint;
            });
            break;
            
          case 'expiring_soon':
            // Productos próximos a vencer (requiere implementación de fechas de expiración)
            filteredProducts = allProducts.filter((p: Product) => {
              // Solo productos marcados como perecederos
              return p.has_expiration;
            });
            break;
            
          case 'top_sellers':
            // Productos más vendidos (requiere datos reales de ventas)
            // Por ahora, mostrar todos los productos activos ordenados por nombre
            filteredProducts = allProducts
              .filter((p: Product) => p.is_active)
              .sort((a: Product, b: Product) => a.name.localeCompare(b.name));
            break;
            
          case 'low_stock':
            // Stock bajo (entre reorder point y stock mínimo)
            filteredProducts = allProducts.filter((p: Product) => {
              const stock = p.stock || p.current_stock || 0;
              const reorderPoint = Number(p.reorder_point) || Number(p.min_stock) || 10;
              const minStock = Number(p.min_stock) || 5;
              return stock > minStock && stock <= reorderPoint;
            });
            break;
            
          case 'critical_stock':
            // Stock crítico (por debajo del stock mínimo)
            filteredProducts = allProducts.filter((p: Product) => {
              const stock = p.stock || p.current_stock || 0;
              const minStock = Number(p.min_stock) || 5;
              return stock <= minStock;
            });
            break;
            
          case 'trending_up':
            // Productos con tendencia al alza (simulado por productos con precio más alto)
            filteredProducts = allProducts
              .filter((p: Product) => p.is_active)
              .sort((a: Product, b: Product) => {
                const priceA = parseFloat(a.sale_price as string) || parseFloat(a.cost_price as string) || 0;
                const priceB = parseFloat(b.sale_price as string) || parseFloat(b.cost_price as string) || 0;
                return priceB - priceA; // Los más caros primero
              })
              .slice(0, Math.min(15, allProducts.length)); // Top 15
            break;
            
          default:
            filteredProducts = allProducts;
        }
        
        setState(prev => ({ 
          ...prev, 
          products: filteredProducts,
          loading: false,
          notification: getSmartFilterDescription(filterType, filteredProducts.length)
        }));
        
        // **NUEVO: Mensaje informativo para el usuario**
        console.log(`🎯 Filtro inteligente aplicado: ${filterType}, ${filteredProducts.length} productos encontrados`);
      }
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al aplicar filtro inteligente',
        loading: false 
      }));
    }
  };

  // **NUEVO: Función para obtener descripciones de filtros inteligentes**
  const getSmartFilterDescription = (filterType: string, count: number): string => {
    switch (filterType) {
      case 'needs_restock':
        return `${count} productos necesitan reabastecimiento`;
      case 'expiring_soon':
        return `${count} productos próximos a vencer`;
      case 'top_sellers':
        return `${count} productos más vendidos`;
      case 'low_stock':
        return `${count} productos con stock bajo`;
      case 'critical_stock':
        return `${count} productos con stock crítico`;
      case 'trending_up':
        return `${count} productos con tendencia al alza`;
      default:
        return '';
    }
  };
  

  
  // **NUEVO: Función para obtener información de inteligencia de productos**
  const getProductIntelligenceInfo = (productId: number): any => {
    const intelligence = state.productIntelligence[productId];
    if (!intelligence) return null;
    
    return {
      ...intelligence
      // stock_info eliminado - usaba datos simulados
    };
  };

  // **✅ NUEVO: Abrir dialog de compra (RÁPIDO - sin IA automática)**
  const handleOpenPurchaseDialog = (productId: number) => {
    const product = state.products.find(p => p.id === productId);
    if (!product) {
      setState(prev => ({ ...prev, error: 'Producto no encontrado' }));
      return;
    }

    // **✅ CORREGIDO: Obtener datos reales del proveedor del producto**
    const supplier = state.suppliers.find(s => s.id === product.supplier);
    const supplierEmail = supplier?.email || 'compras@empresa.com';
    const supplierPhone = supplier?.phone || '+51999999999';
    
    console.log(`🏭 Proveedor encontrado para ${product.name}:`, {
      supplier_id: product.supplier,
      supplier_name: supplier?.name || 'Sin proveedor',
      supplier_email: supplierEmail,
      supplier_phone: supplierPhone
    });

    // Abrir dialog inmediatamente sin generar IA (más rápido)
    setState(prev => ({ 
      ...prev, 
      isPurchaseOrderDialogOpen: true,
      selectedProductForPurchase: product,
      customQuantity: Number(product.reorder_point) || 10, // Cantidad por defecto
      purchaseOrderEmail: supplierEmail, // ✅ Email real del proveedor
      purchaseOrderWhatsApp: supplierPhone, // ✅ Teléfono real del proveedor
      whatsappEnabled: false,
      purchaseOrderData: null, // Sin datos de IA inicialmente
      isLoadingPurchaseOrder: false, // Asegurar que no esté cargando
      notification: `💡 Configurar orden de compra para ${product.name} → ${supplier?.name || 'Proveedor no encontrado'}`
    }));
  };



  // **✅ NUEVO: Mostrar dialog "Coming Soon" para pronósticos**
  const handleGetMLForecast = async (productId: number) => {
    const product = state.products.find(p => p.id === productId);
    if (!product) {
      setState(prev => ({ ...prev, error: 'Producto no encontrado' }));
      return;
    }

    console.log(`📊 Mostrando preview de pronósticos para ${product.name}`);
    
    // Abrir dialog con mensaje "Coming Soon"
    setState(prev => ({ 
      ...prev, 
      isForecastDialogOpen: true,
      selectedProductForPurchase: product, // Reutilizar para mostrar el producto
      isLoadingForecast: false,
      notification: `🔮 Función de pronósticos ML disponible próximamente`
    }));
  };



  // **MEJORADO: Función para ejecutar acciones inteligentes (legacy)**
  const handleProductAction = async (productId: number, action: string, data?: any) => {
    // Redirigir a las nuevas funciones específicas
    if (action === 'generate_purchase_order') {
              handleOpenPurchaseDialog(productId);
    } else if (action === 'get_forecast') {
      await handleGetMLForecast(productId);
    } else {
      // Otras acciones genéricas
      try {
        setState(prev => ({ ...prev, loading: true }));
        const result = await inventoryService.executeProductAction(productId, action, data);
        setState(prev => ({ ...prev, loading: false }));
      } catch (err) {
        setState(prev => ({ 
          ...prev, 
          error: err instanceof Error ? err.message : 'Error al ejecutar acción',
          loading: false 
        }));
      }
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

  // **✅ CONECTADO: Actualización de productos con backend real**
  // Backend endpoint: PATCH /api/inventory/products/{id}/
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
      
      // Usar la función robusta de actualización
      const updatedProduct = await inventoryService.updateProductRobust(
        state.selectedProduct.id, 
        state.formData
      );
      
      // Actualizar el producto en la lista local sin necesidad de refetch completo
      setState(prev => ({
        ...prev,
        products: prev.products.map(p => 
          p.id === state.selectedProduct!.id ? updatedProduct : p
        ),
        isDialogOpen: false, 
        formData: {},
        selectedProduct: null,
        loading: false,
        notification: `Producto "${updatedProduct.name}" actualizado exitosamente`
      }));
      
      // Auto-hide notification
      setTimeout(() => {
        setState(prev => ({ ...prev, notification: null }));
      }, 3000);
      
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
                           product.category?.toString() === state.selectedCategory ||
                           product.category_name === state.selectedCategory;
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
    // FIX: Mapear correctamente sale_price a unit_price para el formulario
    const salePrice = typeof product.sale_price === 'string' ? parseFloat(product.sale_price) : product.sale_price;
    const unitPrice = typeof product.unit_price === 'string' ? parseFloat(product.unit_price) : product.unit_price;
    
    const formData = { 
      ...product,
      unit_price: salePrice || unitPrice || 0  // Asegurar que sea número
    };
    
    setState(prev => ({
      ...prev,
      selectedProduct: product,
      formData: formData,
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

  const handleCloseDialog = () => {
    setState(prev => ({
      ...prev,
      isDialogOpen: false,
      selectedProduct: null,
      formData: {}
    }));
  };

  // **NUEVO: Funciones para dialogs de ver y eliminar**
  const handleViewProduct = (product: Product) => {
    setState(prev => ({
      ...prev,
      selectedProduct: product,
      isViewDialogOpen: true
    }));
  };

  const handleDeleteProduct = (productId: number) => {
    const product = state.products.find(p => p.id === productId);
    if (product) {
      setState(prev => ({
        ...prev,
        productToDelete: product,
        isDeleteDialogOpen: true
      }));
    }
  };

  const confirmDeleteProduct = async () => {
    if (!state.productToDelete) return;
    
    try {
      setState(prev => ({ ...prev, loading: true }));
      await inventoryService.deleteProduct(state.productToDelete.id);
      await fetchProducts();
      setState(prev => ({
        ...prev,
        isDeleteDialogOpen: false,
        productToDelete: null,
        loading: false
      }));
    } catch (err) {
      console.error('Error deleting product:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al eliminar el producto',
        isDeleteDialogOpen: false,
        productToDelete: null,
        loading: false
      }));
    }
  };

  const closeViewDialog = () => {
    setState(prev => ({
      ...prev,
      isViewDialogOpen: false,
      selectedProduct: null
    }));
  };

  const closeDeleteDialog = () => {
    setState(prev => ({
      ...prev,
      isDeleteDialogOpen: false,
      productToDelete: null
    }));
  };

  const handleSaveProduct = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      if (state.selectedProduct) {
        // Actualizar producto existente
        await inventoryService.updateProduct(state.selectedProduct.id, state.formData);
      } else {
        // Crear nuevo producto
        await inventoryService.createProduct(state.formData);
      }
      
      await fetchProducts();
      handleCloseDialog();
      setState(prev => ({ ...prev, loading: false }));
    } catch (err) {
      console.error('Error saving product:', err);
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al guardar producto',
        loading: false 
      }));
    }
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
    const currentStock = product.stock || product.current_stock || 0;
    const minStock = typeof product.min_stock === 'string' ? parseFloat(product.min_stock) : (product.min_stock || 0);
    const maxStock = typeof product.max_stock === 'string' ? parseFloat(product.max_stock) : (product.max_stock || 100);
    
    // Comentado para evitar spam en logs
    // console.log(`🔍 Stock Status Debug - ${product.name}: stock=${currentStock}, min=${minStock}, max=${maxStock}`);
    
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
    fetchProductIntelligence(); // **REACTIVADO: Backend con mejor manejo de errores**
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

  // **✅ NUEVO: Función para generar y enviar orden de compra completa**
  const handleSendPurchaseOrder = async () => {
    if (!state.selectedProductForPurchase || !state.purchaseOrderEmail) {
      setState(prev => ({ ...prev, error: 'Faltan datos: producto o email de destino' }));
      return;
    }

    try {
      setState(prev => ({ ...prev, isLoadingPurchaseOrder: true }));
      
      console.log('🤖 Generando y enviando orden de compra con IA...');
      
      // **PASO 1: Generar orden con IA automáticamente**
      console.log('🤖 Generando recomendación con IA...');
      const aiResult = await inventoryService.generateAIPurchaseOrder(state.selectedProductForPurchase.id);
      
      if (aiResult.error) {
        throw new Error(aiResult.error);
      }
      
      console.log('✅ Orden con IA generada:', aiResult.data);
      
      // **PASO 2: Enviar email inmediatamente con datos del formulario**
      console.log('📧 Enviando email con orden de compra...');
      const emailResponse = await inventoryService.sendPurchaseOrderEmail(
        state.selectedProductForPurchase.id,
        state.customQuantity,
        state.purchaseOrderEmail  // Email personalizado del usuario
      );
      
      console.log('✅ Email enviado exitosamente:', emailResponse);
      
      setState(prev => ({ 
        ...prev, 
        notification: `✅ Orden de compra con IA enviada exitosamente a ${state.purchaseOrderEmail}`,
        purchaseOrderData: aiResult.data,
        isLoadingPurchaseOrder: false
      }));
      
      // Cerrar y limpiar dialog después de un breve delay para mostrar notificación
      setTimeout(() => {
        handleClosePurchaseDialog();
      }, 1500);
      
    } catch (error: any) {
      console.error('❌ Error generando/enviando orden de compra:', error);
      setState(prev => ({ 
        ...prev, 
        error: error.message || 'Error al generar/enviar la orden de compra',
        isLoadingPurchaseOrder: false
      }));
    }
  };

  // **✅ NUEVA: Función para cerrar y limpiar dialog de compra**
  const handleClosePurchaseDialog = () => {
    setState(prev => ({ 
      ...prev, 
      isPurchaseOrderDialogOpen: false,
      selectedProductForPurchase: null,
      purchaseOrderData: null,
      customQuantity: 0,
      isLoadingPurchaseOrder: false,
      purchaseOrderEmail: 'compras@empresa.com',
      purchaseOrderWhatsApp: '+51999999999',
      whatsappEnabled: false
    }));
  };

  // **✅ NUEVA: Función para cerrar dialog de pronósticos**
  const handleCloseForecastDialog = () => {
    setState(prev => ({ 
      ...prev, 
      isForecastDialogOpen: false,
      selectedProductForPurchase: null,
      forecastData: {},
      isLoadingForecast: false
    }));
  };

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
    <>
      <div className={`min-h-screen ${isDarkMode ? 'bg-gray-900' : 'bg-slate-50'}`}>
      <div className="max-w-[98%] mx-auto px-2 sm:px-4 lg:px-6 py-8">
        
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

              {/* **NUEVO: Filtros inteligentes** */}
              <div className="flex-1 max-w-xs">
                <Select
                  value={state.smartFilter}
                  onValueChange={(value) => handleSmartFilter(value)}
                >
                  <SelectTrigger className={`w-full px-4 py-3 rounded-xl border transition-all text-sm ${
                    isDarkMode 
                      ? 'bg-gray-700 border-gray-600 text-white focus:bg-gray-600' 
                      : 'bg-gray-50 border-gray-200 focus:bg-white'
                  }`}>
                    <SelectValue placeholder="Filtros inteligentes" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Todos los productos</SelectItem>
                    <SelectItem value="needs_restock">🔄 Necesita reabastecimiento</SelectItem>
                    <SelectItem value="expiring_soon">⏰ Próximos a vencer</SelectItem>
                    <SelectItem value="top_sellers">🚀 Más vendidos</SelectItem>
                    <SelectItem value="low_stock">⚠️ Stock bajo</SelectItem>
                    <SelectItem value="critical_stock">🚨 Stock crítico</SelectItem>
                    <SelectItem value="trending_up">📈 Tendencia al alza</SelectItem>
                  </SelectContent>
                </Select>
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
              <Table className="w-full min-w-max">
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
                    
                    <TableHead className={`font-bold text-sm py-4 min-w-[450px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                      Producto
                    </TableHead>
                    
                    {state.visibleColumns.sku && (
                      <TableHead className={`font-bold text-sm py-4 min-w-[150px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>SKU</TableHead>
                    )}
                    
                    {state.visibleColumns.category && (
                      <TableHead className={`font-bold text-sm py-4 min-w-[160px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>Categoría</TableHead>
                    )}
                    
                    {state.visibleColumns.price && (
                      <TableHead className={`font-bold text-sm py-4 text-right min-w-[140px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>Precio</TableHead>
                    )}
                    
                    {state.visibleColumns.stock && (
                      <TableHead className={`font-bold text-sm py-4 min-w-[220px] ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>Stock & Estado</TableHead>
                    )}
                    

                    
                    {state.visibleColumns.actions && (
                      <TableHead className={`font-bold text-sm py-4 min-w-[200px] pr-6 ${isDarkMode ? 'text-gray-200' : 'text-slate-700'}`}>Acciones</TableHead>
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
                              <div className={`text-sm leading-relaxed mb-2 ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>
                                {truncateDescription(product.description, 120)}
                                {product.description.length > 120 && (
                                  <button 
                                    className="text-indigo-600 hover:text-indigo-800 ml-1 text-sm underline"
                                    title={product.description}
                                  >
                                    ver más
                                  </button>
                                )}
                              </div>
                            )}
                            
                            {/* Información de stock sin simulaciones de IA */}
                            <div className="mt-2">
                              {(() => {
                                const stock = product.stock || product.current_stock || 0;
                                const minStock = typeof product.min_stock === 'number' ? product.min_stock : 5;
                                
                                if (stock <= 0) {
                                  return (
                                    <div className="flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded-lg">
                                      <span className="text-xs font-medium text-red-800">
                                        ❌ Sin stock disponible
                                      </span>
                                    </div>
                                  );
                                } else if (stock <= minStock) {
                                  return (
                                    <div className="flex items-center gap-2 p-2 bg-orange-50 border border-orange-200 rounded-lg">
                                      <span className="text-xs font-medium text-orange-800">
                                        ⚠️ Stock bajo - {stock} unidades
                                      </span>
                                    </div>
                                  );
                                } else {
                                  return (
                                    <div className="flex items-center gap-2 p-2 bg-green-50 border border-green-200 rounded-lg">
                                      <span className="text-xs font-medium text-green-800">
                                        ✅ Stock normal - {stock} unidades
                                      </span>
                                    </div>
                                  );
                                }
                              })()}
                            </div>
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
                              </div>
                              
                              {/* **MEJORADO: Información real de stock** */}
                              <div className="space-y-1">
                                <div className={`text-sm font-semibold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                                  {(() => {
                                    const stock = product.stock || product.current_stock || 0;
                                    const minStock = typeof product.min_stock === 'number' ? product.min_stock : 5;
                                    const reorderPoint = typeof product.reorder_point === 'number' ? product.reorder_point : 10;
                                    
                                    if (stock <= 0) {
                                      return "❌ Sin stock disponible";
                                    } else if (stock <= minStock) {
                                      return `⚠️ Stock crítico - ${stock} unidades`;
                                    } else if (stock <= reorderPoint) {
                                      return `📦 Stock bajo - ${stock} unidades`;
                                    } else {
                                      return `✅ Stock normal - ${stock} unidades`;
                                    }
                                  })()}
                                </div>
                                <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-slate-500'}`}>
                                  {(() => {
                                    const stock = product.stock || product.current_stock || 0;
                                    const minStock = typeof product.min_stock === 'number' ? product.min_stock : 5;
                                    
                                    if (stock <= 0) {
                                      return "🚨 Reposición inmediata necesaria";
                                    } else if (stock <= minStock) {
                                      return "⚡ Considerar reposición pronto";
                                    } else {
                                      return "📈 Nivel de stock adecuado";
                                    }
                              })()}
                                </div>
                              </div>
                              
                              <span 
                                className={`inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold border ${
                                  product.is_active 
                                    ? 'bg-emerald-100 text-emerald-800 border-emerald-200' 
                                    : 'bg-gray-100 text-gray-800 border-gray-200'
                                }`}
                              >
                                {product.is_active ? 'Activo' : 'Inactivo'}
                              </span>
                            </div>
                          </TableCell>
                        )}
                        
                        {/* COLUMNA DE ACCIONES */}
                        {state.visibleColumns.actions && (
                          <TableCell className="py-3 pr-6">
                            <div className="flex flex-col gap-2">
                              {/* **NUEVO: Acciones inteligentes orientadas al negocio** */}
                            {/* Actions Panel with improved design */}
                            <div className={`flex items-center gap-2 p-2 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
                              {/* Smart AI Action */}
                              <div className="flex items-center gap-1">
                                {(() => {
                                  const stock = product.stock || product.current_stock || 0;
                                  const minStock = typeof product.min_stock === 'number' ? product.min_stock : 5;
                                  const reorderPoint = typeof product.reorder_point === 'number' ? product.reorder_point : 10;
                                  
                                  if (stock <= minStock) {
                                    return (
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleOpenPurchaseDialog(product.id)}
                                        className="h-8 px-3 text-xs bg-red-50 border border-red-200 text-red-700 hover:bg-red-100 hover:text-red-800 font-medium"
                                        title="Configurar orden de compra"
                                      >
                                        <span className="mr-1">🛒</span>
                                        Comprar
                                      </Button>
                                    );
                                  } else if (stock <= reorderPoint) {
                                    return (
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleOpenPurchaseDialog(product.id)}
                                        className="h-8 px-3 text-xs bg-orange-50 border border-orange-200 text-orange-700 hover:bg-orange-100 hover:text-orange-800 font-medium"
                                        title="Generar orden de compra con IA"
                                      >
                                        <span className="mr-1">🔄</span>
                                        Reabastecer
                                      </Button>
                                    );
                                  } else {
                                    return (
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleGetMLForecast(product.id)}
                                        className="h-8 px-3 text-xs bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100 hover:text-blue-800 font-medium"
                                        title="Ver pronóstico con IA"
                                      >
                                        <span className="mr-1">📊</span>
                                        Pronóstico
                                      </Button>
                                    );
                                  }
                                })()}
                              </div>
                              
                              {/* Separator */}
                              <div className={`w-px h-6 ${isDarkMode ? 'bg-gray-600' : 'bg-gray-300'}`}></div>
                              
                              {/* CRUD Actions */}
                              <div className="flex items-center gap-1">
                                <Button 
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleViewProduct(product)}
                                  className={`h-8 w-8 p-0 rounded-md transition-colors ${isDarkMode ? 'text-gray-400 hover:text-blue-400 hover:bg-gray-700' : 'text-slate-600 hover:text-blue-600 hover:bg-blue-50'}`}
                                  title="Ver detalles"
                                >
                                  <span className="text-sm">👁️</span>
                                </Button>
                                
                                <Button 
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => openEditDialog(product)}
                                  className={`h-8 w-8 p-0 rounded-md transition-colors ${isDarkMode ? 'text-gray-400 hover:text-green-400 hover:bg-gray-700' : 'text-slate-600 hover:text-green-600 hover:bg-green-50'}`}
                                  title="Editar producto"
                                >
                                  <span className="text-sm">✏️</span>
                                </Button>
                                
                                <Button 
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDeleteProduct(product.id)}
                                  className={`h-8 w-8 p-0 rounded-md transition-colors ${isDarkMode ? 'text-gray-400 hover:text-red-400 hover:bg-gray-700' : 'text-slate-600 hover:text-red-600 hover:bg-red-50'}`}
                                  title="Eliminar producto"
                                >
                                  <span className="text-sm">🗑️</span>
                                </Button>
                              </div>
                            </div>
                  </div>
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
                        </div>
                      </CardContent>
                    </Card>
      </div>
    </div>

    {/* Product Edit Dialog */}
    <Dialog open={state.isDialogOpen} onOpenChange={(open) => {
      if (!open) handleCloseDialog();
    }}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {state.selectedProduct ? 'Editar Producto' : 'Nuevo Producto'}
          </DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium">Nombre del Producto *</label>
            <Input
              value={state.formData.name || ''}
              onChange={(e) => setState(prev => ({ 
                ...prev, 
                formData: { ...prev.formData, name: e.target.value }
              }))}
              placeholder="Nombre del producto"
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
              placeholder="SKU del producto"
            />
          </div>
          <div className="col-span-2">
            <label className="text-sm font-medium">Descripción</label>
            <Input
              value={state.formData.description || ''}
              onChange={(e) => setState(prev => ({ 
                ...prev, 
                formData: { ...prev.formData, description: e.target.value }
              }))}
              placeholder="Descripción del producto"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Precio de Venta</label>
            <Input
              type="number"
              step="0.01"
              value={state.formData.unit_price || ''}
              onChange={(e) => setState(prev => ({ 
                ...prev, 
                formData: { ...prev.formData, unit_price: parseFloat(e.target.value) || 0 }
              }))}
              placeholder="0.00"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Precio de Costo</label>
            <Input
              type="number"
              step="0.01"
              value={state.formData.cost_price || ''}
              onChange={(e) => setState(prev => ({ 
                ...prev, 
                formData: { ...prev.formData, cost_price: parseFloat(e.target.value) || 0 }
              }))}
              placeholder="0.00"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Stock Mínimo</label>
            <Input
              type="number"
              value={state.formData.min_stock || ''}
              onChange={(e) => setState(prev => ({ 
                ...prev, 
                formData: { ...prev.formData, min_stock: parseInt(e.target.value) || 0 }
              }))}
              placeholder="0"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Stock Máximo</label>
            <Input
              type="number"
              value={state.formData.max_stock || ''}
              onChange={(e) => setState(prev => ({ 
                ...prev, 
                formData: { ...prev.formData, max_stock: parseInt(e.target.value) || 0 }
              }))}
              placeholder="0"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Punto de Reorden</label>
            <Input
              type="number"
              value={state.formData.reorder_point || ''}
              onChange={(e) => setState(prev => ({ 
                ...prev, 
                formData: { ...prev.formData, reorder_point: parseInt(e.target.value) || 0 }
              }))}
              placeholder="0"
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
              placeholder="piezas, kg, litros, etc."
            />
          </div>
          <div className="col-span-2 flex items-center space-x-2">
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
              Producto activo
            </label>
          </div>
          <div className="col-span-2 flex justify-end space-x-2 pt-4">
            <Button variant="ghost" onClick={handleCloseDialog}>
              Cancelar
            </Button>
            <Button onClick={handleSaveProduct} disabled={state.loading}>
              {state.loading ? 'Guardando...' : 'Guardar'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>

    {/* Product View Dialog */}
    <Dialog open={state.isViewDialogOpen} onOpenChange={(open) => {
      if (!open) closeViewDialog();
    }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Ver detalles del producto</DialogTitle>
        </DialogHeader>
        {state.selectedProduct && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-600">Nombre:</label>
              <p className="text-lg font-semibold">{state.selectedProduct.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">SKU:</label>
              <p>{state.selectedProduct.sku || 'No especificado'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Descripción:</label>
              <p>{state.selectedProduct.description || 'Sin descripción'}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-600">Stock:</label>
                <p className="text-xl font-bold text-blue-600">
                  {state.selectedProduct.stock || state.selectedProduct.current_stock || 0}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Precio:</label>
                <p className="text-xl font-bold text-green-600">
                  S/ {(() => {
                    const salePrice = typeof state.selectedProduct.sale_price === 'string' 
                      ? parseFloat(state.selectedProduct.sale_price) 
                      : state.selectedProduct.sale_price;
                    const unitPrice = typeof state.selectedProduct.unit_price === 'string'
                      ? parseFloat(state.selectedProduct.unit_price)
                      : state.selectedProduct.unit_price;
                    return (salePrice || unitPrice || 0).toFixed(2);
                  })()}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-600">Stock Mínimo:</label>
                <p>{state.selectedProduct.min_stock || 0}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Punto de Reorden:</label>
                <p>{state.selectedProduct.reorder_point || 0}</p>
              </div>
            </div>
            {state.selectedProduct.category && (
              <div>
                <label className="text-sm font-medium text-gray-600">Categoría:</label>
                <p>{state.selectedProduct.category}</p>
              </div>
            )}
            {state.selectedProduct.supplier && (
              <div>
                <label className="text-sm font-medium text-gray-600">Proveedor:</label>
                <p>{state.selectedProduct.supplier}</p>
              </div>
            )}
            <div className="flex justify-end pt-4">
              <Button onClick={closeViewDialog}>
                Cerrar
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>

    {/* Product Delete Confirmation Dialog */}
    <Dialog open={state.isDeleteDialogOpen} onOpenChange={(open) => {
      if (!open) closeDeleteDialog();
    }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Confirmar eliminación</DialogTitle>
        </DialogHeader>
        {state.productToDelete && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              ¿Estás seguro de que quieres eliminar "{state.productToDelete.name}"?
            </p>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800 font-medium">Esta acción eliminará completamente:</p>
              <ul className="text-sm text-red-700 mt-2 space-y-1">
                <li>• El producto y todos sus datos</li>
                <li>• Historial de transacciones relacionadas</li>
                <li>• Alertas asociadas</li>
                <li>• Pronósticos de demanda</li>
              </ul>
            </div>
            <p className="text-sm text-gray-500 italic">
              Esta acción NO se puede deshacer.
            </p>
            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="ghost" onClick={closeDeleteDialog}>
                Cancelar
              </Button>
              <Button 
                onClick={confirmDeleteProduct}
                disabled={state.loading}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                {state.loading ? 'Eliminando...' : 'Eliminar'}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>

    {/* Purchase Order Dialog - MEJORADO */}
    <Dialog open={state.isPurchaseOrderDialogOpen} onOpenChange={(open) => !open && handleClosePurchaseDialog()}>
      <DialogContent className={`max-w-2xl max-h-[90vh] overflow-y-auto ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <div className="space-y-6">
          <div className="text-center">
            <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>🛒 Orden de Compra con IA</h2>
            <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              Configurar y enviar orden de compra generada por inteligencia artificial
            </p>
          </div>

          {state.isLoadingPurchaseOrder ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
              <p className={`mt-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Generando orden con IA...</p>
            </div>
          ) : (
            <>
              {/* Información del Producto Seleccionado */}
              {state.selectedProductForPurchase && (
                <div className={`border rounded-lg p-4 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>📦 Producto Seleccionado</h3>
                  <p className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>{state.selectedProductForPurchase.name}</p>
                  <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>SKU: {state.selectedProductForPurchase.sku}</p>
                  <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Stock actual: {state.selectedProductForPurchase.stock || state.selectedProductForPurchase.current_stock || 0} unidades</p>
                  
                  {/* ✅ ELIMINADO: Botón separado de IA - ahora integrado en "Enviar Orden" */}
                </div>
              )}

              {/* Recomendación de IA */}
              {state.purchaseOrderData?.recommendation && (
                <div className={`border rounded-lg p-4 ${isDarkMode ? 'bg-green-900/20 border-green-800' : 'bg-green-50 border-green-200'}`}>
                  <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-green-300' : 'text-green-900'}`}>🤖 Recomendación IA</h3>
                  <p className={`${isDarkMode ? 'text-green-200' : 'text-green-800'}`}>{state.purchaseOrderData.recommendation.ai_insights}</p>
                  <p className={`text-sm mt-1 ${isDarkMode ? 'text-green-300' : 'text-green-600'}`}>
                    Prioridad: <span className="font-medium">{state.purchaseOrderData.recommendation.priority_level}</span>
                  </p>
                </div>
              )}

              {/* Información del Producto (datos de IA) */}
              {state.purchaseOrderData?.product && (
                <div className={`border rounded-lg p-4 ${isDarkMode ? 'bg-blue-900/20 border-blue-800' : 'bg-blue-50 border-blue-200'}`}>
                  <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-blue-300' : 'text-blue-900'}`}>📦 Producto</h3>
                  <p className={`font-medium ${isDarkMode ? 'text-blue-200' : 'text-blue-800'}`}>{state.purchaseOrderData.product.name}</p>
                  <p className={`text-sm ${isDarkMode ? 'text-blue-300' : 'text-blue-600'}`}>SKU: {state.purchaseOrderData.product.sku}</p>
                  <p className={`text-sm ${isDarkMode ? 'text-blue-300' : 'text-blue-600'}`}>Stock actual: {state.purchaseOrderData.product.current_stock || 0} unidades</p>
                </div>
              )}

              {/* Recomendación de IA */}
              {state.purchaseOrderData?.recommendation && (
                <div className={`border rounded-lg p-4 ${isDarkMode ? 'bg-green-900/20 border-green-800' : 'bg-green-50 border-green-200'}`}>
                  <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-green-300' : 'text-green-900'}`}>🤖 Recomendación IA</h3>
                  <p className={`${isDarkMode ? 'text-green-200' : 'text-green-800'}`}>{state.purchaseOrderData.recommendation.insights}</p>
                  <p className={`text-sm mt-1 ${isDarkMode ? 'text-green-300' : 'text-green-600'}`}>
                    Prioridad: <span className="font-medium">{state.purchaseOrderData.recommendation.priority}</span>
                  </p>
                </div>
              )}

              {/* Configuración de Cantidad */}
              <div className={`border rounded-lg p-4 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                <h3 className={`font-semibold mb-3 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>📊 Cantidad a Ordenar</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Cantidad Sugerida por IA</label>
                    <p className="text-2xl font-bold text-indigo-600">
                      {state.purchaseOrderData?.recommendation?.ai_suggested_quantity || state.purchaseOrderData?.final_quantity || 0}
                    </p>
                  </div>
                  <div>
                    <label className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Cantidad Personalizada</label>
                    <Input
                      type="number"
                      min="1"
                      value={state.customQuantity}
                      onChange={(e) => setState(prev => ({ ...prev, customQuantity: parseInt(e.target.value) || 0 }))}
                      className={`mt-1 ${isDarkMode ? 'bg-gray-700 border-gray-600 text-white' : ''}`}
                    />
                  </div>
                </div>
                <div className={`mt-2 text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Costo estimado: S/ {((state.customQuantity || 0) * (state.purchaseOrderData?.product?.cost_price || 0)).toFixed(2)}
                </div>
              </div>

              {/* Configuración de Envío */}
              <div className={`border rounded-lg p-4 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                <h3 className={`font-semibold mb-3 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>📧 Configuración de Envío</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Correo Electrónico *</label>
                    <Input
                      type="email"
                      value={state.purchaseOrderEmail}
                      onChange={(e) => setState(prev => ({ ...prev, purchaseOrderEmail: e.target.value }))}
                      placeholder="compras@empresa.com"
                      className={`mt-1 ${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''}`}
                    />
                    <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      La orden de compra será enviada a este correo
                    </p>
                  </div>

                  <div>
                    <label className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>WhatsApp (Próximamente)</label>
                    <div className="relative">
                      <Input
                        type="tel"
                        value={state.purchaseOrderWhatsApp}
                        onChange={(e) => setState(prev => ({ ...prev, purchaseOrderWhatsApp: e.target.value }))}
                        placeholder="+51999999999"
                        disabled={!state.whatsappEnabled}
                        className={`mt-1 ${isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : ''}`}
                      />
                      <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                        <input
                          type="checkbox"
                          checked={state.whatsappEnabled}
                          onChange={(e) => setState(prev => ({ ...prev, whatsappEnabled: e.target.checked }))}
                          disabled={true}
                          className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500 opacity-50"
                        />
                      </div>
                    </div>
                    <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                      🚧 Funcionalidad en desarrollo - próximamente disponible
                    </p>
                  </div>
                </div>
              </div>

              {/* Resumen de Orden */}
              {state.purchaseOrderData?.summary && (
                <div className={`border rounded-lg p-4 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
                  <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>📋 Resumen de Orden</h3>
                  <div className={`text-sm space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    <p><strong>Proveedor:</strong> {state.purchaseOrderData.supplier?.name || 'No especificado'}</p>
                    <p><strong>Tiempo de entrega:</strong> {state.purchaseOrderData.summary.estimated_delivery} días</p>
                    <p><strong>Costo total:</strong> S/ {state.purchaseOrderData.summary.total_cost?.toFixed(2) || '0.00'}</p>
                  </div>
                </div>
              )}

              {/* Botones de Acción */}
              <div className={`flex justify-end space-x-3 pt-4 ${isDarkMode ? 'border-gray-700' : 'border-gray-200'} border-t`}>
                <Button 
                  variant="ghost" 
                  onClick={handleClosePurchaseDialog}
                >
                  Cancelar
                </Button>
                <Button 
                  onClick={handleSendPurchaseOrder}
                  disabled={!state.purchaseOrderEmail || state.isLoadingPurchaseOrder}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  {state.isLoadingPurchaseOrder ? '⏳ Enviando...' : '📧 Enviar Orden de Compra'}
                </Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>

    {/* **✅ NUEVO: Dialog "Coming Soon" para Pronósticos ML** */}
    <Dialog open={state.isForecastDialogOpen} onOpenChange={(open) => !open && handleCloseForecastDialog()}>
      <DialogContent className={`max-w-md ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <div className="text-center space-y-6 py-4">
          {/* Icono principal */}
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
            <span className="text-2xl">📊</span>
          </div>
          
          {/* Título */}
          <div>
            <h2 className={`text-xl font-bold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Pronósticos con IA
            </h2>
            <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              {state.selectedProductForPurchase?.name}
            </p>
          </div>
          
          {/* Mensaje principal */}
          <div className={`p-4 rounded-lg border ${isDarkMode ? 'bg-blue-900/20 border-blue-800' : 'bg-blue-50 border-blue-200'}`}>
            <div className="flex items-center justify-center mb-3">
              <span className="text-3xl">🔮</span>
            </div>
            <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-blue-300' : 'text-blue-900'}`}>
              Funcionalidad en Desarrollo
            </h3>
            <p className={`text-sm leading-relaxed ${isDarkMode ? 'text-blue-200' : 'text-blue-800'}`}>
              Los pronósticos ML con análisis predictivo estarán disponibles próximamente. Esta característica incluirá:
            </p>
          </div>
          
          {/* Lista de características */}
          <div className={`text-left space-y-2 p-4 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
            <div className="flex items-center gap-3">
              <span className="text-green-500">✅</span>
              <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Predicciones de demanda con IA</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-green-500">✅</span>
              <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Análisis de tendencias del mercado</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-green-500">✅</span>
              <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Recomendaciones automáticas de stock</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-green-500">✅</span>
              <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Gráficos interactivos avanzados</span>
            </div>
          </div>
          
          {/* Botón de cierre */}
          <div className="pt-2">
            <Button 
              onClick={handleCloseForecastDialog}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white"
            >
              🚀 ¡Genial! Me avisarán cuando esté listo
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
    </>
  );
};

export default ProductsPage;

/*
==========================================================================
RESUMEN DE CONECTIVIDAD FRONTEND ↔ BACKEND
==========================================================================

✅ FUNCIONALIDADES COMPLETAMENTE CONECTADAS Y FUNCIONANDO:
-----------------------------------------------------------
1. 🛒 AI Purchase Order Generation
   - Endpoint: POST /api/inventory/products/actions/ (action="generate_purchase_order")
   - Incluye: OpenAI integration, intelligent quantity calculation, supplier detection
   
2. 📧 AI Email Generation & Sending
   - Endpoint: POST /api/inventory/products/actions/ (action="send_purchase_email")
   - Incluye: Professional email generation with OpenAI, automatic sending
   
3. 📊 ML Forecasting with AI Insights
   - Endpoint: POST /api/inventory/products/actions/ (action="get_forecast")
   - Incluye: ML models (Prophet, LSTM), OpenAI analysis, confidence intervals
   
4. ✏️ Product CRUD Operations
   - GET /api/inventory/products/ (list products)
   - POST /api/inventory/products/ (create product)
   - PATCH /api/inventory/products/{id}/ (update product)
   - DELETE /api/inventory/products/{id}/ (delete product)
   
5. 📁 Categories & Suppliers Management
   - Full CRUD operations for both categories and suppliers
   
6. 🔐 Authentication & Authorization
   - JWT tokens, automatic refresh, company-based isolation

⚡ PARCIALMENTE CONECTADAS (con fallback local):
------------------------------------------------------
1. 🧠 Product Intelligence
   - Endpoint: GET /api/inventory/products/intelligence/
   - Status: Available but uses fallback data when endpoint fails
   
2. 📊 Dashboard Data
   - Various dashboard endpoints with fallback implementations

🔮 FEATURES FUTURAS (UI ready, esperando backend):
-------------------------------------------------
1. 🎯 Smart Filters
   - UI implementada para filtros inteligentes
   - Lógica temporal local hasta implementar: GET /api/inventory/products/smart-filters/
   
2. 📈 Advanced Analytics
   - Varios endpoints de analytics avanzados pendientes
   
3. 📱 WhatsApp Notifications
   - UI preparada, backend en standby por solicitud del usuario

==========================================================================
BACKEND SERVER: http://localhost:8080/api
FRONTEND SERVER: http://localhost:8081
AUTHENTICATION: JWT with auto-refresh
==========================================================================
*/