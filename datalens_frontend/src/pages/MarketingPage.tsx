import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Users,
  Shield,
  Zap,
  Target,
  Star,
  CheckCircle,
  ArrowRight,
  Phone,
  Mail,
  MapPin,
  X
} from '../components/ui/icons';
import './MarketingPage.css';

const MarketingPage: React.FC = () => {
  const navigate = useNavigate();
  const [showDemoModal, setShowDemoModal] = useState(false);
  const [demoForm, setDemoForm] = useState({
    name: '',
    email: '',
    company: '',
    phone: '',
    employees: '',
    industry: ''
  });

  const handleLoginRedirect = () => {
    navigate('/login');
  };

  const handleDemoRequest = () => {
    setShowDemoModal(true);
  };

  const handleDemoSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Aquí normalmente enviarías los datos a tu API
    console.log('Demo request:', demoForm);
    alert('¡Gracias! Nos pondremos en contacto contigo en menos de 24 horas para agendar tu demo personalizada.');
    setShowDemoModal(false);
    setDemoForm({ name: '', email: '', company: '', phone: '', employees: '', industry: '' });
  };

  const testimonials = [
    {
      name: "Carlos Mendoza",
      company: "Distribuidora Lima Norte",
      role: "Gerente General",
      image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face",
      quote: "DataLens revolucionó nuestra gestión de inventarios. Ahora predecimos la demanda con 90% de precisión y reducimos el stock muerto en 60%."
    },
    {
      name: "Ana Quispe",
      company: "Farmacia San Juan",
      role: "Propietaria",
      image: "https://images.unsplash.com/photo-1494790108755-2616b612b05b?w=150&h=150&fit=crop&crop=face",
      quote: "Las alertas automáticas nos salvaron de quedarnos sin medicamentos esenciales. Es como tener un asistente inteligente 24/7."
    },
    {
      name: "Roberto Silva",
      company: "Autopartes Perú",
      role: "Jefe de Logística",
      image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
      quote: "Pasamos de tener problemas de stock a optimizar nuestro capital de trabajo. ROI del 300% en 6 meses."
    }
  ];

  const features = [
    {
      icon: <BarChart3 className="h-8 w-8" />,
      title: "Inteligencia Artificial Avanzada",
      description: "Algoritmos de machine learning que predicen la demanda con precisión superior al 85%, optimizando tu inventario automáticamente."
    },
    {
      icon: <AlertTriangle className="h-8 w-8" />,
      title: "Alertas Inteligentes",
      description: "Notificaciones automáticas de stock bajo, productos próximos a vencer y oportunidades de reabastecimiento."
    },
    {
      icon: <TrendingUp className="h-8 w-8" />,
      title: "Pronósticos Precisos",
      description: "Predicciones de demanda basadas en históricos, estacionalidad y tendencias del mercado peruano."
    },
    {
      icon: <Package className="h-8 w-8" />,
      title: "Control Total de Stock",
      description: "Gestiona múltiples almacenes, ubicaciones y lotes con trazabilidad completa en tiempo real."
    },
    {
      icon: <Target className="h-8 w-8" />,
      title: "Optimización de Costos",
      description: "Reduce el capital inmovilizado hasta en 40% mientras mantienes el nivel de servicio óptimo."
    },
    {
      icon: <Shield className="h-8 w-8" />,
      title: "100% Seguro y Confiable",
      description: "Datos encriptados, respaldos automáticos y cumplimiento con normativas peruanas de protección de datos."
    }
  ];

  const benefits = [
    "Reduce costos de inventario hasta 40%",
    "Elimina roturas de stock en 95%",
    "Automatiza reposición inteligente",
    "Identifica productos de baja rotación",
    "Optimiza espacio de almacén",
    "Reportes ejecutivos automáticos"
  ];

  const stats = [
    { number: "500+", label: "Empresas Peruanas", sublabel: "confían en nosotros" },
    { number: "89%", label: "Reducción de Faltantes", sublabel: "promedio de clientes" },
    { number: "45%", label: "Ahorro en Costos", sublabel: "de inventario" },
    { number: "24/7", label: "Soporte Técnico", sublabel: "en español" }
  ];

  return (
    <div className="marketing-page">
      {/* Header Navigation */}
      <nav className="marketing-nav">
        <div className="nav-container">
          <div className="nav-logo">
            <Package className="h-8 w-8 text-blue-600" />
            <span className="logo-text">DataLens</span>
          </div>
          
          <div className="nav-links">
            <a href="#features">Características</a>
            <a href="#benefits">Beneficios</a>
            <a href="#testimonials">Testimonios</a>
            <a href="#pricing">Precios</a>
            <button onClick={handleLoginRedirect} className="nav-login-btn">
              Iniciar Sesión
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <h1 className="hero-title">
              Revoluciona tu Inventario con 
              <span className="gradient-text"> Inteligencia Artificial</span>
            </h1>
            
            <p className="hero-subtitle">
              La plataforma #1 de gestión inteligente de inventarios para PYMEs peruanas. 
              Predice la demanda, optimiza costos y nunca más te quedes sin stock.
            </p>
            
            <div className="hero-stats">
              <div className="stat-item">
                <span className="stat-number">500+</span>
                <span className="stat-label">Empresas</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">89%</span>
                <span className="stat-label">Menos Faltantes</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">45%</span>
                <span className="stat-label">Ahorro Costos</span>
              </div>
            </div>
            
            <div className="hero-actions">
              <button onClick={handleLoginRedirect} className="cta-primary">
                <ArrowRight className="h-5 w-5" />
                Empezar Gratis Ahora
              </button>
              <button onClick={handleDemoRequest} className="cta-secondary">
                <Phone className="h-5 w-5" />
                Agendar Demo
              </button>
            </div>
            
            <div className="hero-guarantee">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span>Prueba gratuita 30 días • Sin compromiso • Soporte en español</span>
            </div>
          </div>
          
          <div className="hero-visual">
            <div className="dashboard-preview">
              <div className="preview-header">
                <div className="preview-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span className="preview-title">DataLens Dashboard</span>
              </div>
              <div className="preview-content">
                <div className="preview-cards">
                  <div className="preview-card">
                    <Package className="h-6 w-6 text-blue-600" />
                    <div>
                      <span className="card-value">1,247</span>
                      <span className="card-label">Productos</span>
                    </div>
                  </div>
                  <div className="preview-card">
                    <TrendingUp className="h-6 w-6 text-green-600" />
                    <div>
                      <span className="card-value">S/ 890K</span>
                      <span className="card-label">Valor Stock</span>
                    </div>
                  </div>
                </div>
                <div className="preview-chart">
                  <div className="chart-bars">
                    <div className="bar" style={{height: '60%'}}></div>
                    <div className="bar" style={{height: '80%'}}></div>
                    <div className="bar" style={{height: '45%'}}></div>
                    <div className="bar" style={{height: '90%'}}></div>
                    <div className="bar" style={{height: '70%'}}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="problem-section">
        <div className="container">
          <h2 className="section-title">¿Te Suena Familiar?</h2>
          
          <div className="problems-grid">
            <div className="problem-card">
              <div className="problem-icon">😰</div>
              <h3>Te Quedas Sin Stock</h3>
              <p>Pierdes ventas porque no sabes cuándo reordenar. Los clientes se van a la competencia.</p>
            </div>
            
            <div className="problem-card">
              <div className="problem-icon">💸</div>
              <h3>Dinero Atrapado</h3>
              <p>Tienes productos que no se mueven, capital inmovilizado que podría estar generando más ingresos.</p>
            </div>
            
            <div className="problem-card">
              <div className="problem-icon">📊</div>
              <h3>Decisiones a Ciegas</h3>
              <p>No tienes datos claros para tomar decisiones. Todo es "por experiencia" o intuición.</p>
            </div>
            
            <div className="problem-card">
              <div className="problem-icon">⏰</div>
              <h3>Tiempo Perdido</h3>
              <p>Horas contando inventario manualmente, creando reportes en Excel que nadie entiende.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section className="solution-section">
        <div className="container">
          <div className="solution-content">
            <div className="solution-text">
              <h2>DataLens: La Solución Inteligente que Necesitas</h2>
              <p className="solution-subtitle">
                Imagina tener un asistente superinteligente que conoce tu negocio mejor que tú, 
                trabaja 24/7 y nunca se equivoca en las predicciones.
              </p>
              
              <div className="solution-benefits">
                {benefits.map((benefit, index) => (
                  <div key={index} className="benefit-item">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span>{benefit}</span>
                  </div>
                ))}
              </div>
              
              <button onClick={handleLoginRedirect} className="cta-solution">
                Ver DataLens en Acción
                <ArrowRight className="h-5 w-5" />
              </button>
            </div>
            
            <div className="solution-visual">
              <div className="ai-brain">
                <div className="brain-core">
                  <Zap className="h-12 w-12 text-yellow-400" />
                </div>
                <div className="brain-connections">
                  <div className="connection"></div>
                  <div className="connection"></div>
                  <div className="connection"></div>
                  <div className="connection"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="container">
          <h2 className="section-title">Características que Transformarán tu Negocio</h2>
          
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className="feature-card">
                <div className="feature-icon">
                  {feature.icon}
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="testimonials-section">
        <div className="container">
          <h2 className="section-title">Lo que Dicen Nuestros Clientes Peruanos</h2>
          
          <div className="testimonials-grid">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="testimonial-card">
                <div className="testimonial-content">
                  <div className="stars">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                    ))}
                  </div>
                  <p>"{testimonial.quote}"</p>
                </div>
                
                <div className="testimonial-author">
                  <img src={testimonial.image} alt={testimonial.name} />
                  <div>
                    <h4>{testimonial.name}</h4>
                    <p>{testimonial.role}</p>
                    <span>{testimonial.company}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="pricing-section">
        <div className="container">
          <h2 className="section-title">Planes Diseñados para PYMEs Peruanas</h2>
          <p className="pricing-subtitle">Escoge el plan perfecto para tu empresa. Sin compromisos, cancela cuando quieras.</p>
          
          <div className="pricing-grid">
            {/* Plan Starter */}
            <div className="pricing-card starter">
              <div className="plan-header">
                <h3>Starter</h3>
                <div className="plan-price">
                  <span className="currency">S/</span>
                  <span className="amount">149</span>
                  <span className="period">/mes</span>
                </div>
                <p className="plan-description">Perfecto para microempresas que inician su transformación digital</p>
              </div>
              
              <div className="plan-features">
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Hasta 500 productos</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>1 usuario incluido</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Dashboard básico</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Alertas de stock bajo</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Reportes básicos</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Soporte por email</span>
                </div>
              </div>
              
              <button onClick={handleLoginRedirect} className="plan-cta starter-cta">
                Empezar Gratis 30 días
              </button>
            </div>

            {/* Plan Professional */}
            <div className="pricing-card professional popular">
              <div className="popular-badge">Más Popular</div>
              <div className="plan-header">
                <h3>Professional</h3>
                <div className="plan-price">
                  <span className="currency">S/</span>
                  <span className="amount">399</span>
                  <span className="period">/mes</span>
                </div>
                <p className="plan-description">Ideal para pequeñas empresas que necesitan predicciones inteligentes</p>
              </div>
              
              <div className="plan-features">
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Hasta 5,000 productos</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Hasta 5 usuarios</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Inteligencia Artificial avanzada</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Pronósticos de demanda</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Múltiples almacenes</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Alertas personalizadas</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Integración con Excel</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Soporte prioritario</span>
                </div>
              </div>
              
              <button onClick={handleLoginRedirect} className="plan-cta professional-cta">
                Empezar Gratis 30 días
              </button>
            </div>

            {/* Plan Enterprise */}
            <div className="pricing-card enterprise">
              <div className="plan-header">
                <h3>Enterprise</h3>
                <div className="plan-price">
                  <span className="currency">S/</span>
                  <span className="amount">899</span>
                  <span className="period">/mes</span>
                </div>
                <p className="plan-description">Para medianas empresas que requieren máximo control y personalización</p>
              </div>
              
              <div className="plan-features">
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Productos ilimitados</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Usuarios ilimitados</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>IA personalizada</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>API completa</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Integración ERP/CRM</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Reportes avanzados</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Soporte 24/7 dedicado</span>
                </div>
                <div className="feature-item">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Gerente de cuenta</span>
                </div>
              </div>
              
              <button onClick={handleLoginRedirect} className="plan-cta enterprise-cta">
                Contactar Ventas
              </button>
            </div>
          </div>
          
          <div className="pricing-guarantee">
            <CheckCircle className="h-6 w-6 text-green-500" />
            <span>Garantía de 30 días. Si no estás satisfecho, te devolvemos tu dinero.</span>
          </div>
        </div>
      </section>

      {/* ROI Calculator */}
      <section className="roi-section">
        <div className="container">
          <h2 className="section-title">Calcula tu Retorno de Inversión</h2>
          
          <div className="roi-calculator">
            <div className="roi-inputs">
              <h3>Ingresa los datos de tu empresa:</h3>
              
              <div className="input-group">
                <label>Número de productos en inventario:</label>
                <input type="number" defaultValue="200" className="roi-input" />
              </div>
              
              <div className="input-group">
                <label>Valor promedio de inventario (S/):</label>
                <input type="number" defaultValue="50000" className="roi-input" />
              </div>
              
              <div className="input-group">
                <label>Horas semanales en gestión manual:</label>
                <input type="number" defaultValue="15" className="roi-input" />
              </div>
            </div>
            
            <div className="roi-results">
              <h3>Tu ahorro anual estimado:</h3>
              
              <div className="savings-card">
                <div className="savings-item">
                  <span className="savings-label">Reducción de capital inmovilizado (30%):</span>
                  <span className="savings-value">S/ 15,000</span>
                </div>
                
                <div className="savings-item">
                  <span className="savings-label">Ahorro en tiempo (15h × S/50 × 52 sem):</span>
                  <span className="savings-value">S/ 39,000</span>
                </div>
                
                <div className="savings-item">
                  <span className="savings-label">Reducción de faltantes de stock (10%):</span>
                  <span className="savings-value">S/ 25,000</span>
                </div>
                
                <div className="savings-total">
                  <span className="savings-label">Total ahorrado anual:</span>
                  <span className="savings-value total">S/ 79,000</span>
                </div>
                
                <div className="roi-highlight">
                  <span>ROI: <strong>1,650%</strong> en el primer año</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>¿Listo para Revolucionar tu Inventario?</h2>
            <p>
              Únete a más de 500 empresas peruanas que ya transformaron su gestión de inventarios. 
              Comienza tu prueba gratuita hoy mismo.
            </p>
            
            <div className="cta-actions">
              <button onClick={handleLoginRedirect} className="cta-primary large">
                <ArrowRight className="h-6 w-6" />
                Comenzar Prueba Gratuita
              </button>
              
              <div className="cta-info">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span>30 días gratis • Sin tarjeta de crédito • Soporte en español</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Modal */}
      {showDemoModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Agenda tu Demo Personalizada</h3>
              <button onClick={() => setShowDemoModal(false)} className="modal-close">
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <form onSubmit={handleDemoSubmit} className="demo-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Nombre completo *</label>
                  <input
                    type="text"
                    required
                    value={demoForm.name}
                    onChange={(e) => setDemoForm({...demoForm, name: e.target.value})}
                    placeholder="Tu nombre completo"
                  />
                </div>
                
                <div className="form-group">
                  <label>Email corporativo *</label>
                  <input
                    type="email"
                    required
                    value={demoForm.email}
                    onChange={(e) => setDemoForm({...demoForm, email: e.target.value})}
                    placeholder="tu@empresa.com"
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Empresa *</label>
                  <input
                    type="text"
                    required
                    value={demoForm.company}
                    onChange={(e) => setDemoForm({...demoForm, company: e.target.value})}
                    placeholder="Nombre de tu empresa"
                  />
                </div>
                
                <div className="form-group">
                  <label>Teléfono</label>
                  <input
                    type="tel"
                    value={demoForm.phone}
                    onChange={(e) => setDemoForm({...demoForm, phone: e.target.value})}
                    placeholder="+51 999 999 999"
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Número de empleados</label>
                  <select
                    value={demoForm.employees}
                    onChange={(e) => setDemoForm({...demoForm, employees: e.target.value})}
                  >
                    <option value="">Selecciona</option>
                    <option value="1-10">1-10 empleados</option>
                    <option value="11-50">11-50 empleados</option>
                    <option value="51-200">51-200 empleados</option>
                    <option value="200+">Más de 200 empleados</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Industria</label>
                  <select
                    value={demoForm.industry}
                    onChange={(e) => setDemoForm({...demoForm, industry: e.target.value})}
                  >
                    <option value="">Selecciona</option>
                    <option value="retail">Retail / Comercio</option>
                    <option value="distribucion">Distribución</option>
                    <option value="manufactura">Manufactura</option>
                    <option value="farmaceutico">Farmacéutico</option>
                    <option value="alimentos">Alimentos y Bebidas</option>
                    <option value="automotriz">Automotriz</option>
                    <option value="otros">Otros</option>
                  </select>
                </div>
              </div>
              
              <div className="demo-benefits">
                <h4>En tu demo personalizada verás:</h4>
                <div className="demo-benefit-list">
                  <div className="demo-benefit">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span>Configuración específica para tu industria</span>
                  </div>
                  <div className="demo-benefit">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span>Simulación con datos de tu empresa</span>
                  </div>
                  <div className="demo-benefit">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span>ROI calculado para tu caso específico</span>
                  </div>
                  <div className="demo-benefit">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span>Hoja de ruta de implementación</span>
                  </div>
                </div>
              </div>
              
              <button type="submit" className="demo-submit">
                Agendar Mi Demo Gratuita
              </button>
              
              <p className="demo-disclaimer">
                Tu demo será de 30 minutos con un especialista en español. 
                Sin compromiso de compra.
              </p>
            </form>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="marketing-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <div className="footer-logo">
                <Package className="h-8 w-8 text-blue-600" />
                <span>DataLens</span>
              </div>
              <p>Inteligencia artificial para inventarios inteligentes</p>
            </div>
            
            <div className="footer-links">
              <div className="link-group">
                <h4>Producto</h4>
                <a href="#features">Características</a>
                <a href="#pricing">Precios</a>
                <a href="#">Integraciones</a>
              </div>
              
              <div className="link-group">
                <h4>Empresa</h4>
                <a href="#">Sobre Nosotros</a>
                <a href="#">Carreras</a>
                <a href="#">Blog</a>
              </div>
              
              <div className="link-group">
                <h4>Contacto</h4>
                <div className="contact-item">
                  <Phone className="h-4 w-4" />
                  <span>+51 1 234-5678</span>
                </div>
                <div className="contact-item">
                  <Mail className="h-4 w-4" />
                  <span>hola@datalens.pe</span>
                </div>
                <div className="contact-item">
                  <MapPin className="h-4 w-4" />
                  <span>Lima, Perú</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="footer-bottom">
            <p>&copy; 2025 DataLens. Todos los derechos reservados.</p>
            <div className="footer-legal">
              <a href="#">Términos de Servicio</a>
              <a href="#">Política de Privacidad</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default MarketingPage;