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
  Building2,
  Plus,
  Search,
  Edit,
  Trash2,
  Phone,
  Mail,
  MapPin,
  TrendingUp,
  Package,
  DollarSign,
  AlertTriangle,
  MessageCircle
} from '../components/ui/icons';
import { inventoryService } from '../services/api';

interface Supplier {
  id: number;
  name: string;
  contact_name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  tax_id: string;
  payment_terms: string;
  is_active: boolean;
  whatsapp_number?: string;
  whatsapp_enabled?: boolean;
  prefers_whatsapp?: boolean;
  minimum_order_quantity?: number;
  delivery_days?: number;
  created_at: string;
}

interface SuppliersPageState {
  suppliers: Supplier[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  isDialogOpen: boolean;
  selectedSupplier: Supplier | null;
  formData: Partial<Supplier>;
}

const SuppliersPage: React.FC = () => {
  const [state, setState] = useState<SuppliersPageState>({
    suppliers: [],
    loading: true,
    error: null,
    searchTerm: '',
    isDialogOpen: false,
    selectedSupplier: null,
    formData: {}
  });

  const fetchSuppliers = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const response = await inventoryService.getSuppliers();
      setState(prev => ({ 
        ...prev, 
        suppliers: response.results || response,
        loading: false 
      }));
    } catch (err) {
      console.error('Error fetching suppliers:', err);
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al cargar proveedores',
        loading: false 
      }));
    }
  };

  const handleSaveSupplier = async () => {
    try {
      if (!state.formData.name?.trim()) {
        setState(prev => ({ ...prev, error: 'El nombre es requerido' }));
        return;
      }

      setState(prev => ({ ...prev, loading: true, error: null }));
      
      if (state.selectedSupplier) {
        // Actualizar proveedor existente
        await inventoryService.updateSupplier(state.selectedSupplier.id, state.formData);
      } else {
        // Crear nuevo proveedor
        await inventoryService.createSupplier({
          ...state.formData,
          is_active: state.formData.is_active !== undefined ? state.formData.is_active : true
        });
      }
      
      await fetchSuppliers();
      handleCloseDialog();
    } catch (err) {
      console.error('Error saving supplier:', err);
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al guardar proveedor',
        loading: false 
      }));
    }
  };

  const handleDeleteSupplier = async (id: number) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar este proveedor?')) {
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      await inventoryService.deleteSupplier(id);
      await fetchSuppliers();
    } catch (err) {
      console.error('Error deleting supplier:', err);
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al eliminar proveedor',
        loading: false 
      }));
    }
  };

  const handleCloseDialog = () => {
    setState(prev => ({
      ...prev,
      isDialogOpen: false,
      selectedSupplier: null,
      formData: {},
      error: null
    }));
  };

  const openEditDialog = (supplier: Supplier) => {
    setState(prev => ({
      ...prev,
      selectedSupplier: supplier,
      formData: { ...supplier },
      isDialogOpen: true
    }));
  };

  const openCreateDialog = () => {
    setState(prev => ({
      ...prev,
      selectedSupplier: null,
      formData: {
        name: '',
        contact_name: '',
        email: '',
        phone: '',
        address: '',
        city: '',
        country: '',
        tax_id: '',
        payment_terms: '',
        is_active: true,
        // ✅ NUEVO: Campos WhatsApp con valores por defecto
        whatsapp_number: '',
        whatsapp_enabled: false,
        prefers_whatsapp: false,
        // ✅ NUEVO: Configuraciones de orden (sin valores por defecto)
        minimum_order_quantity: undefined,
        delivery_days: undefined
      },
      isDialogOpen: true
    }));
  };

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const filteredSuppliers = state.suppliers.filter(supplier =>
    (supplier.name || '').toLowerCase().includes(state.searchTerm.toLowerCase()) ||
    (supplier.contact_name || '').toLowerCase().includes(state.searchTerm.toLowerCase()) ||
    (supplier.email || '').toLowerCase().includes(state.searchTerm.toLowerCase()) ||
    (supplier.city || '').toLowerCase().includes(state.searchTerm.toLowerCase())
  );

  if (state.loading && state.suppliers.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const activeSuppliers = state.suppliers.filter(supplier => supplier.is_active);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Proveedores</h1>
          <p className="text-gray-600">Administra tu red de proveedores y contactos</p>
        </div>
        <Button onClick={openCreateDialog} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Nuevo Proveedor
        </Button>
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
              <Building2 className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Proveedores</p>
                <p className="text-2xl font-bold text-gray-900">{state.suppliers.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Proveedores Activos</p>
                <p className="text-2xl font-bold text-gray-900">{activeSuppliers.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Package className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Resultados Filtrados</p>
                <p className="text-2xl font-bold text-gray-900">{filteredSuppliers.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <DollarSign className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">% Activos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {state.suppliers.length > 0 ? Math.round((activeSuppliers.length / state.suppliers.length) * 100) : 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Buscar proveedores..."
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

      {/* Suppliers Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Proveedores</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Empresa</TableHead>
                <TableHead>Contacto</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Teléfono</TableHead>
                <TableHead>Ciudad</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSuppliers.map((supplier) => (
                <TableRow key={supplier.id}>
                  <TableCell className="font-medium">
                    <div>
                      <div className="font-semibold">{supplier.name}</div>
                      <div className="text-sm text-gray-500">{supplier.tax_id}</div>
                    </div>
                  </TableCell>
                  <TableCell>{supplier.contact_name}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Mail className="h-3 w-3 text-gray-400" />
                      {supplier.email}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Phone className="h-3 w-3 text-gray-400" />
                      {supplier.phone}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3 w-3 text-gray-400" />
                      {supplier.city}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={supplier.is_active ? 'success' : 'secondary'}>
                      {supplier.is_active ? 'Activo' : 'Inactivo'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(supplier)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteSupplier(supplier.id)}
                        className="text-red-600"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Supplier Dialog */}
      <Dialog open={state.isDialogOpen} onOpenChange={(open) => {
        if (!open) handleCloseDialog();
      }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {state.selectedSupplier ? 'Editar Proveedor' : 'Nuevo Proveedor'}
            </DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Nombre de la Empresa *</label>
              <Input
                value={state.formData.name || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, name: e.target.value }
                }))}
                placeholder="Nombre de la empresa"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Persona de Contacto</label>
              <Input
                value={state.formData.contact_name || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, contact_name: e.target.value }
                }))}
                placeholder="Nombre del contacto"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Email</label>
              <Input
                type="email"
                value={state.formData.email || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, email: e.target.value }
                }))}
                placeholder="email@empresa.com"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Teléfono</label>
              <Input
                value={state.formData.phone || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, phone: e.target.value }
                }))}
                placeholder="+51 999 123 456"
              />
            </div>
            <div className="col-span-2">
              <label className="text-sm font-medium">Dirección</label>
              <Input
                value={state.formData.address || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, address: e.target.value }
                }))}
                placeholder="Dirección completa"
              />
            </div>
            
            {/* ✅ NUEVO: Sección WhatsApp */}
            <div className="col-span-2">
              <h3 className="text-lg font-medium mb-3 flex items-center gap-2">
                <MessageCircle className="h-5 w-5 text-green-600" />
                Configuración WhatsApp
              </h3>
              <div className="grid grid-cols-2 gap-4 p-4 bg-green-50 rounded-lg">
                <div>
                  <label className="text-sm font-medium">Número WhatsApp</label>
                  <Input
                    value={state.formData.whatsapp_number || ''}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, whatsapp_number: e.target.value }
                    }))}
                    placeholder="+51999999999"
                  />
                  <p className="text-xs text-gray-500 mt-1">Formato: +51999999999</p>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="whatsapp_enabled"
                      checked={state.formData.whatsapp_enabled || false}
                      onChange={(e) => setState(prev => ({ 
                        ...prev, 
                        formData: { ...prev.formData, whatsapp_enabled: e.target.checked }
                      }))}
                    />
                    <label htmlFor="whatsapp_enabled" className="text-sm font-medium">
                      WhatsApp habilitado
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="prefers_whatsapp"
                      checked={state.formData.prefers_whatsapp || false}
                      onChange={(e) => setState(prev => ({ 
                        ...prev, 
                        formData: { ...prev.formData, prefers_whatsapp: e.target.checked }
                      }))}
                    />
                    <label htmlFor="prefers_whatsapp" className="text-sm font-medium">
                      Prefiere WhatsApp
                    </label>
                  </div>
                  <p className="text-xs text-gray-500">
                    Si está habilitado, las órdenes se enviarán por WhatsApp preferentemente
                  </p>
                </div>
              </div>
            </div>
            
            {/* ✅ NUEVO: Configuraciones de Orden */}
            <div className="col-span-2">
              <h3 className="text-lg font-medium mb-3 flex items-center gap-2">
                <Package className="h-5 w-5 text-blue-600" />
                Configuraciones de Orden
              </h3>
              <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg">
                <div>
                  <label className="text-sm font-medium">Cantidad Mínima de Orden</label>
                  <Input
                    type="number"
                    min="1"
                    value={state.formData.minimum_order_quantity || ''}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, minimum_order_quantity: e.target.value ? parseInt(e.target.value) : undefined }
                    }))}
                    placeholder="Ej: 5, 10, 100..."
                  />
                  <p className="text-xs text-gray-500 mt-1">Cantidad mínima que acepta el proveedor</p>
                </div>
                <div>
                  <label className="text-sm font-medium">Días de Entrega</label>
                  <Input
                    type="number"
                    min="1"
                    value={state.formData.delivery_days || ''}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      formData: { ...prev.formData, delivery_days: e.target.value ? parseInt(e.target.value) : undefined }
                    }))}
                    placeholder="Ej: 1-2 días local, 15-30 días importación..."
                  />
                  <p className="text-xs text-gray-500 mt-1">Tiempo estimado de entrega desde la orden</p>
                </div>
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium">Ciudad</label>
              <Input
                value={state.formData.city || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, city: e.target.value }
                }))}
                placeholder="Ciudad"
              />
            </div>
            <div>
              <label className="text-sm font-medium">País</label>
              <Input
                value={state.formData.country || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, country: e.target.value }
                }))}
                placeholder="País"
              />
            </div>
            <div>
              <label className="text-sm font-medium">RUC/Tax ID</label>
              <Input
                value={state.formData.tax_id || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, tax_id: e.target.value }
                }))}
                placeholder="20123456789"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Términos de Pago</label>
              <Input
                value={state.formData.payment_terms || ''}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, payment_terms: e.target.value }
                }))}
                placeholder="30 días"
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
                Proveedor activo
              </label>
            </div>
            <div className="col-span-2 flex justify-end space-x-2 pt-4">
              <Button variant="ghost" onClick={handleCloseDialog}>
                Cancelar
              </Button>
              <Button onClick={handleSaveSupplier} disabled={state.loading}>
                {state.loading ? 'Guardando...' : 'Guardar'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SuppliersPage;
