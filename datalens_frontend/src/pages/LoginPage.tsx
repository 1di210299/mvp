import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button, Input, Alert, AlertDescription } from '../components/ui';
import { Eye, EyeOff, LogIn } from '../components/ui/icons';
import { ThemeToggle } from '../components/theme/ThemeToggle';
import { useAuth } from '../contexts/AuthContext';

interface LoginState {
  email: string;
  password: string;
  loading: boolean;
  error: string | null;
  showPassword: boolean;
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [state, setState] = useState<LoginState>({
    email: '',
    password: '',
    loading: false,
    error: null,
    showPassword: false
  });

  // Redirigir si ya está autenticado
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/app/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      console.log('Attempting login with:', { email: state.email });
      
      const success = await login(state.email, state.password);

      if (success) {
        console.log('Login successful, redirecting to dashboard...');
        navigate('/app/dashboard');
      } else {
        setState(prev => ({ 
          ...prev, 
          error: 'Credenciales incorrectas. Verifica tu email y contraseña.',
          loading: false 
        }));
      }
      
    } catch (error: any) {
      console.error('Login error:', error);
      setState(prev => ({ 
        ...prev, 
        error: 'Error de conexión. Verifica que el servidor esté ejecutándose en puerto 8081.',
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
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 transition-colors duration-300">
      {/* Theme Toggle en la esquina superior derecha */}
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>
      
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
            Iniciar Sesión
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Accede a tu cuenta de DataLens
          </p>
        </div>

        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="text-center text-gray-900 dark:text-white">Bienvenido</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Correo Electrónico
                </label>
                <Input
                  id="email"
                  type="email"
                  required
                  value={state.email}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('email', e.target.value)}
                  placeholder="tu@email.com"
                  className="mt-1 bg-white dark:bg-slate-800 text-gray-900 dark:text-white border-gray-300 dark:border-slate-600"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
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
                    className="pr-10 bg-white dark:bg-slate-800 text-gray-900 dark:text-white border-gray-300 dark:border-slate-600"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent text-gray-400 dark:text-gray-500"
                    onClick={() => setState(prev => ({ ...prev, showPassword: !prev.showPassword }))}
                  >
                    {state.showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              {state.error && (
                <Alert variant="destructive" className="bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                  <AlertDescription className="text-red-800 dark:text-red-200">{state.error}</AlertDescription>
                </Alert>
              )}

              <Button
                type="submit"
                disabled={state.loading}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white"
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

            <div className="mt-6 border-t border-gray-200 dark:border-slate-600 pt-6">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                <p className="font-medium mb-2">Credenciales de prueba:</p>
                <div className="bg-gray-50 dark:bg-slate-800 p-3 rounded-md space-y-2 border border-gray-200 dark:border-slate-600">
                  <button 
                    type="button"
                    onClick={() => fillTestCredentials('superadmin@datalens.com', 'admin123')}
                    className="block w-full text-left hover:bg-gray-100 dark:hover:bg-slate-700 p-1 rounded cursor-pointer text-gray-900 dark:text-gray-200 transition-colors"
                  >
                    <strong>Nuevo Superadmin:</strong> superadmin@datalens.com / admin123
                  </button>
                  <button 
                    type="button"
                    onClick={() => fillTestCredentials('admin@test.com', 'admin123')}
                    className="block w-full text-left hover:bg-gray-100 dark:hover:bg-slate-700 p-1 rounded cursor-pointer text-gray-900 dark:text-gray-200 transition-colors"
                  >
                    <strong>Superadmin:</strong> admin@test.com / admin123
                  </button>
                  <button 
                    type="button"
                    onClick={() => fillTestCredentials('rolando.morante@distribuidorasanmartín.com.pe', 'password123')}
                    className="block w-full text-left hover:bg-gray-100 dark:hover:bg-slate-700 p-1 rounded cursor-pointer text-gray-900 dark:text-gray-200 transition-colors"
                  >
                    <strong>Admin:</strong> rolando.morante@distribuidorasanmartín.com.pe
                  </button>
                  <button 
                    type="button"
                    onClick={() => fillTestCredentials('modesta.alberdi@distribuidorasanmartín.com.pe', 'password123')}
                    className="block w-full text-left hover:bg-gray-100 dark:hover:bg-slate-700 p-1 rounded cursor-pointer text-gray-900 dark:text-gray-200 transition-colors"
                  >
                    <strong>Manager:</strong> modesta.alberdi@distribuidorasanmartín.com.pe
                  </button>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
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