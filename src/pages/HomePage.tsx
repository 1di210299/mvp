// src/pages/HomePage.tsx

import React from 'react';
import { Plus } from 'lucide-react'; // npm install lucide-react
import ChatbotButton from '../components/ChatbotButton';
import DatasetListWithMetrics from '../components/DatasetListWithMetrics';
import DatasetsChart from '../components/DatasetsChart';
import ExperimentsChart from '../components/ExperimentsChart';

function HomePage() {
  return (
    <div className="p-4 space-y-6 bg-transparent">
      {/* FILA SUPERIOR: Barra de búsqueda + Botón redondo */}
      <div className="flex items-center justify-between">
        <input
          type="text"
          placeholder="Search..."
          className="border border-gray-600 bg-transparent text-cyber-text rounded px-3 py-2 focus:outline-none"
        />

        <button
          className="bg-cyber-primary text-black rounded-full p-3 hover:bg-cyan-300 transition-colors"
          onClick={() => alert('Add new dataset')}
        >
          <Plus size={20} />
        </button>
      </div>

      {/* SECCIÓN: Lista de datasets con fondo semitransparente */}
      <div className="bg-black/50 backdrop-blur-sm p-4 rounded border border-gray-600 shadow">
        <h4 className="text-lg font-semibold mb-2 text-white">Recently Used Datasets</h4>
        <DatasetListWithMetrics />
      </div>

      {/* FILA INFERIOR: Gráficos */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          className="bg-black/50 backdrop-blur-sm p-4 rounded border border-gray-600 shadow"
          style={{ minHeight: 400 }}
        >
          <DatasetsChart />
        </div>
        <div
          className="bg-black/50 backdrop-blur-sm p-4 rounded border border-gray-600 shadow"
          style={{ minHeight: 400 }}
        >
          <ExperimentsChart />
        </div>
      </div>

      {/* Botón flotante del Chatbot */}
      <ChatbotButton />
    </div>
  );
}

export default HomePage;
