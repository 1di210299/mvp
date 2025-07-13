import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  token: string | null;
  // **NUEVOS MÉTODOS**
  refreshToken: () => Promise<boolean>;
  validateToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // **MEJORADO: Inicialización más robusta**
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      const storedToken = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user');
      
      if (storedToken && storedUser) {
        // Verificar que el token no sea demasiado grande
        if (storedToken.length < 2000) {
          // **NUEVO: Validar token antes de usarlo**
          const isValid = await validateStoredToken(storedToken);
          
          if (isValid) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
            console.log('✅ Sesión restaurada exitosamente');
          } else {
            console.log('🔄 Token expirado, intentando renovar...');
            const refreshed = await refreshToken();
            if (!refreshed) {
              clearAuthData();
            }
          }
        } else {
          console.warn('Token demasiado grande, limpiando...');
          clearAuthData();
        }
      }
    } catch (error) {
      console.error('Error al inicializar autenticación:', error);
      clearAuthData();
    }
    setIsLoading(false);
  };

  const validateStoredToken = async (token: string): Promise<boolean> => {
    try {
      const response = await fetch('http://localhost:8080/api/auth/validate-token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          // Actualizar información del usuario si viene en la respuesta
          if (data.user) {
            setUser(data.user);
            localStorage.setItem('user', JSON.stringify(data.user));
          }
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Error validando token:', error);
      return false;
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshTokenStr = localStorage.getItem('refresh_token');
      if (!refreshTokenStr) {
        return false;
      }

      console.log('🔄 Renovando token...');
      
      const response = await fetch('http://localhost:8080/api/auth/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshTokenStr }),
      });

      if (response.ok) {
        const data = await response.json();
        
        if (data.status === 'success' && data.tokens) {
          // Actualizar tokens
          setToken(data.tokens.access);
          localStorage.setItem('access_token', data.tokens.access);
          
          if (data.tokens.refresh) {
            localStorage.setItem('refresh_token', data.tokens.refresh);
          }
          
          // Actualizar información del usuario
          if (data.user) {
            setUser(data.user);
            localStorage.setItem('user', JSON.stringify(data.user));
          }
          
          console.log('✅ Token renovado exitosamente');
          return true;
        }
      }
      
      console.error('❌ Error renovando token');
      return false;
    } catch (error) {
      console.error('❌ Error renovando token:', error);
      return false;
    }
  };

  const validateToken = async (): Promise<boolean> => {
    const currentToken = token || localStorage.getItem('access_token');
    if (!currentToken) return false;
    
    return validateStoredToken(currentToken);
  };

  const clearAuthData = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    sessionStorage.removeItem('user');
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      console.log('🔐 Intentando iniciar sesión...');
      
      const response = await fetch('http://localhost:8080/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
        credentials: 'omit',
        cache: 'no-cache',
        mode: 'cors',
      });

      if (!response.ok) {
        console.error('❌ Respuesta de login no exitosa:', response.status, response.statusText);
        return false;
      }

      const data = await response.json();
      console.log('📥 Respuesta de login:', data);
      
      if (data.status === 'success' && data.tokens && data.tokens.access) {
        const accessToken = data.tokens.access;
        
        // Verificar tamaño del token
        if (accessToken.length > 2000) {
          console.warn('⚠️ Token muy grande, podría causar problemas');
        }
        
        // Guardar tokens
        setToken(accessToken);
        localStorage.setItem('access_token', accessToken);
        
        if (data.tokens.refresh && data.tokens.refresh.length < 2000) {
          localStorage.setItem('refresh_token', data.tokens.refresh);
        }
        
        // Guardar usuario
        if (data.user) {
          setUser(data.user);
          localStorage.setItem('user', JSON.stringify(data.user));
          console.log('✅ Login exitoso, usuario configurado:', data.user);
          return true;
        } else {
          // Obtener datos del perfil si no vienen en la respuesta
          try {
            const userResponse = await fetch('http://localhost:8080/api/auth/profile/', {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
              },
              credentials: 'omit',
              cache: 'no-cache',
              mode: 'cors',
            });
            
            if (userResponse.ok) {
              const userData = await userResponse.json();
              setUser(userData);
              localStorage.setItem('user', JSON.stringify(userData));
              console.log('✅ Login exitoso, perfil obtenido:', userData);
              return true;
            }
          } catch (profileError) {
            console.error('Error obteniendo perfil:', profileError);
          }
        }
      }
      
      console.error('❌ Formato de respuesta inválido:', data);
      return false;
    } catch (error) {
      console.error('❌ Error durante el login:', error);
      
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        console.warn('⚠️ Posible problema de red, limpiando datos...');
        clearAuthData();
      }
      
      return false;
    }
  };

  const logout = () => {
    console.log('🚪 Cerrando sesión...');
    clearAuthData();
    console.log('✅ Logout completado, datos limpiados');
  };

  const isAuthenticated = !!token && !!user;

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
        token,
        refreshToken,
        validateToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};