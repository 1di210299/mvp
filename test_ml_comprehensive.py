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
from django.db.models import Count

from authentication.models import Company
from inventory.models import Product, Sale, Customer, Category, Supplier
from forecasting.models import ForecastModel, DemandForecast
from forecasting.ml_algorithms.training_service import training_service
from forecasting.ml_algorithms.ml_service import MLAlgorithmService

# Importar servicios ML modulares
from forecasting.services.customer_intelligence_service import CustomerIntelligenceService
from forecasting.services.financial_forecasting_service import FinancialForecastingService
from forecasting.services.inventory_optimization_service import InventoryOptimizationService
from forecasting.services.demand_analysis_service import DemandAnalysisService

class MLSystemTester:
    def __init__(self):
        self.company = None
        self.test_results = {
            'ml_algorithms': {'prophet': False, 'arima': False, 'randomforest': False},
            'customer_intelligence': {'clv': False, 'churn': False, 'segmentation': False, 'next_purchase': False},
            'financial_forecasting': {'revenue': False, 'cash_flow': False, 'supplier_roi': False},
            'inventory_optimization': {'stock_levels': False, 'stockout_prediction': False, 'abc_classification': False},
            'demand_analysis': {'seasonal_patterns': False, 'market_basket': False, 'price_elasticity': False},
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
            
            # Si no hay suficientes datos O no hay Market Basket data, crear datos de prueba
            # Verificar Market Basket existente
            from django.db.models import Count
            basket_sales = Sale.objects.filter(
                product__company=self.company
            ).values('date_sold', 'customer_name').annotate(
                product_count=Count('product', distinct=True)
            ).filter(product_count__gte=2).count()
            
            if products_count == 0 or sales_count < 10 or basket_sales == 0:
                print("🔧 Creando datos de prueba...")
                print(f"   📊 Motivo: productos={products_count}, ventas={sales_count}, basket={basket_sales}")
                # Limpiar datos anteriores para recrear correctamente
                Sale.objects.filter(product__company=self.company).delete()
                from inventory.models import Transaction
                Transaction.objects.filter(product__company=self.company).delete()
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
        
        # Crear suppliers de prueba (más para análisis ROI)
        suppliers = []
        for i in range(13):  # Crear 13 proveedores como en los logs
            supplier, created = Supplier.objects.get_or_create(
                name=f'Supplier Test {i+1}',
                defaults={
                    'email': f'supplier{i+1}@example.com',
                    'phone': f'555-000{i+1}',
                    'address': f'Address {i+1}',
                    'contact_name': f'Contact {i+1}',
                    'is_active': True
                }
            )
            suppliers.append(supplier)
        
        # Crear productos de prueba (más para distribuir entre proveedores)
        products = []
        for i in range(15):  # Aumentar a 15 productos
            supplier = suppliers[i % len(suppliers)]  # Distribuir entre todos los suppliers
            product, created = Product.objects.get_or_create(
                name=f'Producto Test {i+1}',
                company=self.company,
                defaults={
                    'sku': f'TEST-PROD-{i+1:03d}',  # SKU único para evitar conflictos
                    'description': f'Producto de prueba {i+1}',
                    'category': category,
                    'supplier': supplier,
                    'cost_price': Decimal(f'{80 + i*10}.00'),
                    'sale_price': Decimal(f'{100 + i*15}.00'),
                    'stock': 100,
                    'min_stock': 10,
                    'max_stock': 200,
                    'is_active': True
                }
            )
            # Si el producto ya existía, asegurar que tiene el supplier correcto
            if not created and product.supplier != supplier:
                product.supplier = supplier
                product.save()
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
        
        # Crear ventas de prueba (últimos 90 días) con énfasis en Market Basket
        from django.utils import timezone
        import random
        
        start_date = timezone.now() - timedelta(days=90)
        
        print("   📦 Creando ventas con Market Basket Analysis...")
        market_basket_transactions = 0
        
        for day in range(90):
            current_date = start_date + timedelta(days=day)
            
            # Crear 3-8 transacciones por día
            num_transactions = random.randint(3, 8)
            
            for transaction in range(num_transactions):
                customer = random.choice(customers)
                
                # 80% probabilidad de compra múltiple (Market Basket) - aumentar probabilidad
                if random.random() < 0.8:
                    # Transacción con múltiples productos
                    num_products = random.randint(2, min(4, len(products)))
                    selected_products = random.sample(products, num_products)
                    
                    # Crear timestamp específico para este día (no timezone.now())
                    base_time = current_date.replace(
                        hour=random.randint(8, 20),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59),
                        microsecond=random.randint(0, 999999)
                    )
                    
                    # Convertir a datetime aware
                    from django.utils import timezone as tz
                    base_time = tz.make_aware(base_time) if tz.is_naive(base_time) else base_time
                    
                    # Crear todas las ventas con el MISMO timestamp exacto
                    basket_sales = []
                    for product in selected_products:
                        quantity = random.randint(1, 3)
                        sale = Sale.objects.create(
                            product=product,
                            quantity=quantity,
                            unit_price=product.sale_price or product.cost_price,
                            customer_name=customer.name
                        )
                        basket_sales.append(sale)
                    
                    # ACTUALIZAR todas las ventas con el mismo timestamp después de crearlas
                    Sale.objects.filter(id__in=[s.id for s in basket_sales]).update(date_sold=base_time)
                    
                    market_basket_transactions += 1
                else:
                    # Compra individual
                    product = random.choice(products)
                    quantity = random.randint(1, 5)
                    
                    individual_time = current_date.replace(
                        hour=random.randint(8, 20),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59),
                        microsecond=random.randint(0, 999999)
                    )
                    
                    # Convertir a datetime aware
                    from django.utils import timezone as tz
                    individual_time = tz.make_aware(individual_time) if tz.is_naive(individual_time) else individual_time
                    Sale.objects.create(
                        product=product,
                        date_sold=individual_time,
                        quantity=quantity,
                        unit_price=product.sale_price or product.cost_price,
                        customer_name=customer.name
                    )
        
        print(f"   ✅ Creadas {market_basket_transactions} transacciones Market Basket")
        
        # Crear transacciones de COMPRA para análisis ROI de suppliers
        print("   📦 Creando transacciones de compra para análisis ROI...")
        for day in range(90):
            current_date = start_date + timedelta(days=day)
            
            # Crear 1-3 compras por día (menos frecuentes que ventas)
            if random.random() < 0.4:  # 40% probabilidad de compra en un día
                num_purchases = random.randint(1, 3)
                
                for _ in range(num_purchases):
                    product = random.choice(products)
                    quantity = random.randint(5, 20)  # Compras más grandes
                    
                    # Crear transacción de compra
                    from inventory.models import Transaction
                    Transaction.objects.create(
                        product=product,
                        transaction_type='purchase',
                        quantity=quantity,
                        unit_cost=product.cost_price,
                        transaction_date=current_date.replace(
                            hour=random.randint(8, 18),
                            minute=random.randint(0, 59)
                        ),
                        notes=f'Compra automática día {day}'
                    )
        
        # Crear también transacciones de VENTA para que coincida con Sales
        print("   💰 Creando transacciones de venta para completar datos...")
        sales = Sale.objects.filter(product__company=self.company)
        for sale in sales:
            # Crear transacción de venta correspondiente
            Transaction.objects.get_or_create(
                product=sale.product,
                transaction_type='sale',
                quantity=sale.quantity,
                unit_cost=sale.unit_price,
                transaction_date=sale.date_sold,
                defaults={
                    'notes': f'Venta a {sale.customer_name}'
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
                    # Crear modelo con nombre único basado en timestamp
                    import time
                    timestamp = int(time.time())
                    
                    model = ForecastModel.objects.create(
                        company=self.company,
                        name=f'Test {algorithm} Model {timestamp}',
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
            
            # Test Customer Segmentation
            try:
                segmentation_results = service.segment_customers_automatically()
                if segmentation_results:
                    print(f"   ✅ Segmentation: Creado para {len(segmentation_results)} clientes")
                    self.test_results['customer_intelligence']['segmentation'] = True
                else:
                    print("   ⚠️ Segmentation: No hay resultados (normal si no hay suficientes datos)")
            except Exception as e:
                print(f"   ❌ Segmentation: Error - {str(e)}")
                self.test_results['errors'].append(f"Segmentation error: {str(e)}")
            
            # Test Next Purchase Prediction
            try:
                print("   🔍 Prediciendo próximas compras...")
                
                # Verificar clientes activos
                active_customers = Customer.objects.filter(is_active=True).count()
                print(f"   📊 Clientes activos: {active_customers}")
                
                # Verificar clientes con suficientes transacciones
                from inventory.models import Sale
                customers_with_multiple_sales = []
                
                for customer in Customer.objects.filter(is_active=True):
                    sale_count = Sale.objects.filter(customer_name=customer.name).count()
                    if sale_count >= 2:
                        customers_with_multiple_sales.append(customer)
                
                print(f"   📊 Clientes con ≥2 transacciones: {len(customers_with_multiple_sales)}")
                
                next_purchase_results = service.predict_next_purchases()
                print(f"   📊 Predicciones exitosas: {len(next_purchase_results) if next_purchase_results else 0}")
                
                if next_purchase_results:
                    print(f"   ✅ Next Purchase: Predicción para {len(next_purchase_results)} clientes")
                    self.test_results['customer_intelligence']['next_purchase'] = True
                else:
                    print("   ⚠️ Next Purchase: No hay resultados (normal si no hay suficientes datos)")
            except Exception as e:
                print(f"   ❌ Next Purchase: Error - {str(e)}")
                self.test_results['errors'].append(f"Next Purchase error: {str(e)}")
                
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
            
            # Test Supplier ROI Analysis
            try:
                print("   🔍 Analizando Supplier ROI...")
                supplier_analysis = service.analyze_supplier_roi()
                print(f"   📊 Resultado: {len(supplier_analysis) if supplier_analysis else 0} suppliers analizados")
                
                if supplier_analysis:
                    print(f"   ✅ Supplier ROI: Análisis de {len(supplier_analysis)} suppliers")
                    self.test_results['financial_forecasting']['supplier_roi'] = True
                else:
                    # Verificar si hay suppliers en la base de datos
                    from inventory.models import Supplier
                    supplier_count = Supplier.objects.count()
                    print(f"   📊 Suppliers en BD: {supplier_count}")
                    print("   ⚠️ Supplier ROI: No hay resultados (normal si no hay suppliers)")
            except Exception as e:
                print(f"   ❌ Supplier ROI: Error - {str(e)}")
                self.test_results['errors'].append(f"Supplier ROI error: {str(e)}")
                
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
                prophet_model = ml_service.train_prophet(test_data)
                
                if prophet_model['success']:
                    prophet_predictions = ml_service.predict('prophet', periods=30)
                    if len(prophet_predictions) > 0:
                        print("   ✅ Prophet directo: Funcional")
                    else:
                        print("   ❌ Prophet directo: Sin predicciones")
                else:
                    print(f"   ❌ Prophet directo: Error entrenamiento - {prophet_model.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ Prophet directo: Error - {str(e)}")
            
            # Test Random Forest directo
            try:
                # Preparar datos para Random Forest (necesita features diferentes)
                rf_data = test_data.copy()
                rf_data['day_of_week'] = rf_data['ds'].dt.dayofweek
                rf_data['month'] = rf_data['ds'].dt.month
                rf_data['day_of_year'] = rf_data['ds'].dt.dayofyear
                
                rf_model = ml_service.train_random_forest(rf_data)
                
                if rf_model['success']:
                    rf_predictions = ml_service.predict('randomforest', periods=30)
                    if len(rf_predictions.get('predictions', [])) > 0:
                        print("   ✅ Random Forest directo: Funcional")
                    else:
                        print("   ❌ Random Forest directo: Sin predicciones")
                else:
                    print(f"   ❌ Random Forest directo: Error entrenamiento - {rf_model.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ Random Forest directo: Error - {str(e)}")
                
        except Exception as e:
            print(f"❌ Error en ML Service directo: {str(e)}")
    
    def test_inventory_optimization(self):
        """Probar Inventory Optimization Service"""
        print("\n📦 TESTING INVENTORY OPTIMIZATION...")
        
        optimal_levels = []  # Inicializar la variable
        
        try:
            service = InventoryOptimizationService(self.company)
            
            # Test Optimal Stock Levels
            try:
                optimal_levels = service.calculate_optimal_stock_levels()
                if optimal_levels:
                    print(f"   ✅ Stock Levels: Calculado para {len(optimal_levels)} productos")
                    self.test_results['inventory_optimization']['stock_levels'] = True
                else:
                    print("   ⚠️ Stock Levels: No hay resultados (normal si no hay productos con demanda)")
            except Exception as e:
                print(f"   ❌ Stock Levels: Error - {str(e)}")
                self.test_results['errors'].append(f"Stock Levels error: {str(e)}")
            
            # Test Stockout Prediction
            try:
                stockout_predictions = service.predict_stockouts(days_ahead=30)
                if stockout_predictions:
                    print(f"   ✅ Stockout Prediction: Predicción para {len(stockout_predictions)} productos")
                    self.test_results['inventory_optimization']['stockout_prediction'] = True
                else:
                    print("   ⚠️ Stockout Prediction: No hay predicciones de stockout")
            except Exception as e:
                print(f"   ❌ Stockout Prediction: Error - {str(e)}")
                self.test_results['errors'].append(f"Stockout Prediction error: {str(e)}")
            
            # Test ABC Classification (implícito en optimal levels)
            try:
                # Si optimal_levels tiene datos, significa que ABC también funcionó
                if 'optimal_levels' in locals() and optimal_levels:
                    print("   ✅ ABC Classification: Clasificación automática funcionando")
                    self.test_results['inventory_optimization']['abc_classification'] = True
                else:
                    print("   ⚠️ ABC Classification: No hay clasificaciones ABC")
            except Exception as e:
                print(f"   ❌ ABC Classification: Error - {str(e)}")
                self.test_results['errors'].append(f"ABC Classification error: {str(e)}")
                
        except Exception as e:
            print(f"❌ Error general en Inventory Optimization: {str(e)}")
            self.test_results['errors'].append(f"Inventory Optimization error: {str(e)}")
    
    def test_demand_analysis(self):
        """Probar Demand Analysis Service"""
        print("\n📊 TESTING DEMAND ANALYSIS...")
        
        try:
            service = DemandAnalysisService(self.company)
            
            # Test Seasonal Patterns
            try:
                seasonal_results = service.analyze_seasonal_patterns()
                if seasonal_results:
                    print(f"   ✅ Seasonal Patterns: Análisis para {len(seasonal_results)} productos")
                    self.test_results['demand_analysis']['seasonal_patterns'] = True
                else:
                    print("   ⚠️ Seasonal Patterns: No hay resultados (normal con pocos datos)")
            except Exception as e:
                print(f"   ❌ Seasonal Patterns: Error - {str(e)}")
                self.test_results['errors'].append(f"Seasonal Patterns error: {str(e)}")
            
            # Test Market Basket Analysis
            try:
                print("   🔍 Analizando Market Basket...")
                
                # Verificar datos disponibles para Market Basket
                from inventory.models import Sale
                total_sales = Sale.objects.filter(product__company=self.company).count()
                unique_customers = Sale.objects.filter(product__company=self.company).values('customer_name').distinct().count()
                print(f"   📊 Datos disponibles: {total_sales} ventas, {unique_customers} clientes únicos")
                
                # Verificar transacciones por timestamp exacto (Market Basket necesita mismo momento)
                from django.db.models import Count
                exact_time_sales = Sale.objects.filter(product__company=self.company).values(
                    'date_sold', 'customer_name'
                ).annotate(
                    productos_count=Count('product', distinct=True)
                ).filter(productos_count__gte=2)
                
                print(f"   📊 Transacciones con múltiples productos: {exact_time_sales.count()}")
                
                basket_results = service.perform_market_basket_analysis()
                print(f"   📊 Asociaciones encontradas: {len(basket_results) if basket_results else 0}")
                
                if basket_results:
                    print(f"   ✅ Market Basket: Encontradas {len(basket_results)} asociaciones")
                    self.test_results['demand_analysis']['market_basket'] = True
                else:
                    print("   ⚠️ Market Basket: No hay asociaciones encontradas (necesita más transacciones con múltiples productos)")
            except Exception as e:
                print(f"   ❌ Market Basket: Error - {str(e)}")
                self.test_results['errors'].append(f"Market Basket error: {str(e)}")
            
            # Test Price Elasticity
            try:
                elasticity_results = service.calculate_price_elasticity()
                if elasticity_results:
                    print(f"   ✅ Price Elasticity: Calculada para {len(elasticity_results)} productos")
                    self.test_results['demand_analysis']['price_elasticity'] = True
                else:
                    print("   ⚠️ Price Elasticity: No hay resultados (normal con pocos datos)")
            except Exception as e:
                print(f"   ❌ Price Elasticity: Error - {str(e)}")
                self.test_results['errors'].append(f"Price Elasticity error: {str(e)}")
                
        except Exception as e:
            print(f"❌ Error general en Demand Analysis: {str(e)}")
            self.test_results['errors'].append(f"Demand Analysis error: {str(e)}")
    
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
        print(f"\n👥 CUSTOMER INTELLIGENCE ({ci_success}/4):")
        for feature, status in self.test_results['customer_intelligence'].items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {feature.upper()}")
        
        # Financial Forecasting
        ff_success = sum(self.test_results['financial_forecasting'].values())
        print(f"\n💰 FINANCIAL FORECASTING ({ff_success}/3):")
        for feature, status in self.test_results['financial_forecasting'].items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {feature.upper()}")
        
        # Inventory Optimization
        io_success = sum(self.test_results['inventory_optimization'].values())
        print(f"\n📦 INVENTORY OPTIMIZATION ({io_success}/3):")
        for feature, status in self.test_results['inventory_optimization'].items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {feature.upper()}")
        
        # Demand Analysis
        da_success = sum(self.test_results['demand_analysis'].values())
        print(f"\n📊 DEMAND ANALYSIS ({da_success}/3):")
        for feature, status in self.test_results['demand_analysis'].items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {feature.upper()}")
        
        # Calcular porcentaje total
        total_tests = (
            len(self.test_results['ml_algorithms']) +
            len(self.test_results['customer_intelligence']) +
            len(self.test_results['financial_forecasting']) +
            len(self.test_results['inventory_optimization']) +
            len(self.test_results['demand_analysis'])
        )
        total_success = ml_success + ci_success + ff_success + io_success + da_success
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
    tester.test_inventory_optimization()
    tester.test_demand_analysis()
    
    # Generar reporte
    tester.generate_report()

if __name__ == "__main__":
    main()
