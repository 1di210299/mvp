import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Crown, FileText, Mail, MessageCircle, Star, CheckCircle, ArrowRight, Sparkles, Zap, Target, TrendingUp } from 'lucide-react';

const Home: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-900 overflow-hidden pt-20">
      {/* Animated Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
        {/* Pattern Background */}
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

      <div className="relative z-10">
        {/* Hero Section */}
        <div className="container mx-auto px-4 py-20">
          <div className="text-center mb-20">
            {/* Floating Badge */}
            <div className="inline-flex items-center px-4 py-2 mb-8 bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-white/10 rounded-full text-white">
              <Sparkles className="w-4 h-4 mr-2 text-yellow-400" />
              <span className="text-sm font-medium">Powered by AI GPT-4 Turbo</span>
            </div>

            <h1 className="text-7xl md:text-8xl font-bold mb-8 bg-gradient-to-r from-white via-purple-200 to-cyan-200 bg-clip-text text-transparent leading-tight">
              Coach de Empleo
              <br />
              <span className="bg-gradient-to-r from-red-400 to-pink-400 bg-clip-text text-transparent">con IA</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-4xl mx-auto leading-relaxed">
              Revoluciona tu búsqueda laboral en Perú con{' '}
              <span className="text-cyan-400 font-semibold">inteligencia artificial avanzada</span>.
              <br />
              Crea CVs impactantes, cartas personalizadas y domina las entrevistas.
            </p>
            
            {user ? (
              <Link
                to="/dashboard"
                className="group relative inline-flex items-center px-8 py-4 bg-gradient-to-r from-red-500 to-pink-500 text-white text-lg font-semibold rounded-2xl shadow-2xl hover:shadow-red-500/25 transition-all duration-300 transform hover:scale-105"
              >
                <Crown className="w-5 h-5 mr-2" />
                Ir a mi Dashboard
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
            ) : (
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link
                  to="/register"
                  className="group relative inline-flex items-center px-8 py-4 bg-gradient-to-r from-red-500 to-pink-500 text-white text-lg font-semibold rounded-2xl shadow-2xl hover:shadow-red-500/25 transition-all duration-300 transform hover:scale-105"
                >
                  <Zap className="w-5 h-5 mr-2" />
                  Comenzar Gratis
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  to="/pricing"
                  className="group inline-flex items-center px-8 py-4 bg-white/10 backdrop-blur-sm border border-white/20 text-white text-lg font-semibold rounded-2xl hover:bg-white/20 transition-all duration-300"
                >
                  Ver Planes Premium
                  <Crown className="w-5 h-5 ml-2 text-yellow-400 group-hover:rotate-12 transition-transform" />
                </Link>
              </div>
            )}
          </div>

          {/* Features Section with Glassmorphism */}
          <div className="grid md:grid-cols-3 gap-8 mb-20">
            <div className="group relative bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl hover:bg-white/10 transition-all duration-500 transform hover:scale-105 hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative z-10">
                <div className="bg-gradient-to-br from-blue-400 to-blue-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                  <FileText className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold mb-4 text-white">Editor Inteligente de CV</h3>
                <p className="text-gray-300 mb-6 leading-relaxed">
                  IA especializada en el mercado peruano que optimiza tu currículum para sistemas ATS 
                  y reclutadores locales.
                </p>
                <div className="flex items-center justify-center text-green-400 bg-green-400/10 px-4 py-2 rounded-full">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium">100% Gratis</span>
                </div>
              </div>
            </div>

            <div className="group relative bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl hover:bg-white/10 transition-all duration-500 transform hover:scale-105 hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative z-10">
                <div className="bg-gradient-to-br from-purple-400 to-purple-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                  <Mail className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold mb-4 text-white">Cartas de Presentación</h3>
                <p className="text-gray-300 mb-6 leading-relaxed">
                  Genera cartas únicas y personalizadas para cada oportunidad laboral 
                  con el tono perfecto para empresas peruanas.
                </p>
                <div className="flex items-center justify-center text-yellow-400 bg-yellow-400/10 px-4 py-2 rounded-full">
                  <Crown className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium">Premium</span>
                </div>
              </div>
            </div>

            <div className="group relative bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl hover:bg-white/10 transition-all duration-500 transform hover:scale-105 hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative z-10">
                <div className="bg-gradient-to-br from-green-400 to-green-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                  <MessageCircle className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold mb-4 text-white">Simulador de Entrevistas</h3>
                <p className="text-gray-300 mb-6 leading-relaxed">
                  Practica con IA avanzada y recibe feedback personalizado 
                  para brillar en entrevistas del mercado laboral peruano.
                </p>
                <div className="flex items-center justify-center text-yellow-400 bg-yellow-400/10 px-4 py-2 rounded-full">
                  <Crown className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium">Premium</span>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Section */}
          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-12 mb-20 shadow-2xl">
            <div className="grid md:grid-cols-4 gap-8 text-center">
              <div className="group">
                <div className="text-4xl font-bold text-transparent bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text mb-2 group-hover:scale-110 transition-transform">
                  500+
                </div>
                <p className="text-gray-300">CVs Mejorados</p>
              </div>
              <div className="group">
                <div className="text-4xl font-bold text-transparent bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text mb-2 group-hover:scale-110 transition-transform">
                  95%
                </div>
                <p className="text-gray-300">Tasa de Éxito</p>
              </div>
              <div className="group">
                <div className="text-4xl font-bold text-transparent bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text mb-2 group-hover:scale-110 transition-transform">
                  48h
                </div>
                <p className="text-gray-300">Tiempo Promedio</p>
              </div>
              <div className="group">
                <div className="text-4xl font-bold text-transparent bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text mb-2 group-hover:scale-110 transition-transform">
                  100%
                </div>
                <p className="text-gray-300">Enfoque Peruano</p>
              </div>
            </div>
          </div>

          {/* Benefits Section */}
          <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/20 rounded-3xl p-12 shadow-2xl mb-20">
            <div className="text-center mb-16">
              <h2 className="text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                La Revolución del Empleo en Perú
              </h2>
              <p className="text-xl text-gray-300 max-w-3xl mx-auto">
                Tecnología de vanguardia diseñada específicamente para el mercado laboral peruano
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="group text-center p-6 rounded-2xl hover:bg-white/5 transition-all duration-300">
                <div className="bg-gradient-to-br from-red-400 to-pink-400 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg group-hover:scale-110 transition-transform">
                  <Target className="w-8 h-8 text-white" />
                </div>
                <h4 className="text-xl font-bold mb-3 text-white">Enfoque Peruano</h4>
                <p className="text-gray-300 leading-relaxed">
                  Algoritmos entrenados con datos del mercado laboral peruano para resultados precisos
                </p>
              </div>

              <div className="group text-center p-6 rounded-2xl hover:bg-white/5 transition-all duration-300">
                <div className="bg-gradient-to-br from-blue-400 to-cyan-400 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg group-hover:scale-110 transition-transform">
                  <Zap className="w-8 h-8 text-white" />
                </div>
                <h4 className="text-xl font-bold mb-3 text-white">IA de Última Generación</h4>
                <p className="text-gray-300 leading-relaxed">
                  GPT-4 Turbo optimizado para crear contenido profesional de alto impacto
                </p>
              </div>

              <div className="group text-center p-6 rounded-2xl hover:bg-white/5 transition-all duration-300">
                <div className="bg-gradient-to-br from-green-400 to-emerald-400 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg group-hover:scale-110 transition-transform">
                  <CheckCircle className="w-8 h-8 text-white" />
                </div>
                <h4 className="text-xl font-bold mb-3 text-white">Experiencia Intuitiva</h4>
                <p className="text-gray-300 leading-relaxed">
                  Interfaz moderna y fluida que te guía paso a paso hacia el éxito profesional
                </p>
              </div>

              <div className="group text-center p-6 rounded-2xl hover:bg-white/5 transition-all duration-300">
                <div className="bg-gradient-to-br from-purple-400 to-pink-400 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg group-hover:scale-110 transition-transform">
                  <TrendingUp className="w-8 h-8 text-white" />
                </div>
                <h4 className="text-xl font-bold mb-3 text-white">Resultados Comprobados</h4>
                <p className="text-gray-300 leading-relaxed">
                  95% de nuestros usuarios mejoran significativamente sus oportunidades laborales
                </p>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          {!user && (
            <div className="text-center relative">
              <div className="bg-gradient-to-r from-red-500/20 to-pink-500/20 backdrop-blur-xl border border-white/20 rounded-3xl p-12 shadow-2xl">
                <h2 className="text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  Tu Futuro Profesional
                  <br />
                  <span className="bg-gradient-to-r from-red-400 to-pink-400 bg-clip-text text-transparent">
                    Comienza Hoy
                  </span>
                </h2>
                <p className="text-xl text-gray-300 mb-10 max-w-2xl mx-auto">
                  Únete a la nueva generación de profesionales peruanos que están 
                  revolucionando su búsqueda laboral con inteligencia artificial
                </p>
                <Link
                  to="/register"
                  className="group inline-flex items-center px-10 py-5 bg-gradient-to-r from-red-500 to-pink-500 text-white text-xl font-bold rounded-2xl shadow-2xl hover:shadow-red-500/25 transition-all duration-300 transform hover:scale-105"
                >
                  <Sparkles className="w-6 h-6 mr-3" />
                  Transformar Mi Carrera Ahora
                  <ArrowRight className="w-6 h-6 ml-3 group-hover:translate-x-2 transition-transform" />
                </Link>
                <p className="text-sm text-gray-400 mt-4">
                  ✨ Sin tarjeta de crédito • Acceso inmediato • 100% gratis para empezar
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Home;