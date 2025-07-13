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
  Save,
  Monitor
} from '../components/ui/icons';
import { settingsService } from '../services/api';
import { ThemeToggle } from '../components/theme/ThemeToggle';

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
  systemInfo: any;
}

const SettingsPage: React.FC = () => {
  const [state, setState] = useState<SettingsPageState>({
    loading: true,
    error: null,
    successMessage: null,
    activeTab: 'profile',
    userSettings: {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
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
    },
    systemInfo: null
  });

  const fetchSettings = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Cargar configuraciones del usuario desde la API real
      const settingsData = await settingsService.getUserSettings();
      
      // NUEVO: Cargar información REAL del sistema desde el backend
      const systemInfo = await settingsService.getSystemInfo();
      
      setState(prev => ({
        ...prev,
        userSettings: {
          firstName: settingsData.user_settings.first_name || '',
          lastName: settingsData.user_settings.last_name || '',
          email: settingsData.user_settings.email || '',
          phone: settingsData.user_settings.phone || '',
          language: settingsData.user_settings.language || 'es',
          timezone: settingsData.user_settings.timezone || 'America/Lima'
        },
        notificationSettings: {
          emailNotifications: settingsData.notification_settings.email_notifications || false,
          smsNotifications: settingsData.notification_settings.sms_notifications || false,
          lowStockAlerts: settingsData.notification_settings.low_stock_alerts || true,
          dailyReports: settingsData.notification_settings.daily_reports || true,
          weeklyReports: settingsData.notification_settings.weekly_reports || false
        },
        securitySettings: {
          twoFactorEnabled: settingsData.security_settings.two_factor_enabled || false,
          passwordExpiry: settingsData.security_settings.password_expiry || '90',
          sessionTimeout: settingsData.security_settings.session_timeout || '30'
        },
        systemSettings: {
          currency: settingsData.system_settings.currency || 'PEN',
          dateFormat: settingsData.system_settings.date_format || 'DD/MM/YYYY',
          lowStockThreshold: settingsData.system_settings.low_stock_threshold || 10,
          autoReorder: settingsData.system_settings.auto_reorder || false
        },
        systemInfo: systemInfo, // AHORA VIENE DEL BACKEND REAL
        loading: false
      }));
    } catch (err) {
      console.error('Error fetching settings:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al cargar configuraciones. Usando valores por defecto.',
        loading: false 
      }));
    }
  };

  const saveSettings = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Preparar datos para enviar a la API
      const settingsData = {
        user_settings: {
          first_name: state.userSettings.firstName,
          last_name: state.userSettings.lastName,
          email: state.userSettings.email,
          phone: state.userSettings.phone,
          language: state.userSettings.language,
          timezone: state.userSettings.timezone
        },
        notification_settings: {
          email_notifications: state.notificationSettings.emailNotifications,
          sms_notifications: state.notificationSettings.smsNotifications,
          low_stock_alerts: state.notificationSettings.lowStockAlerts,
          daily_reports: state.notificationSettings.dailyReports,
          weekly_reports: state.notificationSettings.weeklyReports
        },
        security_settings: {
          two_factor_enabled: state.securitySettings.twoFactorEnabled,
          password_expiry: state.securitySettings.passwordExpiry,
          session_timeout: state.securitySettings.sessionTimeout
        },
        system_settings: {
          currency: state.systemSettings.currency,
          date_format: state.systemSettings.dateFormat,
          low_stock_threshold: state.systemSettings.lowStockThreshold,
          auto_reorder: state.systemSettings.autoReorder
        }
      };
      
      // Enviar a la API real
      await settingsService.updateUserSettings(settingsData);
      
      setState(prev => ({ 
        ...prev, 
        loading: false,
        successMessage: 'Configuraciones guardadas exitosamente'
      }));
      
      // Limpiar mensaje de éxito después de 3 segundos
      setTimeout(() => {
        setState(prev => ({ ...prev, successMessage: null }));
      }, 3000);
      
    } catch (err) {
      console.error('Error saving settings:', err);
      setState(prev => ({ 
        ...prev, 
        error: 'Error al guardar configuraciones. Verifique la conexión.',
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
    { id: 'appearance', label: 'Apariencia', icon: Monitor },
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

          {/* Appearance Settings */}
          {state.activeTab === 'appearance' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Monitor className="h-5 w-5" />
                  Configuración de Apariencia
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div>
                    <ThemeToggle variant="dropdown" />
                  </div>
                  
                  <div className="border-t pt-4">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                      Configuraciones adicionales
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-900 dark:text-gray-100">Animaciones reducidas</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Reduce las animaciones para mejorar el rendimiento
                          </div>
                        </div>
                        <input
                          type="checkbox"
                          className="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-600"
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-900 dark:text-gray-100">Efectos de cristal</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Habilita efectos de glassmorphism en la interfaz
                          </div>
                        </div>
                        <input
                          type="checkbox"
                          defaultChecked
                          className="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-600"
                        />
                      </div>
                    </div>
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
                  {state.systemInfo ? (
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Versión:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.system_info.app_version}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Última actualización:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.system_info.last_updated}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Base de datos:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.database_info.type}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Almacenamiento:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.resources.storage_usage}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Memoria:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.resources.memory_usage}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Tiempo activo:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.resources.uptime}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Python:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.system_info.python_version}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Django:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.system_info.django_version}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Plataforma:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.system_info.platform}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Zona horaria:</span>
                        <span className="ml-2 font-medium">{state.systemInfo.server_config.time_zone}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
                      <p className="text-sm text-gray-500">Cargando información del sistema...</p>
                    </div>
                  )}
                  
                  {state.systemInfo && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <h5 className="font-medium text-sm mb-2">Estadísticas de la Aplicación</h5>
                      <div className="grid grid-cols-3 gap-4 text-xs">
                        <div className="text-center">
                          <div className="font-bold text-lg text-blue-600">{state.systemInfo.app_stats.total_products}</div>
                          <div className="text-gray-600">Productos</div>
                        </div>
                        <div className="text-center">
                          <div className="font-bold text-lg text-green-600">{state.systemInfo.app_stats.total_transactions}</div>
                          <div className="text-gray-600">Transacciones</div>
                        </div>
                        <div className="text-center">
                          <div className="font-bold text-lg text-orange-600">{state.systemInfo.app_stats.active_alerts}</div>
                          <div className="text-gray-600">Alertas Activas</div>
                        </div>
                      </div>
                    </div>
                  )}
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
