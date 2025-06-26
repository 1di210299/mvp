import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Crown, Check, Star } from 'lucide-react';
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
      color: 'blue'
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
      color: 'purple'
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
      color: 'gold'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Planes diseñados para el mercado laboral peruano
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Elige el plan que mejor se adapte a tus necesidades profesionales. 
            Todos incluyen IA especializada en reclutamiento peruano.
          </p>
          {user?.is_premium && (
            <div className="mt-6 inline-flex items-center px-4 py-2 bg-yellow-100 text-yellow-800 rounded-full">
              <Crown className="w-4 h-4 mr-2" />
              Ya tienes una suscripción Premium activa
            </div>
          )}
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`relative bg-white rounded-2xl shadow-lg p-8 ${
                plan.popular ? 'ring-2 ring-purple-500 scale-105' : ''
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium flex items-center">
                    <Star className="w-3 h-3 mr-1" />
                    Más Popular
                  </span>
                </div>
              )}

              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <p className="text-gray-600 mb-4">{plan.description}</p>
                
                <div className="mb-4">
                  {plan.originalPrice && (
                    <p className="text-gray-400 line-through text-sm">
                      S/ {plan.originalPrice}
                    </p>
                  )}
                  <div className="flex items-center justify-center">
                    <span className="text-4xl font-bold text-gray-900">S/ {plan.price}</span>
                    <span className="text-gray-600 ml-2">/ {plan.period}</span>
                  </div>
                  {plan.discount && (
                    <p className="text-green-600 text-sm font-medium mt-1">{plan.discount}</p>
                  )}
                </div>

                <button
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={loading || user?.is_premium}
                  className={`w-full py-3 px-6 rounded-lg font-medium transition-colors ${
                    plan.popular
                      ? 'bg-purple-600 text-white hover:bg-purple-700'
                      : 'bg-gray-900 text-white hover:bg-gray-800'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {loading && selectedPlan === plan.id ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Procesando...
                    </div>
                  ) : user?.is_premium ? (
                    'Plan Activo'
                  ) : (
                    `Elegir ${plan.name}`
                  )}
                </button>
              </div>

              <div className="space-y-3">
                {plan.features.map((feature, index) => (
                  <div key={index} className="flex items-center">
                    <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                    <span className="text-gray-700 text-sm">{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* FAQ Section */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
            Preguntas Frecuentes
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                ¿Qué incluye el plan gratuito?
              </h3>
              <p className="text-gray-600 text-sm">
                El plan gratuito incluye acceso completo al Editor de CV con IA. 
                Puedes mejorar tu currículum tantas veces como necesites.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                ¿Puedo cancelar mi suscripción en cualquier momento?
              </h3>
              <p className="text-gray-600 text-sm">
                Sí, puedes cancelar tu suscripción cuando quieras. 
                Mantendrás acceso premium hasta que termine tu período actual.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                ¿La IA está especializada en el mercado peruano?
              </h3>
              <p className="text-gray-600 text-sm">
                Absolutamente. Nuestra IA está entrenada específicamente para 
                el mercado laboral peruano, incluyendo empresas, cultura y expectativas locales.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                ¿Qué métodos de pago aceptan?
              </h3>
              <p className="text-gray-600 text-sm">
                Aceptamos tarjetas de crédito, débito, y próximamente 
                billeteras digitales populares en Perú como Yape y Plin.
              </p>
            </div>
          </div>
        </div>

        {/* Trust Signals */}
        <div className="text-center mt-16">
          <div className="flex items-center justify-center space-x-8 mb-8">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">500+</div>
              <div className="text-gray-600">CVs mejorados</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">95%</div>
              <div className="text-gray-600">Satisfacción</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">24/7</div>
              <div className="text-gray-600">Soporte</div>
            </div>
          </div>
          
          <p className="text-gray-600">
            🔒 Pago seguro • ✨ IA avanzada • 🇵🇪 Especializado en Perú
          </p>
        </div>
      </div>
    </div>
  );
};

export default Pricing;