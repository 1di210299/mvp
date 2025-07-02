"""
Servicio para evaluación de modelos de machine learning
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import json

from django.conf import settings
from django.utils import timezone
from django.db import models

from ..models import ForecastModel, DemandForecast, ForecastAccuracy
from ..ml_algorithms.model_evaluator import ModelEvaluator
from ..services.ml_model_service import MLModelService
from inventory.models import Product, Transaction
from authentication.models import Company

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Servicio para evaluación y monitoreo de modelos de pronóstico
    """
    
    def __init__(self):
        """
        Inicializa el servicio de evaluación
        """
        self.ml_service = MLModelService()
        self.evaluator = ModelEvaluator()
    
    def evaluate_model_accuracy(self,
                               model_id: int,
                               evaluation_period_days: int = 30,
                               historical_data_days: int = 365) -> Dict[str, Any]:
        """
        Evalúa la precisión de un modelo usando datos históricos
        
        Args:
            model_id: ID del modelo a evaluar
            evaluation_period_days: Días de evaluación hacia atrás
            historical_data_days: Días de datos históricos para re-entrenamiento
            
        Returns:
            Diccionario con métricas de evaluación
        """
        try:
            forecast_model = ForecastModel.objects.get(id=model_id)
            
            logger.info(f"Evaluando precisión del modelo {model_id}")
            
            # Obtiene datos históricos completos
            all_data = self._get_historical_data(forecast_model, historical_data_days + evaluation_period_days)
            
            if len(all_data) < evaluation_period_days + 30:
                raise ValueError("No hay suficientes datos históricos para evaluación")
            
            # Divide datos en entrenamiento y evaluación
            split_point = len(all_data) - evaluation_period_days
            train_data = all_data.iloc[:split_point]
            test_data = all_data.iloc[split_point:]
            
            # Re-entrena el modelo con datos históricos
            ml_model = self._retrain_model_for_evaluation(forecast_model, train_data)
            
            # Evalúa el modelo
            evaluation_results = self.evaluator.evaluate_model(
                model=ml_model,
                test_data=test_data,
                target_column='quantity',
                forecast_periods=evaluation_period_days
            )
            
            # Actualiza métricas del modelo en base de datos
            self._update_model_metrics(forecast_model, evaluation_results)
            
            # Calcula métricas adicionales específicas del negocio
            business_metrics = self._calculate_business_metrics(
                forecast_model, test_data, ml_model, evaluation_period_days
            )
            
            # Combina resultados
            complete_evaluation = {
                **evaluation_results,
                **business_metrics,
                'evaluation_period_days': evaluation_period_days,
                'model_type': forecast_model.model_type,
                'model_name': forecast_model.name
            }
            
            logger.info(f"Modelo {model_id} evaluado: MAE={evaluation_results.get('mae', 'N/A'):.2f}")
            
            return complete_evaluation
            
        except Exception as e:
            logger.error(f"Error evaluando modelo {model_id}: {str(e)}")
            raise
    
    def compare_models_performance(self,
                                 model_ids: List[int],
                                 evaluation_period_days: int = 30,
                                 metrics_to_compare: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compara el rendimiento de múltiples modelos
        
        Args:
            model_ids: Lista de IDs de modelos a comparar
            evaluation_period_days: Días de evaluación
            metrics_to_compare: Métricas específicas a comparar
            
        Returns:
            Diccionario con comparación detallada
        """
        if metrics_to_compare is None:
            metrics_to_compare = ['mae', 'mape', 'rmse', 'r2', 'directional_accuracy']
        
        try:
            models_performance = []
            
            # Evalúa cada modelo
            for model_id in model_ids:
                try:
                    performance = self.evaluate_model_accuracy(model_id, evaluation_period_days)
                    models_performance.append({
                        'model_id': model_id,
                        'model_name': performance['model_name'],
                        'model_type': performance['model_type'],
                        **{metric: performance.get(metric, np.nan) for metric in metrics_to_compare}
                    })
                except Exception as e:
                    logger.warning(f"Error evaluando modelo {model_id}: {str(e)}")
                    models_performance.append({
                        'model_id': model_id,
                        'error': str(e)
                    })
            
            # Crea DataFrame para análisis
            df = pd.DataFrame(models_performance)
            
            # Calcula rankings
            rankings = {}
            for metric in metrics_to_compare:
                if metric in df.columns:
                    ascending = metric not in ['r2', 'directional_accuracy']  # Métricas donde menor es mejor
                    df[f'{metric}_rank'] = df[metric].rank(ascending=ascending, na_option='bottom')
                    rankings[metric] = df.nsmallest(len(df), f'{metric}_rank')[['model_name', metric, f'{metric}_rank']].to_dict('records')
            
            # Identifica el mejor modelo general
            rank_cols = [col for col in df.columns if col.endswith('_rank')]
            if rank_cols:
                df['overall_rank'] = df[rank_cols].mean(axis=1)
                best_model = df.loc[df['overall_rank'].idxmin()]
            else:
                best_model = None
            
            comparison_result = {
                'evaluation_timestamp': timezone.now(),
                'evaluation_period_days': evaluation_period_days,
                'models_evaluated': len([p for p in models_performance if 'error' not in p]),
                'models_performance': models_performance,
                'rankings_by_metric': rankings,
                'best_model_overall': {
                    'model_id': int(best_model['model_id']),
                    'model_name': best_model['model_name'],
                    'overall_rank': float(best_model['overall_rank'])
                } if best_model is not None else None,
                'summary_statistics': self._calculate_comparison_summary(df, metrics_to_compare)
            }
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error comparando modelos: {str(e)}")
            raise
    
    def evaluate_forecast_accuracy_realtime(self,
                                          model_id: int,
                                          days_back: int = 7) -> Dict[str, Any]:
        """
        Evalúa la precisión de pronósticos en tiempo real comparando con datos reales
        
        Args:
            model_id: ID del modelo
            days_back: Días hacia atrás para evaluar
            
        Returns:
            Diccionario con precisión en tiempo real
        """
        try:
            forecast_model = ForecastModel.objects.get(id=model_id)
            
            # Obtiene pronósticos del período
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            forecasts = DemandForecast.objects.filter(
                model=forecast_model,
                forecast_date__range=(start_date, end_date)
            ).select_related('product')
            
            if not forecasts.exists():
                return {'error': 'No hay pronósticos en el período especificado'}
            
            accuracy_records = []
            total_absolute_error = 0
            total_percentage_error = 0
            within_bounds_count = 0
            total_forecasts = 0
            
            for forecast in forecasts:
                # Obtiene demanda real del día
                actual_demand = self._get_actual_demand(
                    forecast.product, 
                    forecast.forecast_date,
                    forecast.location
                )
                
                if actual_demand is not None:
                    # Calcula métricas de precisión
                    absolute_error = abs(float(forecast.predicted_demand) - actual_demand)
                    
                    if actual_demand > 0:
                        percentage_error = (absolute_error / actual_demand) * 100
                    else:
                        percentage_error = 0 if float(forecast.predicted_demand) == 0 else 100
                    
                    within_bounds = (
                        float(forecast.lower_bound) <= actual_demand <= float(forecast.upper_bound)
                    )
                    
                    bias = (float(forecast.predicted_demand) - actual_demand) / actual_demand * 100 if actual_demand > 0 else 0
                    
                    # Crea o actualiza registro de precisión
                    accuracy_record, created = ForecastAccuracy.objects.get_or_create(
                        forecast=forecast,
                        defaults={
                            'actual_demand': Decimal(str(actual_demand)),
                            'absolute_error': Decimal(str(absolute_error)),
                            'percentage_error': Decimal(str(percentage_error)),
                            'within_bounds': within_bounds,
                            'bias': Decimal(str(bias))
                        }
                    )
                    
                    if not created:
                        # Actualiza si ya existe
                        accuracy_record.actual_demand = Decimal(str(actual_demand))
                        accuracy_record.save()  # Esto recalculará automáticamente las métricas
                    
                    accuracy_records.append({
                        'product_sku': forecast.product.sku,
                        'forecast_date': forecast.forecast_date,
                        'predicted_demand': float(forecast.predicted_demand),
                        'actual_demand': actual_demand,
                        'absolute_error': absolute_error,
                        'percentage_error': percentage_error,
                        'within_bounds': within_bounds,
                        'bias': bias
                    })
                    
                    # Acumula para métricas generales
                    total_absolute_error += absolute_error
                    total_percentage_error += percentage_error
                    if within_bounds:
                        within_bounds_count += 1
                    total_forecasts += 1
            
            if total_forecasts == 0:
                return {'error': 'No se encontraron datos reales para comparar'}
            
            # Calcula métricas agregadas
            avg_absolute_error = total_absolute_error / total_forecasts
            avg_percentage_error = total_percentage_error / total_forecasts
            coverage_percentage = (within_bounds_count / total_forecasts) * 100
            
            result = {
                'model_id': model_id,
                'model_name': forecast_model.name,
                'evaluation_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days_back
                },
                'summary_metrics': {
                    'total_forecasts_evaluated': total_forecasts,
                    'average_absolute_error': avg_absolute_error,
                    'average_percentage_error': avg_percentage_error,
                    'interval_coverage_percentage': coverage_percentage,
                    'accuracy_score': max(0, 100 - avg_percentage_error)
                },
                'detailed_accuracy': accuracy_records
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluando precisión en tiempo real del modelo {model_id}: {str(e)}")
            raise
    
    def generate_model_performance_report(self,
                                        company_id: int,
                                        period_days: int = 30) -> Dict[str, Any]:
        """
        Genera un reporte completo de rendimiento de modelos para una empresa
        
        Args:
            company_id: ID de la empresa
            period_days: Período de análisis en días
            
        Returns:
            Reporte completo de rendimiento
        """
        try:
            company = Company.objects.get(id=company_id)
            
            # Obtiene todos los modelos activos de la empresa
            active_models = ForecastModel.objects.filter(
                company=company,
                status='active'
            )
            
            if not active_models.exists():
                return {'error': 'No hay modelos activos para evaluar'}
            
            model_reports = []
            overall_metrics = {
                'total_mae': 0,
                'total_mape': 0,
                'total_forecasts': 0,
                'models_count': 0
            }
            
            for model in active_models:
                try:
                    # Evaluación de precisión
                    accuracy_eval = self.evaluate_forecast_accuracy_realtime(
                        model.id, 
                        days_back=period_days
                    )
                    
                    # Métricas del modelo
                    model_metrics = {
                        'model_id': model.id,
                        'model_name': model.name,
                        'model_type': model.model_type,
                        'training_date': model.training_completed_at.isoformat() if model.training_completed_at else None,
                        'last_prediction': model.last_prediction_at.isoformat() if model.last_prediction_at else None,
                        'stored_mae': float(model.mae or 0),
                        'stored_mape': float(model.mape or 0),
                        'realtime_accuracy': accuracy_eval.get('summary_metrics', {})
                    }
                    
                    # Estadísticas de uso
                    usage_stats = self._get_model_usage_statistics(model, period_days)
                    model_metrics['usage_statistics'] = usage_stats
                    
                    model_reports.append(model_metrics)
                    
                    # Acumula para métricas generales
                    if 'error' not in accuracy_eval:
                        overall_metrics['total_mae'] += accuracy_eval.get('summary_metrics', {}).get('average_absolute_error', 0)
                        overall_metrics['total_mape'] += accuracy_eval.get('summary_metrics', {}).get('average_percentage_error', 0)
                        overall_metrics['models_count'] += 1
                    
                    overall_metrics['total_forecasts'] += usage_stats.get('forecasts_generated', 0)
                    
                except Exception as e:
                    logger.warning(f"Error evaluando modelo {model.id}: {str(e)}")
                    model_reports.append({
                        'model_id': model.id,
                        'model_name': model.name,
                        'error': str(e)
                    })
            
            # Calcula métricas promedio
            if overall_metrics['models_count'] > 0:
                overall_metrics['average_mae'] = overall_metrics['total_mae'] / overall_metrics['models_count']
                overall_metrics['average_mape'] = overall_metrics['total_mape'] / overall_metrics['models_count']
            
            # Identifica mejores y peores modelos
            successful_models = [m for m in model_reports if 'error' not in m and 'realtime_accuracy' in m]
            
            best_model = None
            worst_model = None
            
            if successful_models:
                best_model = min(successful_models, 
                               key=lambda x: x['realtime_accuracy'].get('average_percentage_error', float('inf')))
                worst_model = max(successful_models,
                                key=lambda x: x['realtime_accuracy'].get('average_percentage_error', 0))
            
            report = {
                'company_id': company_id,
                'company_name': company.name,
                'report_period': {
                    'days': period_days,
                    'start_date': (timezone.now().date() - timedelta(days=period_days)).isoformat(),
                    'end_date': timezone.now().date().isoformat()
                },
                'overall_metrics': overall_metrics,
                'models_performance': model_reports,
                'best_performing_model': best_model,
                'worst_performing_model': worst_model,
                'recommendations': self._generate_performance_recommendations(model_reports),
                'generated_at': timezone.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte de rendimiento para empresa {company_id}: {str(e)}")
            raise
    
    def _get_historical_data(self, forecast_model: ForecastModel, days: int) -> pd.DataFrame:
        """
        Obtiene datos históricos para evaluación
        """
        try:
            start_date = timezone.now().date() - timedelta(days=days)
            
            # Obtiene productos del modelo
            products = forecast_model.products.all()
            if not products:
                products = Product.objects.filter(company=forecast_model.company)
            
            # Obtiene transacciones
            transactions = Transaction.objects.filter(
                product__in=products,
                transaction_date__gte=start_date,
                transaction_type__in=['sale', 'usage']
            ).values('transaction_date').annotate(
                quantity=models.Sum('quantity')
            ).order_by('transaction_date')
            
            if not transactions:
                return pd.DataFrame()
            
            # Convierte a DataFrame
            df = pd.DataFrame(list(transactions))
            df['date'] = pd.to_datetime(df['transaction_date'])
            df = df.set_index('date')
            df = df[['quantity']]
            
            # Rellena fechas faltantes
            full_date_range = pd.date_range(start=start_date, end=timezone.now().date(), freq='D')
            df = df.reindex(full_date_range, fill_value=0)
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {str(e)}")
            return pd.DataFrame()
    
    def _retrain_model_for_evaluation(self, forecast_model: ForecastModel, train_data: pd.DataFrame):
        """
        Re-entrena un modelo para evaluación
        """
        try:
            # Determina el tipo de algoritmo
            algorithm_name = forecast_model.model_type
            
            # Entrena el modelo
            model, metrics = self.ml_service.trainer.train_single_model(
                algorithm_name=algorithm_name,
                data=train_data,
                target_column='quantity',
                hyperparameters=forecast_model.hyperparameters
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Error re-entrenando modelo para evaluación: {str(e)}")
            raise
    
    def _update_model_metrics(self, forecast_model: ForecastModel, evaluation_results: Dict[str, Any]) -> None:
        """
        Actualiza métricas del modelo en la base de datos
        """
        try:
            forecast_model.mae = Decimal(str(evaluation_results.get('mae', 0)))
            forecast_model.mape = Decimal(str(evaluation_results.get('mape', 0)))
            forecast_model.rmse = Decimal(str(evaluation_results.get('rmse', 0)))
            forecast_model.r2_score = Decimal(str(evaluation_results.get('r2', 0)))
            forecast_model.save(update_fields=['mae', 'mape', 'rmse', 'r2_score'])
            
        except Exception as e:
            logger.warning(f"Error actualizando métricas del modelo: {str(e)}")
    
    def _calculate_business_metrics(self, 
                                  forecast_model: ForecastModel,
                                  test_data: pd.DataFrame,
                                  ml_model,
                                  evaluation_period_days: int) -> Dict[str, Any]:
        """
        Calcula métricas específicas del negocio
        """
        try:
            # Genera pronósticos para el período de prueba
            predictions = ml_model.predict(len(test_data))
            
            # Calcula métricas de negocio
            predicted_values = predictions['predicted_demand'].values
            actual_values = test_data['quantity'].values
            
            # Precisión de inventario (qué tan bien predice niveles de stock)
            inventory_accuracy = np.mean(np.abs(predicted_values - actual_values) / np.maximum(actual_values, 1))
            
            # Pérdidas por sobre-estimación y sub-estimación
            overestimation_loss = np.sum(np.maximum(predicted_values - actual_values, 0))
            underestimation_loss = np.sum(np.maximum(actual_values - predicted_values, 0))
            
            # Eficiencia de pronóstico (cuánto mejor que un modelo naive)
            naive_forecast = np.full_like(actual_values, np.mean(actual_values))
            naive_mae = np.mean(np.abs(actual_values - naive_forecast))
            model_mae = np.mean(np.abs(actual_values - predicted_values))
            
            forecast_efficiency = max(0, (naive_mae - model_mae) / naive_mae * 100) if naive_mae > 0 else 0
            
            return {
                'inventory_accuracy': float(inventory_accuracy),
                'overestimation_loss': float(overestimation_loss),
                'underestimation_loss': float(underestimation_loss),
                'forecast_efficiency_vs_naive': float(forecast_efficiency)
            }
            
        except Exception as e:
            logger.warning(f"Error calculando métricas de negocio: {str(e)}")
            return {}
    
    def _get_actual_demand(self, 
                         product: Product, 
                         date: datetime.date,
                         location=None) -> Optional[float]:
        """
        Obtiene la demanda real de un producto en una fecha específica
        """
        try:
            filters = {
                'product': product,
                'transaction_date': date,
                'transaction_type__in': ['sale', 'usage']
            }
            
            if location:
                filters['location'] = location
            
            demand = Transaction.objects.filter(**filters).aggregate(
                total=models.Sum('quantity')
            )['total']
            
            return float(demand) if demand is not None else 0.0
            
        except Exception as e:
            logger.warning(f"Error obteniendo demanda real: {str(e)}")
            return None
    
    def _get_model_usage_statistics(self, model: ForecastModel, period_days: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso de un modelo
        """
        try:
            start_date = timezone.now().date() - timedelta(days=period_days)
            
            # Cuenta pronósticos generados
            forecasts_count = DemandForecast.objects.filter(
                model=model,
                created_at__gte=start_date
            ).count()
            
            # Productos únicos pronosticados
            unique_products = DemandForecast.objects.filter(
                model=model,
                created_at__gte=start_date
            ).values('product').distinct().count()
            
            # Ubicaciones únicas
            unique_locations = DemandForecast.objects.filter(
                model=model,
                created_at__gte=start_date
            ).values('location').distinct().count()
            
            return {
                'forecasts_generated': forecasts_count,
                'unique_products_forecasted': unique_products,
                'unique_locations_forecasted': unique_locations,
                'avg_forecasts_per_day': forecasts_count / period_days if period_days > 0 else 0
            }
            
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas de uso: {str(e)}")
            return {}
    
    def _calculate_comparison_summary(self, df: pd.DataFrame, metrics: List[str]) -> Dict[str, Any]:
        """
        Calcula estadísticas de resumen para comparación de modelos
        """
        try:
            summary = {}
            
            for metric in metrics:
                if metric in df.columns:
                    summary[metric] = {
                        'best': float(df[metric].min()) if metric not in ['r2', 'directional_accuracy'] else float(df[metric].max()),
                        'worst': float(df[metric].max()) if metric not in ['r2', 'directional_accuracy'] else float(df[metric].min()),
                        'average': float(df[metric].mean()),
                        'std': float(df[metric].std())
                    }
            
            return summary
            
        except Exception as e:
            logger.warning(f"Error calculando resumen de comparación: {str(e)}")
            return {}
    
    def _generate_performance_recommendations(self, model_reports: List[Dict[str, Any]]) -> List[str]:
        """
        Genera recomendaciones basadas en el rendimiento de los modelos
        """
        recommendations = []
        
        try:
            successful_models = [m for m in model_reports if 'error' not in m and 'realtime_accuracy' in m]
            
            if not successful_models:
                recommendations.append("No hay modelos con evaluaciones exitosas. Revisar configuración y datos.")
                return recommendations
            
            # Analiza precisión general
            avg_mape = np.mean([m['realtime_accuracy'].get('average_percentage_error', 0) for m in successful_models])
            
            if avg_mape > 20:
                recommendations.append("La precisión promedio de los modelos es baja (>20% MAPE). Considerar re-entrenamiento o ajuste de hiperparámetros.")
            elif avg_mape < 10:
                recommendations.append("Excelente precisión promedio de los modelos (<10% MAPE).")
            
            # Analiza variabilidad entre modelos
            mape_values = [m['realtime_accuracy'].get('average_percentage_error', 0) for m in successful_models]
            if np.std(mape_values) > 10:
                recommendations.append("Alta variabilidad en la precisión entre modelos. Considerar estandarizar enfoques o datos.")
            
            # Analiza cobertura de intervalos
            avg_coverage = np.mean([m['realtime_accuracy'].get('interval_coverage_percentage', 0) for m in successful_models])
            if avg_coverage < 80:
                recommendations.append("Baja cobertura de intervalos de confianza (<80%). Revisar calibración de incertidumbre.")
            elif avg_coverage > 95:
                recommendations.append("Intervalos de confianza muy conservadores (>95% cobertura). Considerar ajustar para mayor precisión.")
            
            # Analiza uso de modelos
            total_forecasts = sum([m.get('usage_statistics', {}).get('forecasts_generated', 0) for m in model_reports])
            if total_forecasts < 100:
                recommendations.append("Bajo uso de los modelos de pronóstico. Considerar automatización o integración adicional.")
            
        except Exception as e:
            logger.warning(f"Error generando recomendaciones: {str(e)}")
            recommendations.append("Error generando recomendaciones automáticas. Revisar manualmente.")
        
        return recommendations
