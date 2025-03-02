import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, 
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, Cell 
} from 'recharts';

const colors = ['#00E6E6', '#0094FF', '#6B66FF', '#9C66FF', '#FF66D9'];

function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState('metrics');
  const [dataset, setDataset] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [chatMessages, setChatMessages] = useState<{id: number, text: string, sender: 'user' | 'assistant', timestamp: Date}[]>([
    {
      id: 1,
      text: `Hi! I'm your AI assistant for Dataset ${id}. Ask me anything about this data!`,
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [messageInput, setMessageInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  // Simulación de carga de datos
  useEffect(() => {
    // Aquí harías una llamada a tu API para obtener los detalles del dataset
    setTimeout(() => {
      setDataset({
        id: parseInt(id || '0'),
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
  }, [id]);
  
  // Función para manejar el envío de mensajes en el chat
  const handleSendMessage = () => {
    if (!messageInput.trim()) return;
    
    // Agregar mensaje del usuario
    const userMessage = {
      id: chatMessages.length + 1,
      text: messageInput,
      sender: 'user' as const,
      timestamp: new Date()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setMessageInput('');
    setIsSending(true);
    
    // Simular respuesta del asistente (en producción, aquí llamarías a tu API)
    setTimeout(() => {
      const responses = [
        `Based on the analysis of Dataset ${id}, I can see that the main trend shows a ${Math.floor(Math.random() * 20) + 10}% growth over the last quarter.`,
        `Looking at the predictions for Dataset ${id}, we expect a ${Math.floor(Math.random() * 30) + 5}% change in the next period with ${Math.floor(Math.random() * 20) + 70}% confidence.`,
        `The key metrics for Dataset ${id} show strong performance, particularly in the ${['A', 'B', 'C', 'D', 'E'][Math.floor(Math.random() * 5)]} category.`,
        `I've analyzed the anomalies in Dataset ${id} and found ${Math.floor(Math.random() * 5) + 1} potential outliers that might be worth investigating further.`
      ];
      
      const assistantMessage = {
        id: chatMessages.length + 2,
        text: responses[Math.floor(Math.random() * responses.length)],
        sender: 'assistant' as const,
        timestamp: new Date()
      };
      
      setChatMessages(prev => [...prev, assistantMessage]);
      setIsSending(false);
    }, 1500);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-cyber-cyan"></div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6 bg-transparent">
      {/* Header */}
      <div className="bg-black/50 backdrop-blur-sm p-4 rounded border border-gray-600 shadow">
        <h1 className="text-2xl font-bold text-white">{dataset.name}</h1>
        <p className="text-gray-300 mt-1">{dataset.description}</p>
        <div className="flex space-x-4 mt-4">
          <button 
            className={`px-4 py-2 rounded ${
              activeTab === 'metrics' 
                ? 'bg-cyber-cyan text-cyber-dark' 
                : 'bg-cyber-detail/50 text-white hover:bg-cyber-detail'
            }`}
            onClick={() => setActiveTab('metrics')}
          >
            Metrics & Analysis
          </button>
          <button 
            className={`px-4 py-2 rounded ${
              activeTab === 'predictions' 
                ? 'bg-cyber-cyan text-cyber-dark' 
                : 'bg-cyber-detail/50 text-white hover:bg-cyber-detail'
            }`}
            onClick={() => setActiveTab('predictions')}
          >
            Predictions
          </button>
        </div>
      </div>

      {/* Main Content and Chatbot Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Main content area - takes 2/3 of space on large screens */}
        <div className="lg:col-span-2 space-y-4">
          {activeTab === 'metrics' ? (
            <>
              {/* Metrics Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(dataset.metrics).map(([key, value]) => (
                  <div key={key} className="bg-black/50 backdrop-blur-sm p-4 rounded border border-gray-600">
                    <h3 className="text-cyber-cyan text-sm uppercase">{key}</h3>
                    <p className="text-white text-2xl font-bold">{(value as number).toFixed(2)}</p>
                  </div>
                ))}
              </div>

              {/* Distribution Chart */}
              <div className="bg-black/50 backdrop-blur-sm p-4 rounded border border-gray-600">
                <h3 className="text-lg font-semibold mb-4 text-white">Data Distribution</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={dataset.distribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      >
                        {dataset.distribution.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => [`${value}`, 'Count']} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Trends Chart */}
              <div className="bg-black/50 backdrop-blur-sm p-4 rounded border border-gray-600">
                <h3 className="text-lg font-semibold mb-4 text-white">Trends Over Time</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={dataset.trends}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                      <XAxis dataKey="month" stroke="#E6E6E6" />
                      <YAxis stroke="#E6E6E6" />
                      <Tooltip contentStyle={{ backgroundColor: '#0A192F', borderColor: '#1C3D5A' }} />
                      <Legend />
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
          ) : (
            <>
              {/* Predictions */}
              <div className="bg-black/50 backdrop-blur-sm p-4 rounded border border-gray-600">
                <h3 className="text-lg font-semibold mb-4 text-white">Prediction Scenarios</h3>
                <div className="space-y-4">
                  {dataset.predictions.map((prediction: any, index: number) => (
                    <div 
                      key={index} 
                      className="p-3 border border-gray-600 rounded bg-black/30 hover:bg-black/50 transition-colors"
                    >
                      <div className="flex justify-between items-center">
                        <h4 className="text-white font-medium">{prediction.name}</h4>
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
                              <span className="text-xs font-semibold inline-block text-cyber-cyan">
                                Probability
                              </span>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-semibold inline-block text-cyber-cyan">
                                {Math.round(prediction.probability * 100)}%
                              </span>
                            </div>
                          </div>
                          <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-700">
                            <div 
                              style={{ width: `${prediction.probability * 100}%` }}
                              className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-cyber-cyan"
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Prediction Chart */}
              <div className="bg-black/50 backdrop-blur-sm p-4 rounded border border-gray-600">
                <h3 className="text-lg font-semibold mb-4 text-white">Prediction Probabilities</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={dataset.predictions}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#1C3D5A" />
                      <XAxis dataKey="name" stroke="#E6E6E6" />
                      <YAxis stroke="#E6E6E6" />
                      <Tooltip 
                        formatter={(value) => [`${(Number(value) * 100).toFixed(0)}%`, 'Probability']}
                        contentStyle={{ backgroundColor: '#0A192F', borderColor: '#1C3D5A' }} 
                      />
                      <Bar dataKey="probability" fill="#00E6E6">
                        {dataset.predictions.map((_: any, index: number) => (
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

        {/* Chatbot - takes 1/3 of space on large screens */}
        <div className="bg-black/50 backdrop-blur-sm rounded border border-gray-600 shadow h-[calc(100vh-20rem)] flex flex-col">
          <div className="p-4 border-b border-gray-600">
            <h3 className="text-lg font-semibold text-white">Dataset Assistant</h3>
            <p className="text-sm text-gray-300">Ask questions about this dataset</p>
          </div>
          
          {/* Chat messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.sender === 'user'
                      ? 'bg-cyber-cyan text-cyber-dark'
                      : 'bg-cyber-detail text-white'
                  }`}
                >
                  <p>{message.text}</p>
                  <p className={`text-xs mt-1 ${
                    message.sender === 'user'
                      ? 'text-cyber-dark/70'
                      : 'text-white/70'
                  }`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            
            {isSending && (
              <div className="flex justify-start">
                <div className="bg-cyber-detail text-white rounded-lg px-4 py-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 rounded-full bg-cyber-cyan animate-bounce" />
                    <div className="w-2 h-2 rounded-full bg-cyber-cyan animate-bounce" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 rounded-full bg-cyber-cyan animate-bounce" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Input area */}
          <div className="p-4 border-t border-gray-600">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask about this dataset..."
                className="flex-1 px-4 py-2 bg-cyber-detail/50 text-white border border-gray-600 rounded focus:outline-none focus:border-cyber-cyan"
              />
              <button
                onClick={handleSendMessage}
                disabled={!messageInput.trim() || isSending}
                className={`p-2 rounded ${
                  !messageInput.trim() || isSending
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                    : 'bg-cyber-cyan text-cyber-dark hover:bg-cyan-300'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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