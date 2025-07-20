"""
API para probar el sistema completo de órdenes con IA y WhatsApp
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from inventory.models import PurchaseOrder, Product, Supplier
from inventory.serializers import PurchaseOrderSerializer
from inventory.services.purchase_order_service import PurchaseOrderService
from inventory.services.purchase_order_ai_service import purchase_order_ai_service

logger = logging.getLogger(__name__)


class PurchaseOrderTestViewSet(viewsets.ModelViewSet):
    """
    ViewSet para probar el sistema completo de órdenes de compra
    """
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PurchaseOrder.objects.filter(company=self.request.user.company)
    
    @action(detail=False, methods=['post'])
    def test_complete_flow(self, request):
        """
        Probar flujo completo: Crear orden → Enviar por WhatsApp → Simular respuesta
        """
        try:
            # Datos de prueba
            test_data = request.data.get('test_data', {})
            
            # Producto por defecto para pruebas
            product = Product.objects.filter(company=request.user.company).first()
            if not product:
                # Crear producto de prueba
                product = Product.objects.create(
                    company=request.user.company,
                    name="Producto de Prueba AI",
                    description="Producto para probar sistema AI+WhatsApp",
                    current_stock=10,
                    min_stock=5,
                    unit_price=100.00,
                    category="test"
                )
            
            # Proveedor para pruebas
            supplier = Supplier.objects.filter(
                company=request.user.company,
                whatsapp_number="+51955743403"
            ).first()
            
            if not supplier:
                return Response({
                    'error': 'Proveedor de prueba no encontrado',
                    'message': 'Necesitas un proveedor con WhatsApp +51955743403'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 1. Crear orden de compra
            order_data = {
                'product': product,
                'supplier': supplier,
                'quantity': test_data.get('quantity', 5),
                'unit_price': test_data.get('unit_price', 120.00),
                'company': request.user.company,
                'notes': 'Orden de prueba - Sistema AI completo'
            }
            
            purchase_order = PurchaseOrder.objects.create(**order_data)
            
            # 2. Enviar por WhatsApp usando el servicio
            purchase_service = PurchaseOrderService(company=request.user.company)
            
            whatsapp_result = purchase_service.send_purchase_order_whatsapp(
                purchase_order_id=purchase_order.id,
                recipient_number=supplier.whatsapp_number
            )
            
            # 3. Simular análisis de respuesta
            test_responses = [
                "Sí, confirmamos el pedido. Lo tendremos listo mañana.",
                "OK, pero el precio ahora es S/130 por unidad",
                "No tenemos stock, podemos entregar la mitad",
                "Perfecto, preparando su orden ahora mismo"
            ]
            
            simulated_response = test_data.get('simulated_response', test_responses[0])
            
            # Analizar respuesta simulada
            analysis = purchase_order_ai_service.analyze_whatsapp_message(
                message_text=simulated_response,
                purchase_order=purchase_order,
                sender_phone=supplier.whatsapp_number
            )
            
            # Actualizar orden con análisis
            purchase_order.supplier_response = simulated_response
            purchase_order.ai_analysis = analysis
            
            # Actualizar estado basado en análisis
            action = analysis.get('action')
            if action == 'confirmed':
                purchase_order.status = 'confirmed'
                purchase_order.confirmed_at = timezone.now()
            elif action == 'rejected':
                purchase_order.status = 'rejected'
            elif action == 'negotiating':
                purchase_order.status = 'negotiating'
                if analysis.get('price_proposed'):
                    purchase_order.negotiated_price = analysis.get('price_proposed')
            
            purchase_order.save()
            
            # Generar respuesta de seguimiento
            follow_up = purchase_order_ai_service.generate_follow_up_message(
                purchase_order, analysis
            )
            
            return Response({
                'success': True,
                'message': 'Flujo completo ejecutado exitosamente',
                'results': {
                    'purchase_order': {
                        'id': purchase_order.id,
                        'order_number': purchase_order.order_number,
                        'status': purchase_order.status,
                        'total_amount': float(purchase_order.total_amount),
                        'created_at': purchase_order.created_at.isoformat()
                    },
                    'whatsapp_result': whatsapp_result,
                    'simulated_response': simulated_response,
                    'ai_analysis': analysis,
                    'follow_up_message': follow_up
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en flujo completo: {str(e)}")
            return Response({
                'error': str(e),
                'message': 'Error ejecutando flujo completo'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def simulate_delivery_photo(self, request, pk=None):
        """
        Simular análisis de foto de entrega
        """
        try:
            purchase_order = self.get_object()
            
            # URL de imagen de prueba
            test_image_url = request.data.get('image_url', 
                'https://via.placeholder.com/400x300.png?text=Delivery+Photo'
            )
            
            # Analizar imagen simulada
            photo_analysis = purchase_order_ai_service.analyze_delivery_photo(
                image_url=test_image_url,
                purchase_order=purchase_order
            )
            
            # Actualizar orden
            purchase_order.delivery_photo_url = test_image_url
            purchase_order.delivery_photo_analysis = photo_analysis
            
            # Marcar como entregado si es válido
            if photo_analysis.get('is_valid_delivery') and photo_analysis.get('confidence', 0) > 0.5:
                purchase_order.status = 'delivered'
                purchase_order.delivered_at = timezone.now()
            
            purchase_order.save()
            
            return Response({
                'success': True,
                'message': 'Foto de entrega analizada',
                'photo_analysis': photo_analysis,
                'order_status': purchase_order.status
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error simulando foto de entrega: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def test_summary(self, request):
        """
        Resumen de todas las pruebas del sistema
        """
        try:
            company = request.user.company
            
            # Estadísticas de órdenes
            orders = PurchaseOrder.objects.filter(company=company)
            
            stats = {
                'total_orders': orders.count(),
                'sent_via_whatsapp': orders.filter(whatsapp_sent=True).count(),
                'with_ai_analysis': orders.exclude(ai_analysis__isnull=True).count(),
                'confirmed_orders': orders.filter(status='confirmed').count(),
                'delivered_orders': orders.filter(status='delivered').count(),
                'with_delivery_photos': orders.exclude(delivery_photo_url__isnull=True).count()
            }
            
            # Últimas órdenes con análisis IA
            recent_orders = orders.filter(
                ai_analysis__isnull=False
            ).order_by('-created_at')[:5]
            
            recent_data = []
            for order in recent_orders:
                recent_data.append({
                    'order_number': order.order_number,
                    'status': order.status,
                    'supplier_response': order.supplier_response,
                    'ai_confidence': order.ai_analysis.get('confidence', 0) if order.ai_analysis else 0,
                    'created_at': order.created_at.isoformat()
                })
            
            return Response({
                'company': company.name,
                'whatsapp_configured': bool(company.whatsapp_config),
                'stats': stats,
                'recent_orders_with_ai': recent_data,
                'test_phone': "+51955743403"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
