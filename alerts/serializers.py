from rest_framework import serializers
from .models import AlertRule, Alert, NotificationLog, AlertRecipient
from inventory.models import Product, Category, Location
from authentication.models import User


class AlertRuleSerializer(serializers.ModelSerializer):
    recipients_data = serializers.SerializerMethodField()
    categories_data = serializers.SerializerMethodField()
    products_data = serializers.SerializerMethodField()
    locations_data = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'description', 'alert_type', 'threshold_value',
            'threshold_percentage', 'days_before_expiration', 'send_email',
            'send_whatsapp', 'send_notification', 'frequency', 'additional_emails', 
            'additional_phones', 'is_active', 'created_at', 'updated_at', 
            'recipients', 'categories', 'products', 'locations', 'recipients_data', 
            'categories_data', 'products_data', 'locations_data'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_recipients_data(self, obj):
        return [
            {
                'id': user.id, 
                'full_name': user.get_full_name(), 
                'email': user.email,
                'phone': user.phone,
                'email_notifications': user.email_notifications,
                'whatsapp_notifications': user.whatsapp_notifications
            }
            for user in obj.recipients.all()
        ]
    
    def get_categories_data(self, obj):
        return [
            {'id': cat.id, 'name': cat.name}
            for cat in obj.categories.all()
        ]
    
    def get_products_data(self, obj):
        return [
            {'id': prod.id, 'name': prod.name, 'sku': prod.sku}
            for prod in obj.products.all()
        ]
    
    def get_locations_data(self, obj):
        return [
            {'id': loc.id, 'name': loc.name}
            for loc in obj.locations.all()
        ]
    
    def create(self, validated_data):
        # Obtener el usuario actual de la request
        user = self.context['request'].user
        validated_data['company'] = user.company
        validated_data['created_by'] = user
        return super().create(validated_data)


class AlertSerializer(serializers.ModelSerializer):
    product_data = serializers.SerializerMethodField()
    location_data = serializers.SerializerMethodField()
    rule_data = serializers.SerializerMethodField()
    acknowledged_by_data = serializers.SerializerMethodField()
    resolved_by_data = serializers.SerializerMethodField()
    whatsapp_message = serializers.SerializerMethodField()
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'message', 'severity', 'status', 'current_value',
            'threshold_value', 'context_data', 'created_at', 'acknowledged_at',
            'resolved_at', 'product', 'location', 'rule', 'acknowledged_by',
            'resolved_by', 'product_data', 'location_data', 'rule_data',
            'acknowledged_by_data', 'resolved_by_data', 'whatsapp_message',
            'rule_name'
        ]
        read_only_fields = [
            'id', 'created_at', 'acknowledged_at', 'resolved_at',
            'acknowledged_by', 'resolved_by', 'dismissed_by'
        ]
    
    def get_product_data(self, obj):
        if obj.product:
            return {
                'id': obj.product.id,
                'name': obj.product.name,
                'sku': obj.product.sku
            }
        return None
    
    def get_location_data(self, obj):
        if obj.location:
            return {
                'id': obj.location.id,
                'name': obj.location.name
            }
        return None
    
    def get_rule_data(self, obj):
        if obj.rule:
            return {
                'id': obj.rule.id,
                'name': obj.rule.name,
                'alert_type': obj.rule.alert_type
            }
        return None
    
    def get_acknowledged_by_data(self, obj):
        if obj.acknowledged_by:
            return {
                'id': obj.acknowledged_by.id,
                'full_name': obj.acknowledged_by.get_full_name()
            }
        return None
    
    def get_resolved_by_data(self, obj):
        if obj.resolved_by:
            return {
                'id': obj.resolved_by.id,
                'full_name': obj.resolved_by.get_full_name()
            }
        return None
    
    def get_whatsapp_message(self, obj):
        """Obtener el mensaje optimizado para WhatsApp"""
        return obj.get_whatsapp_message()


class NotificationLogSerializer(serializers.ModelSerializer):
    alert_data = serializers.SerializerMethodField()
    alert_title = serializers.CharField(source='alert.title', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification_type', 'recipient', 'subject', 'content',
            'status', 'sent_at', 'delivered_at', 'error_message',
            'whatsapp_message_id', 'created_at', 'updated_at', 'alert', 'alert_data'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'sent_at']
    
    def get_alert_data(self, obj):
        return {
            'id': obj.alert.id,
            'title': obj.alert.title,
            'severity': obj.alert.severity
        }


class AlertDashboardSerializer(serializers.Serializer):
    total_alerts = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    acknowledged_alerts = serializers.IntegerField()
    resolved_alerts = serializers.IntegerField()
    alerts_by_severity = serializers.DictField()
    alerts_by_type = serializers.DictField()
    notification_stats = serializers.DictField()
    recent_alerts = AlertSerializer(many=True)
    alert_trends = serializers.DictField()


class AlertActionSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class NotificationTestSerializer(serializers.Serializer):
    """Serializer para probar notificaciones"""
    notification_type = serializers.ChoiceField(
        choices=['email', 'whatsapp', 'all'],
        default='all'
    )
    test_phone = serializers.CharField(required=False, allow_blank=True)
    test_email = serializers.EmailField(required=False, allow_blank=True)


class AlertRecipientSerializer(serializers.ModelSerializer):
    """Serializer para gestionar destinatarios de alertas"""
    
    class Meta:
        model = AlertRecipient
        fields = [
            'id', 'name', 'email', 'phone', 'notification_type',
            'receive_all_alerts', 'receive_critical_only', 'receive_high_and_critical',
            'alert_types', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validación personalizada"""
        # Validar que tenga al menos email o teléfono
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError(
                "Debe proporcionar al menos un email o teléfono."
            )
        
        # Validar tipo de notificación vs datos disponibles
        notification_type = data.get('notification_type')
        
        if notification_type in ['email', 'both'] and not data.get('email'):
            raise serializers.ValidationError(
                "Debe proporcionar un email para notificaciones por email."
            )
        
        if notification_type in ['whatsapp', 'both'] and not data.get('phone'):
            raise serializers.ValidationError(
                "Debe proporcionar un teléfono para notificaciones por WhatsApp."
            )
        
        # Validar formato de teléfono
        phone = data.get('phone')
        if phone:
            import re
            # Formato básico: +51999999999
            if not re.match(r'^\+\d{1,3}\d{8,12}$', phone):
                raise serializers.ValidationError(
                    "El teléfono debe tener el formato +51999999999"
                )
        
        return data
    
    def create(self, validated_data):
        """Crear destinatario asignándole la empresa del usuario"""
        user = self.context['request'].user
        validated_data['company'] = user.company
        validated_data['created_by'] = user
        return super().create(validated_data)


class AlertRecipientListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar destinatarios"""
    contact_info = serializers.SerializerMethodField()
    alert_settings = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertRecipient
        fields = [
            'id', 'name', 'contact_info', 'notification_type',
            'alert_settings', 'is_active', 'created_at'
        ]
    
    def get_contact_info(self, obj):
        """Obtiene información de contacto"""
        info = []
        if obj.email:
            info.append(f"📧 {obj.email}")
        if obj.phone:
            info.append(f"📱 {obj.phone}")
        return info
    
    def get_alert_settings(self, obj):
        """Obtiene configuración de alertas en formato legible"""
        if obj.receive_all_alerts:
            return "Todas las alertas"
        elif obj.receive_critical_only:
            return "Solo alertas críticas"
        elif obj.receive_high_and_critical:
            return "Alertas altas y críticas"
        elif obj.alert_types:
            return f"Tipos específicos ({len(obj.alert_types)})"
        else:
            return "Sin configurar"
