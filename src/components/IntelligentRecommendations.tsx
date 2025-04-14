// src/components/IntelligentRecommendations.tsx
import React, { useState, useEffect } from 'react';
import {
  Brain,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  BarChart2,
  TrendingUp,
  Shield,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';
import { decisionService, RecommendationResponse, RecommendationOption } from '../api/decision-service';

interface IntelligentRecommendationsProps {
  datasetId: number | string;
  actionType: 'pricing' | 'inventory' | 'marketing' | string;
  context?: any;
  onActionTaken?: (action: any, feedback: any) => void;
}

const IntelligentRecommendations: React.FC<IntelligentRecommendationsProps> = ({
  datasetId,
  actionType,
  context,
  onActionTaken
}) => {
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAllOptions, setShowAllOptions] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [implementingAction, setImplementingAction] = useState(false);
  const [feedback, setFeedback] = useState<{
    actionId?: number;
    success_score?: number;
    feedback?: string;
  }>({});

  useEffect(() => {
    getRecommendation();
  }, [datasetId, actionType]);

  const getRecommendation = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await decisionService.getRecommendation({
        dataset_id: datasetId,
        action_type: actionType,
        context
      });
      setRecommendation(response.data);
    } catch (err: any) {
      console.error('Error getting recommendation:', err);
      setError(err.response?.data?.error || 'Error al obtener recomendación');
    } finally {
      setLoading(false);
    }
  };

  const handleImplementAction = async (option: any) => {
    setImplementingAction(true);
    try {
      // In a real system, this would call an API to implement the action
      // For now, we'll simulate a successful implementation
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Assuming the action was implemented successfully
      // In a real implementation, you would get the actionId from the API response
      const actionId = Date.now(); // Using timestamp as a placeholder
      
      setFeedback({
        actionId
      });
      
      if (onActionTaken) {
        onActionTaken(option, { actionId });
      }
    } catch (err) {
      setError('Error al implementar la acción');
    } finally {
      setImplementingAction(false);
    }
  };

  const handleProvideFeedback = async (success_score: number) => {
    if (!feedback.actionId) return;
    
    try {
      setLoading(true);
      await decisionService.provideActionFeedback(
        feedback.actionId,
        {
          success_score,
          feedback: feedback.feedback
        }
      );
      
      // Reset state after feedback
      setFeedback({});
      
      // Get new recommendation
      getRecommendation();
    } catch (err: any) {
      console.error('Error providing feedback:', err);
      setError(err.response?.data?.error || 'Error al enviar feedback');
    } finally {
      setLoading(false);
    }
  };

  // Helper functions for styling
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.7) return 'text-green-400';
    if (confidence >= 0.5) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'alta':
        return 'text-red-400 bg-red-900/30 border-red-500/30';
      case 'media':
        return 'text-yellow-400 bg-yellow-900/30 border-yellow-500/30';
      case 'baja':
        return 'text-blue-400 bg-blue-900/30 border-blue-500/30';
      default:
        return 'text-gray-400 bg-gray-900/30 border-gray-500/30';
    }
  };

  // Loading state
  if (loading && !recommendation) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 animate-pulse">
        <div className="h-6 w-2/3 bg-cyber-detail/30 rounded mb-4"></div>
        <div className="h-24 bg-cyber-detail/20 rounded mb-3"></div>
        <div className="h-12 bg-cyber-detail/20 rounded"></div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
        <div className="flex items-center text-red-400 mb-2">
          <AlertTriangle size={18} className="mr-2" />
          <h3 className="font-medium">Error</h3>
        </div>
        <p className="text-cyber-text/70">{error}</p>
        <button
          onClick={getRecommendation}
          className="mt-3 px-4 py-2 bg-cyber-cyan text-cyber-dark rounded"
        >
          Reintentar
        </button>
      </div>
    );
  }

  // Feedback state - after action implementation
  if (feedback.actionId) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
        <div className="flex items-center mb-4">
          <ThumbsUp size={20} className="text-cyber-cyan mr-2" />
          <h3 className="text-lg font-semibold text-cyber-text">¿Cómo evaluaría el resultado?</h3>
        </div>
        <p className="text-cyber-text/80 mb-4">
          Su feedback ayuda al agente IA a aprender y mejorar sus futuras recomendaciones.
        </p>
        <div className="space-y-3 mb-4">
          <textarea
            value={feedback.feedback || ''}
            onChange={(e) => setFeedback({...feedback, feedback: e.target.value})}
            placeholder="Describa los resultados obtenidos (opcional)..."
            className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text"
            rows={3}
          />
          <div className="flex justify-between items-center">
            <div className="text-sm text-cyber-text/70">
              Seleccione una calificación:
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => handleProvideFeedback(0.8)}
                className="px-4 py-2 bg-green-900/30 text-green-400 rounded hover:bg-green-900/50 transition-colors"
              >
                <ThumbsUp size={16} className="mr-1 inline" /> Excelente
              </button>
              <button
                onClick={() => handleProvideFeedback(0.4)}
                className="px-4 py-2 bg-blue-900/30 text-blue-400 rounded hover:bg-blue-900/50 transition-colors"
              >
                <ThumbsUp size={16} className="mr-1 inline" /> Bueno
              </button>
              <button
                onClick={() => handleProvideFeedback(0)}
                className="px-4 py-2 bg-gray-900/30 text-gray-400 rounded hover:bg-gray-900/50 transition-colors"
              >
                Neutral
              </button>
              <button
                onClick={() => handleProvideFeedback(-0.4)}
                className="px-4 py-2 bg-yellow-900/30 text-yellow-400 rounded hover:bg-yellow-900/50 transition-colors"
              >
                <ThumbsDown size={16} className="mr-1 inline" /> Regular
              </button>
              <button
                onClick={() => handleProvideFeedback(-0.8)}
                className="px-4 py-2 bg-red-900/30 text-red-400 rounded hover:bg-red-900/50 transition-colors"
              >
                <ThumbsDown size={16} className="mr-1 inline" /> Malo
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // No recommendation available
  if (!recommendation) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
        <div className="flex items-center mb-4">
          <Brain size={20} className="text-cyber-cyan mr-2" />
          <h3 className="text-lg font-semibold text-cyber-text">Recomendaciones Inteligentes</h3>
        </div>
        <p className="text-cyber-text/70 mb-3">
          No hay recomendaciones disponibles para este dataset. Seleccione otro dataset o tipo de acción.
        </p>
        <button
          onClick={getRecommendation}
          className="px-4 py-2 bg-cyber-cyan text-cyber-dark rounded"
        >
          Intentar de nuevo
        </button>
      </div>
    );
  }

  // Main recommendation display
  return (
    <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20">
      <div className="flex items-center mb-4">
        <Brain size={20} className="text-cyber-cyan mr-2" />
        <h3 className="text-lg font-semibold text-cyber-text">Recomendación del Agente IA</h3>
        <div className="ml-2 px-2 py-0.5 bg-cyber-cyan/20 rounded-full text-xs text-cyber-cyan">
          {actionType} - {recommendation.objective.replace('_', ' ')}
        </div>
      </div>

      {/* Primary recommendation */}
      <div className="bg-cyber-detail/20 rounded-lg p-4 mb-4 border border-cyber-cyan/30">
        <div className="flex items-start">
          <div className="bg-cyber-cyan/20 rounded-full p-2 mr-3">
            <TrendingUp size={20} className="text-cyber-cyan" />
          </div>
          <div className="flex-grow">
            <h4 className="text-md font-medium text-cyber-text mb-1">
              {recommendation.recommended_option?.description || "Acción recomendada"}
            </h4>
            <p className="text-sm text-cyber-text/70 mb-2">
              {recommendation.reasoning.narrative}
            </p>
            <div className="flex items-center text-xs mb-3">
              <span className={`${getConfidenceColor(recommendation.all_options[0]?.confidence || 0)}`}>
                Confianza: {Math.round((recommendation.all_options[0]?.confidence || 0) * 100)}%
              </span>
              <span className="mx-2">•</span>
              <span className="text-cyber-text/60">
                Objetivo: {recommendation.objective.replace('_', ' ')}
              </span>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => handleImplementAction(recommendation.recommended_option)}
                disabled={implementingAction}
                className={`px-3 py-1.5 ${
                  implementingAction
                    ? "bg-cyber-detail/30 text-cyber-text/50 cursor-not-allowed"
                    : "bg-cyber-cyan text-cyber-dark hover:bg-cyber-cyan/90"
                } rounded transition-colors`}
              >
                {implementingAction ? (
                  <>
                    <span className="animate-pulse">Implementando...</span>
                  </>
                ) : (
                  "Implementar acción"
                )}
              </button>
              <button
                onClick={() => setShowExplanation(!showExplanation)}
                className="px-3 py-1.5 bg-cyber-detail/30 text-cyber-text rounded hover:bg-cyber-detail/50 transition-colors"
              >
                {showExplanation ? (
                  <>
                    <ChevronUp size={16} className="inline mr-1" /> Ocultar explicación
                  </>
                ) : (
                  <>
                    <ChevronDown size={16} className="inline mr-1" /> Ver explicación
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Detailed explanation */}
        {showExplanation && (
          <div className="mt-4 pt-4 border-t border-cyber-detail/30">
            <h5 className="text-sm font-medium text-cyber-text mb-2">Factores clave en esta decisión:</h5>
            <div className="space-y-2 mb-3">
              {recommendation.reasoning.factor_explanations.slice(0, 3).map((factor, idx) => (
                <div key={idx} className="bg-cyber-detail/30 p-2 rounded">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-medium text-cyber-cyan">{factor.factor}</span>
                    <span className="text-xs text-cyber-text/70">
                      Importancia: {factor.importance} ({(factor.weight * 100).toFixed(0)}%)
                    </span>
                  </div>
                  <p className="text-xs text-cyber-text/80">{factor.explanation}</p>
                  <div className="w-full bg-cyber-detail/50 h-1.5 mt-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-cyber-cyan h-1.5 rounded-full"
                      style={{ width: `${factor.score * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            {/* Risk factors */}
            {recommendation.all_options[0]?.risks && recommendation.all_options[0].risks.length > 0 && (
              <div className="mb-3">
                <h5 className="text-sm font-medium text-cyber-text mb-2">Riesgos potenciales:</h5>
                <div className="space-y-2">
                  {recommendation.all_options[0].risks.map((risk, idx) => (
                    <div
                      key={idx}
                      className={`p-2 rounded border ${getSeverityColor(risk.severity)}`}
                    >
                      <div className="flex items-start">
                        <Shield size={14} className="mr-1.5 mt-0.5" />
                        <div>
                          <span className="text-xs font-medium">{risk.factor}</span>
                          <p className="text-xs">{risk.description}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Business context */}
            {recommendation.reasoning.business_context && (
              <div className="text-xs text-cyber-text/70 border-t border-cyber-detail/30 pt-2 mt-2">
                <span className="font-medium">Contexto empresarial:</span> {recommendation.reasoning.business_context}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Alternative options toggle */}
      <div className="mb-2">
        <button
          onClick={() => setShowAllOptions(!showAllOptions)}
          className="text-sm text-cyber-cyan hover:text-cyber-cyan/80 transition-colors flex items-center"
        >
          {showAllOptions ? (
            <>
              <ChevronUp size={16} className="mr-1" /> Ocultar opciones alternativas
            </>
          ) : (
            <>
              <ChevronDown size={16} className="mr-1" /> Mostrar opciones alternativas ({recommendation.all_options.length - 1})
            </>
          )}
        </button>
      </div>

      {/* Alternative options */}
      {showAllOptions && recommendation.all_options.length > 1 && (
        <div className="space-y-3 mt-2">
          {recommendation.all_options.slice(1).map((option, idx) => (
            <div key={idx} className="bg-cyber-detail/10 rounded-lg p-3 border border-cyber-detail/30">
              <div className="flex items-start">
                <div className="flex-grow">
                  <h5 className="text-sm font-medium text-cyber-text mb-1">
                    {option.option?.description || `Alternativa ${idx + 1}`}
                  </h5>
                  <p className="text-xs text-cyber-text/70 mb-2">
                    {option.expected_outcome?.narrative || "No hay descripción de resultados esperados."}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className={`text-xs ${getConfidenceColor(option.confidence)}`}>
                      Confianza: {Math.round(option.confidence * 100)}%
                    </span>
                    <button
                      onClick={() => handleImplementAction(option.option)}
                      disabled={implementingAction}
                      className="text-xs px-2 py-1 bg-cyber-detail/30 text-cyber-text rounded hover:bg-cyber-detail/50 transition-colors"
                    >
                      Implementar esta alternativa
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default IntelligentRecommendations;