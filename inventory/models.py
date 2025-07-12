from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre del proveedor")
    contact_name = models.CharField(max_length=100, blank=True, verbose_name="Persona de contacto")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    address = models.TextField(blank=True, verbose_name="Dirección")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
    country = models.CharField(max_length=100, blank=True, default='Perú', verbose_name="País")
    tax_id = models.CharField(max_length=20, blank=True, verbose_name="RUC/Tax ID")
    payment_terms = models.CharField(max_length=100, blank=True, verbose_name="Términos de pago")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['name']

class Location(models.Model):
    """Modelo para ubicaciones de inventario"""
    name = models.CharField(max_length=100, verbose_name="Nombre de ubicación")
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descripción")
    warehouse = models.CharField(max_length=100, verbose_name="Almacén")
    zone = models.CharField(max_length=50, blank=True, verbose_name="Zona")
    aisle = models.CharField(max_length=10, blank=True, verbose_name="Pasillo")
    rack = models.CharField(max_length=10, blank=True, verbose_name="Estante")
    shelf = models.CharField(max_length=10, blank=True, verbose_name="Nivel")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        ordering = ['warehouse', 'zone', 'aisle']

class Product(models.Model):
    # Campos básicos
    name = models.CharField(max_length=200, verbose_name="Nombre del producto")
    sku = models.CharField(max_length=100, unique=True, verbose_name="SKU")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Relaciones
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Empresa"
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="Categoría")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="Proveedor")
    
    # Precios
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio de costo")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio de venta")
    
    # Stock
    stock = models.IntegerField(default=0, verbose_name="Stock actual")
    min_stock = models.IntegerField(default=0, verbose_name="Stock mínimo")
    max_stock = models.IntegerField(default=100, verbose_name="Stock máximo")
    reorder_point = models.IntegerField(default=10, verbose_name="Punto de reorden")
    
    # Otros campos
    unit = models.CharField(max_length=20, default='unidad', verbose_name="Unidad de medida")
    barcode = models.CharField(max_length=50, blank=True, verbose_name="Código de barras")
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Peso")
    dimensions = models.CharField(max_length=100, blank=True, verbose_name="Dimensiones")
    
    # Campos de control
    track_batches = models.BooleanField(default=False, verbose_name="Controlar lotes")
    has_expiration = models.BooleanField(default=False, verbose_name="Tiene vencimiento")
    shelf_life_days = models.PositiveIntegerField(null=True, blank=True, verbose_name="Vida útil (días)")
    
    # Control general
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Propiedades que el frontend espera
    @property
    def current_stock(self):
        return self.stock
    
    @property
    def category_name(self):
        return self.category.name if self.category else None
    
    @property
    def supplier_name(self):
        return self.supplier.name if self.supplier else None
    
    @property
    def unit_price(self):
        return self.sale_price
    
    @property
    def stock_value(self):
        return float(self.stock) * float(self.cost_price) if self.stock and self.cost_price else 0
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['name']

class InventoryItem(models.Model):
    """Modelo para items de inventario por ubicación"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_items", verbose_name="Producto")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="inventory_items", verbose_name="Ubicación")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Cantidad")
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Cantidad reservada")
    unit_cost = models.DecimalField(max_digits=12, decimal_places=4, verbose_name="Costo unitario")
    batch_number = models.CharField(max_length=50, blank=True, verbose_name="Número de lote")
    manufacturing_date = models.DateField(null=True, blank=True, verbose_name="Fecha de fabricación")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="Fecha de vencimiento")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} en {self.location.name} - {self.quantity}"
    
    class Meta:
        verbose_name = "Item de inventario"
        verbose_name_plural = "Items de inventario"
        ordering = ['-created_at']
        unique_together = ['product', 'location', 'batch_number']

class Transaction(models.Model):
    """Modelo para transacciones de inventario"""
    TRANSACTION_TYPES = [
        ('sale', 'Venta'),
        ('purchase', 'Compra'),
        ('adjustment', 'Ajuste'),
        ('transfer', 'Transferencia'),
        ('return', 'Devolución'),
        ('waste', 'Merma'),
        ('usage', 'Uso'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="transactions")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="transactions", null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    transaction_date = models.DateTimeField()  # CAMBIADO: Removido auto_now_add=True para permitir fechas específicas
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.transaction_type}: {self.product.name} - {self.quantity}"
    
    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        ordering = ['-transaction_date']

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    date_sold = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=100, blank=True)
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Venta: {self.product.name} - {self.quantity} unidades"
    
    class Meta:
        ordering = ['-date_sold']

class Customer(models.Model):
    """Modelo para clientes"""
    name = models.CharField(max_length=200, verbose_name="Nombre")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    address = models.TextField(blank=True, verbose_name="Dirección")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
    country = models.CharField(max_length=100, default='Perú', verbose_name="País")
    tax_id = models.CharField(max_length=20, blank=True, verbose_name="RUC/DNI")
    customer_type = models.CharField(max_length=20, choices=[
        ('individual', 'Persona Natural'),
        ('business', 'Empresa'),
    ], default='individual', verbose_name="Tipo de cliente")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Límite de crédito")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['name']


class Lead(models.Model):
    """Modelo para leads/prospectos"""
    name = models.CharField(max_length=200, verbose_name="Nombre")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    company = models.CharField(max_length=200, blank=True, verbose_name="Empresa")
    source = models.CharField(max_length=50, choices=[
        ('web', 'Sitio Web'),
        ('phone', 'Llamada'),
        ('email', 'Email'),
        ('referral', 'Referido'),
        ('social', 'Redes Sociales'),
        ('other', 'Otro'),
    ], default='web', verbose_name="Fuente")
    status = models.CharField(max_length=20, choices=[
        ('new', 'Nuevo'),
        ('contacted', 'Contactado'),
        ('qualified', 'Calificado'),
        ('proposal', 'Propuesta'),
        ('negotiation', 'Negociación'),
        ('won', 'Ganado'),
        ('lost', 'Perdido'),
    ], default='new', verbose_name="Estado")
    interested_products = models.ManyToManyField(Product, blank=True, verbose_name="Productos de interés")
    notes = models.TextField(blank=True, verbose_name="Notas")
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor estimado")
    expected_close_date = models.DateField(null=True, blank=True, verbose_name="Fecha estimada de cierre")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Asignado a")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ['-created_at']

class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ]
    
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"Alerta {self.severity}: {self.message[:50]}"
    
    class Meta:
        ordering = ['-created_at']

class InventoryHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stock_before = models.IntegerField()
    stock_after = models.IntegerField()
    change_reason = models.CharField(max_length=100)
    date_changed = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.product.name}: {self.stock_before} -> {self.stock_after}"
    
    class Meta:
        ordering = ['-date_changed']
        verbose_name_plural = "Inventory Histories"
