"""
Implementación de ensemble de modelos para pronósticos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta

from .base_forecaster import BaseForecaster
from .prophet_forecaster import ProphetForecaster
from .arima_forecaster import ARIMAForecaster

logger = logging.getLogger(__name__)


class EnsembleForecaster(BaseForecaster):
    """
    Ensemble de múltiples algoritmos de pronóstico
    """
    
    def __init__(self, models: Optional[List[BaseForecaster]] = None,
                 weights: Optional[List[float]] = None,
                 voting_method: str = 'weighted_average',
                 hyperparameters: Optional[Dict[str, Any]] = None):
        """
        Inicializa el ensemble forecaster
        
        Args:
            models: Lista de modelos base a usar en el ensemble
            weights: Pesos para cada modelo (si es None, se usan pesos iguales)
            voting_method: Método de agregación ('weighted_average', 'median', 'best_performer')
            hyperparameters: Parámetros adicionales
        """
        default_params = {
            'voting_method': voting_method,
            'auto_weight_calculation': True,  # Calcular pesos automáticamente basado en rendimiento
            'min_models': 2,  # Mínimo número de modelos para funcionar
            'performance_metric': 'mae',  # Métrica para calcular pesos automáticos
            'cross_validation_folds': 3,  # Folds para validación cruzada
            'outlier_detection': True,  # Detectar y manejar outliers en predicciones
            'outlier_threshold': 2.0  # Umbral para detección de outliers (en desviaciones estándar)
        }
        
        if hyperparameters:
            default_params.update(hyperparameters)
            
        super().__init__(default_params)
        
        # Inicializa modelos por defecto si no se proporcionan
        if models is None:
            self.models = [
                ProphetForecaster(),
                ARIMAForecaster()
            ]
        else:
            self.models = models
            
        # Valida que hay suficientes modelos
        if len(self.models) < self.hyperparameters.get('min_models', 2):
            raise ValueError(f"Se requieren al menos {self.hyperparameters.get('min_models', 2)} modelos para el ensemble")
        
        # Inicializa pesos
        if weights is None:
            self.weights = [1.0 / len(self.models)] * len(self.models)
        else:
            if len(weights) != len(self.models):
                raise ValueError("El número de pesos debe coincidir con el número de modelos")
            # Normaliza los pesos
            weight_sum = sum(weights)
            self.weights = [w / weight_sum for w in weights]
            
        self.model_performances = {}
        self.voting_method = self.hyperparameters.get('voting_method', 'weighted_average')
        
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo"""
        model_names = [model.get_model_name() for model in self.models]
        return f"Ensemble({', '.join(model_names)})"
    
    def add_model(self, model: BaseForecaster, weight: float = None) -> None:
        """
        Añade un modelo al ensemble
        
        Args:
            model: Modelo a añadir
            weight: Peso del modelo (si es None, se calcula automáticamente)
        """
        self.models.append(model)
        
        if weight is None:
            # Recalcula pesos para distribución uniforme
            self.weights = [1.0 / len(self.models)] * len(self.models)
        else:
            self.weights.append(weight)
            # Renormaliza pesos
            weight_sum = sum(self.weights)
            self.weights = [w / weight_sum for w in self.weights]
    
    def remove_model(self, index: int) -> None:
        """
        Remueve un modelo del ensemble
        
        Args:
            index: Índice del modelo a remover
        """
        if index < 0 or index >= len(self.models):
            raise ValueError("Índice de modelo inválido")
            
        if len(self.models) <= self.hyperparameters.get('min_models', 2):
            raise ValueError(f"No se puede remover. Se requieren al menos {self.hyperparameters.get('min_models', 2)} modelos")
        
        self.models.pop(index)
        self.weights.pop(index)
        
        # Renormaliza pesos
        weight_sum = sum(self.weights)
        self.weights = [w / weight_sum for w in self.weights]
    
    def _cross_validate_models(self, data: pd.DataFrame, target_column: str) -> Dict[int, float]:
        """
        Realiza validación cruzada para evaluar el rendimiento de cada modelo
        
        Args:
            data: Datos de entrenamiento
            target_column: Columna objetivo
            
        Returns:
            Diccionario con el rendimiento de cada modelo
        """
        performances = {}
        folds = self.hyperparameters.get('cross_validation_folds', 3)
        
        # Divide los datos en folds
        fold_size = len(data) // folds
        
        for i, model in enumerate(self.models):
            fold_scores = []
            
            for fold in range(folds):
                try:
                    # Define inicio y fin del fold de validación
                    val_start = fold * fold_size
                    val_end = (fold + 1) * fold_size if fold < folds - 1 else len(data)
                    
                    # Datos de entrenamiento (todo excepto el fold actual)
                    train_data = pd.concat([
                        data.iloc[:val_start],
                        data.iloc[val_end:]
                    ])
                    
                    # Datos de validación
                    val_data = data.iloc[val_start:val_end]
                    
                    if len(train_data) < 10 or len(val_data) < 1:
                        continue
                    
                    # Entrena el modelo en el fold
                    model_copy = type(model)(model.get_hyperparameters())
                    model_copy.fit(train_data, target_column)
                    
                    # Hace predicciones
                    predictions = model_copy.predict(len(val_data))
                    
                    # Calcula métricas
                    y_true = val_data[target_column].values
                    y_pred = predictions['predicted_demand'].values
                    
                    if len(y_true) == len(y_pred):
                        metrics = model_copy.calculate_metrics(y_true, y_pred)
                        metric_name = self.hyperparameters.get('performance_metric', 'mae')
                        fold_scores.append(metrics.get(metric_name, float('inf')))
                        
                except Exception as e:
                    logger.warning(f"Error en validación cruzada del modelo {i}: {str(e)}")
                    continue
            
            if fold_scores:
                performances[i] = np.mean(fold_scores)
            else:
                performances[i] = float('inf')
                
        return performances
    
    def _calculate_automatic_weights(self, performances: Dict[int, float]) -> List[float]:
        """
        Calcula pesos automáticamente basado en el rendimiento
        
        Args:
            performances: Rendimiento de cada modelo
            
        Returns:
            Lista de pesos calculados
        """
        # Invierte las puntuaciones (menor error = mayor peso)
        inverted_scores = []
        for i in range(len(self.models)):
            score = performances.get(i, float('inf'))
            if score == float('inf') or score <= 0:
                inverted_scores.append(0.001)  # Peso mínimo
            else:
                inverted_scores.append(1.0 / score)
        
        # Normaliza los pesos
        total_score = sum(inverted_scores)
        if total_score > 0:
            weights = [score / total_score for score in inverted_scores]
        else:
            weights = [1.0 / len(self.models)] * len(self.models)
            
        return weights
    
    def fit(self, data: pd.DataFrame, target_column: str = 'demand') -> 'EnsembleForecaster':
        """
        Entrena todos los modelos del ensemble
        
        Args:
            data: DataFrame con datos históricos
            target_column: Nombre de la columna objetivo
            
        Returns:
            self: Instancia del ensemble entrenado
        """
        try:
            # Valida los datos
            self.validate_data(data, target_column)
            
            # Preprocesa los datos
            processed_data = self.preprocess_data(data, target_column)
            self.training_data = processed_data.copy()
            
            logger.info(f"Entrenando ensemble con {len(self.models)} modelos")
            
            # Si está habilitado el cálculo automático de pesos, realiza validación cruzada
            if self.hyperparameters.get('auto_weight_calculation', True):
                logger.info("Calculando pesos automáticamente mediante validación cruzada...")
                performances = self._cross_validate_models(processed_data, target_column)
                self.weights = self._calculate_automatic_weights(performances)
                self.model_performances = performances
                
                for i, (model, weight, perf) in enumerate(zip(self.models, self.weights, performances.values())):
                    logger.info(f"Modelo {i} ({model.get_model_name()}): peso={weight:.3f}, rendimiento={perf:.3f}")
            
            # Entrena cada modelo individual
            trained_models = []
            for i, model in enumerate(self.models):
                try:
                    logger.info(f"Entrenando modelo {i+1}/{len(self.models)}: {model.get_model_name()}")
                    model.fit(processed_data, target_column)
                    trained_models.append(model)
                    
                except Exception as e:
                    logger.error(f"Error entrenando modelo {model.get_model_name()}: {str(e)}")
                    # Si un modelo falla, ajusta los pesos
                    self.weights[i] = 0
            
            # Actualiza la lista de modelos y pesos
            if len(trained_models) < self.hyperparameters.get('min_models', 2):
                raise ValueError(f"Solo {len(trained_models)} modelos se entrenaron exitosamente. Se requieren al menos {self.hyperparameters.get('min_models', 2)}")
            
            # Renormaliza pesos si algunos modelos fallaron
            weight_sum = sum(self.weights)
            if weight_sum > 0:
                self.weights = [w / weight_sum for w in self.weights]
            
            self.is_fitted = True
            
            # Calcula métricas del ensemble usando predicciones dentro de la muestra
            try:
                ensemble_predictions = self._predict_in_sample(processed_data, target_column)
                y_true = processed_data[target_column].values
                y_pred = ensemble_predictions.values
                
                self.metrics = self.calculate_metrics(y_true, y_pred)
                
                logger.info(f"Ensemble entrenado exitosamente. MAE: {self.metrics['mae']:.2f}, MAPE: {self.metrics['mape']:.2f}%")
                
            except Exception as e:
                logger.warning(f"Error calculando métricas del ensemble: {str(e)}")
                self.metrics = {}
            
            return self
            
        except Exception as e:
            logger.error(f"Error entrenando ensemble: {str(e)}")
            raise
    
    def _predict_in_sample(self, data: pd.DataFrame, target_column: str) -> pd.Series:
        """
        Genera predicciones dentro de la muestra para evaluar el ensemble
        """
        predictions = []
        
        for model, weight in zip(self.models, self.weights):
            if weight > 0 and model.is_fitted:
                try:
                    # Para modelos que no tienen predicción dentro de muestra,
                    # usa la última parte de los datos para validación
                    val_size = min(30, len(data) // 4)
                    train_subset = data.iloc[:-val_size]
                    val_subset = data.iloc[-val_size:]
                    
                    # Crea una copia del modelo y entrena con subconjunto
                    model_copy = type(model)(model.get_hyperparameters())
                    model_copy.fit(train_subset, target_column)
                    
                    # Predice el subconjunto de validación
                    model_pred = model_copy.predict(len(val_subset))
                    
                    predictions.append(model_pred['predicted_demand'] * weight)
                    
                except Exception:
                    # Si falla, usa los últimos valores observados
                    last_values = data[target_column].iloc[-30:].mean()
                    dummy_pred = pd.Series([last_values] * 30, index=data.index[-30:])
                    predictions.append(dummy_pred * weight)
        
        if predictions:
            return sum(predictions)
        else:
            return pd.Series([0] * len(data), index=data.index)
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Genera pronósticos usando el ensemble de modelos
        
        Args:
            periods: Número de períodos a pronosticar
            confidence_interval: Nivel de confianza
            
        Returns:
            DataFrame con pronósticos agregados y intervalos de confianza
        """
        if not self.is_fitted:
            raise ValueError("El ensemble debe ser entrenado antes de hacer predicciones")
        
        try:
            # Obtiene predicciones de cada modelo
            model_predictions = []
            model_weights = []
            
            for model, weight in zip(self.models, self.weights):
                if weight > 0 and model.is_fitted:
                    try:
                        pred = model.predict(periods, confidence_interval)
                        model_predictions.append(pred)
                        model_weights.append(weight)
                        
                    except Exception as e:
                        logger.warning(f"Error obteniendo predicciones de {model.get_model_name()}: {str(e)}")
                        continue
            
            if not model_predictions:
                raise ValueError("Ningún modelo pudo generar predicciones")
            
            # Combina las predicciones según el método de votación
            ensemble_result = self._aggregate_predictions(
                model_predictions, 
                model_weights, 
                confidence_interval
            )
            
            logger.info(f"Generados {periods} pronósticos usando ensemble de {len(model_predictions)} modelos")
            
            return ensemble_result
            
        except Exception as e:
            logger.error(f"Error generando pronósticos con ensemble: {str(e)}")
            raise
    
    def _aggregate_predictions(self, predictions: List[pd.DataFrame], 
                             weights: List[float], 
                             confidence_interval: float) -> pd.DataFrame:
        """
        Agrega las predicciones de múltiples modelos
        
        Args:
            predictions: Lista de DataFrames con predicciones
            weights: Pesos correspondientes
            confidence_interval: Nivel de confianza
            
        Returns:
            DataFrame con predicciones agregadas
        """
        if not predictions:
            raise ValueError("No hay predicciones para agregar")
        
        # Normaliza los pesos
        weight_sum = sum(weights)
        normalized_weights = [w / weight_sum for w in weights]
        
        # Obtiene las fechas (asume que todos los modelos usan las mismas fechas)
        dates = predictions[0].index
        
        if self.voting_method == 'weighted_average':
            # Promedio ponderado
            aggregated_demand = sum(
                pred['predicted_demand'] * weight 
                for pred, weight in zip(predictions, normalized_weights)
            )
            
            aggregated_lower = sum(
                pred['lower_bound'] * weight 
                for pred, weight in zip(predictions, normalized_weights)
            )
            
            aggregated_upper = sum(
                pred['upper_bound'] * weight 
                for pred, weight in zip(predictions, normalized_weights)
            )
            
        elif self.voting_method == 'median':
            # Mediana de las predicciones
            demand_matrix = np.column_stack([pred['predicted_demand'].values for pred in predictions])
            lower_matrix = np.column_stack([pred['lower_bound'].values for pred in predictions])
            upper_matrix = np.column_stack([pred['upper_bound'].values for pred in predictions])
            
            aggregated_demand = pd.Series(np.median(demand_matrix, axis=1), index=dates)
            aggregated_lower = pd.Series(np.median(lower_matrix, axis=1), index=dates)
            aggregated_upper = pd.Series(np.median(upper_matrix, axis=1), index=dates)
            
        elif self.voting_method == 'best_performer':
            # Usa el mejor modelo basado en rendimiento histórico
            if self.model_performances:
                best_model_idx = min(self.model_performances.keys(), 
                                   key=lambda k: self.model_performances[k])
                best_prediction = predictions[best_model_idx]
                
                aggregated_demand = best_prediction['predicted_demand']
                aggregated_lower = best_prediction['lower_bound']
                aggregated_upper = best_prediction['upper_bound']
            else:
                # Fallback a promedio ponderado
                aggregated_demand = sum(
                    pred['predicted_demand'] * weight 
                    for pred, weight in zip(predictions, normalized_weights)
                )
                aggregated_lower = sum(
                    pred['lower_bound'] * weight 
                    for pred, weight in zip(predictions, normalized_weights)
                )
                aggregated_upper = sum(
                    pred['upper_bound'] * weight 
                    for pred, weight in zip(predictions, normalized_weights)
                )
        else:
            raise ValueError(f"Método de votación no reconocido: {self.voting_method}")
        
        # Detecta y maneja outliers si está habilitado
        if self.hyperparameters.get('outlier_detection', True):
            aggregated_demand = self._handle_outliers(aggregated_demand)
        
        # Construye el resultado final
        result = pd.DataFrame({
            'predicted_demand': aggregated_demand,
            'lower_bound': aggregated_lower,
            'upper_bound': aggregated_upper,
            'confidence_level': confidence_interval
        }, index=dates)
        
        # Asegura que no haya valores negativos
        result['predicted_demand'] = result['predicted_demand'].clip(lower=0)
        result['lower_bound'] = result['lower_bound'].clip(lower=0)
        result['upper_bound'] = result['upper_bound'].clip(lower=0)
        
        return result
    
    def _handle_outliers(self, series: pd.Series) -> pd.Series:
        """
        Detecta y suaviza outliers en las predicciones
        
        Args:
            series: Serie con predicciones
            
        Returns:
            Serie con outliers suavizados
        """
        try:
            threshold = self.hyperparameters.get('outlier_threshold', 2.0)
            
            # Calcula estadísticas de la serie
            mean_val = series.mean()
            std_val = series.std()
            
            if std_val == 0:
                return series
            
            # Identifica outliers
            z_scores = np.abs((series - mean_val) / std_val)
            outliers = z_scores > threshold
            
            if outliers.any():
                logger.info(f"Detectados {outliers.sum()} outliers en las predicciones")
                
                # Suaviza outliers usando interpolación
                series_clean = series.copy()
                series_clean[outliers] = np.nan
                series_clean = series_clean.interpolate(method='linear')
                
                return series_clean
            
            return series
            
        except Exception as e:
            logger.warning(f"Error manejando outliers: {str(e)}")
            return series
    
    def get_model_weights(self) -> Dict[str, float]:
        """
        Obtiene los pesos de cada modelo en el ensemble
        
        Returns:
            Diccionario con nombres de modelos y sus pesos
        """
        return {
            model.get_model_name(): weight 
            for model, weight in zip(self.models, self.weights)
        }
    
    def get_model_performances(self) -> Dict[str, float]:
        """
        Obtiene el rendimiento de cada modelo
        
        Returns:
            Diccionario con nombres de modelos y su rendimiento
        """
        if not self.model_performances:
            return {}
            
        return {
            self.models[i].get_model_name(): perf
            for i, perf in self.model_performances.items()
        }
