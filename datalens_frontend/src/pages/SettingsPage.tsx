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
  SelectValue
} from '../components/ui';
import {
  Settings,
  User,
  Bell,
  Shield,
  Database,
  Mail,
  Smartphone,
  Globe,
  Key,
  AlertTriangle,
  Check,
  Save
} from '../components/ui/icons';

interface SettingsPageState {
  loading: boolean;
  error: string | null;
  successMessage: string | null;
  activeTab: string;
  userSettings: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    language: string;
    timezone: string;
  };
  notificationSettings: {
    emailNotifications: boolean;
    smsNotifications: boolean;
    lowStockAlerts: boolean;
    dailyReports: boolean;
    weeklyReports: boolean;
  };
  securitySettings: {
    twoFactorEnabled: boolean;
    passwordExpiry: string;
    sessionTimeout: string;
  };
  systemSettings: {
    currency: string;
    dateFormat: string;
    lowStockThreshold: number;
    autoReorder: boolean;
  };
}

const SettingsPage: React.FC = () => {
  const [state, setState] = useState<SettingsPageState>({
    loading: true,
    error: null,
    successMessage: null,
    activeTab: 'profile',
    userSettings: {
      firstName: 'Juan',
      lastName: 'Pérez',
      email: 'juan.perez@empresa.com',
      phone: '+51 999 123 456',
      language: 'es',
      timezone: 'America/Lima'
    },
    notificationSettings: {
      emailNotifications: true,
      smsNotifications: false,
      lowStockAlerts: true,
      dailyReports: true,
      weeklyReports: false
    },
    securitySettings: {
      twoFactorEnabled: false,
      passwordExpiry: '90',
      sessionTimeout: '30'
    },
    systemSettings: {
      currency: 'PEN',
      dateFormat: 'DD/MM/YYYY',
      lowStockThreshold: 10,
      autoReorder: false
    }
  });

  const fetchSettings = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setState(prev => ({ ...prev, loading: false }));
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al cargar configuraciones',
        loading: false 
      }));
    }
  };

  const saveSettings = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      setState(prev => ({ 
        ...prev, 
        loading: false,
        successMessage: 'Configuraciones guardadas exitosamente'
      }));
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setState(prev => ({ ...prev, successMessage: null }));
      }, 3000);
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error al guardar configuraciones',
        loading: false 
      }));
    }
  };

  const updateUserSettings = (field: keyof typeof state.userSettings, value: string) => {
    setState(prev => ({
      ...prev,
      userSettings: { ...prev.userSettings, [field]: value }
    }));
  };

  const updateNotificationSettings = (field: keyof typeof state.notificationSettings, value: boolean) => {
    setState(prev => ({
      ...prev,
      notificationSettings: { ...prev.notificationSettings, [field]: value }
    }));
  };

  const updateSecuritySettings = (field: keyof typeof state.securitySettings, value: string | boolean) => {
    setState(prev => ({
      ...prev,
      securitySettings: { ...prev.securitySettings, [field]: value }
    }));
  };

  const updateSystemSettings = (field: keyof typeof state.systemSettings, value: string | number | boolean) => {
    setState(prev => ({
      ...prev,
      systemSettings: { ...prev.systemSettings, [field]: value }
    }));
  };

  const tabConfig = [
    { id: 'profile', label: 'Perfil', icon: User },
    { id: 'notifications', label: 'Notificaciones', icon: Bell },
    { id: 'security', label: 'Seguridad', icon: Shield },
    { id: 'system', label: 'Sistema', icon: Database },
  ];

  useEffect(() => {
    fetchSettings();
  }, []);

  if (state.loading && state.activeTab === 'profile') {
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
          <h1 className="text-3xl font-bold text-gray-900">Configuraciones</h1>
          <p className="text-gray-600">Administra las preferencias y configuraciones del sistema</p>
        </div>
        <Button 
          onClick={saveSettings} 
          disabled={state.loading}
          className="flex items-center gap-2"
        >
          {state.loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Guardando...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Guardar Cambios
            </>
          )}
        </Button>
      </div>

      {/* Success/Error Messages */}
      {state.successMessage && (
        <Alert variant="success">
          <Check className="h-4 w-4" />
          <AlertDescription>{state.successMessage}</AlertDescription>
        </Alert>
      )}

      {state.error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{state.error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar Navigation */}
        <Card className="lg:col-span-1">
          <CardContent className="p-4">
            <nav className="space-y-2">
              {tabConfig.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setState(prev => ({ ...prev, activeTab: tab.id }))}
                    className={`w-full flex items-center gap-3 px-3 py-2 text-left rounded-md transition-colors ${
                      state.activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </CardContent>
        </Card>

        {/* Content Area */}
        <div className="lg:col-span-3">
          {/* Profile Settings */}
          {state.activeTab === 'profile' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Información del Perfil
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Nombre</label>
                    <Input
                      value={state.userSettings.firstName}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateUserSettings('firstName', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Apellido</label>
                    <Input
                      value={state.userSettings.lastName}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateUserSettings('lastName', e.target.value)}
                    />
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium">Correo Electrónico</label>
                  <Input
                    type="email"
                    value={state.userSettings.email}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateUserSettings('email', e.target.value)}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">Teléfono</label>
                  <Input
                    value={state.userSettings.phone}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateUserSettings('phone', e.target.value)}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Idioma</label>
                    <Select value={state.userSettings.language} onValueChange={(value) => updateUserSettings('language', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="es">Español</SelectItem>
                        <SelectItem value="en">English</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Zona Horaria</label>
                    <Select value={state.userSettings.timezone} onValueChange={(value) => updateUserSettings('timezone', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="America/Lima">Lima (UTC-5)</SelectItem>
                        <SelectItem value="America/New_York">New York (UTC-4)</SelectItem>
                        <SelectItem value="Europe/Madrid">Madrid (UTC+1)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Notification Settings */}
          {state.activeTab === 'notifications' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  Configuración de Notificaciones
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-medium">Notificaciones por Email</div>
                        <div className="text-sm text-gray-500">Recibir notificaciones en tu correo electrónico</div>
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={state.notificationSettings.emailNotifications}
                      onChange={(e) => updateNotificationSettings('emailNotifications', e.target.checked)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Smartphone className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-medium">Notificaciones SMS</div>
                        <div className="text-sm text-gray-500">Recibir alertas importantes por SMS</div>
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={state.notificationSettings.smsNotifications}
                      onChange={(e) => updateNotificationSettings('smsNotifications', e.target.checked)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-medium">Alertas de Stock Bajo</div>
                        <div className="text-sm text-gray-500">Notificar cuando el stock esté por debajo del mínimo</div>
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={state.notificationSettings.lowStockAlerts}
                      onChange={(e) => updateNotificationSettings('lowStockAlerts', e.target.checked)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-medium">Reportes Diarios</div>
                        <div className="text-sm text-gray-500">Recibir resumen diario de actividades</div>
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={state.notificationSettings.dailyReports}
                      onChange={(e) => updateNotificationSettings('dailyReports', e.target.checked)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-medium">Reportes Semanales</div>
                        <div className="text-sm text-gray-500">Recibir resumen semanal de métricas</div>
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={state.notificationSettings.weeklyReports}
                      onChange={(e) => updateNotificationSettings('weeklyReports', e.target.checked)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Security Settings */}
          {state.activeTab === 'security' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Configuración de Seguridad
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Key className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-medium">Autenticación de Dos Factores</div>
                        <div className="text-sm text-gray-500">Agregar una capa extra de seguridad</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={state.securitySettings.twoFactorEnabled ? 'success' : 'secondary'}>
                        {state.securitySettings.twoFactorEnabled ? 'Habilitado' : 'Deshabilitado'}
                      </Badge>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => updateSecuritySettings('twoFactorEnabled', !state.securitySettings.twoFactorEnabled)}
                      >
                        {state.securitySettings.twoFactorEnabled ? 'Deshabilitar' : 'Habilitar'}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium">Expiración de Contraseña (días)</label>
                    <Select 
                      value={state.securitySettings.passwordExpiry} 
                      onValueChange={(value) => updateSecuritySettings('passwordExpiry', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="30">30 días</SelectItem>
                        <SelectItem value="60">60 días</SelectItem>
                        <SelectItem value="90">90 días</SelectItem>
                        <SelectItem value="180">180 días</SelectItem>
                        <SelectItem value="never">Nunca</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium">Tiempo de Sesión (minutos)</label>
                    <Select 
                      value={state.securitySettings.sessionTimeout} 
                      onValueChange={(value) => updateSecuritySettings('sessionTimeout', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="15">15 minutos</SelectItem>
                        <SelectItem value="30">30 minutos</SelectItem>
                        <SelectItem value="60">1 hora</SelectItem>
                        <SelectItem value="120">2 horas</SelectItem>
                        <SelectItem value="480">8 horas</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="border-t pt-4">
                    <Button variant="outline" className="w-full">
                      Cambiar Contraseña
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* System Settings */}
          {state.activeTab === 'system' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Configuración del Sistema
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Moneda</label>
                    <Select 
                      value={state.systemSettings.currency} 
                      onValueChange={(value) => updateSystemSettings('currency', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="PEN">Soles Peruanos (PEN)</SelectItem>
                        <SelectItem value="USD">Dólares Americanos (USD)</SelectItem>
                        <SelectItem value="EUR">Euros (EUR)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium">Formato de Fecha</label>
                    <Select 
                      value={state.systemSettings.dateFormat} 
                      onValueChange={(value) => updateSystemSettings('dateFormat', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                        <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                        <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Umbral de Stock Bajo</label>
                  <Input
                    type="number"
                    value={state.systemSettings.lowStockThreshold}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateSystemSettings('lowStockThreshold', parseInt(e.target.value))}
                    placeholder="Número de unidades"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Se generarán alertas cuando el stock esté por debajo de este número
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Reabastecimiento Automático</div>
                    <div className="text-sm text-gray-500">
                      Generar órdenes de compra automáticamente cuando el stock esté bajo
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={state.systemSettings.autoReorder}
                    onChange={(e) => updateSystemSettings('autoReorder', e.target.checked)}
                    className="h-4 w-4 text-blue-600 rounded border-gray-300"
                  />
                </div>

                <div className="border-t pt-4 space-y-2">
                  <h4 className="font-medium">Información del Sistema</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Versión:</span>
                      <span className="ml-2 font-medium">v2.1.0</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Última actualización:</span>
                      <span className="ml-2 font-medium">15/06/2024</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Base de datos:</span>
                      <span className="ml-2 font-medium">PostgreSQL 13.7</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Almacenamiento:</span>
                      <span className="ml-2 font-medium">2.3 GB / 10 GB</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
