// src/components/EnhancedAssistant.tsx
import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, Download, Sparkles, BarChart, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { assistantService, Visualization, Insight } from '../api/services';

// Interfaces
interface Message {
  id: number;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  visualizations?: Visualization[];
  insights?: Insight[];
}

interface EnhancedAssistantProps {
  datasetId: string | number;
  language?: 'es' | 'en';
  height?: string;
  theme?: 'cyber' | 'light' | 'dark';
}

const EnhancedAssistant: React.FC<EnhancedAssistantProps> = ({ 
  datasetId, 
  language = 'es', 
  height = '600px',
  theme = 'cyber'
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [datasetContext, setDatasetContext] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  // Load dataset context on component mount
  useEffect(() => {
    const fetchDatasetContext = async (): Promise<void> => {
      try {
        // Obtener el contexto del dataset
        const response = await assistantService.getContext(datasetId);
        setDatasetContext(response.data);
        
        // Añadir mensaje de bienvenida
        setMessages([{
          id: Date.now(),
          text: language === 'es' 
            ? `Hola, soy tu asistente de datos para el dataset ${response.data?.name || `#${datasetId}`}. ¿En qué puedo ayudarte?` 
            : `Hi, I'm your data assistant for dataset ${response.data?.name || `#${datasetId}`}. How can I help you?`,
          sender: 'assistant',
          timestamp: new Date()
        }]);
        
        // Generar sugerencias basadas en el contexto del dataset
        if (response.data && response.data.columnNames && response.data.columnNames.length > 0) {
          const columns = response.data.columnNames;
          const updatedSuggestions = [
            `${language === 'es' ? 'Analiza' : 'Analyze'} ${columns[0] || 'data'}`,
            `${language === 'es' ? 'Muestra la tendencia de' : 'Show trend for'} ${columns.length > 1 ? columns[1] : columns[0]}`,
            `${language === 'es' ? '¿Cuáles son los principales insights?' : 'What are the main insights?'}`,
            `${language === 'es' ? 'Genera un reporte' : 'Generate a report'}`
          ];
          setSuggestions(updatedSuggestions);
        } else {
          // Sugerencias predeterminadas si no hay contexto específico
          setSuggestions([
            language === 'es' ? 'Analiza las tendencias' : 'Analyze trends',
            language === 'es' ? 'Muestra un resumen' : 'Show a summary',
            language === 'es' ? '¿Qué insights detectas?' : 'What insights do you detect?',
            language === 'es' ? 'Genera visualizaciones' : 'Generate visualizations'
          ]);
        }
      } catch (err) {
        console.error("Error fetching dataset context:", err);
        setError(language === 'es' 
          ? "No se pudo cargar la información del dataset." 
          : "Could not load dataset information.");
        
        // Mensaje de bienvenida genérico en caso de error
        setMessages([{
          id: Date.now(),
          text: language === 'es' 
            ? `Hola, soy tu asistente de datos. No pude cargar la información específica del dataset, pero intentaré ayudarte con tus consultas.` 
            : `Hi, I'm your data assistant. I couldn't load the specific dataset information, but I'll try to help with your queries.`,
          sender: 'assistant',
          timestamp: new Date()
        }]);
      }
    };
    
    fetchDatasetContext();
  }, [datasetId, language]);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Handle text input
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>): void => {
    setInputValue(e.target.value);
    
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };
  
  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string): void => {
    setInputValue(suggestion);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };
  
  const handleSendMessage = async (): Promise<void> => {
    if (!inputValue.trim() || isProcessing) return;
    
    // Add user message
    const userMessage: Message = {
      id: Date.now(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsProcessing(true);
    
    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
    
    try {
      // Prepare recent message history for context
      const messageHistory = messages
        .slice(-5) // Last 5 messages
        .map(msg => ({
          text: msg.text,
          sender: msg.sender
        }));
        
      // Send to enhanced analysis API with dataset context
      const response = await assistantService.analyze({
        message: inputValue,
        datasetId,
        datasetContext,
        language,
        messageHistory,
        assistantType: 'general'
      });
      
      // Add assistant response
      const assistantMessage: Message = {
        id: Date.now() + 1,
        text: response.data.message,
        visualizations: response.data.visualizations || [],
        insights: response.data.insights || [],
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update suggestions based on response
      if (response.data.suggestions && response.data.suggestions.length > 0) {
        setSuggestions(response.data.suggestions);
      }
    } catch (err) {
      console.error("Error getting assistant response:", err);
      // Add error message
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: language === 'es'
          ? "Lo siento, hubo un error al procesar tu solicitud. Por favor, intenta de nuevo más tarde."
          : "Sorry, there was an error processing your request. Please try again later.",
        sender: 'assistant',
        timestamp: new Date()
      }]);
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Handle key press (submit on Enter, but allow Shift+Enter for new lines)
  const handleKeyPress = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Format timestamp
  const formatTimestamp = (date: Date): string => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Render visualization based on the type
  const renderVisualization = (visualization: Visualization): JSX.Element => {
    // Si hay datos reales para visualizar, mostrar el gráfico
    if (visualization.data) {
      return (
        <div className="my-2 p-3 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-cyber-cyan">{visualization.title}</h4>
            <button className="text-cyber-text/70 hover:text-cyber-cyan">
              <Download size={14} />
            </button>
          </div>
          <div className="h-64 w-full">
            {/* Aquí se renderizaría el gráfico usando la librería de visualización que estés utilizando */}
            {/* Por ejemplo, si estás usando Plotly o Recharts */}
            <div 
              id={`visualization-${Date.now()}`} 
              className="w-full h-full"
              dangerouslySetInnerHTML={{ __html: JSON.stringify(visualization.data) }}
            />
          </div>
        </div>
      );
    }
    
    // Fallback si no hay datos para visualizar
    return (
      <div className="my-2 p-3 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-cyber-cyan">{visualization.title}</h4>
        </div>
        <div className="h-48 bg-cyber-detail/20 rounded flex items-center justify-center">
          <BarChart size={32} className="text-cyber-cyan/40" />
          <span className="ml-2 text-cyber-text/70">
            {language === 'es' 
              ? 'No se pudieron generar visualizaciones para estos datos.' 
              : 'Could not generate visualizations for this data.'}
          </span>
        </div>
      </div>
    );
  };
  
  // Render insights
  const renderInsights = (insights: Insight[]): JSX.Element => {
    return (
      <div className="my-2 p-3 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
        <h4 className="text-sm font-medium text-cyber-cyan mb-2 flex items-center">
          <Sparkles size={14} className="mr-1" />
          {language === 'es' ? 'Insights' : 'Insights'}
        </h4>
        <ul className="space-y-1">
          {insights.map((insight, index) => (
            <li key={index} className="text-sm text-cyber-text flex items-start">
              <span className="inline-block h-4 w-4 rounded-full bg-cyber-cyan/20 text-cyber-cyan flex items-center justify-center text-xs mr-2 mt-0.5">•</span>
              {insight.text}
            </li>
          ))}
        </ul>
      </div>
    );
  };
  
  return (
    <div 
      className={`flex flex-col h-[${height}] ${
        theme === 'cyber' 
          ? 'bg-cyber-dark/70 backdrop-blur-sm border border-cyber-cyan/20' 
          : theme === 'light'
          ? 'bg-white border border-gray-200'
          : 'bg-gray-900 border border-gray-700'
      } rounded-lg shadow-lg overflow-hidden`}
    >
      {/* Header */}
      <div className={`p-4 border-b ${
        theme === 'cyber' 
          ? 'border-cyber-detail bg-cyber-dark/90' 
          : theme === 'light'
          ? 'border-gray-200 bg-gray-50'
          : 'border-gray-700 bg-gray-800'
      }`}>
        <div className="flex items-center">
          <div className={`${
            theme === 'cyber' 
              ? 'bg-cyber-cyan/20 text-cyber-cyan' 
              : theme === 'light'
              ? 'bg-blue-100 text-blue-600'
              : 'bg-blue-900/30 text-blue-400'
          } p-2 rounded-full mr-3`}>
            <Bot size={20} />
          </div>
          <div>
            <h3 className={`text-lg font-semibold ${
              theme === 'cyber' ? 'text-cyber-text' : theme === 'light' ? 'text-gray-800' : 'text-gray-100'
            }`}>
              {language === 'es' ? 'Asistente de Datos' : 'Data Assistant'}
            </h3>
            <p className={`text-sm ${
              theme === 'cyber' ? 'text-cyber-text/70' : theme === 'light' ? 'text-gray-500' : 'text-gray-400'
            }`}>
              {datasetContext?.name 
                ? datasetContext.name 
                : language === 'es' 
                  ? `Dataset #${datasetId}` 
                  : `Dataset #${datasetId}`}
            </p>
          </div>
        </div>
      </div>
      
      {/* Messages Container */}
      <div className={`flex-1 overflow-y-auto p-4 space-y-4 ${
        theme === 'cyber' 
          ? 'bg-gradient-to-b from-cyber-dark/90 to-cyber-dark' 
          : theme === 'light'
          ? 'bg-gray-50'
          : 'bg-gray-900'
      }`}>
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-3/4 sm:max-w-2/3 rounded-lg shadow ${
                message.sender === 'user'
                  ? theme === 'cyber'
                    ? 'bg-cyber-cyan text-cyber-dark'
                    : theme === 'light'
                    ? 'bg-blue-600 text-white'
                    : 'bg-blue-600 text-white'
                  : theme === 'cyber'
                  ? 'bg-cyber-detail text-cyber-text border border-cyber-cyan/20'
                  : theme === 'light'
                  ? 'bg-white text-gray-800 border border-gray-200'
                  : 'bg-gray-800 text-white border border-gray-700'
              }`}>
                {/* Message Content */}
                <div className="p-3">
                  <p className="whitespace-pre-wrap">{message.text}</p>
                  
                  {/* Timestamp */}
                  <p className={`text-xs mt-1 ${
                    message.sender === 'user'
                      ? theme === 'cyber'
                        ? 'text-cyber-dark/70'
                        : 'text-white/70'
                      : theme === 'cyber'
                      ? 'text-cyber-text/70'
                      : theme === 'light'
                      ? 'text-gray-500'
                      : 'text-gray-400'
                  }`}>
                    {formatTimestamp(message.timestamp)}
                  </p>
                </div>
                
                {/* Visualizations (only for assistant messages) */}
                {message.sender === 'assistant' && message.visualizations && message.visualizations.length > 0 && (
                  <div className="mt-2 border-t border-cyber-cyan/10 pt-2">
                    {message.visualizations.map((viz, index) => (
                      <div key={index}>
                        {renderVisualization(viz)}
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Insights (only for assistant messages) */}
                {message.sender === 'assistant' && message.insights && message.insights.length > 0 && (
                  <div className="mt-2">
                    {renderInsights(message.insights)}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {/* Typing indicator for assistant */}
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={`flex justify-start`}
          >
            <div className={`rounded-lg shadow px-4 py-3 ${
              theme === 'cyber'
                ? 'bg-cyber-detail text-cyber-text border border-cyber-cyan/20'
                : theme === 'light'
                ? 'bg-white text-gray-800 border border-gray-200'
                : 'bg-gray-800 text-white border border-gray-700'
            }`}>
              <div className="flex space-x-2">
                <div className={`w-2 h-2 rounded-full animate-bounce ${
                  theme === 'cyber' ? 'bg-cyber-cyan' : theme === 'light' ? 'bg-blue-600' : 'bg-blue-400'
                }`} />
                <div className={`w-2 h-2 rounded-full animate-bounce delay-200 ${
                  theme === 'cyber' ? 'bg-cyber-cyan' : theme === 'light' ? 'bg-blue-600' : 'bg-blue-400'
                }`} style={{ animationDelay: '0.2s' }} />
                <div className={`w-2 h-2 rounded-full animate-bounce delay-400 ${
                  theme === 'cyber' ? 'bg-cyber-cyan' : theme === 'light' ? 'bg-blue-600' : 'bg-blue-400'
                }`} style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          </motion.div>
        )}
        
        {/* Reference for scrolling to bottom */}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Suggestions */}
      {suggestions.length > 0 && !isProcessing && (
        <div className={`px-4 py-2 ${
          theme === 'cyber' 
            ? 'bg-cyber-dark/90 border-t border-cyber-detail' 
            : theme === 'light'
            ? 'bg-gray-50 border-t border-gray-200'
            : 'bg-gray-900 border-t border-gray-700'
        }`}>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  theme === 'cyber'
                    ? 'bg-cyber-detail/30 text-cyber-text border border-cyber-cyan/20 hover:bg-cyber-detail/50'
                    : theme === 'light'
                    ? 'bg-gray-100 text-gray-800 border border-gray-300 hover:bg-gray-200'
                    : 'bg-gray-800 text-gray-100 border border-gray-700 hover:bg-gray-700'
                }`}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
      
      {/* Input Area */}
      <div className={`p-4 ${
        theme === 'cyber' 
          ? 'bg-cyber-dark/90 border-t border-cyber-detail' 
          : theme === 'light'
          ? 'bg-white border-t border-gray-200'
          : 'bg-gray-900 border-t border-gray-700'
      }`}>
        <div className="flex items-end space-x-2">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder={language === 'es' 
              ? "Escribe tu pregunta aquí..." 
              : "Type your question here..."}
            className={`flex-1 p-3 rounded-lg resize-none transition min-h-[40px] max-h-[120px] ${
              theme === 'cyber'
                ? 'bg-cyber-detail/50 text-cyber-text border border-cyber-detail focus:outline-none focus:border-cyber-cyan'
                : theme === 'light'
                ? 'bg-gray-100 text-gray-800 border border-gray-300 focus:outline-none focus:border-blue-500'
                : 'bg-gray-800 text-white border border-gray-700 focus:outline-none focus:border-blue-500'
            }`}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isProcessing}
            className={`p-3 rounded-lg focus:outline-none transition ${
              !inputValue.trim() || isProcessing
                ? theme === 'cyber'
                  ? 'bg-cyber-detail text-cyber-text/40 cursor-not-allowed'
                  : theme === 'light'
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                : theme === 'cyber'
                ? 'bg-cyber-cyan text-cyber-dark hover:bg-cyber-cyan/90'
                : theme === 'light'
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
            aria-label="Enviar Mensaje"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default EnhancedAssistant;