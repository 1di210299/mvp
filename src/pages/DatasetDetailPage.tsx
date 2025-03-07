// src/pages/DatasetDetailPage.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, 
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, Cell 
} from 'recharts';

// Paleta de colores para los gráficos
const colors = ['#00E6E6', '#0094FF', '#6B66FF', '#9C66FF', '#FF66D9'];

// Tipado mínimo para un mensaje en el chat
interface ChatMessage {
  id: number;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

// Tipado mínimo para el dataset
interface DatasetType {
  id: number;
  name: string;
  description: string;
  createdAt: string;
  metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1Score: number;
    [key: string]: number; // Para ser más flexible
  };
  distribution: { name: string; value: number }[];
  trends: { month: string; valueA: number; valueB: number }[];
  predictions: { name: string; probability: number; impact: string }[];
}

function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<'metrics' | 'predictions'>('metrics');
  const [dataset, setDataset] = useState<DatasetType | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Mensajes de chat y estados relacionados
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      text: `Hi! I'm your AI assistant for Dataset ${id}. Ask me anything about this data!`,
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [messageInput, setMessageInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  // -------------------------------------------------------------------
  // 1. Cargar Dataset (simulación con setTimeout)
  // -------------------------------------------------------------------
  useEffect(() => {
    let isMounted = true;

    const fetchDataset = () => {
      // Aquí harías la llamada real a tu API
      setTimeout(() => {
        if (!isMounted) return;

        setDataset({
          id: parseInt(id || '0', 10),
          name: `Dataset ${id}`,
          description: 'A comprehensive dataset with various metrics and predictive features.',
          createdAt: '2025-02-25',
          metrics: {
            accuracy: 0.87,
            precision: 0.83,
            recall: 0.91,
            f1Score: 0.86
          },
          distribution: [
            { name: 'Category A', value: 400 },
            { name: 'Category B', value: 300 },
            { name: 'Category C', value: 200 },
            { name: 'Category D', value: 150 },
            { name: 'Category E', value: 100 },
          ],
          trends: Array.from({ length: 12 }, (_, i) => ({
            month: `Month ${i + 1}`,
            valueA: Math.floor(Math.random() * 1000) + 500,
            valueB: Math.floor(Math.random() * 800) + 300,
          })),
          predictions: [
            { name: 'Scenario 1', probability: 0.65, impact: 'High' },
            { name: 'Scenario 2', probability: 0.48, impact: 'Medium' },
            { name: 'Scenario 3', probability: 0.72, impact: 'Low' },
            { name: 'Scenario 4', probability: 0.34, impact: 'High' },
          ]
        });
        setLoading(false);
      }, 1000);
    };

    fetchDataset();
    return () => {
      isMounted = false;
    };
  }, [id]);

  // -------------------------------------------------------------------
  // 2. Manejar envío de mensajes del chat
  // -------------------------------------------------------------------
  const handleSendMessage = useCallback(() => {
    if (!messageInput.trim()) return;

    // Crear mensaje del usuario
    const userMessage: ChatMessage = {
      id: chatMessages.length + 1,
      text: messageInput,
      sender: 'user',
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setMessageInput('');
    setIsSending(true);

    // Simular respuesta del asistente
    setTimeout(() => {
      const responses = [
        `Based on the analysis of Dataset ${id}, I can see a ${Math.floor(Math.random() * 20) + 10}% growth over the last quarter.`,
        `Looking at the predictions for Dataset ${id}, we expect a ${Math.floor(Math.random() * 30) + 5}% change next period with ~${Math.floor(Math.random() * 20) + 70}% confidence.`,
        `The key metrics for Dataset ${id} show strong performance, especially in category ${['A', 'B', 'C', 'D', 'E'][Math.floor(Math.random() * 5)]}.`,
        `I've found ${Math.floor(Math.random() * 5) + 1} potential outliers in Dataset ${id} that might need further investigation.`
      ];

      const assistantMessage: ChatMessage = {
        id: userMessage.id + 1,
        text: responses[Math.floor(Math.random() * responses.length)],
        sender: 'assistant',
        timestamp: new Date()
      };

      setChatMessages(prev => [...prev, assistantMessage]);
      setIsSending(false);
    }, 1500);
  }, [chatMessages, id, messageInput]);

  // -------------------------------------------------------------------
  // 3. Renderizar loading
  // -------------------------------------------------------------------
  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-[#00E6E6]"></div>
      </div>
    );
  }

  // -------------------------------------------------------------------
  // 4. Render principal
  // -------------------------------------------------------------------
  return (
    <div className="p-4 space-y-6">
      {/* ======================== HEADER DEL DATASET ======================== */}
      <div className="bg-[#000]/50 backdrop-blur-sm p-4 rounded border-2 border-[#00E6E6] shadow">
        <h1 className="text-2xl font-bold text-[#E6E6E6]">{dataset?.name}</h1>
        <p className="text-gray-300 mt-1">{dataset?.description}</p>

        {/* Botones de Tabs */}
        <div className="flex space-x-4 mt-4">
          <button 
            className={`px-4 py-2 rounded transition-colors border ${
              activeTab === 'metrics' 
                ? 'bg-[#00E6E6] text-[#000] border-[#00E6E6]' 
                : 'bg-[#333]/50 text-[#E6E6E6] hover:bg-[#444] border-[#00E6E6]'
            }`}
            onClick={() => setActiveTab('metrics')}
          >
            Metrics & Analysis
          </button>
          <button 
            className={`px-4 py-2 rounded transition-colors border ${
              activeTab === 'predictions' 
                ? 'bg-[#00E6E6] text-[#000] border-[#00E6E6]' 
                : 'bg-[#333]/50 text-[#E6E6E6] hover:bg-[#444] border-[#00E6E6]'
            }`}
            onClick={() => setActiveTab('predictions')}
          >
            Predictions
          </button>
        </div>
      </div>

      {/* ======================== CONTENIDO Y CHAT ======================== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
        {/* Área principal (2/3 en pantallas grandes) */}
        <div className="lg:col-span-2 space-y-4">
          {activeTab === 'metrics' && dataset && (
            <>
              {/* =========== MÉTRICAS =========== */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(dataset.metrics).map(([key, value]) => (
                  <div 
                    key={key} 
                    className="bg-[#000]/50 backdrop-blur-sm p-4 rounded border-2 border-[#00E6E6] shadow"
                  >
                    <h3 className="text-[#00E6E6] text-xs uppercase">{key}</h3>
                    <p className="text-[#E6E6E6] text-2xl font-bold">
                      {(value as number).toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>

              {/* =========== DISTRIBUCIÓN =========== */}
              <div className="bg-[#000]/50 backdrop-blur-sm p-4 rounded border-2 border-[#00E6E6] shadow">
                <h3 className="text-lg font-semibold mb-4 text-[#E6E6E6]">Data Distribution</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={dataset.distribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      >
                        {dataset.distribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value) => [`${value}`, 'Count']} 
                        contentStyle={{ backgroundColor: '#001f2e', border: 'none', color: '#E6E6E6' }} 
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* =========== TENDENCIAS =========== */}
              <div className="bg-[#000]/50 backdrop-blur-sm p-4 rounded border-2 border-[#00E6E6] shadow">
                <h3 className="text-lg font-semibold mb-4 text-[#E6E6E6]">Trends Over Time</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={dataset.trends}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                      <XAxis dataKey="month" stroke="#E6E6E6" />
                      <YAxis stroke="#E6E6E6" />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#001f2e', borderColor: '#1C3D5A', color: '#E6E6E6' }} 
                      />
                      <Legend wrapperStyle={{ color: '#E6E6E6' }} />
                      <Line 
                        type="monotone" 
                        dataKey="valueA" 
                        stroke="#00E6E6" 
                        name="Metric A" 
                        strokeWidth={2} 
                      />
                      <Line 
                        type="monotone" 
                        dataKey="valueB" 
                        stroke="#9C66FF" 
                        name="Metric B" 
                        strokeWidth={2} 
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}

          {activeTab === 'predictions' && dataset && (
            <>
              {/* =========== PREDICCIONES =========== */}
              <div className="bg-[#000]/50 backdrop-blur-sm p-4 rounded border-2 border-[#00E6E6] shadow">
                <h3 className="text-lg font-semibold mb-4 text-[#E6E6E6]">Prediction Scenarios</h3>
                <div className="space-y-4">
                  {dataset.predictions.map((prediction, index) => (
                    <div 
                      key={index} 
                      className="p-3 border-2 border-[#00E6E6]/50 rounded bg-[#000]/30 hover:bg-[#000]/60 transition-colors"
                    >
                      <div className="flex justify-between items-center">
                        <h4 className="text-[#E6E6E6] font-medium">{prediction.name}</h4>
                        <span 
                          className={`px-2 py-1 rounded text-xs ${
                            prediction.impact === 'High' 
                              ? 'bg-red-900/70 text-red-300' 
                              : prediction.impact === 'Medium'
                                ? 'bg-yellow-900/70 text-yellow-300'
                                : 'bg-green-900/70 text-green-300'
                          }`}
                        >
                          {prediction.impact} Impact
                        </span>
                      </div>
                      <div className="mt-2">
                        <div className="relative pt-1">
                          <div className="flex mb-2 items-center justify-between">
                            <div>
                              <span className="text-xs font-semibold inline-block text-[#00E6E6]">
                                Probability
                              </span>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-semibold inline-block text-[#00E6E6]">
                                {Math.round(prediction.probability * 100)}%
                              </span>
                            </div>
                          </div>
                          <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-700">
                            <div 
                              style={{ width: `${prediction.probability * 100}%` }}
                              className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-[#00E6E6]"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* =========== GRÁFICO DE PREDICCIONES =========== */}
              <div className="bg-[#000]/50 backdrop-blur-sm p-4 rounded border-2 border-[#00E6E6] shadow">
                <h3 className="text-lg font-semibold mb-4 text-[#E6E6E6]">Prediction Probabilities</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dataset.predictions}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                      <XAxis dataKey="name" stroke="#E6E6E6" />
                      <YAxis stroke="#E6E6E6" />
                      <Tooltip 
                        formatter={(value) => [`${(Number(value) * 100).toFixed(0)}%`, 'Probability']}
                        contentStyle={{ backgroundColor: '#001f2e', borderColor: '#1C3D5A', color: '#E6E6E6' }} 
                      />
                      <Legend wrapperStyle={{ color: '#E6E6E6' }} />
                      <Bar dataKey="probability">
                        {dataset.predictions.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}
        </div>

        {/* ======================== CHATBOT ======================== */}
        <div className="bg-[#000]/50 backdrop-blur-sm p-4 rounded border-2 border-[#00E6E6] shadow h-[calc(100vh-20rem)] flex flex-col">
          <div className="p-4 border-b-2 border-[#00E6E6]">
            <h3 className="text-lg font-semibold text-[#E6E6E6]">Dataset Assistant</h3>
            <p className="text-sm text-gray-300">Ask questions about this dataset</p>
          </div>
          
          {/* Mensajes del chat */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 shadow ${
                    message.sender === 'user'
                      ? 'bg-[#00E6E6] text-[#000]'
                      : 'bg-[#333]/50 text-[#E6E6E6]'
                  }`}
                >
                  <p>{message.text}</p>
                  <p className={`text-xs mt-1 ${message.sender === 'user' ? 'text-[#000]/70' : 'text-[#E6E6E6]/70'}`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}

            {/* Indicador "escribiendo" */}
            {isSending && (
              <div className="flex justify-start">
                <div className="bg-[#333]/50 text-[#E6E6E6] rounded-lg px-4 py-2 shadow">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 rounded-full bg-[#00E6E6] animate-bounce" />
                    <div className="w-2 h-2 rounded-full bg-[#00E6E6] animate-bounce" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 rounded-full bg-[#00E6E6] animate-bounce" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Input del chat */}
          <div className="p-4 border-t-2 border-[#00E6E6]">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask about this dataset..."
                className="flex-1 px-4 py-2 bg-[#333]/50 text-[#E6E6E6] border border-[#00E6E6]/50 rounded focus:outline-none focus:border-[#00E6E6]"
              />
              <button
                onClick={handleSendMessage}
                disabled={!messageInput.trim() || isSending}
                className={`p-2 rounded transition-colors ${
                  !messageInput.trim() || isSending
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                    : 'bg-[#00E6E6] text-[#000] hover:bg-[#00E6E6]/90'
                }`}
              >
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-5 w-5" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DatasetDetailPage;
