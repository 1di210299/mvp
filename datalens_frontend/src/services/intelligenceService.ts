import api from './api';

export interface MorningBriefing {
  id: number;
  generated_at: string;
  greeting: string;
  summary: string;
  topPriorities: IntelligentInsight[];
  opportunities: IntelligentInsight[];
  recommendations: IntelligentInsight[];
  contextualMetrics: {
    totalValue: {
      current: number;
      previousPeriod: number;
      change: number;
      timeframe: string;
    };
    salesTrend: {
      current: number;
      trend: 'up' | 'down' | 'stable';
      percentage: number;
      timeframe: string;
    };
    criticalAlerts: {
      count: number;
      mostUrgent: string;
      timeframe: string;
    };
    topProducts: {
      name: string;
      demand: number;
      daysLeft: number;
    }[];
  };
  success: boolean;
  error?: string;
}

export interface IntelligentInsight {
  id?: number;
  type: 'priority' | 'opportunity' | 'recommendation' | 'trend' | 'warning';
  title: string;
  message: string;
  priority: 'high' | 'medium' | 'low';
  actions: string[];
  created_at?: string;
  confidence_score?: number;
  days_since_created?: number;
}

export interface IntelligenceMetric {
  id: number;
  metric_type: string;
  current_value: number;
  previous_value: number;
  change_percentage: number;
  trend: 'up' | 'down' | 'stable';
  period_start: string;
  period_end: string;
  calculated_at: string;
  change_direction: 'positive' | 'negative' | 'neutral';
  change_magnitude: 'high' | 'medium' | 'low' | 'minimal';
}

export interface DashboardIntelligence {
  briefing: MorningBriefing;
  criticalInsights: IntelligentInsight[];
  success: boolean;
}

export interface IntelligenceStatus {
  openai_available: boolean;
  service_status: 'active' | 'limited';
  stats: {
    total_briefings: number;
    active_insights: number;
    total_metrics: number;
    last_briefing: string;
  };
  success: boolean;
}

class IntelligenceService {
  private static instance: IntelligenceService;
  private baseUrl = '/intelligence';

  static getInstance(): IntelligenceService {
    if (!IntelligenceService.instance) {
      IntelligenceService.instance = new IntelligenceService();
    }
    return IntelligenceService.instance;
  }

  /**
   * Obtener briefing matutino
   */
  async getMorningBriefing(forceRegenerate: boolean = false): Promise<MorningBriefing> {
    try {
      const method = forceRegenerate ? 'POST' : 'GET';
      const response = await api.request({
        method,
        url: `${this.baseUrl}/briefing/morning/`,
        data: forceRegenerate ? { force_regenerate: true } : undefined,
        timeout: 30000  // 30 segundos para llamadas de IA
      });

      return response.data;
    } catch (error) {
      console.error('Error obteniendo briefing matutino:', error);
      throw new Error('No se pudo obtener el briefing matutino');
    }
  }

  /**
   * Obtener inteligencia del dashboard (endpoint principal)
   */
  async getDashboardIntelligence(): Promise<DashboardIntelligence> {
    try {
      const response = await api.get(`${this.baseUrl}/dashboard/`, {
        timeout: 25000  // 25 segundos para inteligencia del dashboard
      });

      return response.data;
    } catch (error) {
      console.error('Error obteniendo inteligencia del dashboard:', error);
      throw new Error('No se pudo obtener la inteligencia del dashboard');
    }
  }

  /**
   * Obtener insights
   */
  async getInsights(params?: {
    type?: string;
    priority?: string;
    active?: boolean;
    limit?: number;
  }): Promise<{ insights: IntelligentInsight[]; count: number }> {
    try {
      const response = await api.get(`${this.baseUrl}/insights/`, { 
        params,
        timeout: 15000  // 15 segundos para insights
      });

      return response.data;
    } catch (error) {
      console.error('Error obteniendo insights:', error);
      throw new Error('No se pudieron obtener los insights');
    }
  }

  /**
   * Resolver un insight
   */
  async resolveInsight(insightId: number, notes?: string): Promise<{ message: string; success: boolean }> {
    try {
      const response = await api.post(`${this.baseUrl}/insights/${insightId}/resolve/`, {
        resolved_notes: notes
      });
      return response.data;
    } catch (error) {
      console.error('Error resolviendo insight:', error);
      throw new Error('No se pudo resolver el insight');
    }
  }

  /**
   * Obtener métricas inteligentes
   */
  async getMetrics(params?: {
    type?: string;
    days?: number;
  }): Promise<{ metrics: IntelligenceMetric[]; count: number }> {
    try {
      const response = await api.get(`${this.baseUrl}/metrics/`, { params });
      return response.data;
    } catch (error) {
      console.error('Error obteniendo métricas:', error);
      throw new Error('No se pudo obtener las métricas');
    }
  }

  /**
   * Obtener historial de briefings
   */
  async getBriefingHistory(params?: {
    type?: string;
    limit?: number;
  }): Promise<{ briefings: MorningBriefing[]; count: number }> {
    try {
      const response = await api.get(`${this.baseUrl}/briefing/history/`, { params });
      return response.data;
    } catch (error) {
      console.error('Error obteniendo historial:', error);
      throw new Error('No se pudo obtener el historial de briefings');
    }
  }

  /**
   * Obtener estado del servicio de inteligencia
   */
  async getServiceStatus(): Promise<IntelligenceStatus> {
    try {
      const response = await api.get(`${this.baseUrl}/status/`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo estado del servicio:', error);
      throw new Error('No se pudo obtener el estado del servicio');
    }
  }

  /**
   * Generar recomendaciones contextuales
   */
  async generateContextualRecommendations(): Promise<IntelligentInsight[]> {
    try {
      const response = await api.post(`${this.baseUrl}/recommendations/contextual/`, {}, {
        timeout: 25000  // 25 segundos para generar recomendaciones
      });

      return response.data.recommendations || [];
    } catch (error) {
      console.error('Error generando recomendaciones contextuales:', error);
      throw new Error('No se pudieron generar las recomendaciones');
    }
  }

  /**
   * Formatear greeting para mostrar en UI
   */
  formatGreeting(greeting: string): string {
    // Limpiar y formatear el greeting
    return greeting.replace(/[🌅🌄🌇]/g, '').trim();
  }

  /**
   * Obtener color para prioridad
   */
  getPriorityColor(priority: 'high' | 'medium' | 'low'): string {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  }

  /**
   * Obtener icono para tipo de insight
   */
  getInsightIcon(type: string): string {
    switch (type) {
      case 'priority':
        return '🚨';
      case 'opportunity':
        return '💡';
      case 'recommendation':
        return '📋';
      case 'trend':
        return '📈';
      case 'warning':
        return '⚠️';
      default:
        return '📊';
    }
  }

  /**
   * Formatear métricas para display
   */
  formatMetric(value: number, type: string): string {
    switch (type) {
      case 'sales_trend':
      case 'profit_margin':
        return `${value.toFixed(1)}%`;
      case 'inventory_health':
        return `${value.toFixed(0)}/100`;
      case 'customer_behavior':
        return `${value.toFixed(1)} puntos`;
      default:
        return value.toLocaleString();
    }
  }

  /**
   * Determinar si necesita regenerar briefing
   */
  needsRegeneration(lastBriefing?: string): boolean {
    if (!lastBriefing) return true;
    
    const lastBriefingDate = new Date(lastBriefing);
    const now = new Date();
    const diffHours = (now.getTime() - lastBriefingDate.getTime()) / (1000 * 60 * 60);
    
    // Regenerar si han pasado más de 4 horas
    return diffHours > 4;
  }

  /**
   * Verificar si el servicio está disponible
   */
  async isServiceAvailable(): Promise<boolean> {
    try {
      const status = await this.getServiceStatus();
      return status.service_status === 'active';
    } catch (error) {
      console.error('Error verificando disponibilidad:', error);
      return false;
    }
  }
}

// Singleton instance
export const intelligenceService = IntelligenceService.getInstance();

// Export adicional para compatibilidad
export default intelligenceService; 