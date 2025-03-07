// src/components/AsistenteVentas.tsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, Lightbulb, Sparkles, FileText, PieChart } from 'lucide-react';

interface Mensaje {
  id: number;
  texto: string;
  emisor: 'usuario' | 'bot';
  timestamp: Date;
}

interface AsistenteVentasProps {
  empresaId?: number;
  nombreEmpresa?: string;
  sector?: string;
}

function AsistenteVentas({ 
  empresaId = 1, 
  nombreEmpresa = "Mi Empresa", 
  sector = "Retail"
}: AsistenteVentasProps) {
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    {
      id: 1,
      texto: `¡Hola! Soy tu asistente IA de ANNEX para "${nombreEmpresa}". Puedo ayudarte con análisis de ventas, predicciones, segmentación de clientes y más. ¿En qué puedo ayudarte hoy?`,
      emisor: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sugerencias, setSugerencias] = useState<string[]>([
    "¿Cómo mejorar mis ventas?",
    "Analizar tendencias por región",
    "Predecir ventas próximo mes",
    "Segmentar a mis clientes",
  ]);
  const mensajesEndRef = useRef<HTMLDivElement>(null);

  // Respuestas de ejemplo según palabras clave (en un entorno real se consultaría al backend AI)
  const respuestasEjemplo: Record<string, string[]> = {
    tendencia: [
      'Según el análisis de tus datos, hay un crecimiento del 15% en el último trimestre, especialmente en Lima y Arequipa.',
      'Estamos viendo un patrón cíclico con picos cada 3 meses, coincidiendo con fechas de pago de quincena.',
      'Hay una tendencia a la baja en la categoría C, pero el crecimiento en A y B lo compensa. Te recomendaría revisar la estrategia de precios para la categoría C.',
    ],
    predecir: [
      'Basado en tus datos históricos y factores estacionales, predicción para el próximo mes: S/ 58,400 en ventas (+23%).',
      'Nuestro modelo predice un cambio en el mercado para el tercer trimestre. Considera aumentar inventario de productos estacionales.',
      'La confianza de predicción es actualmente 87% para el escenario principal. Los márgenes de error están dentro del 5-8%.',
    ],
    comparar: [
      'Comparado con empresas similares del sector Retail en Perú, tus ventas muestran un 30% más de variación estacional.',
      'Tu ticket promedio (S/ 125) es 45% mayor que el promedio del sector (S/ 86) en MYPES similares.',
      'Comparado con el año pasado, vemos una mejora del 12% en conversión y un 8% en retención de clientes.',
    ],
    campaña: [
      'Las campañas de Fiestas Patrias y Navidad generan el 48% de tus ingresos anuales. Recomendamos reforzar marketing 60 días antes.',
      'Tu ROI en campañas digitales (3.8x) supera al promedio del sector (2.5x). Considera aumentar inversión en este canal.',
      'La campaña "Cyber Days" tuvo un rendimiento 35% mejor que el año anterior. Los productos más vendidos fueron tecnología y moda.',
    ],
    cliente: [
      'Tus clientes se dividen en 4 segmentos principales: frecuentes (22%), ocasionales (45%), nuevos (18%) y dormidos (15%).',
      'El grupo más rentable representa solo el 18% de clientes pero genera el 54% de los ingresos.',
      'La tasa de retención ha mejorado un 8% este año. Recomendamos implementar un programa de fidelización para clientes frecuentes.',
    ],
    sunat: [
      'Detectamos patrones en tus datos que podrían optimizar tu declaración mensual de IGV. Te recomiendo revisar los registros de ventas de Marzo y Abril.',
      'Según tus volúmenes de venta, podrías calificar para el Régimen MYPE Tributario. Esto podría reducir tu tasa de impuesto a la renta.',
      'Tus gastos deducibles no están siendo completamente aprovechados. Hay aproximadamente S/ 4,200 en potenciales deducciones adicionales.',
    ],
    inventario: [
      'Tu rotación de inventario (4.2x) está por debajo del promedio del sector (6.8x). Los productos A1, B7 y C3 tienen mayor riesgo de obsolescencia.',
      'Recomendamos reducir stock de las categorías con baja rotación (-24% en categoría D) y aumentar en categorías de alta demanda (+18% en categoría A).',
      'El análisis de estacionalidad sugiere aumentar inventario 45 días antes de Fiestas Patrias y 60 días antes de Navidad.',
    ],
    default: [
      'Puedo ayudarte a entender patrones y generar insights sobre tus datos de ventas. Pregúntame sobre tendencias, predicciones o métricas específicas.',
      'Como tu asistente de datos, puedo analizar tu información de ventas desde diferentes perspectivas. ¿Te interesa algún análisis en particular?',
      'Para MYPES en Perú, puedo ayudarte con análisis competitivo, predicción de ventas, segmentación de clientes y optimización de inventario.',
    ],
  };

  // Auto-scroll al último mensaje
  useEffect(() => {
    mensajesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  const handleSendMessage = () => {
    const messageText = inputValue.trim();
    if (!messageText) return;

    // Agrega el mensaje del usuario
    const userMessage: Mensaje = {
      id: mensajes.length + 1,
      texto: messageText,
      emisor: 'usuario',
      timestamp: new Date(),
    };
    setMensajes((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simula respuesta del bot con un delay realista
    setTimeout(() => {
      const lowerInput = messageText.toLowerCase();
      let responseCategory = 'default';
      
      // Detecta la categoría basada en palabras clave
      if (lowerInput.includes('tendencia') || lowerInput.includes('trend') || lowerInput.includes('patrón')) {
        responseCategory = 'tendencia';
      } else if (lowerInput.includes('predic') || lowerInput.includes('proyec') || lowerInput.includes('futuro') || lowerInput.includes('próximo')) {
        responseCategory = 'predecir';
      } else if (lowerInput.includes('compar') || lowerInput.includes('benchmark') || lowerInput.includes('competencia') || lowerInput.includes('sector')) {
        responseCategory = 'comparar';
      } else if (lowerInput.includes('campaña') || lowerInput.includes('promoción') || lowerInput.includes('marketing') || lowerInput.includes('publicidad')) {
        responseCategory = 'campaña';
      } else if (lowerInput.includes('cliente') || lowerInput.includes('segmento') || lowerInput.includes('comprador') || lowerInput.includes('retención')) {
        responseCategory = 'cliente';
      } else if (lowerInput.includes('sunat') || lowerInput.includes('impuesto') || lowerInput.includes('tributario') || lowerInput.includes('igv')) {
        responseCategory = 'sunat';
      } else if (lowerInput.includes('inventario') || lowerInput.includes('stock') || lowerInput.includes('producto') || lowerInput.includes('rotación')) {
        responseCategory = 'inventario';
      }
      
      const possibleResponses = respuestasEjemplo[responseCategory];
      let responseText = possibleResponses[Math.floor(Math.random() * possibleResponses.length)];

      // Personaliza la respuesta con el nombre de la empresa y sector
      responseText = responseText
        .replace(/tu empresa/gi, nombreEmpresa)
        .replace(/del sector/gi, `del sector ${sector}`);

      const botMessage: Mensaje = {
        id: mensajes.length + 2,
        texto: responseText,
        emisor: 'bot',
        timestamp: new Date(),
      };

      setMensajes((prev) => [...prev, botMessage]);
      setIsTyping(false);
      
      // Genera nuevas sugerencias basadas en la conversación
      setSugerencias([
        responseCategory === 'tendencia' ? "¿Cómo mejorar estas tendencias?" : "Ver tendencias por producto",
        responseCategory === 'predecir' ? "¿Qué factores afectan esta predicción?" : "Predecir ventas próximo trimestre",
        responseCategory === 'cliente' ? "¿Cómo retener más clientes?" : "Analizar segmentos de clientes",
        responseCategory === 'inventario' ? "Optimizar niveles de inventario" : "Estrategias para aumentar ventas",
      ]);
    }, 1000 + Math.random() * 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Formatea la hora en formato HH:MM
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' });
  };

  // Maneja click en sugerencia
  const handleSugerenciaClick = (sugerencia: string) => {
    setInputValue(sugerencia);
    // Pequeño delay para mejor UX
    setTimeout(() => {
      handleSendMessage();
    }, 300);
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