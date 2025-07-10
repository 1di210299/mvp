from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from inventory.models import Product, InventoryItem, Transaction
from authentication.models import Company
from django.db import models
from datalens_backend.utils import get_default_company


def dashboard_stats(request):
    """
    Vista mejorada para obtener estadísticas completas del dashboard
    """
    try:
        # Usar empresa con productos peruanos reales
        company = get_default_company()
        
        if not company:
            return JsonResponse({
                'total_products': 0,
                'total_stock_value': 0,
                'low_stock_alerts': 0,
                'recent_transactions': 0,
                'active_customers': 0,
                'pipeline_value': 0,
                'top_products': [],
                'stock_levels': [],
                'recent_activity': []
            })
        
        # Obtener productos de la empresa
        products = Product.objects.filter(company=company, is_active=True)
        total_products = products.count()
        
        # Calcular valor total del inventario
        inventory_items = InventoryItem.objects.filter(
            product__company=company,
            is_active=True
        )
        
        total_stock_value = 0
        low_stock_count = 0
        
        for item in inventory_items:
            if item.unit_cost and item.quantity:
                total_stock_value += float(item.quantity * item.unit_cost)
        
        # Contar productos con stock bajo
        for product in products:
            current_stock = product.current_stock or 0
            min_stock = product.min_stock or 0
            if current_stock <= min_stock and min_stock > 0:
                low_stock_count += 1
        
        # Transacciones recientes (últimas 24 horas)
        yesterday = timezone.now() - timedelta(days=1)
        recent_transactions_count = Transaction.objects.filter(
            company=company,
            created_at__gte=yesterday
        ).count()
        
        # Top productos (los que tienen más movimiento)
        top_products = []
        top_inventory_items = inventory_items.order_by('-quantity')[:5]
        
        for item in top_inventory_items:
            product = item.product
            top_products.append({
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'description': product.description or '',
                    'category': {
                        'id': product.category.id if product.category else None,
                        'name': product.category.name if product.category else 'Sin categoría',
                        'is_active': product.category.is_active if product.category else True
                    } if product.category else None,
                    'unit_price': float(product.sale_price) if product.sale_price else 0,
                    'cost_price': float(product.cost_price) if product.cost_price else 0,
                    'min_stock': float(product.min_stock) if product.min_stock else 0,
                    'max_stock': float(product.max_stock) if product.max_stock else 0,
                    'reorder_point': float(product.reorder_point) if product.reorder_point else 0,
                    'unit': product.unit or 'unidad',
                    'weight': float(product.weight) if product.weight else None,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat()
                },
                'quantity': float(item.quantity) if item.quantity else 0,
                'value': float(item.quantity * item.unit_cost) if (item.quantity and item.unit_cost) else 0
            })
        
        # Niveles de stock por ubicación mejorado
        stock_levels = []
        
        # Obtener ubicaciones únicas
        locations_data = inventory_items.values(
            'location__name'
        ).annotate(
            total_items=Count('id'),
            total_quantity=Sum('quantity')
        ).filter(location__name__isnull=False)
        
        for location_data in locations_data:
            location_name = location_data['location__name']
            location_items = inventory_items.filter(location__name=location_name)
            
            current_stock = sum(float(item.quantity or 0) for item in location_items)
            min_stock = sum(float(item.product.min_stock or 0) for item in location_items)
            max_stock = sum(float(item.product.max_stock or 0) for item in location_items)
            
            stock_levels.append({
                'warehouse': location_name or 'Almacén Principal',
                'current_stock': current_stock,
                'min_stock': min_stock,
                'max_stock': max_stock
            })
        
        # Si no hay ubicaciones específicas, crear una genérica
        if not stock_levels:
            total_current = sum(float(item.quantity or 0) for item in inventory_items)
            total_min = sum(float(item.product.min_stock or 0) for item in inventory_items)
            total_max = sum(float(item.product.max_stock or 0) for item in inventory_items)
            
            stock_levels.append({
                'warehouse': 'Almacén Principal',
                'current_stock': total_current,
                'min_stock': total_min,
                'max_stock': total_max
            })
        
        # Actividad reciente (transacciones de los últimos 7 días)
        week_ago = timezone.now() - timedelta(days=7)
        recent_activity = []
        recent_transactions = Transaction.objects.filter(
            company=company,
            created_at__gte=week_ago
        ).order_by('-created_at')[:10]
        
        for transaction in recent_transactions:
            recent_activity.append({
                'id': transaction.id,
                'product_name': transaction.product.name if transaction.product else 'Producto desconocido',
                'quantity': float(transaction.quantity) if transaction.quantity else 0,
                'transaction_type': transaction.transaction_type,
                'created_at': transaction.created_at.isoformat(),
                'notes': transaction.notes or ''
            })
        
        # Métricas adicionales
        active_customers = 0  # Placeholder - implementar cuando esté el módulo CRM
        pipeline_value = 0    # Placeholder - implementar cuando esté el módulo CRM
        
        # Respuesta completa
        data = {
            'total_products': total_products,
            'total_stock_value': total_stock_value,
            'low_stock_alerts': low_stock_count,
            'recent_transactions': recent_transactions_count,
            'active_customers': active_customers,
            'pipeline_value': pipeline_value,
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
            'active_customers': 0,
            'pipeline_value': 0,
            'top_products': [],
            'stock_levels': [],
            'recent_activity': []
        }, status=500)
