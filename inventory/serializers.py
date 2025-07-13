from rest_framework import serializers
from .models import Category, Supplier, Product, Sale, Alert, InventoryHistory, Transaction, Customer, Lead, InventoryItem, Location


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para Category"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'products_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer para Supplier"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_name', 'email', 'phone', 'address',
            'city', 'country', 'tax_id', 'payment_terms', 'products_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer optimizado para Product - eliminando redundancias"""
    
    # Campos relacionales (read-only)
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    # Campos calculados (read-only)
    stock_value = serializers.ReadOnlyField()  # stock * cost_price
    
    # **COMPATIBILIDAD: Alias para el frontend**
    current_stock = serializers.ReadOnlyField(source='stock')  # Alias para compatibilidad
    
    class Meta:
        model = Product
        fields = [
            # Identificación básica
            'id', 'sku', 'name', 'description',
            
            # Relaciones (IDs para escritura, nombres para lectura)
            'category', 'category_name', 
            'supplier', 'supplier_name',
            
            # Precios (solo los esenciales)
            'cost_price',     # Precio de compra
            'sale_price',     # Precio de venta
            
            # Stock (con compatibilidad)
            'stock',          # Stock actual (campo real del modelo)
            'current_stock',  # Alias para compatibilidad con frontend
            'min_stock',      # Stock mínimo
            'max_stock',      # Stock máximo  
            'reorder_point',  # Punto de reorden
            
            # Información básica del producto
            'unit',           # Unidad de medida
            'barcode',        # Código de barras (útil para ventas)
            
            # Campos de control avanzado (solo si se necesitan)
            'track_batches',  # Si maneja lotes
            'has_expiration', # Si tiene vencimiento
            
            # Metadatos
            'stock_value',    # Valor total del stock (calculado)
            'is_active',      # Estado del producto
            'created_at',     # Fecha de creación
        ]
        
        read_only_fields = [
            'id', 'stock_value', 'current_stock', 'category_name', 'supplier_name', 'created_at'
        ]

    def validate(self, data):
        """Validaciones personalizadas"""
        # Validar que el precio de venta sea mayor al costo
        if data.get('sale_price', 0) < data.get('cost_price', 0):
            raise serializers.ValidationError(
                "El precio de venta no puede ser menor al precio de costo"
            )
        
        # Validar que el stock mínimo sea menor al máximo
        if data.get('min_stock', 0) >= data.get('max_stock', 100):
            raise serializers.ValidationError(
                "El stock mínimo debe ser menor al stock máximo"
            )
        
        # Validar que el punto de reorden esté entre min y max
        reorder_point = data.get('reorder_point', 0)
        min_stock = data.get('min_stock', 0)
        max_stock = data.get('max_stock', 100)
        
        if not (min_stock <= reorder_point <= max_stock):
            raise serializers.ValidationError(
                "El punto de reorden debe estar entre el stock mínimo y máximo"
            )
        
        return data


class SaleSerializer(serializers.ModelSerializer):
    """Serializer para Sale"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity',
            'unit_price', 'total_amount', 'customer_name', 'date_sold'
        ]
        read_only_fields = ['id', 'total_amount', 'date_sold']


class AlertSerializer(serializers.ModelSerializer):
    """Serializer para Alert"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'message', 'severity', 'is_active', 'product',
            'product_name', 'product_sku', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class InventoryHistorySerializer(serializers.ModelSerializer):
    """Serializer para InventoryHistory"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = InventoryHistory
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'stock_before',
            'stock_after', 'change_reason', 'user', 'user_name', 'date_changed'
        ]
        read_only_fields = ['id', 'date_changed']


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del dashboard"""
    total_products = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    total_suppliers = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    low_stock_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    recent_transactions = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    top_products = serializers.ListField()
    stock_by_category = serializers.ListField()
    recent_sales = serializers.ListField()


class ProductStockSerializer(serializers.Serializer):
    """Serializer para stock de productos"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    current_stock = serializers.IntegerField()
    min_stock = serializers.IntegerField()
    max_stock = serializers.IntegerField()
    stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    stock_status = serializers.CharField()


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer para Transaction"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'location',
            'location_name', 'transaction_type', 'quantity', 'unit_cost',
            'reference_number', 'notes', 'transaction_date', 'created_by',
            'created_by_name'
        ]
        read_only_fields = ['id', 'transaction_date', 'created_by']
    
    def create(self, validated_data):
        # Asignar el usuario actual como creador
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer para Customer"""
    total_purchases = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'email', 'phone', 'address', 'city', 'country',
            'tax_id', 'customer_type', 'credit_limit', 'total_purchases',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_purchases(self, obj):
        from django.db.models import Sum
        return Sale.objects.filter(customer_name=obj.name).aggregate(
            total=Sum('total_amount')
        )['total'] or 0


class LeadSerializer(serializers.ModelSerializer):
    """Serializer para Lead"""
    interested_products_names = serializers.StringRelatedField(source='interested_products', many=True, read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'email', 'phone', 'company', 'source', 'status',
            'interested_products', 'interested_products_names', 'notes',
            'estimated_value', 'expected_close_date', 'assigned_to',
            'assigned_to_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    """Serializer para Location"""
    inventory_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'code', 'description', 'warehouse', 'zone',
            'aisle', 'rack', 'shelf', 'inventory_items_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_inventory_items_count(self, obj):
        return obj.inventory_items.filter(is_active=True).count()


class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer para InventoryItem"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    available_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'location',
            'location_name', 'quantity', 'reserved_quantity', 'available_quantity',
            'unit_cost', 'batch_number', 'manufacturing_date', 'expiration_date',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_available_quantity(self, obj):
        return float(obj.quantity) - float(obj.reserved_quantity)


class OpportunitySerializer(serializers.ModelSerializer):
    """Serializer para Opportunity (usando Lead como base)"""
    potential_revenue = serializers.DecimalField(source='estimated_value', max_digits=12, decimal_places=2, read_only=True)
    stage = serializers.CharField(source='status', read_only=True)
    contact_name = serializers.CharField(source='name', read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'contact_name', 'company', 'email', 'phone', 'stage',
            'potential_revenue', 'expected_close_date', 'assigned_to_name',
            'source', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
