from django.db import models
from django.contrib.auth import get_user_model
import json
from datetime import datetime

User = get_user_model()


class DataImportSession(models.Model):
    """Sesión de importación de datos"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('mapping', 'Mapeando'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    IMPORT_TYPES = [
        ('products', 'Productos'),
        ('suppliers', 'Proveedores'),
        ('categories', 'Categorías'),
        ('customers', 'Clientes'),
        ('leads', 'Leads'),
        ('inventory', 'Inventario'),
        ('transactions', 'Transacciones'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='import_sessions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='import_sessions'
    )
    
    # Información básica
    import_type = models.CharField(max_length=20, choices=IMPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    
    # Análisis del archivo
    total_rows = models.IntegerField(default=0)
    header_row = models.IntegerField(default=1)
    detected_columns = models.JSONField(default=list)  # Lista de columnas detectadas
    
    # Resultados de procesamiento
    processed_rows = models.IntegerField(default=0)
    successful_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    error_log = models.JSONField(default=list)
    
    # Configuración
    skip_duplicates = models.BooleanField(default=True)
    update_existing = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sesión de Importación"
        verbose_name_plural = "Sesiones de Importación"
    
    def __str__(self):
        return f"{self.import_type} - {self.original_filename} ({self.status})"


class ColumnMapping(models.Model):
    """Mapeo de columnas del archivo a campos del sistema"""
    
    import_session = models.ForeignKey(
        DataImportSession,
        on_delete=models.CASCADE,
        related_name='column_mappings'
    )
    
    # Columna del archivo
    source_column = models.CharField(max_length=255)  # Nombre de la columna en el archivo
    source_index = models.IntegerField()  # Índice de la columna (0-based)
    
    # Campo del sistema
    target_field = models.CharField(max_length=100)  # Campo del modelo Django
    field_type = models.CharField(max_length=50)  # Tipo de campo
    is_required = models.BooleanField(default=False)
    
    # Transformaciones
    default_value = models.TextField(blank=True)
    transformation_rules = models.JSONField(default=dict)  # Reglas de transformación
    
    # Validación
    sample_values = models.JSONField(default=list)  # Valores de muestra
    validation_errors = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['import_session', 'source_column']]
        ordering = ['source_index']
    
    def __str__(self):
        return f"{self.source_column} -> {self.target_field}"


class ImportTemplate(models.Model):
    """Plantillas de importación reutilizables"""
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='import_templates'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_templates'
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    import_type = models.CharField(max_length=20, choices=DataImportSession.IMPORT_TYPES)
    
    # Configuración guardada
    column_mappings = models.JSONField(default=dict)
    import_settings = models.JSONField(default=dict)
    
    is_default = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['company', 'name', 'import_type']]
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.import_type})"


class FieldDefinition(models.Model):
    """Definición de campos disponibles para cada tipo de importación"""
    
    FIELD_TYPES = [
        ('text', 'Texto'),
        ('number', 'Número'),
        ('decimal', 'Decimal'),
        ('date', 'Fecha'),
        ('datetime', 'Fecha y Hora'),
        ('boolean', 'Sí/No'),
        ('email', 'Email'),
        ('phone', 'Teléfono'),
        ('choice', 'Lista de opciones'),
        ('foreign_key', 'Relación'),
    ]
    
    import_type = models.CharField(max_length=20, choices=DataImportSession.IMPORT_TYPES)
    field_name = models.CharField(max_length=100)  # Nombre del campo en el modelo
    display_name = models.CharField(max_length=200)  # Nombre mostrado al usuario
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    description = models.TextField(blank=True)
    
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.TextField(blank=True)
    
    # Para campos de relación
    related_model = models.CharField(max_length=100, blank=True)
    lookup_field = models.CharField(max_length=100, blank=True)
    
    # Para campos de elección
    choices = models.JSONField(default=list)
    
    # Validaciones
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    min_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    max_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    regex_pattern = models.CharField(max_length=500, blank=True)
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [['import_type', 'field_name']]
        ordering = ['import_type', 'order', 'display_name']
    
    def __str__(self):
        return f"{self.import_type} - {self.display_name}"


# Datos iniciales para los campos disponibles
FIELD_DEFINITIONS = {
    'products': [
        {'field_name': 'sku', 'display_name': 'SKU', 'field_type': 'text', 'is_required': True, 'is_unique': True, 'description': 'Código único del producto'},
        {'field_name': 'name', 'display_name': 'Nombre del Producto', 'field_type': 'text', 'is_required': True, 'description': 'Nombre descriptivo del producto'},
        {'field_name': 'description', 'display_name': 'Descripción', 'field_type': 'text', 'description': 'Descripción detallada del producto'},
        {'field_name': 'category', 'display_name': 'Categoría', 'field_type': 'foreign_key', 'related_model': 'Category', 'lookup_field': 'name', 'description': 'Categoría del producto'},
        {'field_name': 'supplier', 'display_name': 'Proveedor', 'field_type': 'foreign_key', 'related_model': 'Supplier', 'lookup_field': 'name', 'description': 'Proveedor del producto'},
        {'field_name': 'barcode', 'display_name': 'Código de Barras', 'field_type': 'text', 'description': 'Código de barras del producto'},
        {'field_name': 'unit', 'display_name': 'Unidad de Medida', 'field_type': 'choice', 'choices': [
            {'value': 'unit', 'label': 'Unidad'},
            {'value': 'kg', 'label': 'Kilogramo'},
            {'value': 'lb', 'label': 'Libra'},
            {'value': 'liter', 'label': 'Litro'},
            {'value': 'gallon', 'label': 'Galón'},
            {'value': 'meter', 'label': 'Metro'},
            {'value': 'box', 'label': 'Caja'},
            {'value': 'pack', 'label': 'Paquete'},
        ]},
        {'field_name': 'cost_price', 'display_name': 'Precio de Costo', 'field_type': 'decimal', 'is_required': True, 'min_value': 0, 'description': 'Precio de compra del producto'},
        {'field_name': 'sale_price', 'display_name': 'Precio de Venta', 'field_type': 'decimal', 'is_required': True, 'min_value': 0, 'description': 'Precio de venta del producto'},
        {'field_name': 'min_stock', 'display_name': 'Stock Mínimo', 'field_type': 'decimal', 'min_value': 0, 'description': 'Cantidad mínima en inventario'},
        {'field_name': 'max_stock', 'display_name': 'Stock Máximo', 'field_type': 'decimal', 'min_value': 0, 'description': 'Cantidad máxima en inventario'},
        {'field_name': 'reorder_point', 'display_name': 'Punto de Reorden', 'field_type': 'decimal', 'min_value': 0, 'description': 'Punto de reorden automático'},
        {'field_name': 'weight', 'display_name': 'Peso', 'field_type': 'decimal', 'min_value': 0, 'description': 'Peso del producto'},
        {'field_name': 'dimensions', 'display_name': 'Dimensiones', 'field_type': 'text', 'description': 'Dimensiones del producto'},
        {'field_name': 'track_batches', 'display_name': 'Controlar Lotes', 'field_type': 'boolean', 'description': 'Si el producto maneja lotes'},
        {'field_name': 'has_expiration', 'display_name': 'Tiene Vencimiento', 'field_type': 'boolean', 'description': 'Si el producto tiene fecha de vencimiento'},
        {'field_name': 'shelf_life_days', 'display_name': 'Vida Útil (días)', 'field_type': 'number', 'min_value': 0, 'description': 'Días de vida útil del producto'},
    ],
    'suppliers': [
        {'field_name': 'name', 'display_name': 'Nombre del Proveedor', 'field_type': 'text', 'is_required': True, 'description': 'Nombre o razón social del proveedor'},
        {'field_name': 'ruc', 'display_name': 'RUC', 'field_type': 'text', 'is_unique': True, 'description': 'Número de RUC del proveedor'},
        {'field_name': 'contact_person', 'display_name': 'Persona de Contacto', 'field_type': 'text', 'description': 'Nombre de la persona de contacto'},
        {'field_name': 'email', 'display_name': 'Email', 'field_type': 'email', 'description': 'Correo electrónico del proveedor'},
        {'field_name': 'phone', 'display_name': 'Teléfono', 'field_type': 'phone', 'description': 'Número de teléfono'},
        {'field_name': 'address', 'display_name': 'Dirección', 'field_type': 'text', 'description': 'Dirección física del proveedor'},
        {'field_name': 'payment_terms', 'display_name': 'Términos de Pago', 'field_type': 'text', 'description': 'Condiciones de pago'},
        {'field_name': 'credit_limit', 'display_name': 'Límite de Crédito', 'field_type': 'decimal', 'min_value': 0, 'description': 'Límite de crédito otorgado'},
        {'field_name': 'lead_time', 'display_name': 'Tiempo de Entrega (días)', 'field_type': 'number', 'min_value': 0, 'description': 'Días de tiempo de entrega'},
    ],
    'categories': [
        {'field_name': 'name', 'display_name': 'Nombre de Categoría', 'field_type': 'text', 'is_required': True, 'is_unique': True, 'description': 'Nombre de la categoría'},
        {'field_name': 'description', 'display_name': 'Descripción', 'field_type': 'text', 'description': 'Descripción de la categoría'},
        {'field_name': 'parent', 'display_name': 'Categoría Padre', 'field_type': 'foreign_key', 'related_model': 'Category', 'lookup_field': 'name', 'description': 'Categoría principal (para subcategorías)'},
    ],
    'customers': [
        {'field_name': 'customer_type', 'display_name': 'Tipo de Cliente', 'field_type': 'choice', 'choices': [
            {'value': 'individual', 'label': 'Persona Natural'},
            {'value': 'business', 'label': 'Empresa'}
        ], 'description': 'Tipo de cliente'},
        {'field_name': 'first_name', 'display_name': 'Nombres', 'field_type': 'text', 'description': 'Nombres del cliente (persona natural)'},
        {'field_name': 'last_name', 'display_name': 'Apellidos', 'field_type': 'text', 'description': 'Apellidos del cliente (persona natural)'},
        {'field_name': 'business_name', 'display_name': 'Razón Social', 'field_type': 'text', 'description': 'Razón social (empresa)'},
        {'field_name': 'trade_name', 'display_name': 'Nombre Comercial', 'field_type': 'text', 'description': 'Nombre comercial (empresa)'},
        {'field_name': 'document_type', 'display_name': 'Tipo de Documento', 'field_type': 'text', 'description': 'Tipo de documento de identidad'},
        {'field_name': 'document_number', 'display_name': 'Número de Documento', 'field_type': 'text', 'is_unique': True, 'description': 'Número de documento de identidad'},
        {'field_name': 'email', 'display_name': 'Email', 'field_type': 'email', 'description': 'Correo electrónico'},
        {'field_name': 'phone', 'display_name': 'Teléfono', 'field_type': 'phone', 'description': 'Número de teléfono'},
        {'field_name': 'mobile', 'display_name': 'Celular', 'field_type': 'phone', 'description': 'Número de celular'},
        {'field_name': 'address', 'display_name': 'Dirección', 'field_type': 'text', 'description': 'Dirección completa'},
        {'field_name': 'city', 'display_name': 'Ciudad', 'field_type': 'text', 'description': 'Ciudad'},
        {'field_name': 'state', 'display_name': 'Región', 'field_type': 'text', 'description': 'Región o estado'},
        {'field_name': 'country', 'display_name': 'País', 'field_type': 'text', 'default_value': 'Perú', 'description': 'País'},
        {'field_name': 'postal_code', 'display_name': 'Código Postal', 'field_type': 'text', 'description': 'Código postal'},
        {'field_name': 'industry', 'display_name': 'Industria', 'field_type': 'text', 'description': 'Sector o industria'},
        {'field_name': 'company_size', 'display_name': 'Tamaño de Empresa', 'field_type': 'text', 'description': 'Tamaño de la empresa'},
        {'field_name': 'annual_revenue', 'display_name': 'Ingresos Anuales', 'field_type': 'decimal', 'min_value': 0, 'description': 'Ingresos anuales estimados'},
    ],
    'leads': [
        {'field_name': 'first_name', 'display_name': 'Nombres', 'field_type': 'text', 'is_required': True, 'description': 'Nombres del lead'},
        {'field_name': 'last_name', 'display_name': 'Apellidos', 'field_type': 'text', 'is_required': True, 'description': 'Apellidos del lead'},
        {'field_name': 'email', 'display_name': 'Email', 'field_type': 'email', 'is_required': True, 'description': 'Correo electrónico'},
        {'field_name': 'phone', 'display_name': 'Teléfono', 'field_type': 'phone', 'description': 'Número de teléfono'},
        {'field_name': 'company_name', 'display_name': 'Empresa', 'field_type': 'text', 'description': 'Nombre de la empresa'},
        {'field_name': 'job_title', 'display_name': 'Cargo', 'field_type': 'text', 'description': 'Cargo en la empresa'},
        {'field_name': 'source', 'display_name': 'Fuente', 'field_type': 'choice', 'choices': [
            {'value': 'website', 'label': 'Sitio Web'},
            {'value': 'social_media', 'label': 'Redes Sociales'},
            {'value': 'email_marketing', 'label': 'Email Marketing'},
            {'value': 'referral', 'label': 'Referencia'},
            {'value': 'cold_call', 'label': 'Llamada Fría'},
            {'value': 'event', 'label': 'Evento'},
            {'value': 'advertisement', 'label': 'Publicidad'},
            {'value': 'other', 'label': 'Otro'},
        ], 'description': 'Fuente de origen del lead'},
        {'field_name': 'industry', 'display_name': 'Industria', 'field_type': 'text', 'description': 'Sector o industria'},
        {'field_name': 'budget', 'display_name': 'Presupuesto', 'field_type': 'decimal', 'min_value': 0, 'description': 'Presupuesto estimado'},
        {'field_name': 'notes', 'display_name': 'Notas', 'field_type': 'text', 'description': 'Notas adicionales'},
    ]
}
