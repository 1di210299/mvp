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
  Briefcase,
  Plus,
  Search,
  Eye,
  Edit,
  Trash2,
  DollarSign,
  Calendar,
  TrendingUp,
  Package,
  User,
  Clock,
  AlertTriangle
} from '../components/ui/icons';
import { inventoryService } from '../services/api';

interface Opportunity {
  id: number;
  name: string;
  customer_name: string;
  contact_person: string;
  stage: string;
  probability: number;
  value: number;
  expected_close_date: string;
  created_at: string;
  last_activity: string;
  next_action: string;
  description: string;
  source: string;
  products: any[];
}

interface OpportunitiesPageState {
  opportunities: Opportunity[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  selectedStage: string;
  selectedSource: string;
  showCreateDialog: boolean;
  editingOpportunity: Opportunity | null;
  formData: Partial<Opportunity>;
}

const OpportunitiesPage: React.FC = () => {
  const [state, setState] = useState<OpportunitiesPageState>({
    opportunities: [],
    loading: true,
    error: null,
    searchTerm: '',
    selectedStage: 'all',
    selectedSource: 'all',
    showCreateDialog: false,
    editingOpportunity: null,
    formData: {}
  });

  const fetchOpportunities = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const response = await inventoryService.getOpportunities();
      const opportunitiesData = response.results || response || [];
      setState(prev => ({ ...prev, opportunities: opportunitiesData, loading: false }));
    } catch (err) {
      console.error('Error fetching opportunities:', err);
      
      // Fallback a datos simulados
      const mockOpportunities: Opportunity[] = [
        {
          id: 1,
          name: 'Sistema de Inventario TechSolutions',
          customer_name: 'TechSolutions Perú',
          contact_person: 'Carlos Mendoza',
          stage: 'proposal',
          probability: 75,
          value: 25000,
          expected_close_date: '2024-02-15',
          created_at: '2024-01-10T09:00:00Z',
          last_activity: '2024-01-18T14:30:00Z',
          next_action: 'Presentar propuesta final',
          description: 'Implementación completa de sistema de inventario con módulos de forecasting',
          source: 'lead_conversion',
          products: ['Sistema Base', 'Módulo Forecasting', 'Soporte Premium']
        },
        {
          id: 2,
          name: 'Expansión StartupPE',
          customer_name: 'StartupPE',
          contact_person: 'Ana Rodriguez',
          stage: 'negotiation',
          probability: 60,
          value: 15000,
          expected_close_date: '2024-02-28',
          created_at: '2024-01-12T11:20:00Z',
          last_activity: '2024-01-19T16:45:00Z',
          next_action: 'Negociar términos de pago',
          description: 'Ampliación del sistema actual para manejar crecimiento de la empresa',
          source: 'existing_customer',
          products: ['Módulos Adicionales', 'Licencias Extra']
        },
        {
          id: 3,
          name: 'Modernización Comercial Lima',
          customer_name: 'Comercial Lima SAC',
          contact_person: 'Miguel Torres',
          stage: 'qualification',
          probability: 40,
          value: 35000,
          expected_close_date: '2024-03-30',
          created_at: '2024-01-14T13:15:00Z',
          last_activity: '2024-01-20T10:00:00Z',
          next_action: 'Reunión de diagnóstico',
          description: 'Reemplazo completo del sistema legacy por solución moderna',
          source: 'referral',
          products: ['Sistema Completo', 'Migración de Datos', 'Capacitación']
        }
      ];
      
      setState(prev => ({
        ...prev,
        opportunities: mockOpportunities,
        loading: false,
        error: 'Conectado con datos simulados - API no disponible'
      }));
    }
  };

  const handleCreateOpportunity = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      
      const opportunityData = {
        name: state.formData.name,
        customer_name: state.formData.customer_name,
        contact_person: state.formData.contact_person,
        stage: state.formData.stage || 'prospecting',
        probability: state.formData.probability || 25,
        value: state.formData.value || 0,
        expected_close_date: state.formData.expected_close_date,
        description: state.formData.description || '',
        source: state.formData.source || 'direct',
        next_action: state.formData.next_action || ''
      };

      await inventoryService.createOpportunity(opportunityData);
      await fetchOpportunities();
      
      setState(prev => ({
        ...prev,
        showCreateDialog: false,
        formData: {},
        loading: false
      }));
    } catch (err) {
      console.error('Error creating opportunity:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al crear oportunidad',
        loading: false
      }));
    }
  };

  const handleUpdateOpportunity = async (id: number) => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      await inventoryService.updateOpportunity(id, state.formData);
      await fetchOpportunities();
      
      setState(prev => ({
        ...prev,
        editingOpportunity: null,
        formData: {},
        loading: false
      }));
    } catch (err) {
      console.error('Error updating opportunity:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al actualizar oportunidad',
        loading: false
      }));
    }
  };

  const handleDeleteOpportunity = async (id: number) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar esta oportunidad?')) {
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true }));
      await inventoryService.deleteOpportunity(id);
      await fetchOpportunities();
    } catch (err) {
      console.error('Error deleting opportunity:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al eliminar oportunidad',
        loading: false
      }));
    }
  };

  const filteredOpportunities = state.opportunities.filter(opportunity => {
    const matchesSearch = (opportunity.name || '').toLowerCase().includes(state.searchTerm.toLowerCase()) ||
                         (opportunity.customer_name || '').toLowerCase().includes(state.searchTerm.toLowerCase()) ||
                         (opportunity.contact_person || '').toLowerCase().includes(state.searchTerm.toLowerCase());
    const matchesStage = state.selectedStage === 'all' || opportunity.stage === state.selectedStage;
    const matchesSource = state.selectedSource === 'all' || opportunity.source === state.selectedSource;
    
    return matchesSearch && matchesStage && matchesSource;
  });

  const getStageLabel = (stage: string) => {
    const stages: Record<string, string> = {
      prospecting: 'Prospección',
      qualification: 'Calificación',
      proposal: 'Propuesta',
      negotiation: 'Negociación',
      closed_won: 'Cerrada Ganada',
      closed_lost: 'Cerrada Perdida'
    };
    return stages[stage] || stage;
  };

  const getSourceLabel = (source: string) => {
    const sources: Record<string, string> = {
      direct: 'Directo',
      lead_conversion: 'Conversión de Lead',
      existing_customer: 'Cliente Existente',
      referral: 'Referido',
      marketing: 'Marketing',
      cold_outreach: 'Prospección Fría'
    };
    return sources[source] || source;
  };

  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      prospecting: 'text-gray-600 bg-gray-100',
      qualification: 'text-blue-600 bg-blue-100',
      proposal: 'text-yellow-600 bg-yellow-100',
      negotiation: 'text-orange-600 bg-orange-100',
      closed_won: 'text-green-600 bg-green-100',
      closed_lost: 'text-red-600 bg-red-100'
    };
    return colors[stage] || 'text-gray-600 bg-gray-100';
  };

  const getProbabilityColor = (probability: number) => {
    if (probability >= 75) return 'text-green-600';
    if (probability >= 50) return 'text-yellow-600';
    if (probability >= 25) return 'text-orange-600';
    return 'text-red-600';
  };

  const getOpportunityStats = () => {
    const totalOpportunities = state.opportunities.length;
    const totalValue = state.opportunities.reduce((sum, opp) => sum + opp.value, 0);
    const weightedValue = state.opportunities.reduce((sum, opp) => sum + (opp.value * opp.probability / 100), 0);
    const avgProbability = state.opportunities.reduce((sum, opp) => sum + opp.probability, 0) / Math.max(totalOpportunities, 1);
    const wonOpportunities = state.opportunities.filter(opp => opp.stage === 'closed_won').length;

    return {
      totalOpportunities,
      totalValue,
      weightedValue: Math.round(weightedValue),
      avgProbability: Math.round(avgProbability),
      wonOpportunities
    };
  };

  useEffect(() => {
    fetchOpportunities();
  }, []);

  if (state.loading && state.opportunities.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const stats = getOpportunityStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Oportunidades</h1>
          <p className="text-gray-600">Administra tus oportunidades de venta y pipeline comercial</p>
        </div>
        <Dialog open={state.showCreateDialog} onOpenChange={(open) => setState(prev => ({ ...prev, showCreateDialog: open }))}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Nueva Oportunidad
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Crear Nueva Oportunidad</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="text-sm font-medium">Nombre de la Oportunidad</label>
                <Input
                  value={state.formData.name || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, name: e.target.value }
                  }))}
                  placeholder="Nombre descriptivo de la oportunidad"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Cliente</label>
                <Input
                  value={state.formData.customer_name || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, customer_name: e.target.value }
                  }))}
                  placeholder="Nombre del cliente"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Persona de Contacto</label>
                <Input
                  value={state.formData.contact_person || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, contact_person: e.target.value }
                  }))}
                  placeholder="Nombre del contacto"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Etapa</label>
                <Select value={state.formData.stage || 'prospecting'} onValueChange={(value) => setState(prev => ({
                  ...prev,
                  formData: { ...prev.formData, stage: value }
                }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="prospecting">Prospección</SelectItem>
                    <SelectItem value="qualification">Calificación</SelectItem>
                    <SelectItem value="proposal">Propuesta</SelectItem>
                    <SelectItem value="negotiation">Negociación</SelectItem>
                    <SelectItem value="closed_won">Cerrada Ganada</SelectItem>
                    <SelectItem value="closed_lost">Cerrada Perdida</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Probabilidad (%)</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={state.formData.probability || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, probability: parseInt(e.target.value) || 25 }
                  }))}
                  placeholder="25"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Valor (S/)</label>
                <Input
                  type="number"
                  value={state.formData.value || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, value: parseFloat(e.target.value) || 0 }
                  }))}
                  placeholder="0"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Fecha Esperada de Cierre</label>
                <Input
                  type="date"
                  value={state.formData.expected_close_date || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, expected_close_date: e.target.value }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Fuente</label>
                <Select value={state.formData.source || 'direct'} onValueChange={(value) => setState(prev => ({
                  ...prev,
                  formData: { ...prev.formData, source: value }
                }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="direct">Directo</SelectItem>
                    <SelectItem value="lead_conversion">Conversión de Lead</SelectItem>
                    <SelectItem value="existing_customer">Cliente Existente</SelectItem>
                    <SelectItem value="referral">Referido</SelectItem>
                    <SelectItem value="marketing">Marketing</SelectItem>
                    <SelectItem value="cold_outreach">Prospección Fría</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium">Descripción</label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                  value={state.formData.description || ''}
                  onChange={(e) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, description: e.target.value }
                  }))}
                  placeholder="Descripción detallada de la oportunidad"
                />
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium">Próxima Acción</label>
                <Input
                  value={state.formData.next_action || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, next_action: e.target.value }
                  }))}
                  placeholder="¿Cuál es el siguiente paso?"
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
              <Button onClick={handleCreateOpportunity}>
                Crear Oportunidad
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Briefcase className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Oportunidades</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalOpportunities}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <DollarSign className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Valor Total</p>
                <p className="text-2xl font-bold text-gray-900">S/ {stats.totalValue.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Valor Ponderado</p>
                <p className="text-2xl font-bold text-gray-900">S/ {stats.weightedValue.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Package className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Prob. Promedio</p>
                <p className="text-2xl font-bold text-gray-900">{stats.avgProbability}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Ganadas</p>
                <p className="text-2xl font-bold text-gray-900">{stats.wonOpportunities}</p>
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
                  placeholder="Buscar oportunidades..."
                  value={state.searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={state.selectedStage} onValueChange={(value) => setState(prev => ({ ...prev, selectedStage: value }))}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Etapa" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las etapas</SelectItem>
                <SelectItem value="prospecting">Prospección</SelectItem>
                <SelectItem value="qualification">Calificación</SelectItem>
                <SelectItem value="proposal">Propuesta</SelectItem>
                <SelectItem value="negotiation">Negociación</SelectItem>
                <SelectItem value="closed_won">Cerrada Ganada</SelectItem>
                <SelectItem value="closed_lost">Cerrada Perdida</SelectItem>
              </SelectContent>
            </Select>
            <Select value={state.selectedSource} onValueChange={(value) => setState(prev => ({ ...prev, selectedSource: value }))}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Fuente" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las fuentes</SelectItem>
                <SelectItem value="direct">Directo</SelectItem>
                <SelectItem value="lead_conversion">Conversión de Lead</SelectItem>
                <SelectItem value="existing_customer">Cliente Existente</SelectItem>
                <SelectItem value="referral">Referido</SelectItem>
                <SelectItem value="marketing">Marketing</SelectItem>
                <SelectItem value="cold_outreach">Prospección Fría</SelectItem>
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

      {/* Opportunities Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Oportunidades</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Oportunidad</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Etapa</TableHead>
                <TableHead>Valor</TableHead>
                <TableHead>Probabilidad</TableHead>
                <TableHead>Fecha Esperada</TableHead>
                <TableHead>Fuente</TableHead>
                <TableHead>Próxima Acción</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredOpportunities.map((opportunity) => (
                <TableRow key={opportunity.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{opportunity.name}</div>
                      <div className="text-sm text-gray-500 flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {opportunity.contact_person}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{opportunity.customer_name}</div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStageColor(opportunity.stage)}>
                      {getStageLabel(opportunity.stage)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">S/ {opportunity.value.toLocaleString()}</div>
                  </TableCell>
                  <TableCell>
                    <div className={`font-medium ${getProbabilityColor(opportunity.probability)}`}>
                      {opportunity.probability}%
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <Calendar className="h-3 w-3" />
                      {new Date(opportunity.expected_close_date).toLocaleDateString()}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {getSourceLabel(opportunity.source)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <Clock className="h-3 w-3" />
                      <span className="truncate max-w-32">{opportunity.next_action}</span>
                    </div>
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
                          editingOpportunity: opportunity, 
                          formData: opportunity 
                        }))}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => handleDeleteOpportunity(opportunity.id)}
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
      {state.editingOpportunity && (
        <Dialog open={!!state.editingOpportunity} onOpenChange={(open) => {
          if (!open) setState(prev => ({ ...prev, editingOpportunity: null, formData: {} }));
        }}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Editar Oportunidad</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Etapa</label>
                <Select value={state.formData.stage || 'prospecting'} onValueChange={(value) => setState(prev => ({
                  ...prev,
                  formData: { ...prev.formData, stage: value }
                }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="prospecting">Prospección</SelectItem>
                    <SelectItem value="qualification">Calificación</SelectItem>
                    <SelectItem value="proposal">Propuesta</SelectItem>
                    <SelectItem value="negotiation">Negociación</SelectItem>
                    <SelectItem value="closed_won">Cerrada Ganada</SelectItem>
                    <SelectItem value="closed_lost">Cerrada Perdida</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Probabilidad (%)</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={state.formData.probability || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, probability: parseInt(e.target.value) || 25 }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Valor (S/)</label>
                <Input
                  type="number"
                  value={state.formData.value || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, value: parseFloat(e.target.value) || 0 }
                  }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Fecha Esperada</label>
                <Input
                  type="date"
                  value={state.formData.expected_close_date || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, expected_close_date: e.target.value }
                  }))}
                />
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium">Próxima Acción</label>
                <Input
                  value={state.formData.next_action || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, next_action: e.target.value }
                  }))}
                />
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium">Descripción</label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                  value={state.formData.description || ''}
                  onChange={(e) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, description: e.target.value }
                  }))}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button 
                variant="outline" 
                onClick={() => setState(prev => ({ ...prev, editingOpportunity: null, formData: {} }))}
              >
                Cancelar
              </Button>
              <Button onClick={() => handleUpdateOpportunity(state.editingOpportunity!.id)}>
                Guardar Cambios
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default OpportunitiesPage;