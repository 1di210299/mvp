"""
ViewSets y APIs para órdenes de compra automáticas
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta

from inventory.models import PurchaseOrder, PurchaseOrderTracking, PurchaseOrderEmailLog, Product
from inventory.serializers.purchase_order_serializers import (
    PurchaseOrderSerializer, PurchaseOrderCreateSerializer, PurchaseOrderUpdateSerializer,
    PurchaseOrderTrackingSerializer, PurchaseOrderEmailLogSerializer,
    AutoGenerateOrderSerializer, SendEmailSerializer, PurchaseOrderStatsSerializer,
    ProductLowStockSerializer
)
from inventory.services.purchase_order_service import PurchaseOrderService


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de órdenes de compra"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar órdenes por empresa del usuario"""
        return PurchaseOrder.objects.filter(
            company=self.request.user.company
        ).select_related(
            'product', 'supplier', 'company', 'created_by'
        ).prefetch_related(
            'tracking_history', 'email_logs'
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'create':
            return PurchaseOrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PurchaseOrderUpdateSerializer
        return PurchaseOrderSerializer
    
    def perform_create(self, serializer):
        """Crear orden con datos del usuario"""
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user
        )
    
    @action(detail=False, methods=['post'], url_path='auto-generate')
    def auto_generate(self, request):
        """
        Generar órdenes de compra automáticamente para productos con stock bajo
        POST /api/purchase-orders/auto-generate/
        """
        serializer = AutoGenerateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            purchase_service = PurchaseOrderService()
            
            # Usar empresa del usuario o la especificada
            company = request.user.company
            if serializer.validated_data.get('company_id'):
                # Solo admin puede generar para otras empresas
                if not request.user.is_staff:
                    return Response(
                        {'error': 'No tiene permisos para generar órdenes para otras empresas'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                from authentication.models import Company
                try:
                    company = Company.objects.get(id=serializer.validated_data['company_id'])
                except Company.DoesNotExist:
                    return Response(
                        {'error': 'Empresa no encontrada'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Generar órdenes
            results = purchase_service.check_low_stock_and_generate_orders(company=company)
            
            if 'error' in results:
                return Response(
                    {'error': results['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response({
                'success': True,
                'message': f'Proceso completado: {results["orders_generated"]} órdenes generadas',
                'results': results
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error generando órdenes: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        """
        Enviar email de orden de compra
        POST /api/purchase-orders/{id}/send-email/
        """
        purchase_order = self.get_object()
        
        serializer = SendEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            purchase_service = PurchaseOrderService()
            email_service = purchase_service.email_service
            
            # Determinar destinatario
            recipient_email = (
                serializer.validated_data.get('recipient_email') or
                purchase_order.supplier_email or
                (purchase_order.supplier.email if purchase_order.supplier else None)
            )
            
            if not recipient_email:
                return Response(
                    {'error': 'No hay email de destinatario configurado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generar o usar contenido personalizado
            if serializer.validated_data.get('use_custom_content'):
                email_content = {
                    'subject': serializer.validated_data.get('custom_subject', f'Orden de Compra #{purchase_order.order_number}'),
                    'content': serializer.validated_data.get('custom_content', '')
                }
            else:
                email_content = email_service.generate_purchase_order_email(purchase_order)
            
            # Enviar email
            success = email_service.send_purchase_order_email(
                purchase_order=purchase_order,
                recipient_email=recipient_email,
                subject=email_content['subject'],
                content=email_content['content']
            )
            
            if success:
                purchase_order.mark_as_sent(recipient_email)
                purchase_order.email_subject = email_content['subject']
                purchase_order.email_content = email_content['content']
                purchase_order.save()
                
                return Response({
                    'success': True,
                    'message': f'Email enviado exitosamente a {recipient_email}',
                    'email_sent_to': recipient_email
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Error enviando email'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': f'Error enviando email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Actualizar estado de orden de compra
        POST /api/purchase-orders/{id}/update-status/
        """
        purchase_order = self.get_object()
        
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if not new_status:
            return Response(
                {'error': 'Estado requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(PurchaseOrder.STATUS_CHOICES):
            return Response(
                {'error': 'Estado inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Actualizar estado
            purchase_order.update_status(new_status, notes)
            
            # Crear entrada de seguimiento
            PurchaseOrderTracking.objects.create(
                purchase_order=purchase_order,
                status=new_status,
                notes=notes,
                created_by=request.user
            )
            
            return Response({
                'success': True,
                'message': f'Estado actualizado a {purchase_order.get_status_display()}',
                'new_status': new_status
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error actualizando estado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Estadísticas de órdenes de compra
        GET /api/purchase-orders/stats/
        """
        try:
            queryset = self.get_queryset()
            
            # Estadísticas básicas
            total_orders = queryset.count()
            
            status_counts = queryset.values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
            
            status_dict = dict(status_counts)
            
            # Órdenes vencidas
            overdue_orders = queryset.filter(
                expected_delivery_date__lt=timezone.now().date(),
                status__in=['sent', 'confirmed', 'in_transit']
            ).count()
            
            # Monto total
            total_amount = queryset.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            # Tiempo promedio de entrega (solo órdenes recibidas)
            avg_delivery = queryset.filter(
                status='received',
                actual_delivery_date__isnull=False,
                expected_delivery_date__isnull=False
            ).aggregate(
                avg_days=Avg('actual_delivery_date') - Avg('expected_delivery_date')
            )
            
            # Tasa de éxito de emails
            total_emails = queryset.filter(email_sent=True).count()
            successful_emails = PurchaseOrderEmailLog.objects.filter(
                purchase_order__in=queryset,
                sent_successfully=True
            ).count()
            
            email_success_rate = (successful_emails / total_emails * 100) if total_emails > 0 else 0
            
            stats = {
                'total_orders': total_orders,
                'pending_orders': status_dict.get('draft', 0),
                'sent_orders': status_dict.get('sent', 0),
                'received_orders': status_dict.get('received', 0),
                'cancelled_orders': status_dict.get('cancelled', 0),
                'overdue_orders': overdue_orders,
                'total_amount': total_amount,
                'avg_delivery_time': avg_delivery.get('avg_days', 0) if avg_delivery else 0,
                'email_success_rate': email_success_rate
            }
            
            serializer = PurchaseOrderStatsSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo estadísticas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='low-stock-products')
    def low_stock_products(self, request):
        """
        Productos con stock bajo que necesitan órdenes
        GET /api/purchase-orders/low-stock-products/
        """
        try:
            from django.db.models import F
            
            # Productos con stock bajo
            low_stock_products = Product.objects.filter(
                company=request.user.company,
                is_active=True
            ).filter(
                Q(current_stock__lte=F('min_stock')) |
                Q(current_stock__lte=10)
            ).select_related('supplier')
            
            products_data = []
            purchase_service = PurchaseOrderService()
            
            for product in low_stock_products:
                # Verificar si tiene orden pendiente
                has_pending = purchase_service._has_pending_order(product)
                
                # Calcular cantidad recomendada
                recommended_qty = purchase_service._calculate_order_quantity(product)
                
                # Determinar prioridad
                priority = purchase_service._determine_priority(product)
                
                products_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_sku': product.sku or '',
                    'current_stock': product.current_stock or 0,
                    'min_stock': product.min_stock or 0,
                    'supplier_name': product.supplier.name if product.supplier else 'Sin proveedor',
                    'supplier_email': product.supplier.email if product.supplier else '',
                    'has_pending_order': has_pending,
                    'recommended_quantity': recommended_qty,
                    'priority': priority
                })
            
            serializer = ProductLowStockSerializer(products_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo productos: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ✅ NUEVO: Endpoint para tracking de emails de órdenes de compra
    @action(detail=True, methods=['get'], url_path='email-tracking')
    def email_tracking_status(self, request, pk=None):
        """
        Obtener estado del tracking del email para una orden de compra específica
        """
        try:
            purchase_order = self.get_object()
            service = PurchaseOrderService()
            
            tracking_status = service.get_purchase_order_tracking_status(purchase_order)
            
            return Response({
                'order_number': purchase_order.order_number,
                'tracking': tracking_status,
                'email_details': {
                    'sent': purchase_order.email_sent,
                    'sent_at': purchase_order.email_sent_at,
                    'sent_to': purchase_order.email_sent_to,
                    'subject': purchase_order.email_subject,
                    'tracking_id': purchase_order.tracking_id,
                    'campaign_id': purchase_order.email_tracking_campaign_id
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo tracking: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='tracking-summary')
    def tracking_summary(self, request):
        """
        Obtener resumen de tracking de todas las órdenes de compra con emails
        """
        try:
            # Parámetros opcionales
            days_back = int(request.query_params.get('days', 30))
            
            service = PurchaseOrderService()
            company = request.user.company
            
            summary = service.get_purchase_orders_with_tracking_summary(
                company=company,
                days_back=days_back
            )
            
            return Response(summary)
            
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo resumen de tracking: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PurchaseOrderTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para seguimiento de órdenes (solo lectura)"""
    
    serializer_class = PurchaseOrderTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar seguimientos por empresa del usuario"""
        return PurchaseOrderTracking.objects.filter(
            purchase_order__company=self.request.user.company
        ).select_related(
            'purchase_order', 'created_by'
        ).order_by('-created_at')


class PurchaseOrderEmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para logs de emails (solo lectura)"""
    
    serializer_class = PurchaseOrderEmailLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar logs por empresa del usuario"""
        return PurchaseOrderEmailLog.objects.filter(
            purchase_order__company=self.request.user.company
        ).select_related(
            'purchase_order'
        ).order_by('-sent_at')
