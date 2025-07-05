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
  AlertTriangle
} from '../components/ui/icons';
import { Category } from '../types';
import { inventoryService } from '../services/api';

interface CategoriesPageState {
  categories: Category[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  isDialogOpen: boolean;
  selectedCategory: Category | null;
  formData: Partial<Category>;
}

const CategoriesPage: React.FC = () => {
  const [state, setState] = useState<CategoriesPageState>({
    categories: [],
    loading: true,
    error: null,
    searchTerm: '',
    isDialogOpen: false,
    selectedCategory: null,
    formData: {}
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
    fetchCategories();
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

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <FolderOpen className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Categorías</p>
                <p className="text-2xl font-bold text-gray-900">{state.categories.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Categorías Activas</p>
                <p className="text-2xl font-bold text-gray-900">{activeCategories.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Package className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Categorías Filtradas</p>
                <p className="text-2xl font-bold text-gray-900">{filteredCategories.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">% Activas</p>
                <p className="text-2xl font-bold text-gray-900">
                  {state.categories.length > 0 ? Math.round((activeCategories.length / state.categories.length) * 100) : 0}%
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

      {/* Categories Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Categorías</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Descripción</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCategories.map((category) => (
                <TableRow key={category.id}>
                  <TableCell className="font-medium">{category.name}</TableCell>
                  <TableCell>{category.description || 'Sin descripción'}</TableCell>
                  <TableCell>
                    <Badge variant={category.is_active ? 'success' : 'secondary'}>
                      {category.is_active ? 'Activa' : 'Inactiva'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
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
              ))}
            </TableBody>
          </Table>
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
