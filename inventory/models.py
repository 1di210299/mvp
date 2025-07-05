from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json


# ===== MIXIN PARA CAMPOS PERSONALIZADOS =====

class CustomFieldMixin:
    """Mixin para agregar funcionalidad de campos personalizados a los modelos"""
    
    def get_custom_fields(self):
        """Obtiene todos los campos personalizados definidos para este modelo"""
        if not hasattr(self, '_custom_fields_cache'):
            model_name = self._meta.model_name
            
            # Mapeo de nombres de modelo
            model_type_map = {
                'product': 'product',
                'supplier': 'supplier',
                'category': 'category',
                'inventoryitem': 'inventory_item',
                'transaction': 'transaction',
            }
            
            model_type = model_type_map.get(model_name)
            if model_type and hasattr(self, 'company'):
                self._custom_fields_cache = CustomFieldDefinition.objects.filter(
                    company=self.company,
                    model_type=model_type,
                    is_active=True
                ).order_by('order', 'field_name')
            else:
                self._custom_fields_cache = CustomFieldDefinition.objects.none()
        
        return self._custom_fields_cache
    
    def get_custom_field_values(self):
        """Obtiene los valores de los campos personalizados para esta instancia"""
        if not self.pk:
            return {}
        
        content_type = ContentType.objects.get_for_model(self)
        values = CustomFieldValue.objects.filter(
            content_type=content_type,
            object_id=self.pk
        ).select_related('custom_field')
        
        return {value.custom_field.field_name: value.get_value() for value in values}
    
    def set_custom_field_value(self, field_name, value):
        """Establece el valor de un campo personalizado"""
        if not self.pk:
            raise ValueError("El objeto debe estar guardado antes de establecer campos personalizados")
        
        try:
            custom_field = self.get_custom_fields().get(field_name=field_name)
        except CustomFieldDefinition.DoesNotExist:
            raise ValueError(f"Campo personalizado '{field_name}' no existe para este modelo")
        
        content_type = ContentType.objects.get_for_model(self)
        
        field_value, created = CustomFieldValue.objects.get_or_create(
            custom_field=custom_field,
            content_type=content_type,
            object_id=self.pk
        )
        
        field_value.set_value(value)
        field_value.save()
        
        return field_value


class Category(CustomFieldMixin, models.Model):
    """Categorías de productos"""
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100, verbose_name="Nombre de categoría")
    description = models.TextField(blank=True, verbose_name="Descripción")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Categoría padre"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        unique_together = [['company', 'name']]
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Supplier(CustomFieldMixin, models.Model):
    """Proveedores"""
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='suppliers'
    )
    name = models.CharField(max_length=200, verbose_name="Nombre del proveedor")
    ruc = models.CharField(max_length=11, blank=True, verbose_name="RUC")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="Persona de contacto")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    address = models.TextField(blank=True, verbose_name="Dirección")
    
    # Términos comerciales
    payment_terms = models.CharField(max_length=100, blank=True, verbose_name="Términos de pago")
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Límite de crédito"
    )
    lead_time = models.PositiveIntegerField(default=7, verbose_name="Tiempo de entrega (días)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        unique_together = [['company', 'ruc']]
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Location(models.Model):
    """Ubicaciones de almacén"""
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='locations'
    )
    name = models.CharField(max_length=100, verbose_name="Nombre de ubicación")
    code = models.CharField(max_length=20, verbose_name="Código de ubicación")
    description = models.TextField(blank=True, verbose_name="Descripción")
    warehouse = models.CharField(max_length=100, verbose_name="Almacén")
    zone = models.CharField(max_length=50, blank=True, verbose_name="Zona")
    aisle = models.CharField(max_length=10, blank=True, verbose_name="Pasillo")
    rack = models.CharField(max_length=10, blank=True, verbose_name="Estante")
    shelf = models.CharField(max_length=10, blank=True, verbose_name="Nivel")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        unique_together = [['company', 'code']]
        ordering = ['warehouse', 'zone', 'aisle']
    
    def __str__(self):
        return f"{self.warehouse} - {self.name}"


class Product(CustomFieldMixin, models.Model):
    """Productos/SKUs"""
    
    UNIT_CHOICES = [
        ('unit', 'Unidad'),
        ('kg', 'Kilogramo'),
        ('lb', 'Libra'),
        ('liter', 'Litro'),
        ('gallon', 'Galón'),
        ('meter', 'Metro'),
        ('box', 'Caja'),
        ('pack', 'Paquete'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='products'
    )
    sku = models.CharField(max_length=100, verbose_name="SKU")
    name = models.CharField(max_length=200, verbose_name="Nombre del producto")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # Información del producto
    barcode = models.CharField(max_length=50, blank=True, verbose_name="Código de barras")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='unit', verbose_name="Unidad de medida")
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Peso")
    dimensions = models.CharField(max_length=100, blank=True, verbose_name="Dimensiones")
    
    # Precios
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Precio de costo"
    )
    sale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Precio de venta"
    )
    
    # Configuración de inventario
    min_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Stock mínimo"
    )
    max_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Stock máximo"
    )
    reorder_point = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Punto de reorden"
    )
    
    # Control de lotes y vencimiento
    track_batches = models.BooleanField(default=False, verbose_name="Controlar lotes")
    has_expiration = models.BooleanField(default=False, verbose_name="Tiene vencimiento")
    shelf_life_days = models.PositiveIntegerField(null=True, blank=True, verbose_name="Vida útil (días)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        unique_together = [['company', 'sku']]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    @property
    def current_stock(self):
        """Stock actual del producto"""
        return self.inventory_items.filter(
            is_active=True
        ).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def stock_value(self):
        """Valor del stock actual"""
        return self.current_stock * self.cost_price


class InventoryItem(models.Model):
    """Items de inventario por ubicación"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_items'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='inventory_items'
    )
    
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Cantidad"
    )
    reserved_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Cantidad reservada"
    )
    
    # Control de lotes
    batch_number = models.CharField(max_length=50, blank=True, verbose_name="Número de lote")
    manufacturing_date = models.DateField(null=True, blank=True, verbose_name="Fecha de fabricación")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="Fecha de vencimiento")
    
    # Costo promedio ponderado
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Costo unitario"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Item de inventario"
        verbose_name_plural = "Items de inventario"
        unique_together = [['product', 'location', 'batch_number']]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.sku} - {self.location.name} - {self.quantity}"
    
    @property
    def available_quantity(self):
        """Cantidad disponible (no reservada)"""
        return self.quantity - self.reserved_quantity
    
    @property
    def total_value(self):
        """Valor total del item"""
        return self.quantity * self.unit_cost


class Transaction(models.Model):
    """Transacciones de inventario"""
    
    TRANSACTION_TYPES = [
        ('purchase', 'Compra'),
        ('sale', 'Venta'),
        ('adjustment', 'Ajuste'),
        ('transfer', 'Transferencia'),
        ('return', 'Devolución'),
        ('waste', 'Merma'),
        ('initial', 'Inventario inicial'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name="Tipo de transacción"
    )
    reference_number = models.CharField(max_length=100, verbose_name="Número de referencia")
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Cantidad"
    )
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Costo unitario"
    )
    
    # Información adicional
    batch_number = models.CharField(max_length=50, blank=True, verbose_name="Número de lote")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="Fecha de vencimiento")
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    # Referencias a documentos
    document_type = models.CharField(max_length=50, blank=True, verbose_name="Tipo de documento")
    document_number = models.CharField(max_length=100, blank=True, verbose_name="Número de documento")
    
    # Usuario y fechas
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions'
    )
    transaction_date = models.DateTimeField(verbose_name="Fecha de transacción")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.product.sku} - {self.quantity}"
    
    @property
    def total_amount(self):
        """Monto total de la transacción"""
        return abs(self.quantity) * self.unit_cost


# ===== MODELOS DE CAMPOS PERSONALIZADOS =====

class CustomFieldDefinition(models.Model):
    """Define campos personalizados que cada empresa puede agregar"""
    
    FIELD_TYPES = [
        ('text', 'Texto'),
        ('number', 'Número'),
        ('decimal', 'Decimal'),
        ('date', 'Fecha'),
        ('datetime', 'Fecha y Hora'),
        ('boolean', 'Sí/No'),
        ('choice', 'Lista de opciones'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('phone', 'Teléfono'),
    ]
    
    MODEL_TYPES = [
        ('product', 'Producto'),
        ('supplier', 'Proveedor'),
        ('category', 'Categoría'),
        ('inventory_item', 'Item de Inventario'),
        ('transaction', 'Transacción'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='custom_field_definitions'
    )
    
    # Para qué modelo se aplica este campo
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)
    
    # Definición del campo
    field_name = models.CharField(max_length=100, verbose_name="Nombre del campo")
    field_label = models.CharField(max_length=200, verbose_name="Etiqueta mostrada")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    
    # Opciones adicionales
    is_required = models.BooleanField(default=False, verbose_name="Campo obligatorio")
    default_value = models.TextField(blank=True, verbose_name="Valor por defecto")
    help_text = models.TextField(blank=True, verbose_name="Texto de ayuda")
    
    # Para campos de tipo 'choice'
    choices_json = models.TextField(
        blank=True, 
        verbose_name="Opciones (JSON)",
        help_text="Para campos de tipo 'choice', formato: [{'value': 'val1', 'label': 'Label 1'}]"
    )
    
    # Validaciones
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    
    # Metadatos
    order = models.IntegerField(default=0, verbose_name="Orden de visualización")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['company', 'model_type', 'field_name']]
        ordering = ['model_type', 'order', 'field_name']
    
    def __str__(self):
        return f"{self.company.name} - {self.get_model_type_display()} - {self.field_label}"
    
    def get_choices(self):
        """Obtiene las opciones para campos de tipo choice"""
        if self.field_type == 'choice' and self.choices_json:
            try:
                import json
                return json.loads(self.choices_json)
            except json.JSONDecodeError:
                return []
        return []


class CustomFieldValue(models.Model):
    """Almacena los valores de los campos personalizados"""
    
    custom_field = models.ForeignKey(
        CustomFieldDefinition,
        on_delete=models.CASCADE,
        related_name='values'
    )
    
    # Referencia genérica al objeto que tiene este valor
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Valores para diferentes tipos de datos
    text_value = models.TextField(blank=True)
    number_value = models.BigIntegerField(null=True, blank=True)
    decimal_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    date_value = models.DateField(null=True, blank=True)
    datetime_value = models.DateTimeField(null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['custom_field', 'content_type', 'object_id']]
    
    def get_value(self):
        """Obtiene el valor apropiado según el tipo de campo"""
        field_type = self.custom_field.field_type
        
        if field_type == 'text' or field_type == 'choice' or field_type == 'email' or field_type == 'url' or field_type == 'phone':
            return self.text_value
        elif field_type == 'number':
            return self.number_value
        elif field_type == 'decimal':
            return self.decimal_value
        elif field_type == 'date':
            return self.date_value
        elif field_type == 'datetime':
            return self.datetime_value
        elif field_type == 'boolean':
            return self.boolean_value
        
        return None
    
    def set_value(self, value):
        """Establece el valor apropiado según el tipo de campo"""
        field_type = self.custom_field.field_type
        
        # Limpiar valores anteriores
        self.text_value = ''
        self.number_value = None
        self.decimal_value = None
        self.date_value = None
        self.datetime_value = None
        self.boolean_value = None
        
        if field_type in ['text', 'choice', 'email', 'url', 'phone']:
            self.text_value = str(value) if value is not None else ''
        elif field_type == 'number':
            self.number_value = int(value) if value is not None else None
        elif field_type == 'decimal':
            self.decimal_value = float(value) if value is not None else None
        elif field_type == 'date':
            self.date_value = value
        elif field_type == 'datetime':
            self.datetime_value = value
        elif field_type == 'boolean':
            self.boolean_value = bool(value) if value is not None else None
