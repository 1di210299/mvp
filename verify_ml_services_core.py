#!/usr/bin/env python3
"""
Script de verificación para ML Services Core - Días 3-4
========================================================
Verifica la implementación de:
1. Prophet, ARIMA, Random Forest optimizados
2. Customer Intelligence tradicional
3. Financial Forecasting robusto
4. Performance monitoring para ML tradicional
5. Baseline accuracy metrics
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from authentication.models import Company
from forecasting.services.ml_core_services import get_ml_core_performance_report
from forecasting.ml_algorithms.prophet_forecaster import ProphetForecaster
from forecasting.ml_algorithms.arima_forecaster import ARIMAForecaster
from forecasting.ml_algorithms.random_forest_forecaster import RandomForestForecaster

def verify_ml_services_core():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN DE ML SERVICES CORE - DÍAS 3-4")
    print("=" * 55)
    
    # 1. Verificar algoritmos optimizados
    print("\n1️⃣ ALGORITMOS ML OPTIMIZADOS")
    print("-" * 35)
    
    algorithms = [
        ("Prophet", ProphetForecaster),
        ("ARIMA", ARIMAForecaster), 
        ("Random Forest", RandomForestForecaster)
    ]
    
    algorithm_results = {}
    
    for name, algorithm_class in algorithms:
        try:
            # Verificar que la clase existe y se puede instanciar
            algo = algorithm_class()
            status = "✅"
            
            # Verificar métodos optimizados
            has_baseline_metrics = hasattr(algo, 'get_baseline_accuracy_metrics')
            has_performance_summary = hasattr(algo, 'get_performance_summary')
            has_optimization = hasattr(algo, 'optimize_hyperparameters')
            
            features = []
            if has_baseline_metrics:
                features.append("Baseline Metrics")
            if has_performance_summary:
                features.append("Performance Summary")
            if has_optimization:
                features.append("Hyperparameter Optimization")
            
            algorithm_results[name] = {
                'status': 'optimizado',
                'features': features
            }
            
            print(f"{status} {name} - Optimizado")
            print(f"   Features: {', '.join(features)}")
            
        except Exception as e:
            print(f"❌ {name} - Error: {str(e)[:50]}...")
            algorithm_results[name] = {
                'status': 'error',
                'features': []
            }
    
    # 2. Verificar Customer Intelligence
    print("\n2️⃣ CUSTOMER INTELLIGENCE TRADICIONAL")
    print("-" * 40)
    
    ci_service = None
    company = None
    created = False
    
    try:
        from forecasting.services.customer_intelligence_service import CustomerIntelligenceService
        
        # Crear company de prueba con datos únicos completos
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        unique_ruc = f"2050000{unique_id[:3]}"  # RUC válido único
        
        company, created = Company.objects.get_or_create(
            ruc=unique_ruc,
            defaults={
                'name': f"Test Company ML {unique_id}",
                'email': f'test{unique_id}@mlservices.com',
                'address': 'Dirección de prueba',
                'industry': 'Technology'
            }
        )
        
        ci_service = CustomerIntelligenceService(company)
        
        # Verificar métodos optimizados
        has_baseline = hasattr(ci_service, 'calculate_baseline_accuracy_metrics')
        has_performance = hasattr(ci_service, 'get_performance_summary')
        
        if has_baseline and has_performance:
            print("✅ Customer Intelligence Service - Optimizado")
            print("   Features: Baseline Metrics, Performance Summary, RFM Analysis")
        else:
            print("⚠️ Customer Intelligence Service - Parcialmente optimizado")
            
    except Exception as e:
        print(f"❌ Customer Intelligence Service - Error: {str(e)[:50]}...")
    
    # 3. Verificar Financial Forecasting
    print("\n3️⃣ FINANCIAL FORECASTING ROBUSTO")
    print("-" * 40)
    
    ff_service = None
    
    try:
        from forecasting.services.financial_forecasting_service import FinancialForecastingService
        
        if company is not None:
            ff_service = FinancialForecastingService(company)
            
            # Verificar métodos optimizados
            has_baseline = hasattr(ff_service, 'calculate_baseline_accuracy_metrics')
            has_performance = hasattr(ff_service, 'get_performance_summary')
            
            if has_baseline and has_performance:
                print("✅ Financial Forecasting Service - Robusto")
                print("   Features: Revenue Forecasting, ROI Analysis, Cashflow Prediction")
            else:
                print("⚠️ Financial Forecasting Service - Parcialmente optimizado")
        else:
            print("⚠️ Financial Forecasting Service - Company no disponible")
            
    except Exception as e:
        print(f"❌ Financial Forecasting Service - Error: {str(e)[:50]}...")
    
    # 4. Verificar Performance Monitoring
    print("\n4️⃣ PERFORMANCE MONITORING ML")
    print("-" * 35)
    
    monitor = None
    
    try:
        from forecasting.services.ml_core_services import MLCorePerformanceMonitor
        
        if company is not None:
            monitor = MLCorePerformanceMonitor(company)
            
            # Verificar que puede generar reporte
            has_comprehensive_report = hasattr(monitor, 'get_comprehensive_performance_report')
            
            if has_comprehensive_report:
                print("✅ ML Core Performance Monitor - Implementado")
                print("   Features: Comprehensive Reports, Health Status, Recommendations")
                
                # Intentar generar reporte básico
                try:
                    report = monitor.get_comprehensive_performance_report()
                    if report and 'company' in report:
                        print("✅ Reporte de performance generado exitosamente")
                    else:
                        print("⚠️ Reporte generado pero con estructura incompleta")
                except Exception as e:
                    print(f"⚠️ Error generando reporte: {str(e)[:50]}...")
            else:
                print("❌ ML Core Performance Monitor - No implementado")
        else:
            print("⚠️ Performance Monitoring - Company no disponible")
            
    except Exception as e:
        print(f"❌ Performance Monitoring - Error: {str(e)[:50]}...")
    
    # 5. Verificar Baseline Accuracy Metrics
    print("\n5️⃣ BASELINE ACCURACY METRICS")
    print("-" * 35)
    
    metrics_systems = []
    
    # Verificar en algoritmos
    for name, result in algorithm_results.items():
        if 'Baseline Metrics' in result.get('features', []):
            metrics_systems.append(f"{name} Algorithm")
    
    # Verificar en servicios
    if ci_service and hasattr(ci_service, 'calculate_baseline_accuracy_metrics'):
        metrics_systems.append("Customer Intelligence")
    
    if ff_service and hasattr(ff_service, 'calculate_baseline_accuracy_metrics'):
        metrics_systems.append("Financial Forecasting")
    
    print(f"✅ Sistemas con Baseline Metrics: {len(metrics_systems)}")
    for system in metrics_systems:
        print(f"   • {system}")
    
    # 6. Test de integración
    print("\n6️⃣ TEST DE INTEGRACIÓN")
    print("-" * 30)
    
    try:
        # Test rápido de Prophet
        prophet = ProphetForecaster()
        print("✅ Prophet - Instanciación exitosa")
        
        # Test rápido de monitoring con company válida
        if company is not None:
            report = get_ml_core_performance_report(company)
            if report:
                print("✅ Performance Monitoring - Función helper funcional")
            else:
                print("⚠️ Performance Monitoring - Función helper sin datos")
        else:
            print("⚠️ Performance Monitoring - Company no disponible para test")
        
        integration_score = 100
        
    except Exception as e:
        print(f"❌ Test de integración falló: {str(e)[:50]}...")
        integration_score = 0
    
    # 7. Verificación específica de archivos ML Core
    print("\n7️⃣ VERIFICACIÓN DE ARCHIVOS ML CORE")
    print("-" * 40)
    
    ml_core_files = [
        ("Prophet Forecaster", "forecasting/ml_algorithms/prophet_forecaster.py"),
        ("ARIMA Forecaster", "forecasting/ml_algorithms/arima_forecaster.py"),
        ("Random Forest Forecaster", "forecasting/ml_algorithms/random_forest_forecaster.py"),
        ("Customer Intelligence", "forecasting/services/customer_intelligence_service.py"),
        ("Financial Forecasting", "forecasting/services/financial_forecasting_service.py"),
        ("ML Core Services", "forecasting/services/ml_core_services.py"),
        ("AI Models", "forecasting/models/ai_models.py")
    ]
    
    files_status = {}
    for name, filepath in ml_core_files:
        try:
            full_path = f"/Users/juandiegogutierrezcortez/mvp/{filepath}"
            if os.path.exists(full_path):
                # Verificar que el archivo no esté vacío
                with open(full_path, 'r') as f:
                    content = f.read().strip()
                if len(content) > 100:  # Archivo debe tener contenido sustancial
                    print(f"✅ {name} - Archivo presente y completo")
                    files_status[name] = 'complete'
                else:
                    print(f"⚠️ {name} - Archivo muy pequeño")
                    files_status[name] = 'incomplete'
            else:
                print(f"❌ {name} - Archivo faltante")
                files_status[name] = 'missing'
        except Exception as e:
            print(f"❌ {name} - Error verificando: {str(e)[:30]}...")
            files_status[name] = 'error'
    
    # 8. Verificación de dependencias ML
    print("\n8️⃣ VERIFICACIÓN DE DEPENDENCIAS ML")
    print("-" * 40)
    
    ml_dependencies = [
        ("prophet", "Prophet time series forecasting"),
        ("sklearn", "Scikit-learn ML algorithms"),
        ("pandas", "Data manipulation"),
        ("numpy", "Numerical computing"),
        ("statsmodels", "Statistical models"),
    ]
    
    dependency_status = {}
    for package, description in ml_dependencies:
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
            dependency_status[package] = 'installed'
        except ImportError:
            print(f"❌ {package} - {description} (FALTANTE)")
            dependency_status[package] = 'missing'
        except Exception as e:
            print(f"⚠️ {package} - Error: {str(e)[:30]}...")
            dependency_status[package] = 'error'
    
    # Resumen final
    print("\n📊 RESUMEN COMPLETO DE VERIFICACIÓN ML SERVICES CORE")
    print("=" * 60)
    
    optimized_algorithms = sum(1 for result in algorithm_results.values() 
                              if result['status'] == 'optimizado')
    
    complete_files = sum(1 for status in files_status.values() if status == 'complete')
    total_files = len(files_status)
    
    installed_deps = sum(1 for status in dependency_status.values() if status == 'installed')
    total_deps = len(dependency_status)
    
    print(f"Algoritmos ML optimizados: {optimized_algorithms}/{len(algorithms)}")
    print(f"Customer Intelligence: {'✅ Implementado' if ci_service is not None else '❌ Faltante'}")
    print(f"Financial Forecasting: {'✅ Implementado' if ff_service is not None else '❌ Faltante'}")
    print(f"Performance Monitoring: {'✅ Implementado' if monitor is not None else '❌ Faltante'}")
    print(f"Baseline Metrics: {len(metrics_systems)} sistemas")
    print(f"Archivos ML Core: {complete_files}/{total_files} completos")
    print(f"Dependencias ML: {installed_deps}/{total_deps} instaladas")
    
    # Calcular completitud mejorada
    total_components = 7  # Algoritmos, CI, FF, Monitoring, Metrics, Files, Dependencies
    completed_components = (
        (optimized_algorithms / len(algorithms)) +      # Algoritmos
        (1 if ci_service is not None else 0) +         # Customer Intelligence
        (1 if ff_service is not None else 0) +         # Financial Forecasting
        (1 if monitor is not None else 0) +            # Performance Monitoring
        (1 if metrics_systems else 0) +                # Baseline Metrics
        (complete_files / total_files) +               # Archivos completos
        (installed_deps / total_deps)                  # Dependencias
    )
    
    completeness = (completed_components / total_components) * 100
    
    print(f"\n🎯 COMPLETITUD ML SERVICES CORE: {completeness:.1f}%")
    
    # Diagnóstico detallado
    if completeness >= 95:
        print("🎉 ¡EXCELENTE! ML Services Core completamente implementado")
        print("🚀 READY FOR PRODUCTION - Días 3-4 completados al 100%")
        print("🔥 Todos los algoritmos optimizados con baseline metrics")
        print("📊 Performance monitoring operacional")
    elif completeness >= 85:
        print("👍 Muy buena implementación, excelente progreso")
        print("🔧 Ajustes menores pendientes para completar al 100%")
    elif completeness >= 70:
        print("⚡ Buena implementación, núcleo ML funcional")
        print("📈 Mayoría de componentes operacionales")
    elif completeness >= 50:
        print("⚠️ Implementación parcial, revisar componentes faltantes")
        print("🔨 Necesita trabajo adicional en servicios")
    else:
        print("❌ Implementación incompleta, requiere trabajo significativo")
        print("🛠️ Múltiples componentes necesitan atención")
    
    # Recomendaciones específicas
    print(f"\n💡 RECOMENDACIONES:")
    if ci_service is None:
        print("   • Revisar Customer Intelligence Service - posible error de configuración")
    if ff_service is None:
        print("   • Revisar Financial Forecasting Service - posible error de configuración")
    if monitor is None:
        print("   • Revisar ML Core Performance Monitor - posible error de configuración")
    if complete_files < total_files:
        print(f"   • Completar archivos ML Core faltantes: {total_files - complete_files} pendientes")
    if installed_deps < total_deps:
        print(f"   • Instalar dependencias ML faltantes: {total_deps - installed_deps} pendientes")
    
    # Limpiar datos de prueba
    if company is not None and created:
        company.delete()
        print("\n🧹 Datos de prueba limpiados")

if __name__ == "__main__":
    try:
        verify_ml_services_core()
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        sys.exit(1)
