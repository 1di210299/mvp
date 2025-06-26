import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { Mail, Crown, Download, History, Trash2, Eye, Sparkles } from 'lucide-react';
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
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center py-16">
          <Crown className="w-24 h-24 text-yellow-500 mx-auto mb-6" />
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Función Premium: Generador de Cartas de Presentación
          </h1>
          <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
            Crea cartas de presentación personalizadas y profesionales para cada puesto y empresa 
            con ayuda de IA especializada en el mercado laboral peruano.
          </p>
          
          <div className="bg-white rounded-lg shadow-md p-8 mb-8 max-w-2xl mx-auto">
            <h3 className="text-xl font-semibold mb-4">Con Premium podrás:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="flex items-start">
                <Sparkles className="w-5 h-5 text-yellow-500 mr-2 mt-0.5" />
                <span className="text-gray-700">Cartas personalizadas por puesto</span>
              </div>
              <div className="flex items-start">
                <Sparkles className="w-5 h-5 text-yellow-500 mr-2 mt-0.5" />
                <span className="text-gray-700">Tono profesional peruano</span>
              </div>
              <div className="flex items-start">
                <Sparkles className="w-5 h-5 text-yellow-500 mr-2 mt-0.5" />
                <span className="text-gray-700">Adaptación a empresas locales</span>
              </div>
              <div className="flex items-start">
                <Sparkles className="w-5 h-5 text-yellow-500 mr-2 mt-0.5" />
                <span className="text-gray-700">Generación ilimitada</span>
              </div>
            </div>
          </div>

          <Link
            to="/pricing"
            className="bg-yellow-500 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-yellow-600 transition-colors inline-flex items-center"
          >
            <Crown className="w-5 h-5 mr-2" />
            Actualizar a Premium
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Mail className="w-8 h-8 mr-3 text-purple-600" />
          Generador de Cartas de Presentación
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          Crea cartas personalizadas para cada puesto con IA especializada en el mercado peruano
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form Section */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Información del Puesto</h2>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="flex items-center text-gray-600 hover:text-purple-600 transition-colors"
              >
                <History className="w-4 h-4 mr-1" />
                Historial
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="jobTitle" className="block text-sm font-medium text-gray-700 mb-2">
                    Puesto de trabajo *
                  </label>
                  <input
                    type="text"
                    id="jobTitle"
                    name="jobTitle"
                    value={formData.jobTitle}
                    onChange={handleChange}
                    placeholder="ej. Desarrollador Frontend"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 mb-2">
                    Empresa *
                  </label>
                  <input
                    type="text"
                    id="companyName"
                    name="companyName"
                    value={formData.companyName}
                    onChange={handleChange}
                    placeholder="ej. BCP, Interbank, Rimac"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label htmlFor="jobDescription" className="block text-sm font-medium text-gray-700 mb-2">
                  Descripción del puesto (opcional)
                </label>
                <textarea
                  id="jobDescription"
                  name="jobDescription"
                  value={formData.jobDescription}
                  onChange={handleChange}
                  placeholder="Pega aquí la descripción del puesto para una carta más personalizada..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>

              <div>
                <label htmlFor="userExperience" className="block text-sm font-medium text-gray-700 mb-2">
                  Tu experiencia relevante (opcional)
                </label>
                <textarea
                  id="userExperience"
                  name="userExperience"
                  value={formData.userExperience}
                  onChange={handleChange}
                  placeholder="Describe brevemente tu experiencia relevante para este puesto..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}

              <div className="flex space-x-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <Sparkles className="w-4 h-4 mr-2" />
                  )}
                  {loading ? 'Generando...' : 'Generar Carta'}
                </button>

                {currentLetter?.generated_content && (
                  <button
                    type="button"
                    onClick={handleDownload}
                    className="flex items-center px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Download className="w-4 h-4 mr-2" />
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
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Historial de Cartas</h3>
              {letterHistory.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No tienes cartas guardadas aún
                </p>
              ) : (
                <div className="space-y-3">
                  {letterHistory.map((letter) => (
                    <div
                      key={letter.id}
                      className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {letter.job_title}
                          </p>
                          <p className="text-xs text-gray-600">
                            {letter.company_name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(letter.created_at).toLocaleDateString('es-PE')}
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleLoadLetter(letter.id)}
                            className="text-purple-600 hover:text-purple-800"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteLetter(letter.id)}
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
          ) : currentLetter?.generated_content ? (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Sparkles className="w-5 h-5 mr-2 text-yellow-500" />
                Carta Generada
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                  {currentLetter.generated_content}
                </pre>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-center py-12">
                <Mail className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  ¿Listo para crear tu carta?
                </h3>
                <p className="text-gray-500 mb-6">
                  Completa la información del puesto y haz clic en "Generar Carta" para obtener una carta personalizada.
                </p>
                <div className="bg-purple-50 p-4 rounded-lg text-left">
                  <h4 className="font-medium text-purple-900 mb-2">💡 Tips para mejores cartas:</h4>
                  <ul className="text-sm text-purple-700 space-y-1">
                    <li>• Incluye el nombre exacto del puesto</li>
                    <li>• Menciona la empresa específica</li>
                    <li>• Agrega la descripción del trabajo si la tienes</li>
                    <li>• Describe tu experiencia más relevante</li>
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

export default CoverLetterGenerator;