from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Company, User, TenantConfig, UsageLog, 
    TenantCommunicationConfig, TenantAIConfig
)


class TenantAuthSerializer(serializers.Serializer):
    """Serializer para autenticación de tenants"""
    client_id = serializers.UUIDField(help_text="Tenant ID (UUID)")
    client_secret = serializers.CharField(help_text="Tenant secret key")


class CompanySerializer(serializers.ModelSerializer):
    """Serializer para Company"""
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'ruc', 'address', 'phone', 'email',
            'industry', 'website', 'max_users', 'subscription_type',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_ruc(self, value):
        """Validar formato de RUC peruano"""
        if value and len(value) != 11:
            raise serializers.ValidationError("El RUC debe tener 11 dígitos")
        if value and not value.isdigit():
            raise serializers.ValidationError("El RUC debe contener solo números")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Serializer para User"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'company', 'company_name', 'role', 'phone', 'position', 'department',
            'email_notifications', 'dashboard_preferences', 'is_active',
            'date_joined', 'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'full_name', 'company_name', 'date_joined', 
            'last_login', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'company', 'role',
            'phone', 'position', 'department'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de nuevos usuarios y empresas"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    # Campos de la empresa
    company_name = serializers.CharField(write_only=True)
    company_ruc = serializers.CharField(write_only=True)
    company_address = serializers.CharField(write_only=True)
    company_phone = serializers.CharField(write_only=True, required=False)
    company_industry = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone',
            'company_name', 'company_ruc', 'company_address', 
            'company_phone', 'company_industry'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        
        # Validar RUC
        ruc = attrs.get('company_ruc', '')
        if len(ruc) != 11 or not ruc.isdigit():
            raise serializers.ValidationError("El RUC debe tener 11 dígitos numéricos")
        
        return attrs
    
    def create(self, validated_data):
        # Extraer datos de la empresa
        company_data = {
            'name': validated_data.pop('company_name'),
            'ruc': validated_data.pop('company_ruc'),
            'address': validated_data.pop('company_address'),
            'phone': validated_data.pop('company_phone', ''),
            'industry': validated_data.pop('company_industry', ''),
            'email': validated_data['email'],  # Usar email del usuario como contacto
        }
        
        # Crear empresa
        company = Company.objects.create(**company_data)
        
        # Crear usuario administrador
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.company = company
        user.role = 'admin'  # Primer usuario es administrador
        user.set_password(password)
        user.save()
        
        return user


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil del usuario"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'company_name', 'role', 'phone', 'position', 'department',
            'email_notifications', 'dashboard_preferences'
        ]
        read_only_fields = ['id', 'username', 'company_name', 'role', 'full_name']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Las contraseñas nuevas no coinciden")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para JWT que permite login con email"""
    username_field = 'email'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField()
        self.fields['password'] = serializers.CharField()
        # Eliminar el campo username por defecto
        if 'username' in self.fields:
            del self.fields['username']
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    if not user.is_active:
                        raise serializers.ValidationError('Esta cuenta está desactivada.')
                    
                    # Usar el username para la validación del token
                    attrs['username'] = user.username
                    attrs.pop('email')  # Remover email ya que JWT espera username
                    
                    refresh = self.get_token(user)
                    
                    data = {}
                    data['refresh'] = str(refresh)
                    data['access'] = str(refresh.access_token)
                    
                    # Agregar información del usuario
                    data['user'] = {
                        'id': user.id,
                        'email': user.email,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'role': user.role,
                        'company': user.company.name if user.company else None,
                    }
                    
                    return data
                else:
                    raise serializers.ValidationError('Email o contraseña incorrectos.')
            except User.DoesNotExist:
                raise serializers.ValidationError('Email o contraseña incorrectos.')
        else:
            raise serializers.ValidationError('Debe proporcionar email y contraseña.')


# Nuevos serializers para el flujo N8N
class TenantConfigSerializer(serializers.ModelSerializer):
    """Serializer para configuración de tenants"""
    tenant_id = serializers.UUIDField(read_only=True)
    wa_token = serializers.CharField(write_only=True, required=False)
    gsuite_key = serializers.JSONField(write_only=True, required=False)
    client_secret = serializers.CharField(read_only=True)  # Visible solo en GET
    
    class Meta:
        model = TenantConfig
        fields = [
            'tenant_id', 'name', 'domain', 'email_address', 
            'phone_number_id', 'wa_token', 'gsuite_key', 
            'dkim_selector', 'dns_zone_id', 'is_active',
            'verification_status', 'client_secret', 'created_at', 'updated_at'
        ]
        read_only_fields = ['tenant_id', 'client_secret', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Extraer datos sensibles
        wa_token = validated_data.pop('wa_token', None)
        gsuite_key = validated_data.pop('gsuite_key', None)
        
        # Crear tenant
        tenant = TenantConfig.objects.create(**validated_data)
        
        # Establecer datos encriptados
        if wa_token:
            tenant.set_wa_token(wa_token)
        if gsuite_key:
            tenant.set_gsuite_key(gsuite_key)
        
        tenant.save()
        return tenant


class TenantCreateSerializer(serializers.Serializer):
    """Serializer para creación de tenants simplificado"""
    name = serializers.CharField(max_length=200)
    domain = serializers.CharField(max_length=100)
    email_address = serializers.EmailField()
    whatsapp_number = serializers.CharField(max_length=20, required=False)
    
    def validate_domain(self, value):
        """Validar que el dominio sea único"""
        if TenantConfig.objects.filter(domain=value).exists():
            raise serializers.ValidationError("Este dominio ya está registrado")
        return value


class UsageLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de uso"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_domain = serializers.CharField(source='tenant.domain', read_only=True)
    
    class Meta:
        model = UsageLog
        fields = [
            'id', 'tenant', 'tenant_name', 'tenant_domain',
            'channel', 'action', 'timestamp', 'status',
            'details', 'request_id', 'retry_count', 'error_message'
        ]
        read_only_fields = ['id', 'timestamp', 'request_id']


class WhatsAppSendSerializer(serializers.Serializer):
    """Serializer para envío de WhatsApp"""
    to = serializers.CharField(max_length=20)
    body = serializers.CharField(max_length=4096)
    
    def validate_to(self, value):
        """Validar formato de número de teléfono"""
        # Remover espacios y caracteres especiales
        cleaned = ''.join(filter(str.isdigit, value))
        if len(cleaned) < 10:
            raise serializers.ValidationError("Número de teléfono inválido")
        return value


class EmailSendSerializer(serializers.Serializer):
    """Serializer para envío de emails"""
    to = serializers.EmailField()
    subject = serializers.CharField(max_length=200)
    body = serializers.CharField()
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True
    )


class UsageReportSerializer(serializers.Serializer):
    """Serializer para reportes de uso"""
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    channel = serializers.ChoiceField(
        choices=['whatsapp', 'email', 'ocr', 'ia'],
        required=False
    )


class WebhookWhatsAppSerializer(serializers.Serializer):
    """Serializer para webhooks de WhatsApp"""
    object = serializers.CharField()
    entry = serializers.ListField()
    
    def validate(self, attrs):
        """Validar estructura del webhook"""
        if attrs.get('object') != 'whatsapp_business_account':
            raise serializers.ValidationError("Tipo de objeto inválido")
        
        entry = attrs.get('entry', [])
        if not entry:
            raise serializers.ValidationError("Entry vacío")


class TenantCommunicationConfigSerializer(serializers.ModelSerializer):
    """Serializer para configuraciones de comunicación por tenant"""
    
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    channel_preference_display = serializers.CharField(source='get_channel_preference_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = TenantCommunicationConfig
        fields = [
            'id', 'tenant', 'tenant_name', 'event_type', 'event_type_display',
            'channel_preference', 'channel_preference_display', 'priority', 'priority_display',
            'use_ai_personalization', 'custom_message_template',
            'send_immediately', 'delay_minutes', 'respect_business_hours',
            'max_retries', 'fallback_channel', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant_name', 'created_at', 'updated_at']
    
    def validate_delay_minutes(self, value):
        """Validar que el retraso sea razonable"""
        if value < 0:
            raise serializers.ValidationError("El retraso no puede ser negativo")
        if value > 10080:  # 7 días en minutos
            raise serializers.ValidationError("El retraso no puede ser mayor a 7 días")
        return value
    
    def validate_max_retries(self, value):
        """Validar número de reintentos"""
        if value < 0:
            raise serializers.ValidationError("El número de reintentos no puede ser negativo")
        if value > 10:
            raise serializers.ValidationError("El número de reintentos no puede ser mayor a 10")
        return value
    
    def validate(self, attrs):
        """Validaciones adicionales"""
        # Si no es inmediato, debe tener retraso
        if not attrs.get('send_immediately', True) and attrs.get('delay_minutes', 0) == 0:
            raise serializers.ValidationError(
                "Si no se envía inmediatamente, debe especificar un retraso en minutos"
            )
        
        # Si se especifica canal de respaldo, debe ser diferente al principal
        channel = attrs.get('channel_preference')
        fallback = attrs.get('fallback_channel')
        if fallback and fallback == channel:
            raise serializers.ValidationError(
                "El canal de respaldo debe ser diferente al canal principal"
            )
        
        return attrs


class TenantAIConfigSerializer(serializers.ModelSerializer):
    """Serializer para configuraciones de IA por tenant"""
    
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    ai_provider_display = serializers.CharField(source='get_ai_provider_display', read_only=True)
    default_tone_display = serializers.CharField(source='get_default_tone_display', read_only=True)
    can_use_ai = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TenantAIConfig
        fields = [
            'id', 'tenant', 'tenant_name', 'ai_provider', 'ai_provider_display',
            'api_key_encrypted', 'custom_api_url', 'default_tone', 'default_tone_display',
            'brand_voice_description', 'custom_instructions', 'max_tokens', 'temperature',
            'include_customer_history', 'include_product_info', 'daily_ai_limit',
            'require_human_approval', 'can_use_ai', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant_name', 'can_use_ai', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key_encrypted': {'write_only': True}
        }
    
    def validate_temperature(self, value):
        """Validar temperatura de IA"""
        if value < 0.0 or value > 1.0:
            raise serializers.ValidationError("La temperatura debe estar entre 0.0 y 1.0")
        return value
    
    def validate_max_tokens(self, value):
        """Validar número máximo de tokens"""
        if value <= 0:
            raise serializers.ValidationError("El número de tokens debe ser mayor a 0")
        if value > 4000:
            raise serializers.ValidationError("El número de tokens no puede ser mayor a 4000")
        return value
    
    def validate_daily_ai_limit(self, value):
        """Validar límite diario de IA"""
        if value <= 0:
            raise serializers.ValidationError("El límite diario debe ser mayor a 0")
        if value > 10000:
            raise serializers.ValidationError("El límite diario no puede ser mayor a 10,000")
        return value
    
    def validate(self, attrs):
        """Validaciones adicionales"""
        ai_provider = attrs.get('ai_provider')
        api_key = attrs.get('api_key_encrypted')
        custom_url = attrs.get('custom_api_url')
        
        # Si el proveedor es custom, requiere URL personalizada
        if ai_provider == 'custom' and not custom_url:
            raise serializers.ValidationError(
                "Para el proveedor personalizado se requiere una URL de API"
            )
        
        # Si el proveedor no es disabled, debe tener alguna configuración
        if ai_provider != 'disabled' and not api_key and ai_provider != 'custom':
            # Para proveedores estándar sin API key, usar configuración por defecto del sistema
            pass
        
        return attrs


class TenantConfigSummarySerializer(serializers.Serializer):
    """Serializer para resumen de configuración de tenant"""
    
    tenant_info = serializers.DictField()
    configuration_summary = serializers.DictField()
    ai_configuration = serializers.DictField(allow_null=True)
    communication_configs = TenantCommunicationConfigSerializer(many=True)
    ai_config = TenantAIConfigSerializer(allow_null=True)


class BulkConfigSetupSerializer(serializers.Serializer):
    """Serializer para configuración masiva de eventos"""
    
    configurations = serializers.ListField(
        child=TenantCommunicationConfigSerializer(),
        min_length=1,
        help_text="Lista de configuraciones a crear/actualizar"
    )
    
    def validate_configurations(self, value):
        """Validar que no haya eventos duplicados"""
        event_types = [config.get('event_type') for config in value]
        if len(event_types) != len(set(event_types)):
            raise serializers.ValidationError("No puede haber eventos duplicados")
        return value


class DefaultSetupSerializer(serializers.Serializer):
    """Serializer para configuración por defecto de tenant"""
    
    default_channel = serializers.ChoiceField(
        choices=TenantCommunicationConfig.CHANNEL_CHOICES,
        default='both_whatsapp_primary',
        help_text="Canal por defecto para todos los eventos"
    )
    default_priority = serializers.ChoiceField(
        choices=TenantCommunicationConfig.PRIORITY_CHOICES,
        default='normal',
        help_text="Prioridad por defecto para todos los eventos"
    )
    use_ai = serializers.BooleanField(
        default=True,
        help_text="Habilitar IA por defecto"
    )
