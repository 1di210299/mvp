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
  Target,
  Plus,
  Search,
  Eye,
  Edit,
  Trash2,
  Mail,
  Phone,
  MapPin,
  Calendar,
  TrendingUp,
  Star,
  User,
  ArrowRight,
  AlertTriangle
} from '../components/ui/icons';
import { inventoryService } from '../services/api';

interface Lead {
  id: number;
  name: string;
  email: string;
  phone: string;
  company: string;
  position: string;
  source: string;
  status: string;
  score: number;
  estimated_value: number;
  notes: string;
  created_at: string;
  last_contact: string;
  next_followup: string;
}

interface LeadsPageState {
  leads: Lead[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  selectedSource: string;
  selectedStatus: string;
  showCreateDialog: boolean;
  showConvertDialog: boolean;
  editingLead: Lead | null;
  convertingLead: Lead | null;
  formData: Partial<Lead>;
}

const LeadsPage: React.FC = () => {
  const [state, setState] = useState<LeadsPageState>({
    leads: [],
    loading: true,
    error: null,
    searchTerm: '',
    selectedSource: 'all',
    selectedStatus: 'all',
    showCreateDialog: false,
    showConvertDialog: false,
    editingLead: null,
    convertingLead: null,
    formData: {}
  });

  const fetchLeads = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const response = await inventoryService.getLeads();
      const leadsData = response.results || response || [];
      setState(prev => ({ ...prev, leads: leadsData, loading: false }));
    } catch (err) {
      console.error('Error fetching leads:', err);
      
      // Fallback a datos simulados
      const mockLeads: Lead[] = [
        {
          id: 1,
          name: 'Carlos Mendoza',
          email: 'carlos.mendoza@empresa.com',
          phone: '+51 999 456 789',
          company: 'TechSolutions Perú',
          position: 'Gerente de Compras',
          source: 'website',
          status: 'qualified',
          score: 85,
          estimated_value: 15000,
          notes: 'Interesado en soluciones de inventario',
          created_at: '2024-01-10T09:00:00Z',
          last_contact: '2024-01-15T14:30:00Z',
          next_followup: '2024-01-20T10:00:00Z'
        },
        {
          id: 2,
          name: 'Ana Rodriguez',
          email: 'a.rodriguez@startup.pe',
          phone: '+51 987 321 654',
          company: 'StartupPE',
          position: 'CEO',
          source: 'referral',
          status: 'contacted',
          score: 70,
          estimated_value: 8000,
          notes: 'Startup en crecimiento, necesita sistema escalable',
          created_at: '2024-01-12T11:20:00Z',
          last_contact: '2024-01-16T16:45:00Z',
          next_followup: '2024-01-22T09:30:00Z'
        },
        {
          id: 3,
          name: 'Miguel Torres',
          email: 'mtorres@comercial.com',
          phone: '+51 555 987 123',
          company: 'Comercial Lima SAC',
          position: 'Director Operaciones',
          source: 'social_media',
          status: 'new',
          score: 45,
          estimated_value: 25000,
          notes: 'Empresa establecida buscando modernizar procesos',
          created_at: '2024-01-14T13:15:00Z',
          last_contact: '2024-01-14T13:15:00Z',
          next_followup: '2024-01-18T15:00:00Z'
        }
      ];
      
      setState(prev => ({
        ...prev,
        leads: mockLeads,
        loading: false,
        error: 'Conectado con datos simulados - API no disponible'
      }));
    }
  };

  const handleCreateLead = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      
      const leadData = {
        name: state.formData.name,
        email: state.formData.email,
        phone: state.formData.phone,
        company: state.formData.company,
        position: state.formData.position,
        source: state.formData.source || 'website',
        status: 'new',
        score: state.formData.score || 50,
        estimated_value: state.formData.estimated_value || 0,
        notes: state.formData.notes || ''
      };

      await inventoryService.createLead(leadData);
      await fetchLeads();
      
      setState(prev => ({
        ...prev,
        showCreateDialog: false,
        formData: {},
        loading: false
      }));
    } catch (err) {
      console.error('Error creating lead:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al crear lead',
        loading: false
      }));
    }
  };

  const handleUpdateLead = async (id: number) => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      await inventoryService.updateLead(id, state.formData);
      await fetchLeads();
      
      setState(prev => ({
        ...prev,
        editingLead: null,
        formData: {},
        loading: false
      }));
    } catch (err) {
      console.error('Error updating lead:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al actualizar lead',
        loading: false
      }));
    }
  };

  const handleConvertToCustomer = async (lead: Lead) => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      
      const customerData = {
        name: lead.company || lead.name,
        email: lead.email,
        phone: lead.phone,
        customer_type: 'corporate',
        status: 'active',
        notes: `Convertido desde lead: ${lead.notes}`
      };

      await inventoryService.convertLeadToCustomer(lead.id, customerData);
      await fetchLeads();
      
      setState(prev => ({
        ...prev,
        showConvertDialog: false,
        convertingLead: null,
        loading: false
      }));
    } catch (err) {
      console.error('Error converting lead:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al convertir lead a cliente',
        loading: false
      }));
    }
  };

  const handleDeleteLead = async (id: number) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este lead?')) {
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true }));
      await inventoryService.deleteLead(id);
      await fetchLeads();
    } catch (err) {
      console.error('Error deleting lead:', err);
      setState(prev => ({
        ...prev,
        error: 'Error al eliminar lead',
        loading: false
      }));
    }
  };

  const filteredLeads = state.leads.filter(lead => {
    const matchesSearch = (lead.name || '').toLowerCase().includes((state.searchTerm || '').toLowerCase()) ||
                         (lead.company || '').toLowerCase().includes((state.searchTerm || '').toLowerCase()) ||
                         (lead.email || '').toLowerCase().includes((state.searchTerm || '').toLowerCase());
    const matchesSource = state.selectedSource === 'all' || lead.source === state.selectedSource;
    const matchesStatus = state.selectedStatus === 'all' || lead.status === state.selectedStatus;
    
    return matchesSearch && matchesSource && matchesStatus;
  });

  const getSourceLabel = (source: string) => {
    const sources: Record<string, string> = {
      website: 'Sitio Web',
      referral: 'Referido',
      social_media: 'Redes Sociales',
      cold_call: 'Llamada Fría',
      event: 'Evento',
      email: 'Email Marketing'
    };
    return sources[source] || source;
  };

  const getStatusLabel = (status: string) => {
    const statuses: Record<string, string> = {
      new: 'Nuevo',
      contacted: 'Contactado',
      qualified: 'Calificado',
      proposal: 'Propuesta',
      negotiation: 'Negociación',
      won: 'Ganado',
      lost: 'Perdido'
    };
    return statuses[status] || status;
  };

  const getStatusBadgeVariant = (status: string) => {
    const variants: Record<string, string> = {
      new: 'secondary',
      contacted: 'outline',
      qualified: 'default',
      proposal: 'warning',
      negotiation: 'info',
      won: 'success',
      lost: 'destructive'
    };
    return variants[status] || 'secondary';
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getLeadStats = () => {
    const totalLeads = state.leads.length;
    const qualifiedLeads = state.leads.filter(l => l.status === 'qualified').length;
    const totalValue = state.leads.reduce((sum, l) => sum + (l.estimated_value || 0), 0);
    const avgScore = state.leads.reduce((sum, l) => sum + (l.score || 0), 0) / Math.max(totalLeads, 1);

    return {
      totalLeads,
      qualifiedLeads,
      totalValue,
      avgScore: Math.round(avgScore)
    };
  };

  useEffect(() => {
    fetchLeads();
  }, []);

  if (state.loading && state.leads.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const stats = getLeadStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Leads</h1>
          <p className="text-gray-600">Administra tus leads y convierte prospectos en clientes</p>
        </div>
        <Dialog open={state.showCreateDialog} onOpenChange={(open) => setState(prev => ({ ...prev, showCreateDialog: open }))}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Nuevo Lead
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Lead</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Nombre Completo</label>
                <Input
                  value={state.formData.name || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, name: e.target.value }
                  }))}
                  placeholder="Nombre del lead"
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
                <label className="text-sm font-medium">Empresa</label>
                <Input
                  value={state.formData.company || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, company: e.target.value }
                  }))}
                  placeholder="Nombre de la empresa"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Cargo</label>
                <Input
                  value={state.formData.position || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, position: e.target.value }
                  }))}
                  placeholder="Cargo en la empresa"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Fuente</label>
                <Select value={state.formData.source || 'website'} onValueChange={(value) => setState(prev => ({
                  ...prev,
                  formData: { ...prev.formData, source: value }
                }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="website">Sitio Web</SelectItem>
                    <SelectItem value="referral">Referido</SelectItem>
                    <SelectItem value="social_media">Redes Sociales</SelectItem>
                    <SelectItem value="cold_call">Llamada Fría</SelectItem>
                    <SelectItem value="event">Evento</SelectItem>
                    <SelectItem value="email">Email Marketing</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Valor Estimado (S/)</label>
                <Input
                  type="number"
                  value={state.formData.estimated_value || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, estimated_value: parseFloat(e.target.value) || 0 }
                  }))}
                  placeholder="0"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Puntuación (1-100)</label>
                <Input
                  type="number"
                  min="1"
                  max="100"
                  value={state.formData.score || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, score: parseInt(e.target.value) || 50 }
                  }))}
                  placeholder="50"
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
                  placeholder="Notas adicionales sobre el lead"
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
              <Button onClick={handleCreateLead}>
                Crear Lead
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Target className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Leads</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalLeads}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Leads Calificados</p>
                <p className="text-2xl font-bold text-gray-900">{stats.qualifiedLeads}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Star className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Puntuación Promedio</p>
                <p className="text-2xl font-bold text-gray-900">{stats.avgScore}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Target className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Valor Estimado</p>
                <p className="text-2xl font-bold text-gray-900">S/ {stats.totalValue.toLocaleString()}</p>
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
                  placeholder="Buscar leads..."
                  value={state.searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={state.selectedSource} onValueChange={(value) => setState(prev => ({ ...prev, selectedSource: value }))}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Fuente" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las fuentes</SelectItem>
                <SelectItem value="website">Sitio Web</SelectItem>
                <SelectItem value="referral">Referido</SelectItem>
                <SelectItem value="social_media">Redes Sociales</SelectItem>
                <SelectItem value="cold_call">Llamada Fría</SelectItem>
                <SelectItem value="event">Evento</SelectItem>
                <SelectItem value="email">Email Marketing</SelectItem>
              </SelectContent>
            </Select>
            <Select value={state.selectedStatus} onValueChange={(value) => setState(prev => ({ ...prev, selectedStatus: value }))}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los estados</SelectItem>
                <SelectItem value="new">Nuevo</SelectItem>
                <SelectItem value="contacted">Contactado</SelectItem>
                <SelectItem value="qualified">Calificado</SelectItem>
                <SelectItem value="proposal">Propuesta</SelectItem>
                <SelectItem value="negotiation">Negociación</SelectItem>
                <SelectItem value="won">Ganado</SelectItem>
                <SelectItem value="lost">Perdido</SelectItem>
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

      {/* Leads Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Leads</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Lead</TableHead>
                <TableHead>Contacto</TableHead>
                <TableHead>Empresa</TableHead>
                <TableHead>Fuente</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Puntuación</TableHead>
                <TableHead>Valor Estimado</TableHead>
                <TableHead>Último Contacto</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLeads.map((lead) => (
                <TableRow key={lead.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{lead.name}</div>
                      <div className="text-sm text-gray-500">{lead.position}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1 text-sm">
                        <Mail className="h-3 w-3" />
                        {lead.email}
                      </div>
                      <div className="flex items-center gap-1 text-sm">
                        <Phone className="h-3 w-3" />
                        {lead.phone}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {lead.company}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {getSourceLabel(lead.source)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadgeVariant(lead.status) as any}>
                      {getStatusLabel(lead.status)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className={`font-medium ${getScoreColor(lead.score)}`}>
                      {lead.score}/100
                    </div>
                  </TableCell>
                  <TableCell>S/ {(lead.estimated_value || 0).toLocaleString()}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <Calendar className="h-3 w-3" />
                      {new Date(lead.last_contact).toLocaleDateString()}
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
                          editingLead: lead, 
                          formData: lead 
                        }))}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => setState(prev => ({ 
                          ...prev, 
                          showConvertDialog: true, 
                          convertingLead: lead 
                        }))}
                        title="Convertir a cliente"
                      >
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => handleDeleteLead(lead.id)}
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
      {state.editingLead && (
        <Dialog open={!!state.editingLead} onOpenChange={(open) => {
          if (!open) setState(prev => ({ ...prev, editingLead: null, formData: {} }));
        }}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Editar Lead</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Estado</label>
                <Select value={state.formData.status || 'new'} onValueChange={(value) => setState(prev => ({
                  ...prev,
                  formData: { ...prev.formData, status: value }
                }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="new">Nuevo</SelectItem>
                    <SelectItem value="contacted">Contactado</SelectItem>
                    <SelectItem value="qualified">Calificado</SelectItem>
                    <SelectItem value="proposal">Propuesta</SelectItem>
                    <SelectItem value="negotiation">Negociación</SelectItem>
                    <SelectItem value="won">Ganado</SelectItem>
                    <SelectItem value="lost">Perdido</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Puntuación</label>
                <Input
                  type="number"
                  min="1"
                  max="100"
                  value={state.formData.score || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setState(prev => ({
                    ...prev,
                    formData: { ...prev.formData, score: parseInt(e.target.value) || 50 }
                  }))}
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
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button 
                variant="outline" 
                onClick={() => setState(prev => ({ ...prev, editingLead: null, formData: {} }))}
              >
                Cancelar
              </Button>
              <Button onClick={() => handleUpdateLead(state.editingLead!.id)}>
                Guardar Cambios
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Convert Dialog */}
      {state.convertingLead && (
        <Dialog open={state.showConvertDialog} onOpenChange={(open) => {
          if (!open) setState(prev => ({ ...prev, showConvertDialog: false, convertingLead: null }));
        }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Convertir Lead a Cliente</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p>¿Estás seguro de que deseas convertir este lead a cliente?</p>
              <div className="bg-gray-50 p-4 rounded-md">
                <p><strong>Lead:</strong> {state.convertingLead.name}</p>
                <p><strong>Empresa:</strong> {state.convertingLead.company}</p>
                <p><strong>Email:</strong> {state.convertingLead.email}</p>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button 
                variant="outline" 
                onClick={() => setState(prev => ({ ...prev, showConvertDialog: false, convertingLead: null }))}
              >
                Cancelar
              </Button>
              <Button onClick={() => handleConvertToCustomer(state.convertingLead!)}>
                Convertir a Cliente
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default LeadsPage;