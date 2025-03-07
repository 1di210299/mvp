// src/components/DatasetChatbot.tsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send } from 'lucide-react';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface DatasetChatbotProps {
  datasetId: number;
  datasetName: string;
}

function DatasetChatbot({ datasetId, datasetName }: DatasetChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: `Hi! I'm your AI assistant for the "${datasetName}" dataset. Ask me any questions about the data, analysis, or predictions.`,
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Respuestas de ejemplo según palabras clave (en un entorno real se consultaría al backend AI)
  const sampleResponses: Record<string, string[]> = {
    trend: [
      'The main trend shows a 15% growth over the last quarter.',
      'We’re seeing a cyclical pattern with peaks every 3 months.',
      'There’s a downward trend in category C, but growth in categories A and B offsets it.',
    ],
    predict: [
      'Based on this data, we predict a 23% increase in the next 30 days.',
      'Our prediction model shows a potential market shift by Q3.',
      'The prediction confidence is currently at 87% for the primary scenario.',
    ],
    compare: [
      'Compared to similar datasets, this one shows 30% higher variance.',
      'Category A performs 45% better than category B in terms of conversion.',
      'When compared to last year, we see a 12% improvement in key metrics.',
    ],
    summary: [
      `This dataset contains performance metrics over time, with a strong correlation between variables X and Y. Prediction models average an 87% accuracy.`,
    ],
    default: [
      'I can help you understand patterns and insights from this dataset. Try asking about trends, predictions, or specific metrics.',
      'This dataset shows several interesting patterns. Would you like me to explain any particular aspect?',
      'I can analyze this data from different perspectives. What specific information are you looking for?',
    ],
  };

  // Auto-scroll a la última respuesta
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = () => {
    const messageText = inputValue.trim();
    if (!messageText) return;

    // Agrega el mensaje del usuario
    const userMessage: Message = {
      id: messages.length + 1,
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simula respuesta del bot con un delay realista
    setTimeout(() => {
      const lowerInput = messageText.toLowerCase();
      const responseCategory =
        Object.keys(sampleResponses).find((key) => lowerInput.includes(key)) || 'default';
      const possibleResponses = sampleResponses[responseCategory];
      let responseText =
        possibleResponses[Math.floor(Math.random() * possibleResponses.length)];

      // Menciona explícitamente el nombre del dataset
      responseText = responseText.replace(
        'this dataset',
        `the "${datasetName}" dataset`
      );

      const botMessage: Message = {
        id: messages.length + 2,
        text: responseText,
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
      setIsTyping(false);
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
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex flex-col h-full bg-[#1E2A38] rounded-lg shadow-xl overflow-hidden">
      {/* Cabecera */}
      <div className="p-4 border-b border-[#2F3C48] bg-[#1E2A38]">
        <h3 className="text-lg font-semibold text-[#E6E6E6]">Dataset Assistant</h3>
        <p className="text-sm text-[#E6E6E6]/70">Ask questions about {datasetName}</p>
      </div>

      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.3 }}
              className={`flex ${
                message.sender === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 shadow-md ${
                  message.sender === 'user'
                    ? 'bg-[#00B8D9] text-[#1E2A38]'
                    : 'bg-[#2F3C48] text-[#E6E6E6]'
                }`}
              >
                <p>{message.text}</p>
                <p
                  className={`text-xs mt-1 ${
                    message.sender === 'user'
                      ? 'text-[#1E2A38]/70'
                      : 'text-[#E6E6E6]/70'
                  }`}
                >
                  {formatTime(message.timestamp)}
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
            <div className="bg-[#2F3C48] text-[#E6E6E6] rounded-lg px-4 py-2 shadow-md">
              <div className="flex space-x-1">
                <div className="w-2 h-2 rounded-full bg-[#00B8D9] animate-bounce" />
                <div
                  className="w-2 h-2 rounded-full bg-[#00B8D9] animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
                <div
                  className="w-2 h-2 rounded-full bg-[#00B8D9] animate-bounce"
                  style={{ animationDelay: '0.4s' }}
                />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input de mensaje */}
      <div className="p-4 border-t border-[#2F3C48] bg-[#1E2A38]">
        <div className="flex items-center space-x-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask something about this dataset..."
            className="flex-1 px-4 py-2 bg-[#2F3C48]/50 text-[#E6E6E6] border border-[#2F3C48] rounded focus:outline-none focus:border-[#00B8D9] resize-none"
            rows={1}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            className={`p-2 rounded focus:outline-none focus:ring-2 focus:ring-[#00B8D9] transition ${
              !inputValue.trim() || isTyping
                ? 'bg-[#2F3C48] text-[#E6E6E6]/40 cursor-not-allowed'
                : 'bg-[#00B8D9] text-[#1E2A38] hover:bg-[#00B8D9]/90'
            }`}
            aria-label="Send Message"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default DatasetChatbot;
