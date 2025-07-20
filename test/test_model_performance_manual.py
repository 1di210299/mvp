#!/usr/bin/env python3
"""
Script para probar manualmente el endpoint de Model Performance
"""

import requests
import json
import sys
import os
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

# Importar modelos después de configurar Django
from forecasting.models import ForecastModel
from inventory.models import Product
from authentication.models import Company, User
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Configuración
BASE_URL = "http://localhost:8080"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
PERFORMANCE_URL = f"{BASE_URL}/api/forecasting/model-performance/"

def create_test_models():
    """Crear modelos de forecast de prueba"""
    print("🔧 Creando modelos de forecast de prueba...")
    
    try:
        # Obtener la empresa existente
        company = Company.objects.first()
        if not company:
            print("   ❌ No se encontró ninguna empresa")
            return False
            
        print(f"   📢 Usando empresa: {company.name}")
        
        # Obtener algunos productos existentes
        products = Product.objects.filter(company=company)[:3]
        if not products:
            print("   ❌ No se encontraron productos para la empresa")
            return False
            
        print(f"   📦 Productos disponibles: {len(products)}")
        
        # Limpiar modelos existentes para evitar duplicados
        existing_models = ForecastModel.objects.filter(company=company)
        if existing_models.exists():
            print(f"   🗑️  Eliminando {existing_models.count()} modelos existentes...")
            existing_models.delete()
        
        # Crear algunos modelos de forecast de prueba
        models_created = []
        
        model_configs = [
            {
                'name': 'Prophet Model - Producto 1',
                'model_type': 'prophet',
                'mae': Decimal('2.5'),
                'mape': Decimal('15.2'), 
                'rmse': Decimal('3.1'),
                'r2_score': Decimal('0.85')
            },
            {
                'name': 'ARIMA Model - Producto 1',
                'model_type': 'arima',
                'mae': Decimal('3.2'),
                'mape': Decimal('18.5'),
                'rmse': Decimal('4.0'),
                'r2_score': Decimal('0.78')
            },
            {
                'name': 'Random Forest Model - Producto 2',
                'model_type': 'random_forest',
                'mae': Decimal('2.8'),
                'mape': Decimal('16.7'),
                'rmse': Decimal('3.5'),
                'r2_score': Decimal('0.82')
            },
            {
                'name': 'LSTM Model - Producto 3',
                'model_type': 'lstm',
                'mae': Decimal('2.1'),
                'mape': Decimal('13.9'),
                'rmse': Decimal('2.9'),
                'r2_score': Decimal('0.88')
            }
        ]
        
        for i, config in enumerate(model_configs):
            if i < len(products):
                model = ForecastModel.objects.create(
                    company=company,
                    name=config['name'],
                    model_type=config['model_type'],
                    status='active',
                    mae=config['mae'],
                    mape=config['mape'],
                    rmse=config['rmse'],
                    r2_score=config['r2_score'],
                    training_completed_at=timezone.now() - timedelta(days=i+1)
                )
                model.products.add(products[i])
                models_created.append(model)
                print(f"   ✅ Creado: {model.name} (ID: {model.id}) - R²: {model.r2_score}")
        
        print(f"   🎉 Total de modelos creados: {len(models_created)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creando modelos: {e}")
        return False


def test_model_performance_endpoint():
    """Probar el endpoint de model performance"""
    
    print("🚀 Probando el endpoint de Model Performance")
    print("=" * 50)
    
    # Primero crear los modelos de prueba
    if not create_test_models():
        print("❌ No se pudieron crear los modelos de prueba")
        return False
    
    print("\n" + "=" * 50)
    
    # Primero necesitamos autenticarnos
    print("1. Intentando autenticación...")
    
    # Datos de login (usando credenciales del usuario existente)
    login_data = {
        'email': 'admin@testcompany.com',
        'password': 'admin123'
    }
    
    token = None
    
    try:
        # Intentar login para obtener token JWT
        login_response = requests.post(LOGIN_URL, json=login_data)
        print(f"   Status de login: {login_response.status_code}")
        
        if login_response.status_code == 200:
            response_data = login_response.json()
            token = response_data.get('tokens', {}).get('access')
            print("   ✅ Login exitoso")
        else:
            print("   ❌ Login falló")
            print(f"   Respuesta: {login_response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("   ❌ No se pudo conectar al servidor para login")
        return False
    
    # Headers con token JWT
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # Probar el endpoint de performance
    print("\n2. Probando GET /api/forecasting/model-performance/")
    
    try:
        # Test 1: Obtener todos los modelos
        print("\n   📊 Test 1: Obtener performance de todos los modelos")
        response = requests.get(PERFORMANCE_URL, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Respuesta exitosa!")
            print(f"   📈 Total de modelos: {data.get('overall_metrics', {}).get('total_models', 'N/A')}")
            print(f"   📈 Modelos activos: {data.get('overall_metrics', {}).get('active_models', 'N/A')}")
            print(f"   📈 Mejor modelo: {data.get('overall_metrics', {}).get('best_performing_model', {}).get('model_name', 'N/A')}")
            
            # Mostrar algunos datos de modelos
            models = data.get('models_performance', [])
            if models:
                print(f"   📈 Modelos encontrados: {len(models)}")
                for i, model in enumerate(models[:3]):  # Mostrar solo los primeros 3
                    print(f"      - {model.get('model_name')} ({model.get('model_type')}) - MAE: {model.get('metrics', {}).get('mae', 'N/A')}")
            else:
                print("   📈 No se encontraron modelos")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Respuesta: {response.text}")
        
        # Test 2: Obtener modelo específico (si hay modelos)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models_performance', [])
            if models:
                model_id = models[0]['model_id']
                print(f"\n   📊 Test 2: Obtener performance del modelo específico ID {model_id}")
                
                specific_response = requests.get(PERFORMANCE_URL, params={'model_id': model_id}, headers=headers)
                print(f"   Status: {specific_response.status_code}")
                
                if specific_response.status_code == 200:
                    specific_data = specific_response.json()
                    print("   ✅ Respuesta exitosa!")
                    perf = specific_data.get('performance', {})
                    print(f"   📈 Modelo: {perf.get('model_name')}")
                    print(f"   📈 Tipo: {perf.get('model_type')}")
                    print(f"   📈 Estado: {perf.get('status')}")
                    metrics = perf.get('stored_metrics', {})
                    print(f"   📈 MAE: {metrics.get('mae')}")
                    print(f"   📈 MAPE: {metrics.get('mape')}")
                    print(f"   📈 RMSE: {metrics.get('rmse')}")
                    print(f"   📈 R²: {metrics.get('r2_score')}")
                else:
                    print(f"   ❌ Error: {specific_response.status_code}")
                    print(f"   Respuesta: {specific_response.text}")
        
        # Test 3: Probar parámetros
        print(f"\n   📊 Test 3: Probar parámetros personalizados")
        params_response = requests.get(PERFORMANCE_URL, params={
            'days_back': 7,
            'include_realtime': 'false'
        }, headers=headers)
        print(f"   Status: {params_response.status_code}")
        
        if params_response.status_code == 200:
            params_data = params_response.json()
            print("   ✅ Respuesta exitosa!")
            print(f"   📈 Período evaluado: {params_data.get('evaluation_period_days')} días")
            print(f"   📈 Incluye tiempo real: {params_data.get('include_realtime_metrics', 'N/A')}")
        else:
            print(f"   ❌ Error: {params_response.status_code}")
            print(f"   Respuesta: {params_response.text}")
        
        # Test 4: Probar modelo inexistente
        print(f"\n   📊 Test 4: Probar modelo inexistente")
        error_response = requests.get(PERFORMANCE_URL, params={'model_id': 99999}, headers=headers)
        print(f"   Status: {error_response.status_code}")
        
        if error_response.status_code == 404:
            print("   ✅ Error 404 correcto para modelo inexistente")
        else:
            print(f"   ⚠️  Status inesperado: {error_response.status_code}")
            print(f"   Respuesta: {error_response.text}")
    
    except requests.exceptions.ConnectionError:
        print("   ❌ No se pudo conectar al servidor. ¿Está corriendo en localhost:8080?")
        return False
    
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Pruebas completadas!")
    return True

if __name__ == "__main__":
    success = test_model_performance_endpoint()
    sys.exit(0 if success else 1)
