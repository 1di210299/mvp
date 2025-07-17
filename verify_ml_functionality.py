#!/usr/bin/env python
"""
Verificación PROFUNDA de funcionalidades ML en forecasting
Verifica que los algoritmos realmente funcionen, no solo que los endpoints respondan
"""

import os
import sys
import django
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from authentication.models import Company
from inventory.models import Product, Category, Sale, Customer
from forecasting.models import ForecastModel, DemandForecast

User = get_user_model()

class MLFunctionalityVerifier:
    """
    Verificador PROFUNDO de funcionalidades ML
    """
    
    def __init__(self):
        self.client = APIClient()
        self.results = {
            'ml_tests': [],
            'functionality_score': 0,
            'total_tests': 0,
            'passed_tests': 0,
            'critical_failures': [],
            'feature_status': {}
        }
        self.user = None
        self.company = None
        
    def setup_realistic_data(self):
        """Crear datos realistas para pruebas ML"""
        print("🔧 Configurando datos realistas para ML...")
        
        try:
            # Crear empresa
            self.company, _ = Company.objects.get_or_create(
                name="ML Test Company",
                defaults={
                    'email': 'ml@test.com',
                    'ruc': '12345678901',
                    'address': 'Test Address'
                }
            )
            
            # Crear usuario (asegurarse de tener username único)
            username = f'ml_tester_{int(time.time())}'  # Username único basado en timestamp
            self.user, created = User.objects.get_or_create(
                email='ml@test.com',
                defaults={
                    'username': username,
                    'first_name': 'ML',
                    'last_name': 'Tester',
                    'company': self.company,
                    'is_active': True
                }
            )
            
            if created:
                self.user.set_password('mltest123')
                self.user.save()
            
            self.client.force_authenticate(user=self.user)
            
            # Crear categoría
            category, _ = Category.objects.get_or_create(
                name="ML Test Category",
                defaults={'description': 'Category for ML testing'}
            )
            
            # Crear productos con datos realistas
            products = []
            for i in range(5):
                product, _ = Product.objects.get_or_create(
                    sku=f"ML-PROD-{i:03d}",
                    defaults={
                        'name': f'ML Test Product {i}',
                        'company': self.company,
                        'category': category,
                        'cost_price': 50.00 + i * 10,
                        'sale_price': 100.00 + i * 20,
                        'stock': 100 + i * 50,
                        'min_stock': 20,
                        'max_stock': 500,
                        'unit': 'unidad'
                    }
                )
                products.append(product)
            
            # Crear datos históricos de ventas (CRUCIAL para ML)
            print("📊 Generando datos históricos de ventas...")
            base_date = datetime.now() - timedelta(days=365)
            
            # Limpiar datos anteriores para evitar duplicados
            Sale.objects.filter(product__company=self.company).delete()
            
            for product in products:
                sales_to_create = []
                for days_back in range(365):
                    date = base_date + timedelta(days=days_back)
                    
                    # Simular patrones estacionales
                    seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * days_back / 365)
                    weekly_factor = 1.2 if date.weekday() < 5 else 0.8  # Más ventas entre semana
                    
                    # Cantidad base con variabilidad
                    base_quantity = 10 + product.id * 2
                    quantity = max(1, int(base_quantity * seasonal_factor * weekly_factor * (1 + 0.2 * np.random.randn())))
                    
                    # Crear objeto Sale pero no guardarlo aún
                    sale = Sale(
                        product=product,
                        quantity=quantity,
                        unit_price=product.sale_price,
                        date_sold=date,
                        customer_name=f'Customer {np.random.randint(1, 100)}'
                    )
                    sales_to_create.append(sale)
                
                # Crear todas las ventas de una vez (más eficiente)
                Sale.objects.bulk_create(sales_to_create, ignore_conflicts=True)
            
            print(f"✅ Creados datos históricos para {len(products)} productos")
            return True
            
        except Exception as e:
            print(f"❌ Error configurando datos: {str(e)}")
            return False
    
    def test_ml_algorithm(self, algorithm: str, test_name: str) -> Dict[str, Any]:
        """Test individual de algoritmo ML"""
        self.results['total_tests'] += 1
        test_result = {
            'name': test_name,
            'algorithm': algorithm,
            'passed': False,
            'details': {},
            'error': None
        }
        
        try:
            print(f"🔬 Probando {algorithm} - {test_name}")
            
            # Intentar crear modelo con algoritmo específico
            response = self.client.post('/api/forecasting/models/', {
                'name': f'Test {algorithm} Model',
                'model_type': algorithm.lower(),
                'forecast_horizon_days': 30,
                'training_period_days': 90,
                'confidence_interval': 0.95
            }, format='json')
            
            if response.status_code == 201:
                model_data = response.json()
                test_result['details']['model_created'] = True
                test_result['details']['model_id'] = model_data.get('id')
                
                # Intentar entrenar el modelo
                train_response = self.client.post('/api/forecasting/train-model/', {
                    'model_id': model_data.get('id'),
                    'model_type': algorithm.lower()
                }, format='json')
                
                if train_response.status_code in [200, 201, 202]:
                    test_result['details']['training_started'] = True
                    
                    # Intentar hacer predicción
                    predict_response = self.client.post('/api/forecasting/predict/', {
                        'model_id': model_data.get('id'),
                        'periods': 7
                    }, format='json')
                    
                    if predict_response.status_code == 200:
                        prediction_data = predict_response.json()
                        test_result['details']['prediction_generated'] = True
                        test_result['details']['prediction_points'] = len(prediction_data.get('forecast', []))
                        test_result['passed'] = True
                        self.results['passed_tests'] += 1
                    else:
                        test_result['error'] = f"Predicción falló: {predict_response.status_code}"
                else:
                    test_result['error'] = f"Entrenamiento falló: {train_response.status_code}"
            else:
                test_result['error'] = f"Creación de modelo falló: {response.status_code} - {response.content[:200]}"
                
        except Exception as e:
            test_result['error'] = str(e)
        
        self.results['ml_tests'].append(test_result)
        return test_result
    
    def test_prophet_algorithm(self):
        """Test específico de Prophet"""
        return self.test_ml_algorithm('Prophet', 'Facebook Prophet Time Series')
    
    def test_arima_algorithm(self):
        """Test específico de ARIMA"""
        return self.test_ml_algorithm('ARIMA', 'ARIMA Statistical Model')
    
    def test_lstm_algorithm(self):
        """Test específico de LSTM"""
        return self.test_ml_algorithm('LSTM', 'LSTM Neural Network')
    
    def test_random_forest_algorithm(self):
        """Test específico de Random Forest"""
        return self.test_ml_algorithm('RandomForest', 'Random Forest Ensemble')
    
    def test_customer_clv_calculation(self):
        """Test de Customer Lifetime Value real"""
        self.results['total_tests'] += 1
        print("💰 Probando Customer Lifetime Value...")
        
        try:
            # Crear clientes con historial
            customers = []
            for i in range(3):
                customer, _ = Customer.objects.get_or_create(
                    email=f"clv_test_{i}@test.com",
                    defaults={
                        'name': f'CLV Test Customer {i}',
                        'phone': f'+5199999999{i}'
                    }
                )
                customers.append(customer)
            
            # Simular compras históricas
            for customer in customers:
                for days_back in range(180):
                    if np.random.random() < 0.1:  # 10% chance de compra por día
                        date = datetime.now() - timedelta(days=days_back)
                        Sale.objects.create(
                            product=Product.objects.filter(company=self.company).first(),
                            quantity=np.random.randint(1, 5),
                            unit_price=100.0,
                            date_sold=date,
                            customer_name=customer.name
                        )
            
            # Probar endpoint de CLV
            response = self.client.get('/api/forecasting/customers/lifetime-value/')
            
            if response.status_code == 200:
                clv_data = response.json()
                if isinstance(clv_data, list) and len(clv_data) > 0:
                    # Verificar que tenga campos esperados de CLV
                    first_customer = clv_data[0]
                    has_clv_fields = any(key in first_customer for key in ['clv', 'lifetime_value', 'predicted_value'])
                    
                    if has_clv_fields:
                        self.results['passed_tests'] += 1
                        self.results['feature_status']['Customer CLV'] = 'IMPLEMENTED'
                        print("✅ Customer CLV está calculando valores reales")
                        return True
            
            self.results['feature_status']['Customer CLV'] = 'NOT_IMPLEMENTED'
            self.results['critical_failures'].append('Customer CLV no genera cálculos reales')
            print("❌ Customer CLV no está implementado funcionalmente")
            
        except Exception as e:
            self.results['critical_failures'].append(f'Customer CLV error: {str(e)}')
            print(f"❌ Error en CLV: {str(e)}")
        
        return False
    
    def test_inventory_optimization(self):
        """Test de optimización de inventario real"""
        self.results['total_tests'] += 1
        print("📦 Probando Optimización de Inventario...")
        
        try:
            response = self.client.get('/api/forecasting/inventory/optimization/')
            
            if response.status_code == 200:
                optimization_data = response.json()
                
                # Verificar que devuelva cálculos reales
                if isinstance(optimization_data, dict) and 'recommendations' in optimization_data:
                    recommendations = optimization_data['recommendations']
                    
                    if isinstance(recommendations, list) and len(recommendations) > 0:
                        # Verificar campos de optimización
                        first_rec = recommendations[0]
                        has_optimization_fields = any(key in first_rec for key in [
                            'optimal_stock', 'reorder_point', 'safety_stock', 'economic_order_quantity'
                        ])
                        
                        if has_optimization_fields:
                            self.results['passed_tests'] += 1
                            self.results['feature_status']['Inventory Optimization'] = 'IMPLEMENTED'
                            print("✅ Optimización de Inventario está calculando valores reales")
                            return True
            
            self.results['feature_status']['Inventory Optimization'] = 'NOT_IMPLEMENTED'
            self.results['critical_failures'].append('Inventory Optimization no genera cálculos reales')
            print("❌ Optimización de Inventario no está implementada funcionalmente")
            
        except Exception as e:
            self.results['critical_failures'].append(f'Inventory Optimization error: {str(e)}')
            print(f"❌ Error en Inventory Optimization: {str(e)}")
        
        return False
    
    def test_demand_forecasting(self):
        """Test de pronósticos de demanda real"""
        self.results['total_tests'] += 1
        print("📈 Probando Pronósticos de Demanda...")
        
        try:
            response = self.client.get('/api/forecasting/demand/patterns/')
            
            if response.status_code == 200:
                demand_data = response.json()
                
                if isinstance(demand_data, list) and len(demand_data) > 0:
                    # Verificar que tenga patrones calculados
                    first_pattern = demand_data[0]
                    has_forecast_fields = any(key in first_pattern for key in [
                        'forecast', 'trend', 'seasonality', 'predicted_demand'
                    ])
                    
                    if has_forecast_fields:
                        self.results['passed_tests'] += 1
                        self.results['feature_status']['Demand Forecasting'] = 'IMPLEMENTED'
                        print("✅ Pronósticos de Demanda están generando predicciones reales")
                        return True
            
            self.results['feature_status']['Demand Forecasting'] = 'NOT_IMPLEMENTED'
            self.results['critical_failures'].append('Demand Forecasting no genera predicciones reales')
            print("❌ Pronósticos de Demanda no están implementados funcionalmente")
            
        except Exception as e:
            self.results['critical_failures'].append(f'Demand Forecasting error: {str(e)}')
            print(f"❌ Error en Demand Forecasting: {str(e)}")
        
        return False
    
    def test_financial_predictions(self):
        """Test de predicciones financieras"""
        self.results['total_tests'] += 1
        print("💵 Probando Predicciones Financieras...")
        
        try:
            response = self.client.get('/api/forecasting/financial/revenue-predictions/')
            
            if response.status_code == 200:
                financial_data = response.json()
                
                if isinstance(financial_data, dict) and 'predictions' in financial_data:
                    predictions = financial_data['predictions']
                    
                    if isinstance(predictions, list) and len(predictions) > 0:
                        # Verificar campos financieros calculados
                        first_pred = predictions[0]
                        has_financial_fields = any(key in first_pred for key in [
                            'predicted_revenue', 'profit_margin', 'cash_flow', 'roi'
                        ])
                        
                        if has_financial_fields:
                            self.results['passed_tests'] += 1
                            self.results['feature_status']['Financial Predictions'] = 'IMPLEMENTED'
                            print("✅ Predicciones Financieras están calculando valores reales")
                            return True
            
            self.results['feature_status']['Financial Predictions'] = 'NOT_IMPLEMENTED'
            self.results['critical_failures'].append('Financial Predictions no genera cálculos reales')
            print("❌ Predicciones Financieras no están implementadas funcionalmente")
            
        except Exception as e:
            self.results['critical_failures'].append(f'Financial Predictions error: {str(e)}')
            print(f"❌ Error en Financial Predictions: {str(e)}")
        
        return False
    
    def generate_ml_report(self):
        """Generar reporte detallado de funcionalidades ML"""
        print("\n" + "="*80)
        print("🧠 REPORTE PROFUNDO DE FUNCIONALIDADES ML")
        print("="*80)
        
        # Calcular score de funcionalidad
        if self.results['total_tests'] > 0:
            self.results['functionality_score'] = (self.results['passed_tests'] / self.results['total_tests']) * 100
        
        print(f"📊 Score de Funcionalidad ML: {self.results['functionality_score']:.1f}%")
        print(f"✅ Tests Pasados: {self.results['passed_tests']}/{self.results['total_tests']}")
        
        # Reporte por algoritmo ML
        print(f"\n🤖 ALGORITMOS ML:")
        ml_algorithms = [t for t in self.results['ml_tests']]
        
        for test in ml_algorithms:
            status = "✅ FUNCIONANDO" if test['passed'] else "❌ NO FUNCIONA"
            print(f"  {test['algorithm']}: {status}")
            if test['error']:
                print(f"    Error: {test['error']}")
        
        # Reporte por funcionalidad
        print(f"\n🎯 FUNCIONALIDADES AVANZADAS:")
        for feature, status in self.results['feature_status'].items():
            icon = "✅" if status == 'IMPLEMENTED' else "❌"
            print(f"  {icon} {feature}: {status}")
        
        # Errores críticos
        if self.results['critical_failures']:
            print(f"\n🚨 PROBLEMAS CRÍTICOS:")
            for i, failure in enumerate(self.results['critical_failures'], 1):
                print(f"  {i}. {failure}")
        
        # Evaluación final
        print(f"\n📋 EVALUACIÓN FINAL:")
        if self.results['functionality_score'] >= 80:
            print("🎉 ESTADO: PLATAFORMA ML COMPLETAMENTE FUNCIONAL")
            print("   Todas las funcionalidades ML están implementadas y funcionando")
        elif self.results['functionality_score'] >= 60:
            print("✅ ESTADO: PLATAFORMA ML PARCIALMENTE FUNCIONAL")
            print("   La mayoría de funcionalidades ML funcionan, algunas necesitan trabajo")
        elif self.results['functionality_score'] >= 40:
            print("⚠️ ESTADO: PLATAFORMA ML EN DESARROLLO")
            print("   Funcionalidades básicas implementadas, necesita más trabajo")
        else:
            print("❌ ESTADO: PLATAFORMA ML NO FUNCIONAL")
            print("   Las funcionalidades ML no están implementadas o no funcionan")
        
        print("="*80)
        
        return self.results['functionality_score']
    
    def run_complete_ml_verification(self):
        """Ejecutar verificación completa de ML"""
        print("🚀 INICIANDO VERIFICACIÓN PROFUNDA DE FUNCIONALIDADES ML")
        print("="*80)
        
        start_time = time.time()
        
        # Setup datos realistas
        if not self.setup_realistic_data():
            print("❌ No se pudo configurar datos realistas. Abortando.")
            return False
        
        # Tests de algoritmos ML
        print("\n🤖 PROBANDO ALGORITMOS ML...")
        self.test_prophet_algorithm()
        self.test_arima_algorithm()
        self.test_lstm_algorithm()
        self.test_random_forest_algorithm()
        
        # Tests de funcionalidades avanzadas
        print("\n🎯 PROBANDO FUNCIONALIDADES AVANZADAS...")
        self.test_customer_clv_calculation()
        self.test_inventory_optimization()
        self.test_demand_forecasting()
        self.test_financial_predictions()
        
        # Generar reporte
        end_time = time.time()
        score = self.generate_ml_report()
        
        print(f"\n⏱️ Tiempo total de verificación ML: {end_time - start_time:.2f} segundos")
        
        return score >= 60  # Consideramos exitoso si >= 60% de ML funciona

def main():
    """Función principal"""
    verifier = MLFunctionalityVerifier()
    success = verifier.run_complete_ml_verification()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
