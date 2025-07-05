#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de demostración para campos personalizados y análisis con IA
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from authentication.models import Company
from inventory.models import Product, CustomFieldDefinition, CustomFieldValue


def demo_custom_fields():
    """Demostración de campos personalizados"""
    print("=" * 60)
    print("DEMOSTRACIÓN DE CAMPOS PERSONALIZADOS")
    print("=" * 60)
    
    # Obtener empresa
    company = Company.objects.first()
    if not company:
        print("No hay empresas en la base de datos")
        return
    
    print(f"Trabajando con empresa: {company.name}")
    
    # 1. Crear campos personalizados para productos
    print("\n1. Creando campos personalizados para productos...")
    
    custom_fields_data = [
        {
            'field_name': 'origen_pais',
            'field_label': 'País de Origen',
            'field_type': 'choice',
            'choices_json': '[{"value": "peru", "label": "Perú"}, {"value": "ecuador", "label": "Ecuador"}, {"value": "colombia", "label": "Colombia"}]',
            'help_text': 'País donde se produce el producto'
        },
        {
            'field_name': 'certificacion_organica',
            'field_label': 'Certificación Orgánica',
            'field_type': 'boolean',
            'help_text': '¿El producto tiene certificación orgánica?'
        },
        {
            'field_name': 'nivel_picante',
            'field_label': 'Nivel de Picante (1-10)',
            'field_type': 'number',
            'min_value': 1,
            'max_value': 10,
            'help_text': 'Escala de picante del 1 al 10'
        },
        {
            'field_name': 'fecha_cosecha',
            'field_label': 'Fecha de Cosecha',
            'field_type': 'date',
            'help_text': 'Fecha de la última cosecha'
        },
        {
            'field_name': 'notas_calidad',
            'field_label': 'Notas de Calidad',
            'field_type': 'text',
            'max_length': 500,
            'help_text': 'Observaciones sobre la calidad del producto'
        }
    ]
    
    for field_data in custom_fields_data:
        field_def, created = CustomFieldDefinition.objects.get_or_create(
            company=company,
            model_type='product',
            field_name=field_data['field_name'],
            defaults={
                'field_label': field_data['field_label'],
                'field_type': field_data['field_type'],
                'help_text': field_data.get('help_text', ''),
                'choices_json': field_data.get('choices_json', ''),
                'min_value': field_data.get('min_value'),
                'max_value': field_data.get('max_value'),
                'max_length': field_data.get('max_length'),
            }
        )
        print(f"{'Creado' if created else 'Encontrado'}: {field_def.field_label}")
    
    # 2. Asignar valores a productos existentes
    print("\n2. Asignando valores a productos existentes...")
    
    products = Product.objects.filter(company=company)[:5]  # Primeros 5 productos
    
    sample_values = {
        'AJI-001': {
            'origen_pais': 'peru',
            'certificacion_organica': True,
            'nivel_picante': 8,
            'fecha_cosecha': '2024-12-15',
            'notas_calidad': 'Excelente calidad, color intenso, sabor característico'
        },
        'AJI-002': {
            'origen_pais': 'peru',
            'certificacion_organica': False,
            'nivel_picante': 6,
            'fecha_cosecha': '2024-11-20',
            'notas_calidad': 'Buena calidad, procesamiento estándar'
        },
        'CAF-001': {
            'origen_pais': 'peru',
            'certificacion_organica': True,
            'nivel_picante': 0,
            'fecha_cosecha': '2024-10-10',
            'notas_calidad': 'Café de altura, tueste medio, notas florales'
        },
        'QUI-001': {
            'origen_pais': 'peru',
            'certificacion_organica': True,
            'nivel_picante': 0,
            'fecha_cosecha': '2024-09-05',
            'notas_calidad': 'Quinua real de alta calidad, grano uniforme'
        },
        'MAC-001': {
            'origen_pais': 'peru',
            'certificacion_organica': True,
            'nivel_picante': 0,
            'fecha_cosecha': '2024-08-15',
            'notas_calidad': 'Maca gelatinizada premium, proceso controlado'
        }
    }
    
    for product in products:
        if product.sku in sample_values:
            values = sample_values[product.sku]
            print(f"\nAsignando valores a {product.sku}: {product.name}")
            
            for field_name, value in values.items():
                try:
                    product.set_custom_field_value(field_name, value)
                    print(f"  - {field_name}: {value}")
                except Exception as e:
                    print(f"  Error en {field_name}: {e}")
    
    # 3. Mostrar productos con campos personalizados
    print("\n3. Productos con campos personalizados:")
    print("-" * 40)
    
    for product in products[:3]:
        custom_values = product.get_custom_field_values()
        print(f"\n{product.sku}: {product.name}")
        print(f"Precio: S/ {product.cost_price} -> S/ {product.sale_price}")
        
        if custom_values:
            print("Campos personalizados:")
            for field_name, value in custom_values.items():
                # Obtener la definición del campo para mostrar la etiqueta
                try:
                    field_def = product.get_custom_fields().get(field_name=field_name)
                    print(f"  - {field_def.field_label}: {value}")
                except:
                    print(f"  - {field_name}: {value}")
        else:
            print("Sin campos personalizados asignados")


def demo_ai_suggestions():
    """Demostración de sugerencias de IA"""
    print("\n" + "=" * 60)
    print("DEMOSTRACIÓN DE SUGERENCIAS DE IA")
    print("=" * 60)
    
    # Simulación de respuesta de IA (sin usar API real)
    ai_suggestions = {
        "suggested_fields": [
            {
                "field_name": "sostenibilidad_score",
                "field_label": "Puntuación de Sostenibilidad",
                "field_type": "number",
                "justification": "Para productos peruanos es importante medir el impacto ambiental",
                "benefits": ["Cumplimiento con estándares internacionales", "Marketing diferenciado"]
            },
            {
                "field_name": "comunidad_origen",
                "field_label": "Comunidad de Origen",
                "field_type": "text",
                "justification": "Trazabilidad social importante para productos artesanales",
                "benefits": ["Historia del producto", "Comercio justo", "Responsabilidad social"]
            },
            {
                "field_name": "temporada_alta",
                "field_label": "Temporada Alta",
                "field_type": "choice",
                "choices": ["Verano", "Invierno", "Todo el año"],
                "justification": "Para optimizar gestión de inventario según estacionalidad",
                "benefits": ["Mejor planificación", "Reducción de mermas"]
            }
        ],
        "analysis": {
            "current_fields_assessment": "Los campos actuales cubren aspectos básicos de calidad y origen",
            "industry_best_practices": "Se recomienda agregar campos de sostenibilidad y trazabilidad social",
            "competitive_advantage": "Campos de certificación y origen pueden ser diferenciadores clave"
        }
    }
    
    print("Sugerencias de campos personalizados basadas en IA:")
    print("-" * 50)
    
    for suggestion in ai_suggestions["suggested_fields"]:
        print(f"\n📋 {suggestion['field_label']} ({suggestion['field_type']})")
        print(f"   Justificación: {suggestion['justification']}")
        print(f"   Beneficios: {', '.join(suggestion['benefits'])}")
    
    print(f"\n🎯 Análisis del sector:")
    print(f"   {ai_suggestions['analysis']['industry_best_practices']}")


def demo_analytics_insights():
    """Demostración de insights analíticos"""
    print("\n" + "=" * 60)
    print("DEMOSTRACIÓN DE INSIGHTS ANALÍTICOS")
    print("=" * 60)
    
    # Simulación de análisis (sin usar API real)
    analytics_insights = {
        "inventory_analysis": {
            "total_products": 15,
            "products_with_custom_fields": 5,
            "organic_products_percentage": 60,
            "average_spice_level": 3.2,
            "top_origin_country": "Perú"
        },
        "recommendations": [
            "Productos orgánicos tienen 15% mayor margen - considerar expandir línea orgánica",
            "Productos con nivel de picante 6-8 tienen mayor rotación",
            "Fecha de cosecha influye en calidad percibida - usar en marketing"
        ],
        "predictions": [
            "Demanda de productos orgánicos crecerá 25% próximo trimestre",
            "Productos de temporada alta en verano necesitan reabastecimiento",
            "Quinua y maca son productos estrella para exportación"
        ],
        "custom_fields_impact": {
            "most_valuable_field": "certificacion_organica",
            "correlation_with_sales": "Productos orgánicos venden 40% más",
            "data_completeness": "85% de productos tienen campos personalizados completos"
        }
    }
    
    print("📊 Análisis de inventario:")
    analysis = analytics_insights["inventory_analysis"]
    print(f"   • Total productos: {analysis['total_products']}")
    print(f"   • Con campos personalizados: {analysis['products_with_custom_fields']}")
    print(f"   • Productos orgánicos: {analysis['organic_products_percentage']}%")
    print(f"   • Nivel promedio picante: {analysis['average_spice_level']}")
    print(f"   • Principal país origen: {analysis['top_origin_country']}")
    
    print(f"\n💡 Recomendaciones:")
    for rec in analytics_insights["recommendations"]:
        print(f"   • {rec}")
    
    print(f"\n🔮 Predicciones:")
    for pred in analytics_insights["predictions"]:
        print(f"   • {pred}")
    
    print(f"\n📈 Impacto campos personalizados:")
    impact = analytics_insights["custom_fields_impact"]
    print(f"   • Campo más valioso: {impact['most_valuable_field']}")
    print(f"   • Correlación ventas: {impact['correlation_with_sales']}")
    print(f"   • Completitud datos: {impact['data_completeness']}")


def demo_use_cases():
    """Casos de uso específicos"""
    print("\n" + "=" * 60)
    print("CASOS DE USO ESPECÍFICOS")
    print("=" * 60)
    
    use_cases = [
        {
            "title": "📦 EMPRESAS DE EXPORTACIÓN",
            "custom_fields": [
                "certificacion_internacional", "puerto_embarque", "codigo_arancelario",
                "requisitos_fitosanitarios", "mercado_destino"
            ],
            "ai_benefits": [
                "Optimizar rutas de exportación",
                "Predecir demanda por mercado",
                "Alertas de certificaciones vencidas"
            ]
        },
        {
            "title": "🥘 RESTAURANTES Y FOOD SERVICE",
            "custom_fields": [
                "tiempo_preparacion", "alergenicos", "temporada_menu",
                "origen_chef", "maridaje_recomendado"
            ],
            "ai_benefits": [
                "Planificación de menús estacionales",
                "Gestión de alérgenos automática",
                "Sugerencias de maridajes"
            ]
        },
        {
            "title": "🏪 RETAIL Y SUPERMERCADOS",
            "custom_fields": [
                "categoria_gondola", "promocion_vigente", "rotacion_promedio",
                "margen_categoria", "proveedor_backup"
            ],
            "ai_benefits": [
                "Optimización de espacios en góndola",
                "Predicción de promociones efectivas",
                "Gestión automática de proveedores"
            ]
        },
        {
            "title": "🧬 LABORATORIOS Y FARMACIA",
            "custom_fields": [
                "principio_activo", "concentracion", "lote_fabricacion",
                "temperatura_almacenamiento", "interacciones_medicamentosas"
            ],
            "ai_benefits": [
                "Control automático de lotes",
                "Alertas de interacciones",
                "Gestión de temperatura"
            ]
        }
    ]
    
    for case in use_cases:
        print(f"\n{case['title']}")
        print("Campos personalizados recomendados:")
        for field in case['custom_fields']:
            print(f"   • {field}")
        print("Beneficios con IA:")
        for benefit in case['ai_benefits']:
            print(f"   ✓ {benefit}")


def main():
    """Función principal"""
    print("🚀 SISTEMA DE CAMPOS PERSONALIZADOS E IA")
    print("DataLens - Gestión Inteligente de Inventarios")
    
    try:
        demo_custom_fields()
        demo_ai_suggestions()
        demo_analytics_insights()
        demo_use_cases()
        
        print("\n" + "=" * 60)
        print("✅ DEMOSTRACIÓN COMPLETADA")
        print("=" * 60)
        print("\nResumen de funcionalidades implementadas:")
        print("1. ✅ Campos personalizados dinámicos por empresa")
        print("2. ✅ Integración con modelos existentes")
        print("3. ✅ API REST para gestión de campos")
        print("4. ✅ Análisis con IA (OpenAI)")
        print("5. ✅ Sugerencias inteligentes de campos")
        print("6. ✅ Reportes personalizados")
        print("7. ✅ Insights predictivos")
        
        print("\nPróximos pasos:")
        print("• Configurar OPENAI_API_KEY en variables de entorno")
        print("• Ejecutar migraciones: python manage.py migrate")
        print("• Probar API endpoints en /api/inventory/custom-fields/")
        print("• Integrar con frontend para UI de campos personalizados")
        
    except Exception as e:
        print(f"❌ Error en demostración: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
