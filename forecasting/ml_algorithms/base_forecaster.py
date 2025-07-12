"""
Clase base para algoritmos de pronóstico
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BaseForecaster(ABC):
    """
    Clase base abstracta para todos los algoritmos de pronóstico
    """
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        """
        Inicializa el algoritmo de pronóstico
        
        Args:
            hyperparameters: Diccionario con hiperparámetros específicos del modelo
        """
        self.hyperparameters = hyperparameters or {}
        self.model = None
        self.is_fitted = False
        self.feature_names = []
        self.training_data = None
        self.metrics = {}
        
    @abstractmethod
    def fit(self, data: pd.DataFrame, target_column: str = 'demand') -> 'BaseForecastingAlgorithm':
        """
        Entrena el modelo con los datos proporcionados
        
        Args:
            data: DataFrame con datos históricos
            target_column: Nombre de la columna objetivo
            
        Returns:
            self: Instancia del modelo entrenado
        """
        pass
    
    @abstractmethod
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Genera pronósticos para los períodos especificados
        
        Args:
            periods: Número de períodos a pronosticar
            confidence_interval: Nivel de confianza (ej: 0.95 para 95%)
            
        Returns:
            DataFrame con pronósticos y intervalos de confianza
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Retorna el nombre del modelo
        """
        pass
    
    def validate_data(self, data: pd.DataFrame, target_column: str = 'demand') -> bool:
        """
        Valida que los datos sean apropiados para el entrenamiento
        
        Args:
            data: DataFrame a validar
            target_column: Columna objetivo
            
        Returns:
            True si los datos son válidos
        """
        if data.empty:
            raise ValueError("Los datos no pueden estar vacíos")
            
        if target_column not in data.columns:
            raise ValueError(f"La columna objetivo '{target_column}' no existe en los datos")
            
        if data[target_column].isnull().all():
            raise ValueError(f"La columna objetivo '{target_column}' contiene solo valores nulos")
            
        if len(data) < 10:
            raise ValueError("Se requieren al menos 10 observaciones para entrenar el modelo")
            
        return True
    
    def preprocess_data(self, data: pd.DataFrame, target_column: str = 'demand') -> pd.DataFrame:
        """
        Preprocesa los datos antes del entrenamiento
        
        Args:
            data: DataFrame original
            target_column: Columna objetivo
            
        Returns:
            DataFrame preprocesado
        """
        # Copia los datos para no modificar el original
        processed_data = data.copy()
        
        # Convierte el índice a datetime si no lo es
        if not isinstance(processed_data.index, pd.DatetimeIndex):
            if 'date' in processed_data.columns:
                processed_data['date'] = pd.to_datetime(processed_data['date'])
                processed_data.set_index('date', inplace=True)
            else:
                raise ValueError("Los datos deben tener un índice de fecha o una columna 'date'")
        
        # Ordena por fecha
        processed_data.sort_index(inplace=True)
        
        # Maneja valores faltantes
        processed_data[target_column] = processed_data[target_column].fillna(method='ffill')
        processed_data[target_column] = processed_data[target_column].fillna(0)
        
        # Elimina valores negativos (opcional, dependiendo del caso de uso)
        processed_data[target_column] = processed_data[target_column].clip(lower=0)
        
        return processed_data
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calcula métricas de evaluación del modelo
        
        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            
        Returns:
            Diccionario con métricas
        """
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        metrics = {}
        
        # Error Absoluto Medio (MAE)
        mae = mean_absolute_error(y_true, y_pred)
        metrics['mae'] = mae if not np.isinf(mae) and not np.isnan(mae) else 0.0
        
        # Error Cuadrático Medio (MSE) y Raíz del Error Cuadrático Medio (RMSE)
        mse = mean_squared_error(y_true, y_pred)
        mse = mse if not np.isinf(mse) and not np.isnan(mse) else 0.0
        metrics['mse'] = mse
        metrics['rmse'] = np.sqrt(mse) if mse >= 0 else 0.0
        
        # Error Porcentual Absoluto Medio (MAPE)
        mask = y_true != 0
        if mask.any() and np.sum(y_true[mask]) > 0:
            mape_values = np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])
            # Filtrar valores infinitos y NaN
            mape_values = mape_values[np.isfinite(mape_values)]
            if len(mape_values) > 0:
                mape = np.mean(mape_values) * 100
                # Limitar MAPE a un valor máximo razonable
                metrics['mape'] = min(mape, 1000.0) if not np.isinf(mape) and not np.isnan(mape) else 100.0
            else:
                metrics['mape'] = 100.0  # Default para casos sin datos válidos
        else:
            metrics['mape'] = 100.0  # Default cuando no hay valores históricos válidos
        
        # Coeficiente de Determinación (R²)
        try:
            r2 = r2_score(y_true, y_pred)
            metrics['r2'] = r2 if not np.isinf(r2) and not np.isnan(r2) else 0.0
        except:
            metrics['r2'] = 0.0
        
        # Error Porcentual Medio (MPE) - para detectar sesgo
        if mask.any() and np.sum(y_true[mask]) > 0:
            mpe_values = (y_true[mask] - y_pred[mask]) / y_true[mask]
            mpe_values = mpe_values[np.isfinite(mpe_values)]
            if len(mpe_values) > 0:
                mpe = np.mean(mpe_values) * 100
                metrics['mpe'] = mpe if not np.isinf(mpe) and not np.isnan(mpe) else 0.0
            else:
                metrics['mpe'] = 0.0
        else:
            metrics['mpe'] = 0.0
        
        # Asegurar que todas las métricas sean números finitos
        for key, value in metrics.items():
            if np.isinf(value) or np.isnan(value):
                if key == 'mape':
                    metrics[key] = 100.0  # MAPE por defecto
                else:
                    metrics[key] = 0.0
        
        return metrics
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Retorna la importancia de las características (si aplica)
        
        Returns:
            Diccionario con importancia de características o None
        """
        return None
    
    def save_model(self, filepath: str) -> bool:
        """
        Guarda el modelo entrenado en un archivo
        
        Args:
            filepath: Ruta donde guardar el modelo
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            import joblib
            
            model_data = {
                'model': self.model,
                'hyperparameters': self.hyperparameters,
                'is_fitted': self.is_fitted,
                'feature_names': self.feature_names,
                'metrics': self.metrics,
                'model_name': self.get_model_name()
            }
            
            joblib.dump(model_data, filepath)
            logger.info(f"Modelo guardado exitosamente en {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar el modelo: {str(e)}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """
        Carga un modelo desde un archivo
        
        Args:
            filepath: Ruta del archivo del modelo
            
        Returns:
            True si se cargó exitosamente
        """
        try:
            import joblib
            
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.hyperparameters = model_data['hyperparameters']
            self.is_fitted = model_data['is_fitted']
            self.feature_names = model_data['feature_names']
            self.metrics = model_data['metrics']
            
            logger.info(f"Modelo cargado exitosamente desde {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {str(e)}")
            return False
    
    def get_hyperparameters(self) -> Dict[str, Any]:
        """
        Retorna los hiperparámetros del modelo
        """
        return self.hyperparameters.copy()
    
    def set_hyperparameters(self, hyperparameters: Dict[str, Any]) -> None:
        """
        Actualiza los hiperparámetros del modelo
        """
        self.hyperparameters.update(hyperparameters)
        # Reset the fitted state since hyperparameters changed
        self.is_fitted = False
    
    def get_training_summary(self) -> Dict[str, Any]:
        """
        Retorna un resumen del entrenamiento del modelo
        """
        return {
            'model_name': self.get_model_name(),
            'is_fitted': self.is_fitted,
            'hyperparameters': self.hyperparameters,
            'metrics': self.metrics,
            'feature_names': self.feature_names
        }
