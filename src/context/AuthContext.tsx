// src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, UserData } from '../api/services';

interface AuthContextType {
  user: UserData | null;
  loading: boolean;
  error: string | null;
  login: (credentials: { username: string; password: string }) => Promise<boolean>;
  register: (userData: {
    username: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
  }) => Promise<boolean>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps): JSX.Element => {
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Verificar estado de autenticación al inicio
  useEffect(() => {
    const checkAuthStatus = async (): Promise<void> => {
      const token = localStorage.getItem('token');
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (!token || !refreshToken) {
        setLoading(false);
        return;
      }
      
      try {
        // Intentar refrescar el token para validar la sesión
        const response = await authService.refreshToken(refreshToken);
        // Actualizar token en localStorage
        localStorage.setItem('token', response.data.access);
        
        // Obtener información del usuario desde el token
        // En una implementación real, podrías tener un endpoint específico para esto
        setUser({
          id: 1,
          username: 'usuario',
          email: 'usuario@example.com',
          first_name: '',
          last_name: ''
        });
      } catch (err) {
        console.error('Error al verificar autenticación:', err);
        // Token inválido o expirado
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
      } finally {
        setLoading(false);
      }
    };
    
    checkAuthStatus();
  }, []);

  // Función para iniciar sesión
  const login = async (credentials: { username: string; password: string }): Promise<boolean> => {
    try {
      setError(null);
      const response = await authService.login(credentials);
      
      // Guardar tokens
      localStorage.setItem('token', response.data.access);
      localStorage.setItem('refreshToken', response.data.refresh);
      
      // Guardar información del usuario
      setUser(response.data.user);
      
      return true;
    } catch (err: any) {
      console.error('Error de login:', err);
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
      return false;
    }
  };

  // Función para registrarse
  const register = async (userData: {
    username: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
  }): Promise<boolean> => {
    try {
      setError(null);
      await authService.register(userData);
      // Iniciar sesión automáticamente después del registro
      return await login({
        username: userData.username,
        password: userData.password
      });
    } catch (err: any) {
      console.error('Error de registro:', err);
      setError(err.response?.data || 'Error al registrar usuario');
      return false;
    }
  };

  // Función para cerrar sesión
  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
      setUser(null);
    } catch (err) {
      console.error('Error al cerrar sesión:', err);
    }
  };

  // Valores proporcionados por el contexto
  const contextValue: AuthContextType = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};