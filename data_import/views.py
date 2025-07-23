from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid
from datetime import datetime
import openai
from django.conf import settings
import json
import re

from .models import DataImportSession, ColumnMapping, ImportTemplate, FieldDefinition, FIELD_DEFINITIONS
from .serializers import (
    DataImportSessionSerializer, ColumnMappingSerializer, ImportTemplateSerializer,
    FieldDefinitionSerializer, FileUploadSerializer, AnalyzeFileSerializer,
    ColumnMappingCreateSerializer, ProcessImportSerializer, ImportResultSerializer
)
from .services import FileAnalysisService, ColumnMappingService, DataImportService


class DataImportDetectionService:
    """Servicio para detección híbrida de tipos de datos"""
    
    @staticmethod
    def detect_by_patterns(filename, columns=None):
        """Detección por patrones (método original)"""
        print(f"🔍 BACKEND: Detección por patrones para archivo: {filename}")
        
        filename_lower = filename.lower()
        patterns = {
            'products': ['producto', 'catalogo', 'item', 'sku', 'articulo'],
            'sales': ['venta', 'factura', 'boleta', 'ticket', 'comprobante', 'transaccion'],
            'customers': ['cliente', 'customer', 'comprador', 'contacto'],
            'suppliers': ['proveedor', 'supplier', 'distribuidor', 'abastecedor'],
            'inventory': ['stock', 'inventario', 'almacen', 'existencia'],
            'purchases': ['compra', 'orden', 'pedido', 'adquisicion'],
            'leads': ['lead', 'prospecto', 'potencial', 'interesado'],
            'categories': ['categoria', 'tipo', 'clase', 'grupo']
        }
        
        detected_type = 'products'  # default
        confidence = 10
        reasons = []
        
        for data_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    detected_type = data_type
                    confidence = 75
                    reasons.append(f"Nombre de archivo contiene '{keyword}'")
                    break
        
        print(f"🔍 BACKEND: Patrones detectaron: {detected_type} ({confidence}%)")
        
        return {
            'detected_type': detected_type,
            'confidence': confidence,
            'reasons': reasons,
            'method': 'patterns'
        }
    
    @staticmethod
    def detect_by_openai(filename, columns=None, country_context='peru'):
        """Detección usando OpenAI API"""
        print(f"🧠 BACKEND: Detección OpenAI para archivo: {filename}, contexto: {country_context}")
        
        try:
            # Verificar si OpenAI está configurado
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                print(f"⚠️ BACKEND: OPENAI_API_KEY no configurado")
                return None
            
            client = openai.OpenAI(api_key=api_key)
            
            # Preparar el prompt con contexto peruano y detección de datos mezclados
            available_types = {
                'products': 'Productos/Catálogo (artículos, SKUs, inventario)',
                'sales': 'Ventas (facturas, boletas, comprobantes, transacciones)',
                'customers': 'Clientes (compradores, contactos, base de datos)',
                'suppliers': 'Proveedores (distribuidores, abastecedores)',
                'inventory': 'Inventario (stock, almacén, existencias)',
                'purchases': 'Compras (órdenes, pedidos, adquisiciones)',
                'leads': 'Leads (prospectos, potenciales clientes)',
                'categories': 'Categorías (tipos, clases, grupos de productos)',
                'mixed_products_inventory': 'Productos + Inventario (catálogo con stock por ubicación)',
                'mixed_sales_products': 'Ventas + Productos (transacciones con detalles de productos)',
                'mixed_suppliers_products': 'Proveedores + Productos (proveedores con sus productos)'
            }
            
            columns_info = ""
            if columns and len(columns) > 0:
                columns_sample = columns[:15]  # Primeras 15 columnas
                columns_info = f"\nColumnas detectadas: {', '.join(columns_sample)}"
                if len(columns) > 15:
                    columns_info += f"... y {len(columns) - 15} columnas más"
            
            prompt = f"""Eres un experto en datos empresariales peruanos especializado en detectar tipos de datos MEZCLADOS.
            
Analiza el siguiente archivo y determina si contiene un solo tipo de datos o DATOS MEZCLADOS:

Archivo: "{filename}"{columns_info}

⚠️ IMPORTANTE: Muchas PYMEs peruanas tienen archivos Excel con DATOS MEZCLADOS. Por ejemplo:
- Un catálogo de productos QUE TAMBIÉN incluye stock por ubicación
- Facturas QUE TAMBIÉN incluyen detalles completos del producto
- Lista de proveedores QUE TAMBIÉN incluye los productos que suministran

Tipos disponibles (incluye tipos mezclados):
{json.dumps(available_types, indent=2, ensure_ascii=False)}

Analiza las columnas y determina:
1. ¿Es un tipo puro o mezclado?
2. Si es mezclado, ¿cuáles tipos están combinados?
3. ¿Cuál es el tipo PRINCIPAL (más columnas dedicadas)?

Responde SOLO con un JSON válido:
{{
    "detected_type": "tipo_principal_o_mezclado",
    "confidence": numero_del_1_al_100,
    "reasoning": "explicación_breve_en_español",
    "is_mixed": true/false,
    "secondary_types": ["tipo2", "tipo3"] (si es mezclado),
    "peru_context": "cómo_el_contexto_peruano_influye",
    "primary_columns": ["col1", "col2"] (columnas del tipo principal),
    "secondary_columns": ["col3", "col4"] (columnas de tipos secundarios)
}}

Considera terminología específica peruana como "boleta", "factura", "RUC", "DNI", etc."""

            print(f"🧠 BACKEND: Enviando prompt a OpenAI para detección de datos mezclados...")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un analista de datos experto en el mercado peruano, especializado en detectar archivos con datos mezclados comunes en PYMEs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            # Parsear respuesta
            content = response.choices[0].message.content.strip()
            print(f"🧠 BACKEND: Respuesta OpenAI: {content}")
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                print(f"🧠 BACKEND: OpenAI detectó: {result.get('detected_type')} ({result.get('confidence')}%)")
                if result.get('is_mixed'):
                    print(f"🔀 BACKEND: Datos mezclados detectados: {result.get('secondary_types')}")
                
                return {
                    'detected_type': result.get('detected_type', 'products'),
                    'confidence': min(max(result.get('confidence', 50), 0), 100),
                    'reasons': [result.get('reasoning', 'Análisis OpenAI')],
                    'peru_context': result.get('peru_context', ''),
                    'is_mixed': result.get('is_mixed', False),
                    'secondary_types': result.get('secondary_types', []),
                    'primary_columns': result.get('primary_columns', []),
                    'secondary_columns': result.get('secondary_columns', []),
                    'method': 'openai'
                }
            else:
                print(f"⚠️ BACKEND: No se pudo parsear JSON de OpenAI")
                return None
                
        except Exception as e:
            print(f"❌ BACKEND: Error en OpenAI: {str(e)}")
            return None
    
    @staticmethod
    def auto_create_fields_for_new_type(import_type, detected_columns=None, mixed_context=None):
        """Crear automáticamente campos para nuevos tipos detectados por IA"""
        print(f"🆕 BACKEND: Creando campos automáticamente para nuevo tipo: {import_type}")
        
        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                print(f"⚠️ BACKEND: OPENAI_API_KEY no configurado")
                return False
            
            client = openai.OpenAI(api_key=api_key)
            
            # Preparar contexto para generar campos
            columns_info = f"Columnas detectadas: {detected_columns}" if detected_columns else ""
            mixed_info = f"\nContexto mezclado: {mixed_context}" if mixed_context else ""
            
            prompt = f"""Eres un experto en sistemas de gestión empresarial peruanos.

Se ha detectado un nuevo tipo de datos mezclados: "{import_type}"
{columns_info}{mixed_info}

Necesito que generes automáticamente una lista de campos apropiados para este tipo de datos.

⚠️ IMPORTANTE: Este es un archivo con DATOS MEZCLADOS común en PYMEs peruanas.
Considera terminología local: RUC, DNI, IGV, boleta, factura, etc.

Basándote en el tipo "{import_type}" y las columnas detectadas, genera entre 8-15 campos relevantes.

Responde SOLO con JSON válido:
{{
    "fields": [
        {{
            "field_name": "nombre_campo_en_minuscula",
            "display_name": "Nombre Legible del Campo", 
            "description": "Descripción clara y específica para empresas peruanas",
            "is_required": true/false,
            "field_type": "text/number/date/boolean"
        }}
    ]
}}

Ejemplo de good field_names: cliente, fecha_venta, ruc_proveedor, precio_unitario, stock_actual"""

            print(f"🤖 BACKEND: Enviando prompt para auto-crear campos...")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un consultor experto en sistemas ERP para PYMEs peruanas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            print(f"🤖 BACKEND: Respuesta IA para campos: {content}")
            
            # Parsear respuesta JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                fields_data = result.get('fields', [])
                
                created_count = 0
                for field_data in fields_data:
                    field_def, created = FieldDefinition.objects.get_or_create(
                        import_type=import_type,
                        field_name=field_data['field_name'],
                        defaults={
                            'display_name': field_data['display_name'],
                            'description': field_data['description'],
                            'is_required': field_data.get('is_required', False),
                            'field_type': field_data.get('field_type', 'text'),
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
                
                print(f"✅ BACKEND: Auto-creados {created_count} campos para {import_type}")
                return True
            else:
                print(f"❌ BACKEND: No se pudo parsear JSON para auto-creación")
                return False
                
        except Exception as e:
            print(f"❌ BACKEND: Error auto-creando campos: {str(e)}")
            return False

    @staticmethod
    def generate_field_descriptions(import_type, detected_columns=None, mixed_context=None):
        """Generar descripciones inteligentes para campos usando OpenAI"""
        print(f"📝 BACKEND: Generando descripciones IA para tipo: {import_type}")
        
        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                print(f"⚠️ BACKEND: OPENAI_API_KEY no configurado para descripciones")
                return {}
            
            client = openai.OpenAI(api_key=api_key)
            
            # Obtener campos disponibles de la base de datos
            field_definitions = FieldDefinition.objects.filter(
                import_type=import_type,
                is_active=True
            ).order_by('order', 'display_name')
            
            # 🆕 Si no hay campos, intentar crearlos automáticamente
            if not field_definitions.exists():
                print(f"🔍 BACKEND: No hay campos para {import_type}, intentando auto-crear...")
                auto_created = DataImportDetectionService.auto_create_fields_for_new_type(
                    import_type, detected_columns, mixed_context
                )
                if auto_created:
                    # Recargar campos después de la auto-creación
                    field_definitions = FieldDefinition.objects.filter(
                        import_type=import_type,
                        is_active=True
                    ).order_by('order', 'display_name')
                    print(f"🎉 BACKEND: Campos auto-creados, recargando...")
            
            available_fields = []
            field_names = []
            for field_def in field_definitions:
                available_fields.append({
                    'field_name': field_def.field_name,
                    'display_name': field_def.display_name,
                    'description': field_def.description
                })
                field_names.append(field_def.field_name)
            
            print(f"📊 BACKEND: Generando descripciones para {len(field_names)} campos de BD")
            
            # Preparar contexto para OpenAI
            detected_info = f"Columnas detectadas en archivo: {detected_columns}" if detected_columns else ""
            mixed_info = f"\n🔀 CONTEXTO MEZCLADO: {mixed_context}" if mixed_context else ""
            
            prompt = f"""Eres un experto en sistemas de gestión empresarial para empresas peruanas especializado en archivos con DATOS MEZCLADOS.

Genera descripciones claras y útiles para los siguientes campos de importación de datos tipo "{import_type}":

Campos disponibles en el sistema: {field_names}
{detected_info}{mixed_info}

⚠️ IMPORTANTE: Este archivo puede contener DATOS MEZCLADOS (común en PYMEs peruanas).
Por ejemplo: Un catálogo de productos que TAMBIÉN incluye stock, ubicaciones, proveedores, etc.

Contexto: Empresa peruana, terminología local (RUC, DNI, IGV, etc.)

Para cada campo, genera:
1. Una descripción clara de QUÉ debe contener
2. Un ejemplo específico para empresas peruanas
3. Si es obligatorio o opcional
4. Consejos para datos mezclados si aplica

Formato de respuesta JSON:
{{
    "field_name": {{
        "description": "Descripción clara del campo",
        "example": "Ejemplo específico peruano",
        "is_required": true/false,
        "tips": "Consejos adicionales para datos mezclados"
    }}
}}

Responde SOLO con JSON válido para TODOS los campos listados."""

            print(f"📝 BACKEND: Enviando prompt de descripciones a OpenAI...")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un consultor experto en sistemas de gestión para empresas peruanas, especializado en archivos con datos mezclados."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1800
            )
            
            content = response.choices[0].message.content.strip()
            print(f"📝 BACKEND: Respuesta descripciones OpenAI recibida")
            
            # Parsear JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                descriptions = json.loads(json_match.group())
                print(f"✅ BACKEND: {len(descriptions)} descripciones generadas")
                return descriptions
            else:
                print(f"⚠️ BACKEND: No se pudo parsear JSON de descripciones")
                return {}
                
        except Exception as e:
            print(f"❌ BACKEND: Error generando descripciones: {str(e)}")
            return {}
            
            prompt = f"""Eres un experto en sistemas de gestión empresarial para empresas peruanas.

Genera descripciones claras y útiles para los siguientes campos de importación de datos tipo "{import_type}":

Campos disponibles en el sistema: {field_names}
{detected_info}

Contexto: Empresa peruana, terminología local (RUC, DNI, IGV, etc.)

Para cada campo, genera:
1. Una descripción clara de QUÉ debe contener
2. Un ejemplo específico para empresas peruanas
3. Si es obligatorio o opcional

Formato de respuesta JSON:
{{
    "field_name": {{
        "description": "Descripción clara del campo",
        "example": "Ejemplo específico peruano",
        "is_required": true/false,
        "tips": "Consejos adicionales"
    }}
}}

Responde SOLO con JSON válido para TODOS los campos listados."""

            print(f"📝 BACKEND: Enviando prompt de descripciones a OpenAI...")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un consultor experto en sistemas de gestión para empresas peruanas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            print(f"📝 BACKEND: Respuesta descripciones OpenAI recibida")
            
            # Parsear JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                descriptions = json.loads(json_match.group())
                print(f"✅ BACKEND: {len(descriptions)} descripciones generadas")
                return descriptions
            else:
                print(f"⚠️ BACKEND: No se pudo parsear JSON de descripciones")
                return {}
                
        except Exception as e:
            print(f"❌ BACKEND: Error generando descripciones: {str(e)}")
            return {}
    
    @staticmethod
    def enhance_field_definitions(import_type, detected_columns=None, detection_result=None):
        """Mejorar definiciones de campos con IA, incluyendo manejo de datos mezclados y creación dinámica"""
        print(f"⚡ BACKEND: Mejorando definiciones de campos con IA para: {import_type}")
        
        # Determinar si tenemos datos mezclados
        is_mixed = detection_result and detection_result.get('is_mixed', False)
        secondary_types = detection_result.get('secondary_types', []) if detection_result else []
        
        if is_mixed:
            print(f"🔀 BACKEND: Datos mezclados detectados. Tipos secundarios: {secondary_types}")
        
        # Obtener campos del tipo principal
        primary_fields = FieldDefinition.objects.filter(
            import_type=import_type,
            is_active=True
        ).order_by('order', 'display_name')
        
        print(f"📊 BACKEND: Encontrados {primary_fields.count()} campos primarios en BD para {import_type}")
        
        # 🚀 SISTEMA DINÁMICO: Si no hay campos, crearlos automáticamente
        if primary_fields.count() == 0 and detected_columns:
            print(f"🔧 BACKEND: No hay campos predefinidos. Creando campos dinámicos...")
            
            # Crear campos dinámicamente
            dynamic_result = DataImportDetectionService.create_dynamic_fields_if_needed(
                import_type, detected_columns
            )
            
            if dynamic_result.get('created'):
                print(f"✅ BACKEND: Creados {dynamic_result['created_count']} campos dinámicos")
                
                # Mejorar con IA
                ai_result = DataImportDetectionService.enhance_dynamic_fields_with_ai(
                    import_type, detected_columns
                )
                
                if ai_result.get('enhanced'):
                    print(f"🧠 BACKEND: Mejorados {ai_result['updated_count']} campos con IA")
                
                # Recargar campos después de la creación
                primary_fields = FieldDefinition.objects.filter(
                    import_type=import_type,
                    is_active=True
                ).order_by('order', 'display_name')
                
                print(f"📊 BACKEND: Recargados {primary_fields.count()} campos dinámicos")
            else:
                print(f"⚠️ BACKEND: No se pudieron crear campos dinámicos: {dynamic_result.get('reason', 'Unknown')}")
        
        print(f"📊 BACKEND: Procesando {primary_fields.count()} campos finales")
        
        # Si hay datos mezclados, obtener campos de tipos secundarios también
        all_field_definitions = list(primary_fields)
        
        if is_mixed and secondary_types:
            for secondary_type in secondary_types:
                # Mapear tipos mezclados a tipos base
                base_type = secondary_type
                if secondary_type.startswith('mixed_'):
                    # Extraer tipos base: mixed_products_inventory -> [products, inventory]
                    base_types = secondary_type.replace('mixed_', '').split('_')
                    for bt in base_types:
                        if bt != import_type:  # Evitar duplicados del tipo principal
                            secondary_fields = FieldDefinition.objects.filter(
                                import_type=bt,
                                is_active=True
                            ).order_by('order', 'display_name')
                            all_field_definitions.extend(list(secondary_fields))
                            print(f"➕ BACKEND: Agregados {secondary_fields.count()} campos de {bt}")
                else:
                    if base_type != import_type:  # Evitar duplicados del tipo principal
                        secondary_fields = FieldDefinition.objects.filter(
                            import_type=base_type,
                            is_active=True
                        ).order_by('order', 'display_name')
                        all_field_definitions.extend(list(secondary_fields))
                        print(f"➕ BACKEND: Agregados {secondary_fields.count()} campos de {base_type}")
        
        # Eliminar duplicados manteniendo orden
        seen_fields = set()
        unique_field_definitions = []
        for field_def in all_field_definitions:
            field_key = f"{field_def.field_name}_{field_def.import_type}"
            if field_key not in seen_fields:
                seen_fields.add(field_key)
                unique_field_definitions.append(field_def)
        
        print(f"📊 BACKEND: Total campos únicos (después de mezclar): {len(unique_field_definitions)}")
        
        # Convertir a formato esperado por el frontend
        base_fields = []
        for field_def in unique_field_definitions:
            field_data = {
                'field_name': field_def.field_name,
                'display_name': field_def.display_name,
                'field_type': field_def.field_type,
                'description': field_def.description,
                'is_required': field_def.is_required,
                'is_unique': field_def.is_unique,
                'default_value': field_def.default_value,
                'related_model': field_def.related_model,
                'lookup_field': field_def.lookup_field,
                'choices': field_def.choices,
                'min_length': field_def.min_length,
                'max_length': field_def.max_length,
                'min_value': float(field_def.min_value) if field_def.min_value else None,
                'max_value': float(field_def.max_value) if field_def.max_value else None,
                'regex_pattern': field_def.regex_pattern,
                'order': field_def.order,
                'source_type': field_def.import_type,  # Indicar de qué tipo viene este campo
                'is_secondary': field_def.import_type != import_type  # Marcar si es campo secundario
            }
            
            # Agregar etiqueta visual para campos mezclados
            if field_data['is_secondary']:
                field_data['display_name'] = f"[{field_def.import_type.title()}] {field_def.display_name}"
            
            base_fields.append(field_data)
        
        # Generar descripciones con IA (incluyendo contexto de datos mezclados)
        ai_context = f"Datos mezclados detectados: {secondary_types}" if is_mixed else None
        ai_descriptions = DataImportDetectionService.generate_field_descriptions(
            import_type, detected_columns, ai_context
        )
        
        # Combinar definiciones base con descripciones IA
        enhanced_fields = []
        for field in base_fields:
            field_name = field['field_name']
            enhanced_field = field.copy()
            
            # Si hay descripción IA, usarla
            if field_name in ai_descriptions:
                ai_desc = ai_descriptions[field_name]
                enhanced_field['ai_description'] = ai_desc.get('description', field.get('description', ''))
                enhanced_field['ai_example'] = ai_desc.get('example', '')
                enhanced_field['ai_tips'] = ai_desc.get('tips', '')
                
                # Usar descripción IA como principal
                enhanced_field['description'] = ai_desc.get('description', field.get('description', ''))
            
            enhanced_fields.append(enhanced_field)
        
        print(f"✅ BACKEND: {len(enhanced_fields)} campos mejorados con IA (mezclados: {is_mixed})")
        return enhanced_fields
    
    @staticmethod
    def combine_detections(pattern_result, openai_result):
        """Combinar resultados de patrones y OpenAI"""
        print(f"⚡ BACKEND: Combinando detecciones...")
        
        if not openai_result:
            print(f"⚡ BACKEND: Solo usando patrones")
            return pattern_result
        
        if not pattern_result:
            print(f"⚡ BACKEND: Solo usando OpenAI")
            return openai_result
        
        # Ambos métodos están disponibles
        pattern_type = pattern_result['detected_type']
        openai_type = openai_result['detected_type']
        pattern_conf = pattern_result['confidence']
        openai_conf = openai_result['confidence']
        
        print(f"⚡ BACKEND: Patrones: {pattern_type} ({pattern_conf}%)")
        print(f"⚡ BACKEND: OpenAI: {openai_type} ({openai_conf}%)")
        
        # Si ambos coinciden, aumentar confianza
        if pattern_type == openai_type:
            final_confidence = min(95, (pattern_conf + openai_conf) // 2 + 20)
            reasons = pattern_result['reasons'] + openai_result['reasons']
            reasons.append(f"Ambos métodos coinciden en {pattern_type}")
            
            print(f"✅ BACKEND: Coincidencia total: {pattern_type} ({final_confidence}%)")
            
            return {
                'detected_type': pattern_type,
                'confidence': final_confidence,
                'reasons': reasons,
                'pattern_detection': pattern_result,
                'openai_detection': openai_result,
                'method': 'hybrid_match'
            }
        
        # Si no coinciden, usar el de mayor confianza
        if openai_conf > pattern_conf:
            final_result = openai_result.copy()
            final_result['pattern_detection'] = pattern_result
            final_result['openai_detection'] = openai_result
            final_result['method'] = 'hybrid_openai_wins'
            reasons = openai_result['reasons'] + [f"OpenAI ({openai_conf}%) vs Patrones ({pattern_conf}%)"]
            final_result['reasons'] = reasons
            print(f"🧠 BACKEND: OpenAI gana: {openai_type} ({openai_conf}%)")
        else:
            final_result = pattern_result.copy()
            final_result['pattern_detection'] = pattern_result
            final_result['openai_detection'] = openai_result
            final_result['method'] = 'hybrid_patterns_wins'
            reasons = pattern_result['reasons'] + [f"Patrones ({pattern_conf}%) vs OpenAI ({openai_conf}%)"]
            final_result['reasons'] = reasons
            print(f"🔍 BACKEND: Patrones ganan: {pattern_type} ({pattern_conf}%)")
        
        return final_result

    @staticmethod
    def create_dynamic_fields_if_needed(import_type, detected_columns=None):
        """Crear campos dinámicamente para nuevas casuísticas"""
        print(f"🚀 BACKEND: Creando campos dinámicos para tipo: {import_type}")
        
        # Verificar si ya existen campos para este tipo
        existing_count = FieldDefinition.objects.filter(import_type=import_type).count()
        if existing_count > 0:
            print(f"✅ BACKEND: Ya existen {existing_count} campos para {import_type}")
            return {'created': False, 'existing_count': existing_count}
        
        # Crear campos basándose en las columnas detectadas
        if not detected_columns:
            print(f"❌ BACKEND: No hay columnas detectadas para crear campos")
            return {'created': False, 'reason': 'No columns provided'}
        
        print(f"🔧 BACKEND: Creando campos para columnas: {detected_columns}")
        
        created_fields = []
        for i, column_name in enumerate(detected_columns):
            # Normalizar nombre del campo
            field_name = re.sub(r'[^a-z0-9_]', '_', column_name.lower().strip())
            field_name = re.sub(r'_+', '_', field_name).strip('_')
            
            # Crear display_name limpio
            display_name = column_name.strip()
            
            # Generar description básica
            description = f"Campo {display_name} detectado automáticamente en archivo Excel"
            
            # Crear el campo
            field_def, created = FieldDefinition.objects.get_or_create(
                import_type=import_type,
                field_name=field_name,
                defaults={
                    'display_name': display_name,
                    'description': description,
                    'is_required': False,
                    'field_type': 'text',
                    'order': i + 1,
                    'is_active': True
                }
            )
            
            if created:
                created_fields.append(field_def)
                print(f"✅ BACKEND: Creado campo dinámico: {display_name}")
            else:
                print(f"⚠️ BACKEND: Campo ya existía: {display_name}")
        
        print(f"🎉 BACKEND: Creados {len(created_fields)} campos dinámicos para {import_type}")
        return {
            'created': True,
            'created_count': len(created_fields),
            'total_fields': len(detected_columns)
        }

    @staticmethod
    def enhance_dynamic_fields_with_ai(import_type, detected_columns):
        """Mejorar campos dinámicos con descripciones de IA"""
        print(f"🧠 BACKEND: Mejorando campos dinámicos con IA para: {import_type}")
        
        try:
            # Configurar OpenAI
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Generar contexto para el tipo mezclado
            mixed_context = ""
            if import_type.startswith('mixed_'):
                types_in_mix = import_type.replace('mixed_', '').split('_')
                mixed_context = f"DATOS MEZCLADOS que combinan: {', '.join(types_in_mix)}"
            
            prompt = f"""Eres un experto en sistemas de gestión empresarial para empresas peruanas.

Acabamos de detectar un nuevo tipo de archivo Excel: "{import_type}"
{mixed_context}

Columnas detectadas en el archivo: {detected_columns}

Para cada columna, genera una descripción inteligente que ayude al usuario peruano a entender:
1. Qué tipo de datos debe contener esta columna
2. Un ejemplo específico para empresas peruanas
3. Si es un campo típicamente obligatorio u opcional
4. Consejos específicos para datos mezclados si aplica

Responde SOLO con JSON en este formato:
{{
    "column_name": {{
        "description": "Descripción clara y específica",
        "example": "Ejemplo peruano concreto",
        "is_required": true/false,
        "tips": "Consejos adicionales si aplica"
    }}
}}

Considera terminología peruana: RUC, DNI, IGV, soles (S/), etc."""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un consultor experto en sistemas ERP para PYMEs peruanas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parsear respuesta
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                ai_descriptions = json.loads(json_match.group())
                
                # Actualizar campos existentes con descripciones IA
                updated_count = 0
                for column_name, ai_info in ai_descriptions.items():
                    field_name = re.sub(r'[^a-z0-9_]', '_', column_name.lower().strip())
                    field_name = re.sub(r'_+', '_', field_name).strip('_')
                    
                    try:
                        field_def = FieldDefinition.objects.get(
                            import_type=import_type,
                            field_name=field_name
                        )
                        
                        field_def.description = ai_info.get('description', field_def.description)
                        field_def.is_required = ai_info.get('is_required', False)
                        field_def.save()
                        
                        updated_count += 1
                        print(f"✅ BACKEND: Actualizado con IA: {field_def.display_name}")
                        
                    except FieldDefinition.DoesNotExist:
                        print(f"⚠️ BACKEND: Campo no encontrado para actualizar: {field_name}")
                
                print(f"🎉 BACKEND: {updated_count} campos mejorados con IA")
                return {'enhanced': True, 'updated_count': updated_count}
            
        except Exception as e:
            print(f"❌ BACKEND: Error mejorando campos con IA: {str(e)}")
        
        return {'enhanced': False, 'reason': 'AI enhancement failed'}


class DataImportViewSet(viewsets.ModelViewSet):
    """ViewSet para manejo de sesiones de importación"""
    serializer_class = DataImportSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DataImportSession.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            user=self.request.user
        )
    
    @action(detail=False, methods=['post'])
    def upload_file(self, request):
        """Subir archivo y crear sesión de importación"""
        print(f"🔄 BACKEND: Recibida request de upload_file")
        print(f"📁 BACKEND: Files en request:", list(request.FILES.keys()))
        print(f"📋 BACKEND: Data en request:", request.data.keys())
        print(f"👤 BACKEND: Usuario:", request.user.email if hasattr(request.user, 'email') else request.user)
        print(f"🏢 BACKEND: Company:", getattr(request.user, 'company', 'No company'))
        
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            print(f"✅ BACKEND: Serializer válido")
            file = serializer.validated_data['file']
            import_type = serializer.validated_data['import_type']
            header_row = serializer.validated_data['header_row']
            
            print(f"📁 BACKEND: Archivo recibido - Nombre: {file.name}, Tamaño: {file.size}")
            print(f"📋 BACKEND: Tipo de importación: {import_type}")
            print(f"📄 BACKEND: Header row: {header_row}")
            
            try:
                # Generar nombre único para el archivo
                file_extension = os.path.splitext(file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                
                # Guardar archivo
                file_path = default_storage.save(
                    f"imports/{unique_filename}",
                    ContentFile(file.read())
                )
                
                # Crear sesión de importación
                print(f"💾 BACKEND: Creando sesión de importación...")
                session = DataImportSession.objects.create(
                    company=request.user.company,
                    user=request.user,
                    import_type=import_type,
                    original_filename=file.name,
                    file_path=default_storage.path(file_path),
                    file_size=file.size,
                    header_row=header_row,
                    status='pending'
                )
                
                print(f"✅ BACKEND: Sesión creada exitosamente - ID: {session.id}")
                
                return Response({
                    'session_id': session.id,
                    'message': 'Archivo subido exitosamente',
                    'next_step': 'analyze_file'
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                print(f"❌ BACKEND: Error procesando archivo: {str(e)}")
                import traceback
                print(f"❌ BACKEND: Traceback: {traceback.format_exc()}")
                return Response({
                    'error': f'Error al procesar archivo: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"❌ BACKEND: Serializer inválido - Errores: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def detect_type(self, request):
        """Detectar automáticamente el tipo de datos del archivo usando sistema híbrido"""
        print(f"🤖🇵🇪 BACKEND: Recibida request de detect_type híbrido")
        
        if 'file' not in request.FILES:
            return Response({
                'error': 'No se proporcionó archivo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        use_openai = request.data.get('use_openai', 'false').lower() == 'true'
        country_context = request.data.get('country_context', 'peru')
        
        print(f"🤖 BACKEND: Analizando archivo: {file.name}")
        print(f"🧠 BACKEND: Usar OpenAI: {use_openai}")
        print(f"🇵🇪 BACKEND: Contexto país: {country_context}")
        
        try:
            # 1. Detección por patrones (siempre)
            pattern_result = DataImportDetectionService.detect_by_patterns(file.name)
            
            # 2. Detección por OpenAI (si está habilitado)
            openai_result = None
            if use_openai:
                print(f"🧠 BACKEND: Iniciando detección OpenAI...")
                try:
                    # Intentar leer algunas líneas del archivo para obtener columnas
                    file.seek(0)  # Resetear puntero
                    sample_content = file.read(1024).decode('utf-8', errors='ignore')
                    file.seek(0)  # Resetear para futuro uso
                    
                    # Extraer posibles columnas de la primera línea
                    first_lines = sample_content.split('\n')[:3]
                    columns = []
                    if first_lines:
                        # Intentar separar por comas o puntos y coma
                        header_line = first_lines[0]
                        if ',' in header_line:
                            columns = [col.strip() for col in header_line.split(',')]
                        elif ';' in header_line:
                            columns = [col.strip() for col in header_line.split(';')]
                        elif '\t' in header_line:
                            columns = [col.strip() for col in header_line.split('\t')]
                    
                    print(f"🧠 BACKEND: Columnas extraídas para OpenAI: {columns[:10]}...")
                    
                    openai_result = DataImportDetectionService.detect_by_openai(
                        file.name, columns, country_context
                    )
                    
                    if openai_result:
                        print(f"✅ BACKEND: OpenAI detectó: {openai_result['detected_type']}")
                    else:
                        print(f"⚠️ BACKEND: OpenAI no pudo detectar")
                        
                except Exception as e:
                    print(f"❌ BACKEND: Error en OpenAI: {str(e)}")
                    openai_result = None
            
            # 3. Combinar resultados
            final_result = DataImportDetectionService.combine_detections(pattern_result, openai_result)
            
            # Labels más amigables
            type_labels = {
                'products': 'Productos',
                'sales': 'Ventas', 
                'customers': 'Clientes',
                'suppliers': 'Proveedores',
                'inventory': 'Inventario',
                'purchases': 'Compras',
                'leads': 'Leads/Prospectos',
                'categories': 'Categorías'
            }
            
            print(f"🎯 BACKEND: Resultado final: {final_result['detected_type']} ({final_result['confidence']}%)")
            
            response_data = {
                'detected_type': final_result['detected_type'],
                'detected_type_label': type_labels.get(final_result['detected_type'], final_result['detected_type']),
                'confidence': final_result['confidence'],
                'reasons': final_result['reasons'],
                'method': final_result.get('method', 'patterns'),
                'country_context': country_context
            }
            
            # Agregar detalles de ambos métodos si están disponibles
            if 'pattern_detection' in final_result:
                response_data['pattern_detection'] = final_result['pattern_detection']
            if 'openai_detection' in final_result:
                response_data['openai_detection'] = final_result['openai_detection']
            
            # Agregar información de datos mezclados
            if final_result.get('is_mixed'):
                response_data['is_mixed'] = True
                response_data['secondary_types'] = final_result.get('secondary_types', [])
                response_data['primary_columns'] = final_result.get('primary_columns', [])
                response_data['secondary_columns'] = final_result.get('secondary_columns', [])
                response_data['mixed_info'] = f"Archivo contiene datos mezclados: {', '.join(final_result.get('secondary_types', []))}"
            
            return Response(response_data)
            
        except Exception as e:
            print(f"❌ BACKEND: Error en detección automática: {str(e)}")
            return Response({
                'error': f'Error al detectar tipo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def analyze_file(self, request, pk=None):
        """Analizar archivo y detectar columnas con descripciones IA"""
        print(f"🔍 BACKEND: Recibida request de analyze_file para session {pk}")
        try:
            session = self.get_object()
            print(f"📋 BACKEND: Sesión encontrada - Status: {session.status}, File: {session.original_filename}")
            
            if session.status != 'pending':
                print(f"❌ BACKEND: Estado de sesión inválido: {session.status}")
                return Response({
                    'error': 'La sesión no está en estado pendiente'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"🔍 BACKEND: Iniciando análisis del archivo: {session.file_path}")
            # Analizar archivo
            analysis = FileAnalysisService.analyze_file(
                session.file_path,
                session.header_row
            )
            
            # Actualizar sesión con información detectada
            session.detected_columns = analysis['detected_columns']
            session.total_rows = analysis['total_rows']
            session.status = 'mapping'
            session.save()
            
            print(f"🧠 BACKEND: Generando campos mejorados con IA...")
            # Obtener información de detección si está disponible en la sesión
            detection_result = None
            if hasattr(session, 'detection_metadata'):
                detection_result = session.detection_metadata
            
            # Obtener campos mejorados con descripciones IA
            enhanced_fields = DataImportDetectionService.enhance_field_definitions(
                session.import_type, 
                analysis['detected_columns'],
                detection_result
            )
            
            # Sugerir mapeos automáticos
            print(f"🎯 BACKEND: Generando mapeos sugeridos...")
            suggested_mappings = ColumnMappingService.suggest_mappings(
                analysis['detected_columns'],
                session.import_type
            )
            
            print(f"✅ BACKEND: Análisis completo - {len(enhanced_fields)} campos con IA")
            
            return Response({
                'session_id': session.id,
                'detected_columns': analysis['detected_columns'],
                'sample_data': analysis['sample_data'],
                'total_rows': analysis['total_rows'],
                'column_info': analysis['column_info'],
                'available_fields': enhanced_fields,  # Campos mejorados con IA
                'suggested_mappings': suggested_mappings,
                'ai_enhanced': True,  # Indicador de que se usó IA
                'next_step': 'configure_mapping'
            })
            
        except Exception as e:
            print(f"❌ BACKEND: Error en analyze_file: {str(e)}")
            return Response({
                'error': f'Error al analizar archivo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def configure_mapping(self, request, pk=None):
        """Configurar mapeo de columnas"""
        try:
            session = self.get_object()
            
            if session.status != 'mapping':
                return Response({
                    'error': 'La sesión no está en estado de mapeo'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ColumnMappingCreateSerializer(data=request.data)
            if serializer.is_valid():
                mappings = serializer.validated_data['mappings']
                
                # Eliminar mapeos anteriores
                session.column_mappings.all().delete()
                
                # Crear nuevos mapeos
                available_fields = {f['field_name']: f for f in FIELD_DEFINITIONS.get(session.import_type, [])}
                
                for idx, mapping in enumerate(mappings):
                    source_column = mapping['source_column']
                    target_field = mapping.get('target_field')
                    
                    if target_field and target_field in available_fields:
                        field_def = available_fields[target_field]
                        
                        ColumnMapping.objects.create(
                            import_session=session,
                            source_column=source_column,
                            source_index=idx,
                            target_field=target_field,
                            field_type=field_def['field_type'],
                            is_required=field_def.get('is_required', False),
                            default_value=mapping.get('default_value', field_def.get('default_value', ''))
                        )
                
                # Validar mapeos requeridos
                required_fields = [f for f in available_fields.values() if f.get('is_required')]
                mapped_fields = [m['target_field'] for m in mappings if m.get('target_field')]
                missing_required = [f['display_name'] for f in required_fields if f['field_name'] not in mapped_fields]
                
                if missing_required:
                    return Response({
                        'error': 'Faltan campos requeridos',
                        'missing_fields': missing_required
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'message': 'Mapeo configurado exitosamente',
                    'mapped_columns': len(mappings),
                    'next_step': 'process_import'
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'Error al configurar mapeo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def process_import(self, request, pk=None):
        """Procesar importación de datos"""
        try:
            session = self.get_object()
            
            if session.status != 'mapping':
                return Response({
                    'error': 'La sesión no está lista para procesar'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ProcessImportSerializer(data=request.data)
            if serializer.is_valid():
                # Actualizar configuración de sesión
                session.skip_duplicates = serializer.validated_data['skip_duplicates']
                session.update_existing = serializer.validated_data['update_existing']
                session.status = 'processing'
                session.save()
                
                # Procesar importación
                results = DataImportService.process_import(
                    session,
                    serializer.validated_data['start_row'],
                    serializer.validated_data.get('end_row')
                )
                
                return Response({
                    'message': 'Importación completada',
                    'results': {
                        'total_rows': results['total_rows'],
                        'successful_rows': results['successful_rows'],
                        'failed_rows': results['failed_rows'],
                        'completion_percentage': (results['successful_rows'] / results['total_rows']) * 100 if results['total_rows'] > 0 else 0,
                        'errors': results['errors'][:10]  # Solo primeros 10 errores
                    }
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'Error al procesar importación: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Obtener estado de la importación"""
        session = self.get_object()
        
        return Response({
            'session_id': session.id,
            'status': session.status,
            'import_type': session.import_type,
            'original_filename': session.original_filename,
            'total_rows': session.total_rows,
            'processed_rows': session.processed_rows,
            'successful_rows': session.successful_rows,
            'failed_rows': session.failed_rows,
            'completion_percentage': (session.processed_rows / session.total_rows) * 100 if session.total_rows > 0 else 0,
            'created_at': session.created_at,
            'completed_at': session.completed_at,
        })
    
    @action(detail=True, methods=['get'])
    def errors(self, request, pk=None):
        """Obtener errores de la importación"""
        session = self.get_object()
        
        return Response({
            'session_id': session.id,
            'error_log': session.error_log,
            'failed_rows': session.failed_rows
        })


class FieldDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar definiciones de campos disponibles"""
    serializer_class = FieldDefinitionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FieldDefinition.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def by_import_type(self, request):
        """Obtener campos disponibles por tipo de importación"""
        import_type = request.query_params.get('import_type')
        
        if not import_type:
            return Response({
                'error': 'Parámetro import_type requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener campos de la base de datos en lugar de las definiciones estáticas
        field_definitions = FieldDefinition.objects.filter(
            import_type=import_type,
            is_active=True
        ).order_by('order', 'display_name')
        
        if not field_definitions.exists():
            return Response({
                'error': f'No se encontraron campos para el tipo de importación: {import_type}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serializar los campos
        serializer = self.get_serializer(field_definitions, many=True)
        
        return Response({
            'import_type': import_type,
            'fields': serializer.data,
            'total_fields': field_definitions.count()
        })


class ImportTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet para plantillas de importación"""
    serializer_class = ImportTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ImportTemplate.objects.filter(
            company=self.request.user.company
        ).order_by('-usage_count', 'name')
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            user=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Usar plantilla para crear mapeo automático"""
        template = self.get_object()
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response({
                'error': 'session_id requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            session = DataImportSession.objects.get(
                id=session_id,
                company=request.user.company
            )
            
            if session.import_type != template.import_type:
                return Response({
                    'error': 'Tipo de importación no coincide con la plantilla'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Aplicar mapeos de la plantilla
            session.column_mappings.all().delete()
            
            available_fields = {f['field_name']: f for f in FIELD_DEFINITIONS.get(session.import_type, [])}
            
            for source_col, target_field in template.column_mappings.items():
                if source_col in session.detected_columns and target_field in available_fields:
                    field_def = available_fields[target_field]
                    
                    ColumnMapping.objects.create(
                        import_session=session,
                        source_column=source_col,
                        source_index=session.detected_columns.index(source_col),
                        target_field=target_field,
                        field_type=field_def['field_type'],
                        is_required=field_def.get('is_required', False)
                    )
            
            # Incrementar contador de uso
            template.usage_count += 1
            template.save()
            
            return Response({
                'message': 'Plantilla aplicada exitosamente',
                'mapped_columns': len(template.column_mappings)
            })
            
        except DataImportSession.DoesNotExist:
            return Response({
                'error': 'Sesión de importación no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error al aplicar plantilla: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
