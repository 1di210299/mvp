"""
ML Core Services - Performance Monitoring Centralizado
======================================================
Servicio centralizado para monitoring de performance de todos los
algoritmos ML en ML Services Core:

- Prophet, ARIMA, Random Forest optimizados
- Customer Intelligence tradicional
- Financial Forecasting robusto
- Baseline accuracy metrics unificados
- Performance monitoring en tiempo real

Días 3-4: ML Services Core Implementation
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from sklearn.model_selection import train_test_split
from authentication.models import Company

# Import services
from .customer_intelligence_service import CustomerIntelligenceService
from .financial_forecasting_service import FinancialForecastingService

# Import ML algorithms
from ..ml_algorithms.prophet_forecaster import ProphetForecaster
from ..ml_algorithms.arima_forecaster import ARIMAForecaster
from ..ml_algorithms.random_forest_forecaster import RandomForestForecaster

# Import models
from ..models import (
    ForecastModel, MLModelVersion, MLMetric, CustomerLifetimeValue,
    ChurnPrediction, FinancialForecastModel, RevenuePrediction
)

logger = logging.getLogger(__name__)


class MLCorePerformanceMonitor:
    """
    Monitor centralizado de performance para ML Services Core
    """
    
    def __init__(self, company: Company):
        self.company = company
        self.customer_intelligence = CustomerIntelligenceService(company)
        self.financial_forecasting = FinancialForecastingService(company)
    
    def get_comprehensive_performance_report(self) -> Dict[str, Any]:
        """
        Reporte completo de performance de ML Services Core
        """
        logger.info(f"Generando reporte de performance ML para {self.company.name}")
        
        try:
            report = {
                'company': self.company.name,
                'generated_at': datetime.now().isoformat(),
                'ml_algorithms_performance': self._get_algorithms_performance(),
                'customer_intelligence_performance': self._get_customer_intelligence_performance(),
                'financial_forecasting_performance': self._get_financial_performance(),
                'baseline_accuracy_summary': self._get_baseline_accuracy_summary(),
                'model_health_status': self._get_model_health_status(),
                'recommendations': self._generate_recommendations(),
                'data_quality_assessment': self._assess_data_quality(),
                'performance_trends': self._analyze_performance_trends()
            }
            
            # Calcular score general
            report['overall_performance_score'] = self._calculate_overall_score(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte de performance: {e}")
            return {
                'error': str(e),
                'company': self.company.name,
                'generated_at': datetime.now().isoformat()
            }
    
    def _get_algorithms_performance(self) -> Dict[str, Any]:
        """
        Performance de algoritmos ML individuales
        """
        try:
            algorithms_performance = {
                'prophet': self._test_prophet_performance(),
                'arima': self._test_arima_performance(),
                'random_forest': self._test_random_forest_performance()
            }
            
            # Resumen de algoritmos
            total_algorithms = len(algorithms_performance)
            healthy_algorithms = sum(1 for algo in algorithms_performance.values() 
                                   if algo.get('status') == 'healthy')
            
            return {
                'individual_algorithms': algorithms_performance,
                'summary': {
                    'total_algorithms': total_algorithms,
                    'healthy_algorithms': healthy_algorithms,
                    'health_rate': round(healthy_algorithms / total_algorithms * 100, 2) if total_algorithms > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo performance de algoritmos: {e}")
            return {'error': str(e)}
    
    def _test_prophet_performance(self) -> Dict[str, Any]:
        """
        Test de performance para Prophet con datos sintéticos perfectamente adaptados
        """
        try:
            # Crear datos de prueba sintéticos válidos para Prophet
            dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
            y = np.random.normal(100, 20, len(dates)) + np.sin(np.arange(len(dates)) * 2 * np.pi / 365) * 10
            synthetic_data = pd.DataFrame({'ds': dates, 'y': y})
            synthetic_data['ds'] = pd.to_datetime(synthetic_data['ds'])
            synthetic_data = synthetic_data.sort_values('ds').reset_index(drop=True)
            
            # Crear instancia Prophet
            prophet = ProphetForecaster()
            
            # Dividir datos
            train_size = int(len(synthetic_data) * 0.8)
            train_data = synthetic_data.iloc[:train_size].copy()
            test_data = synthetic_data.iloc[train_size:].copy()
            
            # Entrenar y predecir
            start_time = datetime.now()
            prophet.fit(train_data, 'y')
            training_time = (datetime.now() - start_time).total_seconds()
            baseline_metrics = prophet.get_baseline_accuracy_metrics(test_data, 'y')
            return {
                'status': 'healthy',
                'training_time_seconds': round(training_time, 2),
                'baseline_metrics': baseline_metrics,
                'model_info': {
                    'name': prophet.get_model_name(),
                    'is_fitted': prophet.is_fitted,
                    'data_points_trained': len(train_data)
                }
            }
        except Exception as e:
            logger.error(f"Error testing Prophet: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'baseline_metrics': {},
                'fallback_status': 'Prophet class imported successfully'
            }
    
    def _test_arima_performance(self) -> Dict[str, Any]:
        """
        Test de performance para ARIMA con datos sintéticos perfectamente adaptados
        """
        try:
            # Crear datos de prueba válidos para ARIMA (Serie con índice de fechas)
            np.random.seed(42)
            dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
            y = np.random.normal(100, 10, len(dates))
            data = pd.Series(y, index=dates)
            
            # Crear instancia ARIMA
            arima = ARIMAForecaster()
            
            start_time = datetime.now()
            arima.fit(data)
            training_time = (datetime.now() - start_time).total_seconds()
            baseline_metrics = arima.get_baseline_accuracy_metrics(data)
            return {
                'status': 'healthy',
                'training_time_seconds': round(training_time, 2),
                'baseline_metrics': baseline_metrics,
                'model_info': {
                    'name': arima.get_model_name(),
                    'is_fitted': arima.is_fitted,
                    'data_points_trained': len(data)
                }
            }
        except Exception as e:
            logger.error(f"Error testing ARIMA: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'baseline_metrics': {},
                'fallback_status': 'ARIMA class imported successfully'
            }
    
    def _test_random_forest_performance(self) -> Dict[str, Any]:
        """
        Test de performance para Random Forest con datos sintéticos perfectamente adaptados
        """
        try:
            # Crear datos de prueba válidos para Random Forest
            np.random.seed(42)
            n_samples = 200
            X = pd.DataFrame({
                'feature_1': np.random.normal(0, 1, n_samples),
                'feature_2': np.random.normal(0, 1, n_samples),
                'feature_3': np.random.normal(0, 1, n_samples)
            })
            y = X['feature_1'] * 2 + X['feature_2'] * 1.5 + np.random.normal(0, 0.5, n_samples)
            y = pd.Series(y, index=X.index)
            
            # Crear instancia Random Forest
            rf = RandomForestForecaster()
            
            # Dividir datos
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Entrenar y predecir
            start_time = datetime.now()
            rf.fit(X_train, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            baseline_metrics = rf.get_baseline_accuracy_metrics(X_test, y_test)
            return {
                'status': 'healthy',
                'training_time_seconds': round(training_time, 2),
                'baseline_metrics': baseline_metrics,
                'model_info': {
                    'name': rf.get_model_name(),
                    'is_fitted': rf.is_fitted,
                    'data_points_trained': len(X_train)
                }
            }
        except Exception as e:
            logger.error(f"Error testing Random Forest: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'baseline_metrics': {},
                'fallback_status': 'Random Forest class imported successfully'
            }
    
    def _get_customer_intelligence_performance(self) -> Dict[str, Any]:
        """
        Performance del Customer Intelligence Service
        """
        try:
            return self.customer_intelligence.get_performance_summary()
        except Exception as e:
            logger.error(f"Error obteniendo performance de Customer Intelligence: {e}")
            return {'error': str(e)}
    
    def _get_financial_performance(self) -> Dict[str, Any]:
        """
        Performance del Financial Forecasting Service
        """
        try:
            return self.financial_forecasting.get_performance_summary()
        except Exception as e:
            logger.error(f"Error obteniendo performance financiero: {e}")
            return {'error': str(e)}
    
    def _get_baseline_accuracy_summary(self) -> Dict[str, Any]:
        """
        Resumen de métricas baseline de accuracy
        """
        try:
            # Recopilar métricas de todos los servicios
            customer_metrics = self.customer_intelligence.calculate_baseline_accuracy_metrics('clv')
            financial_metrics = self.financial_forecasting.calculate_baseline_accuracy_metrics('revenue')
            
            # Calcular promedios
            all_accuracy_scores = [
                customer_metrics.get('accuracy_score', 0),
                financial_metrics.get('accuracy_score', 0)
            ]
            
            all_mape_scores = [
                customer_metrics.get('mape', 100),
                financial_metrics.get('mape', 100)
            ]
            
            return {
                'average_accuracy_score': round(np.mean([s for s in all_accuracy_scores if s > 0]), 2),
                'average_mape': round(np.mean([s for s in all_mape_scores if s < 100]), 2),
                'best_performing_model': self._identify_best_model(customer_metrics, financial_metrics),
                'accuracy_distribution': {
                    'excellent': sum(1 for s in all_accuracy_scores if s >= 90),
                    'good': sum(1 for s in all_accuracy_scores if 70 <= s < 90),
                    'fair': sum(1 for s in all_accuracy_scores if 50 <= s < 70),
                    'poor': sum(1 for s in all_accuracy_scores if s < 50)
                },
                'individual_metrics': {
                    'customer_intelligence': customer_metrics,
                    'financial_forecasting': financial_metrics
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculando resumen baseline: {e}")
            return {'error': str(e)}
    
    def _identify_best_model(self, customer_metrics: Dict, financial_metrics: Dict) -> str:
        """
        Identifica el modelo con mejor performance
        """
        customer_score = customer_metrics.get('accuracy_score', 0)
        financial_score = financial_metrics.get('accuracy_score', 0)
        
        if customer_score > financial_score:
            return 'customer_intelligence'
        elif financial_score > customer_score:
            return 'financial_forecasting'
        else:
            return 'tied'
    
    def _get_model_health_status(self) -> Dict[str, Any]:
        """
        Estado de salud general de los modelos
        """
        try:
            # Contar modelos por estado
            forecast_models = ForecastModel.objects.filter(company=self.company)
            ml_versions = MLModelVersion.objects.filter(forecast_model__company=self.company)
            
            model_counts = {
                'total_forecast_models': forecast_models.count(),
                'active_forecast_models': forecast_models.filter(status='active').count(),
                'training_models': forecast_models.filter(status='training').count(),
                'failed_models': forecast_models.filter(status='failed').count(),
                'ml_model_versions': ml_versions.count(),
                'production_versions': ml_versions.filter(deployment_status='production').count()
            }
            
            # Calcular health score
            total_models = model_counts['total_forecast_models']
            if total_models > 0:
                health_score = (model_counts['active_forecast_models'] / total_models) * 100
            else:
                health_score = 0
            
            # Estado general
            if health_score >= 80:
                overall_status = 'healthy'
            elif health_score >= 60:
                overall_status = 'warning'
            else:
                overall_status = 'critical'
            
            return {
                'overall_status': overall_status,
                'health_score': round(health_score, 2),
                'model_counts': model_counts,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de modelos: {e}")
            return {'error': str(e)}
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """
        Evaluación de calidad de datos
        """
        try:
            from inventory.models import Transaction, Customer
            
            # Métricas de datos
            total_transactions = Transaction.objects.filter(
                product__company=self.company
            ).count()
            
            total_customers = Customer.objects.filter(is_active=True).count()
            
            # Datos de los últimos 30 días
            recent_date = timezone.now().date() - timedelta(days=30)
            recent_transactions = Transaction.objects.filter(
                product__company=self.company,
                transaction_date__date__gte=recent_date
            ).count()
            
            # Completitud de datos
            customers_with_clv = CustomerLifetimeValue.objects.count()
            customers_with_churn = ChurnPrediction.objects.count()
            
            data_completeness = {
                'clv_coverage': round(customers_with_clv / total_customers * 100, 2) if total_customers > 0 else 0,
                'churn_coverage': round(customers_with_churn / total_customers * 100, 2) if total_customers > 0 else 0
            }
            
            # Score de calidad
            quality_factors = [
                min(100, total_transactions / 100),  # Al menos 100 transacciones
                min(100, total_customers / 10),      # Al menos 10 customers
                min(100, recent_transactions / 10),   # Actividad reciente
                data_completeness['clv_coverage'],
                data_completeness['churn_coverage']
            ]
            
            quality_score = round(np.mean(quality_factors), 2)
            
            return {
                'quality_score': quality_score,
                'data_volume': {
                    'total_transactions': total_transactions,
                    'total_customers': total_customers,
                    'recent_transactions': recent_transactions
                },
                'data_completeness': data_completeness,
                'quality_status': 'good' if quality_score >= 70 else 'fair' if quality_score >= 50 else 'poor'
            }
            
        except Exception as e:
            logger.error(f"Error evaluando calidad de datos: {e}")
            return {'error': str(e)}
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """
        Análisis de tendencias de performance
        """
        try:
            # Obtener métricas históricas (últimos 30 días)
            ml_metrics = MLMetric.objects.filter(
                calculation_date__gte=timezone.now() - timedelta(days=30)
            ).order_by('calculation_date')
            
            if not ml_metrics.exists():
                return {
                    'trend_status': 'no_data',
                    'metrics_count': 0,
                    'trend_analysis': 'Insufficient historical data for trend analysis'
                }
            
            # Analizar tendencias de accuracy
            accuracy_metrics = ml_metrics.filter(metric_type='accuracy').values_list('metric_value', 'calculation_date')
            
            if accuracy_metrics:
                accuracy_values = [float(m[0]) for m in accuracy_metrics]
                
                # Calcular tendencia (simple linear regression)
                x = np.arange(len(accuracy_values))
                if len(accuracy_values) > 1:
                    slope = np.polyfit(x, accuracy_values, 1)[0]
                    trend_direction = 'improving' if slope > 0 else 'declining' if slope < 0 else 'stable'
                else:
                    trend_direction = 'stable'
                
                return {
                    'trend_status': trend_direction,
                    'metrics_count': len(accuracy_values),
                    'avg_accuracy': round(np.mean(accuracy_values), 2),
                    'accuracy_trend_slope': round(slope, 4) if 'slope' in locals() else 0,
                    'latest_accuracy': accuracy_values[-1] if accuracy_values else 0
                }
            else:
                return {
                    'trend_status': 'no_accuracy_data',
                    'metrics_count': ml_metrics.count(),
                    'trend_analysis': 'No accuracy metrics found for trend analysis'
                }
                
        except Exception as e:
            logger.error(f"Error analizando tendencias: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """
        Genera recomendaciones basadas en el performance
        """
        recommendations = []
        
        try:
            # Obtener métricas actuales
            customer_metrics = self.customer_intelligence.calculate_baseline_accuracy_metrics('clv')
            financial_metrics = self.financial_forecasting.calculate_baseline_accuracy_metrics('revenue')
            
            # Recomendaciones basadas en accuracy
            if customer_metrics.get('accuracy_score', 0) < 70:
                recommendations.append("Considere reentrenar modelos de Customer Intelligence con más datos históricos")
            
            if financial_metrics.get('accuracy_score', 0) < 70:
                recommendations.append("Modelos financieros necesitan optimización - considere ajustar hiperparámetros")
            
            # Recomendaciones basadas en datos
            data_quality = self._assess_data_quality()
            if data_quality.get('quality_score', 0) < 60:
                recommendations.append("Mejorar calidad y volumen de datos para mejor performance de modelos")
            
            # Recomendaciones generales
            model_health = self._get_model_health_status()
            if model_health.get('health_score', 0) < 80:
                recommendations.append("Revisar y reactivar modelos inactivos o fallidos")
            
            if not recommendations:
                recommendations.append("Todos los modelos están funcionando óptimamente - continuar monitoreo regular")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
            return [f"Error generando recomendaciones: {str(e)}"]
    
    def _calculate_overall_score(self, report: Dict[str, Any]) -> float:
        """
        Calcula score general de performance
        """
        try:
            scores = []
            
            # Score de algoritmos
            algo_performance = report.get('ml_algorithms_performance', {}).get('summary', {})
            if algo_performance.get('health_rate'):
                scores.append(algo_performance['health_rate'])
            
            # Score de baseline accuracy
            baseline_summary = report.get('baseline_accuracy_summary', {})
            if baseline_summary.get('average_accuracy_score'):
                scores.append(baseline_summary['average_accuracy_score'])
            
            # Score de health de modelos
            model_health = report.get('model_health_status', {})
            if model_health.get('health_score'):
                scores.append(model_health['health_score'])
            
            # Score de calidad de datos
            data_quality = report.get('data_quality_assessment', {})
            if data_quality.get('quality_score'):
                scores.append(data_quality['quality_score'])
            
            # Promedio ponderado
            if scores:
                overall_score = round(np.mean(scores), 2)
            else:
                overall_score = 0.0
            
            return overall_score
            
        except Exception as e:
            logger.error(f"Error calculando score general: {e}")
            return 0.0


# Función helper para obtener reporte rápido
def get_ml_core_performance_report(company: Company) -> Dict[str, Any]:
    """
    Función helper para obtener reporte de performance de ML Core
    """
    monitor = MLCorePerformanceMonitor(company)
    return monitor.get_comprehensive_performance_report()
