from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
import logging

from .services import get_intelligence_service, OpenAIConfigurationError, OpenAIConnectionError
from .models import IntelligenceBriefing, IntelligenceInsight, IntelligenceMetric
from .serializers import IntelligenceBriefingSerializer, IntelligenceInsightSerializer, IntelligenceMetricSerializer
from authentication.models import Company

logger = logging.getLogger(__name__)

class MorningBriefingView(APIView):
    """Vista para generar briefing matutino inteligente"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtener briefing matutino para la empresa del usuario - SIN TIMEOUTS"""
        try:
            print(f"🔍 DEBUG: MorningBriefingView.get() iniciado")
            print(f"🔍 DEBUG: Usuario: {request.user}")
            
            # Obtener empresa del usuario
            company = request.user.company
            print(f"🔍 DEBUG: Empresa del usuario: {company}")
            
            if not company:
                return Response({
                    'error': 'Usuario no tiene empresa asignada'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar si hay un briefing reciente en cache
            cache_key = f'morning_briefing_{company.id}_{timezone.now().date()}'
            cached_briefing = cache.get(cache_key)
            print(f"🔍 DEBUG: Cache key: {cache_key}")
            print(f"🔍 DEBUG: Cached briefing: {'Sí' if cached_briefing else 'No'}")
            
            if cached_briefing:
                logger.info(f"Devolviendo briefing desde cache para {company.name}")
                return Response(cached_briefing, status=status.HTTP_200_OK)
            
            # Intentar generar nuevo briefing CON timeout
            try:
                print(f"🔍 DEBUG: Obteniendo intelligence_service...")
                intelligence_service = get_intelligence_service()
                print(f"🔍 DEBUG: Intelligence service obtenido: {intelligence_service}")
                print(f"🔍 DEBUG: Generando briefing matutino...")
                briefing_data = intelligence_service.generate_morning_briefing(company, request.user)
                print(f"🔍 DEBUG: Briefing generado: {type(briefing_data)}")
                
                # Guardar en cache por 1 hora
                cache.set(cache_key, briefing_data, timeout=3600)
                
                logger.info(f"Briefing generado exitosamente para {company.name}")
                return Response(briefing_data, status=status.HTTP_200_OK)
                
            except (OpenAIConfigurationError, OpenAIConnectionError) as e:
                # Error de OpenAI, devolver briefing por defecto
                print(f"⚠️ DEBUG: Error de OpenAI: {str(e)}")
                
                default_briefing = {
                    'id': None,
                    'generated_at': timezone.now().isoformat(),
                    'greeting': 'Buen día! El servicio de inteligencia no está disponible.',
                    'summary': 'Para obtener análisis inteligentes, verifica la configuración de OpenAI.',
                    'topPriorities': [],
                    'opportunities': [],
                    'recommendations': [],
                    'contextualMetrics': {},
                    'success': False,
                    'ai_enabled': False,
                    'error': str(e)
                }
                
                return Response(default_briefing, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generando briefing matutino: {str(e)}")
            return Response({
                'error': 'Error interno del servidor',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Generar nuevo briefing forzando regeneración"""
        try:
            company = request.user.company
            if not company:
                return Response({
                    'error': 'Usuario no tiene empresa asignada'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Limpiar cache
            cache_key = f'morning_briefing_{company.id}_{timezone.now().date()}'
            cache.delete(cache_key)
            
            # Generar nuevo briefing
            intelligence_service = get_intelligence_service()
            briefing_data = intelligence_service.generate_morning_briefing(company, request.user)
            
            # Guardar en cache
            cache.set(cache_key, briefing_data, timeout=3600)
            
            logger.info(f"Briefing regenerado exitosamente para {company.name}")
            return Response(briefing_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error regenerando briefing: {str(e)}")
            return Response({
                'error': 'Error interno del servidor',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BriefingHistoryView(APIView):
    """Vista para obtener historial de briefings"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtener historial de briefings para la empresa"""
        try:
            company = request.user.company
            if not company:
                return Response({
                    'error': 'Usuario no tiene empresa asignada'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener parámetros de consulta
            briefing_type = request.query_params.get('type', 'morning')
            limit = int(request.query_params.get('limit', 10))
            
            # Obtener briefings
            briefings = IntelligenceBriefing.objects.filter(
                company=company,
                briefing_type=briefing_type,
                is_active=True
            ).order_by('-generated_at')[:limit]
            
            serializer = IntelligenceBriefingSerializer(briefings, many=True)
            return Response({
                'briefings': serializer.data,
                'count': briefings.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {str(e)}")
            return Response({
                'error': 'Error interno del servidor',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InsightsView(APIView):
    """Vista para manejar insights inteligentes"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtener insights para la empresa"""
        try:
            company = request.user.company
            if not company:
                return Response({
                    'error': 'Usuario no tiene empresa asignada'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener parámetros
            insight_type = request.query_params.get('type', None)
            priority = request.query_params.get('priority', None)
            is_active = request.query_params.get('active', 'true').lower() == 'true'
            limit = int(request.query_params.get('limit', 20))
            
            # Construir filtros
            filters = {
                'company': company,
                'is_active': is_active
            }
            
            if insight_type:
                filters['insight_type'] = insight_type
            if priority:
                filters['priority'] = priority
            
            # Obtener insights
            insights = IntelligenceInsight.objects.filter(**filters).order_by(
                '-priority', '-created_at'
            )[:limit]
            
            serializer = IntelligenceInsightSerializer(insights, many=True)
            return Response({
                'insights': serializer.data,
                'count': insights.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo insights: {str(e)}")
            return Response({
                'error': 'Error interno del servidor',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MetricsView(APIView):
    """Vista para métricas inteligentes"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtener métricas calculadas por IA"""
        try:
            company = request.user.company
            if not company:
                return Response({
                    'error': 'Usuario no tiene empresa asignada'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener parámetros
            metric_type = request.query_params.get('type', None)
            days = int(request.query_params.get('days', 30))
            
            # Calcular fecha límite
            from datetime import timedelta
            date_limit = timezone.now() - timedelta(days=days)
            
            # Construir filtros
            filters = {
                'company': company,
                'calculated_at__gte': date_limit
            }
            
            if metric_type:
                filters['metric_type'] = metric_type
            
            # Obtener métricas
            metrics = IntelligenceMetric.objects.filter(**filters).order_by(
                'metric_type', '-calculated_at'
            )
            
            serializer = IntelligenceMetricSerializer(metrics, many=True)
            return Response({
                'metrics': serializer.data,
                'count': metrics.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {str(e)}")
            return Response({
                'error': 'Error interno del servidor',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Vistas adicionales para funcionalidades específicas
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_intelligence(request):
    """Endpoint para obtener inteligencia del dashboard - SIN TIMEOUTS"""
    try:
        company = request.user.company
        if not company:
            return Response({
                'error': 'Usuario no tiene empresa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener el briefing más reciente SIN inicializar servicio completo
        latest_briefing = IntelligenceBriefing.objects.filter(
            company=company,
            briefing_type='morning',
            is_active=True
        ).order_by('-generated_at').first()
        
        briefing_data = None
        if latest_briefing:
            briefing_data = {
                'id': latest_briefing.id,
                'generated_at': latest_briefing.generated_at.isoformat(),
                'greeting': latest_briefing.greeting,
                'summary': latest_briefing.summary,
                'topPriorities': latest_briefing.priorities[:3],  # Solo top 3
                'opportunities': latest_briefing.opportunities[:2],  # Solo top 2
                'recommendations': latest_briefing.recommendations[:3],  # Solo top 3
                'contextualMetrics': latest_briefing.metrics
            }
        else:
            # Si no hay briefing, devolver datos por defecto sin generar uno nuevo
            briefing_data = {
                'id': None,
                'generated_at': timezone.now().isoformat(),
                'greeting': 'Buen día! Aún no hay briefings generados para tu empresa.',
                'summary': 'Para obtener análisis inteligentes, asegúrate de que OpenAI esté configurado correctamente.',
                'topPriorities': [],
                'opportunities': [],
                'recommendations': [],
                'contextualMetrics': {}
            }
        
        # Obtener insights críticos de manera eficiente
        critical_insights = IntelligenceInsight.objects.filter(
            company=company,
            priority='high',
            is_active=True,
            is_resolved=False
        ).order_by('-created_at')[:5]
        
        insights_data = []
        for insight in critical_insights:
            try:
                insights_data.append({
                    'id': insight.id,
                    'title': insight.title,
                    'message': insight.message,
                    'type': insight.insight_type,
                    'priority': insight.priority,
                    'actions': insight.actions,
                    'created_at': insight.created_at.isoformat()
                })
            except Exception as e:
                logger.warning(f"Error procesando insight {insight.id}: {str(e)}")
                continue
        
        return Response({
            'briefing': briefing_data,
            'criticalInsights': insights_data,
            'success': True,
            'message': 'Datos obtenidos sin inicializar servicio completo'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo inteligencia del dashboard: {str(e)}")
        return Response({
            'briefing': {
                'id': None,
                'generated_at': timezone.now().isoformat(),
                'greeting': 'Error obteniendo briefing',
                'summary': 'Hubo un problema al obtener los datos de inteligencia.',
                'topPriorities': [],
                'opportunities': [],
                'recommendations': [],
                'contextualMetrics': {}
            },
            'criticalInsights': [],
            'success': False,
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resolve_insight(request, insight_id):
    """Marcar insight como resuelto"""
    try:
        company = request.user.company
        if not company:
            return Response({
                'error': 'Usuario no tiene empresa asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        insight = get_object_or_404(
            IntelligenceInsight,
            id=insight_id,
            company=company
        )
        
        insight.is_resolved = True
        insight.resolved_at = timezone.now()
        insight.resolved_by = request.user
        insight.save()
        
        return Response({
            'message': 'Insight marcado como resuelto',
            'success': True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error resolviendo insight: {str(e)}")
        return Response({
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def intelligence_status(request):
    """Obtener estado del servicio de inteligencia - SIN TIMEOUTS"""
    try:
        # Verificar OpenAI sin inicializar el servicio completo
        import os
        from django.conf import settings
        
        # Verificar si OpenAI está instalado
        try:
            import openai
            openai_installed = True
            openai_version = openai.__version__
        except ImportError:
            openai_installed = False
            openai_version = None
        
        # Verificar si API key está configurada (sin validar conexión)
        api_key_sources = [
            os.getenv('OPENAI_API_KEY'),
            getattr(settings, 'OPENAI_API_KEY', None),
            os.getenv('OPENAI_API')
        ]
        
        api_key_configured = any(
            key and len(str(key).strip()) > 20 and str(key).strip().startswith(('sk-', 'sk-proj-'))
            for key in api_key_sources
        )
        
        # Estadísticas básicas sin inicializar el servicio
        company = request.user.company
        stats = {}
        
        if company:
            try:
                # Usar queries simples sin timeout
                from django.db import connection
                connection.queries_limit = 10  # Limitar queries
                
                stats = {
                    'total_briefings': IntelligenceBriefing.objects.filter(company=company).count(),
                    'active_insights': IntelligenceInsight.objects.filter(
                        company=company,
                        is_active=True,
                        is_resolved=False
                    ).count(),
                    'total_metrics': IntelligenceMetric.objects.filter(company=company).count(),
                    'last_briefing': None
                }
                
                # Obtener último briefing de manera más eficiente
                last_briefing = IntelligenceBriefing.objects.filter(
                    company=company
                ).order_by('-generated_at').first()
                
                if last_briefing:
                    stats['last_briefing'] = last_briefing.generated_at.isoformat()
                    
            except Exception as e:
                logger.warning(f"Error obteniendo estadísticas: {str(e)}")
                stats = {
                    'total_briefings': 0,
                    'active_insights': 0,
                    'total_metrics': 0,
                    'last_briefing': None
                }
        
        # Determinar estado del servicio
        if openai_installed and api_key_configured:
            service_status = 'active'  # Cambiar 'ready' a 'active' para coincidir con el frontend
        elif openai_installed and not api_key_configured:
            service_status = 'needs_config'
        elif not openai_installed:
            service_status = 'needs_install'
        else:
            service_status = 'unknown'
        
        return Response({
            'openai_installed': openai_installed,
            'openai_version': openai_version,
            'api_key_configured': api_key_configured,
            'service_status': service_status,
            'stats': stats,
            'success': True,
            'message': 'Estado obtenido sin inicializar servicio completo'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del servicio: {str(e)}")
        return Response({
            'openai_installed': False,
            'api_key_configured': False,
            'service_status': 'error',
            'stats': {},
            'success': False,
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
