"""
Entrenador automático de modelos de machine learning
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union, Type
import logging
from datetime import datetime, timedelta
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_forecaster import BaseForecaster
from .prophet_forecaster import ProphetForecaster
from .arima_forecaster import ARIMAForecaster
from .ensemble_forecaster import EnsembleForecaster

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Entrenador automático de modelos de pronóstico con optimización de hiperparámetros
    """
    
    def __init__(self, model_storage_path: str = 'models/'):
        """
        Inicializa el entrenador de modelos
        
        Args:
            model_storage_path: Ruta donde guardar los modelos entrenados
        """
        self.model_storage_path = model_storage_path
        self.available_algorithms = {
            'prophet': ProphetForecaster,
            'arima': ARIMAForecaster,
            'ensemble': EnsembleForecaster
        }
        self.training_history = []
        
        # Crea el directorio de modelos si no existe
        os.makedirs(model_storage_path, exist_ok=True)
    
    def register_algorithm(self, name: str, algorithm_class: Type[BaseForecaster]) -> None:
        """
        Registra un nuevo algoritmo disponible
        
        Args:
            name: Nombre del algoritmo
            algorithm_class: Clase del algoritmo
        """
        self.available_algorithms[name] = algorithm_class
        logger.info(f"Algoritmo '{name}' registrado exitosamente")
    
    def get_available_algorithms(self) -> List[str]:
        """
        Obtiene la lista de algoritmos disponibles
        
        Returns:
            Lista de nombres de algoritmos
        """
        return list(self.available_algorithms.keys())
    
    def train_single_model(self, 
                          algorithm_name: str,
                          data: pd.DataFrame,
                          target_column: str = 'demand',
                          hyperparameters: Optional[Dict[str, Any]] = None,
                          model_name: Optional[str] = None) -> Tuple[BaseForecaster, Dict[str, Any]]:
        """
        Entrena un solo modelo
        
        Args:
            algorithm_name: Nombre del algoritmo a usar
            data: Datos de entrenamiento
            target_column: Columna objetivo
            hyperparameters: Hiperparámetros específicos
            model_name: Nombre del modelo (para guardado)
            
        Returns:
            Tuple con (modelo_entrenado, métricas)
        """
        if algorithm_name not in self.available_algorithms:
            raise ValueError(f"Algoritmo '{algorithm_name}' no disponible. Algoritmos disponibles: {list(self.available_algorithms.keys())}")
        
        try:
            start_time = datetime.now()
            
            # Crea la instancia del modelo
            algorithm_class = self.available_algorithms[algorithm_name]
            model = algorithm_class(hyperparameters)
            
            logger.info(f"Iniciando entrenamiento de {algorithm_name} con {len(data)} observaciones")
            
            # Entrena el modelo
            model.fit(data, target_column)
            
            end_time = datetime.now()
            training_duration = end_time - start_time
            
            # Guarda el modelo si se especifica un nombre
            if model_name:
                model_path = os.path.join(self.model_storage_path, f"{model_name}_{algorithm_name}.joblib")
                model.save_model(model_path)
            
            # Registra el entrenamiento
            training_record = {
                'algorithm': algorithm_name,
                'model_name': model_name,
                'training_start': start_time,
                'training_end': end_time,
                'training_duration_seconds': training_duration.total_seconds(),
                'data_points': len(data),
                'hyperparameters': hyperparameters or {},
                'metrics': model.metrics,
                'success': True
            }
            
            self.training_history.append(training_record)
            
            logger.info(f"Modelo {algorithm_name} entrenado exitosamente en {training_duration.total_seconds():.2f}s")
            
            return model, model.metrics
            
        except Exception as e:
            error_msg = f"Error entrenando modelo {algorithm_name}: {str(e)}"
            logger.error(error_msg)
            
            # Registra el error
            training_record = {
                'algorithm': algorithm_name,
                'model_name': model_name,
                'training_start': start_time,
                'training_end': datetime.now(),
                'error': str(e),
                'success': False
            }
            self.training_history.append(training_record)
            
            raise RuntimeError(error_msg)
    
    def train_multiple_models(self,
                            algorithm_names: List[str],
                            data: pd.DataFrame,
                            target_column: str = 'demand',
                            hyperparameters_dict: Optional[Dict[str, Dict[str, Any]]] = None,
                            model_name_prefix: Optional[str] = None,
                            parallel: bool = True,
                            max_workers: int = 3) -> Dict[str, Tuple[BaseForecaster, Dict[str, Any]]]:
        """
        Entrena múltiples modelos
        
        Args:
            algorithm_names: Lista de algoritmos a entrenar
            data: Datos de entrenamiento
            target_column: Columna objetivo
            hyperparameters_dict: Hiperparámetros por algoritmo
            model_name_prefix: Prefijo para nombres de modelos
            parallel: Si entrenar en paralelo
            max_workers: Número máximo de workers para entrenamiento paralelo
            
        Returns:
            Diccionario con {algoritmo: (modelo, métricas)}
        """
        hyperparameters_dict = hyperparameters_dict or {}
        results = {}
        
        if parallel and len(algorithm_names) > 1:
            # Entrenamiento paralelo
            logger.info(f"Entrenando {len(algorithm_names)} modelos en paralelo")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Envía trabajos
                future_to_algorithm = {}
                for algorithm_name in algorithm_names:
                    hyperparams = hyperparameters_dict.get(algorithm_name)
                    model_name = f"{model_name_prefix}_{algorithm_name}" if model_name_prefix else None
                    
                    future = executor.submit(
                        self.train_single_model,
                        algorithm_name,
                        data,
                        target_column,
                        hyperparams,
                        model_name
                    )
                    future_to_algorithm[future] = algorithm_name
                
                # Recolecta resultados
                for future in as_completed(future_to_algorithm):
                    algorithm_name = future_to_algorithm[future]
                    try:
                        model, metrics = future.result()
                        results[algorithm_name] = (model, metrics)
                    except Exception as e:
                        logger.error(f"Error en entrenamiento paralelo de {algorithm_name}: {str(e)}")
                        results[algorithm_name] = (None, {})
        else:
            # Entrenamiento secuencial
            for algorithm_name in algorithm_names:
                try:
                    hyperparams = hyperparameters_dict.get(algorithm_name)
                    model_name = f"{model_name_prefix}_{algorithm_name}" if model_name_prefix else None
                    
                    model, metrics = self.train_single_model(
                        algorithm_name,
                        data,
                        target_column,
                        hyperparams,
                        model_name
                    )
                    results[algorithm_name] = (model, metrics)
                    
                except Exception as e:
                    logger.error(f"Error entrenando {algorithm_name}: {str(e)}")
                    results[algorithm_name] = (None, {})
        
        successful_models = sum(1 for model, _ in results.values() if model is not None)
        logger.info(f"Entrenamiento completado: {successful_models}/{len(algorithm_names)} modelos exitosos")
        
        return results
    
    def hyperparameter_optimization(self,
                                  algorithm_name: str,
                                  data: pd.DataFrame,
                                  target_column: str = 'demand',
                                  param_grid: Optional[Dict[str, List[Any]]] = None,
                                  optimization_metric: str = 'mae',
                                  cv_folds: int = 3,
                                  max_iterations: int = 20) -> Tuple[BaseForecaster, Dict[str, Any], Dict[str, Any]]:
        """
        Optimiza hiperparámetros usando búsqueda en grid o aleatoria
        
        Args:
            algorithm_name: Algoritmo a optimizar
            data: Datos de entrenamiento
            target_column: Columna objetivo
            param_grid: Grid de parámetros a probar
            optimization_metric: Métrica a optimizar
            cv_folds: Número de folds para validación cruzada
            max_iterations: Máximo número de iteraciones
            
        Returns:
            Tuple con (mejor_modelo, mejores_hiperparámetros, histórico_optimización)
        """
        if algorithm_name not in self.available_algorithms:
            raise ValueError(f"Algoritmo '{algorithm_name}' no disponible")
        
        # Define grids por defecto si no se proporcionan
        if param_grid is None:
            param_grid = self._get_default_param_grid(algorithm_name)
        
        logger.info(f"Iniciando optimización de hiperparámetros para {algorithm_name}")
        logger.info(f"Grid de parámetros: {param_grid}")
        
        # Genera combinaciones de parámetros
        param_combinations = self._generate_param_combinations(param_grid, max_iterations)
        
        best_score = float('inf')
        best_params = None
        best_model = None
        optimization_history = []
        
        for i, params in enumerate(param_combinations):
            try:
                logger.info(f"Probando combinación {i+1}/{len(param_combinations)}: {params}")
                
                # Realiza validación cruzada
                cv_scores = self._cross_validate_params(
                    algorithm_name,
                    data,
                    target_column,
                    params,
                    cv_folds,
                    optimization_metric
                )
                
                avg_score = np.mean(cv_scores)
                std_score = np.std(cv_scores)
                
                optimization_history.append({
                    'iteration': i + 1,
                    'parameters': params,
                    'cv_scores': cv_scores,
                    'mean_score': avg_score,
                    'std_score': std_score
                })
                
                logger.info(f"Score promedio: {avg_score:.4f} (±{std_score:.4f})")
                
                # Actualiza mejor resultado
                if avg_score < best_score:
                    best_score = avg_score
                    best_params = params
                    
                    # Entrena modelo con todos los datos usando los mejores parámetros
                    algorithm_class = self.available_algorithms[algorithm_name]
                    best_model = algorithm_class(params)
                    best_model.fit(data, target_column)
                    
                    logger.info(f"Nuevo mejor score: {best_score:.4f}")
                
            except Exception as e:
                logger.warning(f"Error en iteración {i+1}: {str(e)}")
                optimization_history.append({
                    'iteration': i + 1,
                    'parameters': params,
                    'error': str(e)
                })
                continue
        
        if best_model is None:
            raise ValueError("No se pudo encontrar una configuración válida de hiperparámetros")
        
        logger.info(f"Optimización completada. Mejor {optimization_metric}: {best_score:.4f}")
        logger.info(f"Mejores parámetros: {best_params}")
        
        return best_model, best_params, optimization_history
    
    def _get_default_param_grid(self, algorithm_name: str) -> Dict[str, List[Any]]:
        """
        Obtiene grid de parámetros por defecto para cada algoritmo
        """
        if algorithm_name == 'prophet':
            return {
                'seasonality_mode': ['additive', 'multiplicative'],
                'changepoint_prior_scale': [0.01, 0.05, 0.1, 0.5],
                'seasonality_prior_scale': [1.0, 10.0, 20.0],
                'yearly_seasonality': [True, False, 'auto'],
                'weekly_seasonality': [True, False, 'auto']
            }
        elif algorithm_name == 'arima':
            return {
                'auto_arima': [True],
                'seasonal': [True, False],
                'stepwise': [True, False],
                'information_criterion': ['aic', 'bic'],
                'max_p': [3, 5, 7],
                'max_q': [3, 5, 7],
                'max_d': [1, 2]
            }
        else:
            return {}
    
    def _generate_param_combinations(self, param_grid: Dict[str, List[Any]], 
                                   max_combinations: int) -> List[Dict[str, Any]]:
        """
        Genera combinaciones de parámetros limitadas por max_combinations
        """
        import itertools
        
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        # Calcula todas las combinaciones posibles
        all_combinations = list(itertools.product(*values))
        
        # Si hay demasiadas combinaciones, selecciona una muestra aleatoria
        if len(all_combinations) > max_combinations:
            np.random.shuffle(all_combinations)
            selected_combinations = all_combinations[:max_combinations]
        else:
            selected_combinations = all_combinations
        
        # Convierte a lista de diccionarios
        param_combinations = []
        for combination in selected_combinations:
            param_dict = dict(zip(keys, combination))
            param_combinations.append(param_dict)
        
        return param_combinations
    
    def _cross_validate_params(self,
                             algorithm_name: str,
                             data: pd.DataFrame,
                             target_column: str,
                             params: Dict[str, Any],
                             cv_folds: int,
                             metric: str) -> List[float]:
        """
        Realiza validación cruzada para un conjunto de parámetros
        """
        scores = []
        fold_size = len(data) // cv_folds
        
        algorithm_class = self.available_algorithms[algorithm_name]
        
        for fold in range(cv_folds):
            try:
                # Define datos de entrenamiento y validación
                val_start = fold * fold_size
                val_end = (fold + 1) * fold_size if fold < cv_folds - 1 else len(data)
                
                train_data = pd.concat([
                    data.iloc[:val_start],
                    data.iloc[val_end:]
                ])
                val_data = data.iloc[val_start:val_end]
                
                if len(train_data) < 10 or len(val_data) < 1:
                    continue
                
                # Entrena modelo
                model = algorithm_class(params)
                model.fit(train_data, target_column)
                
                # Hace predicciones
                predictions = model.predict(len(val_data))
                
                # Calcula métricas
                y_true = val_data[target_column].values
                y_pred = predictions['predicted_demand'].values
                
                if len(y_true) == len(y_pred):
                    metrics = model.calculate_metrics(y_true, y_pred)
                    scores.append(metrics.get(metric, float('inf')))
                    
            except Exception as e:
                logger.warning(f"Error en fold {fold}: {str(e)}")
                scores.append(float('inf'))
        
        return scores
    
    def auto_train_best_model(self,
                            data: pd.DataFrame,
                            target_column: str = 'demand',
                            algorithms_to_try: Optional[List[str]] = None,
                            optimization_metric: str = 'mae',
                            optimize_hyperparameters: bool = True,
                            model_name: Optional[str] = None) -> Tuple[BaseForecaster, str, Dict[str, Any]]:
        """
        Entrena automáticamente el mejor modelo disponible
        
        Args:
            data: Datos de entrenamiento
            target_column: Columna objetivo
            algorithms_to_try: Algoritmos a probar (None para todos)
            optimization_metric: Métrica para selección del mejor modelo
            optimize_hyperparameters: Si optimizar hiperparámetros
            model_name: Nombre para guardar el modelo
            
        Returns:
            Tuple con (mejor_modelo, nombre_algoritmo, métricas)
        """
        if algorithms_to_try is None:
            algorithms_to_try = list(self.available_algorithms.keys())
        
        logger.info(f"Búsqueda automática del mejor modelo entre: {algorithms_to_try}")
        
        best_model = None
        best_algorithm = None
        best_score = float('inf')
        all_results = {}
        
        for algorithm_name in algorithms_to_try:
            try:
                logger.info(f"Evaluando algoritmo: {algorithm_name}")
                
                if optimize_hyperparameters:
                    # Optimiza hiperparámetros
                    model, best_params, optimization_history = self.hyperparameter_optimization(
                        algorithm_name, data, target_column, optimization_metric=optimization_metric
                    )
                else:
                    # Usa parámetros por defecto
                    model, metrics = self.train_single_model(algorithm_name, data, target_column)
                
                # Evalúa el modelo
                score = model.metrics.get(optimization_metric, float('inf'))
                all_results[algorithm_name] = {
                    'model': model,
                    'score': score,
                    'metrics': model.metrics
                }
                
                logger.info(f"{algorithm_name} - {optimization_metric}: {score:.4f}")
                
                # Actualiza mejor modelo
                if score < best_score:
                    best_score = score
                    best_model = model
                    best_algorithm = algorithm_name
                
            except Exception as e:
                logger.error(f"Error evaluando {algorithm_name}: {str(e)}")
                all_results[algorithm_name] = {
                    'error': str(e),
                    'score': float('inf')
                }
                continue
        
        if best_model is None:
            raise ValueError("No se pudo entrenar ningún modelo exitosamente")
        
        # Guarda el mejor modelo
        if model_name:
            model_path = os.path.join(self.model_storage_path, f"{model_name}_best_{best_algorithm}.joblib")
            best_model.save_model(model_path)
        
        logger.info(f"Mejor modelo seleccionado: {best_algorithm} ({optimization_metric}: {best_score:.4f})")
        
        return best_model, best_algorithm, best_model.metrics
    
    def load_model(self, model_path: str, algorithm_name: str) -> BaseForecaster:
        """
        Carga un modelo previamente entrenado
        
        Args:
            model_path: Ruta del archivo del modelo
            algorithm_name: Nombre del algoritmo
            
        Returns:
            Modelo cargado
        """
        if algorithm_name not in self.available_algorithms:
            raise ValueError(f"Algoritmo '{algorithm_name}' no disponible")
        
        algorithm_class = self.available_algorithms[algorithm_name]
        model = algorithm_class()
        
        if model.load_model(model_path):
            logger.info(f"Modelo {algorithm_name} cargado desde {model_path}")
            return model
        else:
            raise ValueError(f"No se pudo cargar el modelo desde {model_path}")
    
    def get_training_history(self) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de entrenamientos
        
        Returns:
            Lista con registros de entrenamientos
        """
        return self.training_history.copy()
    
    def save_training_history(self, filepath: str) -> None:
        """
        Guarda el historial de entrenamientos en un archivo JSON
        
        Args:
            filepath: Ruta donde guardar el historial
        """
        try:
            # Convierte datetime a string para serialización JSON
            history_for_json = []
            for record in self.training_history:
                record_copy = record.copy()
                if 'training_start' in record_copy:
                    record_copy['training_start'] = record_copy['training_start'].isoformat()
                if 'training_end' in record_copy:
                    record_copy['training_end'] = record_copy['training_end'].isoformat()
                history_for_json.append(record_copy)
            
            with open(filepath, 'w') as f:
                json.dump(history_for_json, f, indent=2)
            
            logger.info(f"Historial de entrenamientos guardado en {filepath}")
            
        except Exception as e:
            logger.error(f"Error guardando historial: {str(e)}")
    
    def clear_training_history(self) -> None:
        """
        Limpia el historial de entrenamientos
        """
        self.training_history = []
        logger.info("Historial de entrenamientos limpiado")
