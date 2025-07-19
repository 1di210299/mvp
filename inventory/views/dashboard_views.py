"""
Dashboard API ViewSets para MVP
Purchase Orders Dashboard API y Email Tracking Dashboard API
Backend only - APIs REST para consumir desde React/TypeScript frontend
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from inventory.models import (
    PurchaseOrder, 
    TrackedEmail, 
    EmailCampaign, 
    EmailClick,
    Supplier
)
from inventory.serializers import (
    PurchaseOrderSerializer,
    TrackedEmailSerializer,
    SupplierSerializer,
    EmailCampaignSerializer
)
from inventory.services.email_tracking_service import get_email_tracking_service
from authentication.models import Company


class DashboardAPIViewSet(viewsets.ViewSet):
    """
    API ViewSet para Dashboard principal
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        GET /api/inventory/dashboard/overview/
        Resumen general del sistema
        """
        user = request.user
        company = user.company
        
        # Métricas generales
        data = {
            'metrics': {
                'total_purchase_orders': PurchaseOrder.objects.filter(company=company).count(),
                'total_suppliers': Supplier.objects.count(),  # Sin filtro de company
                'total_emails_tracked': TrackedEmail.objects.filter(company=company).count(),
                'active_campaigns': EmailCampaign.objects.filter(company=company, is_active=True).count(),
            },
            'quick_stats': {
                'pending_orders': PurchaseOrder.objects.filter(company=company, status='pending').count(),
                'confirmed_orders': PurchaseOrder.objects.filter(company=company, status='confirmed').count(),
                'emails_this_week': TrackedEmail.objects.filter(
                    company=company,
                    sent_at__gte=timezone.now() - timedelta(days=7)
                ).count(),
                'open_rate_this_week': self._calculate_open_rate(company, days=7),
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def activity_chart(self, request):
        """
        GET /api/inventory/dashboard/activity-chart/
        Datos para gráfico de actividad de los últimos 7 días
        """
        user = request.user
        company = user.company
        
        # Datos de los últimos 7 días
        last_7_days = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            
            po_count = PurchaseOrder.objects.filter(
                company=company,
                created_at__date=date
            ).count()
            
            email_count = TrackedEmail.objects.filter(
                company=company,
                sent_at__date=date
            ).count()
            
            last_7_days.append({
                'date': date.strftime('%Y-%m-%d'),
                'day_name': date.strftime('%a'),
                'purchase_orders': po_count,
                'emails_tracked': email_count
            })
        
        return Response({
            'data': list(reversed(last_7_days)),
            'labels': [day['day_name'] for day in reversed(last_7_days)]
        })
    
    def _calculate_open_rate(self, company, days=30):
        """Calcular tasa de apertura"""
        since_date = timezone.now() - timedelta(days=days)
        emails = TrackedEmail.objects.filter(company=company, sent_at__gte=since_date)
        total = emails.count()
        opened = emails.filter(status__in=['opened', 'clicked', 'replied']).count()
        
        return round((opened / total * 100) if total > 0 else 0, 1)


class PurchaseOrderDashboardViewSet(viewsets.ViewSet):
    """
    API ViewSet para Dashboard de Purchase Orders
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        GET /api/inventory/purchase-orders-dashboard/overview/
        Resumen de Purchase Orders con filtros
        """
        user = request.user
        company = user.company
        
        # Filtros de query params
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status_filter = request.query_params.get('status', '')
        supplier_filter = request.query_params.get('supplier', '')
        
        # Query base
        orders = PurchaseOrder.objects.filter(company=company)
        
        # Aplicar filtros
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
        if status_filter:
            orders = orders.filter(status=status_filter)
        if supplier_filter:
            orders = orders.filter(supplier_id=supplier_filter)
        
        # Métricas
        total_orders = orders.count()
        pending_orders = orders.filter(status='pending').count()
        confirmed_orders = orders.filter(status='confirmed').count()
        completed_orders = orders.filter(status='completed').count()
        cancelled_orders = orders.filter(status='cancelled').count()
        
        # Valor total
        total_value = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Distribución por estado
        status_distribution = list(orders.values('status').annotate(count=Count('id')))
        
        # Top suppliers
        top_suppliers = list(
            orders.values('supplier__name', 'supplier__id')
            .annotate(
                order_count=Count('id'), 
                total_value=Sum('total_amount')
            )
            .order_by('-order_count')[:5]
        )
        
        data = {
            'metrics': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'confirmed_orders': confirmed_orders,
                'completed_orders': completed_orders,
                'cancelled_orders': cancelled_orders,
                'total_value': float(total_value),
            },
            'charts': {
                'status_distribution': status_distribution,
                'top_suppliers': top_suppliers,
            },
            'filters_applied': {
                'date_from': date_from,
                'date_to': date_to,
                'status': status_filter,
                'supplier': supplier_filter,
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def orders_list(self, request):
        """
        GET /api/inventory/purchase-orders-dashboard/orders-list/
        Lista paginada de Purchase Orders con email tracking
        """
        user = request.user
        company = user.company
        
        # Filtros
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status_filter = request.query_params.get('status', '')
        supplier_filter = request.query_params.get('supplier', '')
        
        # Paginación
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        offset = (page - 1) * page_size
        
        # Query
        orders = PurchaseOrder.objects.filter(company=company)
        
        # Aplicar filtros
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
        if status_filter:
            orders = orders.filter(status=status_filter)
        if supplier_filter:
            orders = orders.filter(supplier_id=supplier_filter)
        
        # Ordenar y paginar
        orders = orders.order_by('-created_at')[offset:offset + page_size]
        
        # Enriquecer con datos de email tracking
        orders_with_tracking = []
        for order in orders:
            # Buscar email tracking relacionado
            tracking_data = TrackedEmail.objects.filter(
                company=company,
                subject__icontains=order.order_number
            ).first()
            
            order_data = PurchaseOrderSerializer(order).data
            order_data['email_tracking'] = {
                'has_tracking': tracking_data is not None,
                'tracking_id': tracking_data.tracking_id if tracking_data else None,
                'status': tracking_data.status if tracking_data else None,
                'sent_at': tracking_data.sent_at if tracking_data else None,
                'open_count': tracking_data.open_count if tracking_data else 0,
                'click_count': tracking_data.click_count if tracking_data else 0,
            }
            
            orders_with_tracking.append(order_data)
        
        # Contar total para paginación
        total_count = PurchaseOrder.objects.filter(company=company).count()
        total_pages = (total_count + page_size - 1) // page_size
        
        return Response({
            'orders': orders_with_tracking,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
            }
        })
    
    @action(detail=False, methods=['get'])
    def suppliers_list(self, request):
        """
        GET /api/inventory/purchase-orders-dashboard/suppliers-list/
        Lista de suppliers para filtros
        """
        user = request.user
        company = user.company
        
        suppliers = Supplier.objects.all().order_by('name')
        suppliers_data = SupplierSerializer(suppliers, many=True).data
        
        return Response({
            'suppliers': suppliers_data
        })


class EmailTrackingDashboardViewSet(viewsets.ViewSet):
    """
    API ViewSet para Dashboard de Email Tracking
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        GET /api/inventory/email-tracking-dashboard/overview/
        Resumen de Email Tracking con métricas
        """
        user = request.user
        company = user.company
        
        # Filtros
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        campaign_filter = request.query_params.get('campaign', '')
        status_filter = request.query_params.get('status', '')
        
        # Query base
        emails = TrackedEmail.objects.filter(company=company)
        
        # Aplicar filtros
        if date_from:
            emails = emails.filter(sent_at__gte=date_from)
        if date_to:
            emails = emails.filter(sent_at__lte=date_to)
        if campaign_filter:
            emails = emails.filter(campaign_id=campaign_filter)
        if status_filter:
            emails = emails.filter(status=status_filter)
        
        # Métricas principales
        total_sent = emails.count()
        total_opened = emails.filter(status__in=['opened', 'clicked', 'replied']).count()
        total_clicked = emails.filter(status__in=['clicked', 'replied']).count()
        total_replied = emails.filter(status='replied').count()
        
        # Calcular rates
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
        reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
        
        # Engagement score (fórmula personalizada)
        engagement_score = (open_rate * 0.3 + click_rate * 0.4 + reply_rate * 0.3)
        
        # Distribución por estado
        status_distribution = list(emails.values('status').annotate(count=Count('id')))
        
        # Response time analysis
        emails_with_response = emails.filter(replied_at__isnull=False)
        avg_response_time = None
        
        if emails_with_response.exists():
            response_times = []
            for email in emails_with_response:
                if email.sent_at and email.replied_at:
                    diff = email.replied_at - email.sent_at
                    response_times.append(diff.total_seconds() / 3600)  # en horas
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        data = {
            'metrics': {
                'total_sent': total_sent,
                'total_opened': total_opened,
                'total_clicked': total_clicked,
                'total_replied': total_replied,
                'open_rate': round(open_rate, 1),
                'click_rate': round(click_rate, 1),
                'reply_rate': round(reply_rate, 1),
                'engagement_score': round(engagement_score, 1),
                'avg_response_time_hours': round(avg_response_time, 1) if avg_response_time else None,
            },
            'charts': {
                'status_distribution': status_distribution,
            },
            'filters_applied': {
                'date_from': date_from,
                'date_to': date_to,
                'campaign': campaign_filter,
                'status': status_filter,
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def daily_performance(self, request):
        """
        GET /api/inventory/email-tracking-dashboard/daily-performance/
        Performance diario de emails (últimos 30 días)
        """
        user = request.user
        company = user.company
        
        # Últimos 30 días
        days = int(request.query_params.get('days', 30))
        daily_stats = []
        
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            
            emails_day = TrackedEmail.objects.filter(
                company=company,
                sent_at__date=date
            )
            
            sent = emails_day.count()
            opened = emails_day.filter(status__in=['opened', 'clicked', 'replied']).count()
            clicked = emails_day.filter(status__in=['clicked', 'replied']).count()
            replied = emails_day.filter(status='replied').count()
            
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'day_name': date.strftime('%a'),
                'sent': sent,
                'opened': opened,
                'clicked': clicked,
                'replied': replied,
                'open_rate': round((opened / sent * 100) if sent > 0 else 0, 1),
                'click_rate': round((clicked / sent * 100) if sent > 0 else 0, 1),
                'reply_rate': round((replied / sent * 100) if sent > 0 else 0, 1),
            })
        
        return Response({
            'daily_performance': list(reversed(daily_stats)),
            'period_days': days
        })
    
    @action(detail=False, methods=['get'])
    def emails_list(self, request):
        """
        GET /api/inventory/email-tracking-dashboard/emails-list/
        Lista paginada de emails tracked
        """
        user = request.user
        company = user.company
        
        # Filtros
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        campaign_filter = request.query_params.get('campaign', '')
        status_filter = request.query_params.get('status', '')
        
        # Paginación
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        offset = (page - 1) * page_size
        
        # Query
        emails = TrackedEmail.objects.filter(company=company)
        
        # Aplicar filtros
        if date_from:
            emails = emails.filter(sent_at__gte=date_from)
        if date_to:
            emails = emails.filter(sent_at__lte=date_to)
        if campaign_filter:
            emails = emails.filter(campaign_id=campaign_filter)
        if status_filter:
            emails = emails.filter(status=status_filter)
        
        # Ordenar y paginar
        emails = emails.order_by('-sent_at')[offset:offset + page_size]
        
        # Serializar
        emails_data = TrackedEmailSerializer(emails, many=True).data
        
        # Contar total
        total_count = TrackedEmail.objects.filter(company=company).count()
        total_pages = (total_count + page_size - 1) // page_size
        
        return Response({
            'emails': emails_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
            }
        })
    
    @action(detail=False, methods=['get'])
    def campaigns_list(self, request):
        """
        GET /api/inventory/email-tracking-dashboard/campaigns-list/
        Lista de campañas para filtros
        """
        user = request.user
        company = user.company
        
        campaigns = EmailCampaign.objects.filter(company=company).order_by('-created_at')
        campaigns_data = EmailCampaignSerializer(campaigns, many=True).data
        
        return Response({
            'campaigns': campaigns_data
        })
    
    @action(detail=False, methods=['get'])
    def top_performing_emails(self, request):
        """
        GET /api/inventory/email-tracking-dashboard/top-performing-emails/
        Top 10 emails con mejor performance
        """
        user = request.user
        company = user.company
        
        top_emails = TrackedEmail.objects.filter(
            company=company,
            open_count__gt=0
        ).order_by('-open_count', '-click_count')[:10]
        
        emails_data = TrackedEmailSerializer(top_emails, many=True).data
        
        return Response({
            'top_emails': emails_data
        })
