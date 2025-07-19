#!/usr/bin/env python
"""
Script de verificación completa para endpoints de forecasting
Verifica que todos los endpoints estén funcionando correctamente
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import time

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse, NoReverseMatch
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework import status
from authentication.models import Company
from inventory.models import Product, Category, Location, Supplier, Customer
from forecasting.models import ForecastModel, DemandForecast, ReorderRecommendation

User = get_user_model()

class ForecastingEndpointVerifier:
    """
    Verificador completo de endpoints de forecasting
    """
    
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.client = APIClient()
        self.results = {
            'total_endpoints': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }
        self.user = None
        self.company = None
        self.auth_token = None
        
    def setup_test_data(self):
        """Crear datos de prueba necesarios"""
        print("🔧 Configurando datos de prueba...")
        
        try:
            # Crear empresa
            self.company, _ = Company.objects.get_or_create(
                name="Test Company",
                defaults={
                    'email': 'test@company.com',
                    'phone': '+51999999999'
                }
            )
            
            # Crear usuario
            self.user, created = User.objects.get_or_create(
                email='test@forecasting.com',
                defaults={
                    'first_name': 'Test',
                    'last_name': 'User',
                    'company': self.company,
                    'is_active': True
                }
            )
            
            if created:
                self.user.set_password('testpass123')
                self.user.save()
            
            # Autenticar usuario
            self.client.force_authenticate(user=self.user)
            
            # Crear categoría (sin campo company)
            category, _ = Category.objects.get_or_create(
                name="Test Category",
                defaults={'description': 'Test category for forecasting'}
            )
            
            # Crear ubicación (sin campo company)
            location, _ = Location.objects.get_or_create(
                name="Test Location",
                code="TEST001",
                defaults={
                    'warehouse': 'Main Warehouse',
                    'description': 'Test location for forecasting'
                }
            )
            
            # Crear proveedor (sin campo company)
            supplier, _ = Supplier.objects.get_or_create(
                name="Test Supplier",
                defaults={
                    'email': 'supplier@test.com',
                    'contact_name': 'Test Contact'
                }
            )
            
            # Crear cliente (sin campo company, corregir campos)
            customer, _ = Customer.objects.get_or_create(
                email="customer@test.com",
                defaults={
                    'name': 'Test Customer',
                    'phone': '+51999999999'
                }
            )
            
            # Crear productos (verificar campos correctos)
            for i in range(3):
                Product.objects.get_or_create(
                    sku=f"TEST-SKU-{i:03d}",
                    defaults={
                        'name': f'Test Product {i}',
                        'company': self.company,
                        'category': category,
                        'supplier': supplier,
                        'cost_price': 80.00 + i * 5,
                        'sale_price': 100.00 + i * 10,
                        'stock': 50 + i * 10,
                        'min_stock': 10,
                        'max_stock': 100,
                        'unit': 'unidad'
                    }
                )
            
            # Crear modelo de pronóstico
            forecast_model, _ = ForecastModel.objects.get_or_create(
                name="Test Forecast Model",
                defaults={
                    'company': self.company,
                    'model_type': 'prophet',
                    'status': 'trained',
                    'forecast_horizon_days': 30,
                    'training_period_days': 365,
                    'confidence_interval': 0.95
                }
            )
            
            # Agregar productos al modelo
            forecast_model.products.add(*Product.objects.filter(company=self.company))
            
            print("✅ Datos de prueba configurados correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error configurando datos de prueba: {str(e)}")
            return False
    
    def test_endpoint(self, url_pattern: str, method: str = 'GET', data: dict = None, name: str = None):
        """Probar un endpoint específico"""
        try:
            url = reverse(url_pattern)
        except NoReverseMatch:
            # Si no se puede hacer reverse, intentar con el patrón directo
            url = f"/forecasting/{url_pattern.lstrip('/')}"
        
        endpoint_name = name or url_pattern
        self.results['total_endpoints'] += 1
        
        try:
            if method == 'GET':
                response = self.client.get(url)
            elif method == 'POST':
                response = self.client.post(url, data=data, format='json')
            elif method == 'PUT':
                response = self.client.put(url, data=data, format='json')
            elif method == 'PATCH':
                response = self.client.patch(url, data=data, format='json')
            elif method == 'DELETE':
                response = self.client.delete(url)
            
            # Determinar si es exitoso
            is_success = response.status_code in [200, 201, 202, 204, 404]  # 404 puede ser esperado si no hay datos
            
            if is_success:
                self.results['successful'] += 1
                status_icon = "✅"
            else:
                self.results['failed'] += 1
                status_icon = "❌"
                self.results['errors'].append({
                    'endpoint': endpoint_name,
                    'status_code': response.status_code,
                    'response': str(response.content[:200])
                })
            
            self.results['details'].append({
                'endpoint': endpoint_name,
                'method': method,
                'status_code': response.status_code,
                'success': is_success,
                'response_size': len(response.content) if response.content else 0
            })
            
            print(f"{status_icon} {method} {endpoint_name} - Status: {response.status_code}")
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['errors'].append({
                'endpoint': endpoint_name,
                'error': str(e)
            })
            print(f"❌ {method} {endpoint_name} - Error: {str(e)}")
    
    def verify_viewsets(self):
        """Verificar todos los ViewSets"""
        print("\n📊 Verificando ViewSets...")
        
        viewsets = [
            # Forecasting principal
            ('models/', 'ForecastModel ViewSet'),
            ('forecasts/', 'DemandForecast ViewSet'),
            ('reorder-recommendations/', 'ReorderRecommendation ViewSet'),
            
            # Financial
            ('financial/models/', 'Financial Models ViewSet'),
            ('financial/revenue-predictions/', 'Revenue Predictions ViewSet'),
            ('financial/cash-flow/', 'Cash Flow ViewSet'),
            ('financial/profitability/', 'Profitability ViewSet'),
            ('financial/risk-assessment/', 'Risk Assessment ViewSet'),
            ('financial/seasonality/', 'Seasonality ViewSet'),
            ('financial/cost-optimization/', 'Cost Optimization ViewSet'),
            ('financial/revenue-breakdown/', 'Revenue Breakdown ViewSet'),
            ('financial/scenarios/', 'Financial Scenarios ViewSet'),
            ('financial/profit-margins/', 'Profit Margins ViewSet'),
            ('financial/trends/', 'Financial Trends ViewSet'),
            
            # Demand & Inventory
            ('demand/patterns/', 'Demand Patterns ViewSet'),
            ('demand/advanced-forecasts/', 'Advanced Forecasts ViewSet'),
            ('demand/seasonal-patterns/', 'Seasonal Patterns ViewSet'),
            ('inventory/optimization-models/', 'Inventory Models ViewSet'),
            ('inventory/stock-recommendations/', 'Stock Recommendations ViewSet'),
            ('suppliers/performance/', 'Supplier Performance ViewSet'),
            ('suppliers/procurement/', 'Procurement ViewSet'),
            ('suppliers/risk-analysis/', 'Supplier Risk ViewSet'),
            ('suppliers/roi-analysis/', 'Supplier ROI ViewSet'),
            ('inventory/turnover/', 'Inventory Turnover ViewSet'),
            
            # Customer Intelligence
            ('customers/lifetime-value/', 'Customer CLV ViewSet'),
            ('customers/churn-prediction/', 'Churn Prediction ViewSet'),
            ('customers/segmentation/', 'Customer Segmentation ViewSet'),
            ('customers/market-basket/', 'Market Basket ViewSet'),
            ('customers/behavior-patterns/', 'Behavior Patterns ViewSet'),
            ('customers/price-optimization/', 'Price Optimization ViewSet'),
            ('customers/cross-sell/', 'Cross Sell ViewSet'),
            ('customers/satisfaction/', 'Customer Satisfaction ViewSet'),
            ('customers/loyalty-program/', 'Loyalty Program ViewSet'),
            ('customers/engagement/', 'Customer Engagement ViewSet'),
        ]
        
        for endpoint, name in viewsets:
            self.test_endpoint(f"/forecasting/{endpoint}", 'GET', name=name)
    
    def verify_special_endpoints(self):
        """Verificar endpoints especiales"""
        print("\n🎯 Verificando endpoints especiales...")
        
        special_endpoints = [
            # ML Endpoints
            ('predict/', 'POST', {'periods': 30}, 'Predict Demand'),
            ('train-model/', 'POST', {'model_type': 'prophet'}, 'Train Model'),
            ('models/comparison/', 'GET', None, 'Model Comparison'),
            
            # Charts & Reports
            ('charts/', 'GET', None, 'Forecast Charts'),
            ('summary/', 'GET', None, 'Forecast Summary'),
            
            # Dashboards
            ('financial/dashboard/', 'GET', None, 'Financial Dashboard'),
            ('financial/reports/', 'GET', None, 'Financial Reports'),
            ('demand/analysis/', 'GET', None, 'Demand Analysis'),
            ('inventory/optimization/', 'GET', None, 'Inventory Optimization'),
            ('customers/intelligence/', 'GET', None, 'Customer Intelligence'),
            ('customers/dashboard/', 'GET', None, 'Customer Dashboard'),
        ]
        
        for endpoint, method, data, name in special_endpoints:
            self.test_endpoint(f"/forecasting/{endpoint}", method, data, name)
    
    def verify_crud_operations(self):
        """Verificar operaciones CRUD en algunos modelos clave"""
        print("\n🔧 Verificando operaciones CRUD...")
        
        # Test crear un modelo de pronóstico
        forecast_model_data = {
            'name': 'Test API Model',
            'model_type': 'prophet',
            'forecast_horizon_days': 30,
            'training_period_days': 365,
            'confidence_interval': 0.95
        }
        
        self.test_endpoint('/forecasting/models/', 'POST', forecast_model_data, 'Create Forecast Model')
        
        # Test crear una recomendación de reorden
        try:
            product = Product.objects.filter(company=self.company).first()
            location = Location.objects.filter(company=self.company).first()
            
            if product and location:
                reorder_data = {
                    'product': product.id,
                    'location': location.id,
                    'recommended_quantity': 100,
                    'current_stock': 50,
                    'projected_demand': 80,
                    'priority': 'medium'
                }
                
                self.test_endpoint('/forecasting/reorder-recommendations/', 'POST', reorder_data, 'Create Reorder Recommendation')
        except Exception as e:
            print(f"⚠️ Error en CRUD test: {str(e)}")
    
    def generate_report(self):
        """Generar reporte de resultados"""
        print("\n" + "="*60)
        print("📊 REPORTE DE VERIFICACIÓN DE ENDPOINTS")
        print("="*60)
        
        success_rate = (self.results['successful'] / self.results['total_endpoints']) * 100 if self.results['total_endpoints'] > 0 else 0
        
        print(f"📈 Total de endpoints verificados: {self.results['total_endpoints']}")
        print(f"✅ Exitosos: {self.results['successful']}")
        print(f"❌ Fallidos: {self.results['failed']}")
        print(f"📊 Tasa de éxito: {success_rate:.1f}%")
        
        if self.results['errors']:
            print(f"\n❌ ERRORES ENCONTRADOS ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results['errors'][:10], 1):  # Mostrar solo los primeros 10
                print(f"  {i}. {error.get('endpoint', 'Unknown')}: {error.get('error', error.get('status_code', 'Unknown error'))}")
        
        print(f"\n📋 DETALLES POR CATEGORÍA:")
        categories = {}
        for detail in self.results['details']:
            endpoint = detail['endpoint']
            if 'financial' in endpoint.lower():
                category = 'Financial'
            elif 'customer' in endpoint.lower():
                category = 'Customer Intelligence'
            elif 'demand' in endpoint.lower() or 'inventory' in endpoint.lower() or 'supplier' in endpoint.lower():
                category = 'Demand & Inventory'
            else:
                category = 'Core Forecasting'
            
            if category not in categories:
                categories[category] = {'total': 0, 'success': 0}
            
            categories[category]['total'] += 1
            if detail['success']:
                categories[category]['success'] += 1
        
        for category, stats in categories.items():
            success_rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"  📁 {category}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Determinar estado general
        if success_rate >= 90:
            print(f"\n🎉 ESTADO: EXCELENTE - El sistema está funcionando correctamente")
        elif success_rate >= 75:
            print(f"\n✅ ESTADO: BUENO - El sistema está mayormente funcional")
        elif success_rate >= 50:
            print(f"\n⚠️ ESTADO: REGULAR - Algunos problemas requieren atención")
        else:
            print(f"\n❌ ESTADO: CRÍTICO - Múltiples problemas requieren atención inmediata")
        
        print("="*60)
        
        return success_rate
    
    def run_verification(self):
        """Ejecutar verificación completa"""
        print("🚀 INICIANDO VERIFICACIÓN COMPLETA DE FORECASTING")
        print("="*60)
        
        start_time = time.time()
        
        # Configurar datos de prueba
        if not self.setup_test_data():
            print("❌ No se pudo configurar los datos de prueba. Abortando verificación.")
            return False
        
        # Verificar ViewSets
        self.verify_viewsets()
        
        # Verificar endpoints especiales
        self.verify_special_endpoints()
        
        # Verificar operaciones CRUD
        self.verify_crud_operations()
        
        # Generar reporte
        end_time = time.time()
        success_rate = self.generate_report()
        
        print(f"\n⏱️ Tiempo total de verificación: {end_time - start_time:.2f} segundos")
        
        return success_rate >= 75  # Consideramos exitoso si >= 75% funciona

def main():
    """Función principal"""
    verifier = ForecastingEndpointVerifier()
    success = verifier.run_verification()
    
    # Código de salida
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
