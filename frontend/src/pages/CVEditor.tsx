import React, { useState, useEffect } from 'react';
import { FileText, Download, History, Trash2, Eye, Sparkles, ArrowRight, Zap, Target, Brain, CheckCircle } from 'lucide-react';
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
    <div className="min-h-screen bg-gray-900 pt-20">
      {/* Animated Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%239C92AC' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
          }}
        ></div>
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-4000"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center px-4 py-2 mb-6 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 backdrop-blur-sm border border-white/10 rounded-full text-white">
            <Brain className="w-4 h-4 mr-2 text-cyan-400" />
            <span className="text-sm font-medium">IA Especializada en Perú</span>
          </div>
          
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-cyan-200 to-blue-200 bg-clip-text text-transparent mb-4 flex items-center justify-center">
            <FileText className="w-12 h-12 mr-4 text-cyan-400" />
            Editor Inteligente de CV
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Mejora tu currículum con IA especializada en el mercado laboral peruano
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Section */}
          <div className="lg:col-span-2">
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white flex items-center">
                  <Target className="w-6 h-6 mr-3 text-blue-400" />
                  Tu CV Actual
                </h2>
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="flex items-center px-4 py-2 bg-white/10 border border-white/20 text-white rounded-xl hover:bg-white/20 transition-all duration-300"
                >
                  <History className="w-4 h-4 mr-2" />
                  Historial
                </button>
              </div>

              <textarea
                value={originalCV}
                onChange={(e) => setOriginalCV(e.target.value)}
                placeholder="Pega aquí el contenido de tu CV actual o escríbelo desde cero..."
                className="w-full h-96 p-6 bg-white/10 border border-white/20 rounded-2xl text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all duration-300"
              />

              {error && (
                <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                  <p className="text-red-300 text-sm">{error}</p>
                </div>
              )}

              <div className="mt-8 flex flex-col sm:flex-row gap-4">
                <button
                  onClick={handleImproveCV}
                  disabled={loading || !originalCV.trim()}
                  className="group flex items-center justify-center px-8 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105"
                >
                  {loading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Analizando con IA...
                    </div>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5 mr-2" />
                      Mejorar con IA
                      <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </button>

                {currentCV?.improved_content && (
                  <button
                    onClick={handleDownload}
                    className="flex items-center justify-center px-6 py-4 bg-white/10 border border-white/20 text-white rounded-xl hover:bg-white/20 transition-all duration-300"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Descargar CV
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Results/History Section */}
          <div className="lg:col-span-1">
            {showHistory ? (
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                  <History className="w-5 h-5 mr-2 text-purple-400" />
                  Historial de CVs
                </h3>
                {cvHistory.length === 0 ? (
                  <div className="text-center py-12">
                    <FileText className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-400">
                      No tienes CVs guardados aún
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {cvHistory.map((cv) => (
                      <div
                        key={cv.id}
                        className="bg-white/5 border border-white/10 rounded-2xl p-4 hover:bg-white/10 transition-all duration-300"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-white">
                              CV #{cv.id}
                            </p>
                            <p className="text-sm text-gray-400">
                              {new Date(cv.created_at).toLocaleDateString('es-PE')}
                            </p>
                            <span className={`text-xs px-3 py-1 rounded-full mt-2 inline-block font-medium ${
                              cv.status === 'completed' 
                                ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                                : cv.status === 'processing'
                                ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                                : 'bg-red-500/20 text-red-400 border border-red-500/30'
                            }`}>
                              {cv.status === 'completed' ? 'Completado' : 
                               cv.status === 'processing' ? 'Procesando' : 'Error'}
                            </span>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleLoadCV(cv.id)}
                              className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-all duration-300"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteCV(cv.id)}
                              className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all duration-300"
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
                  <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                      <Sparkles className="w-5 h-5 mr-2 text-yellow-400" />
                      CV Mejorado
                    </h3>
                    <div className="bg-white/10 border border-white/20 p-6 rounded-2xl max-h-96 overflow-y-auto">
                      <pre className="whitespace-pre-wrap text-sm text-gray-200 font-sans leading-relaxed">
                        {currentCV.improved_content}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Feedback */}
                {currentCV.feedback && (
                  <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                      <Zap className="w-5 h-5 mr-2 text-green-400" />
                      Retroalimentación y Sugerencias
                    </h3>
                    <div className="bg-white/10 border border-white/20 p-6 rounded-2xl">
                      <div className="whitespace-pre-wrap text-gray-200 leading-relaxed">
                        {currentCV.feedback}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                <div className="text-center py-8">
                  <div className="bg-gradient-to-r from-blue-400 to-cyan-400 p-4 rounded-2xl w-fit mx-auto mb-6 shadow-lg">
                    <FileText className="w-12 h-12 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">
                    ¿Listo para mejorar tu CV?
                  </h3>
                  <p className="text-gray-300 mb-8 leading-relaxed">
                    Ingresa tu CV en el editor y haz clic en "Mejorar con IA" para obtener una versión optimizada para el mercado peruano.
                  </p>
                  <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/20 p-6 rounded-2xl text-left">
                    <h4 className="font-bold text-cyan-400 mb-4 flex items-center">
                      <CheckCircle className="w-5 h-5 mr-2" />
                      Tips para mejores resultados:
                    </h4>
                    <ul className="text-sm text-gray-300 space-y-2">
                      <li className="flex items-center">
                        <ArrowRight className="w-4 h-4 mr-2 text-blue-400" />
                        Incluye tu experiencia laboral completa
                      </li>
                      <li className="flex items-center">
                        <ArrowRight className="w-4 h-4 mr-2 text-blue-400" />
                        Menciona tus habilidades técnicas
                      </li>
                      <li className="flex items-center">
                        <ArrowRight className="w-4 h-4 mr-2 text-blue-400" />
                        Agrega tu educación y certificaciones
                      </li>
                      <li className="flex items-center">
                        <ArrowRight className="w-4 h-4 mr-2 text-blue-400" />
                        Especifica el tipo de puesto que buscas
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CVEditor;