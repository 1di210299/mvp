// src/components/DatasetDetail.tsx
import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Download, 
  Share2, 
  BarChart, 
  Table, 
  Code, 
  Settings,
  Trash2,
  Plus,
  Info,
  Calendar,
  Tag,
  FileText,
  Sparkles
} from 'lucide-react';

// Definir las interfaces para tipar correctamente los datos
interface DatasetPreviewItem {
  id: number;
  [key: string]: string | number;
}

interface Dataset {
  id: string;
  name: string;
  description: string;
  type: string;
  format: string;
  rows: number;
  columns: number;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  owner: string;
  preview: DatasetPreviewItem[];
}

// Datos de ejemplo para simular información del dataset
const getDatasetInfo = (id: string): Dataset => {
  console.log("Buscando dataset con ID:", id);
  
  const datasets: Dataset[] = [
    {
      id: '1',
      name: 'Dataset 1',
      description: 'Datos de ventas mensuales 2024',
      type: 'Ventas',
      format: 'CSV',
      rows: 1250,
      columns: 12,
      createdAt: '15 Feb, 2025',
      updatedAt: '01 Mar, 2025',
      tags: ['ventas', 'mensual', '2024'],
      owner: 'Juan Diego',
      preview: [
        { id: 1, fecha: '2024-01-01', producto: 'Laptop Dell XPS', cantidad: 5, precio: 4500, total: 22500 },
        { id: 2, fecha: '2024-01-02', producto: 'Monitor LG 27"', cantidad: 8, precio: 1200, total: 9600 },
        { id: 3, fecha: '2024-01-03', producto: 'Teclado Logitech', cantidad: 12, precio: 280, total: 3360 },
        { id: 4, fecha: '2024-01-04', producto: 'Mouse Logitech', cantidad: 15, precio: 120, total: 1800 },
        { id: 5, fecha: '2024-01-05', producto: 'Audífonos Sony', cantidad: 7, precio: 450, total: 3150 },
      ]
    },
    {
      id: '2',
      name: 'Dataset 2',
      description: 'Segmentación de clientes por región',
      type: 'Clientes',
      format: 'Excel',
      rows: 845,
      columns: 18,
      createdAt: '10 Feb, 2025',
      updatedAt: '28 Feb, 2025',
      tags: ['clientes', 'segmentación', 'regional'],
      owner: 'Juan Diego',
      preview: [
        { id: 1, cliente: 'Empresa ABC', region: 'Lima', categoria: 'Premium', compras: 15, valor: 45000 },
        { id: 2, cliente: 'Comercial XYZ', region: 'Arequipa', categoria: 'Standard', compras: 8, valor: 12000 },
        { id: 3, cliente: 'Distribuidora 123', region: 'Trujillo', categoria: 'Premium', compras: 12, valor: 36000 },
        { id: 4, cliente: 'Tienda Online', region: 'Lima', categoria: 'Basic', compras: 5, valor: 5500 },
        { id: 5, cliente: 'Corporación Perú', region: 'Cusco', categoria: 'Premium', compras: 10, valor: 28000 },
      ]
    },
    {
      id: '3',
      name: 'Dataset 3',
      description: 'Inventario y rotación de productos',
      type: 'Inventario',
      format: 'CSV',
      rows: 523,
      columns: 9,
      createdAt: '05 Feb, 2025',
      updatedAt: '25 Feb, 2025',
      tags: ['inventario', 'productos', 'rotación'],
      owner: 'Juan Diego',
      preview: [
        { id: 1, sku: 'LAP-001', producto: 'Laptop Dell XPS', stock: 12, rotacion: 'Alta', reorden: 5, valorizado: 54000 },
        { id: 2, sku: 'MON-027', producto: 'Monitor LG 27"', stock: 18, rotacion: 'Media', reorden: 8, valorizado: 21600 },
        { id: 3, sku: 'TEC-012', producto: 'Teclado Logitech', stock: 25, rotacion: 'Alta', reorden: 10, valorizado: 7000 },
        { id: 4, sku: 'MOU-005', producto: 'Mouse Logitech', stock: 30, rotacion: 'Alta', reorden: 15, valorizado: 3600 },
        { id: 5, sku: 'AUD-023', producto: 'Audífonos Sony', stock: 9, rotacion: 'Media', reorden: 5, valorizado: 4050 },
      ]
    },
    {
      id: '4',
      name: 'Dataset 4',
      description: 'Análisis de campañas marketing 2024',
      type: 'Marketing',
      format: 'Excel',
      rows: 325,
      columns: 15,
      createdAt: '20 Feb, 2025',
      updatedAt: '03 Mar, 2025',
      tags: ['marketing', 'campañas', '2024'],
      owner: 'Juan Diego',
      preview: [
        { id: 1, campaña: 'Facebook Ads Q1', inversion: 5000, clics: 15000, conversiones: 350, cpa: 14.3 },
        { id: 2, campaña: 'Google Ads Q1', inversion: 7500, clics: 12500, conversiones: 420, cpa: 17.9 },
        { id: 3, campaña: 'Email Marketing', inversion: 1200, clics: 4500, conversiones: 180, cpa: 6.7 },
        { id: 4, campaña: 'Instagram Stories', inversion: 3000, clics: 9000, conversiones: 210, cpa: 14.3 },
        { id: 5, campaña: 'TikTok Ads Test', inversion: 1500, clics: 8500, conversiones: 125, cpa: 12.0 },
      ]
    },
    {
      id: '5',
      name: 'Dataset 5',
      description: 'Datos financieros trimestrales',
      type: 'Finanzas',
      format: 'CSV',
      rows: 120,
      columns: 22,
      createdAt: '01 Feb, 2025',
      updatedAt: '01 Mar, 2025',
      tags: ['finanzas', 'trimestral', '2024'],
      owner: 'Juan Diego',
      preview: [
        { id: 1, trimestre: 'Q1 2024', ingresos: 125000, costos: 78000, utilidad: 47000, margen: 37.6 },
        { id: 2, trimestre: 'Q2 2024', ingresos: 148000, costos: 86000, utilidad: 62000, margen: 41.9 },
        { id: 3, trimestre: 'Q3 2024', ingresos: 135000, costos: 82500, utilidad: 52500, margen: 38.9 },
        { id: 4, trimestre: 'Q4 2024', ingresos: 180000, costos: 105000, utilidad: 75000, margen: 41.7 },
        { id: 5, trimestre: 'Q1 2025 (Proy)', ingresos: 160000, costos: 92000, utilidad: 68000, margen: 42.5 },
      ]
    }
  ];
  
  const foundDataset = datasets.find(ds => ds.id === id);
  console.log("Dataset encontrado:", foundDataset);
  return foundDataset || datasets[0];
};

// Parámetros para useParams
interface DatasetParams {
  id: string;
}

// Vista principal del detalle del dataset
const DatasetDetail: React.FC = () => {
  const { id } = useParams<DatasetParams>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<string>('data');
  const [loading, setLoading] = useState<boolean>(true);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  
  useEffect(() => {
    // Simular carga de datos
    console.log("ID del parámetro:", id);
    setLoading(true);
    
    setTimeout(() => {
      if (id) {
        const datasetInfo = getDatasetInfo(id);
        setDataset(datasetInfo);
      }
      setLoading(false);
    }, 500);
  }, [id]);
  
  // Si está cargando o no hay dataset, mostrar indicador de carga
  if (loading || !dataset) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyber-cyan"></div>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      {/* Encabezado y navegación */}
      <div className="mb-6">
        <div className="flex items-center mb-2">
          <Link 
            to="/dashboard/datasets"
            className="text-cyber-text/70 hover:text-cyber-cyan mr-2"
          >
            <ArrowLeft size={18} />
          </Link>
          <h1 className="text-2xl font-bold text-cyber-text">{dataset.name}</h1>
        </div>
        <p className="text-cyber-text/70">{dataset.description}</p>
      </div>
      
      {/* Acciones rápidas */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button className="flex items-center bg-cyber-cyan text-cyber-dark px-4 py-2 rounded hover:bg-cyber-cyan/90 transition-colors">
          <BarChart size={16} className="mr-1" />
          Visualizar
        </button>
        <button className="flex items-center bg-cyber-detail/50 text-cyber-text px-4 py-2 rounded hover:bg-cyber-detail/70 transition-colors">
          <Download size={16} className="mr-1" />
          Exportar
        </button>
        <button className="flex items-center bg-cyber-detail/50 text-cyber-text px-4 py-2 rounded hover:bg-cyber-detail/70 transition-colors">
          <Share2 size={16} className="mr-1" />
          Compartir
        </button>
        <button className="flex items-center bg-red-700/30 text-red-400 px-4 py-2 rounded hover:bg-red-700/50 transition-colors ml-auto">
          <Trash2 size={16} className="mr-1" />
          Eliminar
        </button>
      </div>
      
      {/* Pestañas */}
      <div className="border-b border-cyber-detail mb-6">
        <div className="flex flex-wrap">
          <button 
            className={`px-4 py-2 border-b-2 ${
              activeTab === 'data' 
                ? 'border-cyber-cyan text-cyber-cyan' 
                : 'border-transparent text-cyber-text/70 hover:text-cyber-text'
            }`}
            onClick={() => setActiveTab('data')}
          >
            <div className="flex items-center">
              <Table size={16} className="mr-1" />
              Datos
            </div>
          </button>
          <button 
            className={`px-4 py-2 border-b-2 ${
              activeTab === 'visualization' 
                ? 'border-cyber-cyan text-cyber-cyan' 
                : 'border-transparent text-cyber-text/70 hover:text-cyber-text'
            }`}
            onClick={() => setActiveTab('visualization')}
          >
            <div className="flex items-center">
              <BarChart size={16} className="mr-1" />
              Visualización
            </div>
          </button>
          <button 
            className={`px-4 py-2 border-b-2 ${
              activeTab === 'schema' 
                ? 'border-cyber-cyan text-cyber-cyan' 
                : 'border-transparent text-cyber-text/70 hover:text-cyber-text'
            }`}
            onClick={() => setActiveTab('schema')}
          >
            <div className="flex items-center">
              <Code size={16} className="mr-1" />
              Esquema
            </div>
          </button>
          <button 
            className={`px-4 py-2 border-b-2 ${
              activeTab === 'settings' 
                ? 'border-cyber-cyan text-cyber-cyan' 
                : 'border-transparent text-cyber-text/70 hover:text-cyber-text'
            }`}
            onClick={() => setActiveTab('settings')}
          >
            <div className="flex items-center">
              <Settings size={16} className="mr-1" />
              Configuración
            </div>
          </button>
        </div>
      </div>
      
      {/* Contenido de la pestaña actual */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Contenido principal (3/4 del ancho) */}
        <div className="lg:col-span-3">
          {activeTab === 'data' && (
            <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-cyber-text">Vista de Datos</h3>
                <div className="flex space-x-2">
                  <button className="text-cyber-text/70 hover:text-cyber-cyan">
                    <Plus size={18} />
                  </button>
                  <button className="text-cyber-text/70 hover:text-cyber-cyan">
                    <Download size={18} />
                  </button>
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-cyber-detail">
                  <thead className="bg-cyber-detail/30">
                    <tr>
                      {Object.keys(dataset.preview[0]).map((key) => (
                        <th 
                          key={key}
                          className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider"
                        >
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-cyber-detail/10 divide-y divide-cyber-detail/30">
                    {dataset.preview.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-cyber-detail/20">
                        {Object.values(row).map((value, cellIndex) => (
                          <td key={cellIndex} className="px-4 py-2 whitespace-nowrap text-sm text-cyber-text">
                            {String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="flex justify-between items-center mt-4 text-sm text-cyber-text/70">
                <div>Mostrando 5 de {dataset.rows} filas</div>
                <div className="flex space-x-2">
                  <button className="px-3 py-1 border border-cyber-detail/50 rounded hover:bg-cyber-detail/30">Anterior</button>
                  <button className="px-3 py-1 border border-cyber-detail/50 rounded hover:bg-cyber-detail/30">Siguiente</button>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'visualization' && (
            <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-cyber-text">Visualización de Datos</h3>
                <div className="flex space-x-2">
                  <select className="bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded px-3 py-1 text-sm">
                    <option>Gráfico de Barras</option>
                    <option>Gráfico de Líneas</option>
                    <option>Gráfico Circular</option>
                    <option>Dispersión</option>
                  </select>
                </div>
              </div>
              
              <div className="h-64 flex items-center justify-center bg-cyber-detail/20 rounded border border-cyber-detail/50 mb-4">
                <div className="text-center">
                  <BarChart size={48} className="mx-auto text-cyber-cyan/40 mb-2" />
                  <p className="text-cyber-text/70">
                    Seleccione columnas para visualizar o use nuestras sugerencias automáticas
                  </p>
                  <button className="mt-4 px-4 py-2 bg-cyber-cyan text-cyber-dark rounded hover:bg-cyber-cyan/90 transition-colors">
                    Generar Visualización
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-cyber-detail/20 p-3 rounded border border-cyber-detail/50">
                  <h4 className="text-sm font-medium text-cyber-text mb-2">Sugerencias de IA</h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center text-cyber-text/70 hover:text-cyber-cyan cursor-pointer">
                      <BarChart size={14} className="mr-1" />
                      <span>Distribución por categoría</span>
                    </li>
                    <li className="flex items-center text-cyber-text/70 hover:text-cyber-cyan cursor-pointer">
                      <BarChart size={14} className="mr-1" />
                      <span>Tendencia temporal</span>
                    </li>
                    <li className="flex items-center text-cyber-text/70 hover:text-cyber-cyan cursor-pointer">
                      <BarChart size={14} className="mr-1" />
                      <span>Comparación de valores</span>
                    </li>
                  </ul>
                </div>
                
                <div className="bg-cyber-detail/20 p-3 rounded border border-cyber-detail/50">
                  <h4 className="text-sm font-medium text-cyber-text mb-2">Columnas a visualizar</h4>
                  <div className="space-y-2">
                    <div className="flex items-center">
                      <input 
                        type="checkbox" 
                        id="col1" 
                        className="mr-2 h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail/50 rounded"
                      />
                      <label htmlFor="col1" className="text-sm text-cyber-text/70">Columna X</label>
                    </div>
                    <div className="flex items-center">
                      <input 
                        type="checkbox" 
                        id="col2" 
                        className="mr-2 h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail/50 rounded"
                      />
                      <label htmlFor="col2" className="text-sm text-cyber-text/70">Columna Y</label>
                    </div>
                    <div className="flex items-center">
                      <input 
                        type="checkbox" 
                        id="col3" 
                        className="mr-2 h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail/50 rounded"
                      />
                      <label htmlFor="col3" className="text-sm text-cyber-text/70">Columna Z</label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'schema' && (
            <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-cyber-text">Esquema del Dataset</h3>
                <button className="text-cyber-text/70 hover:text-cyber-cyan flex items-center text-sm">
                  <Download size={14} className="mr-1" />
                  Exportar Esquema
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-cyber-detail">
                  <thead className="bg-cyber-detail/30">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">Columna</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">Tipo</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">Descripción</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-cyber-text/70 uppercase tracking-wider">Ejemplo</th>
                    </tr>
                  </thead>
                  <tbody className="bg-cyber-detail/10 divide-y divide-cyber-detail/30">
                    {Object.keys(dataset.preview[0]).slice(1).map((column, index) => (
                      <tr key={index} className="hover:bg-cyber-detail/20">
                        <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-cyber-text">{column}</td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm text-cyber-text">
                          {typeof dataset.preview[0][column] === 'number' ? 'Número' : 'Texto'}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm text-cyber-text/70">
                          {`Contiene datos de ${column}`}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm text-cyber-text">
                          {String(dataset.preview[0][column])}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="mt-6 bg-cyber-detail/20 p-3 rounded border border-cyber-detail/50">
                <h4 className="text-sm font-medium text-cyber-text mb-2">Validación de Datos</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center text-green-400">
                    <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>No se detectaron valores nulos</span>
                  </div>
                  <div className="flex items-center text-green-400">
                    <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Tipos de datos consistentes</span>
                  </div>
                  <div className="flex items-center text-yellow-400">
                    <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span>Se detectaron 3 valores atípicos potenciales</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'settings' && (
            <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-cyber-text">Configuración del Dataset</h3>
                <button className="bg-cyber-cyan text-cyber-dark px-4 py-2 rounded text-sm hover:bg-cyber-cyan/90 transition-colors">
                  Guardar Cambios
                </button>
              </div>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-cyber-text mb-1">Nombre del Dataset</label>
                  <input 
                    type="text" 
                    className="w-full px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                    defaultValue={dataset.name}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-cyber-text mb-1">Descripción</label>
                  <textarea 
                    className="w-full px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                    defaultValue={dataset.description}
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-cyber-text mb-1">Etiquetas</label>
                  <input 
                    type="text" 
                    className="w-full px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                    defaultValue={dataset.tags.join(', ')}
                  />
                  <p className="mt-1 text-xs text-cyber-text/60">Separa las etiquetas con comas</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-cyber-text mb-1">Permisos de Acceso</label>
                  <div className="space-y-2">
                    <div className="flex items-center">
                      <input 
                        type="radio" 
                        id="private" 
                        name="access" 
                        className="mr-2 h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail/50"
                        defaultChecked
                      />
                      <label htmlFor="private" className="text-sm text-cyber-text">
                        Privado (solo tú)
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input 
                        type="radio" 
                        id="team" 
                        name="access" 
                        className="mr-2 h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail/50"
                      />
                      <label htmlFor="team" className="text-sm text-cyber-text">
                        Equipo (todos los miembros)
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input 
                        type="radio" 
                        id="public" 
                        name="access" 
                        className="mr-2 h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail/50"
                      />
                      <label htmlFor="public" className="text-sm text-cyber-text">
                        Público (toda la organización)
                      </label>
                    </div>
                  </div>
                </div>
                
                <div className="border-t border-cyber-detail pt-6">
                  <h4 className="text-sm font-medium text-red-400 mb-4">Zona de Peligro</h4>
                  <div className="flex space-x-4">
                    <button className="bg-red-700/30 text-red-400 px-4 py-2 rounded hover:bg-red-700/50 transition-colors">
                      Eliminar Dataset
                    </button>
                    <button className="bg-cyber-detail/30 text-cyber-text/70 px-4 py-2 rounded hover:bg-cyber-detail/50 transition-colors">
                      Archivar Dataset
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Panel lateral (1/4 del ancho) */}
        <div className="space-y-6">
          {/* Información del Dataset */}
          <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
            <h3 className="text-sm font-semibold text-cyber-text flex items-center mb-4">
              <Info size={16} className="mr-1 text-cyber-cyan" />
              Información del Dataset
            </h3>
            
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-cyber-text/70">Tipo:</span>
                <span className="text-cyber-text font-medium">{dataset.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyber-text/70">Formato:</span>
                <span className="text-cyber-text font-medium">{dataset.format}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyber-text/70">Filas:</span>
                <span className="text-cyber-text font-medium">{dataset.rows.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyber-text/70">Columnas:</span>
                <span className="text-cyber-text font-medium">{dataset.columns}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyber-text/70">Creado:</span>
                <span className="text-cyber-text font-medium">{dataset.createdAt}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyber-text/70">Actualizado:</span>
                <span className="text-cyber-text font-medium">{dataset.updatedAt}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyber-text/70">Propietario:</span>
                <span className="text-cyber-text font-medium">{dataset.owner}</span>
              </div>
            </div>
          </div>
          
          {/* Etiquetas */}
          <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
            <h3 className="text-sm font-semibold text-cyber-text flex items-center mb-3">
              <Tag size={16} className="mr-1 text-cyber-cyan" />
              Etiquetas
            </h3>
            
            <div className="flex flex-wrap gap-2">
              {dataset.tags.map((tag, index) => (
                <span 
                  key={index}
                  className="px-2 py-1 bg-cyber-detail/40 text-cyber-text text-xs rounded-full"
                >
                  {tag}
                </span>
              ))}
              <button className="px-2 py-1 border border-cyber-detail/40 text-cyber-text/70 text-xs rounded-full hover:bg-cyber-detail/30">
                + Añadir
              </button>
            </div>
          </div>
          
          {/* Historia de actividad */}
          <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
            <h3 className="text-sm font-semibold text-cyber-text flex items-center mb-3">
              <Calendar size={16} className="mr-1 text-cyber-cyan" />
              Actividad Reciente
            </h3>
            
            <div className="space-y-3">
              <div className="text-xs border-l-2 border-cyber-cyan pl-3 pb-3">
                <div className="text-cyber-text font-medium">Dataset actualizado</div>
                <div className="text-cyber-text/70">01 Mar, 2025 - 14:32</div>
              </div>
              <div className="text-xs border-l-2 border-cyber-detail/50 pl-3 pb-3">
                <div className="text-cyber-text font-medium">Visualización creada</div>
                <div className="text-cyber-text/70">28 Feb, 2025 - 10:15</div>
              </div>
              <div className="text-xs border-l-2 border-cyber-detail/50 pl-3">
                <div className="text-cyber-text font-medium">Dataset importado</div>
                <div className="text-cyber-text/70">{dataset.createdAt} - 09:45</div>
              </div>
            </div>
          </div>
          
          {/* Análisis IA */}
          <div className="bg-cyber-dark/70 backdrop-blur-sm p-4 rounded-lg border border-cyber-cyan/20 shadow-lg">
            <h3 className="text-sm font-semibold text-cyber-text flex items-center mb-3">
              <Sparkles size={16} className="mr-1 text-cyber-cyan" />
              Insights IA
            </h3>
            
            <div className="space-y-2 text-xs">
              <div className="p-2 bg-cyber-detail/20 rounded">
                <p className="text-cyber-text">Se detecta una correlación fuerte (0.85) entre las columnas X y Y.</p>
              </div>
              <div className="p-2 bg-cyber-detail/20 rounded">
                <p className="text-cyber-text">Hay una tendencia al alza del 12% en los últimos datos.</p>
              </div>
              <div className="p-2 bg-cyber-detail/20 rounded">
                <p className="text-cyber-text">Se identificaron 3 valores atípicos que podrían ser errores.</p>
              </div>
            </div>
            
            <button className="w-full mt-3 text-center text-xs text-cyber-cyan hover:underline">
              Ver análisis completo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatasetDetail;