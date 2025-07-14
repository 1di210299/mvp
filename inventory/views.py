from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Sum, Count, Q, F, DecimalField, Case, When, Value
from django.db.models.functions import TruncDate
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
    """Vista para el dashboard principal de inventario con soporte para filtros"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener estadísticas del dashboard",
        description="Retorna métricas y estadísticas principales del inventario con soporte para filtros"
    )
    def get(self, request):
        print(f"🔍 DashboardView.get() - Iniciando cálculo de estadísticas...")
        try:
            # Obtener filtros de la request
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            category = request.query_params.get('category')
            warehouse = request.query_params.get('warehouse')
            
            # Procesar filtros de fecha
            date_filter = {}
            if start_date:
                try:
                    date_filter['transaction_date__gte'] = datetime.strptime(start_date, '%Y-%m-%d')
                except ValueError:
                    pass
            if end_date:
                try:
                    date_filter['transaction_date__lte'] = datetime.strptime(end_date, '%Y-%m-%d')
                except ValueError:
                    pass
            
            # Filtros para productos
            product_filter = {'is_active': True}
            if category and category != 'all':
                product_filter['category__name__icontains'] = category
            
            # Filtros para inventory items
            inventory_filter = {'product__is_active': True}
            if warehouse and warehouse != 'all':
                inventory_filter['location__name__icontains'] = warehouse
            
            from inventory.models import InventoryItem
            
            # Estadísticas básicas con filtros
            total_products = Product.objects.filter(**product_filter).count()
            total_categories = Category.objects.filter(is_active=True).count()
            total_suppliers = Supplier.objects.filter(is_active=True).count()
            
            print(f"📊 Productos activos: {total_products}")
            print(f"📊 Categorías activas: {total_categories}")
            print(f"📊 Proveedores activos: {total_suppliers}")
            
            # Calcular valor total con filtros - CORREGIDO CON CAST
            total_stock_value = InventoryItem.objects.filter(**inventory_filter).aggregate(
                total_value=Sum(
                    Case(
                        When(quantity__isnull=False,
                             then=F('quantity') * F('unit_cost')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )['total_value'] or 0
            
            print(f"💰 Valor total de inventario: {total_stock_value}")
            
            # Stock crítico con filtros
            low_stock_items = InventoryItem.objects.filter(
                quantity__lt=30,
                **inventory_filter
            )
            low_stock_products = low_stock_items.count()
            
            print(f"⚠️ Items con stock crítico (<30): {low_stock_products}")
            
            # Productos sin stock con filtros
            out_of_stock_products = InventoryItem.objects.filter(
                quantity__lte=0,
                **inventory_filter
            ).count()
            
            print(f"❌ Items sin stock: {out_of_stock_products}")
            
            # Transacciones con filtros de fecha
            transaction_filter = {}
            if not date_filter:
                # Por defecto, últimos 7 días
                seven_days_ago = timezone.now() - timedelta(days=7)
                transaction_filter['transaction_date__gte'] = seven_days_ago
            else:
                transaction_filter.update(date_filter)
            
            try:
                recent_transactions = Transaction.objects.filter(**transaction_filter).count()
                # Transacciones de hoy específicamente
                today = timezone.now().date()
                today_transactions = Transaction.objects.filter(
                    transaction_date__date=today
                ).count()
            except Exception:
                recent_transactions = 0
                today_transactions = 0
            
            print(f"📈 Transacciones filtradas: {recent_transactions}")
            print(f"📈 Transacciones hoy: {today_transactions}")
            
            # Alertas activas
            try:
                from alerts.models import Alert
                active_alerts = Alert.objects.filter(status='active').count()
            except Exception:
                active_alerts = 0
            
            print(f"🚨 Alertas activas: {active_alerts}")
            
            # Top productos por valor con filtros - CORREGIDO CON CAST
            try:
                top_products = list(InventoryItem.objects.select_related('product').filter(
                    **inventory_filter
                ).annotate(
                    total_value=Case(
                        When(quantity__isnull=False,
                             then=F('quantity') * F('unit_cost')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ).order_by('-total_value')[:5].values(
                    'product__id', 'product__name', 'product__sku', 
                    'quantity', 'total_value', 'location__name'
                ))
            except Exception as e:
                print(f"❌ Error obteniendo top productos: {e}")
                top_products = []
            
            # DATOS PARA GRÁFICOS (CORREGIDOS)
            try:
                # Stock por categoría (para gráfico de distribución) - CORREGIDO CON CAST
                products_by_category = list(Category.objects.filter(
                    is_active=True,
                    products__is_active=True
                ).annotate(
                    count=Count('products', distinct=True),
                    total_stock=Sum('products__inventory_items__quantity'),
                    total_value=Sum(
                        Case(
                            When(products__inventory_items__quantity__isnull=False,
                                 then=F('products__inventory_items__quantity') * F('products__inventory_items__unit_cost')),
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        )
                    )
                ).values('name', 'count', 'total_stock', 'total_value'))
                
                # Formatear para frontend
                products_by_category = [
                    {
                        'category': cat['name'],
                        'value': cat['count'] or 0,
                        'stock': cat['total_stock'] or 0,
                        'total_value': float(cat['total_value'] or 0)
                    }
                    for cat in products_by_category
                ]
                
                # Stock por ubicación (para gráfico de almacenes) - CORREGIDO CON CAST
                stock_by_warehouse = list(Location.objects.annotate(
                    current_stock=Sum('inventory_items__quantity'),
                    total_items=Count('inventory_items'),
                    total_value=Sum(
                        Case(
                            When(inventory_items__quantity__isnull=False,
                                 then=F('inventory_items__quantity') * F('inventory_items__unit_cost')),
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        )
                    )
                ).values('name', 'current_stock', 'total_items', 'total_value'))
                
                # Formatear para frontend
                stock_by_warehouse = [
                    {
                        'warehouse': loc['name'],
                        'current_stock': loc['current_stock'] or 0,
                        'min_stock': 50,  # Valor por defecto
                        'max_stock': 500,  # Valor por defecto
                        'total_items': loc['total_items'] or 0,
                        'total_value': float(loc['total_value'] or 0)
                    }
                    for loc in stock_by_warehouse
                ]
                
                # Tendencia de transacciones (últimos 30 días)
                thirty_days_ago = timezone.now() - timedelta(days=30)
                transactions_trend = Transaction.objects.filter(
                    transaction_date__gte=thirty_days_ago
                ).extra(
                    select={'date': 'DATE(transaction_date)'}
                ).values('date').annotate(
                    sales=Sum('quantity', filter=Q(transaction_type='sale')),
                    purchases=Sum('quantity', filter=Q(transaction_type='purchase'))
                ).order_by('date')
                
                # Formatear para frontend
                # CORREGIDO: Usar abs() para ventas ya que están en negativo en la BD
                sales_trend = [
                    {
                        'date': str(item['date']),
                        'sales': abs(item['sales']) if item['sales'] else 0,
                        'forecast': float(abs(item['sales'])) * 1.05 if item['sales'] else 0 # Estimación simple
                    }
                    for item in transactions_trend
                ]
                
            except Exception as e:
                import traceback
                print(f"❌ Error generando datos para gráficos: {e}")
                print(f"🔍 TRACEBACK COMPLETO:")
                traceback.print_exc()
                products_by_category = []
                stock_by_warehouse = []
                sales_trend = []
            
            # NUEVO: Métricas temporales con comparación
            try:
                # Comparar con período anterior
                if date_filter:
                    # Si hay filtros de fecha, comparar con período anterior de igual duración
                    period_days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days if start_date and end_date else 30
                else:
                    period_days = 30
                
                previous_period_start = timezone.now() - timedelta(days=period_days*2)
                previous_period_end = timezone.now() - timedelta(days=period_days)
                
                previous_transactions = Transaction.objects.filter(
                    transaction_date__gte=previous_period_start,
                    transaction_date__lte=previous_period_end
                ).count()
                
                # Calcular cambio porcentual
                if previous_transactions > 0:
                    transaction_change = ((recent_transactions - previous_transactions) / previous_transactions) * 100
                else:
                    transaction_change = 0
                
                # Calcular cambio en valor de inventario (estimado)
                inventory_change = 5.2  # Placeholder - se puede calcular con historical data
                
            except Exception as e:
                transaction_change = 0
                inventory_change = 0
                print(f"❌ Error calculando cambios: {e}")
            
            # Respuesta completa con todos los datos
            dashboard_data = {
                # Métricas principales
                'total_products': total_products,
                'total_categories': total_categories,
                'total_suppliers': total_suppliers,
                'total_stock_value': float(total_stock_value),
                'low_stock_products': low_stock_products,
                'out_of_stock_products': out_of_stock_products,
                'recent_transactions': recent_transactions,
                'active_alerts': active_alerts,
                
                # Aliases para compatibilidad con frontend
                'total_value': float(total_stock_value),
                'low_stock_alerts': low_stock_products,
                'total_transactions_today': today_transactions,
                'active_customers': 0,
                'pipeline_value': 0,
                
                # DATOS PARA GRÁFICOS (CORREGIDOS)
                'products_by_category': products_by_category,
                'stock_by_warehouse': stock_by_warehouse,
                'sales_trend': sales_trend,
                
                # NUEVO: Métricas temporales con contexto
                'period_info': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'period_days': period_days if 'period_days' in locals() else 30,
                    'transaction_change': round(transaction_change, 1),
                    'inventory_change': round(inventory_change, 1),
                    'timeframe': f"últimos {period_days if 'period_days' in locals() else 30} días"
                },
                
                # Productos destacados
                'top_products': top_products,
                
                # Filtros aplicados
                'applied_filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'category': category,
                    'warehouse': warehouse
                }
            }
            
            print(f"✅ Dashboard data calculado exitosamente:")
            print(f"   📦 Total productos: {total_products}")
            print(f"   ⚠️ Stock crítico: {low_stock_products}")
            print(f"   💰 Valor total: {total_stock_value}")
            print(f"   📊 Gráficos: {len(products_by_category)} categorías, {len(stock_by_warehouse)} almacenes")
            
            return Response(dashboard_data)
            
        except Exception as e:
            print(f"❌ Error en dashboard: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
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
                'products_by_category': [],
                'stock_by_warehouse': [],
                'sales_trend': [],
                # Campos adicionales que el frontend espera
                'low_stock_alerts': 0,
                'total_value': 0,
                'total_transactions_today': 0,
                'active_customers': 0,
                'pipeline_value': 0,
                'period_info': {
                    'start_date': None,
                    'end_date': None,
                    'period_days': 30,
                    'transaction_change': 0,
                    'inventory_change': 0,
                    'timeframe': 'últimos 30 días'
                },
                'applied_filters': {
                    'start_date': None,
                    'end_date': None,
                    'category': None,
                    'warehouse': None
                },
                'error': f'Dashboard temporarily unavailable: {str(e)}'
            })


class InventoryDashboardView(APIView):
    """Vista para dashboard de inventario con datos corregidos"""
    
    def get(self, request):
        print(f"🔍 InventoryDashboardView.get() - Iniciando cálculo de estadísticas...")
        
        # NUEVO: Procesar filtros del frontend
        filters = {}
        category_filter = request.GET.get('category')
        warehouse_filter = request.GET.get('warehouse')
        status_filter = request.GET.get('status')
        search_filter = request.GET.get('search')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        print(f"🔍 Filtros recibidos: category={category_filter}, warehouse={warehouse_filter}, status={status_filter}, search={search_filter}, start_date={start_date}, end_date={end_date}")
        
        try:
            # FIX: Recalcular stocks agregados desde InventoryItem hacia Product
            self._update_product_stocks_from_inventory_items()
            
            # NUEVO: Construir queryset base de productos con filtros (SIN FECHA)
            products_queryset = Product.objects.filter(is_active=True)
            
            # Aplicar filtro de categoría
            if category_filter and category_filter != 'all':
                products_queryset = products_queryset.filter(category_id=category_filter)
                print(f"🔍 Aplicando filtro de categoría: {category_filter}")
            
            # Aplicar filtro de almacén (a través de InventoryItem)
            if warehouse_filter and warehouse_filter != 'all':
                # Obtener el nombre del almacén a partir del ID
                try:
                    location = Location.objects.get(id=warehouse_filter)
                    warehouse_name = location.warehouse
                    products_queryset = products_queryset.filter(inventory_items__location__warehouse=warehouse_name)
                    print(f"🔍 Aplicando filtro de almacén: {warehouse_name} (ID: {warehouse_filter})")
                except Location.DoesNotExist:
                    print(f"❌ Almacén con ID {warehouse_filter} no encontrado")
                    pass
            
            # Aplicar filtro de búsqueda
            if search_filter:
                products_queryset = products_queryset.filter(
                    Q(name__icontains=search_filter) |
                    Q(sku__icontains=search_filter) |
                    Q(description__icontains=search_filter)
                )
                print(f"🔍 Aplicando filtro de búsqueda: {search_filter}")
                
            # CORREGIDO: Aplicar filtro de estado al final para tener queryset completo
            if status_filter and status_filter != 'all':
                if status_filter == 'low_stock':
                    products_queryset = products_queryset.filter(stock__lt=F('min_stock'), stock__gt=0)
                elif status_filter == 'out_of_stock':
                    products_queryset = products_queryset.filter(stock__lte=0)
                elif status_filter == 'in_stock':
                    products_queryset = products_queryset.filter(stock__gt=0)
                print(f"🔍 Aplicando filtro de estado: {status_filter}")
            
            # Estadísticas básicas con filtros aplicados
            total_products = products_queryset.count()
            total_categories = Category.objects.filter(is_active=True).count()
            total_suppliers = Supplier.objects.filter(is_active=True).count()
            
            print(f"📊 Productos activos (filtrados): {total_products}")
            
            # NUEVO: Construir queryset de InventoryItem con filtros (SIN FECHA)
            inventory_items_queryset = InventoryItem.objects.filter(product__in=products_queryset)
            
            # Aplicar filtro de almacén a inventory items
            if warehouse_filter and warehouse_filter != 'all':
                try:
                    location = Location.objects.get(id=warehouse_filter)
                    warehouse_name = location.warehouse
                    inventory_items_queryset = inventory_items_queryset.filter(location__warehouse=warehouse_name)
                    print(f"🔍 Aplicando filtro de almacén a inventory items: {warehouse_name}")
                except Location.DoesNotExist:
                    print(f"❌ Almacén con ID {warehouse_filter} no encontrado para inventory items")
                    pass
            
            # FIX: Calcular valor total usando InventoryItem filtrado - CORREGIDO CON CAST
            total_stock_value = inventory_items_queryset.aggregate(
                total_value=Sum(
                    Case(
                        When(quantity__isnull=False,
                             then=F('quantity') * F('unit_cost')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )['total_value'] or 0
            
            print(f"💰 Valor total de inventario (filtrado): {total_stock_value}")
            
            # FIX: Calcular stock crítico usando los stocks agregados en Product filtrado
            # Productos con stock por debajo del mínimo - USANDO QUERYSET FILTRADO
            low_stock_products = products_queryset.filter(
                stock__lt=F('min_stock'),
                stock__gt=0  # Excluir productos sin stock
            ).count()
            
            print(f"⚠️ Productos con stock crítico (filtrados): {low_stock_products}")
            
            # Productos completamente sin stock - USANDO QUERYSET FILTRADO
            out_of_stock_products = products_queryset.filter(
                stock__lte=0
            ).count()
            
            print(f"❌ Productos sin stock (filtrados): {out_of_stock_products}")
            
            # CORREGIDO: Transacciones con filtros de fecha SOLAMENTE
            transactions_queryset = Transaction.objects.all()
            
            # Aplicar filtros de fecha SOLO a transacciones
            if start_date:
                transactions_queryset = transactions_queryset.filter(transaction_date__gte=start_date)
                print(f"🔍 Aplicando filtro de fecha inicio a transacciones: {start_date}")
            if end_date:
                transactions_queryset = transactions_queryset.filter(transaction_date__lte=end_date)
                print(f"🔍 Aplicando filtro de fecha fin a transacciones: {end_date}")
            
            # CORREGIDO: Solo aplicar filtro de 7 días si no hay ningún filtro de fecha explícito
            # Si el usuario selecciona "all", no aplicar ningún filtro de fecha
            if not start_date and not end_date:
                # No aplicar filtro de fecha por defecto - mostrar todas las transacciones
                print("🔍 No hay filtros de fecha - mostrando todas las transacciones")
            
            # Aplicar filtros de productos a transacciones
            if category_filter and category_filter != 'all':
                transactions_queryset = transactions_queryset.filter(product__category_id=category_filter)
            if warehouse_filter and warehouse_filter != 'all':
                # Filtrar transacciones por almacén usando el nombre del almacén
                try:
                    location = Location.objects.get(id=warehouse_filter)
                    warehouse_name = location.warehouse
                    transactions_queryset = transactions_queryset.filter(product__inventory_items__location__warehouse=warehouse_name)
                    print(f"🔍 Aplicando filtro de almacén a transacciones: {warehouse_name} (ID: {warehouse_filter})")
                except Location.DoesNotExist:
                    print(f"❌ Almacén con ID {warehouse_filter} no encontrado para transacciones")
                    pass
            if search_filter:
                transactions_queryset = transactions_queryset.filter(
                    Q(product__name__icontains=search_filter) |
                    Q(product__sku__icontains=search_filter)
                )
            
            # Transacciones con filtros aplicados
            recent_transactions = transactions_queryset.count()
            print(f"📊 Transacciones recientes (filtradas): {recent_transactions}")
            
            # OPTIMIZADO: Calcular métricas de ventas y compras con filtros de fecha usando agregaciones
            sales_queryset = transactions_queryset.filter(transaction_type='sale')
            purchases_queryset = transactions_queryset.filter(transaction_type='purchase')
            
            # OPTIMIZADO: Calcular ventas usando agregación
            sales_aggregation = sales_queryset.aggregate(
                total_sales=Sum(
                    Case(
                        When(product__sale_price__isnull=False,
                             then=F('quantity') * F('product__sale_price') * -1),  # Convertir a positivo
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ),
                count=Count('id')
            )
            
            sales_value = float(sales_aggregation['total_sales'] or 0)
            sales_count = sales_aggregation['count'] or 0
            
            # OPTIMIZADO: Calcular compras usando agregación  
            purchases_aggregation = purchases_queryset.aggregate(
                total_purchases=Sum(
                    Case(
                        When(product__cost_price__isnull=False,
                             then=F('quantity') * F('product__cost_price')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ),
                count=Count('id')
            )
            
            purchases_value = float(purchases_aggregation['total_purchases'] or 0)
            purchases_count = purchases_aggregation['count'] or 0
            
            # Calcular ganancia neta
            net_profit = sales_value - purchases_value
            
            print(f"💰 Ventas en período filtrado: {sales_count} transacciones, S/ {sales_value:.2f}")
            print(f"📦 Compras en período filtrado: {purchases_count} transacciones, S/ {purchases_value:.2f}")
            print(f"📈 Ganancia neta en período filtrado: S/ {net_profit:.2f}")
            print(f"🔍 Filtros aplicados a transacciones: start_date={start_date}, end_date={end_date}, category={category_filter}, warehouse={warehouse_filter}")
            
            # Top 5 productos por valor total - CORREGIDO CON CAST y filtrado
            try:
                top_products = list(products_queryset.annotate(
                    total_value=Case(
                        When(stock__isnull=False,
                             then=F('stock') * F('sale_price')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ).order_by('-total_value')[:5].values(
                    'id', 'name', 'sku', 'stock', 'total_value'
                ))
            except Exception as e:
                print(f"❌ Error obteniendo top productos: {e}")
                top_products = []
            
            # Stock por categoría - CORREGIDO CON CAST y filtrado
            try:
                categories_queryset = Category.objects.filter(is_active=True)
                if category_filter and category_filter != 'all':
                    categories_queryset = categories_queryset.filter(id=category_filter)
                
                stock_by_category = list(categories_queryset.annotate(
                    total_products=Count('products', filter=Q(products__is_active=True) & Q(products__in=products_queryset)),
                    total_stock=Sum('products__stock', filter=Q(products__is_active=True) & Q(products__in=products_queryset)),
                    total_value=Sum(
                        Case(
                            When(products__stock__isnull=False,
                                 then=F('products__stock') * F('products__sale_price')),
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        ),
                        filter=Q(products__is_active=True) & Q(products__in=products_queryset)
                    )
                ).values('name', 'total_products', 'total_stock', 'total_value'))
                print(f"📊 Stock por categoría (filtrado): {len(stock_by_category)} categorías")
            except Exception as e:
                print(f"❌ Error obteniendo stock por categoría: {e}")
                stock_by_category = []
            
            # NUEVO: Calcular ventas por fecha para el gráfico
            try:
                # Obtener ventas agrupadas por fecha
                sales_by_date = sales_queryset.annotate(
                    date=TruncDate('transaction_date')
                ).values('date').annotate(
                    total_sales=Sum(
                        Case(
                            When(product__sale_price__isnull=False,
                                 then=F('quantity') * F('product__sale_price') * -1),  # Convertir a positivo
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        )
                    ),
                    count=Count('id')
                ).order_by('date')
                
                sales_trend_data = []
                for sale in sales_by_date:
                    sales_trend_data.append({
                        'date': sale['date'].strftime('%Y-%m-%d') if sale['date'] else '',
                        'sales': float(sale['total_sales'] or 0),
                        'count': sale['count'] or 0
                    })
                
                print(f"📊 Tendencia de ventas por fecha: {len(sales_trend_data)} días con datos")
                
            except Exception as e:
                print(f"❌ Error calculando tendencia de ventas: {e}")
                sales_trend_data = []

            # NUEVO: Stock por almacén para el gráfico
            try:
                # Obtener almacenes únicos filtrados
                warehouses_queryset = Location.objects.filter(is_active=True)
                if warehouse_filter and warehouse_filter != 'all':
                    try:
                        location = Location.objects.get(id=warehouse_filter)
                        warehouse_name = location.warehouse
                        warehouses_queryset = warehouses_queryset.filter(warehouse=warehouse_name)
                    except Location.DoesNotExist:
                        pass
                
                stock_by_warehouse = []
                seen_warehouses = set()
                
                for location in warehouses_queryset:
                    if location.warehouse not in seen_warehouses:
                        # Calcular stock total para este almacén
                        warehouse_stock = InventoryItem.objects.filter(
                            location__warehouse=location.warehouse,
                            location__is_active=True,
                            product__is_active=True
                        ).aggregate(
                            total_stock=Sum('quantity'),
                            min_stock=Sum('product__min_stock'),
                            max_stock=Sum('product__max_stock')
                        )
                        
                        stock_by_warehouse.append({
                            'warehouse': location.warehouse,
                            'current_stock': float(warehouse_stock['total_stock'] or 0),
                            'min_stock': float(warehouse_stock['min_stock'] or 0),
                            'max_stock': float(warehouse_stock['max_stock'] or 0)
                        })
                        seen_warehouses.add(location.warehouse)
                
                print(f"🏢 Stock por almacén (filtrado): {len(stock_by_warehouse)} almacenes")
            except Exception as e:
                print(f"❌ Error obteniendo stock por almacén: {e}")
                stock_by_warehouse = []
            
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
                'stock_by_warehouse': stock_by_warehouse,
                'products_by_category': stock_by_category,  # Alias para compatibilidad con frontend
                'recent_sales': [],
                
                # NUEVO: Métricas de ventas y compras que cambian con fecha
                'sales_value': float(sales_value),
                'sales_count': sales_count,
                'purchases_value': float(purchases_value),
                'purchases_count': purchases_count,
                'net_profit': float(net_profit),
                'sales_trend_data': sales_trend_data,
                
                # Campos adicionales que el frontend puede esperar
                'total_value': float(total_stock_value),
                'low_stock_alerts': low_stock_products,
                'total_transactions_today': recent_transactions,
                'active_customers': 0,
                'pipeline_value': 0,
                
                # Información de filtros aplicados
                'filters_applied': {
                    'category': category_filter,
                    'warehouse': warehouse_filter, 
                    'status': status_filter,
                    'search': search_filter,
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
            print(f"✅ Dashboard data generado con {total_products} productos filtrados")
            print(f"📊 Resumen: {low_stock_products} productos con stock crítico, {out_of_stock_products} sin stock")
            
            return Response(dashboard_data)
            
        except Exception as e:
            print(f"❌ Error en InventoryDashboardView: {str(e)}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return Response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)
    
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


class FilterOptionsView(APIView):
    """Vista para obtener opciones de filtros del dashboard"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener opciones de filtros",
        description="Retorna las opciones disponibles para los filtros del dashboard (categorías, almacenes, estados)"
    )
    def get(self, request):
        """Devolver opciones de filtros para el dashboard"""
        try:
            print("🔍 FilterOptionsView: Obteniendo opciones de filtros...")
            
            # Obtener categorías activas
            categories = list(Category.objects.filter(is_active=True).values('id', 'name'))
            print(f"📦 Categorías encontradas: {len(categories)}")
            
            # Obtener almacenes únicos (sin duplicados)
            warehouses_raw = Location.objects.filter(is_active=True).values('warehouse').distinct()
            warehouses = []
            seen_warehouses = set()
            
            for warehouse_data in warehouses_raw:
                warehouse_name = warehouse_data['warehouse']
                if warehouse_name not in seen_warehouses:
                    # Obtener el primer ID de este almacén para usar como referencia
                    location = Location.objects.filter(is_active=True, warehouse=warehouse_name).first()
                    if location:
                        warehouses.append({
                            'id': location.id,
                            'warehouse': warehouse_name
                        })
                        seen_warehouses.add(warehouse_name)
            
            print(f"🏢 Almacenes únicos encontrados: {len(warehouses)}")
            
            # Obtener tipos de transacciones únicos
            transaction_types = list(Transaction.objects.values_list('transaction_type', flat=True).distinct())
            print(f"📋 Tipos de transacciones: {len(transaction_types)}")
            
            # Estados predefinidos para el filtro
            status_options = [
                {'id': 'all', 'name': 'Todos los estados'},
                {'id': 'in_stock', 'name': 'Con stock'},
                {'id': 'low_stock', 'name': 'Stock bajo'},
                {'id': 'out_of_stock', 'name': 'Sin stock'}
            ]
            
            filter_options = {
                'categories': categories,
                'warehouses': warehouses,
                'transaction_types': transaction_types,
                'status_options': status_options
            }
            
            print(f"✅ FilterOptionsView: Opciones de filtros enviadas exitosamente")
            return Response(filter_options)
            
        except Exception as e:
            print(f"❌ Error en FilterOptionsView: {str(e)}")
            return Response({
                'categories': [],
                'warehouses': [],
                'transaction_types': [],
                'status_options': [],
                'error': f'Filter options temporarily unavailable: {str(e)}'
            }, status=500)