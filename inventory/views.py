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
from .models import (
    Category, Supplier, Location, Product, InventoryItem, Transaction,
    Customer, Lead, Opportunity, OpportunityProduct, Contact, Activity
)
from .serializers import (
    CategorySerializer, SupplierSerializer, LocationSerializer,
    ProductSerializer, InventoryItemSerializer, TransactionSerializer,
    ProductStockSerializer, DashboardStatsSerializer,
    CustomerSerializer, LeadSerializer, OpportunitySerializer,
    OpportunityProductSerializer, ContactSerializer, ActivitySerializer,
    LeadConvertSerializer, CRMDashboardSerializer, CustomerInsightsSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de categorías"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # permission_classes = [IsAuthenticated]  # Temporalmente desactivado para desarrollo
    
    def get_queryset(self):
        # return Category.objects.filter(company=self.request.user.company)  # Temporalmente desactivado
        return Category.objects.all()  # Devolver todas las categorías para desarrollo
    
    def perform_create(self, serializer):
        # serializer.save(company=self.request.user.company)  # Temporalmente desactivado
        # Por ahora guardar con la primera empresa disponible
        from authentication.models import Company
        company = Company.objects.first()
        if company:
            serializer.save(company=company)


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de proveedores"""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    # TEMPORAL: Comentado para desarrollo - descomentar en producción
    # permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # TEMPORAL: Sin filtro por empresa para desarrollo
        return Supplier.objects.all()
        # return Supplier.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # TEMPORAL: Sin asignación automática de empresa para desarrollo
        serializer.save()
        # serializer.save(company=self.request.user.company)


class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de ubicaciones"""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    # permission_classes = [IsAuthenticated]  # TEMPORAL: Comentado para desarrollo
    
    def get_queryset(self):
        # TEMPORAL: Sin filtro por empresa para desarrollo
        return Location.objects.all()
        # return Location.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # TEMPORAL: Sin asignación automática de empresa para desarrollo
        serializer.save()
        # serializer.save(company=self.request.user.company)

class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de productos"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # permission_classes = [IsAuthenticated]  # ← COMENTADO TEMPORALMENTE
    
    def get_queryset(self):
        # ← MODIFICADO: Sin filtro por company temporalmente
        queryset = Product.objects.all()
        
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
        # ← MODIFICADO: Sin company temporalmente
        serializer.save()
        # serializer.save(company=self.request.user.company)  # ← COMENTADO TEMPORALMENTE
    
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
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    # permission_classes = [IsAuthenticated]  # TEMPORAL: Comentado para desarrollo
    
    def get_queryset(self):
        # TEMPORAL: Sin filtro por empresa para desarrollo
        return InventoryItem.objects.all()
        # return InventoryItem.objects.filter(
        #     product__company=self.request.user.company
        # )
    
    def perform_create(self, serializer):
        # TEMPORAL: Sin validación de empresa para desarrollo
        serializer.save()
        # # Validar que el producto pertenezca a la empresa del usuario
        # product = serializer.validated_data['product']
        # if product.company != self.request.user.company:
        #     raise permissions.PermissionDenied("No tienes acceso a este producto")
        # 
        # serializer.save()


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de transacciones"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    # TEMPORAL: Comentado para desarrollo - descomentar en producción
    # permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # TEMPORAL: Sin filtro por empresa para desarrollo
        return Transaction.objects.all()
        # return Transaction.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # TEMPORAL: Sin asignación automática de empresa y usuario para desarrollo
        from authentication.models import Company, User
        company = Company.objects.first()
        user = User.objects.first()
        if company and user:
            serializer.save(company=company, user=user)
        else:
            serializer.save()
        # serializer.save(
        #     company=self.request.user.company,
        #     user=self.request.user
        # )


class DashboardView(APIView):
    """Vista para el dashboard principal de inventario"""
    # permission_classes = [IsAuthenticated]  # TEMPORAL: Comentado para desarrollo
    
    @extend_schema(
        summary="Obtener estadísticas del dashboard",
        description="Retorna métricas y estadísticas principales del inventario"
    )
    def get(self, request):
        # TEMPORAL: Usar la primera empresa para desarrollo
        from authentication.models import Company
        company = Company.objects.first()
        if not company:
            return Response({"error": "No hay empresas disponibles"}, status=400)
        
        # company = request.user.company
        
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


# ===== CRM VIEWSETS =====

class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de clientes"""
    serializer_class = CustomerSerializer
    # permission_classes = [IsAuthenticated]  # TEMPORAL: Comentado para desarrollo
    
    def get_queryset(self):
        # TEMPORAL: Sin filtro por empresa para desarrollo
        return Customer.objects.all()
        # return Customer.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # TEMPORAL: Sin asignación automática de empresa para desarrollo
        from authentication.models import Company
        company = Company.objects.first()
        if company:
            serializer.save(company=company)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def set_custom_field(self, request, pk=None):
        """Establece un campo personalizado para el cliente"""
        customer = self.get_object()
        field_name = request.data.get('field_name')
        value = request.data.get('value')
        
        try:
            customer.set_custom_field_value(field_name, value)
            return Response({'status': 'success'})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """Obtiene insights de IA para el cliente"""
        customer = self.get_object()
        # Aquí podrías integrar con tu sistema de IA existente
        insights = {
            'customer_id': customer.id,
            'customer_name': customer.display_name,
            'insights': [
                'Cliente de alto valor con historial de compras regulares',
                'Prefiere productos de categoría premium',
                'Responde bien a ofertas por email'
            ],
            'recommendations': [
                'Enviar catálogo de productos nuevos',
                'Ofrecer descuento por lealtad',
                'Programar llamada de seguimiento'
            ],
            'risk_score': 0.2,
            'lifetime_value': float(customer.annual_revenue or 0),
            'next_best_action': 'Programar reunión de seguimiento'
        }
        
        serializer = CustomerInsightsSerializer(insights)
        return Response(serializer.data)


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de leads"""
    serializer_class = LeadSerializer
    # permission_classes = [IsAuthenticated]  # TEMPORAL: Comentado para desarrollo
    
    def get_queryset(self):
        # TEMPORAL: Sin filtro por empresa para desarrollo
        return Lead.objects.all()
        # return Lead.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # TEMPORAL: Sin asignación automática de empresa para desarrollo
        from authentication.models import Company
        company = Company.objects.first()
        if company:
            serializer.save(company=company)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def convert_to_customer(self, request, pk=None):
        """Convierte un lead en cliente"""
        lead = self.get_object()
        
        try:
            customer = lead.convert_to_customer()
            
            # Si se requiere crear oportunidad
            if request.data.get('create_opportunity'):
                opportunity_data = {
                    'name': request.data.get('opportunity_name', f'Oportunidad - {customer.display_name}'),
                    'amount': request.data.get('opportunity_amount', 0),
                    'expected_close_date': request.data.get('opportunity_close_date'),
                    'customer': customer,
                    'company': lead.company,
                    'assigned_to': lead.assigned_to
                }
                
                opportunity = Opportunity.objects.create(**{k: v for k, v in opportunity_data.items() if v is not None})
            
            customer_serializer = CustomerSerializer(customer)
            return Response({
                'status': 'success',
                'customer': customer_serializer.data,
                'message': f'Lead convertido exitosamente en cliente: {customer.display_name}'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'])
    def set_custom_field(self, request, pk=None):
        """Establece un campo personalizado para el lead"""
        lead = self.get_object()
        field_name = request.data.get('field_name')
        value = request.data.get('value')
        
        try:
            lead.set_custom_field_value(field_name, value)
            return Response({'status': 'success'})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)


class OpportunityViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de oportunidades"""
    serializer_class = OpportunitySerializer
    # permission_classes = [IsAuthenticated]  # TEMPORAL: Comentado para desarrollo
    
    def get_queryset(self):
        # TEMPORAL: Sin filtro por empresa para desarrollo
        return Opportunity.objects.all()
        # return Opportunity.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # TEMPORAL: Sin asignación automática de empresa para desarrollo
        from authentication.models import Company
        company = Company.objects.first()
        if company:
            serializer.save(company=company)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def add_product(self, request, pk=None):
        """Agrega un producto a la oportunidad"""
        opportunity = self.get_object()
        
        product_data = {
            'opportunity': opportunity,
            'product_id': request.data.get('product_id'),
            'quantity': request.data.get('quantity', 1),
            'unit_price': request.data.get('unit_price'),
            'discount_percent': request.data.get('discount_percent', 0)
        }
        
        serializer = OpportunityProductSerializer(data=product_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Lista los productos de la oportunidad"""
        opportunity = self.get_object()
        products = OpportunityProduct.objects.filter(opportunity=opportunity)
        serializer = OpportunityProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_custom_field(self, request, pk=None):
        """Establece un campo personalizado para la oportunidad"""
        opportunity = self.get_object()
        field_name = request.data.get('field_name')
        value = request.data.get('value')
        
        try:
            opportunity.set_custom_field_value(field_name, value)
            return Response({'status': 'success'})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de contactos"""
    serializer_class = ContactSerializer
    # permission_classes = [IsAuthenticated]  # TEMPORAL: Comentado para desarrollo
    
    def get_queryset(self):
        # TEMPORAL: Sin filtro por empresa para desarrollo
        return Contact.objects.all()
        # return Contact.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # TEMPORAL: Sin asignación automática de empresa para desarrollo
        from authentication.models import Company
        company = Company.objects.first()
        if company:
            serializer.save(company=company)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def set_custom_field(self, request, pk=None):
        """Establece un campo personalizado para el contacto"""
        contact = self.get_object()
        field_name = request.data.get('field_name')
        value = request.data.get('value')
        
        try:
            contact.set_custom_field_value(field_name, value)
            return Response({'status': 'success'})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)


class ActivityViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de actividades"""
    serializer_class = ActivitySerializer
    # permission_classes = [IsAuthenticated]  # TEMPORAL: Comentado para desarrollo
    
    def get_queryset(self):
        # TEMPORAL: Sin filtro por empresa para desarrollo
        return Activity.objects.all()
        # return Activity.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        # TEMPORAL: Sin asignación automática de empresa para desarrollo
        from authentication.models import Company
        company = Company.objects.first()
        if company:
            serializer.save(company=company)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Marca una actividad como completada"""
        activity = self.get_object()
        activity.status = 'completed'
        activity.completed_date = timezone.now()
        activity.outcome = request.data.get('outcome', '')
        activity.next_action = request.data.get('next_action', '')
        activity.save()
        
        serializer = self.get_serializer(activity)
        return Response(serializer.data)


# ===== VISTAS ESPECIALES CRM =====

class CRMDashboardView(APIView):
    """Vista para el dashboard CRM"""
    
    def get(self, request):
        """Obtiene estadísticas del CRM"""
        # TEMPORAL: Sin filtro por empresa
        from django.db.models import Count, Sum, Avg
        from datetime import datetime, timedelta
        
        current_date = timezone.now().date()
        current_month_start = current_date.replace(day=1)
        
        # Estadísticas básicas
        total_customers = Customer.objects.filter(is_active=True).count()
        total_leads = Lead.objects.filter(is_active=True).count()
        total_opportunities = Opportunity.objects.filter(is_active=True).count()
        
        # Pipeline value
        pipeline_value = Opportunity.objects.filter(
            is_active=True,
            stage__in=['prospecting', 'qualification', 'needs_analysis', 'value_proposition', 'proposal', 'negotiation']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Estadísticas del mes
        leads_this_month = Lead.objects.filter(
            created_at__date__gte=current_month_start
        ).count()
        
        customers_this_month = Customer.objects.filter(
            created_at__date__gte=current_month_start
        ).count()
        
        opportunities_won_this_month = Opportunity.objects.filter(
            stage='closed_won',
            actual_close_date__gte=current_month_start
        ).count()
        
        # Tasa de conversión
        total_converted = Lead.objects.filter(status='won').count()
        conversion_rate = (total_converted / total_leads * 100) if total_leads > 0 else 0
        
        # Datos para gráficos
        leads_by_source = list(Lead.objects.values('source').annotate(count=Count('id')))
        opportunities_by_stage = list(Opportunity.objects.values('stage').annotate(count=Count('id')))
        
        # Pipeline por etapa
        sales_pipeline = list(Opportunity.objects.values('stage').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ))
        
        # Actividades de la semana
        week_start = current_date - timedelta(days=current_date.weekday())
        activities_this_week = list(Activity.objects.filter(
            scheduled_date__date__gte=week_start
        ).values('activity_type').annotate(count=Count('id')))
        
        dashboard_data = {
            'total_customers': total_customers,
            'total_leads': total_leads,
            'total_opportunities': total_opportunities,
            'pipeline_value': pipeline_value,
            'leads_this_month': leads_this_month,
            'customers_this_month': customers_this_month,
            'opportunities_won_this_month': opportunities_won_this_month,
            'conversion_rate': conversion_rate,
            'leads_by_source': leads_by_source,
            'opportunities_by_stage': opportunities_by_stage,
            'sales_pipeline': sales_pipeline,
            'activities_this_week': activities_this_week,
        }
        
        serializer = CRMDashboardSerializer(dashboard_data)
        return Response(serializer.data)
