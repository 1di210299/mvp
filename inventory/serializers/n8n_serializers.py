"""
Serializers para APIs simplificadas con n8n
"""
from rest_framework import serializers
from inventory.models import PurchaseOrder, TenantConfig


class OrderCreateSerializer(serializers.Serializer):
    """Serializer para crear órdenes desde n8n"""
    tenant_id = serializers.IntegerField()
    product_name = serializers.CharField(max_length=200)
    product_sku = serializers.CharField(max_length=100, required=False)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    supplier_name = serializers.CharField(max_length=200, required=False)
    supplier_email = serializers.EmailField(required=False)
    supplier_whatsapp = serializers.CharField(max_length=20, required=False)
    priority = serializers.ChoiceField(
        choices=['low', 'medium', 'high', 'urgent'],
        default='medium'
    )
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, data):
        """Validar que al menos un método de contacto esté presente"""
        if not data.get('supplier_email') and not data.get('supplier_whatsapp'):
            raise serializers.ValidationError(
                "Se requiere al menos supplier_email o supplier_whatsapp"
            )
        return data


class OrderCallbackSerializer(serializers.Serializer):
    """Serializer para callbacks desde n8n"""
    order_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=['draft', 'sent', 'confirmed', 'rejected', 'delivered', 'cancelled']
    )
    supplier_response = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    delivery_date = serializers.DateField(required=False)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)


class TenantConfigSerializer(serializers.ModelSerializer):
    """Serializer para configuración de tenant"""
    
    class Meta:
        model = TenantConfig
        fields = [
            'id', 'company', 
            # Twilio/WhatsApp
            'twilio_account_sid', 'twilio_auth_token', 'whatsapp_from_number',
            # Gmail
            'gmail_client_id', 'gmail_client_secret', 'gmail_access_token', 
            'gmail_refresh_token', 'gmail_email',
            # OAuth2
            'oauth2_client_id', 'oauth2_client_secret', 'oauth2_token_url',
            # Estado
            'is_whatsapp_active', 'is_gmail_active', 
            # N8N
            'n8n_webhook_url', 
            # Computed
            'is_configured'
        ]
        read_only_fields = ['id', 'company', 'is_configured']
        extra_kwargs = {
            'twilio_auth_token': {'write_only': True},
            'gmail_client_secret': {'write_only': True},
            'gmail_access_token': {'write_only': True},
            'gmail_refresh_token': {'write_only': True},
            'oauth2_client_secret': {'write_only': True},
        }
