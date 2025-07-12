import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  token: string | null;
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
    // Verificar si hay un token guardado al iniciar la app
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      console.log('Attempting login with:', { email });
      
      const response = await fetch('http://localhost:8080/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        console.error('Response not ok:', response.status, response.statusText);
        return false;
      }

      const data = await response.json();
      console.log('Login response data:', data);
      
      // Verificar que la respuesta tenga el formato correcto del backend Django
      if (data.status === 'success' && data.tokens && data.tokens.access) {
        setToken(data.tokens.access);
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        
        // El usuario ya viene en la respuesta del login
        if (data.user) {
          setUser(data.user);
          localStorage.setItem('user', JSON.stringify(data.user));
          console.log('Login successful, user set:', data.user);
          return true;
        } else {
          // Si no viene el usuario, obtener datos del perfil
          const userResponse = await fetch('http://localhost:8080/api/auth/profile/', {
            headers: {
              'Authorization': `Bearer ${data.tokens.access}`,
            },
          });
          
          if (userResponse.ok) {
            const userData = await userResponse.json();
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));
            console.log('Login successful, user fetched:', userData);
            return true;
          }
        }
      }
      
      console.error('Invalid response format:', data);
      return false;
    } catch (error) {
      console.error('Error durante el login:', error);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
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