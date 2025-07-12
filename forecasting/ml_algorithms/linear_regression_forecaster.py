"""
Implementación del algoritmo Linear Regression para pronósticos de demanda
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta

try:
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.preprocessing import StandardScaler, PolynomialFeatures
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .base_forecaster import BaseForecaster

logger = logging.getLogger(__name__)


class LinearRegressionForecaster(BaseForecaster):
    """
    Implementación del algoritmo Linear Regression para pronósticos de series temporales
    """
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        """
        Inicializa el forecaster Linear Regression
        
        Args:
            hyperparameters: Parámetros específicos del modelo
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn no está instalado. Instálalo con: pip install scikit-learn")
            
        # Hiperparámetros por defecto
        default_params = {
            'model_type': 'linear',  # 'linear', 'ridge', 'lasso'
            'alpha': 1.0,  # Regularización para Ridge/Lasso
            'polynomial_degree': 1,  # Grado del polinomio para features
            'include_seasonality': True,  # Incluir componentes estacionales
            'seasonal_periods': [7, 30, 365],  # Períodos estacionales a considerar
            'lag_features': [1, 7, 30],  # Lags a incluir como features
            'rolling_features': [7, 14, 30],  # Ventanas para medias móviles
            'trend_features': True,  # Incluir tendencia temporal
            'normalize_features': True,  # Normalizar features
            'fit_intercept': True
        }
        
        if hyperparameters:
            default_params.update(hyperparameters)
            
        super().__init__(default_params)
        
        self.scaler = StandardScaler() if default_params['normalize_features'] else None
        self.poly_features = None
        self.feature_names = []
    
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo"""
        model_type = self.hyperparameters.get('model_type', 'linear')
        return f"Linear Regression ({model_type.title()})"
    
    def _create_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Crea features temporales basadas en el índice de fecha
        
        Args:
            data: DataFrame con índice de fecha
            
        Returns:
            DataFrame con features temporales
        """
        features = pd.DataFrame(index=data.index)
        
        # Features básicos de tiempo
        features['day_of_week'] = data.index.dayofweek
        features['day_of_month'] = data.index.day
        features['day_of_year'] = data.index.dayofyear
        features['month'] = data.index.month
        features['quarter'] = data.index.quarter
        features['week_of_year'] = data.index.isocalendar().week
        
        # Tendencia temporal
        if self.hyperparameters.get('trend_features', True):
            features['trend'] = np.arange(len(data))
            features['trend_squared'] = features['trend'] ** 2
        
        # Features estacionales
        if self.hyperparameters.get('include_seasonality', True):
            for period in self.hyperparameters.get('seasonal_periods', [7, 30, 365]):
                if len(data) >= period:
                    features[f'sin_{period}'] = np.sin(2 * np.pi * features['day_of_year'] / period)
                    features[f'cos_{period}'] = np.cos(2 * np.pi * features['day_of_year'] / period)
        
        return features
    
    def _create_lag_features(self, data: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """
        Crea features de lag (valores pasados) de la serie objetivo
        
        Args:
            data: DataFrame con los datos
            target_column: Columna objetivo
            
        Returns:
            DataFrame con features de lag
        """
        lag_features = pd.DataFrame(index=data.index)
        
        for lag in self.hyperparameters.get('lag_features', [1, 7, 30]):
            if lag < len(data):
                lag_features[f'lag_{lag}'] = data[target_column].shift(lag)
        
        return lag_features
    
    def _create_rolling_features(self, data: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """
        Crea features de medias móviles
        
        Args:
            data: DataFrame con los datos
            target_column: Columna objetivo
            
        Returns:
            DataFrame con features de rolling
        """
        rolling_features = pd.DataFrame(index=data.index)
        
        for window in self.hyperparameters.get('rolling_features', [7, 14, 30]):
            if window < len(data):
                rolling_features[f'rolling_mean_{window}'] = data[target_column].rolling(window=window).mean()
                rolling_features[f'rolling_std_{window}'] = data[target_column].rolling(window=window).std()
                rolling_features[f'rolling_min_{window}'] = data[target_column].rolling(window=window).min()
                rolling_features[f'rolling_max_{window}'] = data[target_column].rolling(window=window).max()
        
        return rolling_features
    
    def _prepare_features(self, data: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """
        Prepara todas las features para el modelo
        
        Args:
            data: DataFrame con los datos
            target_column: Columna objetivo
            
        Returns:
            DataFrame con todas las features
        """
        # Features temporales
        time_features = self._create_time_features(data)
        
        # Features de lag
        lag_features = self._create_lag_features(data, target_column)
        
        # Features de rolling
        rolling_features = self._create_rolling_features(data, target_column)
        
        # Combina todas las features
        all_features = pd.concat([time_features, lag_features, rolling_features], axis=1)
        
        # Elimina filas con NaN (causados por lag y rolling)
        all_features = all_features.dropna()
        
        # Features polinomiales si se especifica
        if self.hyperparameters.get('polynomial_degree', 1) > 1:
            if self.poly_features is None:
                self.poly_features = PolynomialFeatures(
                    degree=self.hyperparameters['polynomial_degree'],
                    include_bias=False
                )
                # Fit solo con una muestra para evitar problemas de memoria
                sample_size = min(1000, len(all_features))
                self.poly_features.fit(all_features.iloc[:sample_size])
            
            # Aplica transformación polinomial
            poly_array = self.poly_features.transform(all_features)
            poly_df = pd.DataFrame(
                poly_array,
                index=all_features.index,
                columns=[f'poly_{i}' for i in range(poly_array.shape[1])]
            )
            all_features = poly_df
        
        return all_features
    
    def fit(self, data: pd.DataFrame, target_column: str = 'demand') -> 'LinearRegressionForecaster':
        """
        Entrena el modelo Linear Regression
        
        Args:
            data: DataFrame con datos históricos
            target_column: Nombre de la columna objetivo
            
        Returns:
            self: Instancia del modelo entrenado
        """
        try:
            # Valida los datos
            self.validate_data(data, target_column)
            
            # Preprocesa los datos
            processed_data = self.preprocess_data(data, target_column)
            self.training_data = processed_data.copy()
            
            logger.info(f"Entrenando modelo Linear Regression con {len(processed_data)} observaciones")
            
            # Prepara features
            features = self._prepare_features(processed_data, target_column)
            
            # Alinea target con features (elimina filas donde no hay features)
            aligned_target = processed_data[target_column].loc[features.index]
            
            if len(features) < 10:
                raise ValueError("Insuficientes datos para entrenar el modelo (mínimo 10 observaciones)")
            
            # Guarda nombres de features
            self.feature_names = features.columns.tolist()
            
            # Normaliza features si se especifica
            if self.scaler is not None:
                features_array = self.scaler.fit_transform(features)
            else:
                features_array = features.values
            
            # Inicializa el modelo según el tipo
            model_type = self.hyperparameters.get('model_type', 'linear')
            if model_type == 'ridge':
                self.model = Ridge(
                    alpha=self.hyperparameters.get('alpha', 1.0),
                    fit_intercept=self.hyperparameters.get('fit_intercept', True)
                )
            elif model_type == 'lasso':
                self.model = Lasso(
                    alpha=self.hyperparameters.get('alpha', 1.0),
                    fit_intercept=self.hyperparameters.get('fit_intercept', True),
                    max_iter=2000
                )
            else:  # linear
                self.model = LinearRegression(
                    fit_intercept=self.hyperparameters.get('fit_intercept', True)
                )
            
            # Entrena el modelo
            self.model.fit(features_array, aligned_target.values)
            self.is_fitted = True
            
            # Calcula métricas en el conjunto de entrenamiento
            y_pred = self.model.predict(features_array)
            self.metrics = self.calculate_metrics(aligned_target.values, y_pred)
            
            logger.info(f"Modelo Linear Regression entrenado exitosamente.")
            logger.info(f"R²: {self.metrics['r2']:.3f}, MAE: {self.metrics['mae']:.2f}, MAPE: {self.metrics['mape']:.2f}%")
            
            return self
            
        except Exception as e:
            logger.error(f"Error entrenando modelo Linear Regression: {str(e)}")
            raise
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Genera pronósticos usando Linear Regression
        
        Args:
            periods: Número de períodos a pronosticar
            confidence_interval: Nivel de confianza
            
        Returns:
            DataFrame con pronósticos y intervalos de confianza
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de hacer predicciones")
        
        try:
            # Extiende los datos para incluir períodos futuros
            last_date = self.training_data.index[-1]
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=periods,
                freq='D'
            )
            
            # Para pronósticos iterativos, necesitamos extender los datos
            extended_data = self.training_data.copy()
            
            predictions = []
            
            for i, future_date in enumerate(future_dates):
                # Crea datos extendidos hasta la fecha actual
                temp_data = extended_data.copy()
                
                # Para la primera predicción, usa los datos originales
                # Para predicciones posteriores, incluye predicciones anteriores
                if i > 0:
                    # Añade predicciones anteriores como datos "históricos"
                    for j, pred_date in enumerate(future_dates[:i]):
                        temp_data.loc[pred_date, temp_data.columns[0]] = predictions[j]
                
                # Prepara features para esta fecha específica
                # Crea un DataFrame temporal que incluya la fecha futura
                temp_index = pd.Index(list(temp_data.index) + [future_date])
                temp_df = pd.DataFrame(
                    index=temp_index,
                    columns=temp_data.columns
                )
                temp_df.loc[temp_data.index] = temp_data.values
                
                # Rellena el valor futuro temporalmente con la media (será reemplazado)
                temp_df.loc[future_date] = temp_data.iloc[-1].values
                
                # Prepara features
                features = self._prepare_features(temp_df, temp_df.columns[0])
                
                # Obtiene features solo para la fecha futura
                if future_date in features.index:
                    future_features = features.loc[[future_date]]
                    
                    # Normaliza si es necesario
                    if self.scaler is not None:
                        future_features_array = self.scaler.transform(future_features)
                    else:
                        future_features_array = future_features.values
                    
                    # Hace predicción
                    pred = self.model.predict(future_features_array)[0]
                    predictions.append(max(0, pred))  # No permite valores negativos
                else:
                    # Si no se pueden crear features, usa el último valor
                    predictions.append(extended_data.iloc[-1, 0])
            
            # Estima intervalos de confianza usando residuales del entrenamiento
            residuals_std = np.std(self.training_data.iloc[:, 0] - 
                                  self.model.predict(self.scaler.transform(
                                      self._prepare_features(self.training_data, self.training_data.columns[0])
                                  ) if self.scaler else 
                                  self._prepare_features(self.training_data, self.training_data.columns[0])))
            
            # Factor para el intervalo de confianza
            z_score = 1.96 if confidence_interval >= 0.95 else 1.645  # Aproximación
            margin = z_score * residuals_std
            
            # Prepara el resultado
            result = pd.DataFrame({
                'date': future_dates,
                'predicted_demand': predictions,
                'lower_bound': [max(0, p - margin) for p in predictions],
                'upper_bound': [p + margin for p in predictions],
                'confidence_level': confidence_interval
            })
            
            result.set_index('date', inplace=True)
            
            logger.info(f"Generados {periods} pronósticos Linear Regression")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando pronósticos Linear Regression: {str(e)}")
            raise
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Obtiene la importancia de las features
        
        Returns:
            DataFrame con importancia de features
        """
        if not self.is_fitted:
            return pd.DataFrame()
        
        # Para modelos lineales, usa los coeficientes como importancia
        if hasattr(self.model, 'coef_'):
            importance = np.abs(self.model.coef_)
            
            return pd.DataFrame({
                'feature': self.feature_names,
                'importance': importance
            }).sort_values('importance', ascending=False)
        
        return pd.DataFrame()
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del modelo
        
        Returns:
            Diccionario con información del modelo
        """
        if not self.is_fitted:
            return {}
        
        summary = {
            'model_type': self.hyperparameters.get('model_type', 'linear'),
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names[:10],  # Primeras 10 features
            'r2_score': self.metrics.get('r2', 0),
            'mae': self.metrics.get('mae', 0),
            'mape': self.metrics.get('mape', 0)
        }
        
        if hasattr(self.model, 'coef_'):
            summary['n_coefficients'] = len(self.model.coef_)
            summary['intercept'] = float(self.model.intercept_) if hasattr(self.model, 'intercept_') else 0
        
        return summary