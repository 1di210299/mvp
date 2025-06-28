import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { MessageCircle, Crown, Play, Send, History, Trash2, Eye, Award, ArrowRight, Zap, Target, Brain, CheckCircle, Users, Mic } from 'lucide-react';
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
              Simulador de Entrevistas
            </h2>
            <p className="text-xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
              Practica entrevistas laborales con IA especializada en el mercado peruano. 
              Recibe feedback inmediato y mejora tus respuestas.
            </p>
            
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 mb-12 shadow-2xl">
              <h3 className="text-2xl font-bold text-white mb-8">Con Premium podrás:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex items-center bg-white/5 p-4 rounded-2xl">
                  <div className="bg-gradient-to-r from-green-400 to-emerald-400 p-3 rounded-xl mr-4">
                    <MessageCircle className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-gray-200 font-medium">Entrevistas simuladas ilimitadas</span>
                </div>
                <div className="flex items-center bg-white/5 p-4 rounded-2xl">
                  <div className="bg-gradient-to-r from-blue-400 to-cyan-400 p-3 rounded-xl mr-4">
                    <Award className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-gray-200 font-medium">Feedback detallado en tiempo real</span>
                </div>
                <div className="flex items-center bg-white/5 p-4 rounded-2xl">
                  <div className="bg-gradient-to-r from-purple-400 to-pink-400 p-3 rounded-xl mr-4">
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-gray-200 font-medium">Preguntas adaptadas al mercado peruano</span>
                </div>
                <div className="flex items-center bg-white/5 p-4 rounded-2xl">
                  <div className="bg-gradient-to-r from-yellow-400 to-orange-400 p-3 rounded-xl mr-4">
                    <Zap className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-gray-200 font-medium">Mejora continua de respuestas</span>
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
          <div className="inline-flex items-center px-4 py-2 mb-6 bg-gradient-to-r from-green-500/20 to-emerald-500/20 backdrop-blur-sm border border-white/10 rounded-full text-white">
            <Brain className="w-4 h-4 mr-2 text-green-400" />
            <span className="text-sm font-medium">IA para Entrevistas Premium</span>
          </div>
          
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-green-200 to-emerald-200 bg-clip-text text-transparent mb-4 flex items-center justify-center">
            <MessageCircle className="w-12 h-12 mr-4 text-green-400" />
            Simulador de Entrevistas
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Practica entrevistas laborales con IA especializada en el mercado peruano
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Interview Section */}
          <div className="lg:col-span-3">
            {!currentInterview ? (
              // Start Interview Form
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                <div className="text-center mb-8">
                  <div className="bg-gradient-to-r from-green-400 to-emerald-400 p-6 rounded-3xl w-fit mx-auto mb-6 shadow-lg">
                    <Play className="w-12 h-12 text-white" />
                  </div>
                  <h2 className="text-3xl font-bold text-white mb-4">
                    Iniciar Nueva Entrevista
                  </h2>
                  <p className="text-gray-300 text-lg">
                    Prepárate para tu próxima entrevista laboral con IA especializada
                  </p>
                </div>

                <form onSubmit={handleStartInterview} className="max-w-md mx-auto space-y-6">
                  <div>
                    <label htmlFor="jobTitle" className="block text-sm font-medium text-gray-300 mb-2">
                      Puesto de trabajo *
                    </label>
                    <input
                      type="text"
                      id="jobTitle"
                      value={startForm.jobTitle}
                      onChange={(e) => setStartForm({...startForm, jobTitle: e.target.value})}
                      placeholder="ej. Analista de Sistemas"
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-400 focus:border-transparent transition-all duration-300"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="companyName" className="block text-sm font-medium text-gray-300 mb-2">
                      Empresa (opcional)
                    </label>
                    <input
                      type="text"
                      id="companyName"
                      value={startForm.companyName}
                      onChange={(e) => setStartForm({...startForm, companyName: e.target.value})}
                      placeholder="ej. Banco de Crédito del Perú"
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-400 focus:border-transparent transition-all duration-300"
                    />
                  </div>

                  {error && (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                      <p className="text-red-300 text-sm">{error}</p>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="group w-full flex items-center justify-center px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-green-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105"
                  >
                    {loading ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Iniciando entrevista...
                      </div>
                    ) : (
                      <>
                        <Play className="w-5 h-5 mr-2" />
                        Comenzar Entrevista
                        <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                      </>
                    )}
                  </button>
                </form>

                <div className="mt-8 bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 p-6 rounded-2xl max-w-md mx-auto">
                  <h4 className="font-bold text-green-400 mb-4 flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    Tips para una buena entrevista:
                  </h4>
                  <ul className="text-sm text-gray-300 space-y-2">
                    <li className="flex items-center">
                      <ArrowRight className="w-4 h-4 mr-2 text-green-400" />
                      Responde con ejemplos específicos de tu experiencia
                    </li>
                    <li className="flex items-center">
                      <ArrowRight className="w-4 h-4 mr-2 text-green-400" />
                      Mantén un tono profesional pero natural
                    </li>
                    <li className="flex items-center">
                      <ArrowRight className="w-4 h-4 mr-2 text-green-400" />
                      Muestra conocimiento sobre la empresa y el mercado peruano
                    </li>
                    <li className="flex items-center">
                      <ArrowRight className="w-4 h-4 mr-2 text-green-400" />
                      Haz preguntas inteligentes sobre el puesto
                    </li>
                  </ul>
                </div>
              </div>
            ) : (
              // Active Interview
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                <div className="flex items-center justify-between mb-8">
                  <div>
                    <h2 className="text-2xl font-bold text-white flex items-center">
                      <Users className="w-6 h-6 mr-3 text-green-400" />
                      Entrevista: {currentInterview.job_title}
                    </h2>
                    {currentInterview.company_name && (
                      <p className="text-gray-300 mt-1">{currentInterview.company_name}</p>
                    )}
                  </div>
                  <button
                    onClick={handleFinishInterview}
                    className="px-4 py-2 bg-red-500/20 border border-red-500/30 text-red-300 rounded-xl hover:bg-red-500/30 transition-all duration-300"
                  >
                    Finalizar Entrevista
                  </button>
                </div>

                {/* Chat History */}
                <div className="bg-white/10 border border-white/20 rounded-2xl p-6 mb-8 max-h-96 overflow-y-auto">
                  {chatHistory.map((message, index) => (
                    <div key={index} className="mb-6 last:mb-0">
                      {message.type === 'question' && (
                        <div className="bg-blue-500/20 border border-blue-500/30 p-4 rounded-2xl">
                          <div className="flex items-start">
                            <div className="bg-gradient-to-r from-blue-400 to-cyan-400 p-2 rounded-xl mr-3">
                              <MessageCircle className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <p className="font-semibold text-blue-300 text-sm mb-1">Entrevistador IA</p>
                              <p className="text-white leading-relaxed">{message.content}</p>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {message.type === 'response' && (
                        <div className="bg-green-500/20 border border-green-500/30 p-4 rounded-2xl ml-8">
                          <div className="flex items-start">
                            <div className="bg-gradient-to-r from-green-400 to-emerald-400 p-2 rounded-xl mr-3">
                              <Users className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <p className="font-semibold text-green-300 text-sm mb-1">Tu respuesta</p>
                              <p className="text-white leading-relaxed">{message.content}</p>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {message.type === 'feedback' && (
                        <div className="bg-yellow-500/20 border border-yellow-500/30 p-4 rounded-2xl ml-4 mr-4">
                          <div className="flex items-start">
                            <div className="bg-gradient-to-r from-yellow-400 to-orange-400 p-2 rounded-xl mr-3">
                              <Award className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <p className="font-semibold text-yellow-300 text-sm mb-1">Feedback IA</p>
                              <p className="text-white leading-relaxed">{message.content}</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Response Input */}
                <div className="flex gap-4">
                  <input
                    type="text"
                    value={userResponse}
                    onChange={(e) => setUserResponse(e.target.value)}
                    placeholder="Escribe tu respuesta aquí..."
                    className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-400 focus:border-transparent transition-all duration-300"
                    onKeyPress={(e) => e.key === 'Enter' && !loading && handleSendResponse()}
                  />
                  <button
                    onClick={handleSendResponse}
                    disabled={loading || !userResponse.trim()}
                    className="flex items-center px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl hover:shadow-lg hover:shadow-green-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
                  >
                    {loading ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    ) : (
                      <Send className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-white">
                  {showHistory ? 'Historial' : 'Estadísticas'}
                </h3>
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="p-2 text-gray-400 hover:text-green-400 hover:bg-green-500/10 rounded-lg transition-all duration-300"
                >
                  <History className="w-5 h-5" />
                </button>
              </div>

              {showHistory ? (
                <div>
                  {interviewHistory.length === 0 ? (
                    <div className="text-center py-12">
                      <MessageCircle className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                      <p className="text-gray-400 text-sm">
                        No tienes entrevistas guardadas aún
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {interviewHistory.slice(0, 5).map((interview) => (
                        <div
                          key={interview.id}
                          className="bg-white/5 border border-white/10 rounded-2xl p-3 hover:bg-white/10 transition-all duration-300"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <p className="text-sm font-medium text-white truncate">
                                {interview.job_title}
                              </p>
                              <p className="text-xs text-gray-400">
                                {new Date(interview.created_at).toLocaleDateString('es-PE')}
                              </p>
                              <span className={`text-xs px-2 py-1 rounded-full mt-2 inline-block font-medium ${
                                interview.status === 'completed' 
                                  ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                                  : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                              }`}>
                                {interview.status === 'completed' ? 'Completada' : 'Activa'}
                              </span>
                            </div>
                            <div className="flex space-x-1">
                              <button
                                onClick={() => handleLoadInterview(interview.id)}
                                className="p-2 text-green-400 hover:text-green-300 hover:bg-green-500/10 rounded-lg transition-all duration-300"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteInterview(interview.id)}
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
              ) : (
                <div className="space-y-6">
                  <div className="text-center bg-white/5 p-4 rounded-2xl">
                    <div className="text-3xl font-bold text-transparent bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text mb-1">
                      {interviewHistory.length}
                    </div>
                    <div className="text-gray-300 text-sm">Entrevistas realizadas</div>
                  </div>
                  
                  <div className="text-center bg-white/5 p-4 rounded-2xl">
                    <div className="text-3xl font-bold text-transparent bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text mb-1">
                      {interviewHistory.filter(i => i.status === 'completed').length}
                    </div>
                    <div className="text-gray-300 text-sm">Completadas</div>
                  </div>

                  <div className="border-t border-white/10 pt-6">
                    <h4 className="font-bold text-green-400 mb-4 flex items-center">
                      <Target className="w-4 h-4 mr-2" />
                      Próximos pasos:
                    </h4>
                    <ul className="text-xs text-gray-300 space-y-2">
                      <li className="flex items-center">
                        <ArrowRight className="w-3 h-3 mr-2 text-green-400" />
                        Practica respuestas específicas
                      </li>
                      <li className="flex items-center">
                        <ArrowRight className="w-3 h-3 mr-2 text-green-400" />
                        Investiga sobre la empresa
                      </li>
                      <li className="flex items-center">
                        <ArrowRight className="w-3 h-3 mr-2 text-green-400" />
                        Prepara preguntas inteligentes
                      </li>
                      <li className="flex items-center">
                        <ArrowRight className="w-3 h-3 mr-2 text-green-400" />
                        Revisa tu CV actualizado
                      </li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewSimulator;