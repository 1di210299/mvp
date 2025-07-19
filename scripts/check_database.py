#!/usr/bin/env python3
"""
Script para verificar datos existentes en la base de datos
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
sys.path.append('/Users/juandiegogutierrezcortez/mvp')
django.setup()

from authentication.models import Company
from inventory.models import Product, Transaction, Sale
from forecasting.models import DemandPattern, StockLevelRecommendation

def check_existing_data():
    """Verificar datos existentes en la base de datos"""
    print("🔍 VERIFICANDO DATOS EXISTENTES EN LA BASE DE DATOS")
    print("=" * 70)
    
    # Verificar Companies
    companies = Company.objects.all()
    print(f"📊 Total Companies: {companies.count()}")
    for company in companies[:5]:
        print(f"  - {company.name} (ID: {company.id})")
    
    # Verificar Products
    products = Product.objects.all()
    print(f"\n📦 Total Products: {products.count()}")
    
    # Agrupar por company
    for company in companies[:3]:
        company_products = Product.objects.filter(company=company)
        print(f"  {company.name}: {company_products.count()} productos")
        
        for product in company_products[:3]:
            print(f"    - {product.name}: Stock={product.stock}")
    
    # Verificar Transactions
    transactions = Transaction.objects.all()
    print(f"\n💰 Total Transactions: {transactions.count()}")
    
    # Verificar por tipo
    sale_transactions = Transaction.objects.filter(transaction_type='sale')
    purchase_transactions = Transaction.objects.filter(transaction_type='purchase')
    print(f"  - Ventas (sales): {sale_transactions.count()}")
    print(f"  - Compras (purchases): {purchase_transactions.count()}")
    
    # Verificar por company
    for company in companies[:3]:
        company_transactions = Transaction.objects.filter(product__company=company)
        print(f"  {company.name}: {company_transactions.count()} transacciones")
        
        if company_transactions.exists():
            recent_transactions = company_transactions.order_by('-transaction_date')[:3]
            for trans in recent_transactions:
                print(f"    - {trans.product.name}: {trans.quantity} unidades ({trans.transaction_type}) - {trans.transaction_date}")
    
    # Verificar Sales (modelo separado si existe)
    try:
        sales = Sale.objects.all()
        print(f"\n🛒 Total Sales: {sales.count()}")
        
        for company in companies[:3]:
            company_sales = Sale.objects.filter(product__company=company)
            print(f"  {company.name}: {company_sales.count()} ventas")
    except Exception as e:
        print(f"\n⚠️ Sale model no disponible o error: {str(e)}")
    
    # Verificar DemandPattern
    demand_patterns = DemandPattern.objects.all()
    print(f"\n📈 Total DemandPatterns: {demand_patterns.count()}")
    
    for company in companies[:3]:
        company_patterns = DemandPattern.objects.filter(product__company=company)
        print(f"  {company.name}: {company_patterns.count()} patrones de demanda")
    
    # Verificar StockLevelRecommendation
    stock_recommendations = StockLevelRecommendation.objects.all()
    print(f"\n📋 Total StockLevelRecommendations: {stock_recommendations.count()}")
    
    for company in companies[:3]:
        company_recommendations = StockLevelRecommendation.objects.filter(product__company=company)
        print(f"  {company.name}: {company_recommendations.count()} recomendaciones de stock")

def check_test_company_data():
    """Verificar datos específicos de la company de prueba"""
    print("\n" + "=" * 70)
    print("🔍 VERIFICANDO DATOS DE COMPANY DE PRUEBA")
    print("=" * 70)
    
    # Buscar company de prueba
    test_companies = Company.objects.filter(name__icontains='test')
    ml_companies = Company.objects.filter(name__icontains='ml')
    
    print(f"📊 Companies con 'test': {test_companies.count()}")
    print(f"📊 Companies con 'ml': {ml_companies.count()}")
    
    # Usar la que tenga más datos
    target_company = None
    if test_companies.exists():
        target_company = test_companies.first()
    elif ml_companies.exists():
        target_company = ml_companies.first()
    else:
        # Usar cualquier company con productos
        companies_with_products = Company.objects.filter(products__isnull=False).distinct()
        if companies_with_products.exists():
            target_company = companies_with_products.first()
    
    if not target_company:
        print("❌ No se encontró ninguna company con productos")
        return
    
    print(f"🎯 Analizando company: {target_company.name}")
    
    # Productos de esta company
    products = Product.objects.filter(company=target_company)
    print(f"📦 Productos: {products.count()}")
    
    for product in products:
        print(f"  - {product.name} (ID: {product.id}): Stock={product.stock}, Activo={product.is_active}")
        
        # Transacciones de este producto
        product_transactions = Transaction.objects.filter(product=product)
        sale_transactions = product_transactions.filter(transaction_type='sale')
        
        print(f"    Transacciones totales: {product_transactions.count()}")
        print(f"    Transacciones de venta: {sale_transactions.count()}")
        
        if sale_transactions.exists():
            # Mostrar algunas transacciones recientes
            recent_sales = sale_transactions.order_by('-transaction_date')[:3]
            for sale in recent_sales:
                print(f"      {sale.transaction_date}: {sale.quantity} unidades")
        
        # Calcular demanda promedio manualmente
        from django.utils import timezone
        from datetime import timedelta
        
        # Últimos 30 días
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_sales = sale_transactions.filter(transaction_date__gte=thirty_days_ago)
        
        if recent_sales.exists():
            total_quantity = sum(sale.quantity for sale in recent_sales)
            daily_average = total_quantity / 30
            print(f"    Demanda promedio (30 días): {daily_average:.2f} unidades/día")
        else:
            print("    Sin ventas en últimos 30 días")

if __name__ == '__main__':
    check_existing_data()
    check_test_company_data()
