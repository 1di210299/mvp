// src/components/AgentSuggestions.tsx
import React, { useState, useEffect } from 'react';
import { agentService, AgentAction } from '../api/agent-service';
import { CheckCircle, XCircle, AlertTriangle, TrendingUp, Package, DollarSign, Users, Target } from 'lucide-react';

const AgentSuggestions: React.FC = () => {
  const [actions, setActions] = useState<AgentAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSuggestedActions();
  }, []);

  const fetchSuggestedActions = async () => {
    try {
      setLoading(true);
      const response = await agentService.getAgentActions({
        status: 'suggested,pending'
      });
      setActions(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching agent actions:', err);
      setError(err.response?.data?.message || 'Error al cargar sugerencias del agente');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await agentService.approveAction(id);
      // Actualizar la lista después de aprobar
      setActions(actions.filter(action => action.id !== id));
    } catch (err: any) {
      console.error('Error approving action:', err);
      alert(err.response?.data?.message || 'Error al aprobar la acción');
    }
  };

  const handleReject = async (id: number) => {
    try {
      const reason = prompt('¿Por qué estás rechazando esta acción? (opcional)');
      await agentService.rejectAction(id, reason || undefined);
      // Actualizar la lista después de rechazar
      setActions(actions.filter(action => action.id !== id));
    } catch (err: any) {
      console.error('Error rejecting action:', err);
      alert(err.response?.data?.message || 'Error al rechazar la acción');
    }
  };

  // Función para renderizar el icono según el tipo de acción
  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'price_change':
        return <DollarSign className="text-cyber-cyan" size={20} />;
      case 'inventory':
        return <Package className="text-cyber-cyan" size={20} />;
      case 'marketing':
        return <Target className="text-cyber-cyan" size={20} />;
      case 'customer':
        return <Users className="text-cyber-cyan" size={20} />;
      default:
        return <TrendingUp className="text-cyber-cyan" size={20} />;
    }
  };

  if (loading) {
    return (
      <div className="p-4 bg-cyber-dark/70 backdrop-blur-sm rounded-lg border border-cyber-cyan/20 animate-pulse">
        <div className="h-6 w-2/3 bg-cyber-detail/30 rounded mb-4"></div>
        <div className="h-20 bg-cyber-detail/20 rounded mb-3"></div>
        <div className="h-20 bg-cyber-detail/20 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-cyber-dark/70 backdrop-blur-sm rounded-lg border border-cyber-cyan/20">
        <div className="flex items-center text-red-400 mb-2">
          <AlertTriangle size={18} className="mr-2" />
          <h3 className="font-medium">Error</h3>
        </div>
        <p className="text-cyber-text/70">{error}</p>
        <button 
          onClick={fetchSuggestedActions}
          className="mt-3 px-4 py-2 bg-cyber-cyan text-cyber-dark rounded"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (actions.length === 0) {
    return (
      <div className="p-4 bg-cyber-dark/70 backdrop-blur-sm rounded-lg border border-cyber-cyan/20">
        <div className="flex items-center mb-2">
          <TrendingUp size={18} className="mr-2 text-cyber-cyan" />
          <h3 className="font-medium text-cyber-text">Sugerencias del Agente</h3>
        </div>
        <p className="text-cyber-text/70">No hay acciones sugeridas en este momento.</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-cyber-dark/70 backdrop-blur-sm rounded-lg border border-cyber-cyan/20">
      <div className="flex items-center mb-4">
        <TrendingUp size={18} className="mr-2 text-cyber-cyan" />
        <h3 className="font-medium text-cyber-text">Sugerencias del Agente IA</h3>
      </div>
      
      <div className="space-y-4">
        {actions.map(action => (
          <div key={action.id} className="bg-cyber-detail/20 rounded-lg p-4 border border-cyber-detail/40">
            <div className="flex items-start">
              <div className="mr-3 mt-1">
                {getActionIcon(action.action_type)}
              </div>
              <div className="flex-grow">
                <h4 className="font-medium text-cyber-text">{action.description}</h4>
                
                {action.expected_impact && (
                  <p className="text-cyber-text/70 text-sm mt-1">
                    <strong>Impacto esperado:</strong> {action.expected_impact}
                  </p>
                )}
                
                <div className="mt-2 flex items-center">
                  <div className="text-xs bg-cyber-cyan/20 text-cyber-cyan px-2 py-1 rounded">
                    Confianza: {(action.confidence * 100).toFixed(0)}%
                  </div>
                  {action.rule_name && (
                    <div className="ml-2 text-xs bg-cyber-detail/30 text-cyber-text/70 px-2 py-1 rounded">
                      Regla: {action.rule_name}
                    </div>
                  )}
                </div>
                
                <div className="mt-3 flex space-x-2">
                  <button
                    onClick={() => handleApprove(action.id!)}
                    className="flex items-center px-3 py-1.5 bg-green-900/30 text-green-400 rounded hover:bg-green-900/50 transition-colors"
                  >
                    <CheckCircle size={16} className="mr-1" />
                    Aprobar
                  </button>
                  <button
                    onClick={() => handleReject(action.id!)}
                    className="flex items-center px-3 py-1.5 bg-red-900/30 text-red-400 rounded hover:bg-red-900/50 transition-colors"
                  >
                    <XCircle size={16} className="mr-1" />
                    Rechazar
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentSuggestions;