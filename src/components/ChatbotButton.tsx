// ChatbotButton.tsx
import { useState } from "react";
import { motion } from "framer-motion";
import { MessageCircle, X } from "lucide-react";
import React from "react";

export default function ChatbotButton() {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  
  console.log("ChatbotButton rendering", { isOpen });

  return (
    <div className="fixed bottom-6 right-6 flex flex-col items-end z-50">
      {/* Chatbot Window */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="w-80 h-96 bg-white shadow-2xl rounded-2xl p-4 border border-gray-200 mb-4"
        >
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Chatbot</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              <X size={20} />
            </button>
          </div>
          <div className="h-full flex items-center justify-center text-gray-500">
            <p>Hola! ¿Cómo puedo ayudarte? 😊</p>
          </div>
        </motion.div>
      )}

      {/* Floating Chat Button */}
      <motion.button
        onClick={() => {
          setIsOpen(!isOpen);
          console.log("Button clicked, isOpen:", !isOpen);
        }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className="p-4 bg-blue-600 text-white rounded-full shadow-lg flex items-center justify-center z-50"
      >
        <MessageCircle size={24} />
      </motion.button>
    </div>
  );
}