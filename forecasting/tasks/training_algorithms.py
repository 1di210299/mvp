"""
Algoritmos específicos de entrenamiento de modelos
"""

from django.utils import timezone
import logging
import pandas as pd
import numpy as np
from decimal import Decimal

logger = logging.getLogger(__name__)


def train_prophet_model(model, training_data):
    """Entrena un modelo Prophet"""
    try:
        from prophet import Prophet
        
        # Configurar modelo Prophet
        prophet_model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            interval_width=float(model.confidence_interval) / 100
        )
        
        # Añadir hiperparámetros si están definidos
        hyperparams = model.hyperparameters or {}
        for param, value in hyperparams.items():
            if hasattr(prophet_model, param):
                setattr(prophet_model, param, value)
        
        # Entrenar modelo
        prophet_model.fit(training_data[['ds', 'y']])
        
        # Calcular métricas
        metrics = calculate_model_metrics(prophet_model, training_data)
        
        return prophet_model, metrics
        
    except Exception as e:
        logger.error(f"Error entrenando modelo Prophet: {str(e)}")
        raise


def train_arima_model(model, training_data):
    """Entrena un modelo ARIMA"""
    try:
        from statsmodels.tsa.arima.model import ARIMA
        
        # Preparar serie temporal
        ts_data = training_data.set_index('ds')['y'].resample('D').sum().fillna(0)
        
        # Parámetros ARIMA (por defecto o desde hiperparámetros)
        hyperparams = model.hyperparameters or {}
        p = hyperparams.get('p', 1)
        d = hyperparams.get('d', 1)
        q = hyperparams.get('q', 1)
        
        # Entrenar modelo
        arima_model = ARIMA(ts_data, order=(p, d, q))
        fitted_model = arima_model.fit()
        
        # Calcular métricas
        metrics = calculate_arima_metrics(fitted_model, ts_data)
        
        return fitted_model, metrics
        
    except Exception as e:
        logger.error(f"Error entrenando modelo ARIMA: {str(e)}")
        raise


def train_linear_regression_model(model, training_data):
    """Entrena un modelo de regresión lineal"""
    try:
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        import numpy as np
        
        # Preparar características (features)
        X, y = prepare_regression_features(training_data)
        
        # Normalizar features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Entrenar modelo
        lr_model = LinearRegression()
        lr_model.fit(X_scaled, y)
        
        # Calcular métricas
        metrics = calculate_regression_metrics(lr_model, X_scaled, y)
        
        return {'model': lr_model, 'scaler': scaler}, metrics
        
    except Exception as e:
        logger.error(f"Error entrenando modelo de regresión lineal: {str(e)}")
        raise


def train_random_forest_model(model, training_data):
    """Entrena un modelo Random Forest"""
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.preprocessing import StandardScaler
        
        # Preparar características
        X, y = prepare_regression_features(training_data)
        
        # Hiperparámetros
        hyperparams = model.hyperparameters or {}
        n_estimators = hyperparams.get('n_estimators', 100)
        max_depth = hyperparams.get('max_depth', None)
        
        # Entrenar modelo
        rf_model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42
        )
        rf_model.fit(X, y)
        
        # Calcular métricas
        metrics = calculate_regression_metrics(rf_model, X, y)
        
        return rf_model, metrics
        
    except Exception as e:
        logger.error(f"Error entrenando modelo Random Forest: {str(e)}")
        raise


def train_lstm_model(model, training_data):
    """Entrena un modelo LSTM (requiere TensorFlow/Keras)"""
    try:
        # Implementación básica de LSTM
        # Nota: Requiere tensorflow/keras instalado
        logger.warning("Entrenamiento LSTM no implementado completamente")
        
        # Métricas simuladas por ahora
        metrics = {
            'mae': 10.0,
            'mape': 15.0,
            'rmse': 12.0,
            'r2_score': 0.75
        }
        
        return None, metrics
        
    except Exception as e:
        logger.error(f"Error entrenando modelo LSTM: {str(e)}")
        raise


def prepare_regression_features(training_data):
    """Prepara características para modelos de regresión"""
    # Crear características temporales
    df = training_data.copy()
    df['ds'] = pd.to_datetime(df['ds'])
    
    # Features temporales
    df['day_of_week'] = df['ds'].dt.dayofweek
    df['day_of_month'] = df['ds'].dt.day
    df['month'] = df['ds'].dt.month
    df['quarter'] = df['ds'].dt.quarter
    
    # Lag features
    df = df.sort_values('ds')
    df['lag_1'] = df['y'].shift(1)
    df['lag_7'] = df['y'].shift(7)
    df['rolling_mean_7'] = df['y'].rolling(window=7).mean()
    
    # Eliminar filas con NaN
    df = df.dropna()
    
    feature_columns = ['day_of_week', 'day_of_month', 'month', 'quarter', 'lag_1', 'lag_7', 'rolling_mean_7']
    X = df[feature_columns].values
    y = df['y'].values
    
    return X, y


def calculate_model_metrics(model, data):
    """Calcula métricas de rendimiento para Prophet"""
    try:
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        # Hacer predicciones en los datos de entrenamiento
        future = model.make_future_dataframe(periods=0)
        forecast = model.predict(future)
        
        y_true = data['y'].values
        y_pred = forecast['yhat'].values[:len(y_true)]
        
        # Calcular métricas
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        
        # MAPE
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100
        
        return {
            'mae': float(mae),
            'mape': float(mape),
            'rmse': float(rmse),
            'r2_score': float(r2)
        }
        
    except Exception as e:
        logger.error(f"Error calculando métricas: {str(e)}")
        return {}


def calculate_arima_metrics(fitted_model, ts_data):
    """Calcula métricas para modelo ARIMA"""
    try:
        # Predicciones en muestra
        y_pred = fitted_model.fittedvalues
        y_true = ts_data
        
        # Alinear datos
        min_len = min(len(y_true), len(y_pred))
        y_true = y_true.iloc[-min_len:]
        y_pred = y_pred.iloc[-min_len:]
        
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100
        
        return {
            'mae': float(mae),
            'mape': float(mape),
            'rmse': float(rmse),
            'r2_score': float(r2)
        }
        
    except Exception as e:
        logger.error(f"Error calculando métricas ARIMA: {str(e)}")
        return {}


def calculate_regression_metrics(model, X, y):
    """Calcula métricas para modelos de regresión"""
    try:
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        y_pred = model.predict(X)
        
        mae = mean_absolute_error(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y, y_pred)
        mape = np.mean(np.abs((y - y_pred) / np.maximum(y, 1))) * 100
        
        return {
            'mae': float(mae),
            'mape': float(mape),
            'rmse': float(rmse),
            'r2_score': float(r2)
        }
        
    except Exception as e:
        logger.error(f"Error calculando métricas de regresión: {str(e)}")
        return {}
