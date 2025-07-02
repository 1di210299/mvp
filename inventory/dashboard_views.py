from django.http import JsonResponse
from django.db.models import Sum, Count
from decimal import Decimal
from inventory.models import Product, InventoryItem
from authentication.models import Company


def dashboard_stats(request):
    """
    Vista para obtener estadísticas del dashboard
    """
    try:
        # Por ahora usaremos la primera empresa (en producción sería por usuario)
        company = Company.objects.first()
        
        if not company:
            return JsonResponse({
                'total_products': 0,
                'total_value': 0,
                'low_stock_alerts': 0,
                'total_transactions_today': 0,
                'top_products': [],
                'stock_levels': []
            })
        
        # Obtener productos de la empresa
        products = Product.objects.filter(company=company, is_active=True)
        total_products = products.count()
        
        # Calcular valor total del inventario
        inventory_items = InventoryItem.objects.filter(
            product__company=company,
            is_active=True
        )
        
        total_value = 0
        low_stock_count = 0
        
        for item in inventory_items:
            total_value += float(item.quantity * item.unit_cost)
        
        # Contar productos con stock bajo
        for product in products:
            current_stock = product.current_stock
            if current_stock <= product.min_stock:
                low_stock_count += 1
        
        # Top productos (los que tienen más stock)
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
                    },
                    'unit_price': float(product.sale_price),
                    'cost_price': float(product.cost_price),
                    'min_stock': float(product.min_stock),
                    'max_stock': float(product.max_stock),
                    'reorder_point': float(product.reorder_point),
                    'unit': product.unit,
                    'weight': float(product.weight) if product.weight else None,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat()
                },
                'quantity': float(item.quantity),
                'value': float(item.quantity * item.unit_cost)
            })
        
        # Niveles de stock por ubicación
        stock_levels = []
        locations = inventory_items.values('location__name').distinct()
        
        for location in locations:
            location_name = location['location__name']
            location_items = inventory_items.filter(location__name=location_name)
            
            current_stock = sum(float(item.quantity) for item in location_items)
            min_stock = sum(float(item.product.min_stock) for item in location_items)
            max_stock = sum(float(item.product.max_stock) for item in location_items)
            
            stock_levels.append({
                'warehouse': location_name,
                'current_stock': current_stock,
                'min_stock': min_stock,
                'max_stock': max_stock
            })
        
        # Respuesta
        data = {
            'total_products': total_products,
            'total_value': total_value,
            'low_stock_alerts': low_stock_count,
            'total_transactions_today': 0,  # Por ahora 0, se puede implementar después
            'top_products': top_products,
            'stock_levels': stock_levels
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'total_products': 0,
            'total_value': 0,
            'low_stock_alerts': 0,
            'total_transactions_today': 0,
            'top_products': [],
            'stock_levels': []
        }, status=500)
