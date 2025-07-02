from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
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


class Supplier(models.Model):
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


class Product(models.Model):
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
