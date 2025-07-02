"""
Tareas asíncronas para el módulo de reportes
"""
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import datetime, timedelta
import logging
import os
import pandas as pd
from decimal import Decimal
import json
from io import BytesIO
import zipfile

from .models import ReportTemplate, Report, ReportDistribution, ReportSchedule
from .services.report_generator import ReportGeneratorService
from .services.scheduled_reports import ScheduledReportService, ReportDistributionService
from inventory.models import Product, Transaction, Location, Category
from authentication.models import User
from alerts.models import Alert
from forecasting.models import DemandForecast
from django.db import models

logger = logging.getLogger(__name__)


# Importar tareas desde los servicios
from .services.scheduled_reports import (
    generate_report_task,
    process_scheduled_reports,
    cleanup_expired_reports
)


@shared_task(bind=True, max_retries=3)
def generate_report_manual(self, template_id, filters, requested_by_id=None):
    """
    Genera un reporte manualmente (por solicitud del usuario)
    """
    try:
        template = ReportTemplate.objects.get(id=template_id)
        
        # Crear registro de reporte
        report = Report.objects.create(
            template=template,
            title=f"{template.name} - {filters.get('date_from')} a {filters.get('date_to')}",
            status='pending',
            date_from=filters['date_from'],
            date_to=filters['date_to'],
            file_format=filters.get('format', template.default_format),
            filters_applied=filters,
            requested_by_id=requested_by_id
        )
        
        # Generar usando la tarea principal
        return generate_report_task.delay(report.id)
        
    except Exception as e:
        logger.error(f"Error iniciando generación manual de reporte: {str(e)}")
        raise self.retry(exc=e, countdown=60)
    """
    Tarea principal para generar reportes programados
    Se ejecuta diariamente según la configuración de Celery Beat
    """
    try:
        logger.info("Iniciando generación de reportes programados")
        
        current_date = timezone.now().date()
        current_weekday = current_date.weekday()  # 0=Lunes, 6=Domingo
        current_day = current_date.day
        
        # Obtener plantillas que deben ejecutarse hoy
        templates_to_process = []
        
        # Reportes diarios
        daily_templates = ReportTemplate.objects.filter(
            frequency='daily',
            is_active=True,
            auto_send=True
        )
        templates_to_process.extend(daily_templates)
        
        # Reportes semanales (ejecutar los lunes)
        if current_weekday == 0:  # Lunes
            weekly_templates = ReportTemplate.objects.filter(
                frequency='weekly',
                is_active=True,
                auto_send=True
            )
            templates_to_process.extend(weekly_templates)
        
        # Reportes mensuales (ejecutar el día 1)
        if current_day == 1:
            monthly_templates = ReportTemplate.objects.filter(
                frequency='monthly',
                is_active=True,
                auto_send=True
            )
            templates_to_process.extend(monthly_templates)
        
        reports_generated = 0
        for template in templates_to_process:
            try:
                generate_report_from_template.delay(template.id, auto_send=True)
                reports_generated += 1
            except Exception as e:
                logger.error(f"Error programando reporte {template.id}: {str(e)}")
        
        logger.info(f"Se programaron {reports_generated} reportes para generación")
        return f"Scheduled {reports_generated} reports for generation"
        
    except Exception as exc:
        logger.error(f"Error en generate_scheduled_reports: {str(exc)}")
        self.retry(countdown=60 * 10, exc=exc)


@shared_task(bind=True, max_retries=2)
def generate_report_from_template(self, template_id, auto_send=False, custom_params=None):
    """
    Genera un reporte basado en una plantilla
    """
    report = None
    try:
        template = ReportTemplate.objects.get(id=template_id, is_active=True)
        logger.info(f"Generando reporte: {template.name}")
        
        # Preparar parámetros del reporte
        params = custom_params or {}
        
        # Fechas por defecto (último mes)
        if 'date_from' not in params:
            params['date_from'] = timezone.now().date() - timedelta(days=30)
        if 'date_to' not in params:
            params['date_to'] = timezone.now().date()
        
        # Crear registro del reporte
        report = Report.objects.create(
            template=template,
            title=f"{template.name} - {timezone.now().strftime('%Y-%m-%d')}",
            status='generating',
            parameters=params,
            filters_applied=template.default_filters,
            date_from=params['date_from'],
            date_to=params['date_to'],
            file_format=template.default_format,
            requested_by_id=params.get('user_id'),
            generation_started_at=timezone.now()
        )
        
        # Generar contenido del reporte
        report_data = generate_report_data(template, params)
        
        # Generar archivo según el formato
        file_path = None
        if template.default_format == 'pdf':
            file_path = generate_pdf_report(report, template, report_data)
        elif template.default_format == 'excel':
            file_path = generate_excel_report(report, template, report_data)
        elif template.default_format == 'csv':
            file_path = generate_csv_report(report, template, report_data)
        elif template.default_format == 'json':
            file_path = generate_json_report(report, template, report_data)
        
        # Actualizar reporte con información del archivo
        if file_path:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            report.file_path = file_path
            report.file_size_mb = Decimal(str(round(file_size_mb, 2)))
            report.total_records = report_data.get('total_records', 0)
        
        # Calcular tiempo de generación
        generation_time = (timezone.now() - report.generation_started_at).total_seconds()
        report.generation_time_seconds = int(generation_time)
        
        # Marcar como completado
        report.status = 'completed'
        report.generation_completed_at = timezone.now()
        report.save()
        
        # Enviar por email si está configurado
        if auto_send and template.auto_send:
            send_report_email.delay(report.id)
        
        logger.info(f"Reporte {template.name} generado exitosamente en {generation_time:.2f}s")
        return f"Report {template.name} generated successfully"
        
    except ReportTemplate.DoesNotExist:
        logger.warning(f"Plantilla de reporte {template_id} no encontrada")
        return f"Report template {template_id} not found"
    except Exception as exc:
        logger.error(f"Error generando reporte {template_id}: {str(exc)}")
        
        # Actualizar estado en caso de error
        if report:
            report.status = 'failed'
            report.error_message = str(exc)
            report.generation_completed_at = timezone.now()
            report.save()
        
        self.retry(countdown=60 * 5, exc=exc)


@shared_task(bind=True, max_retries=3)
def send_report_email(self, report_id):
    """
    Envía un reporte por email
    """
    try:
        report = Report.objects.get(id=report_id, status='completed')
        template = report.template
        
        # Obtener destinatarios
        recipients = template.get_recipient_emails()
        if not recipients:
            logger.warning(f"No hay destinatarios para el reporte {report_id}")
            return "No recipients found"
        
        # Preparar email
        subject = f"[DataLens] Reporte: {report.title}"
        
        # Renderizar contenido del email
        email_context = {
            'report': report,
            'template': template,
            'company': template.company,
        }
        
        html_content = render_to_string('reports/email_report.html', email_context)
        text_content = render_to_string('reports/email_report.txt', email_context)
        
        # Crear email
        email = EmailMessage(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients
        )
        
        # Añadir versión HTML
        email.attach_alternative(html_content, "text/html")
        
        # Adjuntar archivo del reporte si existe
        if report.file_path and os.path.exists(report.file_path):
            filename = f"{report.title}.{report.file_format}"
            email.attach_file(report.file_path, filename)
        
        # Enviar email
        email.send()
        
        # Crear registro de distribución
        ReportDistribution.objects.create(
            report=report,
            distribution_type='email',
            recipients=recipients,
            sent_at=timezone.now(),
            status='sent'
        )
        
        # Actualizar estado del reporte
        report.status = 'sent'
        report.save()
        
        logger.info(f"Reporte {report_id} enviado a {len(recipients)} destinatarios")
        return f"Report sent to {len(recipients)} recipients"
        
    except Report.DoesNotExist:
        logger.warning(f"Reporte {report_id} no encontrado")
        return f"Report {report_id} not found"
    except Exception as exc:
        logger.error(f"Error enviando reporte {report_id}: {str(exc)}")
        self.retry(countdown=60 * 2, exc=exc)


@shared_task
def cleanup_old_reports():
    """
    Limpia reportes antiguos y archivos asociados
    """
    try:
        # Eliminar reportes más antiguos de 6 meses
        cutoff_date = timezone.now() - timedelta(days=180)
        old_reports = Report.objects.filter(
            generation_completed_at__lt=cutoff_date
        )
        
        # Eliminar archivos asociados
        files_deleted = 0
        for report in old_reports:
            if report.file_path and os.path.exists(report.file_path):
                try:
                    os.remove(report.file_path)
                    files_deleted += 1
                except OSError:
                    pass
        
        # Eliminar registros de la base de datos
        reports_deleted = old_reports.delete()[0]
        
        logger.info(f"Limpieza completada: {reports_deleted} reportes y {files_deleted} archivos eliminados")
        return f"Cleaned up {reports_deleted} reports and {files_deleted} files"
        
    except Exception as e:
        logger.error(f"Error en cleanup_old_reports: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def generate_company_dashboard_report(company_id):
    """
    Genera un reporte de dashboard ejecutivo para una empresa
    """
    try:
        from authentication.models import Company
        
        company = Company.objects.get(id=company_id)
        logger.info(f"Generando reporte dashboard para {company.name}")
        
        # Crear plantilla temporal para dashboard
        template_data = {
            'name': f'Dashboard Ejecutivo - {company.name}',
            'report_type': 'dashboard_summary',
            'default_format': 'pdf',
        }
        
        # Generar datos del dashboard
        dashboard_data = generate_dashboard_data(company)
        
        # Generar reporte (implementar según necesidades específicas)
        logger.info(f"Dashboard generado para {company.name}")
        return f"Dashboard generated for {company.name}"
        
    except Exception as e:
        logger.error(f"Error generando dashboard para empresa {company_id}: {str(e)}")
        return f"Error: {str(e)}"


def generate_report_data(template, params):
    """
    Genera los datos del reporte según el tipo
    """
    try:
        company = template.company
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        
        if template.report_type == 'inventory_summary':
            return generate_inventory_summary_data(company, date_from, date_to, template)
        elif template.report_type == 'stock_movement':
            return generate_stock_movement_data(company, date_from, date_to, template)
        elif template.report_type == 'abc_analysis':
            return generate_abc_analysis_data(company, date_from, date_to, template)
        elif template.report_type == 'turnover_analysis':
            return generate_turnover_analysis_data(company, date_from, date_to, template)
        elif template.report_type == 'forecast_accuracy':
            return generate_forecast_accuracy_data(company, date_from, date_to, template)
        elif template.report_type == 'alerts_summary':
            return generate_alerts_summary_data(company, date_from, date_to, template)
        elif template.report_type == 'supplier_performance':
            return generate_supplier_performance_data(company, date_from, date_to, template)
        elif template.report_type == 'product_performance':
            return generate_product_performance_data(company, date_from, date_to, template)
        elif template.report_type == 'cost_analysis':
            return generate_cost_analysis_data(company, date_from, date_to, template)
        else:
            return {'error': f'Tipo de reporte no soportado: {template.report_type}'}
        
    except Exception as e:
        logger.error(f"Error generando datos del reporte: {str(e)}")
        return {'error': str(e)}


def generate_inventory_summary_data(company, date_from, date_to, template):
    """Genera datos de resumen de inventario"""
    try:
        # Obtener productos activos
        products = Product.objects.filter(company=company, is_active=True)
        
        # Aplicar filtros de la plantilla
        filters = template.default_filters or {}
        if filters.get('categories'):
            products = products.filter(category_id__in=filters['categories'])
        if filters.get('locations'):
            # Filtrar por ubicaciones si es necesario
            pass
        
        summary_data = []
        total_value = Decimal('0')
        total_quantity = 0
        
        for product in products:
            current_stock = product.current_stock
            stock_value = current_stock * product.cost_price
            
            total_quantity += current_stock
            total_value += stock_value
            
            summary_data.append({
                'product_code': product.sku,
                'product_name': product.name,
                'category': product.category.name if product.category else '',
                'current_stock': current_stock,
                'unit_cost': product.cost_price,
                'stock_value': stock_value,
                'min_stock': product.min_stock or 0,
                'max_stock': product.max_stock or 0,
                'status': 'Bajo' if current_stock <= (product.min_stock or 0) else 'Normal'
            })
        
        return {
            'data': summary_data,
            'total_records': len(summary_data),
            'summary': {
                'total_products': len(summary_data),
                'total_quantity': total_quantity,
                'total_value': total_value,
                'low_stock_count': len([item for item in summary_data if item['status'] == 'Bajo'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error generando resumen de inventario: {str(e)}")
        return {'error': str(e)}


def generate_stock_movement_data(company, date_from, date_to, template):
    """Genera datos de movimiento de stock"""
    try:
        transactions = Transaction.objects.filter(
            product__company=company,
            transaction_date__range=[date_from, date_to]
        ).select_related('product', 'location', 'user')
        
        # Aplicar filtros
        filters = template.default_filters or {}
        if filters.get('transaction_types'):
            transactions = transactions.filter(transaction_type__in=filters['transaction_types'])
        
        movement_data = []
        for transaction in transactions:
            movement_data.append({
                'date': transaction.transaction_date.date(),
                'product_code': transaction.product.sku,
                'product_name': transaction.product.name,
                'location': transaction.location.name if transaction.location else '',
                'transaction_type': transaction.get_transaction_type_display(),
                'quantity': transaction.quantity,
                'unit_cost': transaction.unit_cost,
                'total_cost': transaction.quantity * transaction.unit_cost,
                'reference': transaction.reference_number or '',
                'user': transaction.user.get_full_name() if transaction.user else ''
            })
        
        # Calcular totales
        total_in = sum(item['quantity'] for item in movement_data if item['transaction_type'] in ['Compra', 'Inventario inicial'])
        total_out = sum(item['quantity'] for item in movement_data if item['transaction_type'] in ['Venta', 'Merma'])
        
        return {
            'data': movement_data,
            'total_records': len(movement_data),
            'summary': {
                'total_transactions': len(movement_data),
                'total_in': total_in,
                'total_out': total_out,
                'net_movement': total_in - total_out
            }
        }
        
    except Exception as e:
        logger.error(f"Error generando movimiento de stock: {str(e)}")
        return {'error': str(e)}


def generate_abc_analysis_data(company, date_from, date_to, template):
    """Genera análisis ABC de productos"""
    try:
        # Obtener transacciones de salida (ventas/consumo)
        transactions = Transaction.objects.filter(
            product__company=company,
            transaction_type='sale',
            transaction_date__range=[date_from, date_to]
        ).values('product__id', 'product__sku', 'product__name').annotate(
            total_quantity=models.Sum('quantity'),
            total_value=models.Sum(models.F('quantity') * models.F('unit_cost'))
        )
        
        # Calcular análisis ABC
        total_value = sum(item['total_value'] for item in transactions)
        
        abc_data = []
        cumulative_percentage = 0
        
        for item in sorted(transactions, key=lambda x: x['total_value'], reverse=True):
            percentage = (item['total_value'] / total_value) * 100 if total_value > 0 else 0
            cumulative_percentage += percentage
            
            # Clasificación ABC
            if cumulative_percentage <= 80:
                classification = 'A'
            elif cumulative_percentage <= 95:
                classification = 'B'
            else:
                classification = 'C'
            
            abc_data.append({
                'product_code': item['product__sku'],
                'product_name': item['product__name'],
                'total_quantity': item['total_quantity'],
                'total_value': item['total_value'],
                'percentage': percentage,
                'cumulative_percentage': cumulative_percentage,
                'classification': classification
            })
        
        return {
            'data': abc_data,
            'total_records': len(abc_data),
            'summary': {
                'total_products': len(abc_data),
                'class_a_count': len([item for item in abc_data if item['classification'] == 'A']),
                'class_b_count': len([item for item in abc_data if item['classification'] == 'B']),
                'class_c_count': len([item for item in abc_data if item['classification'] == 'C']),
                'total_value': total_value
            }
        }
        
    except Exception as e:
        logger.error(f"Error generando análisis ABC: {str(e)}")
        return {'error': str(e)}


def generate_alerts_summary_data(company, date_from, date_to, template):
    """Genera resumen de alertas"""
    try:
        alerts = Alert.objects.filter(
            alert_rule__company=company,
            created_at__date__range=[date_from, date_to]
        ).select_related('alert_rule', 'product', 'location')
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'date': alert.created_at.date(),
                'title': alert.title,
                'type': alert.alert_rule.get_alert_type_display(),
                'severity': alert.get_severity_display(),
                'product': alert.product.name if alert.product else '',
                'location': alert.location.name if alert.location else '',
                'status': alert.get_status_display(),
                'current_value': alert.current_value,
                'threshold_value': alert.threshold_value
            })
        
        # Resumen por tipo y severidad
        summary = {
            'total_alerts': len(alerts_data),
            'by_type': {},
            'by_severity': {},
            'by_status': {}
        }
        
        for alert in alerts_data:
            # Por tipo
            alert_type = alert['type']
            summary['by_type'][alert_type] = summary['by_type'].get(alert_type, 0) + 1
            
            # Por severidad
            severity = alert['severity']
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            # Por estado
            status = alert['status']
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
        
        return {
            'data': alerts_data,
            'total_records': len(alerts_data),
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Error generando resumen de alertas: {str(e)}")
        return {'error': str(e)}


def generate_forecast_accuracy_data(company, date_from, date_to, template):
    """Genera datos de precisión de pronósticos"""
    try:
        # Obtener pronósticos en el rango de fechas
        forecasts = DemandForecast.objects.filter(
            model__company=company,
            forecast_date__range=[date_from, date_to]
        ).select_related('model', 'product', 'location')
        
        accuracy_data = []
        total_mape = 0
        valid_forecasts = 0
        
        for forecast in forecasts:
            # Obtener demanda real
            actual_demand = Transaction.objects.filter(
                product=forecast.product,
                location=forecast.location,
                transaction_type='sale',
                transaction_date__date=forecast.forecast_date
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            # Calcular métricas
            predicted = float(forecast.predicted_demand)
            error = abs(predicted - actual_demand)
            percentage_error = (error / max(actual_demand, 1)) * 100
            
            accuracy_data.append({
                'date': forecast.forecast_date,
                'model_name': forecast.model.name,
                'product_name': forecast.product.name,
                'location_name': forecast.location.name if forecast.location else '',
                'predicted_demand': predicted,
                'actual_demand': actual_demand,
                'error': error,
                'percentage_error': percentage_error,
                'accuracy': max(0, 100 - percentage_error)
            })
            
            total_mape += percentage_error
            valid_forecasts += 1
        
        avg_mape = total_mape / valid_forecasts if valid_forecasts > 0 else 0
        avg_accuracy = max(0, 100 - avg_mape)
        
        return {
            'data': accuracy_data,
            'total_records': len(accuracy_data),
            'summary': {
                'total_forecasts': len(accuracy_data),
                'avg_accuracy': avg_accuracy,
                'avg_mape': avg_mape,
                'best_model': None,  # Implementar si es necesario
                'worst_model': None  # Implementar si es necesario
            }
        }
        
    except Exception as e:
        logger.error(f"Error generando precisión de pronósticos: {str(e)}")
        return {'error': str(e)}


def generate_excel_report(report, template, report_data):
    """Genera reporte en formato Excel"""
    try:
        # Crear directorio si no existe
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Nombre del archivo
        filename = f"report_{report.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = os.path.join(reports_dir, filename)
        
        # Crear Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Hoja principal con datos
            if 'data' in report_data and report_data['data']:
                df = pd.DataFrame(report_data['data'])
                df.to_excel(writer, sheet_name='Datos', index=False)
            
            # Hoja de resumen
            if 'summary' in report_data:
                summary_df = pd.DataFrame([report_data['summary']])
                summary_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        return file_path
        
    except Exception as e:
        logger.error(f"Error generando Excel: {str(e)}")
        raise


def generate_csv_report(report, template, report_data):
    """Genera reporte en formato CSV"""
    try:
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"report_{report.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(reports_dir, filename)
        
        if 'data' in report_data and report_data['data']:
            df = pd.DataFrame(report_data['data'])
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return file_path
        
    except Exception as e:
        logger.error(f"Error generando CSV: {str(e)}")
        raise


def generate_json_report(report, template, report_data):
    """Genera reporte en formato JSON"""
    try:
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"report_{report.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(reports_dir, filename)
        
        # Convertir Decimal a float para JSON
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=decimal_default, ensure_ascii=False)
        
        return file_path
        
    except Exception as e:
        logger.error(f"Error generando JSON: {str(e)}")
        raise


def generate_pdf_report(report, template, report_data):
    """Genera reporte en formato PDF"""
    try:
        # Implementación básica - requiere librerías como ReportLab o WeasyPrint
        logger.warning("Generación de PDF no implementada completamente")
        
        # Por ahora, generar como HTML y convertir a PDF si es necesario
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"report_{report.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.html"
        file_path = os.path.join(reports_dir, filename)
        
        # Generar HTML básico
        html_content = render_to_string('reports/report_template.html', {
            'report': report,
            'template': template,
            'data': report_data
        })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return file_path
        
    except Exception as e:
        logger.error(f"Error generando PDF: {str(e)}")
        raise


def generate_dashboard_data(company):
    """Genera datos para dashboard ejecutivo"""
    try:
        current_date = timezone.now().date()
        last_month = current_date - timedelta(days=30)
        
        # Métricas básicas
        total_products = Product.objects.filter(company=company, is_active=True).count()
        total_locations = Location.objects.filter(company=company, is_active=True).count()
        
        # Alertas activas
        active_alerts = Alert.objects.filter(
            alert_rule__company=company,
            status__in=['pending', 'acknowledged']
        ).count()
        
        # Movimientos recientes
        recent_transactions = Transaction.objects.filter(
            product__company=company,
            transaction_date__gte=last_month
        ).count()
        
        # Valor total del inventario
        total_inventory_value = Decimal('0')
        for product in Product.objects.filter(company=company, is_active=True):
            current_stock = product.current_stock
            total_inventory_value += current_stock * product.cost_price
        
        return {
            'total_products': total_products,
            'total_locations': total_locations,
            'active_alerts': active_alerts,
            'recent_transactions': recent_transactions,
            'total_inventory_value': total_inventory_value,
            'generated_at': current_date
        }
        
    except Exception as e:
        logger.error(f"Error generando datos de dashboard: {str(e)}")
        return {'error': str(e)}


# Funciones auxiliares para otros tipos de reportes
def generate_turnover_analysis_data(company, date_from, date_to, template):
    """Placeholder para análisis de rotación"""
    return {'data': [], 'total_records': 0, 'summary': {}}


def generate_supplier_performance_data(company, date_from, date_to, template):
    """Placeholder para rendimiento de proveedores"""
    return {'data': [], 'total_records': 0, 'summary': {}}


def generate_product_performance_data(company, date_from, date_to, template):
    """Placeholder para rendimiento de productos"""
    return {'data': [], 'total_records': 0, 'summary': {}}


def generate_cost_analysis_data(company, date_from, date_to, template):
    """Placeholder para análisis de costos"""
    return {'data': [], 'total_records': 0, 'summary': {}}
