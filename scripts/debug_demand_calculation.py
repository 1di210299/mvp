#!/usr/bin/env python
"""
Debug: ¿Por qué solo encuentra demanda para ML Test Product 0?
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from inventory.models import Product, Sale
from authentication.models import Company
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum

# Buscar la empresa ML Test Company
company = Company.objects.filter(name="ML Test Company").first()
if not company:
    print("❌ No se encontró ML Test Company")
    sys.exit(1)

print(f"✅ Empresa encontrada: {company.name} (ID: {company.id})")

# Listar productos ML
products = Product.objects.filter(company=company).order_by('name')
print(f"\n📦 Productos en {company.name}:")

for product in products:
    print(f"  - {product.name} (ID: {product.id})")
    
    # Contar ventas
    sales_count = Sale.objects.filter(product=product).count()
    total_quantity = Sale.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
    
    print(f"    Ventas: {sales_count} registros, Cantidad total: {total_quantity}")
    
    # Estadísticas de demanda como lo hace el servicio
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)
    
    sales = Sale.objects.filter(
        product=product,
        date_sold__range=[start_date, end_date]
    )
    
    if sales.exists():
        # Agrupar por día como hace el servicio
        daily_demand = sales.extra(
            select={'date': 'DATE(date_sold)'}
        ).values('date').annotate(
            total_demand=Sum('quantity')
        )
        
        demands = [float(item['total_demand']) for item in daily_demand if item['total_demand'] is not None]
        average_demand = sum(demands) / len(demands) if demands else 0
        
        print(f"    📊 Demanda promedio calculada: {average_demand:.2f}")
        print(f"    📅 Días con ventas: {len(demands)}")
        print(f"    📈 Primeros valores: {demands[:5] if demands else 'Ninguno'}")
    else:
        print(f"    ❌ Sin ventas en el período de análisis")
    
    print()
