#!/usr/bin/env python3
"""
Script para crear automáticamente todos los campos mixed
Ejecutar: python manage.py shell < scripts/setup_mixed_fields.py
"""

from data_import.models import FieldDefinition

def create_mixed_fields():
    """Crear todos los campos para tipos mezclados"""
    
    mixed_fields = {
        'mixed_products_inventory': [
            {'field_name': 'nombre_producto', 'display_name': 'Nombre del Producto', 'description': 'Nombre completo del producto'},
            {'field_name': 'sku', 'display_name': 'SKU/Código', 'description': 'Código único del producto'},
            {'field_name': 'categoria', 'display_name': 'Categoría', 'description': 'Categoría del producto'},
            {'field_name': 'precio_venta', 'display_name': 'Precio de Venta', 'description': 'Precio de venta al público'},
            {'field_name': 'precio_costo', 'display_name': 'Precio de Costo', 'description': 'Precio de costo del producto'},
            {'field_name': 'stock_actual', 'display_name': 'Stock Actual', 'description': 'Cantidad disponible en inventario'},
            {'field_name': 'stock_minimo', 'display_name': 'Stock Mínimo', 'description': 'Cantidad mínima requerida'},
            {'field_name': 'ubicacion', 'display_name': 'Ubicación', 'description': 'Ubicación física del producto'},
            {'field_name': 'proveedor', 'display_name': 'Proveedor', 'description': 'Proveedor principal del producto'},
            {'field_name': 'estado', 'display_name': 'Estado', 'description': 'Estado del producto (activo, inactivo, descontinuado)'},
        ],
        
        'mixed_suppliers_products': [
            {'field_name': 'nombre_proveedor', 'display_name': 'Nombre del Proveedor', 'description': 'Razón social del proveedor'},
            {'field_name': 'ruc_proveedor', 'display_name': 'RUC del Proveedor', 'description': 'RUC del proveedor'},
            {'field_name': 'contacto', 'display_name': 'Contacto', 'description': 'Persona de contacto'},
            {'field_name': 'telefono', 'display_name': 'Teléfono', 'description': 'Número de teléfono'},
            {'field_name': 'email', 'display_name': 'Email', 'description': 'Correo electrónico'},
            {'field_name': 'producto_suministrado', 'display_name': 'Producto Suministrado', 'description': 'Producto que suministra este proveedor'},
            {'field_name': 'precio_proveedor', 'display_name': 'Precio del Proveedor', 'description': 'Precio que cobra el proveedor'},
            {'field_name': 'tiempo_entrega', 'display_name': 'Tiempo de Entrega', 'description': 'Días de entrega estimados'},
            {'field_name': 'condiciones_pago', 'display_name': 'Condiciones de Pago', 'description': 'Términs de pago acordados'},
        ]
    }
    
    for import_type, fields in mixed_fields.items():
        print(f"\n🔀 Creando campos para {import_type}...")
        
        for field_data in fields:
            field_def, created = FieldDefinition.objects.get_or_create(
                import_type=import_type,
                field_name=field_data['field_name'],
                defaults={
                    'display_name': field_data['display_name'],
                    'description': field_data['description'],
                    'is_required': False,
                    'field_type': 'text'
                }
            )
            
            if created:
                print(f"✅ Creado: {field_data['display_name']}")
            else:
                print(f"⚠️  Ya existe: {field_data['display_name']}")
        
        count = FieldDefinition.objects.filter(import_type=import_type).count()
        print(f"📊 Total campos {import_type}: {count}")

if __name__ == "__main__":
    create_mixed_fields()
    print("\n🎉 ¡Configuración de campos mixed completada!")
