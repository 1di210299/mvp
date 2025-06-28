import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Crown, Check, Star, Sparkles, ArrowRight, Shield, Zap, Target, TrendingUp } from 'lucide-react';
import { paymentService } from '../services/paymentService';

const Pricing: React.FC = () => {
  const { user, updateUserPremium } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string>('');

  const handleSubscribe = async (planType: string) => {
    if (!user) {
      navigate('/login');
      return;
    }

    setLoading(true);
    setSelectedPlan(planType);

    try {
      // Crear pago simulado
      const payment = await paymentService.createPayment({
        subscription_type: planType,
        payment_method: 'simulation'
      });

      // Simular éxito del pago
      await paymentService.simulatePaymentSuccess(payment.id);
      
      // Actualizar estado del usuario
      updateUserPremium();
      
      // Redirigir al dashboard
      navigate('/dashboard');
    } catch (error) {
      console.error('Error al procesar el pago:', error);
      alert('Error al procesar el pago. Intenta nuevamente.');
    } finally {
      setLoading(false);
      setSelectedPlan('');
    }
  };

  const plans = [
    {
      id: 'one-time',
      name: 'Prueba Premium',
      price: 9.90,
      period: '7 días',
      description: 'Perfecto para probar todas las funciones',
      features: [
        'Editor de CV ilimitado',
        'Hasta 5 cartas de presentación',
        'Hasta 3 entrevistas simuladas',
        'Feedback detallado con IA',
        'Soporte por email'
      ],
      popular: false,
      gradient: 'from-blue-500 to-cyan-500',
      icon: Target
    },
    {
      id: 'monthly',
      name: 'Plan Mensual',
      price: 29.90,
      period: 'mes',
      description: 'Ideal para búsqueda activa de empleo',
      features: [
        'Editor de CV ilimitado',
        'Cartas de presentación ilimitadas',
        'Entrevistas simuladas ilimitadas',
        'Feedback detallado con IA',
        'Análisis de mercado laboral peruano',
        'Soporte prioritario',
        'Actualizaciones constantes'
      ],
      popular: true,
      gradient: 'from-purple-500 to-pink-500',
      icon: Zap
    },
    {
      id: 'yearly',
      name: 'Plan Anual',
      price: 299.90,
      period: 'año',
      description: 'Mejor valor para desarrollo profesional continuo',
      originalPrice: 358.80,
      discount: '17% de descuento',
      features: [
        'Todo lo del plan mensual',
        'Análisis trimestral de progreso',
        'Sesiones de coaching 1:1 (2 al año)',
        'Acceso a webinars exclusivos',
        'Red de networking premium',
        'Garantía de satisfacción',
        'Soporte 24/7'
      ],
      popular: false,
      gradient: 'from-yellow-400 to-orange-500',
      icon: Crown
    }
  ];

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

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Header */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center px-4 py-2 mb-8 bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-white/10 rounded-full text-white">
            <Sparkles className="w-4 h-4 mr-2 text-yellow-400" />
            <span className="text-sm font-medium">Tecnología de IA Avanzada</span>
          </div>
          
          <h1 className="text-6xl font-bold bg-gradient-to-r from-white via-purple-200 to-cyan-200 bg-clip-text text-transparent mb-6">
            Planes Premium
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Elige el plan que mejor se adapte a tus necesidades profesionales. 
            Todos incluyen IA especializada en reclutamiento peruano.
          </p>
          {user?.is_premium && (
            <div className="mt-8 inline-flex items-center px-6 py-3 bg-gradient-to-r from-yellow-400/20 to-yellow-500/20 backdrop-blur-xl border border-yellow-400/30 rounded-2xl text-yellow-100">
              <Crown className="w-5 h-5 mr-2 text-yellow-400" />
              Ya tienes una suscripción Premium activa
            </div>
          )}
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
          {plans.map((plan) => {
            const IconComponent = plan.icon;
            return (
              <div
                key={plan.id}
                className={`group relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl hover:bg-white/10 transition-all duration-500 transform hover:scale-105 hover:-translate-y-2 ${
                  plan.popular ? 'ring-2 ring-purple-400/50 scale-105' : ''
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-2 rounded-full text-sm font-bold flex items-center shadow-lg">
                      <Star className="w-4 h-4 mr-2" />
                      Más Popular
                    </span>
                  </div>
                )}

                <div className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-3xl"
                     style={{
                       background: plan.popular 
                         ? 'linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(236, 72, 153, 0.1))'
                         : 'linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(16, 185, 129, 0.05))'
                     }}>
                </div>

                <div className="relative z-10">
                  {/* Icon */}
                  <div className={`bg-gradient-to-r ${plan.gradient} p-4 rounded-2xl w-fit mx-auto mb-6 shadow-lg`}>
                    <IconComponent className="w-8 h-8 text-white" />
                  </div>

                  {/* Plan Info */}
                  <div className="text-center mb-8">
                    <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                    <p className="text-gray-300 mb-6">{plan.description}</p>
                    
                    <div className="mb-6">
                      {plan.originalPrice && (
                        <p className="text-gray-400 line-through text-sm">
                          S/ {plan.originalPrice}
                        </p>
                      )}
                      <div className="flex items-center justify-center">
                        <span className="text-4xl font-bold text-white">S/ {plan.price}</span>
                        <span className="text-gray-300 ml-2">/ {plan.period}</span>
                      </div>
                      {plan.discount && (
                        <p className="text-green-400 text-sm font-medium mt-2 flex items-center justify-center">
                          <TrendingUp className="w-4 h-4 mr-1" />
                          {plan.discount}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => handleSubscribe(plan.id)}
                      disabled={loading || user?.is_premium}
                      className={`group w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 transform hover:scale-105 flex items-center justify-center ${
                        plan.popular
                          ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg hover:shadow-purple-500/25'
                          : 'bg-gradient-to-r from-gray-600 to-gray-700 text-white hover:from-gray-500 hover:to-gray-600'
                      } disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none`}
                    >
                      {loading && selectedPlan === plan.id ? (
                        <div className="flex items-center">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                          Procesando...
                        </div>
                      ) : user?.is_premium ? (
                        <>
                          <Crown className="w-5 h-5 mr-2" />
                          Plan Activo
                        </>
                      ) : (
                        <>
                          Elegir {plan.name}
                          <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                        </>
                      )}
                    </button>
                  </div>

                  {/* Features */}
                  <div className="space-y-4">
                    {plan.features.map((feature, index) => (
                      <div key={index} className="flex items-center">
                        <div className="bg-green-500/20 p-1 rounded-full mr-3">
                          <Check className="w-4 h-4 text-green-400" />
                        </div>
                        <span className="text-gray-300 text-sm">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/20 rounded-3xl p-12 shadow-2xl mb-16">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Preguntas Frecuentes
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6">
              <h3 className="font-semibold text-white mb-3 flex items-center">
                <Shield className="w-5 h-5 mr-2 text-blue-400" />
                ¿Qué incluye el plan gratuito?
              </h3>
              <p className="text-gray-300 text-sm leading-relaxed">
                El plan gratuito incluye acceso completo al Editor de CV con IA. 
                Puedes mejorar tu currículum tantas veces como necesites.
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6">
              <h3 className="font-semibold text-white mb-3 flex items-center">
                <ArrowRight className="w-5 h-5 mr-2 text-green-400" />
                ¿Puedo cancelar mi suscripción en cualquier momento?
              </h3>
              <p className="text-gray-300 text-sm leading-relaxed">
                Sí, puedes cancelar tu suscripción cuando quieras. 
                Mantendrás acceso premium hasta que termine tu período actual.
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6">
              <h3 className="font-semibold text-white mb-3 flex items-center">
                <Target className="w-5 h-5 mr-2 text-purple-400" />
                ¿La IA está especializada en el mercado peruano?
              </h3>
              <p className="text-gray-300 text-sm leading-relaxed">
                Absolutamente. Nuestra IA está entrenada específicamente para 
                el mercado laboral peruano, incluyendo empresas, cultura y expectativas locales.
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6">
              <h3 className="font-semibold text-white mb-3 flex items-center">
                <Sparkles className="w-5 h-5 mr-2 text-yellow-400" />
                ¿Qué métodos de pago aceptan?
              </h3>
              <p className="text-gray-300 text-sm leading-relaxed">
                Aceptamos tarjetas de crédito, débito, y próximamente 
                billeteras digitales populares en Perú como Yape y Plin.
              </p>
            </div>
          </div>
        </div>

        {/* Trust Signals */}
        <div className="text-center">
          <div className="grid grid-cols-3 gap-8 mb-12">
            <div className="group text-center">
              <div className="text-4xl font-bold text-transparent bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text mb-2 group-hover:scale-110 transition-transform">
                500+
              </div>
              <div className="text-gray-300">CVs Mejorados</div>
            </div>
            <div className="group text-center">
              <div className="text-4xl font-bold text-transparent bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text mb-2 group-hover:scale-110 transition-transform">
                95%
              </div>
              <div className="text-gray-300">Satisfacción</div>
            </div>
            <div className="group text-center">
              <div className="text-4xl font-bold text-transparent bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text mb-2 group-hover:scale-110 transition-transform">
                24/7
              </div>
              <div className="text-gray-300">Soporte</div>
            </div>
          </div>
          
          <div className="flex items-center justify-center space-x-8 text-gray-300">
            <div className="flex items-center">
              <Shield className="w-5 h-5 text-green-400 mr-2" />
              <span>Pago seguro</span>
            </div>
            <div className="flex items-center">
              <Sparkles className="w-5 h-5 text-yellow-400 mr-2" />
              <span>IA avanzada</span>
            </div>
            <div className="flex items-center">
              <Target className="w-5 h-5 text-red-400 mr-2" />
              <span>Especializado en Perú</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Pricing;