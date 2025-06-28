import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { Mail, Crown, Download, History, Trash2, Eye, Sparkles, ArrowRight, Zap, Target, Brain, CheckCircle, Building, Briefcase } from 'lucide-react';
import { coverLetterService, CoverLetter } from '../services/coverLetterService';

const CoverLetterGenerator: React.FC = () => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    jobTitle: '',
    companyName: '',
    jobDescription: '',
    userExperience: ''
  });
  const [currentLetter, setCurrentLetter] = useState<CoverLetter | null>(null);
  const [letterHistory, setLetterHistory] = useState<CoverLetter[]>([]);
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user?.is_premium) {
      fetchLetterHistory();
    }
  }, [user]);

  const fetchLetterHistory = async () => {
    try {
      const history = await coverLetterService.getCoverLetterHistory();
      setLetterHistory(history);
    } catch (error) {
      console.error('Error fetching letter history:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.jobTitle.trim() || !formData.companyName.trim()) {
      setError('Por favor, completa al menos el puesto y la empresa');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Convert camelCase to snake_case for API
      const requestData = {
        job_title: formData.jobTitle,
        company_name: formData.companyName,
        job_description: formData.jobDescription,
        user_experience: formData.userExperience
      };
      const letter = await coverLetterService.generateCoverLetter(requestData);
      setCurrentLetter(letter);
      fetchLetterHistory();
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('Esta función requiere una suscripción Premium. Actualiza tu plan para continuar.');
      } else {
        setError(err.response?.data?.detail || 'Error al generar la carta de presentación');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleDeleteLetter = async (id: number) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta carta?')) {
      try {
        await coverLetterService.deleteCoverLetter(id);
        fetchLetterHistory();
        if (currentLetter?.id === id) {
          setCurrentLetter(null);
        }
      } catch (error) {
        console.error('Error deleting letter:', error);
      }
    }
  };

  const handleLoadLetter = async (id: number) => {
    try {
      const letter = await coverLetterService.getCoverLetter(id);
      setCurrentLetter(letter);
      setFormData({
        jobTitle: letter.job_title,
        companyName: letter.company_name,
        jobDescription: letter.job_description || '',
        userExperience: letter.user_experience || ''
      });
      setShowHistory(false);
    } catch (error) {
      console.error('Error loading letter:', error);
    }
  };

  const handleDownload = () => {
    if (!currentLetter?.generated_content) return;
    
    const element = document.createElement('a');
    const file = new Blob([currentLetter.generated_content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `carta_${currentLetter.company_name}_${currentLetter.job_title}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  if (!user?.is_premium) {
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

        <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="bg-gradient-to-r from-yellow-400 to-yellow-500 p-6 rounded-3xl w-fit mx-auto mb-8 shadow-2xl">
              <Crown className="w-16 h-16 text-gray-900" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-yellow-200 to-orange-200 bg-clip-text text-transparent mb-6">
              Función Premium
            </h1>
            <h2 className="text-3xl font-bold text-white mb-6">
              Generador de Cartas de Presentación
            </h2>
            <p className="text-xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
              Crea cartas de presentación personalizadas y profesionales para cada puesto y empresa 
              con ayuda de IA especializada en el mercado laboral peruano.
            </p>
            
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 mb-12 shadow-2xl">
              <h3 className="text-2xl font-bold text-white mb-8">Con Premium podrás:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex items-center bg-white/5 p-4 rounded-2xl">
                  <div className="bg-gradient-to-r from-purple-400 to-pink-400 p-3 rounded-xl mr-4">
                    <Sparkles className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-gray-200 font-medium">Cartas personalizadas por puesto</span>
                </div>
                <div className="flex items-center bg-white/5 p-4 rounded-2xl">
                  <div className="bg-gradient-to-r from-blue-400 to-cyan-400 p-3 rounded-xl mr-4">
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-gray-200 font-medium">Tono profesional peruano</span>
                </div>
                <div className="flex items-center bg-white/5 p-4 rounded-2xl">
                  <div className="bg-gradient-to-r from-green-400 to-emerald-400 p-3 rounded-xl mr-4">
                    <Building className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-gray-200 font-medium">Adaptación a empresas locales</span>
                </div>
                <div className="flex items-center bg-white/5 p-4 rounded-2xl">
                  <div className="bg-gradient-to-r from-yellow-400 to-orange-400 p-3 rounded-xl mr-4">
                    <Zap className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-gray-200 font-medium">Generación ilimitada</span>
                </div>
              </div>
            </div>

            <Link
              to="/pricing"
              className="group inline-flex items-center px-10 py-5 bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 rounded-2xl text-xl font-bold hover:shadow-lg hover:shadow-yellow-500/25 transition-all duration-300 transform hover:scale-105"
            >
              <Crown className="w-6 h-6 mr-3" />
              Actualizar a Premium
              <ArrowRight className="w-6 h-6 ml-3 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

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
          <div className="inline-flex items-center px-4 py-2 mb-6 bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-white/10 rounded-full text-white">
            <Brain className="w-4 h-4 mr-2 text-purple-400" />
            <span className="text-sm font-medium">IA Premium para Cartas</span>
          </div>
          
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent mb-4 flex items-center justify-center">
            <Mail className="w-12 h-12 mr-4 text-purple-400" />
            Generador de Cartas
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Crea cartas personalizadas para cada puesto con IA especializada en el mercado peruano
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Form Section */}
          <div className="lg:col-span-2">
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold text-white flex items-center">
                  <Briefcase className="w-6 h-6 mr-3 text-purple-400" />
                  Información del Puesto
                </h2>
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="flex items-center px-4 py-2 bg-white/10 border border-white/20 text-white rounded-xl hover:bg-white/20 transition-all duration-300"
                >
                  <History className="w-4 h-4 mr-2" />
                  Historial
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="jobTitle" className="block text-sm font-medium text-gray-300 mb-2">
                      Puesto de trabajo *
                    </label>
                    <input
                      type="text"
                      id="jobTitle"
                      name="jobTitle"
                      value={formData.jobTitle}
                      onChange={handleChange}
                      placeholder="ej. Desarrollador Frontend"
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-300"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="companyName" className="block text-sm font-medium text-gray-300 mb-2">
                      Empresa *
                    </label>
                    <input
                      type="text"
                      id="companyName"
                      name="companyName"
                      value={formData.companyName}
                      onChange={handleChange}
                      placeholder="ej. BCP, Interbank, Rimac"
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-300"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="jobDescription" className="block text-sm font-medium text-gray-300 mb-2">
                    Descripción del puesto (opcional)
                  </label>
                  <textarea
                    id="jobDescription"
                    name="jobDescription"
                    value={formData.jobDescription}
                    onChange={handleChange}
                    placeholder="Pega aquí la descripción del puesto para una carta más personalizada..."
                    rows={4}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-300 resize-none"
                  />
                </div>

                <div>
                  <label htmlFor="userExperience" className="block text-sm font-medium text-gray-300 mb-2">
                    Tu experiencia relevante (opcional)
                  </label>
                  <textarea
                    id="userExperience"
                    name="userExperience"
                    value={formData.userExperience}
                    onChange={handleChange}
                    placeholder="Describe brevemente tu experiencia relevante para este puesto..."
                    rows={3}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-300 resize-none"
                  />
                </div>

                {error && (
                  <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                    <p className="text-red-300 text-sm">{error}</p>
                  </div>
                )}

                <div className="flex flex-col sm:flex-row gap-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="group flex items-center justify-center px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-purple-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105"
                  >
                    {loading ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Generando carta...
                      </div>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5 mr-2" />
                        Generar Carta
                        <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                      </>
                    )}
                  </button>

                  {currentLetter?.generated_content && (
                    <button
                      type="button"
                      onClick={handleDownload}
                      className="flex items-center justify-center px-6 py-4 bg-white/10 border border-white/20 text-white rounded-xl hover:bg-white/20 transition-all duration-300"
                    >
                      <Download className="w-5 h-5 mr-2" />
                      Descargar
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>

          {/* Results/History Section */}
          <div className="lg:col-span-1">
            {showHistory ? (
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                  <History className="w-5 h-5 mr-2 text-purple-400" />
                  Historial de Cartas
                </h3>
                {letterHistory.length === 0 ? (
                  <div className="text-center py-12">
                    <Mail className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-400">
                      No tienes cartas guardadas aún
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {letterHistory.map((letter) => (
                      <div
                        key={letter.id}
                        className="bg-white/5 border border-white/10 rounded-2xl p-4 hover:bg-white/10 transition-all duration-300"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-white text-sm">
                              {letter.job_title}
                            </p>
                            <p className="text-sm text-purple-300">
                              {letter.company_name}
                            </p>
                            <p className="text-xs text-gray-400">
                              {new Date(letter.created_at).toLocaleDateString('es-PE')}
                            </p>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleLoadLetter(letter.id)}
                              className="p-2 text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 rounded-lg transition-all duration-300"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteLetter(letter.id)}
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
            ) : currentLetter?.generated_content ? (
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                  <Sparkles className="w-5 h-5 mr-2 text-yellow-400" />
                  Carta Generada
                </h3>
                <div className="bg-white/10 border border-white/20 p-6 rounded-2xl max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm text-gray-200 font-sans leading-relaxed">
                    {currentLetter.generated_content}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                <div className="text-center py-8">
                  <div className="bg-gradient-to-r from-purple-400 to-pink-400 p-4 rounded-2xl w-fit mx-auto mb-6 shadow-lg">
                    <Mail className="w-12 h-12 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">
                    ¿Listo para crear tu carta?
                  </h3>
                  <p className="text-gray-300 mb-8 leading-relaxed">
                    Completa la información del puesto y haz clic en "Generar Carta" para obtener una carta personalizada.
                  </p>
                  <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 p-6 rounded-2xl text-left">
                    <h4 className="font-bold text-purple-400 mb-4 flex items-center">
                      <CheckCircle className="w-5 h-5 mr-2" />
                      Tips para mejores cartas:
                    </h4>
                    <ul className="text-sm text-gray-300 space-y-2">
                      <li className="flex items-center">
                        <ArrowRight className="w-4 h-4 mr-2 text-purple-400" />
                        Incluye el nombre exacto del puesto
                      </li>
                      <li className="flex items-center">
                        <ArrowRight className="w-4 h-4 mr-2 text-purple-400" />
                        Menciona la empresa específica
                      </li>
                      <li className="flex items-center">
                        <ArrowRight className="w-4 h-4 mr-2 text-purple-400" />
                        Agrega la descripción del trabajo si la tienes
                      </li>
                      <li className="flex items-center">
                        <ArrowRight className="w-4 h-4 mr-2 text-purple-400" />
                        Describe tu experiencia más relevante
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

export default CoverLetterGenerator;