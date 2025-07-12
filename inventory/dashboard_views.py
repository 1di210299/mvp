from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from inventory.models import Product, Sale, Alert, InventoryHistory
from django.db import models


def dashboard_stats(request):
    """
    Vista mejorada para obtener estadísticas completas del dashboard
    """
    try:
        # Obtener productos
        products = Product.objects.all()
        total_products = products.count()
        
        # Calcular valor total del inventario
        total_stock_value = 0
        low_stock_count = 0
        
        for product in products:
            if product.stock and product.price:
                total_stock_value += float(product.stock * product.price)
            
            # Contar productos con stock bajo
            if product.stock and product.stock < 10:
                low_stock_count += 1
        
        # Ventas recientes (últimas 24 horas)
        yesterday = timezone.now() - timedelta(days=1)
        recent_sales_count = Sale.objects.filter(
            date_sold__gte=yesterday
        ).count()
        
        # Top productos (los que más se han vendido)
        top_products = []
        top_sales = Sale.objects.values('product').annotate(
            total_quantity=Sum('quantity'),
            total_amount=Sum('total_amount')
        ).order_by('-total_quantity')[:5]
        
        for sale_data in top_sales:
            try:
                product = Product.objects.get(id=sale_data['product'])
                top_products.append({
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'description': product.description or '',
                        'price': float(product.price) if product.price else 0,
                        'stock': float(product.stock) if product.stock else 0,
                        'created_at': product.created_at.isoformat()
                    },
                    'quantity_sold': float(sale_data['total_quantity']) if sale_data['total_quantity'] else 0,
                    'total_sales': float(sale_data['total_amount']) if sale_data['total_amount'] else 0
                })
            except Product.DoesNotExist:
                continue
        
        # Niveles de stock 
        stock_levels = []
        
        # Agrupar productos por stock
        high_stock = products.filter(stock__gte=50).count()
        medium_stock = products.filter(stock__gte=10, stock__lt=50).count()
        low_stock = products.filter(stock__lt=10).count()
        
        stock_levels.append({
            'warehouse': 'Almacén Principal',
            'high_stock': high_stock,
            'medium_stock': medium_stock,
            'low_stock': low_stock,
            'total_stock': sum(float(p.stock or 0) for p in products)
        })
        
        # Actividad reciente (ventas de los últimos 7 días)
        week_ago = timezone.now() - timedelta(days=7)
        recent_activity = []
        recent_sales = Sale.objects.filter(
            date_sold__gte=week_ago
        ).order_by('-date_sold')[:10]
        
        for sale in recent_sales:
            recent_activity.append({
                'id': sale.id,
                'product_name': sale.product.name if sale.product else 'Producto desconocido',
                'quantity': float(sale.quantity) if sale.quantity else 0,
                'customer_name': sale.customer_name or 'Cliente anónimo',
                'total_amount': float(sale.total_amount) if sale.total_amount else 0,
                'date_sold': sale.date_sold.isoformat(),
            })
        
        # Alertas activas
        active_alerts = Alert.objects.filter(is_active=True).count()
        
        # Respuesta completa
        data = {
            'total_products': total_products,
            'total_stock_value': total_stock_value,
            'low_stock_alerts': low_stock_count,
            'recent_transactions': recent_sales_count,
            'active_alerts': active_alerts,
            'top_products': top_products,
            'stock_levels': stock_levels,
            'recent_activity': recent_activity,
            'last_updated': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        print(f"Error en dashboard_stats: {str(e)}")  # Para debugging
        return JsonResponse({
            'error': str(e),
            'total_products': 0,
            'total_stock_value': 0,
            'low_stock_alerts': 0,
            'recent_transactions': 0,
            'active_alerts': 0,
            'top_products': [],
            'stock_levels': [],
            'recent_activity': []
        }, status=500)
