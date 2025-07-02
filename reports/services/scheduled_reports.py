"""
Servicio para manejar reportes programados
"""
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
import logging
import os
from celery import shared_task
from celery.schedules import crontab

from ..models import ReportTemplate, Report, ReportSchedule, ReportDistribution
from .report_generator import ReportGeneratorService

logger = logging.getLogger(__name__)


class ScheduledReportService:
    """Servicio para manejar reportes programados"""
    
    def __init__(self):
        self.generator_service = ReportGeneratorService()
    
    def create_schedule(
        self,
        template: ReportTemplate,
        schedule_type: str,
        hour: int = 9,
        minute: int = 0,
        day_of_week: Optional[int] = None,
        day_of_month: Optional[int] = None,
        name: Optional[str] = None,
        created_by=None
    ) -> ReportSchedule:
        """
        Crea una nueva programación de reporte
        
        Args:
            template: Plantilla de reporte
            schedule_type: Tipo de programación (daily, weekly, monthly, quarterly)
            hour: Hora de ejecución (0-23)
            minute: Minuto de ejecución (0-59)
            day_of_week: Día de la semana para reportes semanales (0=lunes, 6=domingo)
            day_of_month: Día del mes para reportes mensuales (1-31)
            name: Nombre de la programación
            created_by: Usuario que crea la programación
        
        Returns:
            ReportSchedule: Objeto de programación creado
        """
        if not name:
            name = f"{template.name} - {schedule_type}"
        
        schedule = ReportSchedule.objects.create(
            template=template,
            name=name,
            schedule_type=schedule_type,
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            created_by=created_by
        )
        
        # Calcular próxima ejecución
        schedule.calculate_next_run()
        
        logger.info(f"Programación creada: {schedule.name}, próxima ejecución: {schedule.next_run_at}")
        
        return schedule
    
    def get_pending_schedules(self) -> List[ReportSchedule]:
        """
        Obtiene las programaciones que deben ejecutarse ahora
        """
        now = timezone.now()
        
        return ReportSchedule.objects.filter(
            is_active=True,
            next_run_at__lte=now
        ).select_related('template', 'template__company')
    
    def execute_schedule(self, schedule: ReportSchedule) -> Dict[str, Any]:
        """
        Ejecuta una programación de reporte
        
        Args:
            schedule: Programación a ejecutar
        
        Returns:
            Dict con resultado de la ejecución
        """
        try:
            logger.info(f"Ejecutando programación: {schedule.name}")
            
            # Actualizar estado
            schedule.last_run_at = timezone.now()
            schedule.last_run_status = 'running'
            schedule.save(update_fields=['last_run_at', 'last_run_status'])
            
            # Determinar período de datos
            date_from, date_to = self._calculate_report_period(schedule.schedule_type)
            
            # Crear reporte
            report = Report.objects.create(
                template=schedule.template,
                title=f"{schedule.template.name} - {date_from} a {date_to}",
                status='pending',
                date_from=date_from,
                date_to=date_to,
                file_format=schedule.template.default_format,
                parameters={
                    'schedule_id': schedule.id,
                    'auto_generated': True
                }
            )
            
            # Generar reporte de forma asíncrona
            generate_report_task.delay(report.id)
            
            # Actualizar programación
            schedule.last_run_status = 'completed'
            schedule.calculate_next_run()
            schedule.save(update_fields=['last_run_status', 'next_run_at'])
            
            logger.info(f"Programación ejecutada exitosamente: {schedule.name}")
            
            return {
                'success': True,
                'report_id': report.id,
                'next_run': schedule.next_run_at
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando programación {schedule.name}: {str(e)}")
            
            schedule.last_run_status = 'failed'
            schedule.save(update_fields=['last_run_status'])
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_report_period(self, schedule_type: str) -> tuple:
        """
        Calcula el período de datos para el reporte basado en el tipo de programación
        """
        now = timezone.now().date()
        
        if schedule_type == 'daily':
            # Reporte del día anterior
            date_to = now - timedelta(days=1)
            date_from = date_to
        
        elif schedule_type == 'weekly':
            # Reporte de la semana anterior (lunes a domingo)
            days_since_monday = now.weekday()
            last_monday = now - timedelta(days=days_since_monday + 7)
            date_from = last_monday
            date_to = last_monday + timedelta(days=6)
        
        elif schedule_type == 'monthly':
            # Reporte del mes anterior
            if now.month == 1:
                last_month = now.replace(year=now.year - 1, month=12, day=1)
            else:
                last_month = now.replace(month=now.month - 1, day=1)
            
            # Último día del mes anterior
            if last_month.month == 12:
                next_month = last_month.replace(year=last_month.year + 1, month=1, day=1)
            else:
                next_month = last_month.replace(month=last_month.month + 1, day=1)
            
            date_from = last_month
            date_to = next_month - timedelta(days=1)
        
        elif schedule_type == 'quarterly':
            # Reporte del trimestre anterior
            current_quarter = (now.month - 1) // 3 + 1
            
            if current_quarter == 1:
                # Q4 del año anterior
                date_from = now.replace(year=now.year - 1, month=10, day=1)
                date_to = now.replace(year=now.year - 1, month=12, day=31)
            else:
                # Trimestre anterior del mismo año
                start_month = (current_quarter - 2) * 3 + 1
                end_month = start_month + 2
                
                date_from = now.replace(month=start_month, day=1)
                
                if end_month == 12:
                    date_to = now.replace(month=12, day=31)
                else:
                    next_month = now.replace(month=end_month + 1, day=1)
                    date_to = next_month - timedelta(days=1)
        
        else:
            # Por defecto, último mes
            date_to = now
            date_from = now - timedelta(days=30)
        
        return date_from, date_to


class ReportDistributionService:
    """Servicio para distribuir reportes"""
    
    def distribute_report(self, report: Report) -> List[Dict[str, Any]]:
        """
        Distribuye un reporte a sus destinatarios
        
        Args:
            report: Reporte a distribuir
        
        Returns:
            Lista de resultados de distribución
        """
        results = []
        
        if not report.template.auto_send:
            logger.info(f"Reporte {report.id} no configurado para envío automático")
            return results
        
        recipients = report.template.get_recipient_emails()
        if not recipients:
            logger.warning(f"No hay destinatarios configurados para el reporte {report.id}")
            return results
        
        # Crear registro de distribución
        distribution = ReportDistribution.objects.create(
            report=report,
            distribution_type='email',
            recipients=recipients,
            status='pending'
        )
        
        try:
            # Enviar por email
            result = self._send_email_report(report, recipients)
            
            if result['success']:
                distribution.status = 'sent'
                distribution.sent_at = timezone.now()
                distribution.delivery_details = result
            else:
                distribution.status = 'failed'
                distribution.error_message = result.get('error', 'Error desconocido')
            
            distribution.save()
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error distribuyendo reporte {report.id}: {str(e)}")
            distribution.status = 'failed'
            distribution.error_message = str(e)
            distribution.save()
            
            results.append({
                'success': False,
                'error': str(e)
            })
        
        return results
    
    def _send_email_report(self, report: Report, recipients: List[str]) -> Dict[str, Any]:
        """
        Envía el reporte por email
        
        Args:
            report: Reporte a enviar
            recipients: Lista de emails destinatarios
        
        Returns:
            Dict con resultado del envío
        """
        try:
            # Preparar asunto y mensaje
            subject = f"Reporte Automático: {report.title}"
            
            # Mensaje del email
            message = f"""
            Estimado usuario,
            
            Se ha generado automáticamente el siguiente reporte:
            
            Reporte: {report.title}
            Período: {report.date_from} - {report.date_to}
            Generado: {report.generated_at.strftime('%d/%m/%Y %H:%M') if report.generated_at else 'En proceso'}
            
            El archivo del reporte se encuentra adjunto a este mensaje.
            
            Para acceder al sistema y ver más detalles, visite: {settings.FRONTEND_URL}
            
            Saludos,
            Sistema DataLens
            """
            
            # Crear email
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients
            )
            
            # Adjuntar archivo si existe
            if report.file_path and os.path.exists(report.file_path):
                with open(report.file_path, 'rb') as f:
                    email.attach(
                        filename=os.path.basename(report.file_path),
                        content=f.read(),
                        mimetype=self._get_mime_type(report.file_format)
                    )
            
            # Enviar email
            email.send()
            
            logger.info(f"Reporte {report.id} enviado por email a {len(recipients)} destinatarios")
            
            return {
                'success': True,
                'recipients_count': len(recipients),
                'sent_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enviando email para reporte {report.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_mime_type(self, file_format: str) -> str:
        """Obtiene el MIME type basado en el formato del archivo"""
        mime_types = {
            'pdf': 'application/pdf',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'json': 'application/json'
        }
        return mime_types.get(file_format, 'application/octet-stream')


# Tareas Celery
@shared_task(bind=True, max_retries=3)
def generate_report_task(self, report_id: int):
    """
    Tarea asíncrona para generar un reporte
    """
    try:
        report = Report.objects.get(id=report_id)
        
        logger.info(f"Iniciando generación de reporte {report_id}")
        
        # Actualizar estado
        report.status = 'generating'
        report.save(update_fields=['status'])
        
        # Obtener datos
        generator_service = ReportGeneratorService()
        
        # Aplicar filtros
        filters = {
            'date_from': report.date_from,
            'date_to': report.date_to,
            **report.filters_applied
        }
        
        data = generator_service.get_report_data(report.template, filters)
        
        # Generar archivo
        result = generator_service.generate_report(
            template=report.template,
            data=data,
            format_type=report.file_format
        )
        
        if result['success']:
            # Actualizar reporte
            report.status = 'completed'
            report.file_path = result['file_path']
            report.file_size_mb = result['file_size']
            report.generation_time_seconds = int(result.get('generation_time', 0))
            report.generated_at = timezone.now()
            
            # Calcular expiración (30 días por defecto)
            report.expires_at = timezone.now() + timedelta(days=30)
            
            if 'main_data' in data:
                report.total_records = len(data['main_data'])
        else:
            report.status = 'failed'
            report.error_message = result.get('error', 'Error desconocido')
        
        report.save()
        
        # Distribuir si está configurado para envío automático
        if report.status == 'completed' and report.template.auto_send:
            distribution_service = ReportDistributionService()
            distribution_service.distribute_report(report)
        
        logger.info(f"Reporte {report_id} generado exitosamente")
        
        return f"Reporte {report_id} generado exitosamente"
        
    except Exception as e:
        logger.error(f"Error generando reporte {report_id}: {str(e)}")
        
        try:
            report = Report.objects.get(id=report_id)
            report.status = 'failed'
            report.error_message = str(e)
            report.save(update_fields=['status', 'error_message'])
        except:
            pass
        
        # Reintentar la tarea
        raise self.retry(exc=e, countdown=60)


@shared_task
def process_scheduled_reports():
    """
    Tarea que se ejecuta periódicamente para procesar reportes programados
    """
    logger.info("Procesando reportes programados")
    
    service = ScheduledReportService()
    pending_schedules = service.get_pending_schedules()
    
    results = []
    for schedule in pending_schedules:
        try:
            result = service.execute_schedule(schedule)
            results.append({
                'schedule_id': schedule.id,
                'schedule_name': schedule.name,
                'result': result
            })
        except Exception as e:
            logger.error(f"Error procesando programación {schedule.id}: {str(e)}")
            results.append({
                'schedule_id': schedule.id,
                'schedule_name': schedule.name,
                'result': {'success': False, 'error': str(e)}
            })
    
    logger.info(f"Procesadas {len(results)} programaciones")
    return results


@shared_task
def cleanup_expired_reports():
    """
    Tarea para limpiar reportes expirados
    """
    logger.info("Limpiando reportes expirados")
    
    # Obtener reportes expirados
    expired_reports = Report.objects.filter(
        expires_at__lt=timezone.now(),
        status='completed'
    )
    
    deleted_count = 0
    for report in expired_reports:
        try:
            # Eliminar archivo físico
            if report.file_path and os.path.exists(report.file_path):
                os.remove(report.file_path)
            
            # Eliminar registro
            report.delete()
            deleted_count += 1
            
        except Exception as e:
            logger.error(f"Error eliminando reporte expirado {report.id}: {str(e)}")
    
    logger.info(f"Eliminados {deleted_count} reportes expirados")
    return f"Eliminados {deleted_count} reportes expirados"


# Configuración de tareas periódicas para Celery Beat
CELERY_BEAT_SCHEDULE = {
    'process-scheduled-reports': {
        'task': 'reports.services.scheduled_reports.process_scheduled_reports',
        'schedule': crontab(minute='*/10'),  # Cada 10 minutos
    },
    'cleanup-expired-reports': {
        'task': 'reports.services.scheduled_reports.cleanup_expired_reports',
        'schedule': crontab(hour=2, minute=0),  # Diariamente a las 2 AM
    },
}
