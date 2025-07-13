import { ForecastData, Product, Warehouse } from '../types';
import axios, { AxiosInstance } from 'axios';

interface ForecastingServiceConfig {
  baseUrl: string;
  timeout: number;
}

interface ForecastingService {
  getForecasts(): Promise<{ results: ForecastData[] }>;
  predictDemand(data: any): Promise<any>;
  getReorderRecommendations(): Promise<any>;
  trainModel(data: any): Promise<any>;
  getModels(): Promise<any>;
  getProductForecast(productId: number): Promise<any>;
  getForecastData(params?: {
    days_ahead?: number;
    product_ids?: string;
    location_ids?: string;
  }): Promise<any>;
  generateRecommendations(): Promise<any>;
}

class ForecastingServiceImpl implements ForecastingService {
  private api: AxiosInstance;
  private baseUrl = 'http://localhost:8080/api/forecasting';
  
  constructor(config?: ForecastingServiceConfig) {
    this.api = axios.create({
      baseURL: config?.baseUrl || this.baseUrl,
      timeout: config?.timeout || 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async getForecasts(): Promise<{ results: ForecastData[] }> {
    try {
      const response = await fetch(`${this.baseUrl}/forecasts/`, {
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar pronósticos');
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error en getForecasts:', error);
      // En caso de error, devolver estructura vacía en lugar de datos mock
      return { results: [] };
    }
  }

  async predictDemand(data: any): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/predict/`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error('Error al generar predicción');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error en predictDemand:', error);
      throw error;
    }
  }

  async getReorderRecommendations(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/reorder-recommendations/`, {
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar recomendaciones');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error en getReorderRecommendations:', error);
      return { results: [] };
    }
  }

  async trainModel(data: any): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/train-model/`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error('Error al entrenar modelo');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error en trainModel:', error);
      throw error;
    }
  }

  async getModels(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/models/`, {
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar modelos');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error en getModels:', error);
      return { results: [] };
    }
  }

  async getProductForecast(productId: number): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/products/${productId}/forecast/`, {
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar pronóstico del producto');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error en getProductForecast:', error);
      return { predicted_demand: 0, confidence: 0 };
    }
  }

  async getForecastData(params?: {
    days_ahead?: number;
    product_ids?: string;
    location_ids?: string;
  }): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/forecast-data/`, {
        headers: this.getAuthHeaders(),
        method: 'POST',
        body: JSON.stringify(params),
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar datos de pronóstico');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error en getForecastData:', error);
      return { results: [] };
    }
  }

  async generateRecommendations(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/generate-recommendations/`, {
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error('Error al generar recomendaciones');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error en generateRecommendations:', error);
      return { results: [] };
    }
  }
}

export const forecastingService = new ForecastingServiceImpl();
export type { ForecastingService };