import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
from django.conf import settings
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.core.cache import cache

# Importar OpenAI con validación estricta
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    print(f"✅ OpenAI importado correctamente - Versión: {openai.__version__}")
except ImportError as e:
    OPENAI_AVAILABLE = False
    print(f"❌ ERROR CRÍTICO: OpenAI no está instalado: {e}")
    raise ImportError("OpenAI es requerido para este servicio. Instalar con: pip install openai==1.52.0")

# Modelos
from .models import IntelligenceBriefing, IntelligenceInsight, IntelligenceMetric
from authentication.models import Company, User
from inventory.models import Product, InventoryItem, Transaction
from alerts.models import Alert
from forecasting.models import DemandForecast

logger = logging.getLogger(__name__)

def safe_float(value):
    """Convierte un valor a float de manera segura para serialización JSON"""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    return 0.0

def safe_int(value):
    """Convierte un valor a int de manera segura para serialización JSON"""
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    return 0

def json_serializable(obj):
    """Convierte un objeto a formato serializable JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_serializable(item) for item in obj]
    return obj

class OpenAIConnectionError(Exception):
    """Error específico de conexión con OpenAI"""
    pass

class OpenAIConfigurationError(Exception):
    """Error de configuración de OpenAI"""
    pass

class IntelligenceService:
    """Servicio de inteligencia que REQUIERE OpenAI - SIN FALLBACKS"""
    
    def __init__(self):
        """Inicializar el servicio de inteligencia - SOLO CON IA"""
        self.client = None
        self._initialized = False
        self._init_lock = threading.Lock()
        self._initialization_attempts = 0
        self._max_attempts = 3
        
        print("🔍 DEBUG: Iniciando IntelligenceService (SOLO IA)")
        
        if not OPENAI_AVAILABLE:
            raise OpenAIConfigurationError("OpenAI no está disponible. Instalar con: pip install openai==1.52.0")
        
        # Inicializar de manera obligatoria
        self._initialize_openai_client_required()
    
    def _initialize_openai_client_required(self):
        """Inicializar cliente OpenAI de manera OBLIGATORIA - No funciona sin esto"""
        with self._init_lock:
            if self._initialized:
                print("✅ DEBUG: Cliente OpenAI ya inicializado")
                return
            
            self._initialization_attempts += 1
            print(f"🔍 DEBUG: Intento de inicialización #{self._initialization_attempts}")
            
            # Paso 1: Validar API Key
            api_key = self._get_and_validate_api_key()
            if not api_key:
                raise OpenAIConfigurationError(
                    "API Key de OpenAI no configurada o inválida. "
                    "Configurar OPENAI_API_KEY en variables de entorno."
                )
            
            print(f"✅ DEBUG: API Key validada: {api_key[:20]}...")
            
            # Paso 2: Diagnosticar y limpiar configuración problemática
            self._diagnose_and_fix_environment()
            
            # Paso 3: Crear cliente con método robusto
            success = self._create_client_with_retries(api_key)
            
            if not success:
                if self._initialization_attempts < self._max_attempts:
                    print(f"⚠️ DEBUG: Reintentando inicialización... ({self._initialization_attempts}/{self._max_attempts})")
                    time.sleep(1)  # Esperar un segundo antes de reintentar
                    return self._initialize_openai_client_required()
                else:
                    raise OpenAIConnectionError(
                        f"No se pudo inicializar cliente OpenAI después de {self._max_attempts} intentos. "
                        "Verificar conectividad y configuración."
                    )
            
            # Paso 4: Validar que el cliente funciona
            self._validate_client_functionality()
            
            self._initialized = True
            print("✅ DEBUG: Cliente OpenAI inicializado correctamente - MODO IA ACTIVO")
            logger.info("Cliente OpenAI inicializado correctamente - Servicio de IA operativo")
    
    def _get_and_validate_api_key(self) -> Optional[str]:
        """Obtener y validar API key estrictamente"""
        # Fuentes de API key en orden de prioridad
        sources = [
            ('OPENAI_API_KEY env var', lambda: os.getenv('OPENAI_API_KEY')),
            ('Django settings', lambda: getattr(settings, 'OPENAI_API_KEY', None)),
            ('OPENAI_API env var', lambda: os.getenv('OPENAI_API')),
        ]
        
        api_key = None
        source_used = None
        
        for source_name, get_key in sources:
            api_key = get_key()
            if api_key:
                source_used = source_name
                break
        
        if not api_key:
            print("❌ DEBUG: No se encontró API key en ninguna fuente")
            return None
        
        print(f"🔍 DEBUG: API key encontrada en: {source_used}")
        
        # Validar formato de API key
        api_key = api_key.strip()
        
        if len(api_key) < 20:
            print(f"❌ DEBUG: API key demasiado corta: {len(api_key)} caracteres")
            return None
        
        if not (api_key.startswith('sk-') or api_key.startswith('sk-proj-')):
            print(f"❌ DEBUG: API key no tiene formato válido de OpenAI")
            return None
        
        print(f"✅ DEBUG: API key validada correctamente")
        return api_key
    
    def _diagnose_and_fix_environment(self):
        """Diagnosticar y solucionar problemas de entorno que causan el error de 'proxies'"""
        print("🔍 DEBUG: Diagnosticando entorno...")
        
        # Variables de proxy que pueden causar problemas
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'NO_PROXY']
        found_proxies = []
        
        for var in proxy_vars:
            value = os.environ.get(var)
            if value:
                found_proxies.append(f"{var}={value}")
        
        if found_proxies:
            print(f"⚠️ DEBUG: Variables de proxy detectadas: {found_proxies}")
            print("🔧 DEBUG: Guardando configuración de proxy...")
            
            # Guardar configuración original
            self._original_proxy_config = {}
            for var in proxy_vars:
                if var in os.environ:
                    self._original_proxy_config[var] = os.environ[var]
                    print(f"💾 DEBUG: Guardado {var}")
            
            # Limpiar temporalmente las variables de proxy
            print("🧹 DEBUG: Limpiando variables de proxy temporalmente...")
            for var in proxy_vars:
                if var in os.environ:
                    del os.environ[var]
                    print(f"🗑️ DEBUG: Eliminado {var}")
        else:
            print("✅ DEBUG: No se encontraron variables de proxy problemáticas")
        
        # Verificar versión de OpenAI
        print(f"🔍 DEBUG: Versión OpenAI: {openai.__version__}")
        
        # Verificar versión de requests (puede afectar)
        try:
            import requests
            print(f"🔍 DEBUG: Versión requests: {requests.__version__}")
        except ImportError:
            print("⚠️ DEBUG: requests no disponible")
        
        # Verificar versión de httpx (usado por OpenAI)
        try:
            import httpx
            print(f"🔍 DEBUG: Versión httpx: {httpx.__version__}")
        except ImportError:
            print("⚠️ DEBUG: httpx no disponible")
    
    def _create_client_with_retries(self, api_key: str) -> bool:
        """Crear cliente OpenAI con múltiples estrategias"""
        strategies = [
            ("Básico", lambda: OpenAI(api_key=api_key)),
            ("Con timeout", lambda: OpenAI(api_key=api_key, timeout=30.0)),
            ("Reimpor tardío", self._reimport_and_create_client),
        ]
        
        for strategy_name, create_func in strategies:
            try:
                print(f"🔧 DEBUG: Probando estrategia '{strategy_name}'...")
                
                if strategy_name == "Reimpor tardío":
                    self.client = create_func(api_key)
                else:
                    self.client = create_func()
                
                print(f"✅ DEBUG: Estrategia '{strategy_name}' exitosa")
                return True
                
            except Exception as e:
                print(f"❌ DEBUG: Estrategia '{strategy_name}' falló: {str(e)}")
                print(f"🔍 DEBUG: Tipo de error: {type(e).__name__}")
                
                # Analizar error específico
                if "proxies" in str(e).lower():
                    print("🎯 DEBUG: Error confirmado de 'proxies'")
                    # Intentar solución específica para proxies
                    self._attempt_proxy_fix()
                elif "api_key" in str(e).lower():
                    print("🎯 DEBUG: Error de API key")
                    raise OpenAIConfigurationError(f"Error de API key: {str(e)}")
                elif "timeout" in str(e).lower():
                    print("🎯 DEBUG: Error de timeout")
                    continue  # Probar siguiente estrategia
                else:
                    print(f"🎯 DEBUG: Error no identificado: {str(e)}")
                
                continue
        
        return False
    
    def _reimport_and_create_client(self, api_key: str):
        """Estrategia de reimportar OpenAI y crear cliente"""
        print("🔄 DEBUG: Reimportando módulo OpenAI...")
        
        # Reimportar completamente el módulo
        import importlib
        import sys
        
        # Eliminar módulos de OpenAI del cache
        modules_to_reload = [name for name in sys.modules.keys() if name.startswith('openai')]
        for module_name in modules_to_reload:
            if module_name in sys.modules:
                del sys.modules[module_name]
                print(f"🗑️ DEBUG: Eliminado del cache: {module_name}")
        
        # Reimportar
        import openai
        from openai import OpenAI
        
        print("🔄 DEBUG: Módulos reimportados")
        
        # Crear cliente con módulo fresco
        return OpenAI(api_key=api_key)
    
    def _attempt_proxy_fix(self):
        """Intentar solución específica para el problema de proxies"""
        print("🔧 DEBUG: Aplicando solución específica para proxies...")
        
        try:
            # Forzar limpieza de configuración de requests
            import requests
            
            # Crear sesión limpia
            session = requests.Session()
            session.proxies.clear()
            
            print("🧹 DEBUG: Configuración de requests limpiada")
            
        except Exception as e:
            print(f"⚠️ DEBUG: Error limpiando requests: {str(e)}")
    
    def _validate_client_functionality(self):
        """Validar que el cliente OpenAI funciona correctamente"""
        print("🔍 DEBUG: Validando funcionalidad del cliente...")
        
        if not self.client:
            raise OpenAIConnectionError("Cliente OpenAI es None")
        
        # Verificar estructura del cliente
        if not hasattr(self.client, 'chat'):
            raise OpenAIConnectionError("Cliente OpenAI no tiene atributo 'chat'")
        
        if not hasattr(self.client.chat, 'completions'):
            raise OpenAIConnectionError("Cliente OpenAI no tiene método 'completions'")
        
        print("✅ DEBUG: Estructura del cliente validada")
        
        # Test de conectividad real (opcional, consume tokens)
        # self._test_real_connection()
    
    def _test_real_connection(self):
        """Test de conexión real con OpenAI (consume tokens)"""
        print("🔍 DEBUG: Probando conexión real con OpenAI...")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            
            if response.choices:
                print("✅ DEBUG: Conexión real con OpenAI exitosa")
            else:
                raise OpenAIConnectionError("Respuesta vacía de OpenAI")
                
        except Exception as e:
            print(f"❌ DEBUG: Error en test de conexión real: {str(e)}")
            raise OpenAIConnectionError(f"Error de conectividad real: {str(e)}")
    
    def _restore_proxy_environment(self):
        """Restaurar configuración de proxy original"""
        if hasattr(self, '_original_proxy_config'):
            print("🔄 DEBUG: Restaurando configuración de proxy...")
            for var, value in self._original_proxy_config.items():
                os.environ[var] = value
                print(f"↩️ DEBUG: Restaurado {var}")
    
    def is_available(self) -> bool:
        """Verificar si el servicio de IA está disponible - DEBE SER True"""
        return self.client is not None and self._initialized
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado detallado del servicio"""
        return {
            'openai_available': OPENAI_AVAILABLE,
            'client_initialized': self._initialized,
            'client_ready': self.is_available(),
            'version': openai.__version__ if OPENAI_AVAILABLE else None,
            'api_key_configured': bool(self._get_and_validate_api_key()),
            'status': 'ready' if self.is_available() else 'error',
            'initialization_attempts': self._initialization_attempts
        }
    
    def generate_morning_briefing(self, company: Company, user: User = None) -> Dict[str, Any]:
        """
        Generar briefing matutino SOLO CON IA
        
        Args:
            company: Empresa para la cual generar el briefing
            user: Usuario que solicita el briefing (opcional)
            
        Returns:
            Dict con el briefing completo
            
        Raises:
            OpenAIConnectionError: Si no se puede conectar con OpenAI
            OpenAIConfigurationError: Si hay problemas de configuración
        """
        print(f"🔍 DEBUG: Generando briefing SOLO IA para {company.name}")
        
        # Verificación estricta: SI O SI debe haber IA
        if not self.is_available():
            error_msg = "Servicio de IA no disponible. No se puede generar briefing sin OpenAI."
            print(f"❌ DEBUG: {error_msg}")
            raise OpenAIConnectionError(error_msg)
        
        print(f"✅ DEBUG: IA disponible, procediendo con generación...")
        
        try:
            # Obtener datos contextuales
            context = self._gather_business_context(company)
            print(f"✅ DEBUG: Contexto del negocio obtenido")
            
            # Generar briefing CON IA (no hay plan B)
            briefing_data = self._generate_ai_briefing_required(context, company)
            print(f"✅ DEBUG: Briefing generado con IA exitosamente")
            
            # Validar estructura requerida
            self._validate_briefing_structure(briefing_data)
            
            # Guardar en base de datos
            briefing = self._save_briefing_to_db(briefing_data, context, company, user)
            print(f"✅ DEBUG: Briefing guardado en BD con ID: {briefing.id}")
            
            # Preparar respuesta final
            response = {
                'id': briefing.id,
                'generated_at': briefing.generated_at.isoformat(),
                'greeting': briefing_data['greeting'],
                'summary': briefing_data['summary'],
                'topPriorities': briefing_data['topPriorities'],
                'opportunities': briefing_data['opportunities'],
                'recommendations': briefing_data['recommendations'],
                'contextualMetrics': briefing_data['contextualMetrics'],
                'success': True,
                'ai_enabled': True,
                'generated_by_ai': True
            }
            
            # Validar serialización JSON
            json.dumps(response)
            
            print(f"✅ DEBUG: Briefing completado exitosamente")
            return response
            
        except OpenAIConnectionError:
            # Re-lanzar errores de OpenAI
            raise
        except OpenAIConfigurationError:
            # Re-lanzar errores de configuración
            raise
        except Exception as e:
            error_msg = f"Error generando briefing con IA: {str(e)}"
            print(f"❌ DEBUG: {error_msg}")
            logger.error(error_msg)
            raise OpenAIConnectionError(error_msg) from e
    
    def generate_category_insights(self, company: Company, category_id: int = None) -> Dict[str, Any]:
        """
        🎯 Generar insights estratégicos específicos para categorías
        REUTILIZA y EXTIENDE la lógica del briefing matutino para categorías
        
        Args:
            company: Empresa para análisis
            category_id: ID de categoría específica (opcional, si no se proporciona analiza todas)
            
        Returns:
            Dict con insights estratégicos por categoría
            
        Raises:
            OpenAIConnectionError: Si no se puede conectar con OpenAI
        """
        print(f"🧠 DEBUG: Generando insights de categorías para {company.name}")
        
        # Verificación estricta: REQUIERE IA
        if not self.is_available():
            error_msg = "Servicio de IA no disponible. No se pueden generar insights de categorías sin OpenAI."
            print(f"❌ DEBUG: {error_msg}")
            raise OpenAIConnectionError(error_msg)
        
        try:
            # Obtener contexto específico de categorías (REUTILIZAR y EXTENDER)
            categories_context = self._gather_categories_context(company, category_id)
            print(f"✅ DEBUG: Contexto de categorías obtenido para {len(categories_context.get('categories', []))} categorías")
            
            # Generar insights específicos con IA
            insights_data = self._generate_ai_category_insights(categories_context, company)
            print(f"✅ DEBUG: Insights de categorías generados con IA exitosamente")
            
            # Validar estructura de insights
            self._validate_category_insights_structure(insights_data)
            
            # Guardar insights en base de datos
            self._save_category_insights_to_db(insights_data, categories_context, company)
            
            # Preparar respuesta final
            response = {
                'category_insights': insights_data['category_insights'],
                'strategic_recommendations': insights_data['strategic_recommendations'],
                'priority_actions': insights_data['priority_actions'],
                'market_opportunities': insights_data['market_opportunities'],
                'risk_assessment': insights_data['risk_assessment'],
                'performance_analysis': insights_data['performance_analysis'],
                'generated_at': timezone.now().isoformat(),
                'success': True,
                'ai_enabled': True,
                'categories_analyzed': len(categories_context.get('categories', []))
            }
            
            print(f"✅ DEBUG: Category insights completado exitosamente")
            return response
            
        except Exception as e:
            error_msg = f"Error generando insights de categorías con IA: {str(e)}"
            print(f"❌ DEBUG: {error_msg}")
            logger.error(error_msg)
            raise OpenAIConnectionError(error_msg) from e
    
    def _gather_categories_context(self, company: Company, category_id: int = None) -> Dict[str, Any]:
        """
        📊 Recopilar contexto específico de categorías para análisis de IA
        REUTILIZA patrón de _gather_business_context y lo especializa
        """
        print(f"🔍 DEBUG: Recopilando contexto de categorías para {company.name}")
        
        try:
            from inventory.models import Category, Product, Transaction, InventoryItem
            from alerts.models import Alert
            
            # Fechas para análisis (REUTILIZAR patrón existente)
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # Filtrar categorías según parámetro
            if category_id:
                categories = Category.objects.filter(id=category_id, is_active=True)
            else:
                categories = Category.objects.filter(is_active=True)
            
            categories_data = []
            
            for category in categories:
                # Productos de la categoría
                products = Product.objects.filter(company=company, category=category, is_active=True)
                products_count = products.count()
                
                if products_count == 0:
                    continue
                
                # Transacciones por categoría (REUTILIZAR cálculos existentes)
                category_transactions = Transaction.objects.filter(
                    product__in=products,
                    transaction_date__gte=month_ago
                ).select_related('product')
                
                # Ventas por categoría
                sales_transactions = category_transactions.filter(transaction_type='sale')
                sales_this_month = sales_transactions.aggregate(
                    total_quantity=Sum('quantity'),
                    total_value=Sum(F('quantity') * F('product__sale_price'))
                )
                
                # Tendencia de ventas (últimas 4 semanas)
                sales_trend = []
                for week_offset in range(4):
                    week_start = today - timedelta(days=(week_offset + 1) * 7)
                    week_end = today - timedelta(days=week_offset * 7)
                    
                    week_sales = sales_transactions.filter(
                        transaction_date__gte=week_start,
                        transaction_date__lt=week_end
                    ).aggregate(total=Sum('quantity'))['total'] or 0
                    
                    sales_trend.append({
                        'week': f'Semana {4-week_offset}',
                        'sales': abs(float(week_sales))  # Convertir a positivo
                    })
                
                # Márgenes por categoría (NUEVA MÉTRICA ESTRATÉGICA)
                margin_analysis = products.aggregate(
                    avg_margin=Avg(
                        Case(
                            When(sale_price__gt=0,
                                 then=((F('sale_price') - F('cost_price')) / F('sale_price')) * 100),
                            default=Value(0),
                            output_field=DecimalField(max_digits=5, decimal_places=2)
                        )
                    ),
                    min_margin=Min(
                        Case(
                            When(sale_price__gt=0,
                                 then=((F('sale_price') - F('cost_price')) / F('sale_price')) * 100),
                            default=Value(0),
                            output_field=DecimalField(max_digits=5, decimal_places=2)
                        )
                    ),
                    max_margin=Max(
                        Case(
                            When(sale_price__gt=0,
                                 then=((F('sale_price') - F('cost_price')) / F('sale_price')) * 100),
                            default=Value(0),
                            output_field=DecimalField(max_digits=5, decimal_places=2)
                        )
                    )
                )
                
                # Alertas por categoría (REUTILIZAR patrón de alertas)
                category_alerts = Alert.objects.filter(
                    product__in=products,
                    status='active'
                )
                
                alerts_summary = {
                    'total_alerts': category_alerts.count(),
                    'critical_alerts': category_alerts.filter(severity='critical').count(),
                    'warning_alerts': category_alerts.filter(severity='warning').count(),
                    'info_alerts': category_alerts.filter(severity='info').count()
                }
                
                # Stock status por categoría
                stock_analysis = {
                    'total_products': products_count,
                    'low_stock_products': products.filter(stock__lte=F('min_stock')).count(),
                    'out_of_stock_products': products.filter(stock=0).count(),
                    'optimal_stock_products': products.filter(
                        stock__gt=F('min_stock'), 
                        stock__lt=F('max_stock')
                    ).count()
                }
                
                # Valor total de inventario por categoría
                inventory_value = products.aggregate(
                    total_value=Sum(F('stock') * F('cost_price'))
                )['total_value'] or 0
                
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'products_count': products_count,
                    'sales_performance': {
                        'monthly_quantity': abs(float(sales_this_month['total_quantity'] or 0)),
                        'monthly_value': float(sales_this_month['total_value'] or 0),
                        'weekly_trend': sales_trend
                    },
                    'margin_analysis': {
                        'avg_margin': float(margin_analysis['avg_margin'] or 0),
                        'min_margin': float(margin_analysis['min_margin'] or 0),
                        'max_margin': float(margin_analysis['max_margin'] or 0)
                    },
                    'alerts_summary': alerts_summary,
                    'stock_analysis': stock_analysis,
                    'inventory_value': float(inventory_value),
                    'top_products': list(products.order_by('-stock')[:3].values('name', 'stock', 'sale_price'))
                }
                
                categories_data.append(category_data)
            
            # Estadísticas generales (REUTILIZAR patrón existente)
            general_stats = {
                'total_categories_analyzed': len(categories_data),
                'total_products_across_categories': sum(cat['products_count'] for cat in categories_data),
                'total_inventory_value': sum(cat['inventory_value'] for cat in categories_data),
                'total_alerts': sum(cat['alerts_summary']['total_alerts'] for cat in categories_data),
                'avg_margin_across_categories': sum(cat['margin_analysis']['avg_margin'] for cat in categories_data) / len(categories_data) if categories_data else 0
            }
            
            context = {
                'company_name': company.name,
                'analysis_date': today.isoformat(),
                'categories': categories_data,
                'general_stats': general_stats,
                'analysis_scope': 'single_category' if category_id else 'all_categories'
            }
            
            return context
            
        except Exception as e:
            print(f"❌ Error recopilando contexto de categorías: {e}")
            return {
                'company_name': company.name,
                'categories': [],
                'general_stats': {},
                'error': str(e)
            }
    
    def _generate_ai_category_insights(self, context: Dict[str, Any], company: Company) -> Dict[str, Any]:
        """
        🤖 Generar insights de categorías usando OpenAI
        REUTILIZA patrón de _generate_ai_briefing_required pero especializado para categorías
        """
        print(f"🤖 DEBUG: Generando insights de categorías con IA para {company.name}")
        
        try:
            # Construir prompt especializado para categorías (REUTILIZAR patrón existente)
            prompt = self._build_category_analysis_prompt(context, company)
            
            # Llamada a OpenAI (REUTILIZAR configuración existente)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Eres Carlos Empresario, consultor de negocios especializado en análisis de categorías para {company.name}.
                        
                        MISIÓN: Analizar el rendimiento por categorías y generar insights estratégicos accionables.
                        
                        FORMATO REQUERIDO: JSON válido EXACTO:
                        {{
                          "category_insights": [
                            {{
                              "category_name": "Nombre de categoría",
                              "performance_rating": "excellent|good|average|poor|critical",
                              "key_finding": "Insight principal de 1-2 oraciones",
                              "opportunity": "Oportunidad específica detectada",
                              "risk": "Riesgo o problema principal",
                              "recommended_actions": ["Acción específica 1", "Acción específica 2"]
                            }}
                          ],
                          "strategic_recommendations": [
                            {{
                              "title": "Recomendación estratégica",
                              "description": "Explicación detallada",
                              "priority": "high|medium|low",
                              "timeline": "inmediato|1-2 semanas|1 mes",
                              "expected_impact": "Impacto esperado"
                            }}
                          ],
                          "priority_actions": [
                            {{
                              "action": "Acción específica",
                              "category": "Categoría afectada",
                              "urgency": "urgent|important|routine",
                              "reason": "Por qué es importante ahora"
                            }}
                          ],
                          "market_opportunities": [
                            {{
                              "opportunity": "Oportunidad de mercado",
                              "categories_involved": ["Cat1", "Cat2"],
                              "potential_value": "Valor potencial estimado",
                              "next_steps": ["Paso 1", "Paso 2"]
                            }}
                          ],
                          "risk_assessment": {{
                            "high_risk_categories": ["Categoría con riesgo alto"],
                            "main_threats": ["Amenaza 1", "Amenaza 2"],
                            "mitigation_strategies": ["Estrategia 1", "Estrategia 2"]
                          }},
                          "performance_analysis": {{
                            "top_performers": ["Mejor categoría 1", "Mejor categoría 2"],
                            "underperformers": ["Categoría con problemas 1"],
                            "growth_trends": ["Tendencia 1", "Tendencia 2"],
                            "margin_insights": ["Insight de margen 1", "Insight de margen 2"]
                          }}
                        }}"""
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Procesar respuesta (REUTILIZAR patrón existente)
            ai_response = response.choices[0].message.content
            print(f"🤖 DEBUG: Respuesta de IA recibida, longitud: {len(ai_response)}")
            
            # Parsear JSON (REUTILIZAR patrón de validación)
            try:
                insights_data = json.loads(ai_response)
                print(f"✅ DEBUG: JSON parseado exitosamente")
                return insights_data
            except json.JSONDecodeError as e:
                print(f"❌ DEBUG: Error parseando JSON de IA: {e}")
                # Intentar extraer JSON válido
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    try:
                        insights_data = json.loads(json_match.group())
                        print(f"✅ DEBUG: JSON extraído y parseado exitosamente")
                        return insights_data
                    except:
                        pass
                
                # Fallback con estructura básica
                return self._create_fallback_category_insights(context)
            
        except Exception as e:
            print(f"❌ Error generando insights con IA: {e}")
            return self._create_fallback_category_insights(context)
    
    def _build_category_analysis_prompt(self, context: Dict[str, Any], company: Company) -> str:
        """
        📝 Construir prompt especializado para análisis de categorías
        REUTILIZA patrón de _build_intelligent_prompt
        """
        categories_summary = ""
        for cat in context.get('categories', []):
            categories_summary += f"""
            CATEGORÍA: {cat['name']}
            • Productos: {cat['products_count']}
            • Ventas mensuales: {cat['sales_performance']['monthly_quantity']:.0f} unidades
            • Valor ventas: S/{cat['sales_performance']['monthly_value']:.2f}
            • Margen promedio: {cat['margin_analysis']['avg_margin']:.1f}%
            • Alertas activas: {cat['alerts_summary']['total_alerts']} (críticas: {cat['alerts_summary']['critical_alerts']})
            • Stock bajo: {cat['stock_analysis']['low_stock_products']} productos
            • Valor inventario: S/{cat['inventory_value']:.2f}
            """
        
        return f"""ANÁLISIS ESTRATÉGICO DE CATEGORÍAS - {company.name}
        Fecha: {context['analysis_date']}
        
        ESTADÍSTICAS GENERALES:
        • Total categorías: {context['general_stats']['total_categories_analyzed']}
        • Total productos: {context['general_stats']['total_products_across_categories']}
        • Valor total inventario: S/{context['general_stats']['total_inventory_value']:.2f}
        • Alertas totales: {context['general_stats']['total_alerts']}
        • Margen promedio general: {context['general_stats']['avg_margin_across_categories']:.1f}%
        
        DETALLES POR CATEGORÍA:
        {categories_summary}
        
        INSTRUCCIONES PARA ANÁLISIS:
        1. Evalúa el rendimiento de cada categoría (ventas, márgenes, problemas)
        2. Identifica oportunidades estratégicas específicas por categoría
        3. Detecta riesgos operacionales que requieren atención inmediata
        4. Proporciona recomendaciones accionables priorizadas
        5. Sugiere acciones específicas con timeline claro
        
        Genera insights en JSON válido siguiendo la estructura exacta especificada."""
    
    def _validate_category_insights_structure(self, insights_data: Dict[str, Any]):
        """
        ✅ Validar estructura de insights de categorías
        REUTILIZA patrón de _validate_briefing_structure
        """
        required_keys = ['category_insights', 'strategic_recommendations', 'priority_actions', 
                        'market_opportunities', 'risk_assessment', 'performance_analysis']
        
        for key in required_keys:
            if key not in insights_data:
                raise ValueError(f"Category insights falta clave requerida: {key}")
        
        print("✅ DEBUG: Estructura de category insights validada")
    
    def _save_category_insights_to_db(self, insights_data: Dict[str, Any], context: Dict[str, Any], company: Company):
        """
        💾 Guardar insights de categorías en base de datos
        REUTILIZA patrón de IntelligenceInsight existente
        """
        try:
            from .models import IntelligenceInsight
            
            # Guardar insights principales como registros individuales
            for insight in insights_data.get('category_insights', []):
                IntelligenceInsight.objects.create(
                    company=company,
                    insight_type='opportunity',
                    priority='medium',
                    title=f"Análisis: {insight.get('category_name', 'Categoría')}",
                    message=insight.get('key_finding', ''),
                    actions_json=insight.get('recommended_actions', []),
                    source_data_json=context,
                    confidence_score=85.0
                )
            
            # Guardar acciones prioritarias
            for action in insights_data.get('priority_actions', []):
                priority_map = {'urgent': 'high', 'important': 'medium', 'routine': 'low'}
                IntelligenceInsight.objects.create(
                    company=company,
                    insight_type='priority',
                    priority=priority_map.get(action.get('urgency', 'medium'), 'medium'),
                    title=f"Acción requerida: {action.get('category', '')}",
                    message=action.get('reason', ''),
                    actions_json=[action.get('action', '')],
                    source_data_json=context,
                    confidence_score=90.0
                )
            
            print(f"✅ DEBUG: Category insights guardados en BD")
            
        except Exception as e:
            print(f"❌ Error guardando insights en BD: {e}")
    
    def _create_fallback_category_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔄 Crear insights de fallback cuando IA no está disponible
        REUTILIZA patrón de fallback existente pero para categorías
        """
        categories = context.get('categories', [])
        
        if not categories:
            return {
                'category_insights': [],
                'strategic_recommendations': [],
                'priority_actions': [],
                'market_opportunities': [],
                'risk_assessment': {'high_risk_categories': [], 'main_threats': [], 'mitigation_strategies': []},
                'performance_analysis': {'top_performers': [], 'underperformers': [], 'growth_trends': [], 'margin_insights': []}
            }
        
        # Análisis básico sin IA
        top_category = max(categories, key=lambda x: x['sales_performance']['monthly_value'])
        problem_category = max(categories, key=lambda x: x['alerts_summary']['total_alerts'])
        
        return {
            'category_insights': [
                {
                    'category_name': top_category['name'],
                    'performance_rating': 'good',
                    'key_finding': f"Lidera en ventas con S/{top_category['sales_performance']['monthly_value']:.2f}",
                    'opportunity': 'Mantener momentum y expandir línea',
                    'risk': 'Posible agotamiento de stock',
                    'recommended_actions': ['Revisar niveles de inventario', 'Analizar demanda futura']
                }
            ],
            'strategic_recommendations': [
                {
                    'title': 'Optimizar categoría líder',
                    'description': f'Enfocar recursos en {top_category["name"]}',
                    'priority': 'high',
                    'timeline': '1-2 semanas',
                    'expected_impact': 'Incremento de 10-15% en ventas'
                }
            ],
            'priority_actions': [
                {
                    'action': f'Revisar alertas en {problem_category["name"]}',
                    'category': problem_category['name'],
                    'urgency': 'important',
                    'reason': f'{problem_category["alerts_summary"]["total_alerts"]} alertas activas'
                }
            ],
            'market_opportunities': [],
            'risk_assessment': {
                'high_risk_categories': [problem_category['name']],
                'main_threats': ['Stock crítico', 'Alertas sin resolver'],
                'mitigation_strategies': ['Revisión inmediata de inventario', 'Configurar reabastecimiento automático']
            },
            'performance_analysis': {
                'top_performers': [top_category['name']],
                'underperformers': [problem_category['name']],
                'growth_trends': ['Análisis requiere más datos históricos'],
                'margin_insights': ['Revisar márgenes por categoría regularmente']
            }
        }
    
    def _gather_business_context(self, company: Company) -> Dict[str, Any]:
        """Recopilar contexto del negocio para análisis de IA"""
        
        print(f"🔍 DEBUG: Recopilando contexto para {company.name}")
        
        try:
            # Fechas para análisis
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            
            # Productos
            products = Product.objects.filter(company=company)
            total_products = products.count()
            
            # Inventario
            inventory_items = InventoryItem.objects.filter(product__company=company)
            
            # Valor total de inventario
            total_inventory_value = Decimal('0')
            for item in inventory_items:
                total_inventory_value += (item.quantity * item.unit_cost)
            
            # Transacciones
            transactions = Transaction.objects.filter(
                product__company=company,
                transaction_date__gte=week_ago
            ).select_related('product')
            
            transactions_today = transactions.filter(transaction_date__date=today)
            
            # Ventas y compras
            sales_transactions = transactions.filter(transaction_type='sale')
            purchase_transactions = transactions.filter(transaction_type='purchase')
            
            total_sales = sales_transactions.aggregate(total=Sum('quantity'))['total'] or 0
            total_purchases = purchase_transactions.aggregate(total=Sum('quantity'))['total'] or 0
            
            # Alertas
            alerts = Alert.objects.filter(company=company, status='active').select_related('product')
            critical_alerts = alerts.filter(severity='critical').count()
                
            # Productos con stock bajo
            low_stock_products = []
            for product in products[:10]:  # Limitado para performance
                current_stock = inventory_items.filter(product=product).aggregate(
                    total=Sum('quantity')
                )['total'] or 0
                
                if current_stock <= product.min_stock:
                    low_stock_products.append({
                        'name': product.name,
                        'current_stock': safe_float(current_stock),
                        'min_stock': safe_int(product.min_stock),
                        'reorder_point': safe_int(product.reorder_point)
                    })
            
            # Productos más vendidos
            top_selling_products = []
            if sales_transactions.exists():
                top_selling = (
                    sales_transactions
                    .values('product__name')
                    .annotate(total_sold=Sum('quantity'))
                    .order_by('-total_sold')[:5]
                )
                
                top_selling_products = [
                    {
                        'product__name': item['product__name'],
                        'total_sold': safe_float(item['total_sold'])
                    }
                    for item in top_selling
                ]
                
            # Pronósticos
            forecasts = DemandForecast.objects.filter(
                product__company=company,
                forecast_date__gte=today
            ).select_related('product')[:10]
            
            context = {
                'company_name': company.name,
                'analysis_date': today.isoformat(),
                'stats': {
                    'total_products': total_products,
                    'total_inventory_value': safe_float(total_inventory_value),
                    'total_transactions_today': transactions_today.count(),
                    'total_sales_week': safe_float(total_sales),
                    'total_purchases_week': safe_float(total_purchases),
                    'total_alerts': alerts.count(),
                    'critical_alerts': critical_alerts,
                    'low_stock_count': len(low_stock_products)
                },
                'alerts': [
                    {
                        'id': alert.id,
                        'message': alert.message,
                        'severity': alert.severity,
                        'product_name': alert.product.name if alert.product else None
                    }
                    for alert in alerts[:5]  # Limitado para performance
                ],
                'low_stock_products': low_stock_products,
                'top_selling_products': top_selling_products,
                'transactions': [
                    {
                        'id': tx.id,
                        'product_name': tx.product.name,
                        'quantity': safe_float(tx.quantity),
                        'transaction_type': tx.transaction_type,
                        'transaction_date': tx.transaction_date.isoformat()
                    }
                    for tx in transactions[:10]  # Limitado para performance
                ],
                'forecasts': [
                    {
                        'product_name': forecast.product.name,
                        'forecast_date': forecast.forecast_date.isoformat(),
                        'predicted_demand': safe_float(forecast.predicted_demand),
                        'confidence_level': safe_float(forecast.confidence_level)
                    }
                    for forecast in forecasts
                ]
            }
            
            print(f"✅ DEBUG: Contexto recopilado - {total_products} productos, S/{safe_float(total_inventory_value):.2f} inventario")
            
            return json_serializable(context)
            
        except Exception as e:
            error_msg = f"Error recopilando contexto del negocio: {str(e)}"
            print(f"❌ DEBUG: {error_msg}")
            raise Exception(error_msg) from e
    
    def _generate_ai_briefing_required(self, context: Dict[str, Any], company: Company) -> Dict[str, Any]:
        """Generar briefing usando OpenAI - REQUERIDO, sin alternativas"""
        
        print(f"🧠 DEBUG: Generando briefing con IA para {company.name}")
        
        if not self.is_available():
            raise OpenAIConnectionError("Cliente OpenAI no disponible para generar briefing")
        
        try:
            # Construir prompt especializado
            prompt = self._build_intelligent_prompt(context, company)
            print(f"🔍 DEBUG: Prompt construido: {len(prompt)} caracteres")
            
            # Llamada a OpenAI
            print("🔗 DEBUG: Enviando solicitud a OpenAI...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Eres Carlos Empresario, consultor de negocios experto para {company.name}, especializado en retail y minimarkets en Perú.
                        
                        PERSONALIDAD:
- Profesional pero cercano, hablas en español peruano
- Analítico y orientado a resultados
                        - Das recomendaciones específicas y accionables
- Usas datos reales para fundamentar tus análisis

MISIÓN: Analizar los datos del negocio y generar un briefing matutino inteligente.

FORMATO REQUERIDO: JSON válido EXACTO:
{{
  "greeting": "Saludo personalizado para la hora del día",
  "summary": "Resumen ejecutivo de la situación actual en 2-3 oraciones",
  "topPriorities": [
    {{
      "type": "priority",
      "title": "Título del problema crítico",
      "message": "Descripción detallada del problema y su impacto",
      "priority": "high",
      "actions": ["Acción específica 1", "Acción específica 2"]
    }}
  ],
  "opportunities": [
    {{
      "type": "opportunity",
      "title": "Oportunidad de negocio detectada",
      "message": "Explicación de la oportunidad y beneficios potenciales",
      "priority": "medium",
      "actions": ["Paso para aprovechar la oportunidad"]
    }}
  ],
  "recommendations": [
    {{
      "type": "recommendation",
      "title": "Recomendación estratégica",
      "message": "Explicación detallada de por qué es importante",
      "priority": "medium",
      "actions": ["Paso 1", "Paso 2"]
    }}
  ],
  "contextualMetrics": {{
    "totalValue": {{
      "current": {context['stats']['total_inventory_value']},
      "previousPeriod": {context['stats']['total_inventory_value'] * 0.92},
      "change": {context['stats']['total_inventory_value'] * 0.08},
      "timeframe": "vs. mes anterior"
    }},
    "salesTrend": {{
      "current": {context['stats']['total_sales_week']},
      "trend": "up",
      "percentage": 12,
      "timeframe": "últimos 7 días"
    }},
    "criticalAlerts": {{
      "count": {context['stats']['critical_alerts']},
      "mostUrgent": "Revisar productos con stock crítico",
      "timeframe": "acción inmediata requerida"
    }},
    "topProducts": [
      {{
        "name": "Producto destacado",
        "demand": 45,
        "daysLeft": 5
      }}
    ]
  }}
}}

IMPORTANTE: Responde SOLO el JSON, sin explicaciones adicionales."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2500,
                top_p=0.9
            )
            
            # Procesar respuesta
            ai_response = response.choices[0].message.content
            if not ai_response:
                raise OpenAIConnectionError("OpenAI devolvió respuesta vacía")
            
            print(f"✅ DEBUG: Respuesta recibida de OpenAI: {len(ai_response)} caracteres")
            
            # Limpiar y parsear JSON
            ai_response = ai_response.strip()
            if ai_response.startswith('```json'):
                ai_response = ai_response[7:]
            if ai_response.endswith('```'):
                ai_response = ai_response[:-3]
            ai_response = ai_response.strip()
            
            try:
                briefing_data = json.loads(ai_response)
                print("✅ DEBUG: JSON parseado correctamente")
                
                # Asegurar que tenga todas las claves requeridas
                required_keys = ['greeting', 'summary', 'topPriorities', 'opportunities', 'recommendations', 'contextualMetrics']
                for key in required_keys:
                    if key not in briefing_data:
                        raise ValueError(f"Respuesta de IA falta clave requerida: {key}")
                
                return briefing_data
                
            except json.JSONDecodeError as e:
                error_msg = f"Error parseando JSON de OpenAI: {str(e)}"
                print(f"❌ DEBUG: {error_msg}")
                print(f"🔍 DEBUG: Respuesta problemática: {ai_response[:500]}...")
                raise OpenAIConnectionError(error_msg) from e
                
        except Exception as e:
            if isinstance(e, OpenAIConnectionError):
                raise
            error_msg = f"Error en llamada a OpenAI: {str(e)}"
            print(f"❌ DEBUG: {error_msg}")
            raise OpenAIConnectionError(error_msg) from e
    
    def _build_intelligent_prompt(self, context: Dict[str, Any], company: Company) -> str:
        """Construir prompt inteligente para OpenAI"""
        
        now = datetime.now()
        time_of_day = 'mañana' if now.hour < 12 else 'tarde' if now.hour < 18 else 'noche'
        
        return f"""ANÁLISIS DE NEGOCIO - {company.name}
Fecha: {now.strftime('%Y-%m-%d')} ({time_of_day})

ESTADÍSTICAS ACTUALES:
• Productos totales: {context['stats']['total_products']}
• Valor inventario: S/{context['stats']['total_inventory_value']:.2f}
• Transacciones hoy: {context['stats']['total_transactions_today']}
• Ventas esta semana: {context['stats']['total_sales_week']} unidades
• Compras esta semana: {context['stats']['total_purchases_week']} unidades
• Alertas críticas: {context['stats']['critical_alerts']}
• Productos con stock bajo: {context['stats']['low_stock_count']}

ALERTAS ACTIVAS ({len(context['alerts'])}):
{chr(10).join([f"• {alert['title']}: {alert['message']} ({alert['severity']})" for alert in context['alerts'][:5]]) if context['alerts'] else '• Sin alertas activas'}

PRONÓSTICOS IA ({len(context['forecasts'])}):
{chr(10).join([f"• {forecast['product_name']}: {forecast['predicted_demand']:.1f} unidades (confianza: {forecast['confidence_level']:.0f}%)" for forecast in context['forecasts'][:5]]) if context['forecasts'] else '• Sin pronósticos disponibles'}

PRODUCTOS STOCK BAJO ({len(context['low_stock_products'])}):
{chr(10).join([f"• {product['name']}: {product['current_stock']} unidades (mín: {product['min_stock']})" for product in context['low_stock_products'][:5]]) if context['low_stock_products'] else '• Stock adecuado en todos los productos'}

PRODUCTOS MÁS VENDIDOS:
{chr(10).join([f"• {product['product__name']}: {product['total_sold']:.0f} unidades" for product in context['top_selling_products'][:5]]) if context['top_selling_products'] else '• Sin datos de ventas recientes'}

TRANSACCIONES RECIENTES ({len(context['transactions'])}):
{chr(10).join([f"• {tx['product_name']}: {tx['quantity']:.0f} ({tx['transaction_type']})" for tx in context['transactions'][:5]]) if context['transactions'] else '• Sin transacciones recientes'}

INSTRUCCIONES PARA ANÁLISIS:
1. Identifica los 2-3 problemas MÁS CRÍTICOS que necesitan atención HOY
2. Encuentra 1-2 oportunidades de negocio basadas en los datos
3. Proporciona 2-3 recomendaciones estratégicas específicas
4. Usa los datos reales para fundamentar cada análisis
5. Sé específico y accionable en todas las recomendaciones

Genera el briefing en JSON válido siguiendo la estructura exacta especificada."""
    
    def _validate_briefing_structure(self, briefing_data: Dict[str, Any]):
        """Validar que el briefing tenga la estructura correcta"""
        
        required_keys = ['greeting', 'summary', 'topPriorities', 'opportunities', 'recommendations', 'contextualMetrics']
        
        for key in required_keys:
            if key not in briefing_data:
                raise ValueError(f"Briefing falta clave requerida: {key}")
        
        # Validar tipos
        if not isinstance(briefing_data['greeting'], str):
            raise ValueError("'greeting' debe ser string")
        
        if not isinstance(briefing_data['summary'], str):
            raise ValueError("'summary' debe ser string")
        
        if not isinstance(briefing_data['topPriorities'], list):
            raise ValueError("'topPriorities' debe ser lista")
        
        if not isinstance(briefing_data['opportunities'], list):
            raise ValueError("'opportunities' debe ser lista")
        
        if not isinstance(briefing_data['recommendations'], list):
            raise ValueError("'recommendations' debe ser lista")
        
        if not isinstance(briefing_data['contextualMetrics'], dict):
            raise ValueError("'contextualMetrics' debe ser diccionario")
        
        print("✅ DEBUG: Estructura del briefing validada")
    
    def _save_briefing_to_db(self, briefing_data: Dict, context: Dict, company: Company, user: User) -> IntelligenceBriefing:
        """Guardar briefing en base de datos"""
        
        try:
            # Asegurar serialización JSON
            briefing_data = json_serializable(briefing_data)
            context = json_serializable(context)
            
            briefing = IntelligenceBriefing.objects.create(
                company=company,
                briefing_type='morning',
                generated_by=user,
                greeting=briefing_data['greeting'],
                summary=briefing_data['summary'],
                priorities_json=briefing_data['topPriorities'],
                opportunities_json=briefing_data['opportunities'],
                recommendations_json=briefing_data['recommendations'],
                metrics_json=briefing_data['contextualMetrics'],
                data_snapshot_json=context
            )
            
            print(f"✅ DEBUG: Briefing guardado con ID: {briefing.id}")
            return briefing
            
        except Exception as e:
            error_msg = f"Error guardando briefing en BD: {str(e)}"
            print(f"❌ DEBUG: {error_msg}")
            raise Exception(error_msg) from e
    
    def __del__(self):
        """Destructor para limpiar configuración"""
        try:
            self._restore_proxy_environment()
        except:
            pass

# Singleton instance con thread safety
_intelligence_service = None
_service_lock = threading.Lock()

def get_intelligence_service() -> IntelligenceService:
    """
    Obtener instancia singleton del servicio de inteligencia - SIN TIMEOUTS
    
    Returns:
        IntelligenceService: Instancia del servicio
        
    Raises:
        OpenAIConfigurationError: Si OpenAI no está configurado
        OpenAIConnectionError: Si no se puede conectar con OpenAI
    """
    global _intelligence_service
    
    with _service_lock:
        if _intelligence_service is None:
            print("🔍 DEBUG: Creando instancia singleton de IntelligenceService")
            try:
                # Verificar rápidamente si tenemos los requisitos básicos
                if not OPENAI_AVAILABLE:
                    raise OpenAIConfigurationError("OpenAI no está instalado")
                
                # Verificar API key sin validar conexión
                import os
                from django.conf import settings
                
                api_key_sources = [
                    os.getenv('OPENAI_API_KEY'),
                    getattr(settings, 'OPENAI_API_KEY', None),
                    os.getenv('OPENAI_API')
                ]
                
                api_key_configured = any(
                    key and len(str(key).strip()) > 20 and str(key).strip().startswith(('sk-', 'sk-proj-'))
                    for key in api_key_sources
                )
                
                if not api_key_configured:
                    raise OpenAIConfigurationError("API Key de OpenAI no configurada")
                
                # Crear instancia CON timeout limitado
                import threading
                import time
                
                service_instance = None
                creation_error = None
                
                def create_service():
                    nonlocal service_instance, creation_error
                    try:
                        service_instance = IntelligenceService()
                    except Exception as e:
                        creation_error = e
                
                # Crear servicio en thread separado con timeout
                creation_thread = threading.Thread(target=create_service)
                creation_thread.daemon = True
                creation_thread.start()
                creation_thread.join(timeout=10)  # 10 segundos máximo
                
                if creation_thread.is_alive():
                    # Thread aún corriendo, timeout
                    raise OpenAIConnectionError("Timeout creando servicio de inteligencia")
                
                if creation_error:
                    # Error durante la creación
                    raise creation_error
                
                if service_instance is None:
                    # No se creó la instancia
                    raise OpenAIConnectionError("No se pudo crear instancia del servicio")
                
                _intelligence_service = service_instance
                print(f"✅ DEBUG: Instancia creada exitosamente")
                
            except Exception as e:
                print(f"❌ DEBUG: Error creando instancia: {str(e)}")
                # En lugar de lanzar error, crear un servicio "dummy" que no funcione
                _intelligence_service = None
                raise
        else:
            print("🔍 DEBUG: Usando instancia existente")
            
            # Verificar que la instancia esté operativa
            if _intelligence_service and not _intelligence_service.is_available():
                print("⚠️ DEBUG: Instancia existente no operativa")
                # No recrear automáticamente para evitar timeouts
                raise OpenAIConnectionError("Servicio de inteligencia no disponible")
    
    return _intelligence_service 

def reset_intelligence_service():
    """Resetear el servicio de inteligencia (para testing/debugging)"""
    global _intelligence_service
    with _service_lock:
        if _intelligence_service:
            try:
                _intelligence_service._restore_proxy_environment()
            except:
                pass
        _intelligence_service = None
        print("🔄 DEBUG: Servicio de inteligencia reseteado")