"""
Evaluador de modelos de machine learning para pronósticos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
import json
import warnings
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .base_forecaster import BaseForecaster

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class ModelEvaluator:
    """
    Evaluador de modelos de pronóstico con métricas avanzadas y análisis de performance
    """
    
    def __init__(self):
        """
        Inicializa el evaluador de modelos
        """
        self.evaluation_history = []
        self.benchmark_models = {}
        
    def evaluate_model(self,
                      model: BaseForecaster,
                      test_data: pd.DataFrame,
                      target_column: str = 'demand',
                      forecast_periods: Optional[int] = None) -> Dict[str, Any]:
        """
        Evalúa un modelo de pronóstico contra datos de prueba
        
        Args:
            model: Modelo a evaluar
            test_data: Datos de prueba
            target_column: Columna objetivo
            forecast_periods: Períodos a pronosticar (si None, usa toda la longitud de test_data)
            
        Returns:
            Diccionario con métricas de evaluación
        """
        if not model.is_fitted:
            raise ValueError("El modelo debe estar entrenado antes de evaluarlo")
        
        if forecast_periods is None:
            forecast_periods = len(test_data)
        
        try:
            start_time = datetime.now()
            
            # Genera pronósticos
            predictions = model.predict(forecast_periods)
            
            end_time = datetime.now()
            prediction_time = (end_time - start_time).total_seconds()
            
            # Alinea predicciones con datos reales
            y_true, y_pred, prediction_dates = self._align_predictions_with_actual(
                test_data, predictions, target_column
            )
            
            if len(y_true) == 0:
                raise ValueError("No se pudieron alinear las predicciones con los datos reales")
            
            # Calcula métricas básicas
            basic_metrics = self._calculate_basic_metrics(y_true, y_pred)
            
            # Calcula métricas avanzadas
            advanced_metrics = self._calculate_advanced_metrics(y_true, y_pred, predictions)
            
            # Calcula métricas de intervalos de confianza
            interval_metrics = self._calculate_interval_metrics(
                y_true, predictions, prediction_dates
            )
            
            # Análisis de residuales
            residual_analysis = self._analyze_residuals(y_true, y_pred)
            
            # Análisis de direccionalidad
            directional_metrics = self._calculate_directional_metrics(y_true, y_pred)
            
            # Combina todas las métricas
            evaluation_result = {
                'model_name': model.get_model_name(),
                'evaluation_timestamp': datetime.now(),
                'prediction_time_seconds': prediction_time,
                'data_points_evaluated': len(y_true),
                'forecast_horizon': forecast_periods,
                **basic_metrics,
                **advanced_metrics,
                **interval_metrics,
                **residual_analysis,
                **directional_metrics
            }
            
            # Registra la evaluación
            self.evaluation_history.append(evaluation_result)
            
            logger.info(f"Modelo {model.get_model_name()} evaluado: MAE={basic_metrics['mae']:.2f}, MAPE={basic_metrics['mape']:.2f}%")
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error evaluando modelo: {str(e)}")
            raise
    
    def _align_predictions_with_actual(self,
                                     test_data: pd.DataFrame,
                                     predictions: pd.DataFrame,
                                     target_column: str) -> Tuple[np.ndarray, np.ndarray, pd.DatetimeIndex]:
        """
        Alinea las predicciones con los datos reales
        """
        # Obtiene las fechas de las predicciones
        pred_dates = predictions.index
        
        # Filtra datos de prueba para las fechas correspondientes
        common_dates = test_data.index.intersection(pred_dates)
        
        if len(common_dates) == 0:
            # Si no hay intersección directa, intenta alinear por posición
            min_length = min(len(test_data), len(predictions))
            y_true = test_data[target_column].iloc[:min_length].values
            y_pred = predictions['predicted_demand'].iloc[:min_length].values
            prediction_dates = predictions.index[:min_length]
        else:
            # Usa fechas comunes
            y_true = test_data.loc[common_dates, target_column].values
            y_pred = predictions.loc[common_dates, 'predicted_demand'].values
            prediction_dates = common_dates
        
        # Elimina valores NaN
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true = y_true[mask]
        y_pred = y_pred[mask]
        prediction_dates = prediction_dates[mask]
        
        return y_true, y_pred, prediction_dates
    
    def _calculate_basic_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calcula métricas básicas de evaluación
        """
        metrics = {}
        
        # Error Absoluto Medio (MAE)
        metrics['mae'] = mean_absolute_error(y_true, y_pred)
        
        # Error Cuadrático Medio (MSE) y Raíz del Error Cuadrático Medio (RMSE)
        mse = mean_squared_error(y_true, y_pred)
        metrics['mse'] = mse
        metrics['rmse'] = np.sqrt(mse)
        
        # Error Porcentual Absoluto Medio (MAPE)
        mask = y_true != 0
        if mask.any():
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            metrics['mape'] = mape
        else:
            metrics['mape'] = float('inf')
        
        # Error Porcentual Medio (MPE) - detecta sesgo
        if mask.any():
            mpe = np.mean((y_true[mask] - y_pred[mask]) / y_true[mask]) * 100
            metrics['mpe'] = mpe
        else:
            metrics['mpe'] = 0
        
        # Coeficiente de Determinación (R²)
        metrics['r2'] = r2_score(y_true, y_pred)
        
        # Error Absoluto Mediano (MAD)
        metrics['mad'] = np.median(np.abs(y_true - y_pred))
        
        return metrics
    
    def _calculate_advanced_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, 
                                  predictions: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula métricas avanzadas de evaluación
        """
        metrics = {}
        
        # SMAPE (Symmetric Mean Absolute Percentage Error)
        denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
        mask = denominator != 0
        if mask.any():
            smape = np.mean(np.abs(y_true[mask] - y_pred[mask]) / denominator[mask]) * 100
            metrics['smape'] = smape
        else:
            metrics['smape'] = 0
        
        # WAPE (Weighted Absolute Percentage Error)
        if np.sum(np.abs(y_true)) > 0:
            wape = np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true)) * 100
            metrics['wape'] = wape
        else:
            metrics['wape'] = float('inf')
        
        # MASE (Mean Absolute Scaled Error) - requiere datos de entrenamiento
        # Por simplicidad, usa la diferencia media de la serie actual
        if len(y_true) > 1:
            naive_forecast_error = np.mean(np.abs(np.diff(y_true)))
            if naive_forecast_error > 0:
                mase = metrics['mae'] / naive_forecast_error
                metrics['mase'] = mase
            else:
                metrics['mase'] = float('inf')
        else:
            metrics['mase'] = float('inf')
        
        # Theil's U statistic
        if len(y_true) > 1:
            numerator = np.sqrt(np.mean((y_pred - y_true) ** 2))
            denominator = np.sqrt(np.mean(y_pred ** 2)) + np.sqrt(np.mean(y_true ** 2))
            if denominator > 0:
                theil_u = numerator / denominator
                metrics['theil_u'] = theil_u
            else:
                metrics['theil_u'] = float('inf')
        else:
            metrics['theil_u'] = float('inf')
        
        # Accuracy (porcentaje de predicciones dentro de un rango aceptable)
        tolerance = 0.1  # 10% de tolerancia
        within_tolerance = np.abs((y_true - y_pred) / np.where(y_true != 0, y_true, 1)) <= tolerance
        metrics['accuracy_10_percent'] = np.mean(within_tolerance) * 100
        
        return metrics
    
    def _calculate_interval_metrics(self, y_true: np.ndarray, 
                                  predictions: pd.DataFrame,
                                  prediction_dates: pd.DatetimeIndex) -> Dict[str, float]:
        """
        Calcula métricas de intervalos de confianza
        """
        metrics = {}
        
        if 'lower_bound' in predictions.columns and 'upper_bound' in predictions.columns:
            # Alinea intervalos con datos reales
            aligned_predictions = predictions.loc[prediction_dates]
            lower_bounds = aligned_predictions['lower_bound'].values
            upper_bounds = aligned_predictions['upper_bound'].values
            
            # Coverage (porcentaje de valores reales dentro de los intervalos)
            within_bounds = (y_true >= lower_bounds) & (y_true <= upper_bounds)
            metrics['coverage'] = np.mean(within_bounds) * 100
            
            # Ancho promedio de los intervalos
            interval_widths = upper_bounds - lower_bounds
            metrics['mean_interval_width'] = np.mean(interval_widths)
            metrics['median_interval_width'] = np.median(interval_widths)
            
            # Interval Score (penaliza tanto la falta de cobertura como intervalos amplios)
            alpha = 0.1  # Para 90% de confianza
            interval_score = []
            for i in range(len(y_true)):
                score = interval_widths[i]
                if y_true[i] < lower_bounds[i]:
                    score += (2 / alpha) * (lower_bounds[i] - y_true[i])
                elif y_true[i] > upper_bounds[i]:
                    score += (2 / alpha) * (y_true[i] - upper_bounds[i])
                interval_score.append(score)
            
            metrics['mean_interval_score'] = np.mean(interval_score)
            
        return metrics
    
    def _analyze_residuals(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Analiza los residuales del modelo
        """
        residuals = y_true - y_pred
        metrics = {}
        
        # Estadísticas básicas de residuales
        metrics['residuals_mean'] = np.mean(residuals)
        metrics['residuals_std'] = np.std(residuals)
        metrics['residuals_skewness'] = self._calculate_skewness(residuals)
        metrics['residuals_kurtosis'] = self._calculate_kurtosis(residuals)
        
        # Test de normalidad (simplificado)
        # Shapiro-Wilk alternativo usando z-scores
        z_scores = (residuals - np.mean(residuals)) / np.std(residuals)
        metrics['residuals_normality_score'] = 1 - np.mean(np.abs(z_scores) > 2)  # % dentro de 2 std
        
        # Autocorrelación de residuales (lag 1)
        if len(residuals) > 1:
            autocorr_lag1 = np.corrcoef(residuals[:-1], residuals[1:])[0, 1]
            metrics['residuals_autocorr_lag1'] = autocorr_lag1 if not np.isnan(autocorr_lag1) else 0
        else:
            metrics['residuals_autocorr_lag1'] = 0
        
        # Heteroscedasticidad (correlación entre residuales y predicciones)
        if np.std(y_pred) > 0:
            heteroscedasticity = np.corrcoef(np.abs(residuals), y_pred)[0, 1]
            metrics['heteroscedasticity'] = heteroscedasticity if not np.isnan(heteroscedasticity) else 0
        else:
            metrics['heteroscedasticity'] = 0
        
        return metrics
    
    def _calculate_directional_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calcula métricas de direccionalidad (capacidad de predecir la dirección del cambio)
        """
        metrics = {}
        
        if len(y_true) < 2:
            return metrics
        
        # Direcciones reales y predichas
        actual_directions = np.diff(y_true) > 0
        predicted_directions = np.diff(y_pred) > 0
        
        # Precisión direccional
        correct_directions = actual_directions == predicted_directions
        metrics['directional_accuracy'] = np.mean(correct_directions) * 100
        
        # Precision y Recall para direcciones al alza
        if np.any(actual_directions):
            # Precision: de las predicciones al alza, cuántas fueron correctas
            predicted_up = predicted_directions
            actual_up = actual_directions
            
            if np.any(predicted_up):
                precision_up = np.mean(actual_up[predicted_up])
                metrics['up_direction_precision'] = precision_up * 100
            else:
                metrics['up_direction_precision'] = 0
            
            # Recall: de los movimientos al alza reales, cuántos fueron predichos
            recall_up = np.mean(predicted_up[actual_up])
            metrics['up_direction_recall'] = recall_up * 100
        else:
            metrics['up_direction_precision'] = 0
            metrics['up_direction_recall'] = 0
        
        return metrics
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """
        Calcula la asimetría de los datos
        """
        if len(data) < 3 or np.std(data) == 0:
            return 0
        
        mean_val = np.mean(data)
        std_val = np.std(data)
        n = len(data)
        
        skewness = (n / ((n - 1) * (n - 2))) * np.sum(((data - mean_val) / std_val) ** 3)
        return skewness
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """
        Calcula la curtosis de los datos
        """
        if len(data) < 4 or np.std(data) == 0:
            return 0
        
        mean_val = np.mean(data)
        std_val = np.std(data)
        n = len(data)
        
        kurtosis = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * np.sum(((data - mean_val) / std_val) ** 4) - \
                  (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))
        return kurtosis
    
    def compare_models(self, models: List[BaseForecaster],
                      test_data: pd.DataFrame,
                      target_column: str = 'demand',
                      metrics_to_compare: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Compara múltiples modelos en los mismos datos de prueba
        
        Args:
            models: Lista de modelos a comparar
            test_data: Datos de prueba
            target_column: Columna objetivo
            metrics_to_compare: Lista de métricas a incluir en la comparación
            
        Returns:
            DataFrame con comparación de modelos
        """
        if metrics_to_compare is None:
            metrics_to_compare = ['mae', 'mape', 'rmse', 'r2', 'smape', 'directional_accuracy']
        
        comparison_results = []
        
        for model in models:
            try:
                evaluation = self.evaluate_model(model, test_data, target_column)
                
                model_result = {'model_name': model.get_model_name()}
                for metric in metrics_to_compare:
                    model_result[metric] = evaluation.get(metric, np.nan)
                
                comparison_results.append(model_result)
                
            except Exception as e:
                logger.warning(f"Error evaluando modelo {model.get_model_name()}: {str(e)}")
                continue
        
        comparison_df = pd.DataFrame(comparison_results)
        
        if not comparison_df.empty:
            # Ordena por la primera métrica
            if len(metrics_to_compare) > 0 and metrics_to_compare[0] in comparison_df.columns:
                ascending = metrics_to_compare[0] not in ['r2', 'directional_accuracy']  # Métricas donde menor es mejor
                comparison_df = comparison_df.sort_values(by=metrics_to_compare[0], ascending=ascending)
        
        return comparison_df
    
    def benchmark_model(self, model: BaseForecaster,
                       test_data: pd.DataFrame,
                       target_column: str = 'demand',
                       benchmark_name: str = 'default') -> Dict[str, Any]:
        """
        Establece un modelo como benchmark y compara otros modelos contra él
        
        Args:
            model: Modelo a usar como benchmark
            test_data: Datos de prueba
            target_column: Columna objetivo
            benchmark_name: Nombre del benchmark
            
        Returns:
            Diccionario con métricas del benchmark
        """
        benchmark_metrics = self.evaluate_model(model, test_data, target_column)
        self.benchmark_models[benchmark_name] = benchmark_metrics
        
        logger.info(f"Benchmark '{benchmark_name}' establecido con {model.get_model_name()}")
        
        return benchmark_metrics
    
    def compare_against_benchmark(self, model: BaseForecaster,
                                test_data: pd.DataFrame,
                                target_column: str = 'demand',
                                benchmark_name: str = 'default') -> Dict[str, Any]:
        """
        Compara un modelo contra un benchmark establecido
        
        Args:
            model: Modelo a comparar
            test_data: Datos de prueba
            target_column: Columna objetivo
            benchmark_name: Nombre del benchmark
            
        Returns:
            Diccionario con comparación detallada
        """
        if benchmark_name not in self.benchmark_models:
            raise ValueError(f"Benchmark '{benchmark_name}' no existe")
        
        model_metrics = self.evaluate_model(model, test_data, target_column)
        benchmark_metrics = self.benchmark_models[benchmark_name]
        
        comparison = {
            'model_name': model.get_model_name(),
            'benchmark_name': benchmark_name,
            'model_metrics': model_metrics,
            'benchmark_metrics': benchmark_metrics,
            'improvements': {}
        }
        
        # Calcula mejoras
        for metric in ['mae', 'mape', 'rmse', 'smape']:
            if metric in model_metrics and metric in benchmark_metrics:
                model_val = model_metrics[metric]
                benchmark_val = benchmark_metrics[metric]
                
                if benchmark_val != 0:
                    improvement = ((benchmark_val - model_val) / benchmark_val) * 100
                    comparison['improvements'][f'{metric}_improvement_percent'] = improvement
        
        # Para métricas donde mayor es mejor
        for metric in ['r2', 'directional_accuracy']:
            if metric in model_metrics and metric in benchmark_metrics:
                model_val = model_metrics[metric]
                benchmark_val = benchmark_metrics[metric]
                
                improvement = model_val - benchmark_val
                comparison['improvements'][f'{metric}_improvement_points'] = improvement
        
        return comparison
    
    def generate_evaluation_report(self, evaluation_results: List[Dict[str, Any]]) -> str:
        """
        Genera un reporte de evaluación en formato texto
        
        Args:
            evaluation_results: Lista de resultados de evaluación
            
        Returns:
            String con reporte formateado
        """
        if not evaluation_results:
            return "No hay resultados de evaluación disponibles."
        
        report = "="*60 + "\n"
        report += "REPORTE DE EVALUACIÓN DE MODELOS\n"
        report += "="*60 + "\n\n"
        
        for i, result in enumerate(evaluation_results, 1):
            report += f"MODELO {i}: {result['model_name']}\n"
            report += "-"*40 + "\n"
            
            # Métricas principales
            report += f"MAE:                    {result.get('mae', 'N/A'):.4f}\n"
            report += f"MAPE:                   {result.get('mape', 'N/A'):.2f}%\n"
            report += f"RMSE:                   {result.get('rmse', 'N/A'):.4f}\n"
            report += f"R²:                     {result.get('r2', 'N/A'):.4f}\n"
            report += f"SMAPE:                  {result.get('smape', 'N/A'):.2f}%\n"
            
            # Métricas de intervalos
            if 'coverage' in result:
                report += f"Cobertura de intervalos: {result['coverage']:.1f}%\n"
            
            # Métricas direccionales
            if 'directional_accuracy' in result:
                report += f"Precisión direccional:   {result['directional_accuracy']:.1f}%\n"
            
            report += f"Tiempo de predicción:    {result.get('prediction_time_seconds', 'N/A'):.3f}s\n"
            report += f"Puntos evaluados:        {result.get('data_points_evaluated', 'N/A')}\n"
            
            report += "\n"
        
        return report
    
    def get_evaluation_history(self) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de evaluaciones
        
        Returns:
            Lista con evaluaciones realizadas
        """
        return self.evaluation_history.copy()
    
    def save_evaluation_results(self, filepath: str, results: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Guarda resultados de evaluación en un archivo JSON
        
        Args:
            filepath: Ruta donde guardar los resultados
            results: Resultados a guardar (si None, usa el historial completo)
        """
        if results is None:
            results = self.evaluation_history
        
        try:
            # Convierte datetime a string para serialización JSON
            results_for_json = []
            for result in results:
                result_copy = result.copy()
                if 'evaluation_timestamp' in result_copy:
                    result_copy['evaluation_timestamp'] = result_copy['evaluation_timestamp'].isoformat()
                results_for_json.append(result_copy)
            
            with open(filepath, 'w') as f:
                json.dump(results_for_json, f, indent=2)
            
            logger.info(f"Resultados de evaluación guardados en {filepath}")
            
        except Exception as e:
            logger.error(f"Error guardando resultados: {str(e)}")
    
    def clear_evaluation_history(self) -> None:
        """
        Limpia el historial de evaluaciones
        """
        self.evaluation_history = []
        logger.info("Historial de evaluaciones limpiado")
