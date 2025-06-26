import React, { useState, useEffect } from 'react';
import { FileText, Download, History, Trash2, Eye, Sparkles } from 'lucide-react';
import { cvService, CV } from '../services/cvService';

const CVEditor: React.FC = () => {
  const [originalCV, setOriginalCV] = useState('');
  const [currentCV, setCurrentCV] = useState<CV | null>(null);
  const [cvHistory, setCvHistory] = useState<CV[]>([]);
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchCVHistory();
  }, []);

  const fetchCVHistory = async () => {
    try {
      const history = await cvService.getCVHistory();
      setCvHistory(history);
    } catch (error) {
      console.error('Error fetching CV history:', error);
    }
  };

  const handleImproveCV = async () => {
    if (!originalCV.trim()) {
      setError('Por favor, ingresa el contenido de tu CV');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const improvedCV = await cvService.improveCV(originalCV);
      setCurrentCV(improvedCV);
      fetchCVHistory(); // Refresh history
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al procesar el CV');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCV = async (id: number) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este CV?')) {
      try {
        await cvService.deleteCV(id);
        fetchCVHistory();
        if (currentCV?.id === id) {
          setCurrentCV(null);
        }
      } catch (error) {
        console.error('Error deleting CV:', error);
      }
    }
  };

  const handleLoadCV = async (id: number) => {
    try {
      const cv = await cvService.getCV(id);
      setCurrentCV(cv);
      setOriginalCV(cv.original_content);
      setShowHistory(false);
    } catch (error) {
      console.error('Error loading CV:', error);
    }
  };

  const handleDownload = () => {
    if (!currentCV?.improved_content) return;
    
    const element = document.createElement('a');
    const file = new Blob([currentCV.improved_content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `cv_mejorado_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <FileText className="w-8 h-8 mr-3 text-blue-600" />
          Editor Inteligente de CV
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          Mejora tu currículum con IA especializada en el mercado laboral peruano
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Section */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Tu CV Actual</h2>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="flex items-center text-gray-600 hover:text-blue-600 transition-colors"
              >
                <History className="w-4 h-4 mr-1" />
                Historial
              </button>
            </div>

            <textarea
              value={originalCV}
              onChange={(e) => setOriginalCV(e.target.value)}
              placeholder="Pega aquí el contenido de tu CV actual o escríbelo desde cero..."
              className="w-full h-96 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            <div className="mt-6 flex space-x-4">
              <button
                onClick={handleImproveCV}
                disabled={loading || !originalCV.trim()}
                className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                {loading ? 'Mejorando...' : 'Mejorar con IA'}
              </button>

              {currentCV?.improved_content && (
                <button
                  onClick={handleDownload}
                  className="flex items-center px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Descargar
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Results/History Section */}
        <div className="lg:col-span-1">
          {showHistory ? (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Historial de CVs</h3>
              {cvHistory.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No tienes CVs guardados aún
                </p>
              ) : (
                <div className="space-y-3">
                  {cvHistory.map((cv) => (
                    <div
                      key={cv.id}
                      className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            CV #{cv.id}
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(cv.created_at).toLocaleDateString('es-PE')}
                          </p>
                          <p className={`text-xs px-2 py-1 rounded-full mt-1 inline-block ${
                            cv.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : cv.status === 'processing'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {cv.status === 'completed' ? 'Completado' : 
                             cv.status === 'processing' ? 'Procesando' : 'Error'}
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleLoadCV(cv.id)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteCV(cv.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : currentCV ? (
            <div className="space-y-6">
              {/* Improved CV */}
              {currentCV.improved_content && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <Sparkles className="w-5 h-5 mr-2 text-yellow-500" />
                    CV Mejorado
                  </h3>
                  <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                      {currentCV.improved_content}
                    </pre>
                  </div>
                </div>
              )}

              {/* Feedback */}
              {currentCV.feedback && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Retroalimentación y Sugerencias
                  </h3>
                  <div className="prose prose-sm max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700">
                      {currentCV.feedback}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-center py-12">
                <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  ¿Listo para mejorar tu CV?
                </h3>
                <p className="text-gray-500 mb-6">
                  Ingresa tu CV en el editor y haz clic en "Mejorar con IA" para obtener una versión optimizada para el mercado peruano.
                </p>
                <div className="bg-blue-50 p-4 rounded-lg text-left">
                  <h4 className="font-medium text-blue-900 mb-2">💡 Tips para mejores resultados:</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Incluye tu experiencia laboral completa</li>
                    <li>• Menciona tus habilidades técnicas</li>
                    <li>• Agrega tu educación y certificaciones</li>
                    <li>• Especifica el tipo de puesto que buscas</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CVEditor;