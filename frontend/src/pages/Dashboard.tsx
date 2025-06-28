import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { FileText, Mail, MessageCircle, Crown, TrendingUp, Star, Sparkles, ArrowRight, Target, Zap, BarChart3, BookOpen } from 'lucide-react';
import { cvService } from '../services/cvService';
import { coverLetterService } from '../services/coverLetterService';
import { interviewService } from '../services/interviewService';
import { paymentService } from '../services/paymentService';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    cvCount: 0,
    coverLetterCount: 0,
    interviewCount: 0,
  });
  const [subscriptionInfo, setSubscriptionInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [cvHistory, letterHistory, interviewHistory, subStatus] = await Promise.all([
          cvService.getCVHistory(),
          user?.is_premium ? coverLetterService.getCoverLetterHistory() : Promise.resolve([]),
          user?.is_premium ? interviewService.getInterviewHistory() : Promise.resolve([]),
          paymentService.getSubscriptionStatus(),
        ]);

        setStats({
          cvCount: cvHistory.length,
          coverLetterCount: letterHistory.length,
          interviewCount: interviewHistory.length,
        });

        setSubscriptionInfo(subStatus);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 pt-20">
        <div className="fixed inset-0 bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
        </div>
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-cyan-400 mx-auto"></div>
            <p className="text-white text-center mt-4">Cargando tu dashboard...</p>
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
        {/* Welcome Section */}
        <div className="mb-12 text-center">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-cyan-200 to-purple-200 bg-clip-text text-transparent mb-4">
            Hola, {user?.full_name}
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Tu centro de comando para transformar tu carrera profesional con inteligencia artificial
          </p>
        </div>

        {/* Premium Status */}
        {user?.is_premium ? (
          <div className="bg-gradient-to-r from-yellow-400/20 to-yellow-600/20 backdrop-blur-xl border border-yellow-400/30 rounded-3xl p-8 mb-12 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-yellow-400/10 to-yellow-600/10"></div>
            <div className="relative z-10 flex items-center">
              <div className="bg-gradient-to-r from-yellow-400 to-yellow-500 p-4 rounded-2xl shadow-lg mr-6">
                <Crown className="w-8 h-8 text-gray-900" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Cuenta Premium Activa</h2>
                <p className="text-yellow-100 flex items-center">
                  <Sparkles className="w-4 h-4 mr-2" />
                  {subscriptionInfo?.subscription_type === 'yearly' && 'Plan Anual - '}
                  {subscriptionInfo?.subscription_type === 'monthly' && 'Plan Mensual - '}
                  Acceso ilimitado a todas las funciones de IA
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 backdrop-blur-xl border border-white/20 rounded-3xl p-8 mb-12 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-cyan-500/10"></div>
            <div className="relative z-10 flex items-center justify-between">
              <div className="flex items-center">
                <div className="bg-gradient-to-r from-purple-500 to-cyan-500 p-4 rounded-2xl shadow-lg mr-6">
                  <Star className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Desbloquea tu Potencial</h2>
                  <p className="text-gray-300">
                    Accede a cartas de presentación y simulador de entrevistas con IA avanzada
                  </p>
                </div>
              </div>
              <Link
                to="/pricing"
                className="bg-gradient-to-r from-purple-500 to-cyan-500 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg hover:shadow-purple-500/25 transition-all duration-300 transform hover:scale-105 flex items-center"
              >
                Actualizar
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all duration-300 group">
            <div className="flex items-center">
              <div className="bg-gradient-to-r from-blue-400 to-blue-600 p-4 rounded-2xl shadow-lg group-hover:scale-110 transition-transform">
                <FileText className="w-8 h-8 text-white" />
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-400 uppercase tracking-wide">CVs Mejorados</p>
                <p className="text-3xl font-bold text-white">{stats.cvCount}</p>
              </div>
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all duration-300 group">
            <div className="flex items-center">
              <div className="bg-gradient-to-r from-purple-400 to-purple-600 p-4 rounded-2xl shadow-lg group-hover:scale-110 transition-transform">
                <Mail className="w-8 h-8 text-white" />
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-400 uppercase tracking-wide">Cartas Generadas</p>
                <p className="text-3xl font-bold text-white">{stats.coverLetterCount}</p>
              </div>
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all duration-300 group">
            <div className="flex items-center">
              <div className="bg-gradient-to-r from-green-400 to-green-600 p-4 rounded-2xl shadow-lg group-hover:scale-110 transition-transform">
                <MessageCircle className="w-8 h-8 text-white" />
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-400 uppercase tracking-wide">Entrevistas Practicadas</p>
                <p className="text-3xl font-bold text-white">{stats.interviewCount}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          <Link
            to="/cv-editor"
            className="group bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all duration-500 transform hover:scale-105 hover:-translate-y-2"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative z-10">
              <div className="bg-gradient-to-r from-blue-400 to-cyan-400 p-4 rounded-2xl w-fit mb-6 shadow-lg">
                <FileText className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Editor de CV</h3>
              <p className="text-gray-300 mb-6 leading-relaxed">
                Optimiza tu currículum con IA especializada en el mercado laboral peruano
              </p>
              <div className="flex items-center text-cyan-400 font-medium">
                <span>Comenzar ahora</span>
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>

          <div className="group bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all duration-500 transform hover:scale-105 hover:-translate-y-2">
            {user?.is_premium ? (
              <Link to="/cover-letter" className="block">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative z-10">
                  <div className="bg-gradient-to-r from-purple-400 to-pink-400 p-4 rounded-2xl w-fit mb-6 shadow-lg">
                    <Mail className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">Cartas de Presentación</h3>
                  <p className="text-gray-300 mb-6 leading-relaxed">
                    Genera cartas personalizadas para cada puesto y empresa peruana
                  </p>
                  <div className="flex items-center text-purple-400 font-medium">
                    <span>Crear carta</span>
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </Link>
            ) : (
              <div className="relative z-10">
                <div className="bg-gradient-to-r from-gray-400 to-gray-500 p-4 rounded-2xl w-fit mb-6 shadow-lg">
                  <Mail className="w-8 h-8 text-white" />
                </div>
                <div className="flex items-center mb-3">
                  <h3 className="text-xl font-bold text-white">Cartas de Presentación</h3>
                  <Crown className="w-5 h-5 text-yellow-400 ml-2" />
                </div>
                <p className="text-gray-400 mb-6 leading-relaxed">
                  Función premium - Genera cartas personalizadas con IA
                </p>
                <Link
                  to="/pricing"
                  className="inline-flex items-center text-yellow-400 font-medium hover:text-yellow-300 transition-colors"
                >
                  <span>Actualizar a Premium</span>
                  <Crown className="w-4 h-4 ml-2" />
                </Link>
              </div>
            )}
          </div>

          <div className="group bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all duration-500 transform hover:scale-105 hover:-translate-y-2">
            {user?.is_premium ? (
              <Link to="/interview" className="block">
                <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative z-10">
                  <div className="bg-gradient-to-r from-green-400 to-emerald-400 p-4 rounded-2xl w-fit mb-6 shadow-lg">
                    <MessageCircle className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">Simulador de Entrevistas</h3>
                  <p className="text-gray-300 mb-6 leading-relaxed">
                    Practica entrevistas laborales con feedback personalizado de IA
                  </p>
                  <div className="flex items-center text-green-400 font-medium">
                    <span>Iniciar práctica</span>
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </Link>
            ) : (
              <div className="relative z-10">
                <div className="bg-gradient-to-r from-gray-400 to-gray-500 p-4 rounded-2xl w-fit mb-6 shadow-lg">
                  <MessageCircle className="w-8 h-8 text-white" />
                </div>
                <div className="flex items-center mb-3">
                  <h3 className="text-xl font-bold text-white">Simulador de Entrevistas</h3>
                  <Crown className="w-5 h-5 text-yellow-400 ml-2" />
                </div>
                <p className="text-gray-400 mb-6 leading-relaxed">
                  Función premium - Practica entrevistas con IA avanzada
                </p>
                <Link
                  to="/pricing"
                  className="inline-flex items-center text-yellow-400 font-medium hover:text-yellow-300 transition-colors"
                >
                  <span>Actualizar a Premium</span>
                  <Crown className="w-4 h-4 ml-2" />
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Tips Section */}
        <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl">
          <div className="flex items-center mb-8">
            <div className="bg-gradient-to-r from-yellow-400 to-orange-400 p-3 rounded-2xl shadow-lg mr-4">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-white">Tips para el mercado laboral peruano</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white/5 backdrop-blur-sm border border-blue-500/30 rounded-2xl p-6 border-l-4 border-l-blue-500">
              <div className="flex items-center mb-3">
                <Target className="w-5 h-5 text-blue-400 mr-2" />
                <h4 className="font-semibold text-white">Personaliza tu CV</h4>
              </div>
              <p className="text-gray-300 text-sm leading-relaxed">
                Adapta tu currículum para cada empresa peruana, destacando experiencia relevante y logros cuantificables
              </p>
            </div>
            
            <div className="bg-white/5 backdrop-blur-sm border border-green-500/30 rounded-2xl p-6 border-l-4 border-l-green-500">
              <div className="flex items-center mb-3">
                <Zap className="w-5 h-5 text-green-400 mr-2" />
                <h4 className="font-semibold text-white">Networking Local</h4>
              </div>
              <p className="text-gray-300 text-sm leading-relaxed">
                Utiliza LinkedIn y eventos locales para conectar con profesionales y empresas peruanas
              </p>
            </div>
            
            <div className="bg-white/5 backdrop-blur-sm border border-purple-500/30 rounded-2xl p-6 border-l-4 border-l-purple-500">
              <div className="flex items-center mb-3">
                <MessageCircle className="w-5 h-5 text-purple-400 mr-2" />
                <h4 className="font-semibold text-white">Prepárate para entrevistas</h4>
              </div>
              <p className="text-gray-300 text-sm leading-relaxed">
                Practica respuestas sobre tu experiencia y demuestra conocimiento del mercado peruano
              </p>
            </div>
            
            <div className="bg-white/5 backdrop-blur-sm border border-yellow-500/30 rounded-2xl p-6 border-l-4 border-l-yellow-500">
              <div className="flex items-center mb-3">
                <BarChart3 className="w-5 h-5 text-yellow-400 mr-2" />
                <h4 className="font-semibold text-white">Empresas objetivo</h4>
              </div>
              <p className="text-gray-300 text-sm leading-relaxed">
                Investiga sobre las principales empresas en tu sector y sus culturas organizacionales en Perú
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;