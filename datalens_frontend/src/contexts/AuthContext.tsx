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
    // **SIMPLIFICADO: Inicialización más directa**
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      console.log('🔄 Inicializando autenticación...');
      const storedToken = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user');
      
      if (storedToken && storedUser) {
        console.log('📦 Token y usuario encontrados en localStorage');
        
        // Verificar que el token no sea demasiado grande
        if (storedToken.length < 2000) {
          try {
            const userData = JSON.parse(storedUser);
            setToken(storedToken);
            setUser(userData);
            console.log('✅ Sesión restaurada exitosamente:', userData.email);
          } catch (parseError) {
            console.error('Error parsing user data:', parseError);
            clearAuthData();
          }
        } else {
          console.warn('Token demasiado grande, limpiando...');
          clearAuthData();
        }
      } else {
        console.log('🔍 No hay sesión guardada');
        clearAuthData();
      }
    } catch (error) {
      console.error('Error al inicializar autenticación:', error);
      clearAuthData();
    }
    setIsLoading(false);
  };

  const validateToken = async (): Promise<boolean> => {
    const currentToken = token || localStorage.getItem('access_token');
    if (!currentToken) return false;
    return true; // Simplificado por ahora
  };

  const refreshToken = async (): Promise<boolean> => {
    // Simplificado por ahora
    return false;
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
      console.log('🔐 Intentando iniciar sesión con:', email);
      
      const response = await fetch('http://localhost:8080/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      console.log('📡 Status de respuesta:', response.status);

      if (!response.ok) {
        console.error('❌ Respuesta de login no exitosa:', response.status, response.statusText);
        const errorData = await response.text();
        console.error('Error data:', errorData);
        return false;
      }

      const data = await response.json();
      console.log('📥 Datos de respuesta:', data);
      
      if (data.access && data.user) {
        const accessToken = data.access;
        
        // Guardar tokens y usuario
        setToken(accessToken);
        setUser(data.user);
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        if (data.refresh) {
          localStorage.setItem('refresh_token', data.refresh);
        }
        
        console.log('✅ Login exitoso:', data.user.email);
        return true;
      } else {
        console.error('❌ Formato de respuesta inválido:', data);
        return false;
      }
    } catch (error) {
      console.error('❌ Error durante el login:', error);
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