// src/pages/BusinessRulesPage.tsx
import React, { useState, useEffect } from 'react';
import { agentService, BusinessRule } from '../api/agent-service';
import { Plus, Edit, Trash2, AlertCircle } from 'lucide-react';

const BusinessRulesPage: React.FC = () => {
  const [rules, setRules] = useState<BusinessRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<BusinessRule | null>(null);
  
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
    try {
      const actionData = JSON.parse(e.target.value);
      setFormData({
        ...formData,
        action_data: actionData
      });
    } catch (err) {
      // Manejar error de JSON inválido si es necesario
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingRule) {
        await agentService.updateBusinessRule(editingRule.id!, formData);
      } else {
        await agentService.createBusinessRule(formData);
      }
      
      // Refrescar lista de reglas
      fetchRules();
      // Cerrar modal
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
    setIsModalOpen(true);
  };
  
  const handleDelete = async (id: number) => {
    if (!window.confirm('¿Estás seguro de eliminar esta regla?')) {
      return;
    }
    
    try {
      await agentService.deleteBusinessRule(id);
      // Refrescar lista
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
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-cyber-text">Reglas de Negocio</h1>
        <button
          onClick={openModal}
          className="flex items-center px-4 py-2 bg-cyber-cyan text-cyber-dark rounded hover:bg-cyber-cyan/90 transition-colors"
        >
          <Plus size={18} className="mr-2" />
          Nueva Regla
        </button>
      </div>
      
      {loading ? (
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-cyber-cyan/20 animate-pulse">
          <div className="h-6 w-1/2 bg-cyber-detail/30 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-cyber-detail/20 rounded"></div>
            <div className="h-20 bg-cyber-detail/20 rounded"></div>
          </div>
        </div>
      ) : error ? (
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-red-500/20">
          <div className="flex items-center text-red-400 mb-2">
            <AlertCircle size={18} className="mr-2" />
            <h3 className="font-medium">Error</h3>
          </div>
          <p className="text-cyber-text/70">{error}</p>
          <button 
            onClick={fetchRules}
            className="mt-3 px-4 py-2 bg-cyber-cyan text-cyber-dark rounded"
          >
            Reintentar
          </button>
        </div>
      ) : rules.length === 0 ? (
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-6 rounded-lg border border-cyber-cyan/20 text-center">
          <p className="text-cyber-text/70 mb-4">No hay reglas de negocio configuradas.</p>
          <button
            onClick={openModal}
            className="px-4 py-2 bg-cyber-cyan text-cyber-dark rounded hover:bg-cyber-cyan/90 transition-colors"
          >
            Crear Primera Regla
          </button>
        </div>
      ) : (
        <div className="bg-cyber-dark/70 backdrop-blur-sm rounded-lg border border-cyber-cyan/20">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-cyber-detail/30">
                  <th className="py-3 px-4 text-left text-cyber-text">Nombre</th>
                  <th className="py-3 px-4 text-left text-cyber-text">Tipo</th>
                  <th className="py-3 px-4 text-left text-cyber-text">Métrica</th>
                  <th className="py-3 px-4 text-left text-cyber-text">Condición</th>
                  <th className="py-3 px-4 text-left text-cyber-text">Acción</th>
                  <th className="py-3 px-4 text-left text-cyber-text">Prioridad</th>
                  <th className="py-3 px-4 text-left text-cyber-text">Estado</th>
                  <th className="py-3 px-4 text-right text-cyber-text">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cyber-detail/30">
                {rules.map(rule => (
                  <tr key={rule.id} className="hover:bg-cyber-detail/10">
                    <td className="py-3 px-4 text-cyber-text">{rule.name}</td>
                    <td className="py-3 px-4 text-cyber-text/70">{rule.rule_type}</td>
                    <td className="py-3 px-4 text-cyber-text/70">{rule.metric}</td>
                    <td className="py-3 px-4 text-cyber-text/70">
                      {rule.condition} {rule.threshold_value}
                    </td>
                    <td className="py-3 px-4 text-cyber-text/70">{rule.action_type}</td>
                    <td className="py-3 px-4 text-cyber-text/70">{rule.priority}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        rule.is_active 
                          ? 'bg-green-900/30 text-green-400' 
                          : 'bg-red-900/30 text-red-400'
                      }`}>
                        {rule.is_active ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => handleEdit(rule)}
                          className="p-1 text-cyber-text/70 hover:text-cyber-cyan transition-colors"
                        >
                          <Edit size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(rule.id!)}
                          className="p-1 text-cyber-text/70 hover:text-red-400 transition-colors"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Modal para crear/editar reglas */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="bg-cyber-dark border border-cyber-cyan/30 rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-cyber-detail/30">
              <h2 className="text-xl font-bold text-cyber-text">
                {editingRule ? 'Editar Regla' : 'Nueva Regla de Negocio'}
              </h2>
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
                    value={JSON.stringify(formData.action_data, null, 2)}
                    onChange={handleActionDataChange}
                    rows={5}
                    className="w-full px-3 py-2 bg-cyber-detail/20 border border-cyber-detail/50 rounded text-cyber-text font-mono text-sm"
                  />
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
                  className="px-4 py-2 bg-cyber-cyan text-cyber-dark rounded hover:bg-cyber-cyan/90 transition-colors"
                >
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

export default BusinessRulesPage;