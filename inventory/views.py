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
from datalens_backend.utils import get_default_company, get_company_for_user
from .models import Category, Supplier, Product, Sale, Alert, InventoryHistory, Transaction, Customer, Lead, InventoryItem, Location
from .serializers import (
    CategorySerializer, SupplierSerializer, ProductSerializer, SaleSerializer, 
    AlertSerializer, InventoryHistorySerializer, DashboardStatsSerializer, TransactionSerializer,
    CustomerSerializer, LeadSerializer, LocationSerializer, InventoryItemSerializer, OpportunitySerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de categorías"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('name')


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de proveedores"""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return Supplier.objects.filter(is_active=True).order_by('name')
        except Exception as e:
            print(f"Error in SupplierViewSet.get_queryset: {e}")
            return Supplier.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Suppliers service temporarily unavailable: {str(e)}'
            })


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de productos"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Override del método create para agregar logging detallado"""
        print(f"🚀 ProductViewSet.create() - Iniciando creación de producto...")
        print(f"📝 request.data: {request.data}")
        print(f"🔍 request.user: {request.user}")
        print(f"🔍 request.headers: {dict(request.headers)}")
        print(f"🔍 request.method: {request.method}")
        
        try:
            # Validar datos con el serializer
            serializer = self.get_serializer(data=request.data)
            print(f"🔧 Serializer creado: {type(serializer).__name__}")
            
            print(f"🔍 Validando datos del serializer...")
            if serializer.is_valid():
                print(f"✅ Datos válidos: {serializer.validated_data}")
                
                # Llamar al método perform_create
                print(f"💾 Llamando a perform_create...")
                self.perform_create(serializer)
                
                headers = self.get_success_headers(serializer.data)
                response_data = serializer.data
                print(f"✅ Producto creado exitosamente: {response_data}")
                
                return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                print(f"❌ ERRORES DE VALIDACIÓN:")
                for field, errors in serializer.errors.items():
                    print(f"   🔥 Campo '{field}': {errors}")
                print(f"❌ serializer.errors completo: {serializer.errors}")
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ EXCEPCIÓN en ProductViewSet.create: {str(e)}")
            print(f"📋 Tipo de error: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            
            return Response({
                'error': 'Error interno al crear producto',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_queryset(self):
        try:
            user = self.request.user
            
            # Si es superadmin, mostrar TODOS los productos sin filtro de empresa
            if hasattr(user, 'role') and user.role == 'superadmin':
                return Product.objects.filter(
                    is_active=True
                ).select_related('category', 'supplier').order_by('name')
            
            # Para otros usuarios, filtrar por empresa si tienen una
            if hasattr(user, 'company') and user.company:
                return Product.objects.filter(
                    is_active=True,
                    company=user.company
                ).select_related('category', 'supplier').order_by('name')
            
            # Fallback: mostrar todos los productos si no hay empresa definida
            return Product.objects.filter(
                is_active=True
            ).select_related('category', 'supplier').order_by('name')
            
        except Exception as e:
            print(f"Error in ProductViewSet.get_queryset: {e}")
            # En caso de error, superadmin ve todo, otros ven productos sin empresa
            if hasattr(self.request.user, 'role') and self.request.user.role == 'superadmin':
                return Product.objects.filter(is_active=True)
            return Product.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Products service temporarily unavailable: {str(e)}'
            })
    
    def perform_create(self, serializer):
        print(f"🔍 ProductViewSet.perform_create() - Iniciando creación de producto...")
        print(f"📝 Datos recibidos: {self.request.data}")
        print(f"🔍 Usuario: {self.request.user}")
        
        try:
            # FIX: Mostrar datos validados
            validated_data = serializer.validated_data
            print(f"✅ Datos validados: {validated_data}")
            
            # Asegurar que price se sincronice con sale_price si no se proporciona
            if not validated_data.get('price') and validated_data.get('sale_price'):
                validated_data['price'] = validated_data['sale_price']
                print(f"🔄 Sincronizando price con sale_price: {validated_data['price']}")
            
            # FIX: Asignar empresa por defecto
            try:
                from datalens_backend.utils import get_default_company
                company = get_default_company()
                if company:
                    validated_data['company'] = company
                    print(f"🏢 Asignando empresa por defecto: {company.name}")
                else:
                    print("⚠️ No se encontró empresa por defecto")
            except Exception as e:
                print(f"⚠️ Error obteniendo empresa: {e}")
            
            # FIX: Valores por defecto para campos requeridos si no se proporcionan
            defaults = {
                'stock': 0,
                'min_stock': 0,
                'max_stock': 0,
                'cost_price': 0.0,
                'sale_price': 0.0,
                'unit': 'unidad',
                'is_active': True
            }
            
            for field, default_value in defaults.items():
                if field not in validated_data or validated_data[field] is None:
                    validated_data[field] = default_value
                    print(f"🔧 Asignando valor por defecto {field}: {default_value}")
            
            print(f"💾 Guardando producto con datos finales: {validated_data}")
            product = serializer.save()
            print(f"✅ Producto creado exitosamente: {product.id} - {product.name}")
            
        except Exception as e:
            print(f"❌ Error en ProductViewSet.perform_create: {str(e)}")
            print(f"📋 Tipo de error: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            raise  # Re-lanzar el error para que DRF lo maneje correctamente
    
    def perform_update(self, serializer):
        # Mantener sincronización de precios
        if 'sale_price' in serializer.validated_data and 'price' not in serializer.validated_data:
            serializer.validated_data['price'] = serializer.validated_data['sale_price']
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        """Obtener información detallada del stock de un producto"""
        product = self.get_object()
        stock_data = {
            'product_id': product.id,
            'product_name': product.name,
            'product_sku': product.sku,
            'current_stock': product.current_stock,
            'min_stock': product.min_stock,
            'max_stock': product.max_stock,
            'stock_value': product.stock_value,
            'stock_status': self._get_stock_status(product)
        }
        return Response(stock_data)
    
    def _get_stock_status(self, product):
        """Determinar el estado del stock"""
        current = product.current_stock
        if current <= 0:
            return 'out_of_stock'
        elif current <= product.min_stock:
            return 'low_stock'
        elif current >= product.max_stock:
            return 'high_stock'
        return 'normal'


class SaleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de ventas"""
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Sale.objects.select_related('product').order_by('-date_sold')
    
    def perform_create(self, serializer):
        # Actualizar stock del producto
        with transaction.atomic():
            sale = serializer.save()
            product = sale.product
            
            # Registrar cambio en historial
            InventoryHistory.objects.create(
                product=product,
                stock_before=product.stock,
                stock_after=product.stock - sale.quantity,
                change_reason=f"Venta #{sale.id}",
                user=self.request.user
            )
            
            # Actualizar stock
            product.stock = F('stock') - sale.quantity
            product.save()


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de alertas"""
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Alert.objects.select_related('product').order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def check_alerts(self, request):
        """Verificar y crear alertas automáticas"""
        alerts_created = []
        
        # Alertas de stock bajo
        low_stock_products = Product.objects.filter(
            is_active=True,
            stock__lte=F('min_stock')
        )
        
        for product in low_stock_products:
            alert, created = Alert.objects.get_or_create(
                product=product,
                severity='medium',
                is_active=True,
                defaults={
                    'message': f'Stock bajo para {product.name} (SKU: {product.sku}). Stock actual: {product.stock}, mínimo: {product.min_stock}'
                }
            )
            if created:
                alerts_created.append(alert.id)
        
        return Response({
            'alerts_created': len(alerts_created),
            'alert_ids': alerts_created
        })


class InventoryHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de historial de inventario"""
    queryset = InventoryHistory.objects.all()
    serializer_class = InventoryHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return InventoryHistory.objects.select_related('product', 'user').order_by('-date_changed')


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de transacciones"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Transaction.objects.select_related('product', 'location', 'created_by').order_by('-transaction_date')
    
    def list(self, request, *args, **kwargs):
        """Override del método list con paginación completa"""
        try:
            # Parámetros de paginación
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            queryset = self.get_queryset()
            total_count = queryset.count()
            
            # Calcular offset
            start = (page - 1) * page_size
            end = start + page_size
            
            # Obtener transacciones para la página actual
            transactions = queryset[start:end]
            serializer = self.get_serializer(transactions, many=True)
            
            # Calcular información de paginación
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_previous = page > 1
            
            return Response({
                'count': total_count,
                'results': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_previous': has_previous,
                    'showing_from': start + 1,
                    'showing_to': min(end, total_count),
                    'total_count': total_count
                }
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Transactions service temporarily unavailable: {str(e)}'
            })
    
    def perform_create(self, serializer):
        # Asignar el usuario current como creador
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtener transacciones recientes (últimos 30 días)"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = self.get_queryset().filter(
            transaction_date__gte=thirty_days_ago
        )[:20]
        
        serializer = self.get_serializer(recent_transactions, many=True)
        return Response({
            'count': recent_transactions.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Obtener transacciones por producto"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=400)
        
        transactions = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(transactions, many=True)
        return Response({
            'count': transactions.count(),
            'results': serializer.data
        })


class DashboardView(APIView):
    """Vista para el dashboard principal de inventario"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener estadísticas del dashboard",
        description="Retorna métricas y estadísticas principales del inventario"
    )
    def get(self, request):
        print(f"🔍 DashboardView.get() - Iniciando cálculo de estadísticas...")
        try:
            # FIX: Usar InventoryItem en lugar de Product para stocks reales
            from inventory.models import InventoryItem
            
            # Estadísticas básicas
            total_products = Product.objects.filter(is_active=True).count()
            total_categories = Category.objects.filter(is_active=True).count()
            total_suppliers = Supplier.objects.filter(is_active=True).count()
            
            print(f"📊 Productos activos: {total_products}")
            print(f"📊 Categorías activas: {total_categories}")
            print(f"📊 Proveedores activos: {total_suppliers}")
            
            # FIX: Calcular valor total usando InventoryItem
            total_stock_value = InventoryItem.objects.aggregate(
                total_value=Sum(F('quantity') * F('unit_cost'))
            )['total_value'] or 0
            
            print(f"💰 Valor total de inventario: {total_stock_value}")
            
            # FIX: Calcular stock crítico usando InventoryItem y los datos reales
            # Productos con stock bajo (menos de 30 unidades en cualquier ubicación)
            low_stock_items = InventoryItem.objects.filter(
                quantity__lt=30,
                product__is_active=True
            )
            low_stock_products = low_stock_items.count()
            
            print(f"⚠️ Items con stock crítico (<30): {low_stock_products}")
            
            # Productos completamente sin stock
            out_of_stock_products = InventoryItem.objects.filter(
                quantity__lte=0,
                product__is_active=True
            ).count()
            
            print(f"❌ Items sin stock: {out_of_stock_products}")
            
            # Transacciones recientes
            seven_days_ago = timezone.now() - timedelta(days=7)
            try:
                recent_transactions = Transaction.objects.filter(
                    transaction_date__gte=seven_days_ago
                ).count()
            except Exception:
                recent_transactions = 0
            
            print(f"📈 Transacciones últimos 7 días: {recent_transactions}")
            
            # Alertas activas
            try:
                from alerts.models import Alert
                active_alerts = Alert.objects.filter(status='active').count()
            except Exception:
                active_alerts = 0
            
            print(f"🚨 Alertas activas: {active_alerts}")
            
            # Top 5 productos por valor de inventario
            try:
                top_products = list(InventoryItem.objects.select_related('product').annotate(
                    total_value=F('quantity') * F('unit_cost')
                ).order_by('-total_value')[:5].values(
                    'product__id', 'product__name', 'product__sku', 
                    'quantity', 'total_value', 'location__name'
                ))
            except Exception as e:
                print(f"❌ Error obteniendo top productos: {e}")
                top_products = []
            
            # Stock por categoría usando datos reales
            try:
                stock_by_category = list(Category.objects.filter(
                    is_active=True,
                    products__is_active=True
                ).annotate(
                    total_products=Count('products', distinct=True),
                    total_items=Count('products__inventoryitem'),
                    total_stock=Sum('products__inventoryitem__quantity'),
                    total_value=Sum(F('products__inventoryitem__quantity') * F('products__inventoryitem__unit_cost'))
                ).values('name', 'total_products', 'total_stock', 'total_value'))
            except Exception as e:
                print(f"❌ Error obteniendo stock por categoría: {e}")
                stock_by_category = []
            
            # FIX: Respuesta corregida con campos que el frontend espera
            dashboard_data = {
                'total_products': total_products,
                'total_categories': total_categories,
                'total_suppliers': total_suppliers,
                'total_stock_value': float(total_stock_value),
                'low_stock_products': low_stock_products,
                'out_of_stock_products': out_of_stock_products,
                'recent_transactions': recent_transactions,
                'active_alerts': active_alerts,
                'top_products': top_products,
                'stock_by_category': stock_by_category,
                'recent_sales': [],  # Placeholder
                
                # FIX: Campos adicionales que el frontend espera específicamente
                'total_value': float(total_stock_value),  # Alias para frontend
                'low_stock_alerts': low_stock_products,  # Alias para frontend
                'total_transactions_today': recent_transactions,
                'active_customers': 0,  # Placeholder
                'pipeline_value': 0,   # Placeholder
                
                # Debug info
                'debug_info': {
                    'inventory_items_total': InventoryItem.objects.count(),
                    'inventory_items_low_stock': low_stock_products,
                    'calculation_method': 'InventoryItem-based'
                }
            }
            
            print(f"✅ Dashboard data calculado exitosamente:")
            print(f"   📦 Total productos: {total_products}")
            print(f"   ⚠️ Stock crítico: {low_stock_products}")
            print(f"   💰 Valor total: {total_stock_value}")
            
            return Response(dashboard_data)
            
        except Exception as e:
            print(f"❌ Error en dashboard: {str(e)}")
            logger.error(f"Error en dashboard view: {str(e)}")
            # En caso de error completo, devolver datos mínimos
            return Response({
                'total_products': 0,
                'total_categories': 0,
                'total_suppliers': 0,
                'total_stock_value': 0,
                'low_stock_products': 0,
                'out_of_stock_products': 0,
                'recent_transactions': 0,
                'active_alerts': 0,
                'top_products': [],
                'stock_by_category': [],
                'recent_sales': [],
                # Campos adicionales que el frontend espera
                'low_stock_alerts': 0,
                'total_value': 0,
                'total_transactions_today': 0,
                'active_customers': 0,
                'pipeline_value': 0,
                'error': f'Dashboard temporarily unavailable: {str(e)}'
            })


class InventoryDashboardView(APIView):
    """Vista para dashboard de inventario con datos corregidos"""
    
    def get(self, request):
        print(f"🔍 InventoryDashboardView.get() - Iniciando cálculo de estadísticas...")
        try:
            # FIX: Recalcular stocks agregados desde InventoryItem hacia Product
            self._update_product_stocks_from_inventory_items()
            
            # Estadísticas básicas
            total_products = Product.objects.filter(is_active=True).count()
            total_categories = Category.objects.filter(is_active=True).count()
            total_suppliers = Supplier.objects.filter(is_active=True).count()
            
            print(f"📊 Productos activos: {total_products}")
            
            # FIX: Calcular valor total usando InventoryItem real
            total_stock_value = InventoryItem.objects.aggregate(
                total_value=Sum(F('quantity') * F('unit_cost'))
            )['total_value'] or 0
            
            print(f"💰 Valor total de inventario: {total_stock_value}")
            
            # FIX: Calcular stock crítico usando los stocks agregados en Product
            # Productos con stock por debajo del mínimo
            low_stock_products = Product.objects.filter(
                is_active=True,
                stock__lt=F('min_stock')  # Stock actual menor que el mínimo
            ).count()
            
            print(f"⚠️ Productos con stock crítico: {low_stock_products}")
            
            # Productos completamente sin stock
            out_of_stock_products = Product.objects.filter(
                is_active=True,
                stock__lte=0
            ).count()
            
            print(f"❌ Productos sin stock: {out_of_stock_products}")
            
            # Transacciones recientes
            seven_days_ago = timezone.now() - timedelta(days=7)
            recent_transactions = Transaction.objects.filter(
                transaction_date__gte=seven_days_ago
            ).count()
            
            # Top 5 productos por valor total
            try:
                top_products = list(Product.objects.filter(
                    is_active=True
                ).annotate(
                    total_value=F('stock') * F('sale_price')
                ).order_by('-total_value')[:5].values(
                    'id', 'name', 'sku', 'stock', 'total_value'
                ))
            except Exception as e:
                print(f"❌ Error obteniendo top productos: {e}")
                top_products = []
            
            # Stock por categoría
            try:
                stock_by_category = list(Category.objects.filter(
                    is_active=True
                ).annotate(
                    total_products=Count('products', filter=Q(products__is_active=True)),
                    total_stock=Sum('products__stock', filter=Q(products__is_active=True)),
                    total_value=Sum(F('products__stock') * F('products__sale_price'), 
                                  filter=Q(products__is_active=True))
                ).values('name', 'total_products', 'total_stock', 'total_value'))
            except Exception as e:
                print(f"❌ Error obteniendo stock por categoría: {e}")
                stock_by_category = []
            
            dashboard_data = {
                'total_products': total_products,
                'total_categories': total_categories,
                'total_suppliers': total_suppliers,
                'total_stock_value': float(total_stock_value),
                'low_stock_products': low_stock_products,  # FIX: Este es el campo que el frontend necesita
                'out_of_stock_products': out_of_stock_products,
                'recent_transactions': recent_transactions,
                'active_alerts': 0,  # Placeholder
                'top_products': top_products,
                'stock_by_category': stock_by_category,
                'recent_sales': [],
                
                # Campos adicionales que el frontend puede esperar
                'total_value': float(total_stock_value),
                'low_stock_alerts': low_stock_products,
                'total_transactions_today': recent_transactions,
                'active_customers': 0,
                'pipeline_value': 0,
                
                # Debug info para verificar
                'debug_info': {
                    'inventory_items_total': InventoryItem.objects.count(),
                    'products_updated': self._get_updated_products_count(),
                    'calculation_timestamp': timezone.now().isoformat()
                }
            }
            
            print(f"✅ Dashboard data calculado:")
            print(f"   📦 Total productos: {total_products}")
            print(f"   ⚠️ Stock crítico: {low_stock_products}")
            print(f"   💰 Valor total: S/ {total_stock_value:.2f}")
            
            return Response(dashboard_data)
            
        except Exception as e:
            print(f"❌ Error en dashboard: {str(e)}")
            logger.error(f"Error en dashboard view: {str(e)}")
            return Response({
                'total_products': 0,
                'total_categories': 0,
                'total_suppliers': 0,
                'total_stock_value': 0,
                'low_stock_products': 0,
                'out_of_stock_products': 0,
                'recent_transactions': 0,
                'active_alerts': 0,
                'top_products': [],
                'stock_by_category': [],
                'recent_sales': [],
                'error': f'Dashboard temporarily unavailable: {str(e)}'
            })
    
    def _update_product_stocks_from_inventory_items(self):
        """Actualizar stocks agregados en Product desde InventoryItem"""
        try:
            print("🔄 Actualizando stocks agregados desde InventoryItem...")
            
            # Agrupar por producto y sumar quantities
            stock_totals = InventoryItem.objects.values('product').annotate(
                total_stock=Sum('quantity')
            )
            
            updated_count = 0
            for item in stock_totals:
                product_id = item['product']
                total_stock = item['total_stock'] or 0
                
                # Actualizar el stock en Product
                Product.objects.filter(id=product_id).update(stock=total_stock)
                updated_count += 1
            
            print(f"✅ {updated_count} productos actualizados con stocks agregados")
            return updated_count
            
        except Exception as e:
            print(f"❌ Error actualizando stocks: {e}")
            return 0
    
    def _get_updated_products_count(self):
        """Obtener conteo de productos actualizados recientemente"""
        try:
            return Product.objects.filter(
                updated_at__gte=timezone.now() - timedelta(minutes=5)
            ).count()
        except:
            return 0
    


class FileUploadView(APIView):
    """Vista para subir archivos CSV de inventario"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        # Implementación básica para subida de archivos
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aquí se implementaría la lógica de procesamiento del CSV
        # Por ahora, retornamos un mensaje de éxito
        return Response({
            'message': 'File uploaded successfully',
            'filename': file_obj.name,
            'size': file_obj.size
        })


class LowStockView(APIView):
    """Vista para obtener productos con stock bajo"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener productos con stock bajo",
        description="Retorna productos que están por debajo del stock mínimo"
    )
    def get(self, request):
        low_stock_products = Product.objects.filter(
            is_active=True,
            stock__lte=F('min_stock')
        ).select_related('category', 'supplier')
        
        serializer = ProductSerializer(low_stock_products, many=True)
        return Response({
            'count': low_stock_products.count(),
            'results': serializer.data
        })


class StockMovementsView(APIView):
    """Vista para obtener movimientos de stock"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener movimientos de stock",
        description="Retorna el historial de movimientos de stock con paginación"
    )
    def get(self, request):
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        queryset = InventoryHistory.objects.select_related('product', 'user').order_by('-date_changed')
        
        start = (page - 1) * page_size
        end = start + page_size
        
        movements = queryset[start:end]
        total_count = queryset.count()
        
        movements_data = []
        for movement in movements:
            movements_data.append({
                'id': movement.id,
                'product_name': movement.product.name,
                'product_sku': movement.product.sku,
                'stock_before': movement.stock_before,
                'stock_after': movement.stock_after,
                'change_reason': movement.change_reason,
                'date_changed': movement.date_changed,
                'user': movement.user.username if movement.user else None
            })
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': movements_data
        })


class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de ubicaciones"""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return Location.objects.filter(is_active=True).order_by('warehouse', 'zone', 'aisle')
        except Exception as e:
            print(f"Error in LocationViewSet.get_queryset: {e}")
            return Location.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Locations service temporarily unavailable: {str(e)}'
            })


class InventoryItemViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de items de inventario"""
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return InventoryItem.objects.filter(is_active=True).select_related(
                'product', 'location'
            ).order_by('-created_at')
        except Exception as e:
            print(f"Error in InventoryItemViewSet.get_queryset: {e}")
            return InventoryItem.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Inventory items service temporarily unavailable: {str(e)}'
            })
    
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Obtener items por ubicación"""
        location_id = request.query_params.get('location_id')
        if not location_id:
            return Response({'error': 'location_id parameter is required'}, status=400)
        
        items = self.get_queryset().filter(location_id=location_id)
        serializer = self.get_serializer(items, many=True)
        return Response({
            'count': items.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Obtener items por producto"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter is required'}, status=400)
        
        items = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(items, many=True)
        return Response({
            'count': items.count(),
            'results': serializer.data
        })


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de clientes"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return Customer.objects.filter(is_active=True).order_by('name')
        except Exception as e:
            print(f"Error in CustomerViewSet.get_queryset: {e}")
            return Customer.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Customers service temporarily unavailable: {str(e)}'
            })


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de leads"""
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return Lead.objects.select_related('assigned_to').prefetch_related('interested_products').order_by('-created_at')
        except Exception as e:
            print(f"Error in LeadViewSet.get_queryset: {e}")
            return Lead.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Leads service temporarily unavailable: {str(e)}'
            })
    
    def perform_create(self, serializer):
        # Asignar el usuario actual como responsable si no se especifica otro
        if not serializer.validated_data.get('assigned_to'):
            serializer.validated_data['assigned_to'] = self.request.user
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Obtener leads por estado"""
        status_filter = request.query_params.get('status')
        if not status_filter:
            return Response({'error': 'status parameter is required'}, status=400)
        
        leads = self.get_queryset().filter(status=status_filter)
        serializer = self.get_serializer(leads, many=True)
        return Response({
            'count': leads.count(),
            'results': serializer.data
        })


class OpportunityViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de oportunidades (basado en Lead)"""
    queryset = Lead.objects.all()
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            # Filtrar leads que son oportunidades (con valor estimado > 0)
            return Lead.objects.filter(
                estimated_value__gt=0
            ).select_related('assigned_to').order_by('-estimated_value')
        except Exception as e:
            print(f"Error in OpportunityViewSet.get_queryset: {e}")
            return Lead.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Opportunities service temporarily unavailable: {str(e)}'
            })
    
    @action(detail=False, methods=['get'])
    def by_stage(self, request):
        """Obtener oportunidades por etapa"""
        stage = request.query_params.get('stage')
        if not stage:
            return Response({'error': 'stage parameter is required'}, status=400)
        
        opportunities = self.get_queryset().filter(status=stage)
        serializer = self.get_serializer(opportunities, many=True)
        return Response({
            'count': opportunities.count(),
            'results': serializer.data
        })
