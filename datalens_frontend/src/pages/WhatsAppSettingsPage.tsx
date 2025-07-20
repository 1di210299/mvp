import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Alert,
  AlertDescription,
  Badge
} from '../components/ui';
import {
  MessageCircle,
  Phone,
  Settings,
  CheckCircle,
  AlertTriangle,
  Plus,
  ArrowRight
} from '../components/ui/icons';

interface WhatsAppConfig {
  company_name: string;
  whatsapp_business_number: string;
  whatsapp_enabled: boolean;
  whatsapp_plan: string;
  phone: string;
  email: string;
  subscription_type: string;
  can_upgrade: boolean;
}

interface WhatsAppSettingsPageState {
  config: WhatsAppConfig | null;
  loading: boolean;
  error: string | null;
  success: string | null;
  testNumber: string;
  testLoading: boolean;
  unsavedChanges: boolean;
}

const WhatsAppSettingsPage: React.FC = () => {
  const [state, setState] = useState<WhatsAppSettingsPageState>({
    config: null,
    loading: true,
    error: null,
    success: null,
    testNumber: '',
    testLoading: false,
    unsavedChanges: false
  });

  // Cargar configuración actual
  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const response = await fetch('/api/company/whatsapp/config/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const config = await response.json();
        setState(prev => ({ 
          ...prev, 
          config, 
          loading: false,
          unsavedChanges: false
        }));
      } else {
        throw new Error('Error al cargar configuración');
      }
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error desconocido',
        loading: false 
      }));
    }
  };

  const handleSaveConfig = async () => {
    if (!state.config) return;

    try {
      setState(prev => ({ ...prev, loading: true, error: null, success: null }));

      const response = await fetch('/api/company/whatsapp/config/', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          whatsapp_business_number: state.config.whatsapp_business_number,
          whatsapp_enabled: state.config.whatsapp_enabled
        })
      });

      if (response.ok) {
        const result = await response.json();
        setState(prev => ({ 
          ...prev, 
          success: 'Configuración guardada exitosamente',
          loading: false,
          unsavedChanges: false
        }));
        
        // Actualizar configuración
        await fetchConfig();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al guardar configuración');
      }
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error desconocido',
        loading: false 
      }));
    }
  };

  const handleTestWhatsApp = async () => {
    if (!state.testNumber.trim()) {
      setState(prev => ({ ...prev, error: 'Ingrese un número para la prueba' }));
      return;
    }

    try {
      setState(prev => ({ ...prev, testLoading: true, error: null }));

      const response = await fetch('/api/company/whatsapp/test/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          test_number: state.testNumber
        })
      });

      if (response.ok) {
        const result = await response.json();
        setState(prev => ({ 
          ...prev, 
          success: `Mensaje de prueba enviado a ${result.sent_to}`,
          testLoading: false
        }));
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al enviar mensaje de prueba');
      }
    } catch (err) {
      setState(prev => ({ 
        ...prev, 
        error: err instanceof Error ? err.message : 'Error desconocido',
        testLoading: false 
      }));
    }
  };

  const updateConfig = (field: keyof WhatsAppConfig, value: any) => {
    setState(prev => ({
      ...prev,
      config: prev.config ? { ...prev.config, [field]: value } : null,
      unsavedChanges: true,
      error: null,
      success: null
    }));
  };

  if (state.loading && !state.config) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <MessageCircle className="h-8 w-8 text-green-600" />
            Configuración WhatsApp Business
          </h1>
          <p className="text-gray-600 mt-2">
            Configure WhatsApp para enviar órdenes de compra automáticamente a sus proveedores
          </p>
        </div>
        
        {state.config?.whatsapp_enabled && (
          <Badge variant="success" className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            WhatsApp Activo
          </Badge>
        )}
      </div>

      {/* Alerts */}
      {state.error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{state.error}</AlertDescription>
        </Alert>
      )}

      {state.success && (
        <Alert variant="default" className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{state.success}</AlertDescription>
        </Alert>
      )}

      {state.config && (
        <div className="grid gap-6">
          {/* Configuración Principal */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Configuración Principal
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Nombre de la Empresa
                  </label>
                  <Input
                    value={state.config.company_name}
                    disabled
                    className="bg-gray-50"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Este nombre aparecerá en los mensajes de WhatsApp
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Plan Actual
                  </label>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={state.config.whatsapp_plan === 'basic' ? 'secondary' : 'primary'}>
                      {state.config.whatsapp_plan === 'basic' ? 'Básico' : 
                       state.config.whatsapp_plan === 'premium' ? 'Premium' : 'Enterprise'}
                    </Badge>
                    {state.config.can_upgrade && (
                      <Button variant="ghost" size="sm">
                        Actualizar Plan
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Número WhatsApp Business *
                  </label>
                  <Input
                    value={state.config.whatsapp_business_number || ''}
                    onChange={(e) => updateConfig('whatsapp_business_number', e.target.value)}
                    placeholder="+51999123456"
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Incluya el código de país. Este número aparecerá en los mensajes.
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Estado del Servicio
                  </label>
                  <div className="flex items-center space-x-3 mt-2">
                    <input
                      type="checkbox"
                      id="whatsapp_enabled"
                      checked={state.config.whatsapp_enabled}
                      onChange={(e) => updateConfig('whatsapp_enabled', e.target.checked)}
                      className="h-4 w-4 text-green-600"
                    />
                    <label htmlFor="whatsapp_enabled" className="text-sm font-medium">
                      Habilitar WhatsApp Business
                    </label>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Active para enviar órdenes de compra por WhatsApp
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Prueba de Configuración */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ArrowRight className="h-5 w-5" />
                Probar Configuración
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700">
                    Número de prueba
                  </label>
                  <Input
                    value={state.testNumber}
                    onChange={(e) => setState(prev => ({ ...prev, testNumber: e.target.value }))}
                    placeholder="+51999999999"
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Ingrese un número para recibir un mensaje de prueba
                  </p>
                </div>
                <Button
                  onClick={handleTestWhatsApp}
                  disabled={state.testLoading || !state.config.whatsapp_enabled}
                  className="flex items-center gap-2"
                >
                  {state.testLoading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <ArrowRight className="h-4 w-4" />
                  )}
                  Enviar Prueba
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Información del Plan */}
          <Card>
            <CardContent className="pt-6">
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">
                  ℹ️ ¿Cómo funciona?
                </h3>
                <div className="text-sm text-blue-800 space-y-1">
                  <p>• Sus proveedores recibirán mensajes de WhatsApp con las órdenes de compra</p>
                  <p>• El número que configuró aparecerá como remitente en los mensajes</p>
                  <p>• Los proveedores pueden responder directamente para confirmar órdenes</p>
                  <p>• Plan {state.config.whatsapp_plan}: {
                    state.config.whatsapp_plan === 'basic' 
                      ? 'Hasta 100 mensajes/mes' 
                      : 'Mensajes ilimitados'
                  }</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Botones de Acción */}
          <div className="flex justify-end space-x-3">
            <Button
              variant="ghost"
              onClick={fetchConfig}
              disabled={state.loading}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSaveConfig}
              disabled={state.loading || !state.unsavedChanges}
              className="flex items-center gap-2"
            >
              {state.loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <CheckCircle className="h-4 w-4" />
              )}
              Guardar Configuración
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default WhatsAppSettingsPage;
