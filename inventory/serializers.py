from rest_framework import serializers
from .models import Category, Supplier, Location, Product, InventoryItem, Transaction


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para Category"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    subcategories_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name',
            'subcategories_count', 'products_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subcategories_count(self, obj):
        return obj.subcategories.filter(is_active=True).count()
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer para Supplier"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'ruc', 'contact_person', 'email', 'phone', 'address',
            'payment_terms', 'credit_limit', 'lead_time', 'products_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class LocationSerializer(serializers.ModelSerializer):
    """Serializer para Location"""
    inventory_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'code', 'description', 'warehouse', 'zone',
            'aisle', 'rack', 'shelf', 'inventory_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_inventory_count(self, obj):
        return obj.inventory_items.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer para Product"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    current_stock = serializers.ReadOnlyField()
    stock_value = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description', 'category', 'category_name',
            'supplier', 'supplier_name', 'barcode', 'unit', 'weight', 'dimensions',
            'cost_price', 'sale_price', 'min_stock', 'max_stock', 'reorder_point',
            'track_batches', 'has_expiration', 'shelf_life_days', 'current_stock',
            'stock_value', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_stock', 'stock_value', 'created_at', 'updated_at']


class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer para InventoryItem"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    available_quantity = serializers.ReadOnlyField()
    total_value = serializers.ReadOnlyField()
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'location', 'location_name',
            'quantity', 'reserved_quantity', 'available_quantity', 'batch_number',
            'manufacturing_date', 'expiration_date', 'unit_cost', 'total_value',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'available_quantity', 'total_value', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer para Transaction"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    total_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'reference_number', 'product', 'product_name',
            'product_sku', 'location', 'location_name', 'quantity', 'unit_cost',
            'batch_number', 'expiration_date', 'notes', 'document_type',
            'document_number', 'user', 'user_name', 'total_amount',
            'transaction_date', 'created_at'
        ]
        read_only_fields = ['id', 'total_amount', 'created_at']


class ProductStockSerializer(serializers.Serializer):
    """Serializer para stock de productos"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    total_stock = serializers.DecimalField(max_digits=12, decimal_places=2)
    available_stock = serializers.DecimalField(max_digits=12, decimal_places=2)
    reserved_stock = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    locations = serializers.ListField()


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del dashboard"""
    total_products = serializers.IntegerField()
    total_locations = serializers.IntegerField()
    total_suppliers = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    low_stock_products = serializers.IntegerField()
    products_near_expiration = serializers.IntegerField()
    recent_transactions = serializers.IntegerField()
    top_products = serializers.ListField()
    stock_by_category = serializers.ListField()
