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
        # Obtener filtros de fecha desde los parámetros de la request
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Si no hay filtros de fecha válidos, usar todos los datos (sin filtro de fecha)
        if start_date_str and end_date_str and start_date_str.strip() and end_date_str.strip():
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                # Convertir a datetime para las consultas
                start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
                end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
                use_date_filter = True
            except ValueError:
                # Si hay error en las fechas, usar todos los datos
                use_date_filter = False
        else:
            # No usar filtro de fecha - mostrar todos los datos
            use_date_filter = False
            
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
        
        # Filtrar transacciones y alertas según el filtro de fecha
        if use_date_filter:
            transactions_in_range = Transaction.objects.filter(
                transaction_date__range=(start_datetime, end_datetime),
                transaction_type='sale'
            )
            
            purchases_in_range = Transaction.objects.filter(
                transaction_date__range=(start_datetime, end_datetime),
                transaction_type='purchase'
            )
            
            recent_alerts = Alert.objects.filter(
                created_at__range=(start_datetime, end_datetime)
            )
        else:
            # Sin filtro de fecha - mostrar todos los datos históricos
            transactions_in_range = Transaction.objects.filter(transaction_type='sale')
            purchases_in_range = Transaction.objects.filter(transaction_type='purchase')
            recent_alerts = Alert.objects.all()
            
        # Calcular días del período para etiquetas (solo si hay filtro de fecha)
        if use_date_filter:
            days_diff = (end_datetime - start_datetime).days
            period_label = f"last_{days_diff}_days" if days_diff > 0 else "selected_period"
        else:
            period_label = "all_time"
        
        # Ventas y compras del período seleccionado
        total_sales_value = sum(
            float(t.quantity * t.unit_cost) for t in transactions_in_range if t.quantity and t.unit_cost
        )
        total_purchases_value = sum(
            float(t.quantity * t.unit_cost) for t in purchases_in_range if t.quantity and t.unit_cost
        )
        
        # Alertas activas
        if user_company:
            active_alerts = Alert.objects.filter(company=user_company, status='active').count()
        else:
            active_alerts = Alert.objects.filter(status='active').count()
        
        # Top productos más vendidos
        top_products = []
        # Calcular usando quantity * unit_cost ya que no existe total_price
        top_sales_data = transactions_in_range.values('product').annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:5]
        
        for sale_data in top_sales_data:
            try:
                product = Product.objects.get(id=sale_data['product'])
                # Calcular total de ventas para este producto
                product_sales = transactions_in_range.filter(product=product)
                total_amount = sum(
                    float(t.quantity * t.unit_cost) for t in product_sales 
                    if t.quantity and t.unit_cost
                )
                
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
                    'total_sales': total_amount
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
        
        # Combinar todas las transacciones para actividad reciente
        if use_date_filter:
            all_transactions = Transaction.objects.filter(
                transaction_date__range=(start_datetime, end_datetime)
            )
        else:
            all_transactions = Transaction.objects.all()
        
        # Actividad reciente (últimas transacciones del período)
        recent_activity = []
        recent_trans = all_transactions.order_by('-transaction_date')[:10]
        
        for transaction in recent_trans:
            total_amount = 0
            if transaction.quantity and transaction.unit_cost:
                total_amount = float(transaction.quantity * transaction.unit_cost)
                
            recent_activity.append({
                'id': transaction.id,
                'product_name': transaction.product.name if transaction.product else 'Producto desconocido',
                'quantity': float(transaction.quantity) if transaction.quantity else 0,
                'transaction_type': transaction.transaction_type,  # Usar 'transaction_type'
                'total_amount': total_amount,
                'date': transaction.transaction_date.isoformat(),  # Usar 'transaction_date'
            })
        
        # Datos para gráficos
        # 1. Stock por proveedor (como proxy de almacén)
        stock_by_warehouse = []
        suppliers = products.values('supplier__name').distinct()
        for supplier in suppliers:
            supplier_name = supplier['supplier__name'] or 'Sin proveedor'
            supplier_products = products.filter(supplier__name=supplier['supplier__name'])
            total_stock = sum(float(p.stock or 0) for p in supplier_products)
            
            if total_stock > 0:  # Solo incluir si hay stock
                stock_by_warehouse.append({
                    'warehouse': supplier_name,
                    'current_stock': total_stock,
                    'min_stock': total_stock * 0.2,  # 20% como mínimo sugerido
                    'max_stock': total_stock * 1.5   # 150% como máximo sugerido
                })
        
        # Si no hay proveedores, crear un almacén general
        if not stock_by_warehouse:
            total_stock = sum(float(p.stock or 0) for p in products)
            if total_stock > 0:
                stock_by_warehouse.append({
                    'warehouse': 'Almacén Principal',
                    'current_stock': total_stock,
                    'min_stock': total_stock * 0.2,
                    'max_stock': total_stock * 1.5
                })
        
        # 2. Ventas por día (últimos 7 días para tendencia)
        sales_trend_data = []
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            day_sales = Transaction.objects.filter(
                transaction_date__date=date.date(),
                transaction_type='sale'
            ).aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            sales_trend_data.append({
                'date': date.date().isoformat(),
                'sales': float(day_sales)
            })
        
        # 3. Productos por categoría
        products_by_category = []
        categories = Category.objects.all()
        for category in categories:
            category_products = products.filter(category=category)
            count = category_products.count()
            if count > 0:
                products_by_category.append({
                    'category': category.name,
                    'count': count,
                    'total_stock': sum(float(p.stock or 0) for p in category_products)
                })
        
        # Respuesta completa
        data = {
            'total_products': total_products,
            'total_stock_value': total_stock_value,
            'low_stock_alerts': low_stock_count,
            'sales_value': total_sales_value,  # Campo genérico
            'purchases_value': total_purchases_value,  # Campo genérico
            'sales_last_7_days': total_sales_value,  # Mantener compatibilidad
            'purchases_last_7_days': total_purchases_value,  # Mantener compatibilidad
            'recent_transactions': all_transactions.count(),
            'active_alerts': active_alerts,
            'top_products': top_products,
            'stock_levels': stock_levels,
            'recent_activity': recent_activity,
            'period_days': days_diff if use_date_filter else None,  # Información del período
            'last_updated': timezone.now().isoformat(),
            # Datos para gráficos
            'stock_by_warehouse': stock_by_warehouse,
            'sales_trend_data': sales_trend_data,
            'products_by_category': products_by_category,
            'stock_by_category': products_by_category  # Alias para compatibilidad
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
            'sales_value': 0,
            'purchases_value': 0,
            'sales_last_7_days': 0,  # Mantener compatibilidad
            'purchases_last_7_days': 0,  # Mantener compatibilidad
            'recent_transactions': 0,
            'active_alerts': 0,
            'top_products': [],
            'stock_levels': [],
            'recent_activity': []
        }, status=500)
