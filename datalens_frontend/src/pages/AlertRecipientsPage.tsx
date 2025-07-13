import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Alert,
  AlertDescription,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Input
} from '../components/ui';
import {
  Users,
  Mail,
  Phone,
  Settings,
  Edit,
  Trash2,
  CheckCircle,
  X,
  Bell,
  Search,
  Download,
  Upload,
  Filter,
  Eye,
  Activity,
  AlertTriangle
} from '../components/ui/icons';
import { createOptimizedHeaders, validateAndCleanToken } from '../services/api';
import './AlertRecipientsPage.css';

interface AlertRecipient {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  notification_type: 'email' | 'whatsapp' | 'both';
  receive_all_alerts: boolean;
  receive_critical_only: boolean;
  receive_high_and_critical: boolean;
  alert_types: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AlertRecipientStats {
  total: number;
  active: number;
  inactive: number;
  email_only: number;
  whatsapp_only: number;
  both: number;
  receive_all: number;
  critical_only: number;
  high_and_critical: number;
}

const AlertRecipientsPage: React.FC = () => {
  const [recipients, setRecipients] = useState<AlertRecipient[]>([]);
  const [filteredRecipients, setFilteredRecipients] = useState<AlertRecipient[]>([]);
  const [stats, setStats] = useState<AlertRecipientStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingRecipient, setEditingRecipient] = useState<AlertRecipient | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [filterType, setFilterType] = useState<'all' | 'email' | 'whatsapp' | 'both'>('all');

  // Estados para el formulario
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    notification_type: 'email' as 'email' | 'whatsapp' | 'both',
    receive_all_alerts: true,
    receive_critical_only: false,
    receive_high_and_critical: false,
    alert_types: [] as string[],
    is_active: true
  });

  useEffect(() => {
    // **COMENTADO TEMPORALMENTE: La limpieza automática está interfiriendo**
    // const cleanupTokens = () => {
    //   console.log('🧹 Limpiando tokens corruptos...');
    //   
    //   // Verificar tamaño de tokens almacenados
    //   const accessToken = localStorage.getItem('access_token');
    //   const refreshToken = localStorage.getItem('refresh_token');
    //   const user = localStorage.getItem('user');
    //   
    //   console.log('Token sizes:', {
    //     access: accessToken?.length || 0,
    //     refresh: refreshToken?.length || 0,
    //     user: user?.length || 0
    //   });
    //   
    //   // Si cualquier token es excesivamente grande, limpiar todo
    //   const maxSize = 1500; // Reducir límite
    //   if (
    //     (accessToken && accessToken.length > maxSize) ||
    //     (refreshToken && refreshToken.length > maxSize) ||
    //     (user && user.length > 2000)
    //   ) {
    //     console.warn('🚨 Tokens excesivamente grandes detectados, limpiando...');
    //     localStorage.clear();
    //     sessionStorage.clear();
    //     window.location.reload();
    //     return false;
    //   }
    //   
    //   return true;
    // };
    
    // Cargar datos directamente sin limpieza automática
    loadRecipients();
    loadStats();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [recipients, searchTerm, filterStatus, filterType]);

  const loadRecipients = async () => {
    console.log('🔍 [DEBUG] Iniciando loadRecipients...');
    
    try {
      // **NUEVO: Verificar tokens antes de hacer la petición**
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      const user = localStorage.getItem('user');
      
      console.log('🔍 [DEBUG] Tokens disponibles:', {
        hasAccessToken: !!accessToken,
        hasRefreshToken: !!refreshToken,
        hasUser: !!user,
        accessTokenLength: accessToken?.length || 0,
        accessTokenPreview: accessToken?.substring(0, 50) + '...'
      });
      
      // **NUEVO: Usar axios con la configuración optimizada**
      const axios = (await import('axios')).default;
      
      const headers = createOptimizedHeaders(true);
      console.log('🔍 [DEBUG] Headers creados:', headers);
      
      console.log('🔍 [DEBUG] Haciendo petición a:', 'http://localhost:8080/api/alerts/recipients/');
      
      const response = await axios.get('http://localhost:8080/api/alerts/recipients/', {
        headers: headers,
        timeout: 10000
      });

      console.log('🔍 [DEBUG] Respuesta recibida:', {
        status: response.status,
        statusText: response.statusText,
        dataType: typeof response.data,
        dataKeys: Object.keys(response.data || {}),
        fullData: response.data,
        // NUEVO: Detalles adicionales de la respuesta
        count: response.data.count,
        results: response.data.results,
        resultsLength: response.data.results?.length || 0,
        next: response.data.next,
        previous: response.data.previous
      });

      // **NUEVO: Detectar si la respuesta indica token expirado**
      if (response.data.detail && response.data.code === 'token_not_valid') {
        console.error('🚨 [ERROR] Token expirado detectado en respuesta:', response.data);
        localStorage.clear();
        sessionStorage.clear();
        alert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
        window.location.href = '/login';
        return;
      }

      const recipientsData = response.data.results || response.data;
      console.log('🔍 [DEBUG] Datos de destinatarios procesados:', {
        isArray: Array.isArray(recipientsData),
        length: recipientsData?.length || 0,
        firstItem: recipientsData?.[0] || null
      });

      setRecipients(recipientsData);
      console.log('🔍 [DEBUG] setRecipients llamado con:', recipientsData);
      
    } catch (err: any) {
      console.error('🚨 [ERROR] Error en loadRecipients:', {
        errorMessage: err.message,
        errorStatus: err.response?.status,
        errorData: err.response?.data,
        errorHeaders: err.response?.headers,
        fullError: err
      });
      
      // **NUEVO: Manejar token expirado también en errores**
      if (err.response?.status === 401 || err.response?.data?.code === 'token_not_valid') {
        console.error('🚨 [ERROR] Token expirado - redirigiendo al login');
        localStorage.clear();
        sessionStorage.clear();
        alert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
        window.location.href = '/login';
        return;
      }
      
      if (err.response?.status === 431) {
        console.warn('🚨 Error 431 detectado, limpiando storage...');
        localStorage.clear();
        sessionStorage.clear();
        window.location.reload();
        return;
      }
      
      setError('Error al cargar destinatarios: ' + (err.response?.data?.detail || err.message));
      console.error('Error loading recipients:', err);
    } finally {
      console.log('🔍 [DEBUG] loadRecipients finalizando, setLoading(false)');
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      // **NUEVO: Usar axios con la configuración optimizada**
      const axios = (await import('axios')).default;
      
      const response = await axios.get('http://localhost:8080/api/alerts/recipients/stats/', {
        headers: createOptimizedHeaders(true),
        timeout: 10000
      });

      setStats(response.data);
    } catch (err: any) {
      if (err.response?.status === 431) {
        console.warn('🚨 Error 431 detectado en stats, limpiando storage...');
        localStorage.clear();
        sessionStorage.clear();
        window.location.reload();
        return;
      }
      
      console.error('Error loading stats:', err);
      setError('Error al cargar estadísticas');
    }
  };

  const applyFilters = () => {
    console.log('🔍 [DEBUG] Aplicando filtros...');
    console.log('🔍 [DEBUG] recipients:', recipients);
    console.log('🔍 [DEBUG] recipients.length:', recipients.length);
    console.log('🔍 [DEBUG] searchTerm:', searchTerm);
    console.log('🔍 [DEBUG] filterStatus:', filterStatus);
    console.log('🔍 [DEBUG] filterType:', filterType);
    
    let filtered = recipients;

    // Filtro de búsqueda
    if (searchTerm) {
      filtered = filtered.filter(recipient =>
        recipient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        recipient.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        recipient.phone?.includes(searchTerm)
      );
      console.log('🔍 [DEBUG] Después de filtro búsqueda:', filtered.length);
    }

    // Filtro de estado
    if (filterStatus !== 'all') {
      filtered = filtered.filter(recipient =>
        filterStatus === 'active' ? recipient.is_active : !recipient.is_active
      );
      console.log('🔍 [DEBUG] Después de filtro estado:', filtered.length);
    }

    // Filtro de tipo de notificación
    if (filterType !== 'all') {
      filtered = filtered.filter(recipient => recipient.notification_type === filterType);
      console.log('🔍 [DEBUG] Después de filtro tipo:', filtered.length);
    }

    console.log('🔍 [DEBUG] filteredRecipients final:', filtered);
    console.log('🔍 [DEBUG] filteredRecipients.length final:', filtered.length);
    
    setFilteredRecipients(filtered);
    console.log('🔍 [DEBUG] setFilteredRecipients llamado con:', filtered);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      phone: '',
      notification_type: 'email',
      receive_all_alerts: true,
      receive_critical_only: false,
      receive_high_and_critical: false,
      alert_types: [],
      is_active: true
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // **NUEVO: Usar axios con headers optimizados**
      const axios = (await import('axios')).default;
      
      const url = editingRecipient 
        ? `/alerts/recipients/${editingRecipient.id}/`
        : '/alerts/recipients/';
      
      const method = editingRecipient ? 'put' : 'post';

      const response = await axios[method](`http://localhost:8080${url}`, formData, {
        headers: createOptimizedHeaders(true),
        timeout: 10000
      });

      await loadRecipients();
      await loadStats();
      setShowAddModal(false);
      setEditingRecipient(null);
      resetForm();
      
    } catch (err: any) {
      if (err.response?.status === 431) {
        console.warn('🚨 Error 431 en submit, limpiando storage...');
        localStorage.clear();
        sessionStorage.clear();
        window.location.reload();
        return;
      }
      
      setError(err.response?.data?.detail || err.message || 'Error al guardar destinatario');
    }
  };

  const handleEdit = (recipient: AlertRecipient) => {
    setEditingRecipient(recipient);
    setFormData({
      name: recipient.name,
      email: recipient.email || '',
      phone: recipient.phone || '',
      notification_type: recipient.notification_type,
      receive_all_alerts: recipient.receive_all_alerts,
      receive_critical_only: recipient.receive_critical_only,
      receive_high_and_critical: recipient.receive_high_and_critical,
      alert_types: recipient.alert_types,
      is_active: recipient.is_active
    });
    setShowAddModal(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este destinatario?')) return;

    try {
      // **NUEVO: Usar axios con headers optimizados**
      const axios = (await import('axios')).default;
      
      await axios.delete(`http://localhost:8080/api/alerts/recipients/${id}/`, {
        headers: createOptimizedHeaders(true),
        timeout: 10000
      });

      await loadRecipients();
      await loadStats();
    } catch (err: any) {
      if (err.response?.status === 431) {
        console.warn('🚨 Error 431 en delete, limpiando storage...');
        localStorage.clear();
        sessionStorage.clear();
        window.location.reload();
        return;
      }
      
      setError('Error al eliminar destinatario');
    }
  };

  const toggleStatus = async (id: number) => {
    try {
      // **NUEVO: Usar axios con headers optimizados**
      const axios = (await import('axios')).default;
      
      await axios.post(`http://localhost:8080/api/alerts/recipients/${id}/toggle_status/`, {}, {
        headers: createOptimizedHeaders(true),
        timeout: 10000
      });

      await loadRecipients();
      await loadStats();
    } catch (err: any) {
      if (err.response?.status === 431) {
        console.warn('🚨 Error 431 en toggle, limpiando storage...');
        localStorage.clear();
        sessionStorage.clear();
        window.location.reload();
        return;
      }
      
      setError('Error al cambiar estado del destinatario');
    }
  };

  const sendTestNotification = async (id: number, type: 'email' | 'whatsapp' | 'both') => {
    try {
      // **NUEVO: Usar axios con headers optimizados**
      const axios = (await import('axios')).default;
      
      const response = await axios.post(`http://localhost:8080/api/alerts/recipients/${id}/test_notification/`, 
        { type }, 
        {
          headers: createOptimizedHeaders(true),
          timeout: 10000
        }
      );

      alert(response.data.message || 'Notificación de prueba enviada');
    } catch (err: any) {
      if (err.response?.status === 431) {
        console.warn('🚨 Error 431 en test notification, limpiando storage...');
        localStorage.clear();
        sessionStorage.clear();
        window.location.reload();
        return;
      }
      
      setError('Error al enviar notificación de prueba');
    }
  };

  const exportRecipients = () => {
    const csvContent = [
      ['Nombre', 'Email', 'Teléfono', 'Tipo', 'Estado', 'Configuración'],
      ...filteredRecipients.map(r => [
        r.name,
        r.email || '',
        r.phone || '',
        r.notification_type,
        r.is_active ? 'Activo' : 'Inactivo',
        r.receive_all_alerts ? 'Todas' : r.receive_critical_only ? 'Solo críticas' : 'Personalizada'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'destinatarios_alertas.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto mb-6"></div>
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300">Cargando destinatarios...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 via-blue-800 to-indigo-800 dark:from-slate-100 dark:via-blue-200 dark:to-indigo-200 bg-clip-text text-transparent">
                Gestión de Destinatarios
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-2">
                Administra quién recibe las alertas del sistema
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="outline" onClick={exportRecipients}>
                <Download className="h-4 w-4 mr-2" />
                Exportar
              </Button>
              <Button onClick={() => setShowAddModal(true)}>
                <Users className="h-4 w-4 mr-2" />
                Agregar Destinatario
              </Button>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <X className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
            <Button variant="ghost" size="sm" onClick={() => setError(null)} className="ml-auto">
              <X className="h-4 w-4" />
            </Button>
          </Alert>
        )}

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Total</p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stats.total}</p>
                  </div>
                  <Users className="h-8 w-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Activos</p>
                    <p className="text-2xl font-bold text-green-600">{stats.active}</p>
                  </div>
                  <CheckCircle className="h-8 w-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Solo Email</p>
                    <p className="text-2xl font-bold text-blue-600">{stats.email_only}</p>
                  </div>
                  <Mail className="h-8 w-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">WhatsApp</p>
                    <p className="text-2xl font-bold text-green-600">{stats.whatsapp_only + stats.both}</p>
                  </div>
                  <Phone className="h-8 w-8 text-green-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                  <Input
                    placeholder="Buscar por nombre, email o teléfono..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              <Select value={filterStatus} onValueChange={(value) => setFilterStatus(value as any)}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Estado" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="active">Activos</SelectItem>
                  <SelectItem value="inactive">Inactivos</SelectItem>
                </SelectContent>
              </Select>

              <Select value={filterType} onValueChange={(value) => setFilterType(value as any)}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos los tipos</SelectItem>
                  <SelectItem value="email">Solo Email</SelectItem>
                  <SelectItem value="whatsapp">Solo WhatsApp</SelectItem>
                  <SelectItem value="both">Email y WhatsApp</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Recipients List */}
        <div className="grid gap-6">
          {filteredRecipients.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Users className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  No hay destinatarios
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-6">
                  {recipients.length === 0 
                    ? 'Aún no has agregado ningún destinatario de alertas'
                    : 'No se encontraron destinatarios con los filtros aplicados'
                  }
                </p>
                <Button onClick={() => setShowAddModal(true)}>
                  <Users className="h-4 w-4 mr-2" />
                  Agregar Primer Destinatario
                </Button>
              </CardContent>
            </Card>
          ) : (
            filteredRecipients.map((recipient) => (
              <Card key={recipient.id} className={`transition-all duration-200 ${!recipient.is_active ? 'opacity-60' : ''}`}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex-shrink-0">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                          recipient.is_active 
                            ? 'bg-green-100 dark:bg-green-900/50' 
                            : 'bg-gray-100 dark:bg-gray-700'
                        }`}>
                          {recipient.is_active ? (
                            <Users className="h-6 w-6 text-green-600 dark:text-green-400" />
                          ) : (
                            <Users className="h-6 w-6 text-gray-400" />
                          )}
                        </div>
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                            {recipient.name}
                          </h3>
                          <Badge variant={recipient.is_active ? 'primary' : 'secondary'}>
                            {recipient.is_active ? 'Activo' : 'Inactivo'}
                          </Badge>
                          <Badge variant="outline">
                            {recipient.notification_type === 'both' ? 'Email + WhatsApp' : 
                             recipient.notification_type === 'email' ? 'Email' : 'WhatsApp'}
                          </Badge>
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                          {recipient.email && (
                            <div className="flex items-center gap-1">
                              <Mail className="h-4 w-4" />
                              <span>{recipient.email}</span>
                            </div>
                          )}
                          {recipient.phone && (
                            <div className="flex items-center gap-1">
                              <Phone className="h-4 w-4" />
                              <span>{recipient.phone}</span>
                            </div>
                          )}
                        </div>
                        
                        <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                          {recipient.receive_all_alerts ? (
                            <span className="inline-flex items-center gap-1">
                              <Bell className="h-3 w-3" />
                              Recibe todas las alertas
                            </span>
                          ) : recipient.receive_critical_only ? (
                            <span className="inline-flex items-center gap-1 text-red-600">
                              <Bell className="h-3 w-3" />
                              Solo alertas críticas
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-yellow-600">
                              <Bell className="h-3 w-3" />
                              Alertas personalizadas
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => sendTestNotification(recipient.id, recipient.notification_type)}
                      >
                        <Mail className="h-4 w-4" />
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleStatus(recipient.id)}
                      >
                        {recipient.is_active ? (
                          <Activity className="h-4 w-4" />
                        ) : (
                          <Activity className="h-4 w-4" />
                        )}
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(recipient)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(recipient.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>
                {editingRecipient ? 'Editar Destinatario' : 'Agregar Destinatario'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Nombre *</label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="Nombre completo"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Tipo de Notificación</label>
                  <Select 
                    value={formData.notification_type} 
                    onValueChange={(value) => setFormData({...formData, notification_type: value as any})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="email">Solo Email</SelectItem>
                      <SelectItem value="whatsapp">Solo WhatsApp</SelectItem>
                      <SelectItem value="both">Email y WhatsApp</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {(formData.notification_type === 'email' || formData.notification_type === 'both') && (
                  <div>
                    <label className="block text-sm font-medium mb-1">Email *</label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      placeholder="email@ejemplo.com"
                      required
                    />
                  </div>
                )}

                {(formData.notification_type === 'whatsapp' || formData.notification_type === 'both') && (
                  <div>
                    <label className="block text-sm font-medium mb-1">Teléfono WhatsApp *</label>
                    <Input
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      placeholder="+51999999999"
                      required
                    />
                  </div>
                )}

                <div className="space-y-3">
                  <label className="block text-sm font-medium">Configuración de Alertas</label>
                  
                  <div className="space-y-2">
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="alertConfig"
                        checked={formData.receive_all_alerts}
                        onChange={() => setFormData({
                          ...formData,
                          receive_all_alerts: true,
                          receive_critical_only: false,
                          receive_high_and_critical: false
                        })}
                      />
                      <span className="text-sm">Recibir todas las alertas</span>
                    </label>
                    
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="alertConfig"
                        checked={formData.receive_critical_only}
                        onChange={() => setFormData({
                          ...formData,
                          receive_all_alerts: false,
                          receive_critical_only: true,
                          receive_high_and_critical: false
                        })}
                      />
                      <span className="text-sm">Solo alertas críticas</span>
                    </label>
                    
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="alertConfig"
                        checked={formData.receive_high_and_critical}
                        onChange={() => setFormData({
                          ...formData,
                          receive_all_alerts: false,
                          receive_critical_only: false,
                          receive_high_and_critical: true
                        })}
                      />
                      <span className="text-sm">Alertas altas y críticas</span>
                    </label>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  />
                  <label className="text-sm">Destinatario activo</label>
                </div>

                <div className="flex gap-2 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowAddModal(false);
                      setEditingRecipient(null);
                      resetForm();
                    }}
                    className="flex-1"
                  >
                    Cancelar
                  </Button>
                  <Button type="submit" className="flex-1">
                    {editingRecipient ? 'Actualizar' : 'Agregar'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AlertRecipientsPage;