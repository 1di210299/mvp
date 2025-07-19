"""
API Views para PDF Analysis y Status Update Automation
Endpoints para gestionar análisis de PDFs y automatización de estados
"""
import json
import logging
import tempfile
import os
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from inventory.services.pdf_analysis_service import get_pdf_analysis_service
from inventory.services.status_update_automation_service import get_status_update_service
from inventory.models import TrackedEmail

logger = logging.getLogger(__name__)


class PDFAnalysisAPIView(APIView):
    """
    API para análisis de documentos PDF
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Analizar un archivo PDF subido
        
        Expected data:
        - pdf_file: archivo PDF a analizar
        - context: contexto adicional (opcional)
        """
        try:
            # Verificar que se subió un archivo
            if 'pdf_file' not in request.FILES:
                return Response({
                    'status': 'error',
                    'message': 'No se proporcionó archivo PDF'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            pdf_file = request.FILES['pdf_file']
            
            # Verificar que es un archivo PDF
            if not pdf_file.name.lower().endswith('.pdf'):
                return Response({
                    'status': 'error',
                    'message': 'El archivo debe ser un PDF'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Guardar archivo temporalmente
            temp_path = None
            try:
                # Crear archivo temporal
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as temp_file:
                    for chunk in pdf_file.chunks():
                        temp_file.write(chunk)
                    temp_path = temp_file.name
                
                # Obtener contexto adicional si se proporciona
                context = {}
                if 'context' in request.data:
                    try:
                        context = json.loads(request.data['context'])
                    except json.JSONDecodeError:
                        context = {'raw_context': request.data['context']}
                
                # Agregar información del usuario
                context.update({
                    'company_id': request.user.company.id if hasattr(request.user, 'company') else None,
                    'uploaded_by': request.user.email,
                    'upload_timestamp': datetime.now().isoformat()
                })
                
                # Analizar PDF
                pdf_service = get_pdf_analysis_service()
                analysis_result = pdf_service.analyze_pdf(temp_path, context)
                
                # Preparar respuesta
                response_data = {
                    'status': 'success',
                    'analysis': {
                        'document_type': analysis_result.document_type,
                        'confidence': analysis_result.confidence,
                        'extracted_data': analysis_result.extracted_data,
                        'text_preview': analysis_result.text_content[:500] + "..." if len(analysis_result.text_content) > 500 else analysis_result.text_content,
                        'metadata': analysis_result.metadata,
                        'status_updates': analysis_result.status_updates
                    },
                    'file_info': {
                        'name': pdf_file.name,
                        'size': pdf_file.size,
                        'content_type': pdf_file.content_type
                    }
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
                
            finally:
                # Limpiar archivo temporal
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"Error en análisis de PDF: {e}")
            return Response({
                'status': 'error',
                'message': f'Error procesando PDF: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatusUpdateAutomationAPIView(APIView):
    """
    API para gestionar automatización de actualizaciones de estado
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Procesar email para automatización de estado
        
        Expected data:
        - tracking_id: ID del email tracked
        - force_reprocess: forzar reprocesamiento (opcional)
        """
        try:
            tracking_id = request.data.get('tracking_id')
            
            if not tracking_id:
                return Response({
                    'status': 'error',
                    'message': 'tracking_id es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar que el email existe y pertenece a la empresa del usuario
            try:
                tracked_email = TrackedEmail.objects.get(
                    tracking_id=tracking_id
                )
                
                # Verificar permisos de empresa si el usuario tiene company
                if hasattr(request.user, 'company') and request.user.company:
                    if tracked_email.company != request.user.company:
                        return Response({
                            'status': 'error',
                            'message': 'No tiene permisos para procesar este email'
                        }, status=status.HTTP_403_FORBIDDEN)
                
            except TrackedEmail.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': f'Email tracked no encontrado: {tracking_id}'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Procesar automatización
            automation_service = get_status_update_service()
            automation_logs = automation_service.process_email_for_status_updates(tracking_id)
            
            # Preparar respuesta
            response_data = {
                'status': 'success',
                'tracking_id': tracking_id,
                'automation_results': {
                    'total_rules_processed': len(automation_logs),
                    'successful_actions': len([log for log in automation_logs if log.success]),
                    'failed_actions': len([log for log in automation_logs if not log.success]),
                    'logs': [
                        {
                            'rule_name': log.rule_name,
                            'action_taken': log.action_taken,
                            'success': log.success,
                            'error_message': log.error_message,
                            'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                            'metadata': log.metadata
                        }
                        for log in automation_logs
                    ]
                },
                'email_info': {
                    'subject': tracked_email.subject,
                    'recipient': tracked_email.recipient_email,
                    'status': tracked_email.status,
                    'sent_at': tracked_email.sent_at.isoformat() if tracked_email.sent_at else None
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en automatización: {e}")
            return Response({
                'status': 'error',
                'message': f'Error procesando automatización: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """
        Obtener estadísticas de automatización
        """
        try:
            automation_service = get_status_update_service()
            
            # Obtener estadísticas
            stats = automation_service.get_automation_stats()
            
            # Obtener logs recientes
            recent_logs = automation_service.get_recent_logs(20)
            
            response_data = {
                'status': 'success',
                'statistics': stats,
                'recent_logs': recent_logs,
                'timestamp': datetime.now().isoformat()
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return Response({
                'status': 'error',
                'message': f'Error obteniendo estadísticas: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PDFEmailProcessingAPIView(APIView):
    """
    API para procesar PDFs adjuntos en emails tracked
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Procesar PDF adjunto para automatización basada en email
        
        Expected data:
        - pdf_file: archivo PDF adjunto
        - email_context: contexto del email que contenía el PDF
        """
        try:
            # Verificar archivo PDF
            if 'pdf_file' not in request.FILES:
                return Response({
                    'status': 'error',
                    'message': 'No se proporcionó archivo PDF'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            pdf_file = request.FILES['pdf_file']
            
            if not pdf_file.name.lower().endswith('.pdf'):
                return Response({
                    'status': 'error',
                    'message': 'El archivo debe ser un PDF'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener contexto del email
            email_context = {}
            if 'email_context' in request.data:
                try:
                    email_context = json.loads(request.data['email_context'])
                except json.JSONDecodeError:
                    email_context = {'raw_context': request.data['email_context']}
            
            # Agregar información del usuario
            email_context.update({
                'company_id': request.user.company.id if hasattr(request.user, 'company') else None,
                'processed_by': request.user.email,
                'processing_timestamp': datetime.now().isoformat()
            })
            
            temp_path = None
            try:
                # Guardar archivo temporalmente
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as temp_file:
                    for chunk in pdf_file.chunks():
                        temp_file.write(chunk)
                    temp_path = temp_file.name
                
                # Procesar PDF para automatización
                automation_service = get_status_update_service()
                automation_logs = automation_service.process_pdf_attachment_for_status_updates(
                    temp_path, email_context
                )
                
                # También realizar análisis del PDF
                pdf_service = get_pdf_analysis_service()
                analysis_result = pdf_service.analyze_pdf(temp_path, email_context)
                
                # Preparar respuesta completa
                response_data = {
                    'status': 'success',
                    'pdf_analysis': {
                        'document_type': analysis_result.document_type,
                        'confidence': analysis_result.confidence,
                        'extracted_data': analysis_result.extracted_data,
                        'status_updates_suggested': analysis_result.status_updates
                    },
                    'automation_results': {
                        'total_rules_processed': len(automation_logs),
                        'successful_actions': len([log for log in automation_logs if log.success]),
                        'failed_actions': len([log for log in automation_logs if not log.success]),
                        'logs': [
                            {
                                'rule_name': log.rule_name,
                                'action_taken': log.action_taken,
                                'success': log.success,
                                'error_message': log.error_message,
                                'timestamp': log.timestamp.isoformat() if log.timestamp else None
                            }
                            for log in automation_logs
                        ]
                    },
                    'file_info': {
                        'name': pdf_file.name,
                        'size': pdf_file.size,
                        'content_type': pdf_file.content_type
                    },
                    'email_context': email_context
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
                
            finally:
                # Limpiar archivo temporal
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"Error procesando PDF de email: {e}")
            return Response({
                'status': 'error',
                'message': f'Error procesando PDF de email: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AutomationRulesAPIView(APIView):
    """
    API para gestionar reglas de automatización
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Obtener reglas de automatización disponibles
        """
        try:
            automation_service = get_status_update_service()
            
            # Obtener reglas predefinidas
            rules = automation_service.predefined_rules
            
            rules_data = []
            for rule in rules:
                rules_data.append({
                    'name': rule.name,
                    'trigger_type': rule.trigger_type,
                    'conditions': rule.conditions,
                    'actions': rule.actions,
                    'priority': rule.priority,
                    'is_active': rule.is_active
                })
            
            response_data = {
                'status': 'success',
                'rules': rules_data,
                'total_rules': len(rules_data),
                'active_rules': len([rule for rule in rules if rule.is_active])
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo reglas: {e}")
            return Response({
                'status': 'error',
                'message': f'Error obteniendo reglas: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_tracked_email_batch(request):
    """
    Procesar múltiples emails tracked para automatización en lote
    
    Expected data:
    - tracking_ids: lista de IDs de emails tracked
    """
    try:
        tracking_ids = request.data.get('tracking_ids', [])
        
        if not tracking_ids or not isinstance(tracking_ids, list):
            return Response({
                'status': 'error',
                'message': 'tracking_ids debe ser una lista de IDs'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        automation_service = get_status_update_service()
        
        batch_results = []
        successful_count = 0
        failed_count = 0
        
        for tracking_id in tracking_ids:
            try:
                # Verificar que el email existe
                tracked_email = TrackedEmail.objects.get(tracking_id=tracking_id)
                
                # Verificar permisos de empresa
                if hasattr(request.user, 'company') and request.user.company:
                    if tracked_email.company != request.user.company:
                        batch_results.append({
                            'tracking_id': tracking_id,
                            'status': 'error',
                            'message': 'Sin permisos para este email'
                        })
                        failed_count += 1
                        continue
                
                # Procesar automatización
                automation_logs = automation_service.process_email_for_status_updates(tracking_id)
                
                batch_results.append({
                    'tracking_id': tracking_id,
                    'status': 'success',
                    'automation_count': len(automation_logs),
                    'successful_actions': len([log for log in automation_logs if log.success])
                })
                successful_count += 1
                
            except TrackedEmail.DoesNotExist:
                batch_results.append({
                    'tracking_id': tracking_id,
                    'status': 'error',
                    'message': 'Email no encontrado'
                })
                failed_count += 1
                
            except Exception as e:
                batch_results.append({
                    'tracking_id': tracking_id,
                    'status': 'error',
                    'message': str(e)
                })
                failed_count += 1
        
        response_data = {
            'status': 'success',
            'batch_summary': {
                'total_processed': len(tracking_ids),
                'successful': successful_count,
                'failed': failed_count,
                'success_rate': (successful_count / len(tracking_ids) * 100) if tracking_ids else 0
            },
            'results': batch_results
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en procesamiento en lote: {e}")
        return Response({
            'status': 'error',
            'message': f'Error en procesamiento en lote: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def automation_dashboard(request):
    """
    Dashboard con métricas completas de automatización
    """
    try:
        automation_service = get_status_update_service()
        
        # Obtener estadísticas
        stats = automation_service.get_automation_stats()
        
        # Obtener logs recientes
        recent_logs = automation_service.get_recent_logs(50)
        
        # Calcular métricas adicionales
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        # Filtrar logs de la última semana
        recent_logs_week = [
            log for log in recent_logs 
            if log.get('timestamp') and 
            datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) >= week_ago
        ]
        
        # Métricas por día de la semana
        daily_stats = {}
        for log in recent_logs_week:
            if log.get('timestamp'):
                day = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                if day not in daily_stats:
                    daily_stats[day] = {'total': 0, 'successful': 0}
                daily_stats[day]['total'] += 1
                if log.get('success'):
                    daily_stats[day]['successful'] += 1
        
        # Top acciones ejecutadas
        action_counts = {}
        for log in recent_logs:
            action = log.get('action_taken', 'unknown')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        response_data = {
            'status': 'success',
            'dashboard': {
                'overview': stats,
                'weekly_activity': daily_stats,
                'top_actions': [{'action': action, 'count': count} for action, count in top_actions],
                'recent_activity': recent_logs[:20],
                'performance_metrics': {
                    'avg_processing_time': 0.5,  # En implementación real, se calcularía
                    'system_uptime': 99.9,
                    'last_updated': datetime.now().isoformat()
                }
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        return Response({
            'status': 'error',
            'message': f'Error obteniendo dashboard: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
