"""
Serializers para APIs REST del sistema de inventario
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from ..models import (
    PurchaseOrder,
    Supplier, 
    TrackedEmail,
    EmailCampaign,
    EmailClick,
    Product,
    Category,
    InventoryItem
)

User = get_user_model()


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer para Supplier"""
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'email', 'phone', 'address',
            'contact_name', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para Category"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer para Product"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'category', 'category_name',
            'cost_price', 'sale_price', 'unit', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Comentado temporalmente - PurchaseOrderItem no existe en el modelo actual
# class PurchaseOrderItemSerializer(serializers.ModelSerializer):
#     """Serializer para PurchaseOrderItem"""
#     product_name = serializers.CharField(source='product.name', read_only=True)
#     product_sku = serializers.CharField(source='product.sku', read_only=True)
#     
#     class Meta:
#         model = PurchaseOrderItem
#         fields = [
#             'id', 'product', 'product_name', 'product_sku',
#             'quantity', 'unit_price', 'total_price'
#         ]
#         read_only_fields = ['id', 'total_price']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer para PurchaseOrder"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_email = serializers.CharField(source='supplier.email', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    # items = PurchaseOrderItemSerializer(many=True, read_only=True)  # Comentado temporalmente
    
    # Campos calculados
    # items_count = serializers.SerializerMethodField()  # Comentado temporalmente
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'supplier_name', 'supplier_email',
            'status', 'status_display', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'total_amount', 'quantity', 'unit_price',
            # 'items', 'items_count'  # Comentado temporalmente
        ]
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at']
    
    # def get_items_count(self, obj):
    #     """Número de items en la orden"""
    #     return obj.items.count()


class EmailCampaignSerializer(serializers.ModelSerializer):
    """Serializer para EmailCampaign"""
    emails_count = serializers.SerializerMethodField()
    open_rate = serializers.SerializerMethodField()
    click_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailCampaign
        fields = [
            'id', 'name', 'description', 'is_active', 'created_at',
            'emails_count', 'open_rate', 'click_rate'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_emails_count(self, obj):
        """Número de emails en la campaña"""
        return obj.tracked_emails.count()
    
    def get_open_rate(self, obj):
        """Tasa de apertura de la campaña"""
        emails = obj.tracked_emails.all()
        total = emails.count()
        opened = emails.filter(status__in=['opened', 'clicked', 'replied']).count()
        return round((opened / total * 100) if total > 0 else 0, 1)
    
    def get_click_rate(self, obj):
        """Tasa de clicks de la campaña"""
        emails = obj.tracked_emails.all()
        total = emails.count()
        clicked = emails.filter(status__in=['clicked', 'replied']).count()
        return round((clicked / total * 100) if total > 0 else 0, 1)


class EmailClickSerializer(serializers.ModelSerializer):
    """Serializer para EmailClick"""
    
    class Meta:
        model = EmailClick
        fields = [
            'id', 'tracked_email', 'link_url', 'clicked_at',
            'user_agent', 'ip_address'
        ]
        read_only_fields = ['id', 'clicked_at']


class TrackedEmailSerializer(serializers.ModelSerializer):
    """Serializer para TrackedEmail"""
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    clicks = EmailClickSerializer(many=True, read_only=True)
    
    # Campos calculados
    response_time_hours = serializers.SerializerMethodField()
    engagement_score = serializers.SerializerMethodField()
    
    class Meta:
        model = TrackedEmail
        fields = [
            'id', 'tracking_id', 'campaign', 'campaign_name',
            'recipient_email', 'subject', 'status', 'status_display',
            'sent_at', 'first_opened_at', 'first_clicked_at', 'replied_at',
            'open_count', 'click_count', 'response_time_hours', 'engagement_score', 'clicks'
        ]
        read_only_fields = [
            'id', 'tracking_id', 'first_opened_at', 'first_clicked_at', 'replied_at',
            'open_count', 'click_count'
        ]
    
    def get_response_time_hours(self, obj):
        """Tiempo de respuesta en horas"""
        if obj.sent_at and obj.replied_at:
            diff = obj.replied_at - obj.sent_at
            return round(diff.total_seconds() / 3600, 1)
        return None
    
    def get_engagement_score(self, obj):
        """Score de engagement personalizado"""
        score = 0
        
        # Puntos por apertura
        if obj.status in ['opened', 'clicked', 'replied']:
            score += 30
        
        # Puntos por clicks
        if obj.status in ['clicked', 'replied']:
            score += 40
        
        # Puntos por respuesta
        if obj.status == 'replied':
            score += 30
        
        # Bonus por múltiples interacciones
        if obj.open_count > 1:
            score += min(obj.open_count * 5, 20)
        
        if obj.click_count > 1:
            score += min(obj.click_count * 10, 30)
        
        # Bonus por respuesta rápida (menos de 24 horas)
        if obj.sent_at and obj.replied_at:
            diff = obj.replied_at - obj.sent_at
            if diff.total_seconds() < 86400:  # 24 horas
                score += 20
        
        return min(score, 100)  # Máximo 100


class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer para InventoryItem"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity_in_stock', 'minimum_stock_level',
            'last_updated', 'notes'
        ]
        read_only_fields = ['id', 'last_updated']


# Serializers para resúmenes y reportes
class DashboardMetricsSerializer(serializers.Serializer):
    """Serializer para métricas del dashboard"""
    total_purchase_orders = serializers.IntegerField()
    total_suppliers = serializers.IntegerField()
    total_emails_tracked = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    confirmed_orders = serializers.IntegerField()
    emails_this_week = serializers.IntegerField()
    open_rate_this_week = serializers.FloatField()


class EmailPerformanceSerializer(serializers.Serializer):
    """Serializer para performance de emails"""
    date = serializers.DateField()
    day_name = serializers.CharField()
    sent = serializers.IntegerField()
    opened = serializers.IntegerField()
    clicked = serializers.IntegerField()
    replied = serializers.IntegerField()
    open_rate = serializers.FloatField()
    click_rate = serializers.FloatField()
    reply_rate = serializers.FloatField()


class SupplierPerformanceSerializer(serializers.Serializer):
    """Serializer para performance de suppliers"""
    supplier_name = serializers.CharField()
    supplier_id = serializers.IntegerField()
    order_count = serializers.IntegerField()
    total_value = serializers.FloatField()
    avg_response_time = serializers.FloatField(allow_null=True)
    reliability_score = serializers.FloatField()
