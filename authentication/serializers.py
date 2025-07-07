from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Company, User


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
