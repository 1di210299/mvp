import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X } from 'lucide-react';

function ChatbotButton() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="chatbot"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="w-80 h-96 bg-white rounded-2xl p-4 border border-gray-300 shadow-xl mb-4 flex flex-col"
            role="dialog"
            aria-label="Chatbot Window"
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800">Chatbot</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 rounded-full text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition"
                aria-label="Close Chatbot"
              >
                <X size={20} />
              </button>
            </div>
            <div className="flex-grow flex items-center justify-center text-gray-500">
              <p className="text-center">¡Hola! ¿Cómo puedo ayudarte hoy?</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={() => setIsOpen(prev => !prev)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        className="p-4 bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 rounded-full shadow-lg flex items-center justify-center"
        aria-label="Open Chatbot"
      >
        <MessageCircle size={24} />
      </motion.button>
    </div>
  );
}

export default ChatbotButton;
