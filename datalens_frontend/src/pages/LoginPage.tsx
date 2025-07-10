import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button, Input, Alert, AlertDescription } from '../components/ui';
import { Eye, EyeOff, LogIn } from '../components/ui/icons';
import { authService } from '../services/api';

interface LoginState {
  email: string;
  password: string;
  loading: boolean;
  error: string | null;
  showPassword: boolean;
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<LoginState>({
    email: '',
    password: '',
    loading: false,
    error: null,
    showPassword: false
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      console.log('Attempting login with:', { email: state.email });
      
      const response = await authService.login({
        email: state.email,
        password: state.password
      });

      console.log('Login successful:', response);

      // Store tokens in localStorage
      localStorage.setItem('access_token', response.tokens.access);
      localStorage.setItem('refresh_token', response.tokens.refresh);
      
      // Store user info if needed
      localStorage.setItem('user_info', JSON.stringify(response.user));

      // Redirect to dashboard
      console.log('Redirecting to dashboard...');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Login error:', error);
      setState(prev => ({ 
        ...prev, 
        error: error.response?.data?.message || error.message || 'Error de autenticación. Verifica tus credenciales.',
        loading: false 
      }));
    }
  };

  const handleInputChange = (field: keyof LoginState, value: string) => {
    setState(prev => ({ ...prev, [field]: value }));
  };

  // Función para llenar credenciales de prueba
  const fillTestCredentials = (email: string, password: string) => {
    setState(prev => ({ 
      ...prev, 
      email: email,
      password: password
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Iniciar Sesión
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Accede a tu cuenta de DataLens
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-center">Bienvenido</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Correo Electrónico
                </label>
                <Input
                  id="email"
                  type="email"
                  required
                  value={state.email}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('email', e.target.value)}
                  placeholder="tu@email.com"
                  className="mt-1"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Contraseña
                </label>
                <div className="relative mt-1">
                  <Input
                    id="password"
                    type={state.showPassword ? 'text' : 'password'}
                    required
                    value={state.password}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('password', e.target.value)}
                    placeholder="Tu contraseña"
                    className="pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setState(prev => ({ ...prev, showPassword: !prev.showPassword }))}
                  >
                    {state.showPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </Button>
                </div>
              </div>

              {state.error && (
                <Alert variant="destructive">
                  <AlertDescription>{state.error}</AlertDescription>
                </Alert>
              )}

              <Button
                type="submit"
                disabled={state.loading}
                className="w-full flex items-center justify-center gap-2"
              >
                {state.loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Iniciando sesión...
                  </>
                ) : (
                  <>
                    <LogIn className="h-4 w-4" />
                    Iniciar Sesión
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 border-t pt-6">
              <div className="text-sm text-gray-600">
                <p className="font-medium mb-2">Credenciales de prueba:</p>
                <div className="bg-gray-50 p-3 rounded-md space-y-2">
                  <button 
                    type="button"
                    onClick={() => fillTestCredentials('superadmin@datalens.com', 'admin123')}
                    className="block w-full text-left hover:bg-gray-100 p-1 rounded cursor-pointer"
                  >
                    <strong>Nuevo Superadmin:</strong> superadmin@datalens.com / admin123
                  </button>
                  <button 
                    type="button"
                    onClick={() => fillTestCredentials('admin@test.com', 'admin123')}
                    className="block w-full text-left hover:bg-gray-100 p-1 rounded cursor-pointer"
                  >
                    <strong>Superadmin:</strong> admin@test.com / admin123
                  </button>
                  <button 
                    type="button"
                    onClick={() => fillTestCredentials('rolando.morante@distribuidorasanmartín.com.pe', 'password123')}
                    className="block w-full text-left hover:bg-gray-100 p-1 rounded cursor-pointer"
                  >
                    <strong>Admin:</strong> rolando.morante@distribuidorasanmartín.com.pe
                  </button>
                  <button 
                    type="button"
                    onClick={() => fillTestCredentials('modesta.alberdi@distribuidorasanmartín.com.pe', 'password123')}
                    className="block w-full text-left hover:bg-gray-100 p-1 rounded cursor-pointer"
                  >
                    <strong>Manager:</strong> modesta.alberdi@distribuidorasanmartín.com.pe
                  </button>
                  <p className="text-xs text-gray-500 mt-2">
                    Haz clic en las credenciales para auto-completar los campos
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;