import React, { useState } from 'react';
import { authService } from '../../services/api';
import { LoginData } from '../../types';
import './Login.css';

interface LoginProps {
  onLogin: (token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [formData, setFormData] = useState<LoginData>({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authService.login(formData);
      localStorage.setItem('access_token', response.tokens.access);
      localStorage.setItem('refresh_token', response.tokens.refresh);
      onLogin(response.tokens.access);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1 className="login-title">DataLens</h1>
          <p className="login-subtitle">Gestión inteligente de inventarios</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Correo Electrónico
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="form-input"
              placeholder="tu@email.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Contraseña
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="form-input"
              placeholder="Ingresa tu contraseña"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg w-full"
            disabled={loading}
          >
            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>

        <div className="login-footer">
          <div className="text-sm text-secondary">
            <p className="font-medium mb-2">Credenciales de prueba:</p>
            <div className="bg-gray-50 p-3 rounded-md space-y-1">
              <p><strong>Superadmin:</strong> juan@gmail.com</p>
              <p><strong>Admin:</strong> rolando.morante@distribuidorasanmartín.com.pe</p>
              <p><strong>Manager:</strong> modesta.alberdi@distribuidorasanmartín.com.pe</p>
              <p className="text-xs text-gray-500 mt-2">
                Nota: Las contraseñas deben ser configuradas en el sistema
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
