import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { FileText, Mail, MessageCircle, Crown, TrendingUp, Star } from 'lucide-react';
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          ¡Hola, {user?.full_name}! 👋
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          Bienvenido a tu dashboard de coaching laboral con IA
        </p>
      </div>

      {/* Premium Status */}
      {user?.is_premium ? (
        <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-lg p-6 mb-8 text-white">
          <div className="flex items-center">
            <Crown className="w-8 h-8 mr-3" />
            <div>
              <h2 className="text-xl font-semibold">Cuenta Premium Activa</h2>
              <p className="text-yellow-100">
                {subscriptionInfo?.subscription_type === 'yearly' && 'Plan Anual - '}
                {subscriptionInfo?.subscription_type === 'monthly' && 'Plan Mensual - '}
                Acceso ilimitado a todas las funciones
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 mb-8 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Star className="w-8 h-8 mr-3" />
              <div>
                <h2 className="text-xl font-semibold">Actualiza a Premium</h2>
                <p className="text-blue-100">
                  Desbloquea cartas de presentación y simulador de entrevistas
                </p>
              </div>
            </div>
            <Link
              to="/pricing"
              className="bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Ver Planes
            </Link>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="bg-blue-100 p-3 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">CVs Mejorados</p>
              <p className="text-2xl font-bold text-gray-900">{stats.cvCount}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="bg-purple-100 p-3 rounded-lg">
              <Mail className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Cartas Generadas</p>
              <p className="text-2xl font-bold text-gray-900">{stats.coverLetterCount}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="bg-green-100 p-3 rounded-lg">
              <MessageCircle className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Entrevistas Practicadas</p>
              <p className="text-2xl font-bold text-gray-900">{stats.interviewCount}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Link
          to="/cv-editor"
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow group"
        >
          <div className="flex items-center mb-4">
            <div className="bg-blue-100 p-3 rounded-lg group-hover:bg-blue-200 transition-colors">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="ml-3 text-lg font-semibold text-gray-900">Editor de CV</h3>
          </div>
          <p className="text-gray-600 text-sm">
            Mejora tu currículum con IA especializada en el mercado peruano
          </p>
          <div className="mt-4 flex items-center text-blue-600 text-sm font-medium">
            <span>Comenzar ahora</span>
            <TrendingUp className="w-4 h-4 ml-1" />
          </div>
        </Link>

        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow group">
          {user?.is_premium ? (
            <Link to="/cover-letter" className="block">
              <div className="flex items-center mb-4">
                <div className="bg-purple-100 p-3 rounded-lg group-hover:bg-purple-200 transition-colors">
                  <Mail className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="ml-3 text-lg font-semibold text-gray-900">Cartas de Presentación</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Genera cartas personalizadas para cada puesto y empresa
              </p>
              <div className="mt-4 flex items-center text-purple-600 text-sm font-medium">
                <span>Crear carta</span>
                <TrendingUp className="w-4 h-4 ml-1" />
              </div>
            </Link>
          ) : (
            <div>
              <div className="flex items-center mb-4">
                <div className="bg-gray-100 p-3 rounded-lg">
                  <Mail className="w-6 h-6 text-gray-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-semibold text-gray-900">Cartas de Presentación</h3>
                  <Crown className="w-4 h-4 text-yellow-500 inline-block ml-1" />
                </div>
              </div>
              <p className="text-gray-500 text-sm">
                Función premium - Genera cartas personalizadas
              </p>
              <Link
                to="/pricing"
                className="mt-4 inline-flex items-center text-yellow-600 text-sm font-medium"
              >
                <span>Actualizar a Premium</span>
                <Crown className="w-4 h-4 ml-1" />
              </Link>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow group">
          {user?.is_premium ? (
            <Link to="/interview" className="block">
              <div className="flex items-center mb-4">
                <div className="bg-green-100 p-3 rounded-lg group-hover:bg-green-200 transition-colors">
                  <MessageCircle className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="ml-3 text-lg font-semibold text-gray-900">Simulador de Entrevistas</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Practica entrevistas laborales con feedback personalizado
              </p>
              <div className="mt-4 flex items-center text-green-600 text-sm font-medium">
                <span>Iniciar práctica</span>
                <TrendingUp className="w-4 h-4 ml-1" />
              </div>
            </Link>
          ) : (
            <div>
              <div className="flex items-center mb-4">
                <div className="bg-gray-100 p-3 rounded-lg">
                  <MessageCircle className="w-6 h-6 text-gray-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-semibold text-gray-900">Simulador de Entrevistas</h3>
                  <Crown className="w-4 h-4 text-yellow-500 inline-block ml-1" />
                </div>
              </div>
              <p className="text-gray-500 text-sm">
                Función premium - Practica entrevistas con IA
              </p>
              <Link
                to="/pricing"
                className="mt-4 inline-flex items-center text-yellow-600 text-sm font-medium"
              >
                <span>Actualizar a Premium</span>
                <Crown className="w-4 h-4 ml-1" />
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Tips Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          💡 Tips para el mercado laboral peruano
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border-l-4 border-blue-500 pl-4">
            <h4 className="font-medium text-gray-900">Personaliza tu CV</h4>
            <p className="text-sm text-gray-600">
              Adapta tu currículum para cada empresa peruana, destacando experiencia relevante
            </p>
          </div>
          <div className="border-l-4 border-green-500 pl-4">
            <h4 className="font-medium text-gray-900">Networking Local</h4>
            <p className="text-sm text-gray-600">
              Utiliza LinkedIn y eventos locales para conectar con profesionales peruanos
            </p>
          </div>
          <div className="border-l-4 border-purple-500 pl-4">
            <h4 className="font-medium text-gray-900">Prepárate para entrevistas</h4>
            <p className="text-sm text-gray-600">
              Practica respuestas sobre tu experiencia y conocimiento del mercado peruano
            </p>
          </div>
          <div className="border-l-4 border-yellow-500 pl-4">
            <h4 className="font-medium text-gray-900">Empresas objetivo</h4>
            <p className="text-sm text-gray-600">
              Investiga sobre las principales empresas en tu sector en Perú
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;