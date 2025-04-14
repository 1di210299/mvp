// src/api/services.ts
import apiClient from './client';

// Tipos para los objetos de respuesta
export interface Dataset {
  id: number;
  name: string;
  description: string;
  category: string;
  created_at: string;
  columns: any[];
  connection: number;
  owner: number;
}

export interface DatasetContext {
  id: number;
  name: string;
  description: string;
  category: string;
  created_at: string;
  columnNames: string[];
  connection_type: string;
}

export interface UserData {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: UserData;
}

export interface Visualization {
  type: string;
  data: any;
  title: string;
}

export interface Insight {
  type: string;
  text: string;
}

export interface AnalysisResponse {
  message: string;
  visualizations?: Visualization[];
  insights?: Insight[];
  suggestions?: string[];
}

export interface AnalysisRequest {
  message: string;
  datasetId: number | string;
  datasetContext?: any;
  language?: string;
  messageHistory?: any[];
  assistantType?: 'general' | 'sales';
}

export interface SalesAnalysisRequest {
  message: string;
  empresaId: number | string;
  nombreEmpresa?: string;
  sector?: string;
  language?: string;
  messageHistory?: any[];
}

export interface SentimentAnalysis {
  original_text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  score: number;
  key_phrases: string[];
  explanation: string;
  analysis: {
    is_peruvian_context: boolean;
    processed_text: string;
  };
}

// Interfaces para gráficas
export interface ChartData {
  date_of_entry?: string;
  date?: string;
  fecha?: string;
  sales?: number;
  ventas?: number;
  value?: number;
  valor?: number;
  category?: string;
  categoria?: string;
  region?: string;
  región?: string;
  growth?: number;
  crecimiento?: number;
  ticket?: number;
  [key: string]: any;
}

export interface ChartResponse {
  chart: {
    data: any[];
    layout: any;
    frames: any[];
    config: any;
  };
  analysis: {
    total_sales?: number;
    average_sale?: number;
    max_sale?: number;
    min_sale?: number;
    growth_rate?: number;
    top_category?: string;
    top_region?: string;
    prediction?: {
      confidence: number;
      growth_rate: number;
      average_sale: number;
    };
    [key: string]: any;
  };
  raw_data: any[];
  predictions?: any[];
}

export interface SalesVisualizationResponse extends ChartResponse {
  prediction_chart: {
    data: any[];
    layout: any;
    frames: any[];
    config: any;
  } | null;
  recommendations: string[];
}

// Servicio para datasets
export const datasetService = {
  getAll: (params: any = {}) => 
    apiClient.get<Dataset[]>('/datasets/', { params }),
  
  getById: (id: number | string) => 
    apiClient.get<Dataset>(`/datasets/${id}/`),
  
  create: (data: Partial<Dataset>) => 
    apiClient.post<Dataset>('/datasets/', data),
  
  update: (id: number | string, data: Partial<Dataset>) => 
    apiClient.put<Dataset>(`/datasets/${id}/`, data),
  
  delete: (id: number | string) => 
    apiClient.delete(`/datasets/${id}/`),
  
  getContext: (id: number | string) => 
    apiClient.get<DatasetContext>(`/datasets/${id}/context/`),
  
  uploadFile: (formData: FormData) => {
    return apiClient.post('/upload-dataset/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  getDatasetData: (id: number | string) => 
    apiClient.get(`/datasets/${id}/data`),
};

// Servicio para asistente IA
export const assistantService = {
  // Método general para el asistente de análisis de datos
  analyze: (data: AnalysisRequest) => 
    apiClient.post<AnalysisResponse>('/assistant/analyze/', data),
  
  // Método específico para asistente de ventas
  analyzeSales: (data: SalesAnalysisRequest) => 
    apiClient.post<AnalysisResponse>('/assistant/analyze/', {
      message: data.message,
      datasetId: data.empresaId,
      datasetContext: {
        nombreEmpresa: data.nombreEmpresa,
        sector: data.sector
      },
      language: data.language || 'es',
      messageHistory: data.messageHistory || [],
      assistantType: 'sales'
    }),
  
  // Método para obtener el contexto de un dataset
  getContext: (datasetId: number | string) => 
    apiClient.get<DatasetContext>(`/datasets/${datasetId}/context/`),
};

// Servicio para visualizaciones
export const chartService = {
  // Generar gráfico básico de ventas
  generateSalesChart: (data: ChartData[]) => 
    apiClient.post<ChartResponse>('/generate-chart/', { 
      data,
      chart_type: 'sales'
    }),
  
  // Generar gráfico por categoría
  generateCategoryChart: (data: ChartData[], categoryField: string = 'category', valueField: string = 'value') => 
    apiClient.post<ChartResponse>('/generate-chart/', { 
      data,
      chart_type: 'category',
      category_field: categoryField,
      value_field: valueField
    }),
  
  // Generar gráfico regional
  generateRegionalChart: (data: ChartData[], regionField: string = 'region', valueField: string = 'sales') => 
    apiClient.post<ChartResponse>('/generate-chart/', { 
      data,
      chart_type: 'regional',
      region_field: regionField,
      value_field: valueField
    }),
  
  // Generar gráfico de comparación temporal
  generateTimeComparisonChart: (data: ChartData[], dateField: string = 'date', valueField: string = 'value', compareField: string = 'category') => 
    apiClient.post<ChartResponse>('/generate-chart/', { 
      data,
      chart_type: 'time_comparison',
      date_field: dateField,
      value_field: valueField,
      compare_field: compareField
    }),
  
  // Generar heatmap
  generateHeatmapChart: (data: ChartData[], xField: string, yField: string, valueField: string) => 
    apiClient.post<ChartResponse>('/generate-chart/', { 
      data,
      chart_type: 'heatmap',
      x_field: xField,
      y_field: yField,
      value_field: valueField
    }),
  
  // Generar visualización de ventas con análisis y recomendaciones
  generateSalesVisualization: (data: ChartData[], period: string = 'monthly', category?: string, region?: string) => 
    apiClient.post<SalesVisualizationResponse>('/generate-sales-visualization/', { 
      data,
      period,
      category,
      region
    }),
  
  // Predecir ventas futuras
  predictSales: (data: ChartData[], periods: number = 3) => 
    apiClient.post<ChartResponse>('/predict-sales/', { 
      data,
      periods
    }),
    
  // Método genérico para generar gráficos (para mantener compatibilidad)
  generateChart: (data: any, chartType: string = 'sales') => 
    apiClient.post('/generate-chart/', { 
      data, 
      chart_type: chartType 
    }),
};

// Servicio para procesamiento NLP
export const nlpService = {
  analyzeSentiment: (text: string, includePeruvianContext: boolean = true) => 
    apiClient.post<SentimentAnalysis>('/nlp/sentiment/', { 
      text, 
      include_peruvian_context: includePeruvianContext 
    }),
  
  classifyFeedback: (text: string) => 
    apiClient.post('/nlp/classify-feedback/', { text }),
  
  analyzeBusinessText: (text: string, businessType: string = 'retail') => 
    apiClient.post('/nlp/business-analysis/', { 
      text, 
      business_type: businessType 
    }),
  
  explainFinancialTerms: (terms: string) => 
    apiClient.post('/nlp/financial-terms/', { terms }),
};

// Servicio para autenticación
export const authService = {
  login: (credentials: { username: string; password: string }) => 
    apiClient.post<AuthResponse>('/auth/login/', credentials),
  
  register: (userData: {
    username: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
  }) => apiClient.post<UserData>('/auth/register/', userData),
  
  refreshToken: (refreshToken: string) => 
    apiClient.post<{ access: string }>('/auth/refresh/', { refresh: refreshToken }),
  
  // La función logout solo elimina tokens locales
  logout: (): Promise<void> => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    return Promise.resolve();
  }
};

// Servicio para conexiones externas
export const connectionService = {
  testConnection: (connectionData: {
    connectionType: string;
    connectionString?: string;
    username?: string;
    password?: string;
    query?: string;
  }) => apiClient.post('/test-connection/', connectionData),
};