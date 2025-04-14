// src/pages/DatasetDetailPage.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, 
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, Cell 
} from 'recharts';
import { 
  ArrowLeft, 
  Table, 
  Send, 
  FileText,
  Calendar,
  BarChart2,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Brain,
  AlertTriangle,
  Trash2,
  Zap
} from 'lucide-react';
import { datasetService, assistantService, chartService } from '../api/services';
import { monitorService } from '../api/monitor-service';
import DataMonitorPanel from '../components/DataMonitorPanel';
import ProactiveInsights from '../components/ProactiveInsights';
import AgentSuggestions from '../components/AgentSuggestions';

// Paleta de colores para los gráficos
const colors = ['#00E6E6', '#0094FF', '#6B66FF', '#9C66FF', '#FF66D9'];

// Tipado para un mensaje en el chat
interface ChatMessage {
  id: number;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  visualizations?: any[];
  insights?: any[];
}

const DatasetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'structure' | 'chat' | 'agent'>('overview');
  const [dataset, setDataset] = useState<any>(null);
  const [context, setContext] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Estados para el chat
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  
  // Datos para visualizaciones
  const [distributionData, setDistributionData] = useState<any[]>([]);
  const [trendsData, setTrendsData] = useState<any[]>([]);
  const [datasetLoaded, setDatasetLoaded] = useState(false);

  // Cargar datos del dataset
  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        
        // Obtener dataset
        const datasetResponse = await datasetService.getById(id);
        setDataset(datasetResponse.data);
        
        // Obtener contexto
        const contextResponse = await datasetService.getContext(id);
        setContext(contextResponse.data);
        
        // Mensaje inicial del asistente
        setChatMessages([{
          id: 1,
          text: `Hola, soy el asistente de datos para el dataset "${datasetResponse.data.name}". ¿En qué puedo ayudarte?`,
          sender: 'assistant',
          timestamp: new Date()
        }]);
        
        setDatasetLoaded(true);
      } catch (err: any) {
        console.error('Error fetching dataset:', err);
        setError(err.response?.data?.error || 'Error al cargar el dataset');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  // Cargar visualizaciones
  useEffect(() => {
    // Modificar el código en loadVisualizations:
const loadVisualizations = async () => {
  if (!id || !datasetLoaded) return;
  
  try {
    // Obtener los datos del dataset usando el método correcto
    const dataResponse = await datasetService.getDatasetData(id);
    
    if (dataResponse && dataResponse.data) {
      // Ahora usar chartService con los datos reales
      const distributionResponse = await chartService.generateCategoryChart(
        dataResponse.data,
        'category'
      );
      
      if (distributionResponse.data && distributionResponse.data.raw_data) {
        setDistributionData(distributionResponse.data.raw_data);
      }
      
      const trendsResponse = await chartService.generateSalesChart(dataResponse.data);
      if (trendsResponse.data && trendsResponse.data.raw_data) {
        setTrendsData(trendsResponse.data.raw_data);
      }
    }
  } catch (err) {
    console.error('Error loading visualizations:', err);
  }
};
    
    loadVisualizations();
  }, [id, datasetLoaded]);

  // Manejar eliminación del dataset
  const handleDelete = async () => {
    if (!id || !window.confirm('¿Estás seguro de eliminar este dataset?')) {
      return;
    }

    try {
      await datasetService.delete(id);
      navigate('/dashboard/datasets');
    } catch (err: any) {
      console.error('Error deleting dataset:', err);
      alert(err.response?.data?.error || 'Error al eliminar el dataset');
    }
  };

  // Manejar envío de mensajes en el chat
  const handleSendMessage = useCallback(async () => {
    if (!messageInput.trim() || isSending || !id) return;

    // Mensaje del usuario
    const userMessage: ChatMessage = {
      id: Date.now(),
      text: messageInput,
      sender: 'user',
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setMessageInput('');
    setIsSending(true);

    try {
      // Llamar a la API real del asistente
      const response = await assistantService.analyze({
        message: messageInput,
        datasetId: id,
        datasetContext: context,
        language: 'es',
        messageHistory: chatMessages.slice(-5).map(m => ({
          text: m.text,
          sender: m.sender
        }))
      });

      // Añadir la respuesta del asistente
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        text: response.data.message,
        visualizations: response.data.visualizations || [],
        insights: response.data.insights || [],
        sender: 'assistant',
        timestamp: new Date()
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Error getting assistant response:', err);
      
      // Mensaje de error
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        text: "Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, intenta nuevamente.",
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  }, [messageInput, isSending, id, context, chatMessages]);

  // Mostrar loading
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-cyber-cyan"></div>
      </div>
    );
  }

  // Mostrar error
  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-900/30 border border-red-500/30 text-red-400 px-4 py-3 rounded mb-4">
          <h3 className="font-medium mb-2">Error</h3>
          <p>{error}</p>
          <Link to="/dashboard/datasets" className="mt-4 inline-flex items-center text-cyber-cyan hover:underline">
            <ArrowLeft size={16} className="mr-1" />
            Volver a Datasets
          </Link>
        </div>
      </div>
    );
  }

  // Si no hay dataset
  if (!dataset) {
    return (
      <div className="p-6">
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded border border-cyber-cyan/20 shadow">
          <p className="text-cyber-text/70">Dataset no encontrado</p>
          <Link to="/dashboard/datasets" className="mt-4 inline-flex items-center text-cyber-cyan hover:underline">
            <ArrowLeft size={16} className="mr-1" />
            Volver a Datasets
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      {/* Cabecera del dataset */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex items-start">
          <Link 
            to="/dashboard/datasets"
            className="mr-3 p-2 text-cyber-text/70 hover:text-cyber-cyan hover:bg-cyber-detail/20 rounded transition-colors"
          >
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-cyber-text">{dataset.name}</h1>
            <p className="text-cyber-text/70 mt-1">{dataset.description || 'Sin descripción'}</p>
            <div className="flex items-center mt-2 text-xs text-cyber-text/60">
              <span className="flex items-center">
                <Calendar size={14} className="mr-1" />
                Creado: {new Date(dataset.created_at).toLocaleDateString()}
              </span>
              <span className="mx-2">•</span>
              <span className="flex items-center">
                <FileText size={14} className="mr-1" />
                {context?.columnNames?.length || 0} columnas
              </span>
            </div>
          </div>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-2">
          <button 
            className="px-3 py-1.5 bg-red-900/30 text-red-400 rounded hover:bg-red-900/50 transition-colors flex items-center"
            onClick={handleDelete}
          >
            <Trash2 size={16} className="mr-1" />
            Eliminar
          </button>
        </div>
      </div>
      
      {/* Tabs de navegación */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-2 rounded-lg border border-cyber-cyan/20 shadow-lg">
        <div className="flex flex-wrap">
          <button 
            className={`px-4 py-2 rounded-md mr-2 flex items-center ${
              activeTab === 'overview' 
                ? 'bg-cyber-cyan text-cyber-dark' 
                : 'bg-transparent text-cyber-text/70 hover:bg-cyber-detail/20'
            }`}
            onClick={() => setActiveTab('overview')}
          >
            <BarChart2 size={16} className="mr-1.5" />
            Resumen
          </button>
          <button 
            className={`px-4 py-2 rounded-md mr-2 flex items-center ${
              activeTab === 'structure' 
                ? 'bg-cyber-cyan text-cyber-dark' 
                : 'bg-transparent text-cyber-text/70 hover:bg-cyber-detail/20'
            }`}
            onClick={() => setActiveTab('structure')}
          >
            <Table size={16} className="mr-1.5" />
            Estructura
          </button>
          <button 
            className={`px-4 py-2 rounded-md mr-2 flex items-center ${
              activeTab === 'chat' 
                ? 'bg-cyber-cyan text-cyber-dark' 
                : 'bg-transparent text-cyber-text/70 hover:bg-cyber-detail/20'
            }`}
            onClick={() => setActiveTab('chat')}
          >
            <HelpCircle size={16} className="mr-1.5" />
            Asistente
          </button>
          <button 
            className={`px-4 py-2 rounded-md flex items-center ${
              activeTab === 'agent' 
                ? 'bg-cyber-cyan text-cyber-dark' 
                : 'bg-transparent text-cyber-text/70 hover:bg-cyber-detail/20'
            }`}
            onClick={() => setActiveTab('agent')}
          >
            <Brain size={16} className="mr-1.5" />
            Agente IA
          </button>
        </div>
      </div>
      
      {/* Contenido principal según la tab activa */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Distribución */}
          <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
            <h2 className="text-lg font-semibold text-cyber-text mb-4">Distribución de datos</h2>
            {distributionData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={distributionData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      nameKey="category" // o el campo adecuado según tu API
                      dataKey="value" // o el campo adecuado según tu API
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {distributionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value) => [`${value}`, 'Cantidad']} 
                      contentStyle={{ backgroundColor: '#001f2e', border: 'none', color: '#E6E6E6' }} 
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="bg-cyber-detail/20 p-4 rounded text-cyber-text/70 text-center h-64 flex flex-col justify-center items-center">
                <AlertTriangle size={24} className="mb-2 text-cyber-cyan" />
                <p>No hay suficientes datos para mostrar esta visualización.</p>
              </div>
            )}
          </div>
          
          {/* Tendencia */}
          <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
            <h2 className="text-lg font-semibold text-cyber-text mb-4">Tendencia temporal</h2>
            {trendsData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendsData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                    <XAxis dataKey="date" stroke="#E6E6E6" />
                    <YAxis stroke="#E6E6E6" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#001f2e', border: 'none', color: '#E6E6E6' }} 
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="sales" // o el campo adecuado según tu API 
                      stroke="#00E6E6" 
                      strokeWidth={2} 
                      dot={{ stroke: '#00E6E6', strokeWidth: 2, r: 4, fill: '#00E6E6' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="bg-cyber-detail/20 p-4 rounded text-cyber-text/70 text-center h-64 flex flex-col justify-center items-center">
                <AlertTriangle size={24} className="mb-2 text-cyber-cyan" />
                <p>No hay suficientes datos temporales para mostrar esta visualización.</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {activeTab === 'structure' && (
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
          <h2 className="text-lg font-semibold text-cyber-text mb-4">Estructura del Dataset</h2>
          
          {context?.columnNames && context.columnNames.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-cyber-detail/30">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-cyber-cyan uppercase tracking-wider">
                      Columna
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-cyber-cyan uppercase tracking-wider">
                      Tipo
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cyber-detail/30">
                {context.columnNames.map((column: string, index: number) => (
                <tr key={index} className="hover:bg-cyber-detail/10">
                  <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-cyber-text">
                    {column}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-cyber-text/70">
                    {context.columnTypes && context.columnTypes[index] 
                      ? context.columnTypes[index] 
                      : "desconocido"}
                  </td>
                </tr> 
              ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-cyber-detail/20 p-4 rounded text-cyber-text/70">
              No hay información de columnas disponible para este dataset.
            </div>
          )}
          
          {/* Información adicional sobre la estructura */}
          <div className="mt-6 space-y-4">
            <div className="bg-cyber-detail/20 p-4 rounded">
              <h3 className="text-sm font-medium text-cyber-cyan mb-2">Información de conexión</h3>
              <p className="text-cyber-text/70 text-sm">
                Tipo: {context?.connection_type || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}
      
      {activeTab === 'chat' && (
        <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg h-[calc(100vh-20rem)]">
          <div className="flex flex-col h-full">
            {/* Cabecera del chat */}
            <div className="border-b border-cyber-detail/30 pb-3 mb-3">
              <h2 className="text-lg font-semibold text-cyber-text">Asistente de Datos</h2>
              <p className="text-cyber-text/70 text-sm">
                Pregunta cualquier cosa sobre este dataset
              </p>
            </div>
            
            {/* Área de mensajes */}
            <div className="flex-grow overflow-y-auto p-2 space-y-4">
              {chatMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 shadow ${
                      message.sender === 'user'
                        ? 'bg-cyber-cyan text-cyber-dark'
                        : 'bg-cyber-detail/50 text-cyber-text border border-cyber-cyan/20'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                    
                    {/* Visualizaciones e insights si los hay */}
                    {message.visualizations && message.visualizations.length > 0 && (
                      <div className="mt-3 border-t border-cyber-detail/30 pt-3">
                        <p className="text-xs font-medium mb-2">Visualizaciones:</p>
                        {message.visualizations.map((viz, index) => (
                          <div key={index} className="mt-2 bg-cyber-detail/30 p-2 rounded">
                            {/* Aquí puedes renderizar diferentes tipos de visualizaciones 
                                basadas en el contenido de 'viz' */}
                            <p className="text-xs">{viz.type || 'Visualización'}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {message.insights && message.insights.length > 0 && (
                      <div className="mt-3 border-t border-cyber-detail/30 pt-3">
                        <p className="text-xs font-medium mb-2">Insights:</p>
                        <ul className="list-disc list-inside text-xs space-y-1">
                          {message.insights.map((insight, index) => (
                            <li key={index}>{insight}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <p className={`text-xs mt-1 ${
                      message.sender === 'user' 
                        ? 'text-cyber-dark/70' 
                        : 'text-cyber-text/70'
                    }`}>
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
              
              {/* Indicador de escritura */}
              {isSending && (
                <div className="flex justify-start">
                  <div className="bg-cyber-detail/50 text-cyber-text rounded-lg px-4 py-2 border border-cyber-cyan/20 shadow">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 rounded-full bg-cyber-cyan animate-bounce" />
                      <div className="w-2 h-2 rounded-full bg-cyber-cyan animate-bounce" style={{ animationDelay: '0.2s' }} />
                      <div className="w-2 h-2 rounded-full bg-cyber-cyan animate-bounce" style={{ animationDelay: '0.4s' }} />
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Área de entrada de mensajes */}
            <div className="border-t border-cyber-detail/30 pt-3 mt-3">
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Pregunta sobre este dataset..."
                  className="flex-grow px-4 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!messageInput.trim() || isSending}
                  className={`p-2 rounded ${
                    !messageInput.trim() || isSending
                      ? 'bg-cyber-detail/30 text-cyber-text/40 cursor-not-allowed'
                      : 'bg-cyber-cyan text-cyber-dark hover:bg-cyber-cyan/90'
                  } transition-colors`}
                >
                  <Send size={18} />
                </button>
              </div>
              
              {/* Sugerencias de preguntas */}
              <div className="mt-3 flex flex-wrap gap-2">
                <button 
                  onClick={() => setMessageInput('¿Qué insights puedes darme sobre este dataset?')}
                  className="px-2 py-1 text-xs bg-cyber-detail/30 text-cyber-text/70 rounded hover:bg-cyber-detail/50 transition-colors"
                >
                  Insights generales
                </button>
                <button 
                  onClick={() => setMessageInput('Muestra la distribución de valores')}
                  className="px-2 py-1 text-xs bg-cyber-detail/30 text-cyber-text/70 rounded hover:bg-cyber-detail/50 transition-colors"
                >
                  Mostrar distribución
                </button>
                <button 
                  onClick={() => setMessageInput('¿Cuál es la tendencia principal?')}
                  className="px-2 py-1 text-xs bg-cyber-detail/30 text-cyber-text/70 rounded hover:bg-cyber-detail/50 transition-colors"
                >
                  Tendencias
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'agent' && dataset && (
        <div className="space-y-6">
          <div className="flex items-center mb-4">
            <Brain size={20} className="text-cyber-cyan mr-2" />
            <h2 className="text-lg font-semibold text-cyber-text">Asistente Proactivo IA</h2>
            <div className="ml-3 px-2 py-1 bg-cyber-cyan/20 rounded-full text-xs text-cyber-cyan">
              Avanzado
            </div>
          </div>
          
          {/* Panel de alertas y monitoreo */}
          <DataMonitorPanel datasetId={Number(id)} refreshInterval={300000} />
          
          {/* Insights generados por el agente */}
          <ProactiveInsights datasetId={Number(id)} />
          
          {/* Acciones sugeridas por el agente */}
          <AgentSuggestions />
          
          {/* Información sobre el Agente IA */}
          <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
            <div className="flex items-center mb-3">
              <Zap size={18} className="text-cyber-cyan mr-2" />
              <h3 className="text-md font-semibold text-cyber-text">Acerca del Agente IA</h3>
            </div>
            <p className="text-cyber-text/80 text-sm">
              El Agente IA analiza proactivamente tus datos para identificar patrones, anomalías y oportunidades de negocio. A diferencia del asistente conversacional, el agente monitorea continuamente y puede tomar decisiones autónomas cuando se configura para ello.
            </p>
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-cyber-detail/20 p-3 rounded-lg">
                <h4 className="text-sm font-medium text-cyber-cyan mb-1">Capacidades</h4>
                <ul className="text-xs text-cyber-text/70 space-y-1">
                  <li>• Detección automática de anomalías</li>
                  <li>• Identificación proactiva de oportunidades</li>
                  <li>• Monitoreo continuo de métricas clave</li>
                  <li>• Sugerencias basadas en reglas de negocio</li>
                </ul>
              </div>
              <div className="bg-cyber-detail/20 p-3 rounded-lg">
                <h4 className="text-sm font-medium text-cyber-cyan mb-1">Configuración</h4>
                <p className="text-xs text-cyber-text/70">
                  Para ajustar el comportamiento del agente IA, configura reglas de negocio en la sección 
                  <span className="text-cyber-cyan mx-1">Configuración → Reglas de Negocio</span>
                  del panel.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetDetailPage;