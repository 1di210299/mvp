// src/api/agent-service.ts
import apiClient from './client';

// Interfaces para las entidades del agente
export interface BusinessRule {
  id?: number;
  name: string;
  description?: string;
  rule_type: 'threshold' | 'anomaly' | 'opportunity' | 'risk';
  metric: string;
  condition: 'gt' | 'lt' | 'eq' | 'change';
  threshold_value: number;
  action_type: 'notify' | 'suggest' | 'auto';
  action_data: any;
  priority: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AgentAction {
  id?: number;
  action_type: string;
  status: string;
  description: string;
  action_data: any;
  expected_impact?: string;
  confidence: number;
  created_at?: string;
  executed_at?: string;
  result_notes?: string;
  dataset: number;
  rule?: number;
  rule_name?: string;
  monitoring_log?: number;
}

export interface BusinessContext {
  id?: number;
  name: string;
  business_type: string;
  region: string;
  seasonality_data: any;
  market_trends: any;
  external_factors: any;
  key_metrics: any;
  created_at?: string;
  updated_at?: string;
}

export interface MonitoringLog {
  id?: number;
  dataset: number;
  rule?: number;
  rule_name?: string;
  log_type: string;
  description: string;
  metrics: any;
  created_at?: string;
  severity: string;
  is_resolved: boolean;
  resolution_notes?: string;
  resolution_date?: string;
}

// Servicio para las funciones del agente
export const agentService = {
  // Reglas de negocio
  getBusinessRules: () => 
    apiClient.get<BusinessRule[]>('/agent/business-rules/'),
  
  getBusinessRule: (id: number) => 
    apiClient.get<BusinessRule>(`/agent/business-rules/${id}/`),
  
  createBusinessRule: (rule: BusinessRule) => 
    apiClient.post<BusinessRule>('/agent/business-rules/', rule),
  
  updateBusinessRule: (id: number, rule: Partial<BusinessRule>) => 
    apiClient.put<BusinessRule>(`/agent/business-rules/${id}/`, rule),
  
  deleteBusinessRule: (id: number) => 
    apiClient.delete(`/agent/business-rules/${id}/`),
  
  // Acciones del agente
  getAgentActions: (params: any = {}) => 
    apiClient.get<AgentAction[]>('/agent/agent-actions/', { params }),
  
  approveAction: (id: number) => 
    apiClient.post(`/agent/actions/approve/${id}/`),
  
  rejectAction: (id: number, reason?: string) => 
    apiClient.post(`/agent/actions/reject/${id}/`, { reason }),
  
  // Contexto de negocio
  getBusinessContexts: () => 
    apiClient.get<BusinessContext[]>('/agent/business-contexts/'),
  
  createBusinessContext: (context: BusinessContext) => 
    apiClient.post<BusinessContext>('/agent/business-contexts/', context),
  
  updateBusinessContext: (id: number, context: Partial<BusinessContext>) => 
    apiClient.put<BusinessContext>(`/agent/business-contexts/${id}/`, context),
};