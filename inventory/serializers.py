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
    
    # Campos relacionales (read-only para mostrar nombres)
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    # Campos calculados (read-only)
    stock_value = serializers.ReadOnlyField()  # stock * cost_price
    
    # **COMPATIBILIDAD: Alias para el frontend**
    current_stock = serializers.ReadOnlyField(source='stock')  # Alias para compatibilidad
    
    # FIX: Campos para crear categoría/proveedor sobre la marcha
    category_data = serializers.DictField(write_only=True, required=False, help_text="Datos para crear nueva categoría si category no se proporciona")
    supplier_data = serializers.DictField(write_only=True, required=False, help_text="Datos para crear nuevo proveedor si supplier no se proporciona")
    
    class Meta:
        model = Product
        fields = [
            # Identificación básica
            'id', 'sku', 'name', 'description',
            
            # Relaciones (IDs para escritura, nombres para lectura)
            'category', 'category_name', 'category_data',  # FIX: Agregar category_data
            'supplier', 'supplier_name', 'supplier_data',  # FIX: Agregar supplier_data
            
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

    def to_internal_value(self, data):
        """Override para agregar logging de datos recibidos"""
        print(f"🔍 ProductSerializer.to_internal_value() - Datos recibidos:")
        print(f"📝 Raw data: {data}")
        
        try:
            # FIX: Mapear unit_price a sale_price si viene del frontend
            if 'unit_price' in data and 'sale_price' not in data:
                data['sale_price'] = data.pop('unit_price')
                print(f"🔄 Mapeando unit_price a sale_price: {data['sale_price']}")
            
            result = super().to_internal_value(data)
            print(f"✅ Datos procesados exitosamente: {result}")
            return result
        except Exception as e:
            print(f"❌ Error en to_internal_value: {str(e)}")
            print(f"📋 Tipo de error: {type(e).__name__}")
            raise

    def validate(self, data):
        """Validaciones personalizadas con logging"""
        print(f"🔍 ProductSerializer.validate() - Validando datos:")
        print(f"📝 Data a validar: {data}")
        
        try:
            # FIX: Validar que se proporcione categoría O datos para crearla
            if not data.get('category') and not data.get('category_data'):
                raise serializers.ValidationError("Debe proporcionar una categoría existente o datos para crear una nueva")
            
            # FIX: Validar datos de nueva categoría si se proporcionan
            if data.get('category_data'):
                category_data = data['category_data']
                if not category_data.get('name'):
                    raise serializers.ValidationError("El nombre de la categoría es requerido")
                print(f"📋 Nueva categoría a crear: {category_data}")
            
            # FIX: Validar datos de nuevo proveedor si se proporcionan  
            if data.get('supplier_data'):
                supplier_data = data['supplier_data']
                if not supplier_data.get('name'):
                    raise serializers.ValidationError("El nombre del proveedor es requerido")
                print(f"🚚 Nuevo proveedor a crear: {supplier_data}")
            
            # Validar precios (solo si ambos están presentes)
            sale_price = data.get('sale_price')
            cost_price = data.get('cost_price')
            
            if sale_price is not None and cost_price is not None:
                if float(sale_price) < float(cost_price):
                    error_msg = "El precio de venta no puede ser menor al precio de costo"
                    print(f"❌ Error de validación: {error_msg}")
                    raise serializers.ValidationError(error_msg)
                else:
                    print(f"✅ Precios válidos: venta={sale_price}, costo={cost_price}")
            
            # Validar stocks (solo si ambos están presentes)
            min_stock = data.get('min_stock')
            max_stock = data.get('max_stock')
            
            if min_stock is not None and max_stock is not None:
                if int(min_stock) >= int(max_stock):
                    error_msg = "El stock mínimo debe ser menor al stock máximo"
                    print(f"❌ Error de validación: {error_msg}")
                    raise serializers.ValidationError(error_msg)
                else:
                    print(f"✅ Stocks válidos: min={min_stock}, max={max_stock}")
            
            # Auto-calcular reorder_point si no se proporciona
            reorder_point = data.get('reorder_point')
            if min_stock is not None and max_stock is not None:
                if reorder_point is None or int(reorder_point) == 0:
                    # Auto-calcular: punto medio entre min y max, pero más cerca del mínimo
                    auto_reorder = int(min_stock) + max(5, int((int(max_stock) - int(min_stock)) * 0.3))
                    data['reorder_point'] = auto_reorder
                    print(f"🔧 Auto-calculando reorder_point: {auto_reorder} (entre {min_stock} y {max_stock})")
                elif not (int(min_stock) <= int(reorder_point) <= int(max_stock)):
                    # Si está fuera del rango, ajustarlo automáticamente
                    auto_reorder = int(min_stock) + max(5, int((int(max_stock) - int(min_stock)) * 0.3))
                    data['reorder_point'] = auto_reorder
                    print(f"🔧 Ajustando reorder_point fuera de rango de {reorder_point} a {auto_reorder}")
                else:
                    print(f"✅ Punto de reorden válido: {reorder_point}")
            
            print(f"✅ Todas las validaciones pasaron exitosamente")
            return data
            
        except serializers.ValidationError:
            # Re-lanzar errores de validación
            raise
        except Exception as e:
            print(f"❌ Error inesperado en validate: {str(e)}")
            print(f"📋 Tipo de error: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            raise serializers.ValidationError(f"Error de validación: {str(e)}")

    def create(self, validated_data):
        """Override del método create con logging y creación de relaciones"""
        print(f"🔍 ProductSerializer.create() - Creando producto:")
        print(f"📝 Validated data: {validated_data}")
        
        try:
            # FIX: Crear categoría si se proporcionaron datos para una nueva
            category_data = validated_data.pop('category_data', None)
            if category_data and not validated_data.get('category'):
                print(f"📋 Creando nueva categoría: {category_data}")
                category, created = Category.objects.get_or_create(
                    name=category_data['name'],
                    defaults={
                        'description': category_data.get('description', ''),
                        'is_active': True
                    }
                )
                validated_data['category'] = category
                print(f"✅ Categoría {'creada' if created else 'existente'}: {category.name}")
            
            # FIX: Crear proveedor si se proporcionaron datos para uno nuevo
            supplier_data = validated_data.pop('supplier_data', None)
            if supplier_data and not validated_data.get('supplier'):
                print(f"🚚 Creando nuevo proveedor: {supplier_data}")
                supplier, created = Supplier.objects.get_or_create(
                    name=supplier_data['name'],
                    defaults={
                        'contact_name': supplier_data.get('contact_name', ''),
                        'email': supplier_data.get('email', ''),
                        'phone': supplier_data.get('phone', ''),
                        'address': supplier_data.get('address', ''),
                        'is_active': True
                    }
                )
                validated_data['supplier'] = supplier
                print(f"✅ Proveedor {'creado' if created else 'existente'}: {supplier.name}")
            
            # Asignar valores por defecto si no se proporcionan
            defaults = {
                'stock': 0,
                'min_stock': 0,
                'max_stock': 100,
                'reorder_point': 10,
                'cost_price': 0.0,
                'sale_price': 0.0,
                'unit': 'unidad',
                'is_active': True,
                'track_batches': False,
                'has_expiration': False
            }
            
            for field, default_value in defaults.items():
                if field not in validated_data or validated_data[field] is None:
                    validated_data[field] = default_value
                    print(f"🔧 Asignando valor por defecto {field}: {default_value}")
            
            print(f"💾 Creando producto con datos finales: {validated_data}")
            product = super().create(validated_data)
            print(f"✅ Producto creado exitosamente: {product.id} - {product.name}")
            
            return product
            
        except Exception as e:
            print(f"❌ Error en ProductSerializer.create: {str(e)}")
            print(f"📋 Tipo de error: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            raise


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
