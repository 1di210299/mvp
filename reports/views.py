from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import os
import pandas as pd
import logging
import mimetypes

from .models import ReportTemplate, Report, KPIDefinition, KPIValue, ReportSchedule, ReportDistribution
from .serializers import (
    ReportTemplateSerializer, ReportTemplateCreateSerializer, ReportSerializer,
    ReportCreateSerializer, KPIDefinitionSerializer, KPIValueSerializer,
    ReportScheduleSerializer, ReportDistributionSerializer,
    GenerateReportRequestSerializer, ExportDataRequestSerializer,
    KPICalculationRequestSerializer
)
from .tasks import generate_report_manual
from .services.report_generator import ReportGeneratorService
from .services.scheduled_reports import ScheduledReportService, ReportDistributionService

logger = logging.getLogger(__name__)


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet para plantillas de reportes"""
    serializer_class = ReportTemplateSerializer
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ReportTemplate.objects.none()
        
        return ReportTemplate.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReportTemplateCreateSerializer
        return super().get_serializer_class()
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicar una plantilla existente"""
        original = self.get_object()
        
        # Crear una copia de la plantilla
        new_template = ReportTemplate.objects.create(
            company=original.company,
            name=f"Copia de {original.name}",
            description=original.description,
            report_type=original.report_type,
            default_format=original.default_format,
            frequency=original.frequency,
            default_filters=original.default_filters,
            columns_config=original.columns_config,
            charts_config=original.charts_config,
            grouping_config=original.grouping_config,
            sorting_config=original.sorting_config,
            auto_send=original.auto_send,
            additional_emails=original.additional_emails,
            created_by=request.user
        )
        
        # Copiar destinatarios
        for recipient in original.recipients.all():
            new_template.recipients.add(recipient)
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generar un reporte a partir de la plantilla"""
        template = self.get_object()
        serializer = GenerateReportRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Crear tarea para generar reporte
            task = generate_report_manual.delay(
                template.id,
                {
                    'date_from': serializer.validated_data['date_from'],
                    'date_to': serializer.validated_data['date_to'],
                    'format': serializer.validated_data['format'],
                    'send_email': serializer.validated_data['send_email'],
                    **serializer.validated_data['filters']
                },
                request.user.id
            )
            
            return Response({
                'message': 'Reporte en proceso de generación',
                'task_id': task.id,
                'template': template.name
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet para reportes generados"""
    serializer_class = ReportSerializer
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Report.objects.none()
        
        # Filtrar por plantillas de la compañía del usuario
        return Report.objects.filter(
            template__company=self.request.user.company
        ).select_related('template', 'requested_by').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        return super().get_serializer_class()
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar el archivo del reporte"""
        report = self.get_object()
        
        if not report.file_path or not os.path.exists(report.file_path):
            return Response(
                {"error": "Archivo no disponible"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Determinar tipo de contenido
        mime_type, _ = mimetypes.guess_type(report.file_path)
        if not mime_type:
            mime_types = {
                'pdf': 'application/pdf',
                'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'csv': 'text/csv',
                'json': 'application/json'
            }
            mime_type = mime_types.get(report.file_format, 'application/octet-stream')
        
        # Registrar descarga
        logger.info(f"Usuario {request.user.id} descargando reporte {report.id}")
        
        return FileResponse(
            open(report.file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(report.file_path),
            content_type=mime_type
        )
    
    @action(detail=True, methods=['post'])
    def send_by_email(self, request, pk=None):
        """Enviar el reporte por email"""
        report = self.get_object()
        
        if report.status != 'completed':
            return Response(
                {"error": "El reporte debe estar completado para enviar por email"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener destinatarios adicionales
        recipients = request.data.get('recipients', [])
        
        # Usar servicio de distribución
        distribution_service = ReportDistributionService()
        
        # Crear distribución
        distribution = ReportDistribution.objects.create(
            report=report,
            distribution_type='email',
            recipients=recipients,
            status='pending'
        )
        
        # Enviar el reporte
        try:
            results = distribution_service.distribute_report(report)
            return Response({
                'message': 'Reporte enviado correctamente',
                'distribution_id': distribution.id
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtener reportes recientes"""
        queryset = self.get_queryset().filter(
            status='completed',
            created_at__gte=timezone.now() - timedelta(days=30)
        )[:10]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class KPIDefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet para definiciones de KPIs"""
    serializer_class = KPIDefinitionSerializer
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return KPIDefinition.objects.none()
        
        return KPIDefinition.objects.filter(
            company=self.request.user.company
        ).order_by('sort_order', 'name')


class KPIValueViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para valores de KPIs"""
    serializer_class = KPIValueSerializer
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return KPIValue.objects.none()
        
        return KPIValue.objects.filter(
            kpi_definition__company=self.request.user.company
        ).select_related('kpi_definition').order_by('-period_end')


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet para programaciones de reportes"""
    serializer_class = ReportScheduleSerializer
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ReportSchedule.objects.none()
        
        return ReportSchedule.objects.filter(
            template__company=self.request.user.company
        ).select_related('template', 'created_by').order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activar/desactivar una programación"""
        schedule = self.get_object()
        schedule.is_active = not schedule.is_active
        schedule.save(update_fields=['is_active'])
        
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def execute_now(self, request, pk=None):
        """Ejecutar una programación inmediatamente"""
        schedule = self.get_object()
        
        # Usar servicio de programación
        service = ScheduledReportService()
        result = service.execute_schedule(schedule)
        
        if result['success']:
            return Response({
                'message': 'Programación ejecutada correctamente',
                'report_id': result['report_id']
            })
        
        return Response(
            {"error": result.get('error', 'Error desconocido')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class GenerateReportView(APIView):
    """Vista para generar reportes manualmente"""
    
    def post(self, request):
        serializer = GenerateReportRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Obtener la plantilla
            try:
                template = ReportTemplate.objects.get(
                    id=serializer.validated_data['template_id'],
                    company=request.user.company
                )
            except ReportTemplate.DoesNotExist:
                return Response(
                    {"error": "Plantilla no encontrada"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Crear tarea para generar reporte
            task = generate_report_manual.delay(
                template.id,
                {
                    'date_from': serializer.validated_data['date_from'],
                    'date_to': serializer.validated_data['date_to'],
                    'format': serializer.validated_data['format'],
                    'send_email': serializer.validated_data['send_email'],
                    **serializer.validated_data['filters']
                },
                request.user.id
            )
            
            return Response({
                'message': 'Reporte en proceso de generación',
                'task_id': task.id,
                'template_id': template.id,
                'template_name': template.name
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DownloadReportView(APIView):
    """Vista para descargar reportes"""
    
    def get(self, request, report_id):
        # Verificar que el usuario tenga acceso al reporte
        report = get_object_or_404(
            Report, 
            id=report_id,
            template__company=request.user.company
        )
        
        if not report.file_path or not os.path.exists(report.file_path):
            return Response(
                {"error": "Archivo no disponible"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Determinar tipo de contenido
        mime_type, _ = mimetypes.guess_type(report.file_path)
        if not mime_type:
            mime_types = {
                'pdf': 'application/pdf',
                'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'csv': 'text/csv',
                'json': 'application/json'
            }
            mime_type = mime_types.get(report.file_format, 'application/octet-stream')
        
        # Registrar descarga
        logger.info(f"Usuario {request.user.id} descargando reporte {report.id}")
        
        return FileResponse(
            open(report.file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(report.file_path),
            content_type=mime_type
        )


class ReportsDashboardView(APIView):
    """Vista para el dashboard de reportes"""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "No autorizado"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Obtener información para el dashboard
        recent_reports = Report.objects.filter(
            template__company=request.user.company,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')[:5]
        
        scheduled_reports = ReportSchedule.objects.filter(
            template__company=request.user.company,
            is_active=True
        ).select_related('template').order_by('next_run_at')[:5]
        
        # Estadísticas básicas
        report_counts = {
            'total': Report.objects.filter(template__company=request.user.company).count(),
            'completed': Report.objects.filter(template__company=request.user.company, status='completed').count(),
            'pending': Report.objects.filter(template__company=request.user.company, status__in=['pending', 'generating']).count(),
            'failed': Report.objects.filter(template__company=request.user.company, status='failed').count(),
        }
        
        template_counts = {
            'total': ReportTemplate.objects.filter(company=request.user.company).count(),
            'system': ReportTemplate.objects.filter(company=request.user.company, is_system_template=True).count(),
            'custom': ReportTemplate.objects.filter(company=request.user.company, is_system_template=False).count(),
        }
        
        kpi_counts = {
            'total': KPIDefinition.objects.filter(company=request.user.company).count(),
            'active': KPIDefinition.objects.filter(company=request.user.company, is_active=True).count(),
        }
        
        return Response({
            'recent_reports': ReportSerializer(recent_reports, many=True).data,
            'scheduled_reports': ReportScheduleSerializer(scheduled_reports, many=True).data,
            'stats': {
                'reports': report_counts,
                'templates': template_counts,
                'kpis': kpi_counts
            }
        })


class CalculateKPIsView(APIView):
    """Vista para calcular KPIs manualmente"""
    
    def post(self, request):
        serializer = KPICalculationRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Obtener los KPIs a calcular
            kpi_ids = serializer.validated_data.get('kpi_ids', [])
            company = request.user.company
            
            if kpi_ids:
                kpis = KPIDefinition.objects.filter(
                    id__in=kpi_ids,
                    company=company,
                    is_active=True
                )
            else:
                kpis = KPIDefinition.objects.filter(
                    company=company,
                    is_active=True
                )
            
            # Datos de período
            period_start = serializer.validated_data['period_start']
            period_end = serializer.validated_data['period_end']
            period_type = serializer.validated_data['period_type']
            
            # Calcular los KPIs
            results = []
            for kpi in kpis:
                try:
                    # Este es un ejemplo simplificado. En una implementación real,
                    # se usaría un servicio específico para calcular KPIs
                    value = 0
                    
                    # Crear o actualizar el valor del KPI
                    kpi_value, created = KPIValue.objects.update_or_create(
                        kpi_definition=kpi,
                        period_start=period_start,
                        period_end=period_end,
                        period_type=period_type,
                        defaults={
                            'value': value,
                            'context_data': {'calculated_at': timezone.now().isoformat()}
                        }
                    )
                    
                    results.append({
                        'kpi_id': kpi.id,
                        'kpi_name': kpi.name,
                        'value': kpi_value.value,
                        'status': kpi_value.status_color,
                        'created': created
                    })
                except Exception as e:
                    results.append({
                        'kpi_id': kpi.id,
                        'kpi_name': kpi.name,
                        'error': str(e)
                    })
            
            return Response({
                'message': f'Calculados {len(results)} KPIs',
                'results': results
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExportDataView(APIView):
    """Vista para exportar datos en diferentes formatos"""
    
    def post(self, request):
        serializer = ExportDataRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            data_type = serializer.validated_data['data_type']
            format_type = serializer.validated_data['format']
            date_from = serializer.validated_data.get('date_from')
            date_to = serializer.validated_data.get('date_to')
            filters = serializer.validated_data.get('filters', {})
            
            # Obtener datos según el tipo
            try:
                data_frame = self._get_data_for_export(
                    data_type, 
                    request.user.company,
                    date_from,
                    date_to,
                    filters
                )
                
                # Generar archivo en el formato solicitado
                if format_type == 'csv':
                    response = self._generate_csv_response(data_frame, data_type)
                elif format_type == 'excel':
                    response = self._generate_excel_response(data_frame, data_type)
                else:  # json
                    response = self._generate_json_response(data_frame, data_type)
                
                return response
                
            except Exception as e:
                logger.error(f"Error exportando datos: {str(e)}")
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_data_for_export(self, data_type, company, date_from=None, date_to=None, filters=None):
        """Obtiene datos para exportar según el tipo"""
        from inventory.models import Product, Transaction
        from alerts.models import Alert
        from forecasting.models import DemandForecast
        from django.db.models import F, Value, CharField
        from django.db.models.functions import Concat
        
        filters = filters or {}
        now = timezone.now()
        
        # Establecer fechas predeterminadas si no se proporcionan
        if not date_from:
            date_from = now - timedelta(days=30)
        if not date_to:
            date_to = now
        
        # Exportar diferentes tipos de datos
        if data_type == 'products':
            queryset = Product.objects.filter(company=company)
            
            # Aplicar filtros adicionales
            if 'category' in filters:
                queryset = queryset.filter(category__name=filters['category'])
            if 'active_only' in filters and filters['active_only']:
                queryset = queryset.filter(is_active=True)
            
            # Valores a exportar
            values = [
                'id', 'code', 'name', 'description', 'unit', 'current_stock',
                'minimum_stock', 'maximum_stock', 'unit_cost', 'is_active'
            ]
            
            # Añadir campos relacionados
            queryset = queryset.annotate(
                category_name=F('category__name'),
                location_name=F('location__name'),
                created_at_str=F('created_at')
            )
            values.extend(['category_name', 'location_name', 'created_at_str'])
            
            # Convertir a DataFrame
            data = list(queryset.values(*values))
            df = pd.DataFrame(data)
            
        elif data_type == 'transactions':
            queryset = Transaction.objects.filter(
                product__company=company,
                created_at__date__range=[date_from, date_to]
            )
            
            # Aplicar filtros adicionales
            if 'product_id' in filters:
                queryset = queryset.filter(product_id=filters['product_id'])
            if 'transaction_type' in filters:
                queryset = queryset.filter(transaction_type=filters['transaction_type'])
            
            # Valores a exportar
            queryset = queryset.annotate(
                product_name=F('product__name'),
                product_code=F('product__code'),
                location_name=F('location__name'),
                created_by_name=Concat(
                    F('created_by__first_name'), 
                    Value(' '), 
                    F('created_by__last_name'),
                    output_field=CharField()
                ),
                transaction_type_display=F('transaction_type')
            )
            
            values = [
                'id', 'product_name', 'product_code', 'quantity', 'transaction_type',
                'transaction_type_display', 'reference', 'location_name', 
                'created_by_name', 'created_at'
            ]
            
            # Convertir a DataFrame
            data = list(queryset.values(*values))
            df = pd.DataFrame(data)
            
        elif data_type == 'alerts':
            queryset = Alert.objects.filter(
                company=company,
                created_at__date__range=[date_from, date_to]
            )
            
            # Aplicar filtros adicionales
            if 'priority' in filters:
                queryset = queryset.filter(priority=filters['priority'])
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            if 'alert_type' in filters:
                queryset = queryset.filter(alert_type=filters['alert_type'])
            
            # Valores a exportar
            queryset = queryset.annotate(
                product_name=F('product__name'),
                priority_display=F('priority'),
                status_display=F('status'),
                alert_type_display=F('alert_type')
            )
            
            values = [
                'id', 'product_name', 'message', 'alert_type', 'alert_type_display',
                'priority', 'priority_display', 'status', 'status_display',
                'created_at', 'resolved_at', 'resolution_notes'
            ]
            
            # Convertir a DataFrame
            data = list(queryset.values(*values))
            df = pd.DataFrame(data)
            
        elif data_type == 'forecasts':
            queryset = DemandForecast.objects.filter(
                product__company=company,
                created_at__date__range=[date_from, date_to]
            )
            
            # Aplicar filtros adicionales
            if 'product_id' in filters:
                queryset = queryset.filter(product_id=filters['product_id'])
            
            # Valores a exportar
            queryset = queryset.annotate(
                product_name=F('product__name'),
                product_code=F('product__code')
            )
            
            values = [
                'id', 'product_name', 'product_code', 'forecast_period_start',
                'forecast_period_end', 'predicted_demand', 'actual_demand',
                'accuracy_percentage', 'created_at'
            ]
            
            # Convertir a DataFrame
            data = list(queryset.values(*values))
            df = pd.DataFrame(data)
        
        else:
            raise ValueError(f"Tipo de datos no soportado: {data_type}")
        
        return df
    
    def _generate_csv_response(self, df, data_type):
        """Genera respuesta CSV"""
        response = Response(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{data_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        # Convertir DataFrame a CSV
        csv_data = df.to_csv(index=False)
        response.content = csv_data
        
        return response
    
    def _generate_excel_response(self, df, data_type):
        """Genera respuesta Excel"""
        # Crear archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=data_type.capitalize())
        
        # Preparar respuesta
        output.seek(0)
        response = Response(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{data_type}_{timezone.now().strftime("%Y%m%d")}.xlsx"'
        
        return response
    
    def _generate_json_response(self, df, data_type):
        """Genera respuesta JSON"""
        # Convertir DataFrame a JSON
        json_data = df.to_json(orient='records')
        
        # Crear respuesta
        response = Response(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{data_type}_{timezone.now().strftime("%Y%m%d")}.json"'
        
        return response
