#!/usr/bin/env python
"""
Script para probar las correcciones implementadas en el sistema ML
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

import logging
from datetime import datetime, timedelta
from django.utils import timezone

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_lstm_fix():
    """Probar corrección del problema LSTM"""
    print("🔧 Probando corrección LSTM...")
    
    try:
        from forecasting.ml_algorithms.lstm_forecaster import LSTMForecaster
        
        # Crear instancia
        forecaster = LSTMForecaster()
        print("✅ LSTM forecaster creado exitosamente")
        
        # Simular datos de entrenamiento
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'quantity': np.random.randint(1, 100, 100)
        })
        data.set_index('date', inplace=True)
        
        print(f"📊 Datos de prueba: {len(data)} observaciones")
        
        # Entrenar modelo - PRUEBA CONTUNDENTE
        forecaster.fit(data, target_column='quantity')
        print("✅ Modelo LSTM entrenado exitosamente")
        
        # Verificar que el modelo está correctamente entrenado
        assert forecaster.is_fitted, "El modelo no está marcado como entrenado"
        assert hasattr(forecaster, 'model'), "El modelo no tiene el atributo 'model'"
        assert hasattr(forecaster, 'metrics'), "El modelo no tiene métricas"
        assert 'mae' in forecaster.metrics, "Las métricas no incluyen MAE"
        assert 'r2' in forecaster.metrics, "Las métricas no incluyen R²"
        
        # Probar predicción
        predictions = forecaster.predict(periods=7)
        print(f"✅ Predicciones generadas: {len(predictions)} períodos")
        
        # Validar que las predicciones son válidas
        assert len(predictions) == 7, "No se generaron 7 predicciones"
        assert 'date' in predictions.columns, "Las predicciones no tienen columna 'date'"
        assert 'predicted_value' in predictions.columns, "Las predicciones no tienen 'predicted_value'"
        assert 'lower_bound' in predictions.columns, "Las predicciones no tienen 'lower_bound'"
        assert 'upper_bound' in predictions.columns, "Las predicciones no tienen 'upper_bound'"
        
        # Validar valores de predicción
        for i, row in predictions.iterrows():
            assert row['predicted_value'] >= 0, f"Predicción {i} tiene valor negativo"
            assert row['lower_bound'] >= 0, f"Predicción {i} tiene lower_bound negativo"
            assert row['upper_bound'] >= row['lower_bound'], f"Predicción {i} tiene upper_bound < lower_bound"
            print(f"  📊 {row['date'].strftime('%Y-%m-%d')}: {row['predicted_value']:.2f} [{row['lower_bound']:.2f}, {row['upper_bound']:.2f}]")
        
        # Probar guardar modelo - PRUEBA CONTUNDENTE DE SERIALIZACIÓN
        test_path = "/tmp/test_lstm_model.joblib"
        if forecaster.save_model(test_path):
            print("✅ Modelo guardado exitosamente")
            
            # Probar cargar modelo - PRUEBA CONTUNDENTE DE DESERIALIZACIÓN
            new_forecaster = LSTMForecaster()
            if new_forecaster.load_model(test_path):
                print("✅ Modelo cargado exitosamente")
                
                # Verificar que el modelo cargado funciona
                assert new_forecaster.is_fitted, "El modelo cargado no está marcado como entrenado"
                new_predictions = new_forecaster.predict(periods=3)
                assert len(new_predictions) == 3, "El modelo cargado no genera predicciones correctas"
                print("✅ Modelo cargado genera predicciones válidas")
                
            else:
                print("❌ Error cargando modelo")
                return False
        else:
            print("❌ Error guardando modelo")
            return False
        
        print("✅ Todas las pruebas LSTM son válidas")
            
    except Exception as e:
        print(f"❌ Error en prueba LSTM: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_random_forest_fix():
    """Probar corrección del problema RandomForest"""
    print("\n🔧 Probando corrección RandomForest...")
    
    try:
        from forecasting.ml_algorithms.random_forest_forecaster import RandomForestForecaster
        
        # Crear instancia
        forecaster = RandomForestForecaster()
        print("✅ RandomForest forecaster creado exitosamente")
        
        # Simular datos con valores NaN para probar la corrección
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'quantity': np.random.randint(1, 100, 100)
        })
        
        # Introducir algunos valores NaN intencionalmente
        data.loc[5:10, 'quantity'] = np.nan
        data.loc[20:25, 'quantity'] = np.inf
        data.loc[30:35, 'quantity'] = -np.inf
        
        data.set_index('date', inplace=True)
        
        print(f"📊 Datos de prueba: {len(data)} observaciones (con NaN/inf)")
        
        # Verificar que hay valores problemáticos antes del entrenamiento
        nan_count = data['quantity'].isna().sum()
        inf_count = np.isinf(data['quantity']).sum()
        print(f"🔍 Valores problemáticos: {nan_count} NaN, {inf_count} infinitos")
        
        # Entrenar modelo - ESTA ES LA PRUEBA CONTUNDENTE
        forecaster.fit(data, target_column='quantity')
        print("✅ Modelo RandomForest entrenado exitosamente")
        
        # Verificar que el modelo está correctamente entrenado
        assert forecaster.is_fitted, "El modelo no está marcado como entrenado"
        assert hasattr(forecaster, 'model'), "El modelo no tiene el atributo 'model'"
        assert hasattr(forecaster, 'training_data'), "El modelo no tiene datos de entrenamiento"
        assert forecaster.training_data is not None, "Los datos de entrenamiento son None"
        
        # Probar predicción
        predictions = forecaster.predict(periods=7)
        print(f"✅ Predicciones generadas: {len(predictions['forecast'])} períodos")
        
        # Validar que las predicciones son válidas
        assert len(predictions['forecast']) == 7, "No se generaron 7 predicciones"
        for i, pred in enumerate(predictions['forecast']):
            assert 'predicted_value' in pred, f"Predicción {i} no tiene 'predicted_value'"
            assert 'lower_bound' in pred, f"Predicción {i} no tiene 'lower_bound'"
            assert 'upper_bound' in pred, f"Predicción {i} no tiene 'upper_bound'"
            assert pred['predicted_value'] >= 0, f"Predicción {i} tiene valor negativo"
            assert pred['lower_bound'] >= 0, f"Predicción {i} tiene lower_bound negativo"
            assert pred['upper_bound'] >= pred['lower_bound'], f"Predicción {i} tiene upper_bound < lower_bound"
            print(f"  📊 Predicción {i+1}: {pred['predicted_value']:.2f} [{pred['lower_bound']:.2f}, {pred['upper_bound']:.2f}]")
        
        print("✅ Todas las predicciones RandomForest son válidas")
        
    except Exception as e:
        print(f"❌ Error en prueba RandomForest: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_financial_predictions_fix():
    """Probar corrección del problema de predicciones financieras"""
    print("\n🔧 Probando corrección de predicciones financieras...")
    
    try:
        from forecasting.services.financial_forecasting_service import FinancialForecastingService
        from authentication.models import Company
        
        # Crear o obtener empresa de prueba con nombre único
        import uuid
        company_name = f"Test Company Fix {uuid.uuid4().hex[:8]}"
        
        company, created = Company.objects.get_or_create(
            name=company_name,
            defaults={
                'email': f'test{uuid.uuid4().hex[:8]}@example.com',
                'phone': '123456789',
                'address': 'Test Address',
                'ruc': f'12345678{uuid.uuid4().hex[:3]}'  # RUC único
            }
        )
        
        service = FinancialForecastingService(company)
        print("✅ Servicio financiero creado exitosamente")
        
        # Probar crear modelo
        model = service.create_revenue_forecast_model()
        print("✅ Modelo financiero creado exitosamente")
        
        # Probar obtener datos históricos
        historical_data = service._get_financial_historical_data(model, 'monthly')
        print(f"✅ Datos históricos obtenidos: {len(historical_data)} registros")
        
        # Probar entrenamiento del modelo
        trained_model = service._train_revenue_model(historical_data)
        print("✅ Modelo entrenado exitosamente")
        
        # Probar predicciones completas - ESTA ES LA PRUEBA CONTUNDENTE
        predictions = service.generate_revenue_predictions(model, period_type='monthly', periods_ahead=3)
        print(f"✅ Predicciones financieras generadas: {len(predictions)} predicciones")
        
        # Validar que las predicciones tienen los datos correctos
        for i, prediction in enumerate(predictions):
            assert prediction.predicted_revenue >= 0, f"Predicción {i} tiene ingresos negativos: {prediction.predicted_revenue}"
            assert prediction.confidence_level > 0, f"Predicción {i} tiene confianza <= 0"
            assert prediction.category_breakdown is not None, f"Predicción {i} no tiene desglose"
            print(f"  📊 Predicción {i+1}: S/ {prediction.predicted_revenue} (confianza: {prediction.confidence_level}%)")
        
        print("✅ Todas las predicciones financieras son válidas")
        
    except Exception as e:
        print(f"❌ Error en prueba financiera: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_customer_clv_fix():
    """Probar corrección del problema CLV"""
    print("\n🔧 Probando corrección de Customer CLV...")
    
    try:
        from forecasting.services.customer_intelligence_service import CustomerIntelligenceService
        from authentication.models import Company
        from inventory.models import Customer, Product, Sale
        
        # Crear o obtener empresa de prueba con nombre único
        import uuid
        company_name = f"Test Company CLV {uuid.uuid4().hex[:8]}"
        
        company, created = Company.objects.get_or_create(
            name=company_name,
            defaults={
                'email': f'test{uuid.uuid4().hex[:8]}@example.com',
                'phone': '123456789',
                'address': 'Test Address',
                'ruc': f'98765432{uuid.uuid4().hex[:3]}'  # RUC único
            }
        )
        
        service = CustomerIntelligenceService(company)
        print("✅ Servicio de inteligencia de clientes creado exitosamente")
        
        # Crear datos de prueba más realistas
        customers_created = []
        products_created = []
        
        # Crear productos de prueba
        for i in range(3):
            product = Product.objects.create(
                name=f"Test Product {i+1} {uuid.uuid4().hex[:6]}",
                sku=f"SKU{i+1}{uuid.uuid4().hex[:6]}",
                company=company,
                sale_price=100.0 + i * 50,
                cost_price=50.0 + i * 25,
                stock=100
            )
            products_created.append(product)
        
        # Crear clientes y ventas de prueba
        for i in range(5):
            customer_name = f"Test Customer {i+1} {uuid.uuid4().hex[:6]}"
            customer = Customer.objects.create(
                name=customer_name,
                email=f'customer{i+1}@test.com',
                phone=f'98765432{i}',
                address=f'Customer Address {i+1}'
            )
            customers_created.append(customer)
            
            # Crear algunas ventas para este cliente
            for j in range(2):
                Sale.objects.create(
                    product=products_created[j % len(products_created)],
                    customer_name=customer.name,
                    quantity=5 + j,
                    unit_price=products_created[j % len(products_created)].sale_price,
                    date_sold=timezone.now().date() - timedelta(days=30 * j)
                )
        
        print(f"✅ Datos de prueba creados: {len(customers_created)} clientes, {len(products_created)} productos")
        
        # Probar CLV - PRUEBA CONTUNDENTE
        clv_results = service.calculate_customer_lifetime_value()
        print(f"✅ Análisis CLV generado: {len(clv_results)} resultados")
        
        # Validar que los resultados son válidos
        assert len(clv_results) > 0, "No se generaron resultados CLV"
        
        for i, clv in enumerate(clv_results):
            assert clv.customer is not None, f"CLV {i} no tiene customer asociado"
            assert clv.predicted_clv >= 0, f"CLV {i} tiene valor negativo"
            assert clv.clv_confidence >= 0, f"CLV {i} tiene confianza negativa"
            assert clv.average_order_value >= 0, f"CLV {i} tiene AOV negativo"
            assert clv.purchase_frequency >= 0, f"CLV {i} tiene frecuencia negativa"
            assert clv.rfm_segment is not None, f"CLV {i} no tiene segmento RFM"
            
            print(f"  📊 Cliente {clv.customer.name}: CLV = S/ {clv.predicted_clv} (confianza: {clv.clv_confidence}%)")
            print(f"       AOV: S/ {clv.average_order_value}, Frecuencia: {clv.purchase_frequency}, Segmento: {clv.rfm_segment}")
        
        # Probar predicción de churn
        churn_predictions = service.predict_customer_churn()
        print(f"✅ Predicciones de churn generadas: {len(churn_predictions)} resultados")
        
        # Validar predicciones de churn
        for i, churn in enumerate(churn_predictions):
            assert churn.customer is not None, f"Churn {i} no tiene customer asociado"
            assert 0 <= churn.churn_probability <= 1, f"Churn {i} tiene probabilidad inválida"
            assert churn.churn_risk_level in ['low', 'medium', 'high', 'unknown'], f"Churn {i} tiene nivel de riesgo inválido"
            
            print(f"  🚨 Cliente {churn.customer.name}: Riesgo = {churn.churn_risk_level} ({churn.churn_probability:.2%})")
        
        print("✅ Todas las predicciones CLV y churn son válidas")
        
    except Exception as e:
        print(f"❌ Error en prueba CLV: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Función principal para ejecutar todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS DE CORRECCIONES ML")
    print("=" * 50)
    
    tests = [
        ("LSTM Fix", test_lstm_fix),
        ("RandomForest Fix", test_random_forest_fix),
        ("Financial Predictions Fix", test_financial_predictions_fix),
        ("Customer CLV Fix", test_customer_clv_fix)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        if test_func():
            print(f"✅ {test_name}: PASADO")
            passed += 1
        else:
            print(f"❌ {test_name}: FALLIDO")
    
    print("\n" + "=" * 50)
    print(f"🎯 RESUMEN DE PRUEBAS: {passed}/{total} pasadas")
    
    if passed == total:
        print("🎉 ¡TODAS LAS CORRECCIONES FUNCIONAN CORRECTAMENTE!")
    else:
        print("⚠️  Algunas correcciones necesitan trabajo adicional")
    
    return passed == total

if __name__ == "__main__":
    main()
