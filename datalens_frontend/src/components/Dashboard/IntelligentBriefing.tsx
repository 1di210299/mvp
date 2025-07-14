import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Alert, AlertDescription } from '../ui';
import { RefreshCw, Zap, AlertTriangle, TrendingUp, CheckCircle, Clock, Target, Brain, ChevronDown, ArrowUp, EyeOff } from '../ui/icons';
import { intelligenceService, MorningBriefing, IntelligentInsight } from '../../services/intelligenceService';
import { formatCurrency, formatDate } from '../../utils/formatting';
import { useTheme } from '../../contexts/ThemeContext';

interface IntelligentBriefingProps {
  className?: string;
  onInsightClick?: (insight: IntelligentInsight) => void;
}

export const IntelligentBriefing: React.FC<IntelligentBriefingProps> = ({ 
  className = '', 
  onInsightClick 
}) => {
  const { actualTheme } = useTheme();
  const isDarkMode = actualTheme === 'dark';
  const [briefing, setBriefing] = useState<MorningBriefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [serviceAvailable, setServiceAvailable] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem('briefing-collapsed');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    loadBriefing();
    checkServiceStatus();
  }, []);

  useEffect(() => {
    localStorage.setItem('briefing-collapsed', JSON.stringify(isCollapsed));
  }, [isCollapsed]);

  const checkServiceStatus = async () => {
    try {
      const available = await intelligenceService.isServiceAvailable();
      setServiceAvailable(available);
    } catch (error) {
      console.error('Error verificando servicio:', error);
      setServiceAvailable(false);
    }
  };

  const loadBriefing = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const briefingData = await intelligenceService.getMorningBriefing();
      setBriefing(briefingData);
      
      if (!briefingData.success) {
        setError(briefingData.error || 'Error generando briefing');
      }
    } catch (error) {
      console.error('Error cargando briefing:', error);
      setError('No se pudo cargar el briefing matutino');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      const briefingData = await intelligenceService.getMorningBriefing(true);
      setBriefing(briefingData);
      
      if (!briefingData.success) {
        setError(briefingData.error || 'Error regenerando briefing');
      }
    } catch (error) {
      console.error('Error regenerando briefing:', error);
      setError('No se pudo regenerar el briefing');
    } finally {
      setRegenerating(false);
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <AlertTriangle className={`h-4 w-4 ${isDarkMode ? 'text-red-400' : 'text-red-500'}`} />;
      case 'medium':
        return <Clock className={`h-4 w-4 ${isDarkMode ? 'text-yellow-400' : 'text-yellow-500'}`} />;
      case 'low':
        return <Target className={`h-4 w-4 ${isDarkMode ? 'text-green-400' : 'text-green-500'}`} />;
      default:
        return <Target className={`h-4 w-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} />;
    }
  };

  const getInsightTypeIcon = (type: string) => {
    switch (type) {
      case 'priority':
        return <AlertTriangle className={`h-4 w-4 ${isDarkMode ? 'text-red-400' : 'text-red-500'}`} />;
      case 'opportunity':
        return <Brain className={`h-4 w-4 ${isDarkMode ? 'text-blue-400' : 'text-blue-500'}`} />;
      case 'recommendation':
        return <CheckCircle className={`h-4 w-4 ${isDarkMode ? 'text-green-400' : 'text-green-500'}`} />;
      case 'trend':
        return <TrendingUp className={`h-4 w-4 ${isDarkMode ? 'text-purple-400' : 'text-purple-500'}`} />;
      default:
        return <Target className={`h-4 w-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} />;
    }
  };

  const renderInsight = (insight: IntelligentInsight, index: number) => {
    const priorityColor = intelligenceService.getPriorityColor(insight.priority);
    
    return (
      <div
        key={index}
        className={`p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow ${
          insight.priority === 'high' 
            ? isDarkMode 
              ? 'border-red-800/50 bg-red-900/20' 
              : 'border-red-200 bg-red-50'
            : insight.priority === 'medium' 
              ? isDarkMode 
                ? 'border-yellow-800/50 bg-yellow-900/20' 
                : 'border-yellow-200 bg-yellow-50'
              : isDarkMode 
                ? 'border-green-800/50 bg-green-900/20' 
                : 'border-green-200 bg-green-50'
        }`}
        onClick={() => onInsightClick && onInsightClick(insight)}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center space-x-2">
            {getInsightTypeIcon(insight.type)}
            <h4 className={`font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
              {insight.title}
            </h4>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={insight.priority === 'high' ? 'destructive' : 'secondary'}>
              {insight.priority}
            </Badge>
            {getPriorityIcon(insight.priority)}
          </div>
        </div>
        
        <p className={`mb-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          {insight.message}
        </p>
        
        {insight.actions && insight.actions.length > 0 && (
          <div className="space-y-1">
            <p className={`text-sm font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>
              Acciones recomendadas:
            </p>
            <ul className={`text-sm space-y-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              {insight.actions.map((action, idx) => (
                <li key={idx} className="flex items-center space-x-2">
                  <span className={`w-1 h-1 rounded-full ${isDarkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderMetrics = () => {
    if (!briefing?.contextualMetrics) return null;

    const { totalValue, salesTrend, criticalAlerts, topProducts } = briefing.contextualMetrics;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Valor Total */}
        <div className={`p-4 text-white rounded-lg ${
          isDarkMode 
            ? 'bg-gradient-to-r from-blue-600 to-blue-700' 
            : 'bg-gradient-to-r from-blue-500 to-blue-600'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">{totalValue?.timeframe || 'Período actual'}</p>
              <p className="text-2xl font-bold">{formatCurrency(totalValue?.current || 0)}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-blue-100">Cambio</p>
              <p className={`text-sm font-semibold ${(totalValue?.change || 0) >= 0 ? 'text-green-200' : 'text-red-200'}`}>
                {(totalValue?.change || 0) >= 0 ? '+' : ''}{formatCurrency(totalValue?.change || 0)}
              </p>
            </div>
          </div>
        </div>

        {/* Tendencia de Ventas */}
        <div className={`p-4 text-white rounded-lg ${
          isDarkMode 
            ? 'bg-gradient-to-r from-green-600 to-green-700' 
            : 'bg-gradient-to-r from-green-500 to-green-600'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">{salesTrend?.timeframe || 'Últimos 7 días'}</p>
              <p className="text-2xl font-bold">{salesTrend?.current || 0}</p>
            </div>
            <div className="text-right">
              <TrendingUp className="w-5 h-5 text-green-200" />
              <p className={`text-sm font-semibold ${(salesTrend?.trend === 'up') ? 'text-green-200' : 'text-red-200'}`}>
                {(salesTrend?.trend === 'up') ? '+' : ''}{salesTrend?.percentage || 0}%
              </p>
            </div>
          </div>
        </div>

        {/* Alertas Críticas */}
        <div className={`p-4 text-white rounded-lg ${
          isDarkMode 
            ? 'bg-gradient-to-r from-red-600 to-red-700' 
            : 'bg-gradient-to-r from-red-500 to-red-600'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-100 text-sm">{criticalAlerts?.timeframe || 'Alertas activas'}</p>
              <p className="text-2xl font-bold">{criticalAlerts?.count || 0}</p>
            </div>
            <div className="text-right">
              <AlertTriangle className="w-5 h-5 text-red-200" />
              <p className="text-xs text-red-100">
                {criticalAlerts?.mostUrgent || 'Sin alertas críticas'}
              </p>
            </div>
          </div>
        </div>

        {/* Productos Top */}
        <div className={`p-4 text-white rounded-lg ${
          isDarkMode 
            ? 'bg-gradient-to-r from-purple-600 to-purple-700' 
            : 'bg-gradient-to-r from-purple-500 to-purple-600'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">Top Productos</p>
              <p className="text-2xl font-bold">{topProducts?.length || 0}</p>
            </div>
            <div className="text-right">
              <Target className="w-5 h-5 text-purple-200" />
              <p className="text-xs text-purple-100">
                {topProducts?.[0]?.name || 'No hay datos'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Card className={`${className} animate-pulse ${
        isDarkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-gray-200'
      }`}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className={`h-5 w-5 ${isDarkMode ? 'text-yellow-400' : 'text-yellow-500'}`} />
              <span className={isDarkMode ? 'text-slate-200' : 'text-slate-900'}>
                Cargando Briefing...
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1"
              title={isCollapsed ? 'Mostrar briefing' : 'Ocultar briefing'}
            >
              {isCollapsed ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardHeader>
        {!isCollapsed && (
          <CardContent className="transition-all duration-300 ease-in-out">
            <div className="space-y-4">
              <div className={`h-4 rounded w-full ${
                isDarkMode ? 'bg-slate-600' : 'bg-gray-300'
              }`}></div>
              <div className={`h-4 rounded w-3/4 ${
                isDarkMode ? 'bg-slate-600' : 'bg-gray-300'
              }`}></div>
              <div className={`h-32 rounded w-full ${
                isDarkMode ? 'bg-slate-600' : 'bg-gray-300'
              }`}></div>
            </div>
          </CardContent>
        )}
      </Card>
    );
  }

  if (error && !briefing) {
    return (
      <Card className={`${className} ${
        isDarkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-gray-200'
      }`}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Zap className={`h-5 w-5 ${isDarkMode ? 'text-yellow-400' : 'text-yellow-500'}`} />
              <span className={isDarkMode ? 'text-slate-200' : 'text-slate-900'}>
                Briefing Matutino
              </span>
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1"
              title={isCollapsed ? 'Mostrar briefing' : 'Ocultar briefing'}
            >
              {isCollapsed ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardHeader>
        {!isCollapsed && (
          <CardContent className="transition-all duration-300 ease-in-out">
            <Alert className={isDarkMode ? 'bg-red-900/20 border-red-800/50' : 'bg-red-50 border-red-200'}>
              <AlertTriangle className={`h-4 w-4 ${isDarkMode ? 'text-red-400' : 'text-red-500'}`} />
              <AlertDescription className={isDarkMode ? 'text-red-300' : 'text-red-800'}>
                {error}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadBriefing}
                  className="ml-2"
                >
                  Reintentar
                </Button>
              </AlertDescription>
            </Alert>
          </CardContent>
        )}
      </Card>
    );
  }

  return (
    <Card className={`${className} ${
      isDarkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-gray-200'
    }`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Zap className={`h-5 w-5 ${isDarkMode ? 'text-yellow-400' : 'text-yellow-500'}`} />
            <span className={isDarkMode ? 'text-slate-200' : 'text-slate-900'}>
              Briefing Matutino
            </span>
            {!serviceAvailable && (
              <Badge variant="secondary" className="ml-2">
                Modo Básico
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1"
              title={isCollapsed ? 'Mostrar briefing' : 'Ocultar briefing'}
            >
              {isCollapsed ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </Button>
            {!isCollapsed && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRegenerate}
                disabled={regenerating}
              >
                {regenerating ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {regenerating ? 'Generando...' : 'Actualizar'}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      {!isCollapsed && (
        <CardContent className="transition-all duration-300 ease-in-out">
          {briefing && (
          <div className="space-y-6">
            {/* Saludo y Resumen */}
            <div className={`p-4 rounded-lg border ${
              isDarkMode 
                ? 'bg-gradient-to-r from-blue-900/40 to-indigo-900/40 border-blue-800/50' 
                : 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200'
            }`}>
              <h3 className={`text-lg font-semibold mb-2 ${
                isDarkMode ? 'text-blue-200' : 'text-blue-900'
              }`}>
                {intelligenceService.formatGreeting(briefing.greeting)}
              </h3>
              <p className={isDarkMode ? 'text-blue-300' : 'text-blue-800'}>
                {briefing.summary}
              </p>
              <div className={`mt-2 text-xs ${
                isDarkMode ? 'text-blue-400' : 'text-blue-600'
              }`}>
                Generado el {formatDate(briefing.generated_at)}
              </div>
            </div>

            {/* Métricas Contextuales */}
            {renderMetrics()}

            {/* Prioridades Top */}
            {briefing.topPriorities && briefing.topPriorities.length > 0 && (
              <div>
                <h4 className={`text-lg font-semibold mb-3 flex items-center ${
                  isDarkMode ? 'text-gray-100' : 'text-gray-900'
                }`}>
                  <AlertTriangle className={`h-5 w-5 mr-2 ${
                    isDarkMode ? 'text-red-400' : 'text-red-500'
                  }`} />
                  Prioridades de Hoy
                </h4>
                <div className="space-y-3">
                  {briefing.topPriorities.map((priority, index) => renderInsight(priority, index))}
                </div>
              </div>
            )}

            {/* Oportunidades */}
            {briefing.opportunities && briefing.opportunities.length > 0 && (
              <div>
                <h4 className={`text-lg font-semibold mb-3 flex items-center ${
                  isDarkMode ? 'text-gray-100' : 'text-gray-900'
                }`}>
                  <Brain className={`h-5 w-5 mr-2 ${
                    isDarkMode ? 'text-blue-400' : 'text-blue-500'
                  }`} />
                  Oportunidades Detectadas
                </h4>
                <div className="space-y-3">
                  {briefing.opportunities.map((opportunity, index) => renderInsight(opportunity, index))}
                </div>
              </div>
            )}

            {/* Recomendaciones */}
            {briefing.recommendations && briefing.recommendations.length > 0 && (
              <div>
                <h4 className={`text-lg font-semibold mb-3 flex items-center ${
                  isDarkMode ? 'text-gray-100' : 'text-gray-900'
                }`}>
                  <CheckCircle className={`h-5 w-5 mr-2 ${
                    isDarkMode ? 'text-green-400' : 'text-green-500'
                  }`} />
                  Recomendaciones IA
                </h4>
                <div className="space-y-3">
                  {briefing.recommendations.map((recommendation, index) => renderInsight(recommendation, index))}
                </div>
              </div>
            )}

            {/* Footer con estado */}
            <div className={`border-t pt-4 ${
              isDarkMode ? 'border-slate-700' : 'border-gray-200'
            }`}>
              <div className={`flex items-center justify-between text-sm ${
                isDarkMode ? 'text-gray-400' : 'text-gray-600'
              }`}>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${briefing.success ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span>
                    {briefing.success ? 'Briefing completo' : 'Briefing con limitaciones'}
                  </span>
                </div>
                <div>
                  {serviceAvailable ? (
                    <span className={isDarkMode ? 'text-green-400' : 'text-green-600'}>
                      🤖 IA Activa
                    </span>
                  ) : (
                    <span className={isDarkMode ? 'text-yellow-400' : 'text-yellow-600'}>
                      ⚡ Modo Básico
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
      )}
    </Card>
  );
};

export default IntelligentBriefing; 