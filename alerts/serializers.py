from rest_framework import serializers
from .models import AlertRule, Alert, NotificationLog
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
