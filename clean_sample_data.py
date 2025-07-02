#!/usr/bin/env python
"""
Script para limpiar datos de prueba
Ejecutar con: python manage.py shell < clean_sample_data.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from authentication.models import Company, User
from inventory.models import Category, Supplier, Location, Product, InventoryItem


def clean_sample_data():
    """Limpiar todos los datos de prueba"""
    print("=== Limpiando datos de prueba ===\n")
    
    try:
        # Obtener la empresa de prueba
        company = Company.objects.filter(ruc='20123456789').first()
        
        if not company:
            print("No se encontró la empresa de prueba.")
            return
        
        print(f"Limpiando datos de: {company.name}")
        
        # Contar registros antes
        inventory_count = InventoryItem.objects.filter(product__company=company).count()
        product_count = Product.objects.filter(company=company).count()
        location_count = Location.objects.filter(company=company).count()
        supplier_count = Supplier.objects.filter(company=company).count()
        category_count = Category.objects.filter(company=company).count()
        
        print(f"\nRegistros a eliminar:")
        print(f"- Items de inventario: {inventory_count}")
        print(f"- Productos: {product_count}")
        print(f"- Ubicaciones: {location_count}")
        print(f"- Proveedores: {supplier_count}")
        print(f"- Categorías: {category_count}")
        
        # Eliminar en orden correcto para evitar problemas de FK
        print("\nEliminando registros...")
        
        # 1. Items de inventario
        InventoryItem.objects.filter(product__company=company).delete()
        print("✓ Items de inventario eliminados")
        
        # 2. Productos
        Product.objects.filter(company=company).delete()
        print("✓ Productos eliminados")
        
        # 3. Ubicaciones
        Location.objects.filter(company=company).delete()
        print("✓ Ubicaciones eliminadas")
        
        # 4. Proveedores
        Supplier.objects.filter(company=company).delete()
        print("✓ Proveedores eliminados")
        
        # 5. Categorías
        Category.objects.filter(company=company).delete()
        print("✓ Categorías eliminadas")
        
        # 6. Empresa (opcional - descomenta si quieres eliminar también la empresa)
        # company.delete()
        # print("✓ Empresa eliminada")
        
        print("\n=== ¡Datos limpiados exitosamente! ===")
        
    except Exception as e:
        print(f"Error al limpiar datos: {e}")
        raise


if __name__ == "__main__":
    clean_sample_data()
