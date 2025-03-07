// src/components/DatasetsPage.tsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Filter, 
  SortDesc, 
  FileText, 
  Calendar, 
  Database,
  BarChart
} from 'lucide-react';

// Datos de ejemplo para los datasets
const datasetsList = [
  {
    id: '1',
    name: 'Dataset 1',
    description: 'Datos de ventas mensuales 2024',
    type: 'Ventas',
    format: 'CSV',
    size: '1.2 MB',
    rows: 1250,
    updatedAt: '01 Mar, 2025',
    tags: ['ventas', 'mensual', '2024']
  },
  {
    id: '2',
    name: 'Dataset 2',
    description: 'Segmentación de clientes por región',
    type: 'Clientes',
    format: 'Excel',
    size: '850 KB',
    rows: 845,
    updatedAt: '28 Feb, 2025',
    tags: ['clientes', 'segmentación', 'regional']
  },
  {
    id: '3',
    name: 'Dataset 3',
    description: 'Inventario y rotación de productos',
    type: 'Inventario',
    format: 'CSV',
    size: '640 KB',
    rows: 523,
    updatedAt: '25 Feb, 2025',
    tags: ['inventario', 'productos', 'rotación']
  },
  {
    id: '4',
    name: 'Dataset 4',
    description: 'Análisis de campañas marketing 2024',
    type: 'Marketing',
    format: 'Excel',
    size: '1.5 MB',
    rows: 325,
    updatedAt: '03 Mar, 2025',
    tags: ['marketing', 'campañas', '2024']
  },
  {
    id: '5',
    name: 'Dataset 5',
    description: 'Datos financieros trimestrales',
    type: 'Finanzas',
    format: 'CSV',
    size: '920 KB',
    rows: 120,
    updatedAt: '01 Mar, 2025',
    tags: ['finanzas', 'trimestral', '2024']
  }
];

// Componente principal
const DatasetsPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Filtrar datasets basados en búsqueda y tipo
  const filteredDatasets = datasetsList.filter(dataset => {
    const matchesSearch = 
      dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      dataset.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      dataset.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      
    const matchesType = selectedType === 'all' || dataset.type.toLowerCase() === selectedType.toLowerCase();
    
    return matchesSearch && matchesType;
  });
  
  return (
    <div className="p-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyber-text">Datasets</h1>
          <p className="text-cyber-text/70">Gestiona y analiza tus fuentes de datos</p>
        </div>
        <div className="mt-4 md:mt-0">
          <button 
            className="flex items-center bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors"
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={16} className="mr-1" />
            Nuevo Dataset
          </button>
        </div>
      </div>
      
      {/* Filtros y búsqueda */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-grow">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={16} className="text-cyber-text/50" />
            </div>
            <input
              type="text"
              placeholder="Buscar datasets..."
              className="pl-10 w-full px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="flex flex-wrap gap-2">
            <select
              className="px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
            >
              <option value="all">Todos los tipos</option>
              <option value="ventas">Ventas</option>
              <option value="clientes">Clientes</option>
              <option value="inventario">Inventario</option>
              <option value="marketing">Marketing</option>
              <option value="finanzas">Finanzas</option>
            </select>
            
            <button className="flex items-center px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded hover:bg-cyber-detail/50 transition-colors">
              <Filter size={16} className="mr-1" />
              Filtros
            </button>
            
            <button className="flex items-center px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded hover:bg-cyber-detail/50 transition-colors">
              <SortDesc size={16} className="mr-1" />
              Ordenar
            </button>
          </div>
        </div>
      </div>
      
      {/* Lista de datasets */}
      <div className="bg-cyber-dark/70 backdrop-blur-sm rounded-lg border border-cyber-cyan/20 shadow-lg overflow-hidden">
        {filteredDatasets.length > 0 ? (
          <div className="divide-y divide-cyber-detail/30">
            {filteredDatasets.map((dataset) => (
              <Link
                key={dataset.id}
                to={`/dashboard/datasets/${dataset.id}`}
                className="block hover:bg-cyber-detail/20 transition-colors"
              >
                <div className="p-4">
                  <div className="flex items-start">
                    <div className="flex-shrink-0 p-2 bg-cyber-detail/30 rounded mr-4">
                      {dataset.type === 'Ventas' && <BarChart size={24} className="text-cyber-cyan" />}
                      {dataset.type === 'Clientes' && <Users size={24} className="text-blue-400" />}
                      {dataset.type === 'Inventario' && <Boxes size={24} className="text-green-400" />}
                      {dataset.type === 'Marketing' && <TrendingUp size={24} className="text-purple-400" />}
                      {dataset.type === 'Finanzas' && <DollarSign size={24} className="text-yellow-400" />}
                      {!['Ventas', 'Clientes', 'Inventario', 'Marketing', 'Finanzas'].includes(dataset.type) && (
                        <Database size={24} className="text-cyber-text/70" />
                      )}
                    </div>
                    
                    <div className="flex-grow min-w-0">
                      <div className="flex flex-col md:flex-row md:justify-between md:items-start">
                        <div>
                          <h3 className="text-lg font-medium text-cyber-text truncate">{dataset.name}</h3>
                          <p className="text-cyber-text/70 text-sm">{dataset.description}</p>
                        </div>
                        <div className="md:text-right mt-2 md:mt-0">
                          <span className="inline-block px-2 py-1 text-xs rounded-full bg-cyber-detail/40 text-cyber-text">
                            {dataset.format}
                          </span>
                        </div>
                      </div>
                      
                      <div className="mt-2 flex flex-wrap gap-2">
                        {dataset.tags.map((tag, tagIndex) => (
                          <span 
                            key={tagIndex}
                            className="px-2 py-0.5 bg-cyber-detail/30 text-cyber-text/70 text-xs rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                      
                      <div className="mt-3 flex flex-col md:flex-row md:items-center text-xs text-cyber-text/60">
                        <div className="flex items-center">
                          <FileText size={14} className="mr-1" />
                          <span>{dataset.rows.toLocaleString()} filas</span>
                        </div>
                        <span className="hidden md:block mx-2">•</span>
                        <div className="flex items-center">
                          <Database size={14} className="mr-1" />
                          <span>{dataset.size}</span>
                        </div>
                        <span className="hidden md:block mx-2">•</span>
                        <div className="flex items-center">
                          <Calendar size={14} className="mr-1" />
                          <span>Actualizado: {dataset.updatedAt}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <div className="inline-flex items-center justify-center p-4 rounded-full bg-cyber-detail/30 text-cyber-text/70 mb-4">
              <Database size={32} />
            </div>
            <p className="text-cyber-text/70 mb-2">No se encontraron datasets</p>
            <p className="text-cyber-text/50 text-sm mb-4">Intenta con otra búsqueda o crea un nuevo dataset</p>
            <button 
              className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors"
              onClick={() => setIsModalOpen(true)}
            >
              <Plus size={16} className="inline mr-1" />
              Nuevo Dataset
            </button>
          </div>
        )}
      </div>
      
      {/* Modal para nuevo dataset (comentado por ahora) */}
      {/* {isModalOpen && (
        <AddDatasetModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSave={handleAddDataset}
        />
      )} */}
    </div>
  );
};

import { Users, Boxes, TrendingUp, DollarSign } from 'lucide-react';

export default DatasetsPage;