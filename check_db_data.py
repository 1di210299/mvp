#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar qué datos hay en la base de datos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from authentication.models import Company, User
from inventory.models import Category, Supplier, Location, Product, InventoryItem, Transaction

def check_database_data():
    """Verificar qué datos existen en la base de datos"""
    
    print("=" * 60)
    print("VERIFICACIÓN DE DATOS EN LA BASE DE DATOS")
    print("=" * 60)
    
    # Empresas
    print("\n=== EMPRESAS ===")
    companies = Company.objects.all()
    if companies:
        for company in companies:
            print(f"- {company.name} (RUC: {company.ruc})")
            print(f"  Dirección: {company.address}")
            print(f"  Teléfono: {company.phone}")
            print(f"  Email: {company.email}")
            print(f"  Tipo suscripción: {company.subscription_type}")
    else:
        print("No hay empresas registradas")
    
    # Categorías
    print("\n=== CATEGORÍAS ===")
    categories = Category.objects.all()
    if categories:
        for cat in categories:
            parent_info = f" (Padre: {cat.parent.name})" if cat.parent else ""
            print(f"- {cat.name}{parent_info}")
            print(f"  Empresa: {cat.company.name}")
            print(f"  Descripción: {cat.description}")
    else:
        print("No hay categorías registradas")
    
    # Proveedores
    print("\n=== PROVEEDORES ===")
    suppliers = Supplier.objects.all()
    if suppliers:
        for supplier in suppliers:
            print(f"- {supplier.name} (RUC: {supplier.ruc})")
            print(f"  Empresa: {supplier.company.name}")
            print(f"  Contacto: {supplier.contact_person}")
            print(f"  Email: {supplier.email}")
            print(f"  Teléfono: {supplier.phone}")
            print(f"  Términos pago: {supplier.payment_terms}")
            print(f"  Límite crédito: S/ {supplier.credit_limit}")
    else:
        print("No hay proveedores registrados")
    
    # Ubicaciones
    print("\n=== UBICACIONES ===")
    locations = Location.objects.all()
    if locations:
        for location in locations:
            print(f"- {location.name} (Código: {location.code})")
            print(f"  Empresa: {location.company.name}")
            print(f"  Almacén: {location.warehouse}")
            if location.zone:
                print(f"  Zona: {location.zone}")
            if location.aisle:
                print(f"  Pasillo: {location.aisle}")
            print(f"  Descripción: {location.description}")
    else:
        print("No hay ubicaciones registradas")
    
    # Productos
    print("\n=== PRODUCTOS ===")
    products = Product.objects.all()
    if products:
        for product in products:
            print(f"- {product.sku}: {product.name}")
            print(f"  Empresa: {product.company.name}")
            print(f"  Categoría: {product.category.name if product.category else 'Sin categoría'}")
            print(f"  Proveedor: {product.supplier.name if product.supplier else 'Sin proveedor'}")
            print(f"  Unidad: {product.get_unit_display()}")
            print(f"  Precio costo: S/ {product.cost_price}")
            print(f"  Precio venta: S/ {product.sale_price}")
            print(f"  Stock mínimo: {product.min_stock}")
            print(f"  Stock actual: {product.current_stock}")
    else:
        print("No hay productos registrados")
    
    # Items de inventario
    print("\n=== ITEMS DE INVENTARIO ===")
    inventory_items = InventoryItem.objects.all()
    if inventory_items:
        for item in inventory_items:
            print(f"- {item.product.sku} en {item.location.name}")
            print(f"  Cantidad: {item.quantity}")
            print(f"  Cantidad reservada: {item.reserved_quantity}")
            print(f"  Cantidad disponible: {item.available_quantity}")
            print(f"  Costo unitario: S/ {item.unit_cost}")
            print(f"  Valor total: S/ {item.total_value}")
            if item.batch_number:
                print(f"  Lote: {item.batch_number}")
            if item.expiration_date:
                print(f"  Vencimiento: {item.expiration_date}")
    else:
        print("No hay items de inventario registrados")
    
    # Transacciones
    print("\n=== TRANSACCIONES ===")
    transactions = Transaction.objects.all()[:10]  # Solo las últimas 10
    if transactions:
        print("(Mostrando las últimas 10 transacciones)")
        for transaction in transactions:
            print(f"- {transaction.get_transaction_type_display()}: {transaction.product.sku}")
            print(f"  Cantidad: {transaction.quantity}")
            print(f"  Fecha: {transaction.transaction_date}")
            print(f"  Referencia: {transaction.reference_number}")
            print(f"  Ubicación: {transaction.location.name}")
    else:
        print("No hay transacciones registradas")
    
    # Resumen de conteos
    print("\n" + "=" * 60)
    print("RESUMEN DE CONTEOS")
    print("=" * 60)
    print(f"Empresas: {companies.count()}")
    print(f"Categorías: {categories.count()}")
    print(f"Proveedores: {suppliers.count()}")
    print(f"Ubicaciones: {locations.count()}")
    print(f"Productos: {products.count()}")
    print(f"Items de inventario: {inventory_items.count()}")
    print(f"Transacciones: {Transaction.objects.count()}")
    print("=" * 60)

if __name__ == "__main__":
    check_database_data()
