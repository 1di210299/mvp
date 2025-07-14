from rest_framework import serializers
from .models import IntelligenceBriefing, IntelligenceInsight, IntelligenceMetric
from authentication.models import Company

class IntelligenceBriefingSerializer(serializers.ModelSerializer):
    """Serializer para briefings de inteligencia"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    
    # Campos JSON como propiedades
    priorities = serializers.JSONField(source='priorities_json', read_only=True)
    opportunities = serializers.JSONField(source='opportunities_json', read_only=True)
    recommendations = serializers.JSONField(source='recommendations_json', read_only=True)
    metrics = serializers.JSONField(source='metrics_json', read_only=True)
    data_snapshot = serializers.JSONField(source='data_snapshot_json', read_only=True)
    
    class Meta:
        model = IntelligenceBriefing
        fields = [
            'id',
            'company',
            'company_name',
            'briefing_type',
            'generated_at',
            'generated_by',
            'generated_by_name',
            'greeting',
            'summary',
            'priorities',
            'opportunities',
            'recommendations',
            'metrics',
            'data_snapshot',
            'is_active'
        ]
        read_only_fields = ['id', 'generated_at', 'company_name', 'generated_by_name']

class IntelligenceInsightSerializer(serializers.ModelSerializer):
    """Serializer para insights de inteligencia"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    # Campos JSON como propiedades
    actions = serializers.JSONField(source='actions_json', read_only=True)
    source_data = serializers.JSONField(source='source_data_json', read_only=True)
    
    # Campos calculados
    days_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = IntelligenceInsight
        fields = [
            'id',
            'company',
            'company_name',
            'insight_type',
            'priority',
            'title',
            'message',
            'actions',
            'created_at',
            'is_active',
            'is_resolved',
            'resolved_at',
            'resolved_by',
            'resolved_by_name',
            'source_data',
            'confidence_score',
            'days_since_created'
        ]
        read_only_fields = ['id', 'created_at', 'company_name', 'resolved_by_name', 'days_since_created']
    
    def get_days_since_created(self, obj):
        """Calcular días desde la creación"""
        from django.utils import timezone
        from datetime import timedelta
        
        if obj.created_at:
            delta = timezone.now() - obj.created_at
            return delta.days
        return 0

class IntelligenceMetricSerializer(serializers.ModelSerializer):
    """Serializer para métricas de inteligencia"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    raw_data = serializers.JSONField(source='raw_data_json', read_only=True)
    
    # Campos calculados
    change_direction = serializers.SerializerMethodField()
    change_magnitude = serializers.SerializerMethodField()
    
    class Meta:
        model = IntelligenceMetric
        fields = [
            'id',
            'company',
            'company_name',
            'metric_type',
            'current_value',
            'previous_value',
            'change_percentage',
            'trend',
            'period_start',
            'period_end',
            'comparison_period_start',
            'comparison_period_end',
            'calculated_at',
            'calculation_method',
            'raw_data',
            'change_direction',
            'change_magnitude'
        ]
        read_only_fields = ['id', 'calculated_at', 'company_name', 'change_direction', 'change_magnitude']
    
    def get_change_direction(self, obj):
        """Obtener dirección del cambio"""
        if obj.change_percentage is None:
            return 'unknown'
        elif obj.change_percentage > 0:
            return 'positive'
        elif obj.change_percentage < 0:
            return 'negative'
        else:
            return 'neutral'
    
    def get_change_magnitude(self, obj):
        """Obtener magnitud del cambio"""
        if obj.change_percentage is None:
            return 'unknown'
        
        abs_change = abs(obj.change_percentage)
        if abs_change >= 20:
            return 'high'
        elif abs_change >= 10:
            return 'medium'
        elif abs_change >= 5:
            return 'low'
        else:
            return 'minimal'

# Serializers adicionales para vistas específicas
class DashboardIntelligenceSerializer(serializers.Serializer):
    """Serializer para datos de inteligencia del dashboard"""
    
    briefing = IntelligenceBriefingSerializer(read_only=True)
    critical_insights = IntelligenceInsightSerializer(many=True, read_only=True)
    success = serializers.BooleanField(read_only=True)

class IntelligenceStatusSerializer(serializers.Serializer):
    """Serializer para estado del servicio de inteligencia"""
    
    openai_available = serializers.BooleanField(read_only=True)
    service_status = serializers.CharField(read_only=True)
    stats = serializers.JSONField(read_only=True)
    success = serializers.BooleanField(read_only=True)

class BriefingRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de briefing"""
    
    force_regenerate = serializers.BooleanField(default=False)
    include_history = serializers.BooleanField(default=False)
    
class InsightResolveSerializer(serializers.Serializer):
    """Serializer para resolver insights"""
    
    resolved_notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
class MetricFilterSerializer(serializers.Serializer):
    """Serializer para filtros de métricas"""
    
    metric_type = serializers.CharField(required=False)
    days = serializers.IntegerField(default=30, min_value=1, max_value=365)
    trend = serializers.CharField(required=False)
    
class InsightFilterSerializer(serializers.Serializer):
    """Serializer para filtros de insights"""
    
    insight_type = serializers.CharField(required=False)
    priority = serializers.CharField(required=False)
    is_active = serializers.BooleanField(default=True)
    is_resolved = serializers.BooleanField(required=False)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100) 