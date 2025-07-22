"""
Views simplificadas para APIs REST con n8n
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone

from inventory.models import PurchaseOrder, Product, Supplier, TenantConfig
from inventory.serializers.n8n_serializers import (
    OrderCreateSerializer, 
    OrderCallbackSerializer,
    TenantConfigSerializer
)
from inventory.services.n8n_integration_service import N8nIntegrationService
from authentication.models import Company

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    POST /api/orders
    Crear orden y enviar a n8n para procesamiento
    """
    serializer = OrderCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Datos inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        data = serializer.validated_data
        
        # Obtener empresa
        try:
            company = Company.objects.get(id=data['tenant_id'])
        except Company.DoesNotExist:
            return Response(
                {'error': 'Tenant no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar configuración del tenant
        tenant_config = N8nIntegrationService.get_tenant_config(company.id)
        if not tenant_config or not tenant_config.is_configured:
            return Response(
                {'error': 'Tenant no configurado correctamente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar o crear producto
        product, created = Product.objects.get_or_create(
            sku=data.get('product_sku', data['product_name'][:20]),
            company=company,
            defaults={
                'name': data['product_name'],
                'unit_price': data['unit_price'],
                'current_stock': 0,
                'min_stock': 1
            }
        )
        
        # Buscar o crear proveedor
        supplier = None
        if data.get('supplier_name'):
            supplier, created = Supplier.objects.get_or_create(
                name=data['supplier_name'],
                company=company,
                defaults={
                    'email': data.get('supplier_email'),
                    'whatsapp_number': data.get('supplier_whatsapp'),
                    'whatsapp_enabled': bool(data.get('supplier_whatsapp'))
                }
            )
        
        # Crear orden de compra
        purchase_order = PurchaseOrder.objects.create(
            company=company,
            product=product,
            supplier=supplier,
            quantity=data['quantity'],
            unit_price=data['unit_price'],
            supplier_email=data.get('supplier_email'),
            supplier_whatsapp=data.get('supplier_whatsapp'),
            priority=data['priority'],
            notes=data.get('notes', ''),
            status='draft'
        )
        
        # Enviar a n8n para procesamiento
        n8n_result = N8nIntegrationService.send_order_to_n8n(purchase_order)
        
        if n8n_result['success']:
            # Actualizar status a 'sent' ya que n8n la procesará
            purchase_order.status = 'sent'
            purchase_order.save()
            
            return Response({
                'success': True,
                'order_id': purchase_order.id,
                'order_number': purchase_order.order_number,
                'message': 'Orden creada y enviada a n8n para procesamiento'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Error enviando a n8n',
                'details': n8n_result.get('error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error creando orden: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def order_callback(request):
    """
    POST /api/orders/callback
    Recibir updates de estado desde n8n
    """
    serializer = OrderCallbackSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Datos inválidos', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        data = serializer.validated_data
        
        # Actualizar orden
        result = N8nIntegrationService.update_order_from_n8n(
            order_id=data['order_id'],
            status=data['status'],
            supplier_response=data.get('supplier_response'),
            delivery_date=data.get('delivery_date'),
            notes=data.get('notes')
        )
        
        if result['success']:
            return Response({
                'success': True,
                'message': f'Orden {data["order_id"]} actualizada'
            })
        else:
            return Response(
                {'error': result.get('error')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    except Exception as e:
        logger.error(f"Error en callback: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])  # Para testing OAuth2
def tenant_config(request):
    """
    GET/PUT /api/tenant/config
    Obtener o actualizar configuración del tenant
    """
    try:
        # Para testing, usar la primera company disponible
        if request.user.is_authenticated:
            company = request.user.company
        else:
            # Fallback para testing sin autenticación
            company = Company.objects.first()
            
        if not company:
            return Response(
                {'error': 'No hay company disponible'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        config, created = TenantConfig.objects.get_or_create(
            company=company
        )
        
        if request.method == 'GET':
            serializer = TenantConfigSerializer(config)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = TenantConfigSerializer(config, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Configuración actualizada',
                    'config': serializer.data
                })
            else:
                return Response(
                    {'error': 'Datos inválidos', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    except Exception as e:
        logger.error(f"Error en tenant config: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
