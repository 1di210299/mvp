// src/pages/DatasetsPage.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Filter, 
  SortDesc, 
  FileText, 
  Calendar, 
  Database,
  BarChart,
  Users,
  Boxes,
  TrendingUp,
  DollarSign,
  Trash2
} from 'lucide-react';
import { datasetService, Dataset } from '../api/services';

const DatasetsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Cargar datasets al montar el componente
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        setLoading(true);
        const response = await datasetService.getAll();
        setDatasets(response.data);
      } catch (err: any) {
        console.error('Error fetching datasets:', err);
        setError(err.response?.data?.error || 'Error al cargar los datasets');
      } finally {
        setLoading(false);
      }
    };

    fetchDatasets();
  }, []);
  
  // Filtrar datasets basados en búsqueda y tipo
  const filteredDatasets = datasets.filter(dataset => {
    const matchesSearch = 
      dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (dataset.description && dataset.description.toLowerCase().includes(searchTerm.toLowerCase()));
      
    const matchesType = selectedType === 'all' || 
                        (dataset.category && dataset.category.toLowerCase() === selectedType.toLowerCase());
    
    return matchesSearch && matchesType;
  });

  // Función para manejar la eliminación de un dataset
  const handleDeleteDataset = async (id: number, e: React.MouseEvent) => {
    e.preventDefault(); // Evitar navegación
    e.stopPropagation(); // Evitar que el click llegue al enlace padre
    
    if (window.confirm('¿Estás seguro de eliminar este dataset?')) {
      try {
        await datasetService.delete(id);
        // Actualizar la lista después de eliminar
        setDatasets(prevDatasets => prevDatasets.filter(dataset => dataset.id !== id));
      } catch (err: any) {
        console.error('Error deleting dataset:', err);
        alert(err.response?.data?.error || 'Error al eliminar el dataset');
      }
    }
  };
  
  // Determinar el icono según la categoría del dataset
  const getDatasetIcon = (category: string) => {
    const categoryLower = category ? category.toLowerCase() : '';
    
    if (categoryLower.includes('venta')) return <BarChart size={24} className="text-cyber-cyan" />;
    if (categoryLower.includes('cliente')) return <Users size={24} className="text-blue-400" />;
    if (categoryLower.includes('inventario')) return <Boxes size={24} className="text-green-400" />;
    if (categoryLower.includes('marketing')) return <TrendingUp size={24} className="text-purple-400" />;
    if (categoryLower.includes('finanza')) return <DollarSign size={24} className="text-yellow-400" />;
    return <Database size={24} className="text-cyber-text/70" />;
  };
  
  // Renderizar pantalla de carga
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-cyber-cyan"></div>
      </div>
    );
  }
  
  // Renderizar mensaje de error
  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-900/30 border border-red-500/30 text-red-400 px-4 py-3 rounded mb-4">
          <h3 className="font-medium mb-2">Error</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

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
                      {getDatasetIcon(dataset.category)}
                    </div>
                    
                    <div className="flex-grow min-w-0">
                      <div className="flex flex-col md:flex-row md:justify-between md:items-start">
                        <div>
                          <h3 className="text-lg font-medium text-cyber-text truncate">{dataset.name}</h3>
                          <p className="text-cyber-text/70 text-sm">{dataset.description || 'Sin descripción'}</p>
                        </div>
                        <div className="md:text-right mt-2 md:mt-0 flex items-center">
                          <span className="inline-block px-2 py-1 text-xs rounded-full bg-cyber-detail/40 text-cyber-text mr-2">
                            {dataset.category || 'Sin categoría'}
                          </span>
                          <button
                            onClick={(e) => handleDeleteDataset(dataset.id, e)}
                            className="p-1 text-red-400 hover:bg-red-900/30 rounded"
                            title="Eliminar dataset"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                      
                      <div className="mt-3 flex flex-col md:flex-row md:items-center text-xs text-cyber-text/60">
                        <div className="flex items-center">
                          <FileText size={14} className="mr-1" />
                          <span>{dataset.columns?.length || 0} columnas</span>
                        </div>
                        <span className="hidden md:block mx-2">•</span>
                        <div className="flex items-center">
                          <Calendar size={14} className="mr-1" />
                          <span>Creado: {new Date(dataset.created_at).toLocaleDateString()}</span>
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
      
      {/* Modal para nuevo dataset - se implementaría con un componente modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-cyber-dark/90 p-6 rounded-lg border border-cyber-cyan/20 max-w-md w-full">
            <h2 className="text-xl text-cyber-text font-bold mb-4">Nuevo Dataset</h2>
            
            <p className="text-cyber-text/70 mb-6">
              La funcionalidad de crear nuevos datasets está pendiente de implementación
            </p>
            
            <div className="flex justify-end">
              <button
                className="px-4 py-2 bg-cyber-detail/50 text-cyber-text rounded hover:bg-cyber-detail transition-colors mr-2"
                onClick={() => setIsModalOpen(false)}
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetsPage;