"""
Serializers para órdenes de compra
"""
from rest_framework import serializers
from inventory.models import PurchaseOrder, PurchaseOrderTracking, PurchaseOrderEmailLog


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer principal para órdenes de compra"""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    can_be_sent = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    # ✅ NUEVO: Campos WhatsApp
    sent_method_display = serializers.CharField(source='get_sent_method_display', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'uuid', 'order_number', 'company', 'product', 'supplier',
            'product_name', 'product_sku', 'supplier_name',
            'quantity', 'unit_price', 'total_amount',
            'status', 'status_display', 'priority', 'priority_display',
            'supplier_email', 'supplier_phone',
            
            # ✅ NUEVO: Campos WhatsApp
            'supplier_whatsapp', 'whatsapp_sent', 'whatsapp_sent_at', 
            'whatsapp_message_id', 'sent_method', 'sent_method_display',
            
            'expected_delivery_date', 'actual_delivery_date',
            'email_sent', 'email_sent_at', 'email_sent_to',
            'email_subject', 'email_content', 'notes', 'supplier_response',
            'ai_generated', 'ai_confidence_score',
            'can_be_sent', 'is_overdue',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uuid', 'order_number', 'total_amount', 'email_sent',
            'email_sent_at', 'whatsapp_sent', 'whatsapp_sent_at', 
            'whatsapp_message_id', 'sent_method', 'created_at', 'updated_at'
        ]
    
    def validate_quantity(self, value):
        """Validar cantidad"""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value
    
    def validate_unit_price(self, value):
        """Validar precio unitario"""
        if value <= 0:
            raise serializers.ValidationError("El precio unitario debe ser mayor a 0")
        return value


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear órdenes de compra"""
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'product', 'supplier', 'quantity', 'unit_price',
            'priority', 'supplier_email', 'supplier_phone',
            'expected_delivery_date', 'notes'
        ]
    
    def create(self, validated_data):
        """Crear orden de compra con company del usuario"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['company'] = request.user.company
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class PurchaseOrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar órdenes de compra"""
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'status', 'priority', 'supplier_email', 'supplier_phone',
            'expected_delivery_date', 'actual_delivery_date',
            'notes', 'supplier_response'
        ]


class PurchaseOrderTrackingSerializer(serializers.ModelSerializer):
    """Serializer para seguimiento de órdenes"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseOrderTracking
        fields = [
            'id', 'status', 'status_display', 'notes',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PurchaseOrderEmailLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de emails"""
    
    email_type_display = serializers.CharField(source='get_email_type_display', read_only=True)
    email_service_display = serializers.CharField(source='get_email_service_display', read_only=True)
    
    class Meta:
        model = PurchaseOrderEmailLog
        fields = [
            'id', 'email_type', 'email_type_display', 'recipient_email',
            'subject', 'content', 'sent_successfully', 'error_message',
            'email_service', 'email_service_display', 'sent_at'
        ]
        read_only_fields = ['id', 'sent_at']


class AutoGenerateOrderSerializer(serializers.Serializer):
    """Serializer para generar órdenes automáticas"""
    
    company_id = serializers.IntegerField(required=False, help_text="ID de la empresa (opcional)")
    force_regenerate = serializers.BooleanField(
        default=False,
        help_text="Forzar generación incluso si existen órdenes recientes"
    )
    send_emails = serializers.BooleanField(
        default=True,
        help_text="Enviar emails automáticamente"
    )
    min_stock_threshold = serializers.IntegerField(
        default=10,
        help_text="Umbral mínimo de stock para generar órdenes"
    )


class SendEmailSerializer(serializers.Serializer):
    """Serializer para enviar emails de órdenes"""
    
    recipient_email = serializers.EmailField(
        required=False,
        help_text="Email alternativo (opcional, usa el del proveedor por defecto)"
    )
    use_custom_content = serializers.BooleanField(
        default=False,
        help_text="Usar contenido personalizado"
    )
    custom_subject = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Asunto personalizado"
    )
    custom_content = serializers.CharField(
        required=False,
        help_text="Contenido personalizado del email"
    )


class PurchaseOrderStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de órdenes"""
    
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    sent_orders = serializers.IntegerField()
    received_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    overdue_orders = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_delivery_time = serializers.FloatField()
    email_success_rate = serializers.FloatField()


class ProductLowStockSerializer(serializers.Serializer):
    """Serializer para productos con stock bajo"""
    
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    current_stock = serializers.IntegerField()
    min_stock = serializers.IntegerField()
    supplier_name = serializers.CharField()
    supplier_email = serializers.EmailField()
    has_pending_order = serializers.BooleanField()
    recommended_quantity = serializers.IntegerField()
    priority = serializers.CharField()
