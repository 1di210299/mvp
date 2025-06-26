import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { MessageCircle, Crown, Play, Send, History, Trash2, Eye, Award } from 'lucide-react';
import { interviewService, Interview, InterviewChat } from '../services/interviewService';

const InterviewSimulator: React.FC = () => {
  const { user } = useAuth();
  const [currentInterview, setCurrentInterview] = useState<Interview | null>(null);
  const [interviewHistory, setInterviewHistory] = useState<Interview[]>([]);
  const [userResponse, setUserResponse] = useState('');
  const [chatHistory, setChatHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [startForm, setStartForm] = useState({
    jobTitle: '',
    companyName: ''
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (user?.is_premium) {
      fetchInterviewHistory();
    }
  }, [user]);

  const fetchInterviewHistory = async () => {
    try {
      const history = await interviewService.getInterviewHistory();
      setInterviewHistory(history);
    } catch (error) {
      console.error('Error fetching interview history:', error);
    }
  };

  const handleStartInterview = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!startForm.jobTitle.trim()) {
      setError('Por favor, ingresa el puesto de trabajo');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Convert camelCase to snake_case for API
      const requestData = {
        job_title: startForm.jobTitle,
        company_name: startForm.companyName
      };
      const interview = await interviewService.startInterview(requestData);
      setCurrentInterview(interview);
      setChatHistory([{
        type: 'question',
        content: interview.current_question,
        timestamp: new Date()
      }]);
      fetchInterviewHistory();
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('Esta función requiere una suscripción Premium. Actualiza tu plan para continuar.');
      } else {
        setError(err.response?.data?.detail || 'Error al iniciar la entrevista');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSendResponse = async () => {
    if (!userResponse.trim() || !currentInterview) return;

    setLoading(true);
    
    // Agregar respuesta del usuario al chat
    const newUserMessage = {
      type: 'response',
      content: userResponse,
      timestamp: new Date()
    };
    
    setChatHistory(prev => [...prev, newUserMessage]);
    const currentResponse = userResponse;
    setUserResponse('');

    try {
      const chatResponse = await interviewService.respondToInterview(
        currentInterview.id,
        currentResponse
      );

      // Agregar feedback y siguiente pregunta al chat
      const newMessages: Array<{type: string; content: string; timestamp: Date}> = [];
      
      if (chatResponse.feedback) {
        newMessages.push({
          type: 'feedback',
          content: chatResponse.feedback,
          timestamp: new Date()
        });
      }

      if (chatResponse.question) {
        newMessages.push({
          type: 'question',
          content: chatResponse.question,
          timestamp: new Date()
        });
      }

      setChatHistory(prev => [...prev, ...newMessages]);
    } catch (error) {
      console.error('Error sending response:', error);
      setError('Error al procesar la respuesta');
    } finally {
      setLoading(false);
    }
  };

  const handleFinishInterview = async () => {
    if (!currentInterview) return;

    try {
      await interviewService.finishInterview(currentInterview.id);
      setCurrentInterview(null);
      setChatHistory([]);
      fetchInterviewHistory();
    } catch (error) {
      console.error('Error finishing interview:', error);
    }
  };

  const handleDeleteInterview = async (id: number) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta entrevista?')) {
      try {
        await interviewService.deleteInterview(id);
        fetchInterviewHistory();
        if (currentInterview?.id === id) {
          setCurrentInterview(null);
          setChatHistory([]);
        }
      } catch (error) {
        console.error('Error deleting interview:', error);
      }
    }
  };

  const handleLoadInterview = async (id: number) => {
    try {
      const interview = await interviewService.getInterview(id);
      setCurrentInterview(interview);
      setStartForm({
        jobTitle: interview.job_title,
        companyName: interview.company_name || ''
      });
      
      // Reconstruir historial básico
      setChatHistory([{
        type: 'question',
        content: interview.current_question || 'Entrevista cargada',
        timestamp: new Date(interview.created_at)
      }]);
      
      setShowHistory(false);
    } catch (error) {
      console.error('Error loading interview:', error);
    }
  };

  if (!user?.is_premium) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center py-16">
          <Crown className="w-24 h-24 text-yellow-500 mx-auto mb-6" />
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Función Premium: Simulador de Entrevistas
          </h1>
          <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
            Practica entrevistas laborales con IA especializada en el mercado peruano. 
            Recibe feedback inmediato y mejora tus respuestas.
          </p>
          
          <div className="bg-white rounded-lg shadow-md p-8 mb-8 max-w-2xl mx-auto">
            <h3 className="text-xl font-semibold mb-4">Con Premium podrás:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="flex items-start">
                <MessageCircle className="w-5 h-5 text-green-500 mr-2 mt-0.5" />
                <span className="text-gray-700">Entrevistas simuladas ilimitadas</span>
              </div>
              <div className="flex items-start">
                <Award className="w-5 h-5 text-green-500 mr-2 mt-0.5" />
                <span className="text-gray-700">Feedback detallado en tiempo real</span>
              </div>
              <div className="flex items-start">
                <MessageCircle className="w-5 h-5 text-green-500 mr-2 mt-0.5" />
                <span className="text-gray-700">Preguntas adaptadas al mercado peruano</span>
              </div>
              <div className="flex items-start">
                <Award className="w-5 h-5 text-green-500 mr-2 mt-0.5" />
                <span className="text-gray-700">Mejora continua de respuestas</span>
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
          <MessageCircle className="w-8 h-8 mr-3 text-green-600" />
          Simulador de Entrevistas
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          Practica entrevistas laborales con IA especializada en el mercado peruano
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Interview Section */}
        <div className="lg:col-span-3">
          {!currentInterview ? (
            // Start Interview Form
            <div className="bg-white rounded-lg shadow-md p-8">
              <div className="text-center mb-8">
                <Play className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Iniciar Nueva Entrevista
                </h2>
                <p className="text-gray-600">
                  Prepárate para tu próxima entrevista laboral con IA especializada
                </p>
              </div>

              <form onSubmit={handleStartInterview} className="max-w-md mx-auto space-y-6">
                <div>
                  <label htmlFor="jobTitle" className="block text-sm font-medium text-gray-700 mb-2">
                    Puesto de trabajo *
                  </label>
                  <input
                    type="text"
                    id="jobTitle"
                    value={startForm.jobTitle}
                    onChange={(e) => setStartForm({...startForm, jobTitle: e.target.value})}
                    placeholder="ej. Analista de Sistemas"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 mb-2">
                    Empresa (opcional)
                  </label>
                  <input
                    type="text"
                    id="companyName"
                    value={startForm.companyName}
                    onChange={(e) => setStartForm({...startForm, companyName: e.target.value})}
                    placeholder="ej. Banco de Crédito del Perú"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>

                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-700 text-sm">{error}</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <Play className="w-4 h-4 mr-2" />
                  )}
                  {loading ? 'Iniciando...' : 'Comenzar Entrevista'}
                </button>
              </form>

              <div className="mt-8 bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">💡 Tips para una buena entrevista:</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• Responde con ejemplos específicos de tu experiencia</li>
                  <li>• Mantén un tono profesional pero natural</li>
                  <li>• Muestra conocimiento sobre la empresa y el mercado peruano</li>
                  <li>• Haz preguntas inteligentes sobre el puesto</li>
                </ul>
              </div>
            </div>
          ) : (
            // Active Interview
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    Entrevista: {currentInterview.job_title}
                  </h2>
                  {currentInterview.company_name && (
                    <p className="text-gray-600">{currentInterview.company_name}</p>
                  )}
                </div>
                <button
                  onClick={handleFinishInterview}
                  className="px-4 py-2 text-red-600 hover:text-red-800 transition-colors"
                >
                  Finalizar Entrevista
                </button>
              </div>

              {/* Chat History */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6 max-h-96 overflow-y-auto">
                {chatHistory.map((message, index) => (
                  <div key={index} className="mb-4 last:mb-0">
                    {message.type === 'question' && (
                      <div className="bg-blue-100 p-3 rounded-lg">
                        <div className="flex items-start">
                          <MessageCircle className="w-5 h-5 text-blue-600 mr-2 mt-0.5" />
                          <div>
                            <p className="font-medium text-blue-900 text-sm">Entrevistador</p>
                            <p className="text-blue-800">{message.content}</p>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {message.type === 'response' && (
                      <div className="bg-green-100 p-3 rounded-lg ml-8">
                        <div className="flex items-start">
                          <div className="bg-green-600 text-white rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">
                            <span className="text-xs">Tú</span>
                          </div>
                          <div>
                            <p className="font-medium text-green-900 text-sm">Tu respuesta</p>
                            <p className="text-green-800">{message.content}</p>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {message.type === 'feedback' && (
                      <div className="bg-yellow-100 p-3 rounded-lg ml-4 mr-4">
                        <div className="flex items-start">
                          <Award className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
                          <div>
                            <p className="font-medium text-yellow-900 text-sm">Feedback</p>
                            <p className="text-yellow-800">{message.content}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Response Input */}
              <div className="flex space-x-4">
                <input
                  type="text"
                  value={userResponse}
                  onChange={(e) => setUserResponse(e.target.value)}
                  placeholder="Escribe tu respuesta aquí..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  onKeyPress={(e) => e.key === 'Enter' && !loading && handleSendResponse()}
                />
                <button
                  onClick={handleSendResponse}
                  disabled={loading || !userResponse.trim()}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {showHistory ? 'Historial' : 'Estadísticas'}
              </h3>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-gray-600 hover:text-green-600 transition-colors"
              >
                <History className="w-4 h-4" />
              </button>
            </div>

            {showHistory ? (
              <div>
                {interviewHistory.length === 0 ? (
                  <p className="text-gray-500 text-center py-8 text-sm">
                    No tienes entrevistas guardadas aún
                  </p>
                ) : (
                  <div className="space-y-3">
                    {interviewHistory.slice(0, 5).map((interview) => (
                      <div
                        key={interview.id}
                        className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {interview.job_title}
                            </p>
                            <p className="text-xs text-gray-500">
                              {new Date(interview.created_at).toLocaleDateString('es-PE')}
                            </p>
                            <p className={`text-xs px-2 py-1 rounded-full mt-1 inline-block ${
                              interview.status === 'completed' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {interview.status === 'completed' ? 'Completada' : 'Activa'}
                            </p>
                          </div>
                          <div className="flex space-x-1">
                            <button
                              onClick={() => handleLoadInterview(interview.id)}
                              className="text-green-600 hover:text-green-800"
                            >
                              <Eye className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => handleDeleteInterview(interview.id)}
                              className="text-red-600 hover:text-red-800"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{interviewHistory.length}</div>
                  <div className="text-gray-600 text-sm">Entrevistas realizadas</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {interviewHistory.filter(i => i.status === 'completed').length}
                  </div>
                  <div className="text-gray-600 text-sm">Completadas</div>
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-medium text-gray-900 mb-2 text-sm">Próximos pasos:</h4>
                  <ul className="text-xs text-gray-600 space-y-1">
                    <li>• Practica respuestas específicas</li>
                    <li>• Investiga sobre la empresa</li>
                    <li>• Prepara preguntas inteligentes</li>
                    <li>• Revisa tu CV actualizado</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewSimulator;