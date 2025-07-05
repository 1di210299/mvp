"""
Servicio de integración con OpenAI para análisis predictivo y reportes inteligentes
"""
import openai
import json
import pandas as pd
from django.conf import settings
from django.db import models
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OpenAIAnalyticsService:
    """Servicio para análisis de inventario usando OpenAI"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def analyze_inventory_trends(self, company_id: int, custom_fields_data: Dict = None) -> Dict:
        """
        Analiza tendencias de inventario incluyendo campos personalizados
        """
        try:
            # Obtener datos de inventario
            inventory_data = self._get_inventory_data(company_id)
            
            # Incluir campos personalizados si están disponibles
            if custom_fields_data:
                inventory_data.update(custom_fields_data)
            
            # Crear prompt para análisis
            prompt = self._create_inventory_analysis_prompt(inventory_data)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto analista de inventarios y cadena de suministro. 
                        Analiza los datos proporcionados y proporciona insights accionables sobre:
                        1. Patrones de rotación de inventario
                        2. Productos de baja/alta rotación
                        3. Predicciones de demanda
                        4. Recomendaciones de reabastecimiento
                        5. Análisis de campos personalizados si están presentes
                        
                        Responde en formato JSON estructurado con conclusiones claras."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error en análisis de inventario: {str(e)}")
            return {"error": f"Error en análisis: {str(e)}"}
    
    def generate_demand_forecast(self, product_id: int, periods: int = 12) -> Dict:
        """
        Genera pronóstico de demanda para un producto específico
        """
        try:
            # Obtener datos históricos del producto
            historical_data = self._get_product_historical_data(product_id)
            
            prompt = f"""
            Basándote en los siguientes datos históricos de movimiento de inventario,
            genera un pronóstico de demanda para los próximos {periods} períodos:
            
            Datos históricos:
            {json.dumps(historical_data, indent=2, default=str)}
            
            Considera:
            - Estacionalidad
            - Tendencias
            - Anomalías
            - Factores externos
            
            Proporciona el pronóstico en formato JSON con intervalos de confianza.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en pronósticos de demanda. Proporciona análisis precisos y confiables."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error en pronóstico de demanda: {str(e)}")
            return {"error": f"Error en pronóstico: {str(e)}"}
    
    def analyze_custom_fields_insights(self, company_id: int, model_type: str) -> Dict:
        """
        Analiza insights específicos de campos personalizados
        """
        try:
            from .custom_fields import CustomFieldDefinition, CustomFieldValue
            
            # Obtener definiciones de campos personalizados
            custom_fields = CustomFieldDefinition.objects.filter(
                company_id=company_id,
                model_type=model_type,
                is_active=True
            )
            
            # Recopilar datos de campos personalizados
            custom_data = {}
            for field in custom_fields:
                values = CustomFieldValue.objects.filter(
                    custom_field=field
                ).values_list('text_value', 'number_value', 'decimal_value', 'boolean_value')
                
                custom_data[field.field_name] = {
                    'type': field.field_type,
                    'label': field.field_label,
                    'values': list(values)
                }
            
            if not custom_data:
                return {"message": "No hay campos personalizados para analizar"}
            
            prompt = f"""
            Analiza los siguientes campos personalizados de una empresa y proporciona insights:
            
            Datos de campos personalizados:
            {json.dumps(custom_data, indent=2, default=str)}
            
            Proporciona:
            1. Patrones identificados en los datos personalizados
            2. Correlaciones con métricas de negocio
            3. Recomendaciones para optimización
            4. Oportunidades de mejora
            
            Responde en JSON estructurado.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un analista de datos empresariales especializado en campos personalizados y métricas de negocio."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error en análisis de campos personalizados: {str(e)}")
            return {"error": f"Error en análisis: {str(e)}"}
    
    def generate_intelligent_report(self, company_id: int, report_type: str, custom_filters: Dict = None) -> Dict:
        """
        Genera reportes inteligentes combinando datos estándar y campos personalizados
        """
        try:
            # Obtener datos base
            base_data = self._get_company_data(company_id)
            
            # Obtener datos de campos personalizados
            custom_data = self._get_all_custom_fields_data(company_id)
            
            # Aplicar filtros personalizados si existen
            if custom_filters:
                base_data = self._apply_custom_filters(base_data, custom_filters)
            
            prompt = f"""
            Genera un reporte inteligente tipo '{report_type}' para una empresa con los siguientes datos:
            
            Datos base:
            {json.dumps(base_data, indent=2, default=str)}
            
            Campos personalizados:
            {json.dumps(custom_data, indent=2, default=str)}
            
            El reporte debe incluir:
            1. Resumen ejecutivo
            2. Métricas clave
            3. Análisis de tendencias
            4. Insights de campos personalizados
            5. Recomendaciones accionables
            6. Gráficos sugeridos (descripción)
            
            Formato: JSON estructurado para fácil consumo por frontend.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"Eres un analista de negocios experto generando reportes tipo '{report_type}'. Proporciona insights valiosos y accionables."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error generando reporte inteligente: {str(e)}")
            return {"error": f"Error generando reporte: {str(e)}"}
    
    def suggest_custom_fields(self, company_id: int, model_type: str, business_context: str = "") -> Dict:
        """
        Sugiere campos personalizados basado en el contexto del negocio y mejores prácticas
        """
        try:
            # Analizar datos existentes
            existing_data = self._get_model_data(company_id, model_type)
            
            prompt = f"""
            Basándote en los datos existentes de una empresa y el contexto del negocio,
            sugiere campos personalizados útiles para el modelo '{model_type}':
            
            Datos existentes:
            {json.dumps(existing_data, indent=2, default=str)}
            
            Contexto del negocio:
            {business_context}
            
            Proporciona sugerencias de campos personalizados que podrían:
            1. Mejorar el análisis de datos
            2. Facilitar reportes específicos del sector
            3. Optimizar operaciones
            4. Cumplir con regulaciones específicas
            
            Para cada sugerencia incluye:
            - Nombre del campo
            - Tipo de dato
            - Justificación
            - Beneficios esperados
            
            Responde en JSON estructurado.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un consultor en sistemas de gestión empresarial. Sugieres mejoras basadas en mejores prácticas del sector."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error sugiriendo campos personalizados: {str(e)}")
            return {"error": f"Error en sugerencias: {str(e)}"}
    
    # Métodos auxiliares para obtener datos
    
    def _get_inventory_data(self, company_id: int) -> Dict:
        """Obtiene datos de inventario para análisis"""
        from .models import Product, InventoryItem
        
        products = Product.objects.filter(company_id=company_id).values(
            'sku', 'name', 'cost_price', 'sale_price', 'minimum_stock', 'current_stock'
        )
        
        inventory_items = InventoryItem.objects.filter(
            product__company_id=company_id
        ).values(
            'product__sku', 'quantity', 'reserved_quantity', 'unit_cost', 'batch_number', 'expiry_date'
        )
        
        return {
            'products': list(products),
            'inventory_items': list(inventory_items),
            'summary': {
                'total_products': len(products),
                'total_inventory_value': sum(item['quantity'] * item['unit_cost'] for item in inventory_items)
            }
        }
    
    def _get_product_historical_data(self, product_id: int) -> Dict:
        """Obtiene datos históricos de un producto"""
        from .models import Transaction
        
        transactions = Transaction.objects.filter(
            product_id=product_id
        ).order_by('date').values(
            'date', 'transaction_type', 'quantity', 'unit_cost'
        )
        
        return {
            'product_id': product_id,
            'transactions': list(transactions)
        }
    
    def _get_company_data(self, company_id: int) -> Dict:
        """Obtiene datos generales de la empresa"""
        from .models import Product, Supplier, Category
        
        return {
            'products_count': Product.objects.filter(company_id=company_id).count(),
            'suppliers_count': Supplier.objects.filter(company_id=company_id).count(),
            'categories_count': Category.objects.filter(company_id=company_id).count(),
            'total_inventory_value': self._calculate_total_inventory_value(company_id)
        }
    
    def _get_all_custom_fields_data(self, company_id: int) -> Dict:
        """Obtiene todos los datos de campos personalizados"""
        from .custom_fields import CustomFieldDefinition, CustomFieldValue
        
        custom_fields = CustomFieldDefinition.objects.filter(
            company_id=company_id,
            is_active=True
        )
        
        data = {}
        for field in custom_fields:
            values = CustomFieldValue.objects.filter(custom_field=field)
            data[f"{field.model_type}_{field.field_name}"] = {
                'definition': {
                    'label': field.field_label,
                    'type': field.field_type
                },
                'values': [value.get_value() for value in values]
            }
        
        return data
    
    def _create_inventory_analysis_prompt(self, data: Dict) -> str:
        """Crea el prompt para análisis de inventario"""
        return f"""
        Analiza los siguientes datos de inventario y proporciona insights detallados:
        
        {json.dumps(data, indent=2, default=str)}
        
        Enfócate en:
        1. Productos con stock bajo vs demanda
        2. Productos de alta rotación
        3. Análisis de rentabilidad por producto
        4. Optimización de niveles de stock
        5. Predicciones de reabastecimiento
        """
    
    def _apply_custom_filters(self, data: Dict, filters: Dict) -> Dict:
        """Aplica filtros personalizados a los datos"""
        # Implementar lógica de filtrado según necesidades
        return data
    
    def _get_model_data(self, company_id: int, model_type: str) -> Dict:
        """Obtiene datos de un modelo específico"""
        from .models import Product, Supplier, Category
        
        model_map = {
            'product': Product.objects.filter(company_id=company_id),
            'supplier': Supplier.objects.filter(company_id=company_id),
            'category': Category.objects.filter(company_id=company_id)
        }
        
        queryset = model_map.get(model_type)
        if queryset:
            return {'count': queryset.count(), 'sample_data': list(queryset.values()[:5])}
        
        return {}
    
    def _calculate_total_inventory_value(self, company_id: int) -> float:
        """Calcula el valor total del inventario"""
        from .models import InventoryItem
        
        total = InventoryItem.objects.filter(
            product__company_id=company_id
        ).aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_cost'))
        )['total']
        
        return float(total or 0)


# Funciones de utilidad para usar en views

def get_ai_insights_for_product(product_id: int) -> Dict:
    """Obtiene insights de IA para un producto específico"""
    service = OpenAIAnalyticsService()
    return service.generate_demand_forecast(product_id)

def get_ai_inventory_analysis(company_id: int, include_custom_fields: bool = True) -> Dict:
    """Obtiene análisis completo de inventario con IA"""
    service = OpenAIAnalyticsService()
    
    custom_data = {}
    if include_custom_fields:
        custom_data = service._get_all_custom_fields_data(company_id)
    
    return service.analyze_inventory_trends(company_id, custom_data)

def suggest_optimization_fields(company_id: int, business_type: str = "") -> Dict:
    """Sugiere campos personalizados para optimización"""
    service = OpenAIAnalyticsService()
    return service.suggest_custom_fields(company_id, 'product', business_type)
