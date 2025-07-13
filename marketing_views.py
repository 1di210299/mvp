from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView

def marketing_page(request):
    """Vista para servir la página de marketing"""
    # Redirigir al frontend React para la página de marketing
    return HttpResponse('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DataLens - Inteligencia Artificial para Inventarios</title>
        <meta name="description" content="La plataforma #1 de gestión inteligente de inventarios para PYMEs peruanas. Predice la demanda, optimiza costos y nunca más te quedes sin stock.">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                text-align: center;
                max-width: 600px;
                padding: 40px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 25px 45px rgba(0, 0, 0, 0.1);
            }
            .logo {
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 20px;
                background: linear-gradient(45deg, #4facfe, #00f2fe);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle {
                font-size: 20px;
                margin-bottom: 30px;
                opacity: 0.9;
            }
            .description {
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 40px;
                opacity: 0.8;
            }
            .cta-button {
                display: inline-block;
                padding: 15px 30px;
                background: linear-gradient(45deg, #4facfe, #00f2fe);
                color: white;
                text-decoration: none;
                border-radius: 50px;
                font-weight: 600;
                font-size: 18px;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                margin: 10px;
            }
            .cta-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 15px 35px rgba(79, 172, 254, 0.4);
            }
            .cta-secondary {
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }
            .feature {
                padding: 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                text-align: left;
            }
            .feature-icon {
                font-size: 24px;
                margin-bottom: 10px;
            }
            .feature-title {
                font-weight: 600;
                margin-bottom: 10px;
            }
            .feature-desc {
                font-size: 14px;
                opacity: 0.8;
            }
            .redirect-info {
                margin-top: 30px;
                padding: 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                font-size: 14px;
                opacity: 0.9;
            }
            @media (max-width: 768px) {
                .container { padding: 20px; }
                .logo { font-size: 36px; }
                .subtitle { font-size: 18px; }
                .cta-button { font-size: 16px; padding: 12px 24px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">📦 DataLens</div>
            <div class="subtitle">Inteligencia Artificial para Inventarios Inteligentes</div>
            <div class="description">
                La plataforma #1 de gestión inteligente de inventarios para PYMEs peruanas. 
                Predice la demanda, optimiza costos y nunca más te quedes sin stock.
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">IA Avanzada</div>
                    <div class="feature-desc">Predicciones con 90% de precisión</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Reportes Inteligentes</div>
                    <div class="feature-desc">Insights automáticos de tu negocio</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-title">Alertas en Tiempo Real</div>
                    <div class="feature-desc">Nunca más te quedes sin stock</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">💰</div>
                    <div class="feature-title">Ahorra hasta 45%</div>
                    <div class="feature-desc">En costos de inventario</div>
                </div>
            </div>
            
            <a href="http://localhost:3000" class="cta-button">
                Ver Página Completa de Marketing
            </a>
            <a href="http://localhost:3000/login" class="cta-button cta-secondary">
                Iniciar Sesión
            </a>
            
            <div class="redirect-info">
                <strong>💡 Experiencia Completa:</strong><br>
                Para ver la página completa de marketing con todas las características, testimonios, precios y demo interactivo, 
                visita <a href="http://localhost:3000" style="color: #4facfe;">localhost:3000</a>
            </div>
        </div>
        
        <script>
            // Auto-redirect después de 3 segundos si es la primera visita
            if (!sessionStorage.getItem('visited')) {
                setTimeout(() => {
                    if (confirm('¿Te gustaría ver la página completa de marketing de DataLens?')) {
                        window.location.href = 'http://localhost:3000';
                    }
                    sessionStorage.setItem('visited', 'true');
                }, 3000);
            }
        </script>
    </body>
    </html>
    ''')

class MarketingRedirectView(TemplateView):
    """Vista alternativa para redireccionar al frontend"""
    def get(self, request, *args, **kwargs):
        return marketing_page(request)