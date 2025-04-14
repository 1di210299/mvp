// src/api/decision-service.ts
import apiClient from './client';

export interface RecommendationRequest {
  dataset_id: number | string;
  action_type: 'pricing' | 'inventory' | 'marketing' | string;
  context?: any;
}

export interface RecommendationOption {
  option: any;
  score: number;
  confidence: number;
  factors: {[key: string]: any};
  expected_outcome: any;
  risks: Array<{
    factor: string;
    severity: string;
    description: string;
  }>;
}

export interface RecommendationResponse {
  recommended_option: any;
  all_options: RecommendationOption[];
  objective: string;
  reasoning: {
    factor_explanations: Array<{
      factor: string;
      score: number;
      weight: number;
      importance: string;
      contribution: number;
      explanation: string;
    }>;
    narrative: string;
    confidence_explanation: string;
    business_context: string;
  };
}

export interface ActionFeedbackRequest {
  success_score: number; // -1 to 1
  metrics?: {[key: string]: any};
  feedback?: string;
}

export interface InsightResponse {
  performance: {
    summary: {
      total_actions: number;
      successful_actions: number;
      failed_actions: number;
      neutral_actions: number;
      success_rate: number;
      avg_success_score: number;
    };
    action_type_performance: {[key: string]: any};
    time_series: Array<{
      period: string;
      count: number;
      success_rate: number;
    }>;
    insights: string[];
    learning_level: {
      level: string;
      progress: number;
      description: string;
    };
  };
  insights: string[];
  recommendations: Array<{
    area: string;
    action: string;
    action_type?: string;
    description: string;
    priority: 'alta' | 'media' | 'baja';
  }>;
  learning_level: {
    level: string;
    progress: number;
    description: string;
  };
}

// Servicio para interactuar con el motor de decisiones
export const decisionService = {
  // Obtener recomendación del agente IA
  getRecommendation: (request: RecommendationRequest) => 
    apiClient.post<RecommendationResponse>('/agent/recommend/', request),
    
  // Proporcionar feedback sobre una acción
  provideActionFeedback: (actionId: number, feedback: ActionFeedbackRequest) => 
    apiClient.post(`/agent/feedback/${actionId}/`, feedback),
    
  // Obtener insights de aprendizaje
  getLearningInsights: (period: string = 'all') => 
    apiClient.get<InsightResponse>(`/agent/insights/`, {
      params: { period }
    }),
    
  // Adaptar parámetros del agente
  adaptAgentParameters: () => 
    apiClient.post('/agent/adapt/')
};