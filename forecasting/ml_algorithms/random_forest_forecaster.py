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
            
        # Hiperparámetros optimizados para ML Services Core
        default_params = {
            # Parámetros del modelo optimizados
            'n_estimators': 100,  # Aumentado para mejor accuracy
            'max_depth': 15,  # Balanceado para evitar overfitting
            'min_samples_split': 5,  # Más conservador
            'min_samples_leaf': 2,  # Reduce overfitting
            'max_features': 'sqrt',  # Óptimo para features
            'bootstrap': True,
            'random_state': 42,
            'n_jobs': -1,
            'oob_score': True,
            'max_samples': 0.8,  # Bootstrap sampling ratio
            
            # Features específicas para series temporales optimizadas
            'lag_features': [1, 2, 3, 7, 14],  # Lags más relevantes
            'rolling_features': [3, 7, 14, 30],  # Ventanas móviles estratégicas
            'seasonal_periods': [7, 30],  # Semanal y mensual
            'include_time_features': True,
            'include_cyclical_features': True,
            'include_statistical_features': True,  # Nueva feature
            'normalize_features': False,
            
            # Performance monitoring
            'track_feature_importance': True,
            'calculate_oob_predictions': True,
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
    
    def _validate_and_clean_data(self, X_features: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Valida y limpia los datos de entrada de forma robusta
        """
        # Crear copias para evitar modificar originales
        X_clean = X_features.copy()
        y_clean = y.copy()
        
        # Verificar si hay columnas completamente vacías
        empty_cols = X_clean.columns[X_clean.isnull().all()].tolist()
        if empty_cols:
            logger.warning(f"Eliminando columnas completamente vacías: {empty_cols}")
            X_clean = X_clean.drop(columns=empty_cols)
        
        # Reemplazar valores infinitos con NaN primero
        X_clean = X_clean.replace([np.inf, -np.inf], np.nan)
        
        # Identificar tipos de features para tratamiento diferenciado
        lag_cols = [col for col in X_clean.columns if 'lag_' in col]
        rolling_cols = [col for col in X_clean.columns if 'rolling_' in col]
        time_cols = [col for col in X_clean.columns if any(x in col for x in ['day_', 'month', 'quarter', 'week_', 'is_', 'trend'])]
        
        # Para lag features, usa forward fill con límite
        for col in lag_cols:
            if X_clean[col].isna().any():
                # Usar forward fill con límite de 3 períodos
                X_clean[col] = X_clean[col].fillna(method='ffill', limit=3)
                # Si aún hay NaN, usar la mediana
                if X_clean[col].isna().any():
                    median_val = X_clean[col].median()
                    X_clean[col] = X_clean[col].fillna(median_val if not pd.isna(median_val) else 0)
        
        # Para rolling features, usa forward fill también
        for col in rolling_cols:
            if X_clean[col].isna().any():
                X_clean[col] = X_clean[col].fillna(method='ffill', limit=5)
                # Si aún hay NaN, usar la mediana
                if X_clean[col].isna().any():
                    median_val = X_clean[col].median()
                    X_clean[col] = X_clean[col].fillna(median_val if not pd.isna(median_val) else 0)
        
        # Para features de tiempo, usar valores por defecto
        for col in time_cols:
            if X_clean[col].isna().any():
                if 'trend' in col:
                    X_clean[col] = X_clean[col].fillna(method='ffill')
                    # Si aún hay NaN, usar interpolación lineal
                    if X_clean[col].isna().any():
                        X_clean[col] = X_clean[col].interpolate(method='linear')
                else:
                    X_clean[col] = X_clean[col].fillna(0)
        
        # Para features restantes, usa la mediana
        remaining_cols = [col for col in X_clean.columns if col not in lag_cols + rolling_cols + time_cols]
        for col in remaining_cols:
            if X_clean[col].isna().any():
                # Usar mediana para mayor robustez ante outliers
                median_val = X_clean[col].median()
                if pd.isna(median_val):
                    # Si la mediana es NaN, usar media
                    mean_val = X_clean[col].mean()
                    fill_val = mean_val if not pd.isna(mean_val) else 0
                else:
                    fill_val = median_val
                X_clean[col] = X_clean[col].fillna(fill_val)
        
        # Limpieza final
        X_clean = X_clean.fillna(0)
        y_clean = y_clean.fillna(y_clean.median() if not pd.isna(y_clean.median()) else 0)
        
        # Verificar que no hay valores infinitos
        if np.isinf(X_clean.values).any():
            logger.warning("Detectados valores infinitos en X, reemplazando con 0")
            X_clean = X_clean.replace([np.inf, -np.inf], 0)
        
        if np.isinf(y_clean.values).any():
            logger.warning("Detectados valores infinitos en y, reemplazando con mediana")
            y_median = y_clean.median()
            y_clean = y_clean.replace([np.inf, -np.inf], y_median if not pd.isna(y_median) else 0)
        
        # Verificar que todas las features son numéricas
        for col in X_clean.columns:
            if not pd.api.types.is_numeric_dtype(X_clean[col]):
                logger.warning(f"Columna {col} no es numérica, convirtiendo")
                X_clean[col] = pd.to_numeric(X_clean[col], errors='coerce').fillna(0)
        
        return X_clean, y_clean
    
    def _get_model_params(self) -> Dict[str, Any]:
        """
        Obtiene los parámetros del modelo Random Forest
        """
        return {
            'n_estimators': self.hyperparameters.get('n_estimators', 100),
            'max_depth': self.hyperparameters.get('max_depth', 15),
            'min_samples_split': self.hyperparameters.get('min_samples_split', 5),
            'min_samples_leaf': self.hyperparameters.get('min_samples_leaf', 2),
            'max_features': self.hyperparameters.get('max_features', 'sqrt'),
            'bootstrap': self.hyperparameters.get('bootstrap', True),
            'random_state': self.hyperparameters.get('random_state', 42),
            'n_jobs': self.hyperparameters.get('n_jobs', -1),
            'oob_score': self.hyperparameters.get('oob_score', True),
            'max_samples': self.hyperparameters.get('max_samples', 0.8)
        }
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calcula métricas de evaluación
        """
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        # Asegurar que ambos son arrays numpy
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        
        # Calcular métricas básicas
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        
        # MAPE con manejo de ceros
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-8))) * 100
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'r2': r2,
            'mape': mape
        }
    
    def fit(self, X, y=None, target_column: str = 'quantity') -> 'RandomForestForecaster':
        """
        Entrena el modelo Random Forest con validación robusta de datos
        
        Args:
            X: DataFrame con features o datos completos
            y: Serie objetivo (opcional si está en X), o nombre de columna si es string
            target_column: Nombre de la columna objetivo si y=None
            
        Returns:
            self: Instancia del modelo entrenado
        """
        try:
            # CASO ESPECIAL: Si y es string, lo tratamos como nombre de columna
            if isinstance(y, str):
                logger.info(f"Tratando y='{y}' como nombre de columna objetivo")
                if isinstance(X, pd.DataFrame) and y in X.columns:
                    # y es el nombre de la columna
                    target_column = y
                    y_series = X[target_column].copy()
                    X_features = X.drop(columns=[target_column])
                    
                    # Si no hay features, crear básicas
                    if X_features.empty:
                        logger.warning("No hay features, creando features básicas")
                        X_features = pd.DataFrame({
                            'trend': range(len(y_series)),
                            'lag_1': y_series.shift(1).fillna(y_series.mean()),
                            'rolling_mean_3': y_series.rolling(3).mean().fillna(y_series.mean())
                        }, index=y_series.index)
                    
                    # Actualizar variables para el procesamiento posterior
                    X = X_features
                    y = y_series
                    
                else:
                    logger.error(f"String '{y}' no es una columna válida en X: {list(X.columns)}")
                    raise ValueError(f"Columna '{y}' no encontrada en X")
            
            # VALIDACIÓN ROBUSTA DE DATOS
            if isinstance(X, pd.DataFrame) and y is None:
                # Si X es DataFrame y no hay y, buscar la columna objetivo
                if target_column not in X.columns:
                    # Buscar alternativas comunes
                    alternative_columns = ['quantity', 'demand', 'value', 'y', 'target']
                    found_column = None
                    
                    for col in alternative_columns:
                        if col in X.columns:
                            found_column = col
                            break
                    
                    if found_column:
                        target_column = found_column
                        logger.info(f"Usando columna '{target_column}' como objetivo")
                    elif len(X.columns) == 1:
                        target_column = X.columns[0]
                        logger.info(f"Usando única columna '{target_column}' como objetivo")
                    else:
                        logger.error(f"Columnas disponibles: {list(X.columns)}")
                        raise ValueError(f"Columna objetivo '{target_column}' no encontrada en {list(X.columns)}")
                
                # Separar features y target
                y = X[target_column].copy()
                X_features = X.drop(columns=[target_column])
                
                # Si no hay features (solo target), crear features básicas
                if X_features.empty:
                    logger.warning("No hay features disponibles, creando features básicas")
                    X_features = pd.DataFrame({
                        'trend': range(len(y)),
                        'lag_1': y.shift(1).fillna(y.mean()),
                        'rolling_mean_3': y.rolling(3).mean().fillna(y.mean())
                    }, index=y.index)
                
            elif isinstance(X, pd.DataFrame) and isinstance(y, pd.Series):
                # Si tenemos X (features) y y (target) separados
                X_features = X.copy()
                y = y.copy()
                
            elif isinstance(X, pd.Series):
                # Si X es una Serie, tratarla como target
                y = X.copy()
                logger.warning("Recibido Series, creando features básicas")
                X_features = pd.DataFrame({
                    'trend': range(len(y)),
                    'lag_1': y.shift(1).fillna(y.mean()),
                    'rolling_mean_3': y.rolling(3).mean().fillna(y.mean())
                }, index=y.index)
                
            else:
                logger.error(f"Tipo de X: {type(X)}, Tipo de y: {type(y)}")
                logger.error(f"Valor de y: {y}")
                raise ValueError(f"Tipos de datos no soportados: X={type(X)}, y={type(y)}")
            
            # Validar longitud mínima
            if len(X_features) < 5:
                raise ValueError("Se necesitan al menos 5 observaciones para entrenar Random Forest")
            
            # Alinear índices
            common_index = X_features.index.intersection(y.index)
            if len(common_index) == 0:
                # Si no hay índices comunes, resetear ambos
                X_features = X_features.reset_index(drop=True)
                y = y.reset_index(drop=True)
                common_index = X_features.index
            
            X_features = X_features.loc[common_index]
            y = y.loc[common_index]
            
            # Limpiar y validar datos MEJORADO
            X_features, y = self._validate_and_clean_data(X_features, y)
            
            # Verificar que tenemos datos suficientes después de la limpieza
            if len(X_features) < 3:
                raise ValueError("Datos insuficientes después de la limpieza")
            
            logger.info(f"Entrenando Random Forest con {len(X_features)} observaciones y {len(X_features.columns)} features")
            
            # Validar que no hay problemas en los datos
            if X_features.isnull().any().any():
                raise ValueError("Aún hay valores NaN en los datos después de la limpieza")
            
            if np.isinf(X_features.values).any():
                raise ValueError("Hay valores infinitos en los datos después de la limpieza")
            
            # Entrenar modelo
            self.model = RandomForestRegressor(**self._get_model_params())
            self.model.fit(X_features, y)
            
            # Calcular métricas
            y_pred = self.model.predict(X_features)
            self.metrics = self._calculate_metrics(y, y_pred)
            
            # Guardar información del entrenamiento
            self.feature_names = list(X_features.columns)
            self.is_fitted = True
            
            # Guardar datos de entrenamiento para predicciones futuras
            self.training_data = pd.concat([X_features, y], axis=1)
            self.training_data.columns = list(X_features.columns) + ['target']
            
            if self.hyperparameters.get('track_feature_importance', True):
                self.feature_importance_ = dict(zip(
                    self.feature_names, 
                    self.model.feature_importances_
                ))
            
            logger.info(f"Random Forest entrenado exitosamente. MAE: {self.metrics['mae']:.2f}, R²: {self.metrics['r2']:.3f}")
            
            return self
            
        except Exception as e:
            logger.error(f"Error entrenando Random Forest: {str(e)}")
            raise
    
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> Dict[str, Any]:
        """
        Genera pronósticos usando Random Forest - FORMATO CORREGIDO
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de hacer predicciones")
        
        # Verificar que tenemos datos de entrenamiento
        if not hasattr(self, 'training_data') or self.training_data is None:
            raise ValueError("No hay datos de entrenamiento disponibles para hacer predicciones")
        
        try:
            # Preparar datos para predicción
            predictions = []
            
            # Obtener los últimos valores para generar predicciones
            if hasattr(self, 'feature_names') and self.feature_names:
                # Crear características básicas para cada período futuro
                for i in range(periods):
                    # Crear características simples
                    features = pd.DataFrame({
                        'trend': [i],
                        'lag_1': [predictions[-1] if predictions else self.training_data.iloc[-1, 0]],
                        'rolling_mean_3': [np.mean(predictions[-3:]) if len(predictions) >= 3 else self.training_data.iloc[-1, 0]]
                    })
                    
                    # Hacer predicción
                    pred = self.model.predict(features)[0]
                    predictions.append(max(0, pred))  # Asegurar valores no negativos
            else:
                # Fallback: usar media móvil simple
                base_value = self.training_data.iloc[-1, 0]
                for i in range(periods):
                    predictions.append(base_value)
            
            # Generar fechas futuras
            last_date = self.training_data.index[-1]
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=periods,
                freq='D'
            )
            
            # Estimar intervalos de confianza
            std_dev = np.std(predictions) if len(predictions) > 1 else predictions[0] * 0.1
            confidence_multiplier = 1.96  # Para 95% de confianza
            
            # FORMATO CORREGIDO - Devolver diccionario compatible con el endpoint
            forecast_data = []
            for i, (date, pred) in enumerate(zip(future_dates, predictions)):
                forecast_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'predicted_demand': float(pred),
                    'lower_bound': float(max(0, pred - confidence_multiplier * std_dev)),
                    'upper_bound': float(pred + confidence_multiplier * std_dev),
                    'model_type': 'random_forest',
                    'period': i + 1
                })
            
            logger.info(f"Generados {periods} pronósticos Random Forest")
            
            # DEVOLVER EN FORMATO ESPERADO POR EL ENDPOINT
            return {
                'success': True,
                'forecast': forecast_data,
                'model_type': 'random_forest',
                'periods': periods,
                'confidence_interval': confidence_interval,
                'metrics': getattr(self, 'metrics', {}),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando pronósticos Random Forest: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'forecast': [],
                'model_type': 'random_forest'
            }

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Obtiene la importancia de las features
        """
        if not self.is_fitted or not hasattr(self, 'feature_importance_'):
            return pd.DataFrame()
        
        if hasattr(self, 'feature_names') and self.feature_names:
            return pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.feature_importance_
            }).sort_values('importance', ascending=False)
        else:
            return pd.DataFrame()
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del modelo
        """
        if not self.is_fitted:
            return {}
        
        summary = {
            'n_estimators': getattr(self.model, 'n_estimators', 0),
            'max_depth': getattr(self.model, 'max_depth', 0),
            'n_features': len(self.feature_names) if hasattr(self, 'feature_names') else 0,
            'oob_score': getattr(self.model, 'oob_score_', None),
            'r2_score': self.metrics.get('r2', 0),
            'mae': self.metrics.get('mae', 0),
            'mape': self.metrics.get('mape', 0)
        }
        
        return summary
        
        mase = mean_absolute_scaled_error(actual, predictions)
        
        # Accuracy score (100 - MAPE)
        accuracy_score = max(0, 100 - mape)
        
        # Directional accuracy
        if len(actual) > 1:
            actual_direction = np.diff(actual) > 0
            predicted_direction = np.diff(predictions) > 0
            directional_accuracy = np.mean(actual_direction == predicted_direction) * 100
        else:
            directional_accuracy = 0
        
        # Feature-specific metrics
        feature_stability = self._calculate_feature_stability()
        prediction_variance = np.var(predictions)
        
        return {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'mape': float(mape),
            'mase': float(mase),
            'r2_score': float(r2),
            'accuracy_score': float(accuracy_score),
            'directional_accuracy': float(directional_accuracy),
            'forecast_bias': float(np.mean(predictions - actual)),
            'prediction_variance': float(prediction_variance),
            'feature_stability': feature_stability,
            'oob_score': float(getattr(self.model, 'oob_score_', 0))
        }
    
    def _calculate_feature_stability(self) -> float:
        """
        Calcula la estabilidad de las features basada en su importancia
        """
        if self.feature_importance_ is None:
            return 0.0
        
        # Coeficiente de variación de las importancias
        cv = np.std(self.feature_importance_) / np.mean(self.feature_importance_)
        stability = 1 / (1 + cv)  # Mayor estabilidad = menor variación
        
        return float(stability)
    
    def get_performance_summary(self, X_test: pd.DataFrame, 
                              y_test: pd.Series) -> Dict[str, Any]:
        """
        Resumen completo de performance para ML Services Core
        """
        baseline_metrics = self.get_baseline_accuracy_metrics(X_test, y_test)
        
        # Información del modelo
        model_info = {
            'model_name': self.get_model_name(),
            'hyperparameters': self.hyperparameters,
            'is_fitted': self.is_fitted,
            'n_features': len(self.feature_names),
            'training_samples': getattr(self, 'training_samples_', 0),
            'feature_types': self._categorize_features()
        }
        
        # Feature importance top 10
        top_features = {}
        if self.feature_importance_ is not None:
            importance_df = self.get_feature_importance()
            top_features = dict(importance_df.head(10).values)
        
        return {
            'model_info': model_info,
            'baseline_metrics': baseline_metrics,
            'top_features': top_features,
            'model_components': {
                'n_estimators': self.hyperparameters.get('n_estimators', 0),
                'max_depth': self.hyperparameters.get('max_depth', 0),
                'oob_enabled': self.hyperparameters.get('oob_score', False)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _categorize_features(self) -> Dict[str, int]:
        """
        Categoriza las features por tipo
        """
        categories = {
            'lag_features': 0,
            'rolling_features': 0,
            'time_features': 0,
            'cyclical_features': 0,
            'other_features': 0
        }
        
        for feature in self.feature_names:
            if 'lag_' in feature:
                categories['lag_features'] += 1
            elif 'rolling_' in feature or 'mean_' in feature or 'std_' in feature:
                categories['rolling_features'] += 1
            elif any(time_feat in feature for time_feat in ['day_', 'month_', 'quarter_', 'week_']):
                categories['time_features'] += 1
            elif '_sin' in feature or '_cos' in feature:
                categories['cyclical_features'] += 1
            else:
                categories['other_features'] += 1
        
        return categories
    
    def optimize_hyperparameters(self, X_train: pd.DataFrame, y_train: pd.Series,
                                X_val: pd.DataFrame, y_val: pd.Series) -> Dict[str, Any]:
        """
        Optimización automática de hiperparámetros para ML Services Core
        """
        from sklearn.model_selection import RandomizedSearchCV
        from scipy.stats import randint, uniform
        
        # Definir distribuciones para búsqueda aleatoria
        param_distributions = {
            'n_estimators': randint(50, 200),
            'max_depth': randint(5, 20),
            'min_samples_split': randint(2, 20),
            'min_samples_leaf': randint(1, 10),
            'max_features': ['sqrt', 'log2', 0.5, 0.7, 0.9],
            'max_samples': uniform(0.7, 0.3)  # 0.7 a 1.0
        }
        
        # Crear modelo base
        base_model = RandomForestRegressor(
            random_state=42,
            n_jobs=-1,
            oob_score=True
        )
        
        # Búsqueda aleatoria
        random_search = RandomizedSearchCV(
            base_model,
            param_distributions,
            n_iter=50,  # Número de iteraciones
            cv=3,  # 3-fold cross validation
            scoring='neg_mean_absolute_error',
            random_state=42,
            n_jobs=-1
        )
        
        logger.info("Iniciando optimización de hiperparámetros Random Forest...")
        
        try:
            # Realizar búsqueda
            random_search.fit(X_train, y_train)
            
            # Obtener mejores parámetros
            best_params = random_search.best_params_
            best_score = -random_search.best_score_  # Convertir a MAE positivo
            
            # Actualizar hiperparámetros del modelo
            self.hyperparameters.update(best_params)
            
            # Evaluar en conjunto de validación
            best_model = random_search.best_estimator_
            val_predictions = best_model.predict(X_val)
            val_mae = mean_absolute_error(y_val, val_predictions)
            
            logger.info(f"Mejores parámetros encontrados con MAE: {best_score:.4f}")
            
            return {
                'best_params': best_params,
                'best_cv_score': best_score,
                'validation_mae': val_mae,
                'cv_results': random_search.cv_results_
            }
            
        except Exception as e:
            logger.error(f"Error en optimización de hiperparámetros: {e}")
            return {
                'best_params': None,
                'best_cv_score': None,
                'validation_mae': None,
                'error': str(e)
            }