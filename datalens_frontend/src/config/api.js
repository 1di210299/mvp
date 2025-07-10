// Configuración de API para diferentes entornos
const API_CONFIG = {
  development: {
    baseURL: 'http://localhost:8080/api',
    timeout: 30000,
  },
  production: {
    baseURL: 'https://your-backend-app.railway.app/api', // Cambiar por tu URL de Railway
    timeout: 30000,
  }
};

const environment = process.env.NODE_ENV || 'development';
export const apiConfig = API_CONFIG[environment];

// Función helper para construir URLs
export const buildApiUrl = (endpoint) => {
  return `${apiConfig.baseURL}${endpoint}`;
};

export default apiConfig;