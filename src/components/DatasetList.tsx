// src/components/DatasetList.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { datasetService, Dataset } from '../api/services';

const DatasetList: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const handleDelete = async (id: number) => {
    if (!window.confirm('¿Estás seguro de eliminar este dataset?')) {
      return;
    }

    try {
      await datasetService.delete(id);
      setDatasets(prevDatasets => prevDatasets.filter(dataset => dataset.id !== id));
    } catch (err: any) {
      console.error('Error deleting dataset:', err);
      alert(err.response?.data?.error || 'Error al eliminar el dataset');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-48">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-cyber-cyan"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/30 border border-red-500/30 text-red-400 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (datasets.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-cyber-text/70 mb-4">No hay datasets disponibles.</p>
        <Link 
          to="/dashboard/datasets/new" 
          className="px-4 py-2 bg-cyber-cyan text-cyber-dark rounded hover:bg-cyber-cyan/90 transition-colors"
        >
          Crear nuevo dataset
        </Link>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {datasets.map(dataset => (
        <div 
          key={dataset.id} 
          className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg"
        >
          <h3 className="text-lg font-semibold text-cyber-cyan mb-1">{dataset.name}</h3>
          <p className="text-cyber-text/70 text-sm mb-4 line-clamp-2">{dataset.description}</p>
          
          <div className="flex items-center justify-between mt-4">
            <Link 
              to={`/dashboard/datasets/${dataset.id}`}
              className="px-3 py-1 bg-cyber-cyan/20 text-cyber-cyan rounded hover:bg-cyber-cyan/30 transition-colors text-sm"
            >
              Ver detalles
            </Link>
            
            <button
              onClick={() => handleDelete(dataset.id)}
              className="px-3 py-1 bg-red-900/20 text-red-400 rounded hover:bg-red-900/30 transition-colors text-sm"
            >
              Eliminar
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DatasetList;