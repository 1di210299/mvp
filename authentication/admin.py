from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Company, User, TenantConfig, UsageLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'ruc', 'industry', 'subscription_type', 'is_active', 'created_at')
    list_filter = ('subscription_type', 'is_active', 'industry', 'created_at')
    search_fields = ('name', 'ruc', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'ruc', 'address', 'phone', 'email', 'industry', 'website')
        }),
        ('Configuración', {
            'fields': ('max_users', 'subscription_type', 'is_active')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'company', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'company', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'company__name')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información de la empresa', {
            'fields': ('company', 'role', 'phone', 'position', 'department')
        }),
        ('Configuraciones', {
            'fields': ('email_notifications', 'dashboard_preferences')
        }),
        ('Metadatos adicionales', {
            'fields': ('last_login_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información adicional', {
            'fields': ('email', 'company', 'role', 'first_name', 'last_name')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login_ip')


@admin.register(TenantConfig)
class TenantConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'email_address', 'verification_status', 'is_active', 'created_at')
    list_filter = ('verification_status', 'is_active', 'created_at')
    search_fields = ('name', 'domain', 'email_address')
    readonly_fields = ('tenant_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información básica', {
            'fields': ('tenant_id', 'name', 'domain', 'email_address')
        }),
        ('Configuración WhatsApp', {
            'fields': ('phone_number_id', 'wa_token'),
            'classes': ('collapse',)
        }),
        ('Configuración G Suite', {
            'fields': ('gsuite_key',),
            'classes': ('collapse',)
        }),
        ('Configuración DNS/DKIM', {
            'fields': ('dkim_selector', 'dns_zone_id'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('verification_status', 'is_active')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        # Ocultar campos sensibles en el admin
        if obj:
            readonly.extend(['wa_token', 'gsuite_key'])
        return readonly


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'channel', 'action', 'status', 'timestamp', 'retry_count')
    list_filter = ('channel', 'status', 'timestamp', 'tenant')
    search_fields = ('tenant__name', 'tenant__domain', 'action', 'details')
    readonly_fields = ('request_id', 'timestamp')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Información básica', {
            'fields': ('tenant', 'channel', 'action', 'status')
        }),
        ('Detalles', {
            'fields': ('details', 'error_message', 'retry_count'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('request_id', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Los logs se crean automáticamente, no manualmente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Los logs no deben modificarse
        return False
