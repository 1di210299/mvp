from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Sum, Count, Q, F
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema
from .models import Category, Supplier, Location, Product, InventoryItem, Transaction
from .serializers import (
    CategorySerializer, SupplierSerializer, LocationSerializer,
    ProductSerializer, InventoryItemSerializer, TransactionSerializer,
    ProductStockSerializer, DashboardStatsSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de categorías"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de proveedores"""
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Supplier.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de ubicaciones"""
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Location.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de productos"""
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Product.objects.filter(company=self.request.user.company)
        
        # Filtros opcionales
        category = self.request.query_params.get('category')
        supplier = self.request.query_params.get('supplier')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category=category)
        if supplier:
            queryset = queryset.filter(supplier=supplier)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
    
    @extend_schema(
        summary="Obtener productos con stock bajo",
        description="Retorna productos cuyo stock actual está por debajo del mínimo"
    )
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        products = self.get_queryset().filter(
            inventory_items__quantity__lt=F('min_stock')
        ).distinct()
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class InventoryItemViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de items de inventario"""
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return InventoryItem.objects.filter(
            product__company=self.request.user.company
        )
    
    def perform_create(self, serializer):
        # Validar que el producto pertenezca a la empresa del usuario
        product = serializer.validated_data['product']
        if product.company != self.request.user.company:
            raise permissions.PermissionDenied("No tienes acceso a este producto")
        
        serializer.save()


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de transacciones"""
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Transaction.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            user=self.request.user
        )


class DashboardView(APIView):
    """Vista para el dashboard principal de inventario"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener estadísticas del dashboard",
        description="Retorna métricas y estadísticas principales del inventario"
    )
    def get(self, request):
        company = request.user.company
        
        # Estadísticas básicas
        total_products = Product.objects.filter(company=company, is_active=True).count()
        total_locations = Location.objects.filter(company=company, is_active=True).count()
        total_suppliers = Supplier.objects.filter(company=company, is_active=True).count()
        total_categories = Category.objects.filter(company=company, is_active=True).count()
        
        # Valor total del inventario
        total_stock_value = InventoryItem.objects.filter(
            product__company=company,
            is_active=True
        ).aggregate(
            total=Sum('quantity') * Sum('unit_cost')
        )['total'] or 0
        
        # Productos con stock bajo
        low_stock_products = Product.objects.filter(
            company=company,
            is_active=True
        ).annotate(
            current_stock=Sum('inventory_items__quantity')
        ).filter(
            current_stock__lt=F('min_stock')
        ).count()
        
        # Productos próximos a vencer (30 días)
        expiration_date = timezone.now().date() + timedelta(days=30)
        products_near_expiration = InventoryItem.objects.filter(
            product__company=company,
            is_active=True,
            expiration_date__lte=expiration_date,
            expiration_date__gte=timezone.now().date()
        ).count()
        
        # Transacciones recientes (últimos 30 días)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = Transaction.objects.filter(
            company=company,
            created_at__gte=thirty_days_ago
        ).count()
        
        # Top 5 productos por movimiento
        top_products = Transaction.objects.filter(
            company=company,
            created_at__gte=thirty_days_ago
        ).values(
            'product__name', 'product__sku'
        ).annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:5]
        
        # Stock por categoría
        stock_by_category = Category.objects.filter(
            company=company,
            is_active=True
        ).annotate(
            total_products=Count('products'),
            total_stock=Sum('products__inventory_items__quantity')
        ).values('name', 'total_products', 'total_stock')
        
        data = {
            'total_products': total_products,
            'total_locations': total_locations,
            'total_suppliers': total_suppliers,
            'total_categories': total_categories,
            'total_stock_value': total_stock_value,
            'low_stock_products': low_stock_products,
            'products_near_expiration': products_near_expiration,
            'recent_transactions': recent_transactions,
            'top_products': list(top_products),
            'stock_by_category': list(stock_by_category),
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)


class FileUploadView(APIView):
    """Vista para subir archivos CSV de inventario"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        summary="Subir archivo CSV de inventario",
        description="Permite subir un archivo CSV para importar datos de inventario"
    )
    def post(self, request):
        # Esta es una implementación básica
        # En una versión completa, aquí procesaríamos el archivo CSV
        file = request.FILES.get('file')
        
        if not file:
            return Response({
                'status': 'error',
                'message': 'No se proporcionó archivo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not file.name.endswith('.csv'):
            return Response({
                'status': 'error',
                'message': 'El archivo debe ser formato CSV'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Aquí iría la lógica de procesamiento del CSV
        # Por ahora retornamos éxito
        return Response({
            'status': 'success',
            'message': f'Archivo {file.name} subido exitosamente',
            'size': file.size
        })


class ProductStockView(APIView):
    """Vista para obtener el stock detallado de un producto"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener stock detallado de un producto",
        description="Retorna información detallada del stock de un producto por ubicaciones"
    )
    def get(self, request, product_id):
        try:
            product = Product.objects.get(
                id=product_id,
                company=request.user.company
            )
        except Product.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Producto no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener stock por ubicaciones
        inventory_items = InventoryItem.objects.filter(
            product=product,
            is_active=True
        ).select_related('location')
        
        locations_data = []
        total_stock = 0
        available_stock = 0
        reserved_stock = 0
        stock_value = 0
        
        for item in inventory_items:
            location_data = {
                'location_id': item.location.id,
                'location_name': item.location.name,
                'quantity': item.quantity,
                'reserved_quantity': item.reserved_quantity,
                'available_quantity': item.available_quantity,
                'batch_number': item.batch_number,
                'expiration_date': item.expiration_date,
                'unit_cost': item.unit_cost,
                'total_value': item.total_value
            }
            locations_data.append(location_data)
            
            total_stock += item.quantity
            available_stock += item.available_quantity
            reserved_stock += item.reserved_quantity
            stock_value += item.total_value
        
        data = {
            'product_id': product.id,
            'product_name': product.name,
            'product_sku': product.sku,
            'total_stock': total_stock,
            'available_stock': available_stock,
            'reserved_stock': reserved_stock,
            'stock_value': stock_value,
            'locations': locations_data
        }
        
        serializer = ProductStockSerializer(data)
        return Response(serializer.data)


class LowStockView(APIView):
    """Vista para obtener productos con stock bajo"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener productos con stock bajo",
        description="Retorna lista de productos cuyo stock está por debajo del mínimo configurado"
    )
    def get(self, request):
        company = request.user.company
        
        products = Product.objects.filter(
            company=company,
            is_active=True
        ).annotate(
            current_stock=Sum('inventory_items__quantity')
        ).filter(
            current_stock__lt=F('min_stock')
        ).select_related('category', 'supplier')
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class StockMovementsView(APIView):
    """Vista para obtener movimientos de stock"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener movimientos de stock",
        description="Retorna el historial de movimientos de stock filtrable por fechas y productos"
    )
    def get(self, request):
        company = request.user.company
        
        # Filtros opcionales
        product_id = request.query_params.get('product_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        transaction_type = request.query_params.get('transaction_type')
        
        queryset = Transaction.objects.filter(company=company)
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        queryset = queryset.order_by('-transaction_date')
        
        # Paginación básica
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        transactions = queryset[start:end]
        total_count = queryset.count()
        
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })
