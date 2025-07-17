#!/usr/bin/env python3
"""
Script de prueba comprehensiva del sistema ML de forecasting
Verifica la funcionalidad real de los algoritmos implementados
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from decimal import Decimal

from authentication.models import Company
from inventory.models import Product, Sale, Customer, Category
from forecasting.models import ForecastModel, DemandForecast
from forecasting.ml_algorithms.training_service import training_service
from forecasting.ml_algorithms.ml_service import MLAlgorithmService
from forecasting.services.advanced_ml_service import CustomerIntelligenceService, FinancialForecastingService

class MLSystemTester:
    def __init__(self):
        self.company = None
        self.test_results = {
            'ml_algorithms': {'prophet': False, 'arima': False, 'randomforest': False},
            'customer_intelligence': {'clv': False, 'churn': False, 'segmentation': False},
            'financial_forecasting': {'revenue': False, 'cash_flow': False},
            'inventory_optimization': {'stock_levels': False, 'stockout_prediction': False},
            'errors': []
        }
    
    def setup_test_environment(self):
        """Configurar entorno de prueba con datos mínimos"""
        try:
            # Obtener o crear company de prueba
            self.company = Company.objects.filter(name__icontains='test').first()
            if not self.company:
                self.company = Company.objects.first()
            
            if not self.company:
                print("❌ No hay companies en la base de datos")
                return False
            
            print(f"✅ Usando company: {self.company.name}")
            
            # Verificar datos mínimos
            products_count = Product.objects.filter(company=self.company).count()
            sales_count = Sale.objects.filter(product__company=self.company).count()
            customers_count = Customer.objects.count()  # Customer no tiene campo company
            
            print(f"📊 Datos disponibles:")
            print(f"   - Productos: {products_count}")
            print(f"   - Ventas: {sales_count}")
            print(f"   - Clientes: {customers_count}")
            
            # Si no hay suficientes datos, crear datos de prueba
            if products_count == 0 or sales_count < 10:
                print("🔧 Creando datos de prueba...")
                try:
                    self._create_test_data()
                    
                    # Verificar nuevamente
                    products_count = Product.objects.filter(company=self.company).count()
                    sales_count = Sale.objects.filter(product__company=self.company).count()
                    customers_count = Customer.objects.count()  # Customer no tiene campo company
                    
                    print(f"📊 Datos después de creación:")
                    print(f"   - Productos: {products_count}")
                    print(f"   - Ventas: {sales_count}")
                    print(f"   - Clientes: {customers_count}")
                except Exception as e:
                    print(f"❌ Error creando datos de prueba: {str(e)}")
                    self.test_results['errors'].append(f"Data creation error: {str(e)}")
                    return False
            
            final_check = products_count > 0 and sales_count > 10
            print(f"✅ Check final: productos={products_count > 0}, ventas={sales_count > 10}")
            return final_check
            
        except Exception as e:
            self.test_results['errors'].append(f"Setup error: {str(e)}")
            return False
    
    def _create_test_data(self):
        """Crear datos de prueba mínimos para ML"""
        from django.contrib.auth.models import User
        
        # Crear categoría de prueba
        category, _ = Category.objects.get_or_create(
            name='Test Category',
            defaults={'description': 'Categoría de prueba para ML'}
        )
        
        # Crear productos de prueba
        products = []
        for i in range(3):
            product, created = Product.objects.get_or_create(
                name=f'Producto Test {i+1}',
                company=self.company,
                defaults={
                    'description': f'Producto de prueba {i+1}',
                    'category': category,
                    'price': Decimal('100.00'),
                    'stock_quantity': 100,
                    'minimum_stock': 10
                }
            )
            products.append(product)
        
        # Crear clientes de prueba
        customers = []
        for i in range(5):
            customer, created = Customer.objects.get_or_create(
                name=f'Cliente Test {i+1}',
                defaults={
                    'email': f'test{i+1}@example.com',
                    'phone': f'123456789{i}',
                    'is_active': True
                }
            )
            customers.append(customer)
        
        # Crear ventas de prueba (últimos 90 días)
        from django.utils import timezone
        import random
        
        start_date = timezone.now() - timedelta(days=90)
        
        for day in range(90):
            current_date = start_date + timedelta(days=day)
            
            # Crear 1-5 ventas por día
            num_sales = random.randint(1, 5)
            
            for _ in range(num_sales):
                product = random.choice(products)
                customer = random.choice(customers)
                quantity = random.randint(1, 10)
                
                Sale.objects.get_or_create(
                    product=product,
                    customer=customer,
                    sale_date=current_date.date(),
                    quantity=quantity,
                    defaults={
                        'unit_price': product.price,
                        'total_amount': product.price * quantity
                    }
                )
        
        print("   ✅ Datos de prueba creados exitosamente")
    
    def test_ml_algorithms(self):
        """Probar algoritmos ML básicos"""
        print("\n🤖 TESTING ML ALGORITHMS...")
        
        try:
            # Crear modelo de prueba para cada algoritmo
            algorithms = ['prophet', 'arima', 'randomforest']
            
            for algorithm in algorithms:
                print(f"\n   Testing {algorithm.upper()}...")
                
                try:
                    # Crear modelo
                    model = ForecastModel.objects.create(
                        company=self.company,
                        name=f'Test {algorithm} Model',
                        model_type=algorithm,
                        status='training'
                    )
                    
                    # Entrenar modelo
                    result = training_service.train_model(model)
                    
                    if result['success']:
                        print(f"   ✅ {algorithm}: Entrenamiento exitoso")
                        
                        # Probar predicción
                        prediction_result = training_service.generate_predictions(model, periods=7)
                        
                        if prediction_result['success']:
                            print(f"   ✅ {algorithm}: Predicción exitosa")
                            self.test_results['ml_algorithms'][algorithm] = True
                        else:
                            print(f"   ❌ {algorithm}: Error en predicción - {prediction_result.get('error')}")
                    else:
                        print(f"   ❌ {algorithm}: Error en entrenamiento - {result.get('error')}")
                        
                except Exception as e:
                    print(f"   ❌ {algorithm}: Exception - {str(e)}")
                    self.test_results['errors'].append(f"{algorithm} error: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Error general en ML algorithms: {str(e)}")
            self.test_results['errors'].append(f"ML algorithms error: {str(e)}")
    
    def test_customer_intelligence(self):
        """Probar Customer Intelligence"""
        print("\n👥 TESTING CUSTOMER INTELLIGENCE...")
        
        try:
            service = CustomerIntelligenceService(self.company)
            
            # Test CLV
            try:
                clv_results = service.calculate_customer_lifetime_value()
                if clv_results:
                    print(f"   ✅ CLV: Calculado para {len(clv_results)} clientes")
                    self.test_results['customer_intelligence']['clv'] = True
                else:
                    print("   ⚠️ CLV: No hay resultados (normal si no hay suficientes datos)")
            except Exception as e:
                print(f"   ❌ CLV: Error - {str(e)}")
                self.test_results['errors'].append(f"CLV error: {str(e)}")
            
            # Test Churn Prediction
            try:
                churn_results = service.predict_customer_churn()
                if churn_results:
                    print(f"   ✅ Churn: Predicción para {len(churn_results)} clientes")
                    self.test_results['customer_intelligence']['churn'] = True
                else:
                    print("   ⚠️ Churn: No hay resultados (normal si no hay suficientes datos)")
            except Exception as e:
                print(f"   ❌ Churn: Error - {str(e)}")
                self.test_results['errors'].append(f"Churn error: {str(e)}")
                
        except Exception as e:
            print(f"❌ Error general en Customer Intelligence: {str(e)}")
            self.test_results['errors'].append(f"Customer Intelligence error: {str(e)}")
    
    def test_financial_forecasting(self):
        """Probar Financial Forecasting"""
        print("\n💰 TESTING FINANCIAL FORECASTING...")
        
        try:
            service = FinancialForecastingService(self.company)
            
            # Test Revenue Forecasting
            try:
                revenue_model = service.create_revenue_forecast_model()
                if revenue_model:
                    print("   ✅ Revenue: Modelo creado exitosamente")
                    self.test_results['financial_forecasting']['revenue'] = True
                else:
                    print("   ❌ Revenue: No se pudo crear modelo")
            except Exception as e:
                print(f"   ❌ Revenue: Error - {str(e)}")
                self.test_results['errors'].append(f"Revenue forecasting error: {str(e)}")
            
            # Test Cash Flow
            try:
                cash_flow_result = service.predict_cash_flow(days_ahead=30)
                if cash_flow_result and 'predictions' in cash_flow_result:
                    print("   ✅ Cash Flow: Predicción exitosa")
                    self.test_results['financial_forecasting']['cash_flow'] = True
                else:
                    print("   ❌ Cash Flow: No hay predicciones")
            except Exception as e:
                print(f"   ❌ Cash Flow: Error - {str(e)}")
                self.test_results['errors'].append(f"Cash flow error: {str(e)}")
                
        except Exception as e:
            print(f"❌ Error general en Financial Forecasting: {str(e)}")
            self.test_results['errors'].append(f"Financial Forecasting error: {str(e)}")
    
    def test_direct_ml_service(self):
        """Probar MLAlgorithmService directamente"""
        print("\n🧠 TESTING DIRECT ML SERVICE...")
        
        try:
            # Crear datos de prueba simples
            dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
            values = np.random.randint(10, 100, len(dates)) + np.sin(np.arange(len(dates)) * 0.1) * 20
            
            test_data = pd.DataFrame({
                'ds': dates,
                'y': values
            })
            
            ml_service = MLAlgorithmService()
            
            # Test Prophet directo
            try:
                prophet_data = ml_service.prepare_data(test_data, algorithm='prophet')
                prophet_model = ml_service.train_prophet(prophet_data)
                prophet_predictions = ml_service.predict(prophet_model, periods=30, algorithm='prophet')
                
                if len(prophet_predictions) > 0:
                    print("   ✅ Prophet directo: Funcional")
                else:
                    print("   ❌ Prophet directo: Sin predicciones")
                    
            except Exception as e:
                print(f"   ❌ Prophet directo: Error - {str(e)}")
            
            # Test Random Forest directo
            try:
                rf_data = ml_service.prepare_data(test_data, algorithm='randomforest')
                rf_model = ml_service.train_random_forest(rf_data)
                rf_predictions = ml_service.predict(rf_model, periods=30, algorithm='randomforest', data=rf_data)
                
                if len(rf_predictions) > 0:
                    print("   ✅ Random Forest directo: Funcional")
                else:
                    print("   ❌ Random Forest directo: Sin predicciones")
                    
            except Exception as e:
                print(f"   ❌ Random Forest directo: Error - {str(e)}")
                
        except Exception as e:
            print(f"❌ Error en ML Service directo: {str(e)}")
    
    def generate_report(self):
        """Generar reporte final"""
        print("\n" + "="*60)
        print("📋 REPORTE FINAL DE FUNCIONALIDAD ML")
        print("="*60)
        
        # ML Algorithms
        ml_success = sum(self.test_results['ml_algorithms'].values())
        print(f"\n🤖 ML ALGORITHMS ({ml_success}/3):")
        for alg, status in self.test_results['ml_algorithms'].items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {alg.upper()}")
        
        # Customer Intelligence
        ci_success = sum(self.test_results['customer_intelligence'].values())
        print(f"\n👥 CUSTOMER INTELLIGENCE ({ci_success}/3):")
        for feature, status in self.test_results['customer_intelligence'].items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {feature.upper()}")
        
        # Financial Forecasting
        ff_success = sum(self.test_results['financial_forecasting'].values())
        print(f"\n💰 FINANCIAL FORECASTING ({ff_success}/2):")
        for feature, status in self.test_results['financial_forecasting'].items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {feature.upper()}")
        
        # Calcular porcentaje total
        total_tests = (
            len(self.test_results['ml_algorithms']) +
            len(self.test_results['customer_intelligence']) +
            len(self.test_results['financial_forecasting'])
        )
        total_success = ml_success + ci_success + ff_success
        percentage = (total_success / total_tests) * 100
        
        print(f"\n📊 FUNCIONALIDAD TOTAL: {total_success}/{total_tests} ({percentage:.1f}%)")
        
        if percentage >= 80:
            print("🎉 SISTEMA ML COMPLETAMENTE FUNCIONAL!")
        elif percentage >= 60:
            print("⚠️ Sistema ML parcialmente funcional - revisar errores")
        else:
            print("❌ Sistema ML necesita trabajo significativo")
        
        # Mostrar errores si los hay
        if self.test_results['errors']:
            print(f"\n❌ ERRORES ENCONTRADOS ({len(self.test_results['errors'])}):")
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"   {i}. {error}")
        
        print("\n" + "="*60)

def main():
    print("🔬 INICIANDO PRUEBA COMPREHENSIVA DEL SISTEMA ML")
    print("="*60)
    
    tester = MLSystemTester()
    
    # Setup
    if not tester.setup_test_environment():
        print("❌ No se pudo configurar el entorno de prueba")
        if tester.test_results['errors']:
            print("🔍 Errores de setup:")
            for error in tester.test_results['errors']:
                print(f"   - {error}")
        return
    
    # Ejecutar pruebas
    tester.test_direct_ml_service()
    tester.test_ml_algorithms()
    tester.test_customer_intelligence() 
    tester.test_financial_forecasting()
    
    # Generar reporte
    tester.generate_report()

if __name__ == "__main__":
    main()
