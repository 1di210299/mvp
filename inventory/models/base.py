from django.db import models
from django.conf import settings
import uuid

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


# =============================================================================
# PURCHASE ORDERS MODELS - Sistema de Órdenes de Compra Automáticas
# =============================================================================

from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class PurchaseOrder(models.Model):
    """Modelo para órdenes de compra automáticas"""
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviado'),
        ('confirmed', 'Confirmado'),
        ('in_transit', 'En Camino'),
        ('received', 'Recibido'),
        ('cancelled', 'Cancelado'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    # Identificación
    order_number = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Número de Orden"
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )
    
    # Relaciones principales
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='purchase_orders'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='purchase_orders'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders'
    )
    alert = models.ForeignKey(
        'alerts.Alert',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        verbose_name="Alerta que generó la orden"
    )
    
    # Detalles de la orden
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio Unitario"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto Total"
    )
    
    # Estado y gestión
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Estado"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Prioridad"
    )
    
    # Información de contacto
    supplier_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email del Proveedor"
    )
    supplier_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono del Proveedor"
    )
    
    # Fechas importantes
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Esperada de Entrega"
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Real de Entrega"
    )
    
    # Tracking de emails
    email_sent = models.BooleanField(
        default=False,
        verbose_name="Email Enviado"
    )
    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Envío de Email"
    )
    email_sent_to = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email Enviado A"
    )
    
    # ✅ NUEVO: Integración con EmailTrackingService
    tracking_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ID de Tracking del Email",
        help_text="ID para seguimiento automático del email enviado"
    )
    email_tracking_campaign_id = models.UUIDField(
        blank=True,
        null=True,
        verbose_name="ID de Campaña de Email",
        help_text="ID de la campaña de email para analytics"
    )
    
    # Contenido del email generado por IA
    email_subject = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Asunto del Email"
    )
    email_content = models.TextField(
        blank=True,
        null=True,
        verbose_name="Contenido del Email"
    )
    
    # Notas y observaciones
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas"
    )
    supplier_response = models.TextField(
        blank=True,
        null=True,
        verbose_name="Respuesta del Proveedor"
    )
    
    # Auditoría
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_purchase_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configuración AI
    ai_generated = models.BooleanField(
        default=True,
        verbose_name="Generado por IA"
    )
    ai_confidence_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score de Confianza IA"
    )
    
    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.product.name} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Generar número de orden automáticamente
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # Calcular monto total
        self.total_amount = self.quantity * self.unit_price
        
        # Configurar email del proveedor si no está definido
        if self.supplier and not self.supplier_email:
            self.supplier_email = getattr(self.supplier, 'email', None)
        
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generar número de orden único"""
        from django.utils import timezone
        
        # Formato: PO-YYYY-MM-DD-XXXX
        date_str = timezone.now().strftime('%Y-%m-%d')
        
        # Contar órdenes del día
        today_orders = PurchaseOrder.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        sequence = str(today_orders + 1).zfill(4)
        return f"PO-{date_str}-{sequence}"
    
    @property
    def can_be_sent(self):
        """Verificar si la orden puede ser enviada"""
        return (
            self.status == 'draft' and
            self.supplier_email and
            not self.email_sent
        )
    
    @property
    def is_overdue(self):
        """Verificar si la orden está atrasada"""
        if not self.expected_delivery_date:
            return False
        
        from django.utils import timezone
        today = timezone.now().date()
        
        return (
            self.status in ['sent', 'confirmed', 'in_transit'] and
            self.expected_delivery_date < today
        )
    
    def mark_as_sent(self, email_address=None):
        """Marcar orden como enviada"""
        from django.utils import timezone
        
        self.status = 'sent'
        self.email_sent = True
        self.email_sent_at = timezone.now()
        if email_address:
            self.email_sent_to = email_address
        self.save()
    
    def update_status(self, new_status, notes=None):
        """Actualizar estado de la orden"""
        old_status = self.status
        self.status = new_status
        
        if notes:
            current_notes = self.notes or ""
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            new_note = f"[{timestamp}] Estado cambiado de {old_status} a {new_status}: {notes}"
            self.notes = f"{current_notes}\n{new_note}" if current_notes else new_note
        
        # Si se marca como recibido, actualizar fecha
        if new_status == 'received':
            from django.utils import timezone
            self.actual_delivery_date = timezone.now().date()
        
        self.save()


class PurchaseOrderTracking(models.Model):
    """Seguimiento de estados de órdenes de compra"""
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='tracking_history'
    )
    status = models.CharField(
        max_length=20,
        choices=PurchaseOrder.STATUS_CHOICES,
        verbose_name="Estado"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Seguimiento de Orden"
        verbose_name_plural = "Seguimientos de Órdenes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.purchase_order.order_number} - {self.get_status_display()}"


class PurchaseOrderEmailLog(models.Model):
    """Log de emails enviados para órdenes de compra"""
    
    EMAIL_TYPES = [
        ('order', 'Orden de Compra'),
        ('reminder', 'Recordatorio'),
        ('follow_up', 'Seguimiento'),
        ('confirmation', 'Confirmación'),
    ]
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='email_logs'
    )
    email_type = models.CharField(
        max_length=20,
        choices=EMAIL_TYPES,
        default='order'
    )
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    # Status del envío
    sent_successfully = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    # Información del servicio usado
    email_service = models.CharField(
        max_length=20,
        choices=[
            ('gmail', 'Gmail API'),
            ('sendgrid', 'SendGrid'),
            ('smtp', 'SMTP')
        ],
        default='smtp'
    )
    
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Email"
        verbose_name_plural = "Logs de Emails"
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.purchase_order.order_number} - {self.email_type} - {self.recipient_email}"


# ==============================================
# MODELOS DE EMAIL TRACKING SERVICE
# ==============================================

class EmailCampaign(models.Model):
    """Campañas de email para organizar el tracking"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Nombre de la campaña")
    description = models.TextField(blank=True, verbose_name="Descripción")
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='email_campaigns'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_email_campaigns'
    )
    
    # Configuración
    track_opens = models.BooleanField(default=True, verbose_name="Trackear aperturas")
    track_clicks = models.BooleanField(default=True, verbose_name="Trackear clicks")
    
    # Métricas
    total_sent = models.IntegerField(default=0, verbose_name="Total enviados")
    total_delivered = models.IntegerField(default=0, verbose_name="Total entregados")
    total_opened = models.IntegerField(default=0, verbose_name="Total abiertos")
    total_clicked = models.IntegerField(default=0, verbose_name="Total con clicks")
    total_bounced = models.IntegerField(default=0, verbose_name="Total rebotados")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    class Meta:
        verbose_name = "Campaña de Email"
        verbose_name_plural = "Campañas de Email"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"
    
    @property
    def open_rate(self):
        """Tasa de apertura"""
        if self.total_delivered == 0:
            return 0
        return (self.total_opened / self.total_delivered) * 100
    
    @property
    def click_rate(self):
        """Tasa de clicks"""
        if self.total_delivered == 0:
            return 0
        return (self.total_clicked / self.total_delivered) * 100
    
    @property
    def bounce_rate(self):
        """Tasa de rebote"""
        if self.total_sent == 0:
            return 0
        return (self.total_bounced / self.total_sent) * 100


class TrackedEmail(models.Model):
    """Emails individuales con tracking"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('delivered', 'Entregado'),
        ('opened', 'Abierto'),
        ('clicked', 'Con clicks'),
        ('replied', 'Respondido'),
        ('bounced', 'Rebotado'),
        ('failed', 'Falló'),
    ]
    
    # Identificación
    email_id = models.CharField(max_length=200, unique=True, verbose_name="ID del email")
    tracking_id = models.CharField(max_length=100, unique=True, verbose_name="ID de tracking")
    
    # Campaña relacionada (opcional)
    campaign = models.ForeignKey(
        EmailCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tracked_emails'
    )
    
    # Contenido del email
    recipient_email = models.EmailField(verbose_name="Email destinatario")
    recipient_name = models.CharField(max_length=200, blank=True, verbose_name="Nombre destinatario")
    subject = models.CharField(max_length=500, verbose_name="Asunto")
    content_preview = models.TextField(blank=True, verbose_name="Vista previa del contenido")
    
    # Estado y tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    
    # Timestamps de eventos
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviado en")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Entregado en")
    first_opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Primera apertura")
    last_opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Última apertura")
    first_clicked_at = models.DateTimeField(null=True, blank=True, verbose_name="Primer click")
    last_clicked_at = models.DateTimeField(null=True, blank=True, verbose_name="Último click")
    replied_at = models.DateTimeField(null=True, blank=True, verbose_name="Respondido en")
    bounced_at = models.DateTimeField(null=True, blank=True, verbose_name="Rebotado en")
    
    # Contadores
    open_count = models.IntegerField(default=0, verbose_name="Número de aperturas")
    click_count = models.IntegerField(default=0, verbose_name="Número de clicks")
    
    # Datos adicionales
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    location_data = models.JSONField(default=dict, blank=True, verbose_name="Datos de ubicación")
    device_info = models.JSONField(default=dict, blank=True, verbose_name="Información del dispositivo")
    
    # Metadatos
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='tracked_emails'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email Tracked"
        verbose_name_plural = "Emails Tracked"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_id']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['recipient_email']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"{self.subject} -> {self.recipient_email} ({self.status})"
    
    def mark_as_opened(self, user_agent=None, ip_address=None, location_data=None):
        """Marcar email como abierto"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.first_opened_at:
            self.first_opened_at = now
            if self.status in ['sent', 'delivered']:
                self.status = 'opened'
        
        self.last_opened_at = now
        self.open_count += 1
        
        if user_agent:
            self.user_agent = user_agent
        if ip_address:
            self.ip_address = ip_address
        if location_data:
            self.location_data = location_data
        
        self.save()
        
        # Actualizar campaña si existe
        if self.campaign:
            self._update_campaign_metrics()
    
    def mark_as_clicked(self, user_agent=None, ip_address=None):
        """Marcar email como clickeado"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.first_clicked_at:
            self.first_clicked_at = now
            if self.status in ['sent', 'delivered', 'opened']:
                self.status = 'clicked'
        
        self.last_clicked_at = now
        self.click_count += 1
        
        if user_agent:
            self.user_agent = user_agent
        if ip_address:
            self.ip_address = ip_address
        
        self.save()
        
        # Actualizar campaña si existe
        if self.campaign:
            self._update_campaign_metrics()
    
    def _update_campaign_metrics(self):
        """Actualizar métricas de la campaña"""
        if not self.campaign:
            return
        
        # Recalcular métricas de la campaña
        campaign_emails = TrackedEmail.objects.filter(campaign=self.campaign)
        
        self.campaign.total_sent = campaign_emails.count()
        self.campaign.total_delivered = campaign_emails.filter(
            status__in=['delivered', 'opened', 'clicked', 'replied']
        ).count()
        self.campaign.total_opened = campaign_emails.filter(
            first_opened_at__isnull=False
        ).count()
        self.campaign.total_clicked = campaign_emails.filter(
            first_clicked_at__isnull=False
        ).count()
        self.campaign.total_bounced = campaign_emails.filter(
            status='bounced'
        ).count()
        
        self.campaign.save()


class EmailClick(models.Model):
    """Clicks individuales en emails"""
    
    tracked_email = models.ForeignKey(
        TrackedEmail,
        on_delete=models.CASCADE,
        related_name='clicks'
    )
    
    # Información del click
    url = models.URLField(verbose_name="URL clickeada")
    link_text = models.CharField(max_length=500, blank=True, verbose_name="Texto del enlace")
    position = models.IntegerField(null=True, blank=True, verbose_name="Posición en el email")
    
    # Contexto del click
    clicked_at = models.DateTimeField(auto_now_add=True, verbose_name="Clickeado en")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    referrer = models.URLField(blank=True, verbose_name="Referrer")
    
    # Datos del dispositivo
    device_type = models.CharField(max_length=50, blank=True, verbose_name="Tipo de dispositivo")
    browser = models.CharField(max_length=100, blank=True, verbose_name="Navegador")
    os = models.CharField(max_length=100, blank=True, verbose_name="Sistema operativo")
    
    class Meta:
        verbose_name = "Click de Email"
        verbose_name_plural = "Clicks de Email"
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['tracked_email', 'clicked_at']),
            models.Index(fields=['url']),
        ]
    
    def __str__(self):
        return f"Click en {self.url} - {self.tracked_email.subject}"


class EmailPattern(models.Model):
    """Patrones detectados en emails"""
    
    PATTERN_TYPES = [
        ('time_peak', 'Pico de Tiempo'),
        ('sender_frequency', 'Frecuencia de Remitente'),
        ('subject_similarity', 'Similitud de Asunto'),
        ('content_category', 'Categoría de Contenido'),
        ('engagement_trend', 'Tendencia de Engagement'),
        ('ai_insight', 'Insight de IA'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='email_patterns'
    )
    
    # Información del patrón
    pattern_type = models.CharField(
        max_length=30,
        choices=PATTERN_TYPES,
        verbose_name="Tipo de patrón"
    )
    name = models.CharField(max_length=200, verbose_name="Nombre del patrón")
    description = models.TextField(verbose_name="Descripción")
    
    # Métricas del patrón
    frequency = models.IntegerField(verbose_name="Frecuencia")
    confidence = models.FloatField(verbose_name="Confianza (0-1)")
    impact_score = models.FloatField(default=0, verbose_name="Puntuación de impacto")
    
    # Datos del patrón
    pattern_data = models.JSONField(default=dict, verbose_name="Datos del patrón")
    examples = models.JSONField(default=list, verbose_name="Ejemplos")
    
    # Recomendaciones
    recommendation = models.TextField(blank=True, verbose_name="Recomendación")
    action_items = models.JSONField(default=list, verbose_name="Elementos de acción")
    
    # Metadatos
    detected_at = models.DateTimeField(auto_now_add=True, verbose_name="Detectado en")
    period_start = models.DateTimeField(verbose_name="Inicio del período")
    period_end = models.DateTimeField(verbose_name="Fin del período")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Patrón de Email"
        verbose_name_plural = "Patrones de Email"
        ordering = ['-detected_at', '-confidence']
        indexes = [
            models.Index(fields=['company', 'pattern_type']),
            models.Index(fields=['confidence', 'impact_score']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.company.name} ({self.confidence:.2f})"


class EmailInsight(models.Model):
    """Insights generados por IA sobre emails"""
    
    INSIGHT_TYPES = [
        ('opportunity', 'Oportunidad'),
        ('optimization', 'Optimización'),
        ('risk', 'Riesgo'),
        ('automation', 'Automatización'),
        ('behavior', 'Comportamiento'),
        ('trend', 'Tendencia'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='email_insights'
    )
    
    # Información del insight
    insight_type = models.CharField(
        max_length=20,
        choices=INSIGHT_TYPES,
        verbose_name="Tipo de insight"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='medium',
        verbose_name="Prioridad"
    )
    
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción")
    
    # Datos del análisis
    confidence_score = models.FloatField(verbose_name="Puntuación de confianza")
    impact_potential = models.FloatField(default=0, verbose_name="Potencial de impacto")
    
    # Acciones recomendadas
    action_items = models.JSONField(default=list, verbose_name="Elementos de acción")
    expected_outcome = models.TextField(blank=True, verbose_name="Resultado esperado")
    
    # Referencias a patrones
    related_patterns = models.ManyToManyField(
        EmailPattern,
        blank=True,
        related_name='insights'
    )
    
    # Estado de implementación
    is_implemented = models.BooleanField(default=False, verbose_name="Implementado")
    implemented_at = models.DateTimeField(null=True, blank=True, verbose_name="Implementado en")
    implementation_notes = models.TextField(blank=True, verbose_name="Notas de implementación")
    
    # Metadatos
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Generado en")
    generated_by_ai = models.BooleanField(default=True, verbose_name="Generado por IA")
    source_data_period = models.JSONField(default=dict, verbose_name="Período de datos fuente")
    
    class Meta:
        verbose_name = "Insight de Email"
        verbose_name_plural = "Insights de Email"
        ordering = ['-priority', '-confidence_score', '-generated_at']
        indexes = [
            models.Index(fields=['company', 'insight_type']),
            models.Index(fields=['priority', 'is_implemented']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_priority_display()} - {self.company.name}"
    
    def mark_as_implemented(self, notes=None):
        """Marcar insight como implementado"""
        from django.utils import timezone
        self.is_implemented = True
        self.implemented_at = timezone.now()
        if notes:
            self.implementation_notes = notes
        self.save()


class GmailWebhookLog(models.Model):
    """Log de webhooks recibidos de Gmail"""
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='gmail_webhook_logs'
    )
    
    # Datos del webhook
    history_id = models.CharField(max_length=100, verbose_name="History ID")
    email_address = models.EmailField(verbose_name="Email address")
    
    # Payload del webhook
    raw_payload = models.JSONField(verbose_name="Payload completo")
    processed_changes = models.JSONField(default=list, verbose_name="Cambios procesados")
    
    # Estado del procesamiento
    processed_at = models.DateTimeField(auto_now_add=True, verbose_name="Procesado en")
    processing_success = models.BooleanField(default=True, verbose_name="Procesamiento exitoso")
    error_message = models.TextField(blank=True, verbose_name="Mensaje de error")
    
    class Meta:
        verbose_name = "Log de Webhook Gmail"
        verbose_name_plural = "Logs de Webhooks Gmail"
        ordering = ['-processed_at']
        indexes = [
            models.Index(fields=['company', 'history_id']),
            models.Index(fields=['processed_at']),
        ]
    
    def __str__(self):
        return f"Webhook {self.history_id} - {self.email_address} - {self.company.name}"
