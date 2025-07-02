from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Company(models.Model):
    """Modelo para representar las empresas en el sistema"""
    name = models.CharField(max_length=200, verbose_name="Nombre de la empresa")
    ruc = models.CharField(max_length=11, unique=True, verbose_name="RUC")
    address = models.TextField(verbose_name="Dirección")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Email de contacto")
    industry = models.CharField(max_length=100, blank=True, verbose_name="Industria")
    website = models.URLField(blank=True, verbose_name="Sitio web")
    
    # Configuración del sistema
    max_users = models.PositiveIntegerField(default=5, verbose_name="Máximo de usuarios")
    subscription_type = models.CharField(
        max_length=20,
        choices=[
            ('trial', 'Prueba'),
            ('basic', 'Básico'),
            ('premium', 'Premium'),
        ],
        default='trial',
        verbose_name="Tipo de suscripción"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    is_active = models.BooleanField(default=True, verbose_name="Empresa activa")
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""
    
    def create_user(self, username, email=None, password=None, company=None, **extra_fields):
        """Crear un usuario regular"""
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        if not company:
            raise ValueError('La empresa es obligatoria')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, company=company, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, company=None, **extra_fields):
        """Crear un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        
        return self.create_user(username, email, password, company, **extra_fields)


class User(AbstractUser):
    """Modelo de usuario personalizado"""
    
    ROLE_CHOICES = [
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrador'),
        ('analyst', 'Analista'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name="Empresa"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='analyst',
        verbose_name="Rol"
    )
    
    # Información adicional del usuario
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    position = models.CharField(max_length=100, blank=True, verbose_name="Cargo")
    department = models.CharField(max_length=100, blank=True, verbose_name="Departamento")
    
    # Configuraciones del usuario
    email_notifications = models.BooleanField(default=True, verbose_name="Notificaciones por email")
    dashboard_preferences = models.JSONField(default=dict, verbose_name="Preferencias del dashboard")
    
    # Metadatos
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Última IP de login")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    # Manager personalizado
    objects = UserManager()
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} - {self.company.name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def has_permission(self, permission):
        """Verificar si el usuario tiene un permiso específico"""
        role_permissions = {
            'superadmin': ['all'],
            'admin': ['manage_inventory', 'view_reports', 'manage_alerts', 'manage_users'],
            'analyst': ['view_reports', 'view_inventory'],
        }
        
        user_permissions = role_permissions.get(self.role, [])
        return 'all' in user_permissions or permission in user_permissions
