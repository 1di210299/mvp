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
  TableRow,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '../components/ui';
import {
  Users,
  Plus,
  Search,
  Eye,
  Edit,
  Trash2,
  Phone,
  Mail,
  MapPin,
  Building2,
  Calendar,
  TrendingUp,
  DollarSign,
  User,
  AlertTriangle,
  Package
} from '../components/ui/icons';
import { inventoryService } from '../services/api';

interface Customer {
  id: number;
  name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  customer_type: string;
  status: string;
  total_orders: number;
  total_spent: number;
  last_order_date: string;
  created_at: string;
  notes: string;
  company_name?: string;
  contact_person?: string;
  total_sales?: number;
  last_purchase_date?: string;
}

interface CustomersPageState {
  customers: Customer[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  selectedType: string;
  selectedStatus: string;
  showCreateDialog: boolean;
  editingCustomer: Customer | null;
  formData: Partial<Customer>;
}

const CustomersPage: React.FC = () => {
  const [state, setState] = useState<CustomersPageState>({
    customers: [],
    loading: true,
    error: null,
    searchTerm: '',
    selectedType: 'all',
    selectedStatus: 'all',
    showCreateDialog: false,
    editingCustomer: null,
    formData: {}
  });

  const fetchCustomers = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Usar API real del sistema de clientes Django
      const response = await inventoryService.getCustomers();
      const customersData = response.results || response || [];
      
      setState(prev => ({ ...prev, customers: customersData, loading: false }));
    } catch (err) {
      console.error('Error fetching customers:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al conectar con el sistema de clientes Django. Verificar servidor.',
        loading: false,
        customers: [] // NO usar datos mock
      }));
    }
  };

  const handleCreateCustomer = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      
      const customerData = {
        name: state.formData.name,
        email: state.formData.email,
        phone: state.formData.phone,
        address: state.formData.address,
        city: state.formData.city,
        country: state.formData.country || 'Perú',
        customer_type: state.formData.customer_type || 'individual',
        status: 'active',
        notes: state.formData.notes || ''
      };

      await inventoryService.createCustomer(customerData);
      await fetchCustomers();
      
      setState(prev => ({
        ...prev,
        showCreateDialog: false,
        formData: {},
        loading: false
      }));
    } catch (err) {
      console.error('Error creating customer:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al crear cliente. Verificar conexión con Django.',
        loading: false
      }));
    }
  };

  const handleUpdateCustomer = async (id: number) => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      await inventoryService.updateCustomer(id, state.formData);
      await fetchCustomers();
      
      setState(prev => ({
        ...prev,
        editingCustomer: null,
        formData: {},
        loading: false
      }));
    } catch (err) {
      console.error('Error updating customer:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al actualizar cliente. Verificar conexión con Django.',
        loading: false
      }));
    }
  };

  const handleDeleteCustomer = async (id: number) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este cliente?')) {
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true }));
      await inventoryService.deleteCustomer(id);
      await fetchCustomers();
      setState(prev => ({ ...prev, loading: false }));
    } catch (err) {
      console.error('Error deleting customer:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al eliminar cliente. Verificar conexión con Django.',
        loading: false
      }));
    }
  };

  const filteredCustomers = state.customers.filter(customer => {
    const matchesSearch = (customer.name || '').toLowerCase().includes(state.searchTerm.toLowerCase()) ||
                         (customer.email || '').toLowerCase().includes(state.searchTerm.toLowerCase());
    const matchesType = state.selectedType === 'all' || customer.customer_type === state.selectedType;
    const matchesStatus = state.selectedStatus === 'all' || customer.status === state.selectedStatus;
    
    return matchesSearch && matchesType && matchesStatus;
  });

  const getCustomerTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      individual: 'Individual',
      corporate: 'Corporativo',
      distributor: 'Distribuidor'
    };
    return types[type] || type;
  };

  const getStatusColor = (status: string) => {
    return status === 'active' ? 'text-green-600 bg-green-50' : 'text-gray-600 bg-gray-50';
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      active: 'Activo',
      inactive: 'Inactivo'
    };
    return labels[status] || status;
  };

  const getCustomerStats = () => {
    const totalCustomers = state.customers.length;
    const activeCustomers = state.customers.filter(c => c.status === 'active').length;
    const totalRevenue = state.customers.reduce((sum, c) => sum + c.total_spent, 0);
    const avgOrderValue = totalRevenue / Math.max(state.customers.reduce((sum, c) => sum + c.total_orders, 0), 1);

    return {
      totalCustomers,
      activeCustomers,
      totalRevenue,
      avgOrderValue: Math.round(avgOrderValue)
    };
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  if (state.loading && state.customers.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const stats = getCustomerStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Clientes</h1>
          <p className="text-gray-600">Administra tu base de clientes y relaciones comerciales</p>
        </div>
        <Dialog open={state.showCreateDialog} onOpenChange={(open) => setState(prev => ({ ...prev, showCreateDialog: open }))}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Nuevo Cliente
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Cliente</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Nombre/Empresa</label>
                <Input
                  value={state.formData.name || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, name: e.target.value }
                  }))}
                  placeholder="Nombre del cliente"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Email</label>
                <Input
                  type="email"
                  value={state.formData.email || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, email: e.target.value }
                  }))}
                  placeholder="email@ejemplo.com"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Teléfono</label>
                <Input
                  value={state.formData.phone || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, phone: e.target.value }
                  }))}
                  placeholder="+51 999 123 456"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Tipo de Cliente</label>
                <Select value={state.formData.customer_type || 'individual'} onValueChange={(value) => setState(prev => ({
                  ...prev,
                  formData: { ...prev.formData, customer_type: value }
                }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="individual">Individual</SelectItem>
                    <SelectItem value="corporate">Corporativo</SelectItem>
                    <SelectItem value="distributor">Distribuidor</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium">Dirección</label>
                <Input
                  value={state.formData.address || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, address: e.target.value }
                  }))}
                  placeholder="Dirección completa"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Ciudad</label>
                <Input
                  value={state.formData.city || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, city: e.target.value }
                  }))}
                  placeholder="Lima"
                />
              </div>
              <div>
                <label className="text-sm font-medium">País</label>
                <Input
                  value={state.formData.country || 'Perú'}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, country: e.target.value }
                  }))}
                  placeholder="Perú"
                />
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium">Notas</label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                  value={state.formData.notes || ''}
                  onChange={(e) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, notes: e.target.value }
                  }))}
                  placeholder="Notas adicionales sobre el cliente"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button 
                variant="outline" 
                onClick={() => setState(prev => ({ ...prev, showCreateDialog: false, formData: {} }))}
              >
                Cancelar
              </Button>
              <Button onClick={handleCreateCustomer}>
                Crear Cliente
              </Button>
            </div>
          </DialogContent>
        </Dialog>
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
              <Users className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Clientes</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalCustomers}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Clientes Activos</p>
                <p className="text-2xl font-bold text-gray-900">{stats.activeCustomers}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <DollarSign className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Ingresos Totales</p>
                <p className="text-2xl font-bold text-gray-900">S/ {stats.totalRevenue.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Package className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Valor Promedio</p>
                <p className="text-2xl font-bold text-gray-900">S/ {stats.avgOrderValue.toLocaleString()}</p>
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
                  placeholder="Buscar clientes..."
                  value={state.searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={state.selectedType} onValueChange={(value) => setState(prev => ({ ...prev, selectedType: value }))}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Tipo de cliente" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los tipos</SelectItem>
                <SelectItem value="individual">Individual</SelectItem>
                <SelectItem value="corporate">Corporativo</SelectItem>
                <SelectItem value="distributor">Distribuidor</SelectItem>
              </SelectContent>
            </Select>
            <Select value={state.selectedStatus} onValueChange={(value) => setState(prev => ({ ...prev, selectedStatus: value }))}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los estados</SelectItem>
                <SelectItem value="active">Activo</SelectItem>
                <SelectItem value="inactive">Inactivo</SelectItem>
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

      {/* Customers Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Clientes</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead>Contacto</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Ubicación</TableHead>
                <TableHead>Ventas Totales</TableHead>
                <TableHead>Última Compra</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCustomers.map((customer) => (
                <TableRow key={customer.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{customer.company_name || customer.name}</div>
                      <div className="text-sm text-gray-500 flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {customer.contact_person || customer.name}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1 text-sm">
                        <Mail className="h-3 w-3" />
                        {customer.email}
                      </div>
                      <div className="flex items-center gap-1 text-sm">
                        <Phone className="h-3 w-3" />
                        {customer.phone}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">
                      {getCustomerTypeLabel(customer.customer_type)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <MapPin className="h-3 w-3" />
                      {customer.address}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium text-green-600">
                      S/ {(customer.total_sales || customer.total_spent || 0).toLocaleString()}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <Calendar className="h-3 w-3" />
                      {(customer.last_purchase_date || customer.last_order_date) ? 
                        new Date(customer.last_purchase_date || customer.last_order_date).toLocaleDateString() : 
                        'N/A'
                      }
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(customer.status)}>
                      {getStatusLabel(customer.status)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => setState(prev => ({ 
                          ...prev, 
                          editingCustomer: customer, 
                          formData: customer 
                        }))}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => handleDeleteCustomer(customer.id)}
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

      {/* Edit Dialog */}
      {state.editingCustomer && (
        <Dialog open={!!state.editingCustomer} onOpenChange={(open) => {
          if (!open) setState(prev => ({ ...prev, editingCustomer: null, formData: {} }));
        }}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Editar Cliente</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Nombre/Empresa</label>
                <Input
                  value={state.formData.name || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, name: e.target.value }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Email</label>
                <Input
                  type="email"
                  value={state.formData.email || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, email: e.target.value }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Teléfono</label>
                <Input
                  value={state.formData.phone || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, phone: e.target.value }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Estado</label>
                <Select value={state.formData.status || 'active'} onValueChange={(value) => setState(prev => ({
                  ...prev,
                  formData: { ...prev.formData, status: value }
                }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Activo</SelectItem>
                    <SelectItem value="inactive">Inactivo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button 
                variant="outline" 
                onClick={() => setState(prev => ({ ...prev, editingCustomer: null, formData: {} }))}
              >
                Cancelar
              </Button>
              <Button onClick={() => handleUpdateCustomer(state.editingCustomer!.id)}>
                Guardar Cambios
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default CustomersPage;