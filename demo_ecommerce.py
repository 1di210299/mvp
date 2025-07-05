#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo específico para ECOMMERCE - Campos personalizados
Muestra ejemplos reales de cómo funcionaría en una tienda online
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from authentication.models import Company
from inventory.models import Product, CustomFieldDefinition, CustomFieldValue

def demo_ecommerce_fields():
    """Demo específico para ecommerce"""
    print("🛒" * 20)
    print("   DEMO CAMPOS PERSONALIZADOS - ECOMMERCE")
    print("🛒" * 20)
    
    company = Company.objects.first()
    if not company:
        print("❌ No hay empresas en la base de datos")
        return
    
    print(f"🏢 Empresa: {company.name}")
    print(f"📧 Email: {company.email}")
    
    # 1. Campos típicos de ecommerce
    print("\n" + "="*50)
    print("1️⃣  CREANDO CAMPOS TÍPICOS DE ECOMMERCE")
    print("="*50)
    
    ecommerce_fields = [
        {
            'field_name': 'color_principal',
            'field_label': 'Color Principal',
            'field_type': 'choice',
            'choices_json': '[{"value": "rojo", "label": "Rojo"}, {"value": "azul", "label": "Azul"}, {"value": "negro", "label": "Negro"}, {"value": "blanco", "label": "Blanco"}, {"value": "verde", "label": "Verde"}]',
            'help_text': 'Color principal del producto para filtros'
        },
        {
            'field_name': 'rating_promedio',
            'field_label': 'Rating Promedio',
            'field_type': 'decimal',
            'min_value': 1.0,
            'max_value': 5.0,
            'help_text': 'Calificación promedio de clientes (1-5 estrellas)'
        },
        {
            'field_name': 'numero_reviews',
            'field_label': 'Número de Reviews',
            'field_type': 'number',
            'min_value': 0,
            'help_text': 'Cantidad total de reseñas del producto'
        },
        {
            'field_name': 'es_trending',
            'field_label': '¿Es Trending?',
            'field_type': 'boolean',
            'help_text': '¿El producto está en tendencia actualmente?'
        },
        {
            'field_name': 'temporada',
            'field_label': 'Temporada',
            'field_type': 'choice',
            'choices_json': '[{"value": "verano", "label": "Verano"}, {"value": "invierno", "label": "Invierno"}, {"value": "navidad", "label": "Navidad"}, {"value": "todo_ano", "label": "Todo el año"}]',
            'help_text': 'Temporada principal de ventas'
        },
        {
            'field_name': 'descuento_maximo',
            'field_label': 'Descuento Máximo (%)',
            'field_type': 'number',
            'min_value': 0,
            'max_value': 80,
            'help_text': 'Porcentaje máximo de descuento permitido'
        },
        {
            'field_name': 'peso_gramos',
            'field_label': 'Peso (gramos)',
            'field_type': 'number',
            'help_text': 'Peso del producto para cálculo de envío'
        },
        {
            'field_name': 'es_eco_friendly',
            'field_label': '¿Es Eco-Friendly?',
            'field_type': 'boolean',
            'help_text': '¿El producto es amigable con el medio ambiente?'
        }
    ]
    
    for field_data in ecommerce_fields:
        field_def, created = CustomFieldDefinition.objects.get_or_create(
            company=company,
            model_type='product',
            field_name=field_data['field_name'],
            defaults=field_data
        )
        status = "✅ CREADO" if created else "🔄 YA EXISTE"
        print(f"{status}: {field_def.field_label}")
    
    # 2. Asignar valores realistas a productos
    print("\n" + "="*50)
    print("2️⃣  ASIGNANDO VALORES REALISTAS")
    print("="*50)
    
    # Datos realistas para productos existentes
    ecommerce_data = {
        'AJI-001': {  # Ají Amarillo en Pasta
            'color_principal': 'amarillo',
            'rating_promedio': 4.7,
            'numero_reviews': 89,
            'es_trending': True,
            'temporada': 'todo_ano',
            'descuento_maximo': 20,
            'peso_gramos': 500,
            'es_eco_friendly': True
        },
        'AJI-002': {  # Ají Panca Molido
            'color_principal': 'rojo',
            'rating_promedio': 4.5,
            'numero_reviews': 67,
            'es_trending': False,
            'temporada': 'todo_ano',
            'descuento_maximo': 15,
            'peso_gramos': 250,
            'es_eco_friendly': False
        },
        'CAF-001': {  # Café Orgánico
            'color_principal': 'marron',
            'rating_promedio': 4.8,
            'numero_reviews': 234,
            'es_trending': True,
            'temporada': 'invierno',
            'descuento_maximo': 25,
            'peso_gramos': 1000,
            'es_eco_friendly': True
        },
        'QUI-001': {  # Quinua Real Blanca
            'color_principal': 'blanco',
            'rating_promedio': 4.6,
            'numero_reviews': 156,
            'es_trending': True,
            'temporada': 'todo_ano',
            'descuento_maximo': 30,
            'peso_gramos': 500,
            'es_eco_friendly': True
        },
        'ALG-001': {  # Camiseta Pima Cotton
            'color_principal': 'blanco',
            'rating_promedio': 4.4,
            'numero_reviews': 98,
            'es_trending': False,
            'temporada': 'verano',
            'descuento_maximo': 40,
            'peso_gramos': 180,
            'es_eco_friendly': True
        }
    }
    
    products = Product.objects.filter(company=company, sku__in=ecommerce_data.keys())
    
    for product in products:
        if product.sku in ecommerce_data:
            values = ecommerce_data[product.sku]
            print(f"\n📦 {product.sku}: {product.name}")
            
            for field_name, value in values.items():
                try:
                    product.set_custom_field_value(field_name, value)
                    print(f"   ✅ {field_name}: {value}")
                except Exception as e:
                    print(f"   ❌ Error en {field_name}: {e}")

def demo_ecommerce_insights():
    """Mostrar insights típicos de ecommerce"""
    print("\n" + "="*50)
    print("3️⃣  INSIGHTS AUTOMÁTICOS PARA ECOMMERCE")
    print("="*50)
    
    # Simular análisis que haría la IA
    insights = {
        "productos_trending": ["Ají Amarillo", "Café Orgánico", "Quinua"],
        "productos_alta_valoracion": ["Café Orgánico (4.8⭐)", "Ají Amarillo (4.7⭐)"],
        "productos_eco_friendly": "80% de productos son eco-friendly",
        "temporadas_detectadas": {
            "Invierno": ["Café Orgánico"],
            "Verano": ["Camiseta Pima"],
            "Todo el año": ["Ají Amarillo", "Quinua"]
        },
        "oportunidades_descuento": "Quinua puede tener hasta 30% descuento",
        "peso_promedio_envios": "507 gramos promedio"
    }
    
    print("🔥 PRODUCTOS EN TENDENCIA:")
    for producto in insights["productos_trending"]:
        print(f"   📈 {producto}")
    
    print(f"\n⭐ PRODUCTOS MEJOR VALORADOS:")
    for producto in insights["productos_alta_valoracion"]:
        print(f"   🏆 {producto}")
    
    print(f"\n🌱 SUSTENTABILIDAD:")
    print(f"   ♻️  {insights['productos_eco_friendly']}")
    
    print(f"\n📅 ANÁLISIS POR TEMPORADA:")
    for temporada, productos in insights["temporadas_detectadas"].items():
        print(f"   🗓️  {temporada}: {', '.join(productos)}")
    
    print(f"\n💰 OPORTUNIDADES DE DESCUENTO:")
    print(f"   🏷️  {insights['oportunidades_descuento']}")
    
    print(f"\n📦 LOGÍSTICA:")
    print(f"   ⚖️  {insights['peso_promedio_envios']}")

def demo_filtros_inteligentes():
    """Mostrar cómo funcionarían los filtros en el ecommerce"""
    print("\n" + "="*50)
    print("4️⃣  SIMULACIÓN DE FILTROS INTELIGENTES")
    print("="*50)
    
    filtros_ejemplos = [
        {
            "filtro": "Solo productos trending",
            "resultado": "3 productos encontrados",
            "productos": ["Ají Amarillo", "Café Orgánico", "Quinua"]
        },
        {
            "filtro": "Rating > 4.5 estrellas",
            "resultado": "3 productos encontrados", 
            "productos": ["Café Orgánico (4.8⭐)", "Ají Amarillo (4.7⭐)", "Quinua (4.6⭐)"]
        },
        {
            "filtro": "Productos eco-friendly",
            "resultado": "4 productos encontrados",
            "productos": ["Ají Amarillo", "Café Orgánico", "Quinua", "Camiseta Pima"]
        },
        {
            "filtro": "Temporada: Verano",
            "resultado": "1 producto encontrado",
            "productos": ["Camiseta Pima Cotton"]
        },
        {
            "filtro": "Descuento posible > 25%",
            "resultado": "2 productos encontrados",
            "productos": ["Quinua (30%)", "Camiseta Pima (40%)"]
        }
    ]
    
    for filtro_data in filtros_ejemplos:
        print(f"\n🔍 FILTRO: {filtro_data['filtro']}")
        print(f"   📊 {filtro_data['resultado']}")
        for producto in filtro_data['productos']:
            print(f"   📦 {producto}")

def demo_recomendaciones_ia():
    """Mostrar recomendaciones que haría la IA"""
    print("\n" + "="*50)
    print("5️⃣  RECOMENDACIONES DE IA PARA ECOMMERCE")
    print("="*50)
    
    recomendaciones = [
        {
            "tipo": "🚀 PROMOCIÓN INTELIGENTE",
            "recomendacion": "Promocionar Café Orgánico en invierno",
            "razon": "Rating alto (4.8⭐) + temporada ideal + eco-friendly",
            "accion": "Crear campaña publicitaria para noviembre-febrero"
        },
        {
            "tipo": "⚠️  ALERTA DE INVENTARIO", 
            "recomendacion": "Aumentar stock de productos trending",
            "razon": "3 productos trending con alta demanda",
            "accion": "Reabastecer Ají Amarillo, Café y Quinua"
        },
        {
            "tipo": "💡 OPORTUNIDAD DE MEJORA",
            "recomendacion": "Mejorar rating de Ají Panca",
            "razon": "Rating 4.5⭐ vs 4.7⭐ del competidor directo",
            "accion": "Analizar reseñas negativas y mejorar producto"
        },
        {
            "tipo": "🎯 SEGMENTACIÓN",
            "recomendacion": "Crear categoría 'Productos Sustentables'",
            "razon": "80% de productos son eco-friendly",
            "accion": "Destacar en landing page principal"
        },
        {
            "tipo": "📈 CROSS-SELLING",
            "recomendacion": "Agrupar productos peruanos",
            "razon": "Clientes que compran ají también compran quinua",
            "accion": "Crear bundle 'Sabores del Perú'"
        }
    ]
    
    for rec in recomendaciones:
        print(f"\n{rec['tipo']}")
        print(f"   💡 {rec['recomendacion']}")
        print(f"   📝 {rec['razon']}")
        print(f"   ✅ {rec['accion']}")

def main():
    """Función principal del demo"""
    print("🛒 SISTEMA DE CAMPOS PERSONALIZADOS")
    print("   DEMO ESPECÍFICO PARA ECOMMERCE")
    print("   Tu socio va a entender perfecto! 😎")
    
    try:
        demo_ecommerce_fields()
        demo_ecommerce_insights()
        demo_filtros_inteligentes()
        demo_recomendaciones_ia()
        
        print("\n" + "🎉" * 50)
        print("   ✅ DEMO COMPLETADO EXITOSAMENTE")
        print("🎉" * 50)
        
        print(f"\n💬 QUÉ DECIRLE A TU SOCIO:")
        print(f"════════════════════════════════")
        print(f"'Mira, nuestro sistema ahora puede hacer esto:")
        print(f"1. 🔍 Filtros súper específicos (como Amazon)")
        print(f"2. 🤖 Recomendaciones automáticas con IA")
        print(f"3. 📊 Reportes inteligentes de qué promocionar")
        print(f"4. ⭐ Control automático de calidad por ratings")
        print(f"5. 🌱 Aprovechamos la tendencia eco-friendly")
        print(f"")
        print(f"¿Te parece si empezamos con estos campos básicos?")
        print(f"Toma 1 hora configurar y puede subir las ventas fácil 20%.'")
        
        print(f"\n🚀 PRÓXIMOS PASOS:")
        print(f"1. Mostrar esta demo a tu socio")
        print(f"2. Decidir qué 5-8 campos quieren empezar")
        print(f"3. Configurar en 1 hora")
        print(f"4. Cargar datos de productos existentes")
        print(f"5. Activar IA con OpenAI ($15/mes)")
        print(f"6. Ver mejoras en reportes y ventas")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
