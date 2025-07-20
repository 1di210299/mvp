from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from inventory.models import Product, Category, Supplier, Transaction
from alerts.models import Alert
from django.db import models


def dashboard_stats(request):
    """
    Vista mejorada para obtener estadísticas completas del dashboard
    """
    try:
        # Obtener productos de la empresa del usuario
        user_company = request.user.company if hasattr(request.user, 'company') else None
        if user_company:
            products = Product.objects.filter(company=user_company)
        else:
            products = Product.objects.all()
        
        total_products = products.count()
        
        # Calcular valor total del inventario
        total_stock_value = 0
        low_stock_count = 0
        
        for product in products:
            if product.stock and product.cost_price:
                total_stock_value += float(product.stock * product.cost_price)
            
            # Contar productos con stock bajo
            if product.stock and product.stock <= product.min_stock:
                low_stock_count += 1
        
        # Transacciones recientes (últimos 7 días)
        week_ago = timezone.now() - timedelta(days=7)
        if user_company:
            recent_transactions = Transaction.objects.filter(
                company=user_company,
                transaction_date__gte=week_ago
            )
        else:
            recent_transactions = Transaction.objects.filter(
                transaction_date__gte=week_ago
            )
        
        # Ventas y compras de los últimos 7 días
        sales_transactions = recent_transactions.filter(transaction_type='sale')
        purchase_transactions = recent_transactions.filter(transaction_type='purchase')
        
        total_sales_value = sum(
            float(t.total_price) for t in sales_transactions if t.total_price
        )
        total_purchases_value = sum(
            float(t.total_price) for t in purchase_transactions if t.total_price
        )
        
        # Alertas activas
        if user_company:
            active_alerts = Alert.objects.filter(company=user_company, is_resolved=False).count()
        else:
            active_alerts = Alert.objects.filter(is_resolved=False).count()
        
        # Top productos más vendidos
        top_products = []
        top_sales_data = sales_transactions.values('product').annotate(
            total_quantity=Sum('quantity'),
            total_amount=Sum('total_price')
        ).order_by('-total_quantity')[:5]
        
        for sale_data in top_sales_data:
            try:
                product = Product.objects.get(id=sale_data['product'])
                top_products.append({
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'description': product.description or '',
                        'cost_price': float(product.cost_price) if product.cost_price else 0,
                        'sale_price': float(product.sale_price) if product.sale_price else 0,
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
        
        # Actividad reciente (transacciones de los últimos 7 días)
        recent_activity = []
        recent_trans = recent_transactions.order_by('-transaction_date')[:10]
        
        for transaction in recent_trans:
            recent_activity.append({
                'id': transaction.id,
                'product_name': transaction.product.name if transaction.product else 'Producto desconocido',
                'quantity': float(transaction.quantity) if transaction.quantity else 0,
                'transaction_type': transaction.transaction_type,
                'total_amount': float(transaction.total_price) if transaction.total_price else 0,
                'date': transaction.transaction_date.isoformat(),
            })
        
        # Respuesta completa
        data = {
            'total_products': total_products,
            'total_stock_value': total_stock_value,
            'low_stock_alerts': low_stock_count,
            'sales_last_7_days': total_sales_value,
            'purchases_last_7_days': total_purchases_value,
            'recent_transactions': recent_transactions.count(),
            'active_alerts': active_alerts,
            'top_products': top_products,
            'stock_levels': stock_levels,
            'recent_activity': recent_activity,
            'last_updated': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        print(f"Error en dashboard_stats: {str(e)}")  # Para debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'total_products': 0,
            'total_stock_value': 0,
            'low_stock_alerts': 0,
            'sales_last_7_days': 0,
            'purchases_last_7_days': 0,
            'recent_transactions': 0,
            'active_alerts': 0,
            'top_products': [],
            'stock_levels': [],
            'recent_activity': []
        }, status=500)
