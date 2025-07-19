"""
Views para EmailTrackingService API
"""
import json
import logging
from datetime import datetime, timedelta

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from inventory.services.email_tracking_service import (
    EmailTrackingService, 
    get_email_tracking_service,
    send_tracked_email,
    analyze_email_patterns,
    get_email_insights
)
from inventory.models import (
    TrackedEmail, 
    EmailCampaign, 
    EmailClick,
    EmailPattern,
    EmailInsight,
    GmailWebhookLog
)
from authentication.models import Company

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class EmailTrackingPixelView(View):
    """
    Vista para el pixel de tracking de aperturas de email
    """
    
    def get(self, request, tracking_id):
        """Manejar request del pixel de tracking"""
        try:
            # Obtener información del request
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = self._get_client_ip(request)
            
            # Buscar email tracked
            try:
                tracked_email = TrackedEmail.objects.get(tracking_id=tracking_id)
                
                # Marcar como abierto
                tracked_email.mark_as_opened(
                    user_agent=user_agent,
                    ip_address=ip_address
                )
                
                logger.info(f"Email tracking: apertura registrada para {tracking_id}")
                
            except TrackedEmail.DoesNotExist:
                # Usar servicio como fallback
                service = get_email_tracking_service()
                service.track_email_open(tracking_id, user_agent, ip_address)
                logger.info(f"Email tracking: apertura registrada via servicio para {tracking_id}")
            
            # Retornar pixel transparente de 1x1
            pixel_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
            
            response = HttpResponse(pixel_data, content_type='image/png')
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
            
        except Exception as e:
            logger.error(f"Error en tracking pixel: {e}")
            # Retornar pixel vacío incluso en error
            return HttpResponse(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82',
                content_type='image/png'
            )
    
    def _get_client_ip(self, request):
        """Obtener IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@method_decorator(csrf_exempt, name='dispatch')
class EmailClickTrackingView(View):
    """
    Vista para tracking de clicks en emails
    """
    
    def get(self, request, tracking_id):
        """Manejar click en enlace tracked"""
        try:
            # Obtener URL de destino
            target_url = request.GET.get('url')
            if not target_url:
                return JsonResponse({'error': 'URL no proporcionada'}, status=400)
            
            # Obtener información del request
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = self._get_client_ip(request)
            referrer = request.META.get('HTTP_REFERER', '')
            
            # Registrar click
            try:
                tracked_email = TrackedEmail.objects.get(tracking_id=tracking_id)
                
                # Marcar email como clickeado
                tracked_email.mark_as_clicked(user_agent=user_agent, ip_address=ip_address)
                
                # Crear registro de click individual
                EmailClick.objects.create(
                    tracked_email=tracked_email,
                    url=target_url,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    referrer=referrer,
                    clicked_at=timezone.now()
                )
                
                logger.info(f"Email click registrado: {tracking_id} -> {target_url}")
                
            except TrackedEmail.DoesNotExist:
                # Usar servicio como fallback
                service = get_email_tracking_service()
                service.track_email_click(tracking_id, target_url, user_agent, ip_address)
                logger.info(f"Email click registrado via servicio: {tracking_id} -> {target_url}")
            
            # Redirigir a la URL original
            from django.shortcuts import redirect
            return redirect(target_url)
            
        except Exception as e:
            logger.error(f"Error en tracking de click: {e}")
            # Intentar redirigir aunque haya error en tracking
            target_url = request.GET.get('url', 'https://google.com')
            from django.shortcuts import redirect
            return redirect(target_url)
    
    def _get_client_ip(self, request):
        """Obtener IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@method_decorator(csrf_exempt, name='dispatch')
class GmailWebhookView(View):
    """
    Vista para recibir webhooks de Gmail
    """
    
    def post(self, request):
        """Procesar webhook de Gmail"""
        try:
            # Parsear datos del webhook
            webhook_data = json.loads(request.body)
            
            # Obtener company_id del request o usar default
            company_id = request.GET.get('company_id')
            if company_id:
                company = get_object_or_404(Company, id=company_id)
            else:
                # Usar primera company como fallback
                company = Company.objects.first()
                if not company:
                    return JsonResponse({'error': 'No company found'}, status=400)
            
            # Procesar con el servicio
            service = get_email_tracking_service(company.id)
            result = service.process_gmail_webhook(webhook_data)
            
            # Guardar log del webhook
            GmailWebhookLog.objects.create(
                company=company,
                history_id=webhook_data.get('message', {}).get('messageId', ''),
                email_address=request.GET.get('email', 'unknown'),
                raw_payload=webhook_data,
                processed_changes=result.get('changes', []),
                processing_success=result.get('success', False),
                error_message=result.get('error', '')
            )
            
            logger.info(f"Gmail webhook procesado para company {company.id}")
            
            return JsonResponse({
                'success': True,
                'message': 'Webhook procesado exitosamente'
            })
            
        except Exception as e:
            logger.error(f"Error procesando Gmail webhook: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class EmailTrackingAPIView(APIView):
    """
    API principal para EmailTrackingService
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener dashboard de email tracking"""
        try:
            company = request.user.company
            service = get_email_tracking_service(company.id)
            
            dashboard_data = service.get_email_analytics_dashboard()
            
            return Response({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard de email tracking: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def post(self, request):
        """Enviar email tracked"""
        try:
            company = request.user.company
            data = request.data
            
            # Validar datos requeridos
            required_fields = ['to', 'subject', 'body']
            for field in required_fields:
                if field not in data:
                    return Response({
                        'success': False,
                        'error': f'Campo requerido: {field}'
                    }, status=400)
            
            # Enviar email
            result = send_tracked_email(
                to=data['to'],
                subject=data['subject'],
                body=data['body'],
                company_id=company.id,
                html_body=data.get('html_body'),
                track_opens=data.get('track_opens', True),
                track_clicks=data.get('track_clicks', True)
            )
            
            # Crear registro en base de datos si fue exitoso
            if result.get('success'):
                TrackedEmail.objects.create(
                    email_id=result['email_id'],
                    tracking_id=result['tracking_id'],
                    recipient_email=data['to'],
                    subject=data['subject'],
                    content_preview=data['body'][:500],
                    status='sent',
                    sent_at=timezone.now(),
                    company=company
                )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error enviando email tracked: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


class EmailPatternsAPIView(APIView):
    """
    API para análisis de patrones de email
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener patrones de email"""
        try:
            company = request.user.company
            days_back = int(request.GET.get('days_back', 30))
            
            # Obtener patrones del servicio
            patterns = analyze_email_patterns(company.id, days_back)
            
            # Convertir a formato serializable
            patterns_data = []
            for pattern in patterns:
                patterns_data.append({
                    'pattern_type': pattern.pattern_type,
                    'frequency': pattern.frequency,
                    'confidence': pattern.confidence,
                    'description': pattern.description,
                    'examples': pattern.examples,
                    'recommendation': pattern.recommendation
                })
            
            return Response({
                'success': True,
                'patterns': patterns_data,
                'total_patterns': len(patterns_data)
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo patrones de email: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def post(self, request):
        """Forzar nuevo análisis de patrones"""
        try:
            company = request.user.company
            days_back = int(request.data.get('days_back', 30))
            
            service = get_email_tracking_service(company.id)
            patterns = service.analyze_email_patterns(days_back, include_ai_analysis=True)
            
            # Guardar patrones en base de datos
            period_start = timezone.now() - timedelta(days=days_back)
            period_end = timezone.now()
            
            # Limpiar patrones antiguos
            EmailPattern.objects.filter(
                company=company,
                period_start__gte=period_start,
                period_end__lte=period_end
            ).delete()
            
            # Crear nuevos patrones
            created_patterns = []
            for pattern in patterns:
                db_pattern = EmailPattern.objects.create(
                    company=company,
                    pattern_type=pattern.pattern_type,
                    name=f"{pattern.pattern_type}_{timezone.now().strftime('%Y%m%d')}",
                    description=pattern.description,
                    frequency=pattern.frequency,
                    confidence=pattern.confidence,
                    pattern_data={'examples': pattern.examples},
                    examples=pattern.examples,
                    recommendation=pattern.recommendation,
                    period_start=period_start,
                    period_end=period_end
                )
                created_patterns.append(db_pattern)
            
            return Response({
                'success': True,
                'message': f'Análisis completado: {len(created_patterns)} patrones detectados',
                'patterns_created': len(created_patterns)
            })
            
        except Exception as e:
            logger.error(f"Error analizando patrones: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


class EmailInsightsAPIView(APIView):
    """
    API para insights de email generados por IA
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener insights de email"""
        try:
            company = request.user.company
            
            # Obtener insights de la base de datos
            insights_qs = EmailInsight.objects.filter(
                company=company,
                generated_at__gte=timezone.now() - timedelta(days=7)
            ).order_by('-priority', '-confidence_score')
            
            insights_data = []
            for insight in insights_qs:
                insights_data.append({
                    'id': insight.id,
                    'insight_type': insight.insight_type,
                    'priority': insight.priority,
                    'title': insight.title,
                    'description': insight.description,
                    'confidence_score': insight.confidence_score,
                    'action_items': insight.action_items,
                    'is_implemented': insight.is_implemented,
                    'generated_at': insight.generated_at.isoformat()
                })
            
            return Response({
                'success': True,
                'insights': insights_data,
                'total_insights': len(insights_data)
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo insights: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def post(self, request):
        """Generar nuevos insights"""
        try:
            company = request.user.company
            
            # Generar insights con el servicio
            insights = get_email_insights(company.id)
            
            # Guardar en base de datos
            created_insights = []
            for insight in insights:
                db_insight = EmailInsight.objects.create(
                    company=company,
                    insight_type=insight.insight_type,
                    priority=insight.priority,
                    title=insight.title,
                    description=insight.description,
                    confidence_score=insight.confidence_score,
                    action_items=insight.action_items,
                    generated_by_ai=True,
                    source_data_period={
                        'start': (timezone.now() - timedelta(days=30)).isoformat(),
                        'end': timezone.now().isoformat()
                    }
                )
                created_insights.append(db_insight)
            
            return Response({
                'success': True,
                'message': f'Insights generados: {len(created_insights)}',
                'insights_created': len(created_insights)
            })
            
        except Exception as e:
            logger.error(f"Error generando insights: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


class EmailCampaignAPIView(APIView):
    """
    API para gestión de campañas de email
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Listar campañas"""
        try:
            company = request.user.company
            campaigns = EmailCampaign.objects.filter(company=company, is_active=True)
            
            campaigns_data = []
            for campaign in campaigns:
                campaigns_data.append({
                    'id': campaign.id,
                    'name': campaign.name,
                    'description': campaign.description,
                    'total_sent': campaign.total_sent,
                    'total_delivered': campaign.total_delivered,
                    'total_opened': campaign.total_opened,
                    'total_clicked': campaign.total_clicked,
                    'open_rate': campaign.open_rate,
                    'click_rate': campaign.click_rate,
                    'bounce_rate': campaign.bounce_rate,
                    'created_at': campaign.created_at.isoformat()
                })
            
            return Response({
                'success': True,
                'campaigns': campaigns_data
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo campañas: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def post(self, request):
        """Crear nueva campaña"""
        try:
            company = request.user.company
            data = request.data
            
            campaign = EmailCampaign.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                company=company,
                created_by=request.user,
                track_opens=data.get('track_opens', True),
                track_clicks=data.get('track_clicks', True)
            )
            
            return Response({
                'success': True,
                'campaign_id': campaign.id,
                'message': 'Campaña creada exitosamente'
            })
            
        except Exception as e:
            logger.error(f"Error creando campaña: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


# Funciones de utilidad para APIs

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def email_tracking_stats(request):
    """Obtener estadísticas rápidas de email tracking"""
    try:
        company = request.user.company
        
        # Estadísticas de los últimos 30 días
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        tracked_emails = TrackedEmail.objects.filter(
            company=company,
            sent_at__gte=thirty_days_ago
        )
        
        stats = {
            'total_sent': tracked_emails.count(),
            'total_opened': tracked_emails.filter(first_opened_at__isnull=False).count(),
            'total_clicked': tracked_emails.filter(first_clicked_at__isnull=False).count(),
            'total_replied': tracked_emails.filter(replied_at__isnull=False).count(),
            'total_bounced': tracked_emails.filter(status='bounced').count(),
        }
        
        # Calcular tasas
        if stats['total_sent'] > 0:
            stats['open_rate'] = (stats['total_opened'] / stats['total_sent']) * 100
            stats['click_rate'] = (stats['total_clicked'] / stats['total_sent']) * 100
            stats['reply_rate'] = (stats['total_replied'] / stats['total_sent']) * 100
            stats['bounce_rate'] = (stats['total_bounced'] / stats['total_sent']) * 100
        else:
            stats.update({
                'open_rate': 0,
                'click_rate': 0,
                'reply_rate': 0,
                'bounce_rate': 0
            })
        
        return Response({
            'success': True,
            'stats': stats,
            'period': 'last_30_days'
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_gmail_integration(request):
    """Configurar integración con Gmail"""
    try:
        company = request.user.company
        service = get_email_tracking_service(company.id)
        
        # Configurar Gmail API
        credentials_path = request.data.get('credentials_path')
        setup_result = service.setup_gmail_api(credentials_path=credentials_path)
        
        if setup_result:
            # Configurar webhook
            webhook_url = f"{settings.FRONTEND_URL}/api/email-tracking/webhook/?company_id={company.id}"
            webhook_result = service.setup_gmail_webhook(webhook_url)
            
            return Response({
                'success': True,
                'gmail_setup': setup_result,
                'webhook_setup': webhook_result,
                'message': 'Integración con Gmail configurada exitosamente'
            })
        else:
            return Response({
                'success': False,
                'error': 'No se pudo configurar Gmail API'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error configurando Gmail: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
