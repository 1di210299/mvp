"""
Serializers para el módulo de reportes
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ReportTemplate, Report, KPIDefinition, KPIValue, 
    ReportSchedule, ReportDistribution
)

User = get_user_model()


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de reportes"""
    
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    default_format_display = serializers.CharField(source='get_default_format_display', read_only=True)
    recipient_emails = serializers.ListField(source='get_recipient_emails', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_type', 'report_type_display',
            'default_format', 'default_format_display', 'frequency', 'frequency_display',
            'default_filters', 'columns_config', 'charts_config', 'grouping_config',
            'sorting_config', 'auto_send', 'recipients', 'additional_emails',
            'recipient_emails', 'is_active', 'is_system_template', 'created_at',
            'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'company', 'created_at', 'updated_at', 'is_system_template']
    
    def create(self, validated_data):
        # Asignar compañía del usuario actual
        request = self.context.get('request')
        if request and request.user:
            validated_data['company'] = request.user.company
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ReportTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer simplificado para crear plantillas"""
    
    class Meta:
        model = ReportTemplate
        fields = [
            'name', 'description', 'report_type', 'default_format',
            'frequency', 'default_filters', 'auto_send', 'recipients',
            'additional_emails'
        ]


class ReportSerializer(serializers.ModelSerializer):
    """Serializer para reportes generados"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_type = serializers.CharField(source='template.get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    download_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'template', 'template_name', 'template_type', 'title',
            'description', 'status', 'status_display', 'parameters',
            'filters_applied', 'date_from', 'date_to', 'file_format',
            'file_path', 'file_size_mb', 'total_records', 'generation_time_seconds',
            'error_message', 'execution_log', 'requested_by', 'requested_by_name',
            'generated_at', 'sent_at', 'expires_at', 'created_at', 'updated_at',
            'is_expired', 'download_url'
        ]
        read_only_fields = [
            'id', 'file_path', 'file_size_mb', 'total_records', 'generation_time_seconds',
            'error_message', 'execution_log', 'generated_at', 'sent_at', 'created_at',
            'updated_at', 'is_expired', 'download_url'
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear nuevos reportes"""
    
    class Meta:
        model = Report
        fields = [
            'template', 'title', 'description', 'date_from', 'date_to',
            'file_format', 'parameters', 'filters_applied'
        ]
    
    def validate(self, data):
        # Validar que date_from sea menor que date_to
        if data['date_from'] > data['date_to']:
            raise serializers.ValidationError(
                "La fecha de inicio debe ser anterior a la fecha final"
            )
        
        # Validar que el template pertenezca a la compañía del usuario
        request = self.context.get('request')
        if request and request.user:
            template = data['template']
            if template.company != request.user.company:
                raise serializers.ValidationError(
                    "No tiene permisos para usar esta plantilla"
                )
        
        return data
    
    def create(self, validated_data):
        # Asignar usuario que solicita el reporte
        request = self.context.get('request')
        if request and request.user:
            validated_data['requested_by'] = request.user
        
        return super().create(validated_data)


class KPIDefinitionSerializer(serializers.ModelSerializer):
    """Serializer para definiciones de KPIs"""
    
    calculation_type_display = serializers.CharField(source='get_calculation_type_display', read_only=True)
    data_source_display = serializers.CharField(source='get_data_source_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = KPIDefinition
        fields = [
            'id', 'name', 'description', 'code', 'calculation_type',
            'calculation_type_display', 'data_source', 'data_source_display',
            'formula', 'default_filters', 'unit', 'decimal_places',
            'show_as_percentage', 'good_threshold', 'warning_threshold',
            'critical_threshold', 'track_trend', 'trend_periods',
            'is_active', 'is_system_kpi', 'sort_order', 'created_at',
            'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'company', 'created_at', 'updated_at', 'is_system_kpi']
    
    def create(self, validated_data):
        # Asignar compañía del usuario actual
        request = self.context.get('request')
        if request and request.user:
            validated_data['company'] = request.user.company
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class KPIValueSerializer(serializers.ModelSerializer):
    """Serializer para valores de KPIs"""
    
    kpi_name = serializers.CharField(source='kpi_definition.name', read_only=True)
    kpi_unit = serializers.CharField(source='kpi_definition.unit', read_only=True)
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)
    status_color = serializers.CharField(read_only=True)
    
    class Meta:
        model = KPIValue
        fields = [
            'id', 'kpi_definition', 'kpi_name', 'kpi_unit', 'period_start',
            'period_end', 'period_type', 'period_type_display', 'value',
            'context_data', 'calculated_at', 'calculation_duration_ms',
            'status_color'
        ]
        read_only_fields = [
            'id', 'calculated_at', 'calculation_duration_ms', 'status_color'
        ]


class ReportScheduleSerializer(serializers.ModelSerializer):
    """Serializer para programaciones de reportes"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    schedule_type_display = serializers.CharField(source='get_schedule_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    last_run_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'template', 'template_name', 'name', 'schedule_type',
            'schedule_type_display', 'hour', 'minute', 'day_of_week',
            'day_of_month', 'is_active', 'last_run_at', 'next_run_at',
            'last_run_status', 'last_run_status_display', 'created_at',
            'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'last_run_at', 'next_run_at', 'last_run_status',
            'created_at', 'updated_at'
        ]
    
    def get_last_run_status_display(self, obj):
        """Obtiene la descripción del estado de la última ejecución"""
        status_map = {
            'completed': 'Completado',
            'failed': 'Falló',
            'running': 'Ejecutando',
            '': 'Sin ejecutar'
        }
        return status_map.get(obj.last_run_status, obj.last_run_status)
    
    def create(self, validated_data):
        # Asignar usuario que crea la programación
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        schedule = super().create(validated_data)
        
        # Calcular próxima ejecución
        schedule.calculate_next_run()
        
        return schedule
    
    def validate(self, data):
        # Validaciones específicas por tipo de programación
        schedule_type = data.get('schedule_type')
        
        if schedule_type == 'weekly' and not data.get('day_of_week'):
            raise serializers.ValidationError(
                "Debe especificar el día de la semana para reportes semanales"
            )
        
        if schedule_type == 'monthly' and not data.get('day_of_month'):
            raise serializers.ValidationError(
                "Debe especificar el día del mes para reportes mensuales"
            )
        
        # Validar template pertenece a la compañía del usuario
        request = self.context.get('request')
        if request and request.user:
            template = data.get('template')
            if template and template.company != request.user.company:
                raise serializers.ValidationError(
                    "No tiene permisos para programar esta plantilla"
                )
        
        return data


class ReportDistributionSerializer(serializers.ModelSerializer):
    """Serializer para distribuciones de reportes"""
    
    report_title = serializers.CharField(source='report.title', read_only=True)
    distribution_type_display = serializers.CharField(source='get_distribution_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recipient_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ReportDistribution
        fields = [
            'id', 'report', 'report_title', 'distribution_type',
            'distribution_type_display', 'status', 'status_display',
            'recipients', 'recipient_count', 'sent_at', 'delivered_at',
            'error_message', 'delivery_details', 'created_at'
        ]
        read_only_fields = [
            'id', 'sent_at', 'delivered_at', 'error_message',
            'delivery_details', 'created_at', 'recipient_count'
        ]


class GenerateReportRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de generación de reportes"""
    
    template_id = serializers.IntegerField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    format = serializers.ChoiceField(
        choices=['pdf', 'excel', 'csv', 'json'],
        default='pdf'
    )
    filters = serializers.JSONField(default=dict)
    send_email = serializers.BooleanField(default=False)
    
    def validate(self, data):
        # Validar fechas
        if data['date_from'] > data['date_to']:
            raise serializers.ValidationError(
                "La fecha de inicio debe ser anterior a la fecha final"
            )
        
        # Validar que el template existe y es accesible
        request = self.context.get('request')
        if request and request.user:
            try:
                template = ReportTemplate.objects.get(
                    id=data['template_id'],
                    company=request.user.company,
                    is_active=True
                )
            except ReportTemplate.DoesNotExist:
                raise serializers.ValidationError(
                    "Plantilla de reporte no encontrada o no accesible"
                )
        
        return data


class ExportDataRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de exportación de datos"""
    
    data_type = serializers.ChoiceField(choices=[
        'products', 'transactions', 'alerts', 'forecasts'
    ])
    format = serializers.ChoiceField(
        choices=['csv', 'excel', 'json'],
        default='csv'
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    filters = serializers.JSONField(default=dict)
    
    def validate(self, data):
        # Validar fechas si se proporcionan ambas
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                "La fecha de inicio debe ser anterior a la fecha final"
            )
        
        return data


class KPICalculationRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de cálculo de KPIs"""
    
    kpi_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    period_type = serializers.ChoiceField(choices=[
        'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    ])
    
    def validate(self, data):
        # Validar fechas
        if data['period_start'] > data['period_end']:
            raise serializers.ValidationError(
                "La fecha de inicio debe ser anterior a la fecha final"
            )
        
        # Validar KPIs si se especifican
        request = self.context.get('request')
        if request and request.user and data.get('kpi_ids'):
            user_kpis = KPIDefinition.objects.filter(
                company=request.user.company,
                id__in=data['kpi_ids'],
                is_active=True
            ).count()
            
            if user_kpis != len(data['kpi_ids']):
                raise serializers.ValidationError(
                    "Algunos KPIs especificados no son válidos"
                )
        
        return data
