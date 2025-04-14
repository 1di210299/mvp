// src/components/BusinessRuleEditor.tsx
import React, { useState, useEffect } from 'react';
import {
  List,
  Plus,
  Edit,
  Trash2,
  AlertCircle,
  Save,
  X,
  Eye,
  EyeOff,
  Info,
  Filter,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { agentService } from '../api/agent-service';

// Define interfaces for business rules
interface BusinessRule {
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

const BusinessRuleEditor: React.FC = () => {
  const [rules, setRules] = useState<BusinessRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<BusinessRule | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [formData, setFormData] = useState<BusinessRule>({
    name: '',
    description: '',
    rule_type: 'threshold',
    metric: '',
    condition: 'gt',
    threshold_value: 0,
    action_type: 'notify',
    action_data: {},
    priority: 5,
    is_active: true
  });
  const [actionDataString, setActionDataString] = useState('{}');
  const [showHelpText, setShowHelpText] = useState(false);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const response = await agentService.getBusinessRules();
      setRules(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching business rules:', err);
      setError(err.response?.data?.message || 'Error al cargar reglas de negocio');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData({
        ...formData,
        [name]: checked
      });
    } else if (name === 'threshold_value') {
      setFormData({
        ...formData,
        [name]: parseFloat(value)
      });
    } else if (name === 'priority') {
      setFormData({
        ...formData,
        [name]: parseInt(value, 10)
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };
  
  const handleActionDataChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setActionDataString(e.target.value);
    try {
      const actionData = JSON.parse(e.target.value);
      setFormData({
        ...formData,
        action_data: actionData
      });
    } catch (err) {
      // Invalid JSON, but we still update the string value
      // Error handling will be done on submit
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate action_data JSON
    try {
      JSON.parse(actionDataString);
    } catch (err) {
      alert('Error: Los datos de acción deben ser un JSON válido');
      return;
    }
    
    try {
      if (editingRule?.id) {
        await agentService.updateBusinessRule(editingRule.id, formData);
      } else {
        await agentService.createBusinessRule(formData);
      }
      
      // Refresh rules list
      await fetchRules();
      
      // Close modal
      closeModal();
    } catch (err: any) {
      console.error('Error saving business rule:', err);
      alert(err.response?.data?.message || 'Error al guardar la regla de negocio');
    }
  };

  const handleEdit = (rule: BusinessRule) => {
    setEditingRule(rule);
    setFormData({
      ...rule,
      action_data: rule.action_data || {}
    });
    setActionDataString(JSON.stringify(rule.action_data || {}, null, 2));
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('¿Estás seguro de eliminar esta regla?')) {
      return;
    }
    
    try {
      await agentService.deleteBusinessRule(id);
      // Refresh list
      setRules(rules.filter(rule => rule.id !== id));
    } catch (err: any) {
      console.error('Error deleting business rule:', err);
      alert(err.response?.data?.message || 'Error al eliminar la regla de negocio');
    }
  };

  const openModal = () => {
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingRule(null);
    setFormData({
      name: '',
      description: '',
      rule_type: 'threshold',
      metric: '',
      condition: 'gt',
      threshold_value: 0,
      action_type: 'notify',
      action_data: {},
      priority: 5,
      is_active: true
    });
    setActionDataString('{}');
  };

  // Filter rules based on selected type
  const filteredRules = filterType === 'all' 
    ? rules 
    : rules.filter(rule => rule.rule_type === filterType);

  // Loading state
  if (loading && rules.length === 0) {
    return (
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 animate-pulse">
        <div className="h-6 w-1/3 bg-cyber-detail/30 rounded mb-4"></div>
        <div className="space-y-2">
          <div className="h-12 bg-cyber-detail/20 rounded"></div>
          <div className="h-12 bg-cyber-detail/20 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-cyber-dark/70 backdrop-blur-sm rounded-lg border border-cyber-cyan/20">
      {/* Header */}
      <div className="p-4 border-b border-cyber-detail/30 flex justify-between items-center">
        <div className="flex items-center">
          <List size={20} className="text-cyber-cyan mr-2" />
          <h3 className="text-lg font-semibold text-cyber-text">Reglas de Negocio</h3>
        </div>
        <div className="flex space-x-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-2 py-1 text-sm bg-cyber-detail/30 text-cyber-text border border-cyber-detail rounded"
          >
            <option value="all">Todas las reglas</option>
            <option value="threshold">Umbral</option>
            <option value="anomaly">Anomalía</option>
            <option value="opportunity">Oportunidad</option>
            <option value="risk">Riesgo</option>
          </select>
          <button
            onClick={openModal}
            className="px-3 py-1 bg-cyber-cyan text-cyber-dark rounded hover:bg-cyber-cyan/90 transition-colors flex items-center"
          >
            <Plus size={16} className="mr-1" />
            Nueva Regla
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="p-4">
          <div className="bg-red-900/30 border border-red-500/30 text-red-400 px-4 py-3 rounded mb-4">
            <div className="flex items-center">
              <AlertCircle size={18} className="mr-2" />
              <span>{error}</span>
            </div>
          </div>
        </div>
      )}

      {/* Help text toggle */}
      <div className="px-4 py-2 border-b border-cyber-detail/30">
        <button
          onClick={() => setShowHelpText(!showHelpText)}
          className="text-cyber-text/70 text-sm flex items-center hover:text-cyber-text transition-colors"
        >
          <Info size={16} className="mr-1.5 text-cyber-cyan" />
          {showHelpText ? 'Ocultar información' : 'Mostrar información sobre reglas de negocio'}
          {showHelpText ? <ChevronUp size={16} className="ml-1" /> : <ChevronDown size={16} className="ml-1" />}
        </button>
        
        {showHelpText && (
          <div className="mt-2 p-3 bg-cyber-detail/20 rounded-lg text-sm text-cyber-text/80">
            <p className="mb-2">
              Las reglas de negocio permiten al agente IA tomar decisiones automáticas basadas en condiciones específicas detectadas en los datos.
            </p>
            <h4 className="font-medium text-cyber-text mb-1">Tipos de reglas:</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li><span className="text-cyber-cyan">Umbral:</span> Se activa cuando una métrica específica supera, baja o iguala un valor determinado.</li>
              <li><span className="text-cyber-cyan">Anomalía:</span> Se activa cuando se detecta un comportamiento anormal en los datos.</li>
              <li><span className="text-cyber-cyan">Oportunidad:</span> Se activa cuando se identifica una posible oportunidad de negocio.</li>
              <li><span className="text-cyber-cyan">Riesgo:</span> Se activa cuando se detecta un posible riesgo para el negocio.</li>
            </ul>
            <h4 className="font-medium text-cyber-text mt-2 mb-1">Tipos de acciones:</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li><span className="text-cyber-cyan">Notificar:</span> Solo genera una alerta sin ejecutar acciones.</li>
              <li><span className="text-cyber-cyan">Sugerir:</span> Genera una sugerencia de acción que debe ser aprobada por el usuario.</li>
              <li><span className="text-cyber-cyan">Automática:</span> Ejecuta la acción automáticamente sin intervención del usuario.</li>
            </ul>
          </div>
        )}
      </div>

      {/* Rules list */}
      <div className="divide-y divide-cyber-detail/30">
        {filteredRules.length > 0 ? (
          filteredRules.map(rule => (
            <div key={rule.id} className="p-4 hover:bg-cyber-detail/10 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-cyber-text font-medium flex items-center">
                    {rule.name}
                    {!rule.is_active && (
                      <span className="ml-2 text-xs bg-yellow-900/30 text-yellow-400 px-2 py-0.5 rounded-full">
                        Inactiva
                      </span>
                    )}
                  </h4>
                  <p className="text-cyber-text/70 text-sm mt-0.5">
                    {rule.description || 'Sin descripción'}
                  </p>
                  <div className="flex flex-wrap mt-2 gap-2">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-cyber-detail/30 text-cyber-text/80">
                      Tipo: {rule.rule_type}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-cyber-detail/30 text-cyber-text/80">
                      Métrica: {rule.metric}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-cyber-detail/30 text-cyber-text/80">
                      Condición: {rule.condition} {rule.threshold_value}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-cyber-detail/30 text-cyber-text/80">
                      Acción: {rule.action_type}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-cyber-detail/30 text-cyber-text/80">
                      Prioridad: {rule.priority}
                    </span>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEdit(rule)}
                    className="p-1.5 text-cyber-text/70 hover:text-cyber-cyan hover:bg-cyber-detail/20 rounded transition-colors"
                    title="Editar regla"
                  >
                    <Edit size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(rule.id!)}
                    className="p-1.5 text-cyber-text/70 hover:text-red-400 hover:bg-cyber-detail/20 rounded transition-colors"
                    title="Eliminar regla"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="p-8 text-center">
            <p className="text-cyber-text/70 mb-2">No se encontraron reglas de negocio</p>
            <p className="text-cyber-text/50 text-sm mb-4">
              Las reglas de negocio permiten al agente IA tomar decisiones automáticas
            </p>
            <button
              onClick={openModal}
              className="px-4 py-2 bg-cyber-cyan text-cyber-dark rounded hover:bg-cyber-cyan/90 transition-colors"
            >
              Crear primera regla
            </button>
          </div>
        )}
      </div>

      {/* Modal for create/edit */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="bg-cyber-dark border border-cyber-cyan/30 rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-cyber-detail/30 flex justify-between items-center">
              <h2 className="text-xl font-bold text-cyber-text">
                {editingRule ? 'Editar Regla' : 'Nueva Regla de Negocio'}
              </h2>
              <button 
                onClick={closeModal}
                className="p-1.5 text-cyber-text/70 hover:text-cyber-cyan hover:bg-cyber-detail/20 rounded transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Nombre de la regla */}
                <div className="col-span-2">
                  <label htmlFor="name" className="block text-sm font-medium text-cyber-text/70 mb-1">
                    Nombre de la Regla *
                  </label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    value={formData.name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text"
                  />
                </div>

                {/* Descripción */}
                <div className="col-span-2">
                  <label htmlFor="description" className="block text-sm font-medium text-cyber-text/70 mb-1">
                    Descripción
                  </label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description || ''}
                    onChange={handleInputChange}
                    rows={2}
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text"
                  />
                </div>

                {/* Tipo de regla */}
                <div>
                  <label htmlFor="rule_type" className="block text-sm font-medium text-cyber-text/70 mb-1">
                    Tipo de Regla *
                  </label>
                  <select
                    id="rule_type"
                    name="rule_type"
                    value={formData.rule_type}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text"
                  >
                    <option value="threshold">Umbral</option>
                    <option value="anomaly">Anomalía</option>
                    <option value="opportunity">Oportunidad</option>
                    <option value="risk">Riesgo</option>
                  </select>
                </div>

                {/* Métrica */}
                <div>
                  <label htmlFor="metric" className="block text-sm font-medium text-cyber-text/70 mb-1">
                    Métrica a Monitorear *
                  </label>
                  <input
                    id="metric"
                    name="metric"
                    type="text"
                    value={formData.metric}
                    onChange={handleInputChange}
                    required
                    placeholder="Ej: sales, inventory, customer_count"
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text"
                  />
                </div>

                {/* Condición */}
                <div>
                  <label htmlFor="condition" className="block text-sm font-medium text-cyber-text/70 mb-1">
                    Condición *
                  </label>
                  <select
                    id="condition"
                    name="condition"
                    value={formData.condition}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text"
                  >
                    <option value="gt">Mayor que</option>
                    <option value="lt">Menor que</option>
                    <option value="eq">Igual a</option>
                    <option value="change">Cambio porcentual</option>
                  </select>
                </div>

                {/* Valor umbral */}
                <div>
                  <label htmlFor="threshold_value" className="block text-sm font-medium text-cyber-text/70 mb-1">
                    Valor Umbral *
                  </label>
                  <input
                    id="threshold_value"
                    name="threshold_value"
                    type="number"
                    step="any"
                    value={formData.threshold_value}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text"
                  />
                </div>

                {/* Tipo de acción */}
                <div>
                  <label htmlFor="action_type" className="block text-sm font-medium text-cyber-text/70 mb-1">
                    Tipo de Acción *
                  </label>
                  <select
                    id="action_type"
                    name="action_type"
                    value={formData.action_type}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text"
                  >
                    <option value="notify">Notificar</option>
                    <option value="suggest">Sugerir acción</option>
                    <option value="auto">Ejecutar automáticamente</option>
                  </select>
                </div>

                {/* Prioridad */}
                <div>
                  <label htmlFor="priority" className="block text-sm font-medium text-cyber-text/70 mb-1">
                    Prioridad (1-10) *
                  </label>
                  <input
                    id="priority"
                    name="priority"
                    type="number"
                    min="1"
                    max="10"
                    value={formData.priority}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text"
                  />
                </div>

                {/* Activo */}
                <div className="flex items-center space-x-2">
                  <input
                    id="is_active"
                    name="is_active"
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={handleInputChange}
                    className="h-4 w-4 rounded border-cyber-detail/50 bg-cyber-detail/20 text-cyber-cyan focus:ring-cyber-cyan"
                  />
                  <label htmlFor="is_active" className="text-sm font-medium text-cyber-text/70">
                    Activar regla
                  </label>
                </div>

                {/* Datos de acción */}
                <div className="col-span-2">
                  <label htmlFor="action_data" className="block text-sm font-medium text-cyber-text/70 mb-1">
                    Datos de Acción (JSON)
                  </label>
                  <textarea
                    id="action_data"
                    name="action_data"
                    value={actionDataString}
                    onChange={handleActionDataChange}
                    rows={5}
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text font-mono text-sm"
                  />
                  <p className="text-xs text-cyber-text/60 mt-1">
                    Ejemplo: {"{ \"action_type\": \"price_change\", \"percentage\": 5, \"reason\": \"Aumento de demanda\" }"}
                  </p>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-cyber-detail/30">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 border border-cyber-detail/50 text-cyber-text rounded hover:bg-cyber-detail/20 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-cyber-cyan text-cyber-dark rounded hover:bg-cyber-cyan/90 transition-colors flex items-center"
                >
                  <Save size={16} className="mr-1.5" />
                  {editingRule ? 'Actualizar' : 'Crear'} Regla
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default BusinessRuleEditor;