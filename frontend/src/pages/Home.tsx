import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Crown, FileText, Mail, MessageCircle, Star, CheckCircle } from 'lucide-react';

const Home: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Coach de Empleo con <span className="text-peru-red">IA</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Potencia tu búsqueda laboral en Perú con inteligencia artificial. 
            Mejora tu CV, crea cartas de presentación personalizadas y practica 
            entrevistas con nuestro asistente especializado en el mercado peruano.
          </p>
          
          {user ? (
            <Link
              to="/dashboard"
              className="bg-peru-red text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-red-700 transition-colors inline-flex items-center"
            >
              <Crown className="w-5 h-5 mr-2" />
              Ir a mi Dashboard
            </Link>
          ) : (
            <div className="space-x-4">
              <Link
                to="/register"
                className="bg-peru-red text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-red-700 transition-colors inline-block"
              >
                Comenzar Gratis
              </Link>
              <Link
                to="/pricing"
                className="border-2 border-peru-red text-peru-red px-8 py-4 rounded-lg text-lg font-semibold hover:bg-peru-red hover:text-white transition-colors inline-block"
              >
                Ver Planes
              </Link>
            </div>
          )}
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white p-8 rounded-xl shadow-lg text-center">
            <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Editor Inteligente de CV</h3>
            <p className="text-gray-600 mb-4">
              Mejora tu currículum con IA especializada en el mercado laboral peruano. 
              Optimización para ATS y feedback personalizado.
            </p>
            <div className="flex items-center justify-center text-green-600">
              <CheckCircle className="w-4 h-4 mr-1" />
              <span className="text-sm">Gratis para todos</span>
            </div>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg text-center">
            <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mail className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Cartas de Presentación</h3>
            <p className="text-gray-600 mb-4">
              Genera cartas personalizadas para cada puesto y empresa. 
              Tono profesional adaptado al contexto peruano.
            </p>
            <div className="flex items-center justify-center text-yellow-600">
              <Crown className="w-4 h-4 mr-1" />
              <span className="text-sm">Requiere Premium</span>
            </div>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg text-center">
            <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageCircle className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Simulador de Entrevistas</h3>
            <p className="text-gray-600 mb-4">
              Practica entrevistas laborales con IA. Recibe feedback inmediato 
              y mejora tus respuestas para el mercado peruano.
            </p>
            <div className="flex items-center justify-center text-yellow-600">
              <Crown className="w-4 h-4 mr-1" />
              <span className="text-sm">Requiere Premium</span>
            </div>
          </div>
        </div>

        {/* Benefits Section */}
        <div className="bg-white rounded-2xl p-12 shadow-xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              ¿Por qué elegir nuestro Coach de Empleo con IA?
            </h2>
            <p className="text-lg text-gray-600">
              Especializado específicamente en el mercado laboral peruano
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="bg-red-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Star className="w-6 h-6 text-peru-red" />
              </div>
              <h4 className="font-semibold mb-2">Enfoque Peruano</h4>
              <p className="text-sm text-gray-600">
                Conocimiento específico de empresas, cultura y expectativas laborales en Perú
              </p>
            </div>

            <div className="text-center">
              <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Crown className="w-6 h-6 text-blue-600" />
              </div>
              <h4 className="font-semibold mb-2">IA Avanzada</h4>
              <p className="text-sm text-gray-600">
                Powered by GPT-4 Turbo para generar contenido de alta calidad y relevante
              </p>
            </div>

            <div className="text-center">
              <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <h4 className="font-semibold mb-2">Fácil de Usar</h4>
              <p className="text-sm text-gray-600">
                Interfaz intuitiva y proceso guiado para obtener resultados rápidos
              </p>
            </div>

            <div className="text-center">
              <div className="bg-yellow-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Star className="w-6 h-6 text-yellow-600" />
              </div>
              <h4 className="font-semibold mb-2">Resultados Probados</h4>
              <p className="text-sm text-gray-600">
                Mejora significativa en la calidad de CVs y preparación para entrevistas
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        {!user && (
          <div className="text-center mt-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              ¿Listo para impulsar tu carrera profesional?
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Únete a cientos de profesionales peruanos que ya están usando nuestra plataforma
            </p>
            <Link
              to="/register"
              className="bg-peru-red text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-red-700 transition-colors inline-block"
            >
              Comenzar Ahora - Es Gratis
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;