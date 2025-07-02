#!/usr/bin/env python
"""
Script de validación para el sistema de Machine Learning de pronósticos.
Verifica que todos los componentes estén correctamente implementados.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.core.management import call_command
from django.test.utils import get_runner
from django.conf import settings
import importlib
import warnings

def validate_dependencies():
    """Valida que todas las dependencias de ML estén instaladas"""
    print("🔍 Validando dependencias de Machine Learning...")
    
    required_packages = [
        'prophet',
        'statsmodels', 
        'pmdarima',
        'matplotlib',
        'seaborn',
        'plotly',
        'joblib',
        'numpy',
        'pandas',
        'sklearn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} - NO ENCONTRADO")
    
    if missing_packages:
        print(f"\n⚠️  Paquetes faltantes: {', '.join(missing_packages)}")
        print("Instala con: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ Todas las dependencias están instaladas")
        return True

def validate_models():
    """Valida que los modelos estén correctamente definidos"""
    print("\n🗃️  Validando modelos de Django...")
    
    try:
        from forecasting.models import ForecastModel, DemandForecast, ReorderRecommendation
        print("  ✅ Modelos de forecasting importados correctamente")
        
        # Verificar campos del modelo
        model_fields = [field.name for field in ForecastModel._meta.fields]
        required_fields = ['product', 'name', 'algorithm', 'parameters', 'accuracy_metrics']
        
        for field in required_fields:
            if field in model_fields:
                print(f"    ✅ Campo {field} presente")
            else:
                print(f"    ❌ Campo {field} faltante")
                return False
        
        return True
    except ImportError as e:
        print(f"  ❌ Error importando modelos: {e}")
        return False

def validate_ml_algorithms():
    """Valida que los algoritmos de ML estén implementados"""
    print("\n🤖 Validando algoritmos de Machine Learning...")
    
    try:
        from forecasting.ml_algorithms.base_forecaster import BaseForecaster
        from forecasting.ml_algorithms.prophet_forecaster import ProphetForecaster
        from forecasting.ml_algorithms.arima_forecaster import ARIMAForecaster
        from forecasting.ml_algorithms.ensemble_forecaster import EnsembleForecaster
        
        print("  ✅ BaseForecaster")
        print("  ✅ ProphetForecaster")
        print("  ✅ ARIMAForecaster")
        print("  ✅ EnsembleForecaster")
        
        # Verificar métodos requeridos
        forecaster_instance = ProphetForecaster()
        required_methods = ['train', 'predict', 'evaluate']
        
        for method in required_methods:
            if hasattr(forecaster_instance, method):
                print(f"    ✅ Método {method} implementado")
            else:
                print(f"    ❌ Método {method} faltante")
                return False
        
        return True
    except ImportError as e:
        print(f"  ❌ Error importando algoritmos: {e}")
        return False

def validate_services():
    """Valida que los servicios estén implementados"""
    print("\n🔧 Validando servicios...")
    
    try:
        from forecasting.services.ml_model_service import MLModelService
        from forecasting.services.forecast_service import ForecastService
        from forecasting.services.evaluation_service import EvaluationService
        
        print("  ✅ MLModelService")
        print("  ✅ ForecastService")
        print("  ✅ EvaluationService")
        
        # Verificar métodos de servicios
        ml_service = MLModelService()
        required_methods = ['train_model_for_product', 'train_models_for_company']
        
        for method in required_methods:
            if hasattr(ml_service, method):
                print(f"    ✅ Método {method} implementado")
            else:
                print(f"    ❌ Método {method} faltante")
                return False
        
        return True
    except ImportError as e:
        print(f"  ❌ Error importando servicios: {e}")
        return False

def validate_apis():
    """Valida que las APIs estén configuradas"""
    print("\n🌐 Validando APIs...")
    
    try:
        from forecasting.views import (
            ForecastModelViewSet, DemandForecastViewSet, ReorderRecommendationViewSet,
            PredictDemandView, TrainModelView, ModelAccuracyView,
            ProductForecastView, GenerateRecommendationsView
        )
        
        print("  ✅ ForecastModelViewSet")
        print("  ✅ DemandForecastViewSet")
        print("  ✅ ReorderRecommendationViewSet")
        print("  ✅ PredictDemandView")
        print("  ✅ TrainModelView")
        print("  ✅ ModelAccuracyView")
        print("  ✅ ProductForecastView")
        print("  ✅ GenerateRecommendationsView")
        
        return True
    except ImportError as e:
        print(f"  ❌ Error importando vistas: {e}")
        return False

def validate_serializers():
    """Valida que los serializers estén implementados"""
    print("\n📋 Validando serializers...")
    
    try:
        from forecasting.serializers import (
            ForecastModelSerializer, DemandForecastSerializer, ReorderRecommendationSerializer,
            TrainModelRequestSerializer, PredictDemandRequestSerializer
        )
        
        print("  ✅ ForecastModelSerializer")
        print("  ✅ DemandForecastSerializer")
        print("  ✅ ReorderRecommendationSerializer")
        print("  ✅ TrainModelRequestSerializer")
        print("  ✅ PredictDemandRequestSerializer")
        
        return True
    except ImportError as e:
        print(f"  ❌ Error importando serializers: {e}")
        return False

def validate_celery_tasks():
    """Valida que las tareas de Celery estén configuradas"""
    print("\n⚡ Validando tareas de Celery...")
    
    try:
        from forecasting.tasks import (
            train_ml_models_task, generate_forecasts_task,
            evaluate_models_task, compare_models_task
        )
        
        print("  ✅ train_ml_models_task")
        print("  ✅ generate_forecasts_task")
        print("  ✅ evaluate_models_task")
        print("  ✅ compare_models_task")
        
        return True
    except ImportError as e:
        print(f"  ❌ Error importando tareas: {e}")
        return False

def validate_management_commands():
    """Valida que los comandos de administración estén disponibles"""
    print("\n💻 Validando comandos de administración...")
    
    try:
        from forecasting.management.commands.train_ml_models import Command as TrainCommand
        from forecasting.management.commands.evaluate_ml_models import Command as EvalCommand
        
        print("  ✅ train_ml_models command")
        print("  ✅ evaluate_ml_models command")
        
        return True
    except ImportError as e:
        print(f"  ❌ Error importando comandos: {e}")
        return False

def validate_settings():
    """Valida que la configuración esté correcta"""
    print("\n⚙️  Validando configuración...")
    
    try:
        # Verificar configuración ML
        if hasattr(settings, 'ML_CONFIG'):
            print("  ✅ ML_CONFIG presente en settings")
            
            required_keys = ['MODEL_STORAGE_PATH', 'EXPERIMENTS_PATH', 'PROPHET_PARAMS', 'ARIMA_PARAMS']
            for key in required_keys:
                if key in settings.ML_CONFIG:
                    print(f"    ✅ {key} configurado")
                else:
                    print(f"    ⚠️  {key} no configurado")
        else:
            print("  ⚠️  ML_CONFIG no encontrado en settings")
        
        # Verificar configuración de pronósticos
        if hasattr(settings, 'FORECAST_CONFIG'):
            print("  ✅ FORECAST_CONFIG presente en settings")
        else:
            print("  ⚠️  FORECAST_CONFIG no encontrado en settings")
        
        return True
    except Exception as e:
        print(f"  ❌ Error validando configuración: {e}")
        return False

def run_basic_tests():
    """Ejecuta tests básicos"""
    print("\n🧪 Ejecutando tests básicos...")
    
    try:
        # Suprimir warnings durante tests
        warnings.filterwarnings('ignore')
        
        # Ejecutar tests específicos de forecasting
        call_command('test', 'forecasting.tests.MLModelServiceTest.test_ml_model_service_initialization', verbosity=0)
        print("  ✅ Test de inicialización de MLModelService")
        
        call_command('test', 'forecasting.tests.ModelIntegrationTest.test_forecast_model_creation', verbosity=0)
        print("  ✅ Test de creación de modelos")
        
        return True
    except Exception as e:
        print(f"  ⚠️  Algunos tests fallaron: {e}")
        return False

def check_directories():
    """Verifica que los directorios necesarios existan"""
    print("\n📁 Verificando estructura de directorios...")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    required_dirs = [
        'ml_algorithms',
        'services',
        'management/commands'
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = os.path.join(base_path, dir_name)
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ - FALTANTE")
            all_exist = False
    
    return all_exist

def main():
    """Función principal de validación"""
    print("🚀 Iniciando validación del sistema de Machine Learning para pronósticos")
    print("=" * 70)
    
    validations = [
        ("Dependencias", validate_dependencies),
        ("Directorios", check_directories),
        ("Modelos Django", validate_models),
        ("Algoritmos ML", validate_ml_algorithms),
        ("Servicios", validate_services),
        ("APIs", validate_apis),
        ("Serializers", validate_serializers),
        ("Tareas Celery", validate_celery_tasks),
        ("Comandos", validate_management_commands),
        ("Configuración", validate_settings),
        ("Tests básicos", run_basic_tests)
    ]
    
    results = []
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"  💥 Error inesperado en {name}: {e}")
            results.append((name, False))
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} validaciones exitosas")
    
    if passed == total:
        print("🎉 ¡Todas las validaciones pasaron! El sistema está listo para usar.")
        print("\nPróximos pasos:")
        print("1. Ejecutar migraciones: python manage.py migrate")
        print("2. Crear datos de prueba: python manage.py generate_sample_data")
        print("3. Entrenar modelos: python manage.py train_ml_models")
        print("4. Iniciar servidor: python manage.py runserver")
    else:
        print("⚠️  Algunas validaciones fallaron. Revisa los errores anteriores.")
        print("\nRevisiones sugeridas:")
        print("1. Instalar dependencias faltantes")
        print("2. Verificar importaciones y rutas")
        print("3. Ejecutar migraciones si es necesario")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
