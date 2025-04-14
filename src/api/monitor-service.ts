// src/api/monitor-service.ts
import apiClient from './client';

export interface AnalysisResult {
  trends: {
    [key: string]: any;
  };
  anomalies: {
    [key: string]: any;
  };
  opportunities: {
    [key: string]: any;
  };
  forecasts: {
    [key: string]: any;
  };
}

export interface MonitoringAlert {
  id: number;
  log_type: string;
  description: string;
  created_at: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  rule_name?: string;
  metrics: any;
  is_resolved: boolean;
}

// Servicio para interactuar con el monitor autónomo
export const monitorService = {
  analyzeDataset: (datasetId: number) => 
    apiClient.post<{
      success: boolean;
      analysis_results: AnalysisResult;
      detected_issues: any[];
      opportunities: any[];
      actions_taken: any[];
    }>('/monitor/analyze/', { dataset_id: datasetId }),
    
  getActiveAlerts: (datasetId: number) => 
    apiClient.get<MonitoringAlert[]>(`/monitor/alerts/${datasetId}/`),
    
  getSuggestedActions: (datasetId: number) => 
    apiClient.get<any[]>(`/monitor/actions/${datasetId}/`),
    
  resolveAlert: (alertId: number, notes?: string) => 
    apiClient.post(`/monitor/alerts/resolve/${alertId}/`, { notes }),
    
  // Método para programar análisis automáticos
  scheduleAnalysis: (datasetId: number, frequency: string) => 
    apiClient.post('/monitor/schedule/', { 
      dataset_id: datasetId, 
      frequency 
    }),
};