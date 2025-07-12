"""
Implementación del algoritmo Random Forest para pronósticos de demanda
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .base_forecaster import BaseForecaster

logger = logging.getLogger(__name__)


class RandomForestForecaster(BaseForecaster):
    """
    Implementación del algoritmo Random Forest para pronósticos de series temporales
    """
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        """
        Inicializa el forecaster Random Forest
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn no está instalado. Instálalo con: pip install scikit-learn")
            
        # Hiperparámetros por defecto
        default_params = {
            'n_estimators': 50,  # Reducido para ser más eficiente
            'max_depth': 10,  # Limitado para evitar overfitting
            'min_samples_split': 2,  # Mínimo de muestras para dividir
            'min_samples_leaf': 1,  # Mínimo de muestras en hoja
            'max_features': 'sqrt',  # Número de features por árbol
            'bootstrap': True,  # Bootstrap sampling
            'random_state': 42,  # Semilla para reproducibilidad
            'n_jobs': -1,  # Usar todos los cores
            'oob_score': True,  # Calcular out-of-bag score
            
            # Features específicas para series temporales - Más conservadores
            'lag_features': [1, 7],  # Menos lags para conservar datos
            'rolling_features': [7, 14],  # Menos ventanas
            'seasonal_periods': [7],  # Solo período semanal
            'include_time_features': True,  # Features temporales
            'include_cyclical_features': True,  # Features cíclicas
            'normalize_features': False,  # RF no necesita normalización
        }
        
        if hyperparameters:
            default_params.update(hyperparameters)
            
        super().__init__(default_params)
        
        self.feature_names = []
        self.feature_importance_ = None
    
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo"""
        return "Random Forest"
    
    def _create_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Crea features temporales basadas en el índice de fecha
        """
        features = pd.DataFrame(index=data.index)
        
        if self.hyperparameters.get('include_time_features', True):
            # Features básicos de tiempo
            features['day_of_week'] = data.index.dayofweek
            features['day_of_month'] = data.index.day
            features['day_of_year'] = data.index.dayofyear
            features['month'] = data.index.month
            features['quarter'] = data.index.quarter
            features['week_of_year'] = data.index.isocalendar().week
            features['is_weekend'] = (data.index.dayofweek >= 5).astype(int)
            features['is_month_start'] = data.index.is_month_start.astype(int)
            features['is_month_end'] = data.index.is_month_end.astype(int)
            features['is_quarter_start'] = data.index.is_quarter_start.astype(int)
            features['is_quarter_end'] = data.index.is_quarter_end.astype(int)
            
            # Tendencia temporal
            features['trend'] = np.arange(len(data))
        
        if self.hyperparameters.get('include_cyclical_features', True):
            # Features cíclicas
            features['day_sin'] = np.sin(2 * np.pi * features['day_of_week'] / 7)
            features['day_cos'] = np.cos(2 * np.pi * features['day_of_week'] / 7)
            features['month_sin'] = np.sin(2 * np.pi * features['month'] / 12)
            features['month_cos'] = np.cos(2 * np.pi * features['month'] / 12)
            
            # Features estacionales
            for period in self.hyperparameters.get('seasonal_periods', [7, 30]):
                if len(data) >= period:
                    features[f'seasonal_sin_{period}'] = np.sin(2 * np.pi * features['day_of_year'] / period)
                    features[f'seasonal_cos_{period}'] = np.cos(2 * np.pi * features['day_of_year'] / period)
        
        return features
    
    def _create_lag_features(self, data: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """
        Crea features de lag (valores pasados)
        """
        lag_features = pd.DataFrame(index=data.index)
        
        for lag in self.hyperparameters.get('lag_features', [1, 7, 14, 30]):
            if lag < len(data):
                lag_features[f'lag_{lag}'] = data[target_column].shift(lag)
                
                # Diferencias de lag
                if lag > 1:
                    lag_features[f'lag_diff_{lag}'] = data[target_column].diff(lag)
        
        return lag_features
    
    def _create_rolling_features(self, data: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """
        Crea features de estadísticas móviles
        """
        rolling_features = pd.DataFrame(index=data.index)
        
        for window in self.hyperparameters.get('rolling_features', [7, 14, 30]):
            if window < len(data):
                rolling = data[target_column].rolling(window=window)
                
                # Estadísticas básicas
                rolling_features[f'rolling_mean_{window}'] = rolling.mean()
                rolling_features[f'rolling_std_{window}'] = rolling.std()
                rolling_features[f'rolling_min_{window}'] = rolling.min()
                rolling_features[f'rolling_max_{window}'] = rolling.max()
                rolling_features[f'rolling_median_{window}'] = rolling.median()
                
                # Percentiles
                rolling_features[f'rolling_q25_{window}'] = rolling.quantile(0.25)
                rolling_features[f'rolling_q75_{window}'] = rolling.quantile(0.75)
                
                # Features derivadas
                rolling_features[f'rolling_range_{window}'] = (
                    rolling_features[f'rolling_max_{window}'] - rolling_features[f'rolling_min_{window}']
                )
                
                # Comparación con media móvil
                rolling_features[f'above_rolling_mean_{window}'] = (
                    data[target_column] > rolling_features[f'rolling_mean_{window}']
                ).astype(int)
                
                # Tendencia en ventana móvil
                if window >= 3:
                    rolling_features[f'rolling_trend_{window}'] = (
                        rolling_features[f'rolling_mean_{window}'].diff()
                    )
        
        return rolling_features
    
    def _create_advanced_features(self, data: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """
        Crea features avanzadas específicas para Random Forest
        """
        advanced_features = pd.DataFrame(index=data.index)
        
        # Volatilidad (desviación estándar móvil)
        for window in [7, 14, 30]:
            if window < len(data):
                volatility = data[target_column].rolling(window=window).std()
                advanced_features[f'volatility_{window}'] = volatility.fillna(0)
                
                # Ratio de volatilidad con protección contra división por cero
                if window > 7:
                    short_vol = data[target_column].rolling(window=7).std().fillna(0)
                    # Añadir epsilon para evitar división por cero
                    epsilon = 1e-8
                    advanced_features[f'volatility_ratio_{window}_7'] = volatility / (short_vol + epsilon)
        
        # Momentum features con protección contra división por cero
        for period in [3, 7, 14]:
            if period < len(data):
                shifted_values = data[target_column].shift(period)
                # Protección contra división por cero
                epsilon = 1e-8
                momentum = (data[target_column] / (shifted_values + epsilon)) - 1
                advanced_features[f'momentum_{period}'] = momentum.fillna(0)
        
        # Rate of change con manejo seguro
        for period in [1, 7, 14]:
            if period < len(data):
                roc = data[target_column].pct_change(periods=period)
                # Reemplazar infinitos y NaN
                roc = roc.replace([np.inf, -np.inf], 0).fillna(0)
                advanced_features[f'roc_{period}'] = roc
        
        # Autocorrelación local con manejo seguro
        for lag in [1, 7]:
            if lag < len(data) - 14:
                try:
                    rolling_corr = data[target_column].rolling(window=14).corr(
                        data[target_column].shift(lag)
                    )
                    # Manejo de NaN e infinitos
                    rolling_corr = rolling_corr.replace([np.inf, -np.inf], 0).fillna(0)
                    advanced_features[f'autocorr_{lag}'] = rolling_corr
                except Exception:
                    # Fallback si falla el cálculo de correlación
                    advanced_features[f'autocorr_{lag}'] = 0
        
        # Asegurar que todas las features son finitas
        for col in advanced_features.columns:
            advanced_features[col] = advanced_features[col].replace([np.inf, -np.inf], 0).fillna(0)
        
        return advanced_features
    
    def _prepare_features(self, data: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """
        Prepara todas las features para el modelo
        """
        # Todas las categorías de features
        time_features = self._create_time_features(data)
        lag_features = self._create_lag_features(data, target_column)
        rolling_features = self._create_rolling_features(data, target_column)
        advanced_features = self._create_advanced_features(data, target_column)
        
        # Combina todas las features
        all_features = pd.concat([
            time_features, 
            lag_features, 
            rolling_features, 
            advanced_features
        ], axis=1)
        
        # Manejo más inteligente de NaN values
        # Primero reemplaza infinitos
        all_features = all_features.replace([np.inf, -np.inf], np.nan)
        
        # Forward fill para features de lag (usa el último valor conocido)
        lag_cols = [col for col in all_features.columns if 'lag_' in col]
        for col in lag_cols:
            all_features[col] = all_features[col].fillna(method='ffill')
        
        # Para rolling features, usa forward fill también
        rolling_cols = [col for col in all_features.columns if 'rolling_' in col]
        for col in rolling_cols:
            all_features[col] = all_features[col].fillna(method='ffill')
        
        # Para features de tiempo y avanzadas, usa interpolación o valores por defecto
        time_cols = [col for col in all_features.columns if any(x in col for x in ['day_', 'month', 'quarter', 'week_', 'is_', 'trend'])]
        for col in time_cols:
            if all_features[col].isna().any():
                if 'trend' in col:
                    all_features[col] = all_features[col].fillna(method='ffill')
                else:
                    all_features[col] = all_features[col].fillna(0)
        
        # Para features restantes, usa la mediana
        remaining_cols = [col for col in all_features.columns if col not in lag_cols + rolling_cols + time_cols]
        for col in remaining_cols:
            if all_features[col].isna().any():
                median_val = all_features[col].median()
                if pd.isna(median_val):
                    median_val = 0
                all_features[col] = all_features[col].fillna(median_val)
        
        # Solo elimina filas que tengan todos los valores NaN
        all_features = all_features.dropna(how='all')
        
        # Si aún quedan NaN, reemplaza con 0
        all_features = all_features.fillna(0)
        
        return all_features
    
    def fit(self, data: pd.DataFrame, target_column: str = 'quantity') -> 'RandomForestForecaster':
        """
        Entrena el modelo Random Forest
        """
        try:
            # Valida los datos
            self.validate_data(data, target_column)
            
            # Preprocesa los datos
            processed_data = self.preprocess_data(data, target_column)
            self.training_data = processed_data.copy()
            
            logger.info(f"Entrenando modelo Random Forest con {len(processed_data)} observaciones")
            
            # Prepara features
            features = self._prepare_features(processed_data, target_column)
            
            # Alinea target con features
            aligned_target = processed_data[target_column].loc[features.index]
            
            logger.info(f"Features preparadas: {len(features)} filas, {len(features.columns)} columnas")
            
            # Validación más flexible - solo necesitamos al menos 5 observaciones para RF
            if len(features) < 5:
                raise ValueError(f"Insuficientes datos para entrenar Random Forest (mínimo 5 observaciones, disponibles: {len(features)})")
            
            # Guarda nombres de features
            self.feature_names = features.columns.tolist()
            
            # Ajusta hiperparámetros según el tamaño de datos
            n_estimators = min(self.hyperparameters.get('n_estimators', 50), max(10, len(features) // 2))
            max_depth = min(self.hyperparameters.get('max_depth', 10), max(3, len(features) // 5))
            
            # Inicializa el modelo Random Forest
            self.model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=max(2, min(self.hyperparameters.get('min_samples_split', 2), len(features) // 3)),
                min_samples_leaf=max(1, min(self.hyperparameters.get('min_samples_leaf', 1), len(features) // 5)),
                max_features=self.hyperparameters.get('max_features', 'sqrt'),
                bootstrap=self.hyperparameters.get('bootstrap', True),
                random_state=self.hyperparameters.get('random_state', 42),
                n_jobs=self.hyperparameters.get('n_jobs', -1),
                oob_score=self.hyperparameters.get('oob_score', True) and len(features) > 10
            )
            
            # Entrena el modelo
            self.model.fit(features.values, aligned_target.values)
            self.is_fitted = True
            
            # Guarda importancia de features
            self.feature_importance_ = self.model.feature_importances_
            
            # Calcula métricas en el conjunto de entrenamiento
            y_pred = self.model.predict(features.values)
            self.metrics = self.calculate_metrics(aligned_target.values, y_pred)
            
            # Añade métricas específicas de Random Forest
            if hasattr(self.model, 'oob_score_'):
                self.metrics['oob_score'] = self.model.oob_score_
            
            logger.info(f"Modelo Random Forest entrenado exitosamente.")
            logger.info(f"R²: {self.metrics['r2']:.3f}, MAE: {self.metrics['mae']:.2f}, MAPE: {self.metrics['mape']:.2f}%")
            if 'oob_score' in self.metrics:
                logger.info(f"OOB Score: {self.metrics['oob_score']:.3f}")
            
            return self
            
        except Exception as e:
            logger.error(f"Error entrenando modelo Random Forest: {str(e)}")
            raise
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Genera pronósticos usando Random Forest
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de hacer predicciones")
        
        # Verificar que tenemos datos de entrenamiento
        if not hasattr(self, 'training_data') or self.training_data is None or self.training_data.empty:
            raise ValueError("No hay datos de entrenamiento disponibles para hacer predicciones")
        
        try:
            # Extiende los datos para pronósticos futuros
            last_date = self.training_data.index[-1]
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=periods,
                freq='D'
            )
            
            extended_data = self.training_data.copy()
            target_column = extended_data.columns[0]  # Asume que la primera columna es el target
            predictions = []
            prediction_intervals = []
            
            for i, future_date in enumerate(future_dates):
                try:
                    # Crea datos temporales incluyendo predicciones anteriores
                    temp_data = extended_data.copy()
                    
                    # Añade predicciones anteriores como datos históricos
                    if i > 0:
                        for j, pred_date in enumerate(future_dates[:i]):
                            temp_data.loc[pred_date, target_column] = predictions[j]
                    
                    # Extiende datos para incluir la fecha futura
                    temp_index = pd.Index(list(temp_data.index) + [future_date])
                    temp_df = pd.DataFrame(
                        index=temp_index,
                        columns=temp_data.columns
                    )
                    temp_df.loc[temp_data.index] = temp_data.values
                    
                    # Rellena temporalmente el valor futuro con el último valor conocido
                    temp_df.loc[future_date] = temp_data.iloc[-1].values
                    
                    # Prepara features
                    features = self._prepare_features(temp_df, target_column)
                    
                    # Verificar que features no es None y tiene la fecha futura
                    if features is not None and not features.empty and future_date in features.index:
                        future_features = features.loc[[future_date]]
                        
                        # Verificar que las features tienen las columnas correctas
                        if len(future_features.columns) == len(self.feature_names):
                            # Predicción puntual
                            pred = self.model.predict(future_features.values)[0]
                            predictions.append(max(0, pred))
                            
                            # Intervalos de confianza usando quantile regression
                            # Para RF, estimamos intervalos usando la varianza de los árboles
                            try:
                                tree_predictions = np.array([
                                    tree.predict(future_features.values)[0] 
                                    for tree in self.model.estimators_[:min(20, len(self.model.estimators_))]  # Reduce para eficiencia
                                ])
                                
                                pred_std = np.std(tree_predictions)
                                z_score = 1.96 if confidence_interval >= 0.95 else 1.645
                                margin = z_score * pred_std
                                
                                prediction_intervals.append({
                                    'lower': max(0, pred - margin),
                                    'upper': pred + margin
                                })
                            except Exception:
                                # Fallback para intervalos
                                prediction_intervals.append({
                                    'lower': max(0, pred * 0.8),
                                    'upper': pred * 1.2
                                })
                        else:
                            # Fallback si las features no coinciden
                            logger.warning(f"Features no coinciden para fecha {future_date}")
                            avg_pred = np.mean(predictions) if predictions else temp_data[target_column].mean()
                            predictions.append(max(0, avg_pred))
                            prediction_intervals.append({
                                'lower': max(0, avg_pred * 0.8),
                                'upper': avg_pred * 1.2
                            })
                    else:
                        # Fallback si no se pueden crear features válidas
                        logger.warning(f"No se pudieron crear features para fecha {future_date}")
                        last_value = temp_data[target_column].iloc[-1]
                        predictions.append(max(0, last_value))
                        prediction_intervals.append({
                            'lower': max(0, last_value * 0.8),
                            'upper': last_value * 1.2
                        })
                        
                except Exception as e:
                    logger.warning(f"Error procesando fecha {future_date}: {str(e)}")
                    # Fallback a último valor conocido
                    last_value = extended_data[target_column].iloc[-1] if not extended_data.empty else 1.0
                    predictions.append(max(0, last_value))
                    prediction_intervals.append({
                        'lower': max(0, last_value * 0.8),
                        'upper': last_value * 1.2
                    })
            
            # Prepara el resultado
            result = pd.DataFrame({
                'predicted_demand': predictions,
                'lower_bound': [interval['lower'] for interval in prediction_intervals],
                'upper_bound': [interval['upper'] for interval in prediction_intervals],
                'confidence_level': confidence_interval
            }, index=future_dates)
            
            logger.info(f"Generados {periods} pronósticos Random Forest")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando pronósticos Random Forest: {str(e)}")
            raise
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Obtiene la importancia de las features
        """
        if not self.is_fitted or self.feature_importance_ is None:
            return pd.DataFrame()
        
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.feature_importance_
        }).sort_values('importance', ascending=False)
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del modelo
        """
        if not self.is_fitted:
            return {}
        
        summary = {
            'n_estimators': self.model.n_estimators,
            'max_depth': self.model.max_depth,
            'n_features': len(self.feature_names),
            'oob_score': getattr(self.model, 'oob_score_', None),
            'r2_score': self.metrics.get('r2', 0),
            'mae': self.metrics.get('mae', 0),
            'mape': self.metrics.get('mape', 0)
        }
        
        # Top 10 features más importantes
        if self.feature_importance_ is not None:
            importance_df = self.get_feature_importance()
            summary['top_features'] = importance_df.head(10)['feature'].tolist()
        
        return summary