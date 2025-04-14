// src/components/AsistenteVentas.tsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, Lightbulb, Sparkles, FileText, PieChart, Download } from 'lucide-react';
import { assistantService } from '../api/services';

interface Mensaje {
  id: number;
  texto: string;
  emisor: 'usuario' | 'bot';
  timestamp: Date;
  visualizaciones?: any[];
  insights?: any[];
}

interface AsistenteVentasProps {
  empresaId: number;
  nombreEmpresa: string;
  sector?: string;
}

function AsistenteVentas({ 
  empresaId, 
  nombreEmpresa, 
  sector = "Retail"
}: AsistenteVentasProps) {
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sugerencias, setSugerencias] = useState<string[]>([
    "¿Cómo mejorar mis ventas?",
    "Analizar tendencias por región",
    "Predecir ventas próximo mes",
    "Segmentar a mis clientes",
  ]);
  const mensajesEndRef = useRef<HTMLDivElement>(null);
  
  // Cargar mensaje inicial de bienvenida
  useEffect(() => {
    setMensajes([{
      id: 1,
      texto: `¡Hola! Soy tu asistente IA de ANNEX para "${nombreEmpresa}". Puedo ayudarte con análisis de ventas, predicciones, segmentación de clientes y más. ¿En qué puedo ayudarte hoy?`,
      emisor: 'bot',
      timestamp: new Date(),
    }]);
  }, [nombreEmpresa]);
  
  // Auto-scroll al último mensaje
  useEffect(() => {
    mensajesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  const handleSendMessage = async () => {
    const messageText = inputValue.trim();
    if (!messageText || isTyping) return;

    // Agregar el mensaje del usuario
    const userMessage: Mensaje = {
      id: Date.now(),
      texto: messageText,
      emisor: 'usuario',
      timestamp: new Date(),
    };
    setMensajes((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Preparar historial de mensajes para contexto
      const messageHistory = mensajes
        .slice(-5) // Últimos 5 mensajes
        .map(msg => ({
          text: msg.texto,
          sender: msg.emisor === 'usuario' ? 'user' : 'assistant'
        }));
      
      // Llamada a la API real
      const response = await assistantService.analyzeSales({
        message: messageText,
        empresaId,
        nombreEmpresa,
        sector,
        language: 'es',
        messageHistory
      });
      
      // Crear el mensaje del asistente con la respuesta
      const botMessage: Mensaje = {
        id: Date.now() + 1,
        texto: response.data.message,
        emisor: 'bot',
        timestamp: new Date(),
        visualizaciones: response.data.visualizations || [],
        insights: response.data.insights || []
      };
      
      setMensajes((prev) => [...prev, botMessage]);
      
      // Actualizar sugerencias si hay disponibles
      if (response.data.suggestions && response.data.suggestions.length > 0) {
        setSugerencias(response.data.suggestions);
      }
    } catch (error) {
      console.error("Error al obtener respuesta:", error);
      // Mensaje de error para el usuario
      setMensajes((prev) => [...prev, {
        id: Date.now() + 1,
        texto: "Lo siento, hubo un problema al procesar tu consulta. Por favor, intenta nuevamente.",
        emisor: 'bot',
        timestamp: new Date(),
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Formatear la hora en formato HH:MM
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' });
  };

  // Manejar click en sugerencia
  const handleSugerenciaClick = (sugerencia: string) => {
    setInputValue(sugerencia);
    // Pequeño delay para mejor UX
    setTimeout(() => {
      handleSendMessage();
    }, 100);
  };
  
  // Renderizar visualización
  const renderVisualizacion = (visualizacion: any) => {
    if (!visualizacion) return null;
    
    return (
      <div className="my-2 p-3 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-cyber-cyan">{visualizacion.title || "Visualización"}</h4>
          <button className="text-cyber-text/70 hover:text-cyber-cyan">
            <Download size={14} />
          </button>
        </div>
        <div className="h-64 w-full">
          {visualizacion.data ? (
            <div 
              id={`visualization-${Date.now()}`} 
              className="w-full h-full"
              dangerouslySetInnerHTML={{ __html: JSON.stringify(visualizacion.data) }}
            />
          ) : (
            <div className="h-full flex items-center justify-center">
              <PieChart size={32} className="text-cyber-cyan/40 mr-2" />
              <span className="text-cyber-text/70">Sin datos para visualizar</span>
            </div>
          )}
        </div>
      </div>
    );
  };
  
  // Renderizar insights
  const renderInsights = (insights: any[]) => {
    if (!insights || insights.length === 0) return null;
    
    return (
      <div className="my-2 p-3 bg-cyber-detail/30 rounded-lg border border-cyber-cyan/10">
        <h4 className="text-sm font-medium text-cyber-cyan mb-2 flex items-center">
          <Sparkles size={14} className="mr-1" />
          Insights
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
    <div className="flex flex-col h-full bg-cyber-dark rounded-lg shadow-xl overflow-hidden border border-cyber-cyan/30">
      {/* Cabecera */}
      <div className="p-4 border-b border-cyber-detail bg-cyber-dark/90">
        <div className="flex items-center">
          <div className="bg-cyber-cyan/20 p-2 rounded-full mr-3">
            <Bot size={24} className="text-cyber-cyan" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-cyber-text">Asistente ANNEX IA</h3>
            <p className="text-sm text-cyber-text/70">Especialista en ventas para MYPES peruanas</p>
          </div>
        </div>
      </div>

      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-cyber-dark/90 to-cyber-dark">
        <AnimatePresence>
          {mensajes.map((mensaje) => (
            <motion.div
              key={mensaje.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.3 }}
              className={`flex ${
                mensaje.emisor === 'usuario' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 shadow-md ${
                  mensaje.emisor === 'usuario'
                    ? 'bg-cyber-cyan text-cyber-dark'
                    : 'bg-cyber-detail text-cyber-text border border-cyber-cyan/20'
                }`}
              >
                <p className="text-sm leading-relaxed">{mensaje.texto}</p>
                <p
                  className={`text-xs mt-1 ${
                    mensaje.emisor === 'usuario'
                      ? 'text-cyber-dark/70'
                      : 'text-cyber-text/70'
                  }`}
                >
                  {formatTime(mensaje.timestamp)}
                </p>
                
                {/* Visualizaciones (solo para mensajes del bot) */}
                {mensaje.emisor === 'bot' && mensaje.visualizaciones && mensaje.visualizaciones.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-cyber-cyan/10">
                    {mensaje.visualizaciones.map((viz, index) => (
                      <div key={index}>
                        {renderVisualizacion(viz)}
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Insights (solo para mensajes del bot) */}
                {mensaje.emisor === 'bot' && mensaje.insights && mensaje.insights.length > 0 && (
                  <div className="mt-2">
                    {renderInsights(mensaje.insights)}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex justify-start"
          >
            <div className="bg-cyber-detail text-cyber-text rounded-lg px-4 py-2 shadow-md border border-cyber-cyan/20">
              <div className="flex space-x-1">
                <div className="w-2 h-2 rounded-full bg-cyber-cyan animate-bounce" />
                <div
                  className="w-2 h-2 rounded-full bg-cyber-cyan animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
                <div
                  className="w-2 h-2 rounded-full bg-cyber-cyan animate-bounce"
                  style={{ animationDelay: '0.4s' }}
                />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={mensajesEndRef} />
      </div>

      {/* Sugerencias */}
      {!isTyping && (
        <div className="px-4 py-2 bg-cyber-dark/90">
          <div className="flex flex-wrap gap-2">
            {sugerencias.map((sugerencia, index) => (
              <button
                key={index}
                onClick={() => handleSugerenciaClick(sugerencia)}
                className="px-3 py-1 bg-cyber-detail/30 text-cyber-text text-xs rounded-full border border-cyber-cyan/20 hover:bg-cyber-detail/50 transition-colors"
              >
                {sugerencia}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Herramientas de asistente */}
      <div className="px-4 py-2 border-t border-cyber-detail bg-cyber-dark/90">
        <div className="flex justify-between">
          <div className="flex space-x-2">
            <button className="p-2 text-cyber-text/70 hover:text-cyber-cyan rounded-full transition-colors" title="Generar reportes">
              <FileText size={18} />
            </button>
            <button className="p-2 text-cyber-text/70 hover:text-cyber-cyan rounded-full transition-colors" title="Visualizar datos">
              <PieChart size={18} />
            </button>
            <button className="p-2 text-cyber-text/70 hover:text-cyber-cyan rounded-full transition-colors" title="Insights IA">
              <Lightbulb size={18} />
            </button>
            <button className="p-2 text-cyber-text/70 hover:text-cyber-cyan rounded-full transition-colors" title="Acciones sugeridas">
              <Sparkles size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Input de mensaje */}
      <div className="p-4 border-t border-cyber-detail bg-cyber-dark/90">
        <div className="flex items-center space-x-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Pregúntame sobre ventas, tendencias, clientes..."
            className="flex-1 px-4 py-2 bg-cyber-detail/50 text-cyber-text border border-cyber-detail rounded focus:outline-none focus:border-cyber-cyan resize-none"
            rows={1}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            className={`p-2 rounded-full focus:outline-none focus:ring-2 focus:ring-cyber-cyan transition ${
              !inputValue.trim() || isTyping
                ? 'bg-cyber-detail text-cyber-text/40 cursor-not-allowed'
                : 'bg-cyber-cyan text-cyber-dark hover:bg-cyber-cyan/90'
            }`}
            aria-label="Enviar Mensaje"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default AsistenteVentas;