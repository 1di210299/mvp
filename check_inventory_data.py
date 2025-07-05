#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from inventory.models import Category, Supplier, Location, Product, InventoryItem, Transaction
from authentication.models import Company, User

print("=== Verificando datos de inventario ===")

print(f"Companías: {Company.objects.count()}")
print(f"Usuarios: {User.objects.count()}")
print(f"Categorías: {Category.objects.count()}")
print(f"Proveedores: {Supplier.objects.count()}")
print(f"Ubicaciones: {Location.objects.count()}")
print(f"Productos: {Product.objects.count()}")
print(f"Items de inventario: {InventoryItem.objects.count()}")
print(f"Transacciones: {Transaction.objects.count()}")

if Product.objects.exists():
    print("\n=== Primeros 5 productos ===")
    for product in Product.objects.all()[:5]:
        print(f"- {product.sku}: {product.name} (Empresa: {product.company.name})")

if Category.objects.exists():
    print("\n=== Categorías ===")
    for category in Category.objects.all():
        print(f"- {category.name} (Empresa: {category.company.name})")
