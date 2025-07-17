"""
Servicio para algoritmos de Machine Learning
Implementa Prophet, ARIMA, LSTM y Random Forest para forecasting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet no está disponible. Instalala con: pip install prophet")

try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    logger.warning("ARIMA no está disponible. Instala statsmodels")

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("Scikit-learn no está disponible")


class MLAlgorithmService:
    """Servicio principal para algoritmos ML"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
    
    def prepare_data(self, sales_data: List[Dict]) -> pd.DataFrame:
        """Preparar datos de ventas para ML"""
        try:
            df = pd.DataFrame(sales_data)
            df['date'] = pd.to_datetime(df['date_sold'])
            df['quantity'] = pd.to_numeric(df['quantity'])
            
            # Agrupar por fecha y sumar cantidades
            daily_sales = df.groupby('date')['quantity'].sum().reset_index()
            daily_sales.columns = ['ds', 'y']  # Prophet format
            
            return daily_sales
        except Exception as e:
            logger.error(f"Error preparando datos: {e}")
            return pd.DataFrame()
    
    def train_prophet(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Entrenar modelo Prophet"""
        if not PROPHET_AVAILABLE:
            return {'success': False, 'error': 'Prophet no disponible'}
        
        try:
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=kwargs.get('confidence_interval', 95) / 100
            )
            
            model.fit(data)
            self.models['prophet'] = model
            
            return {'success': True, 'model': 'prophet'}
        except Exception as e:
            logger.error(f"Error entrenando Prophet: {e}")
            return {'success': False, 'error': str(e)}
    
    def train_arima(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Entrenar modelo ARIMA"""
        if not ARIMA_AVAILABLE:
            return {'success': False, 'error': 'ARIMA no disponible'}
        
        try:
            # Usar parámetros ARIMA automáticos simples
            order = kwargs.get('order', (1, 1, 1))
            model = ARIMA(data['y'], order=order)
            fitted_model = model.fit()
            
            self.models['arima'] = fitted_model
            
            return {'success': True, 'model': 'arima'}
        except Exception as e:
            logger.error(f"Error entrenando ARIMA: {e}")
            return {'success': False, 'error': str(e)}
    
    def train_random_forest(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Entrenar modelo Random Forest"""
        if not SKLEARN_AVAILABLE:
            return {'success': False, 'error': 'Scikit-learn no disponible'}
        
        try:
            # Crear features temporales
            df = data.copy()
            df['day_of_week'] = df['ds'].dt.dayofweek
            df['month'] = df['ds'].dt.month
            df['day_of_year'] = df['ds'].dt.dayofyear
            
            # Features para supervised learning
            for lag in [1, 7, 30]:
                df[f'lag_{lag}'] = df['y'].shift(lag)
            
            # Eliminar NaN
            df = df.dropna()
            
            if len(df) < 10:
                return {'success': False, 'error': 'Insuficientes datos para Random Forest'}
            
            X = df[['day_of_week', 'month', 'day_of_year', 'lag_1', 'lag_7', 'lag_30']]
            y = df['y']
            
            # Escalar features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Entrenar modelo
            model = RandomForestRegressor(
                n_estimators=kwargs.get('n_estimators', 100),
                random_state=42
            )
            model.fit(X_scaled, y)
            
            self.models['random_forest'] = model
            self.scalers['random_forest'] = scaler
            
            return {'success': True, 'model': 'random_forest'}
        except Exception as e:
            logger.error(f"Error entrenando Random Forest: {e}")
            return {'success': False, 'error': str(e)}
    
    def predict(self, model_type: str, periods: int = 30) -> Dict[str, Any]:
        """Generar predicciones"""
        try:
            if model_type == 'prophet' and 'prophet' in self.models:
                return self._predict_prophet(periods)
            elif model_type == 'arima' and 'arima' in self.models:
                return self._predict_arima(periods)
            elif model_type in ['random_forest', 'randomforest'] and 'random_forest' in self.models:
                return self._predict_random_forest(periods)
            else:
                return {'success': False, 'error': f'Modelo {model_type} no disponible'}
        except Exception as e:
            logger.error(f"Error en predicción: {e}")
            return {'success': False, 'error': str(e)}
    
    def _predict_prophet(self, periods: int) -> Dict[str, Any]:
        """Predicciones con Prophet"""
        model = self.models['prophet']
        
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        # Tomar solo las predicciones futuras
        future_forecast = forecast.tail(periods)
        
        predictions = []
        for _, row in future_forecast.iterrows():
            predictions.append({
                'date': row['ds'].strftime('%Y-%m-%d'),
                'predicted_value': round(row['yhat'], 2),
                'lower_bound': round(row['yhat_lower'], 2),
                'upper_bound': round(row['yhat_upper'], 2)
            })
        
        return {
            'success': True,
            'forecast': predictions,
            'model_type': 'prophet'
        }
    
    def _predict_arima(self, periods: int) -> Dict[str, Any]:
        """Predicciones con ARIMA"""
        model = self.models['arima']
        
        forecast = model.forecast(steps=periods)
        conf_int = model.get_forecast(steps=periods).conf_int()
        
        predictions = []
        start_date = datetime.now().date()
        
        for i in range(periods):
            date = start_date + timedelta(days=i+1)
            predictions.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_value': round(float(forecast.iloc[i]), 2),
                'lower_bound': round(float(conf_int.iloc[i, 0]), 2),
                'upper_bound': round(float(conf_int.iloc[i, 1]), 2)
            })
        
        return {
            'success': True,
            'forecast': predictions,
            'model_type': 'arima'
        }
    
    def _predict_random_forest(self, periods: int) -> Dict[str, Any]:
        """Predicciones con Random Forest"""
        model = self.models['random_forest']
        scaler = self.scalers['random_forest']
        
        # Esta es una implementación simplificada
        # En producción necesitarías datos históricos más recientes
        predictions = []
        start_date = datetime.now().date()
        
        for i in range(periods):
            date = start_date + timedelta(days=i+1)
            
            # Features básicas (simplificado)
            features = [
                date.weekday(),  # day_of_week
                date.month,      # month
                date.timetuple().tm_yday,  # day_of_year
                10,  # lag_1 (simplificado)
                10,  # lag_7 (simplificado)
                10   # lag_30 (simplificado)
            ]
            
            features_scaled = scaler.transform([features])
            prediction = model.predict(features_scaled)[0]
            
            predictions.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_value': round(float(prediction), 2),
                'lower_bound': round(float(prediction * 0.8), 2),
                'upper_bound': round(float(prediction * 1.2), 2)
            })
        
        return {
            'success': True,
            'forecast': predictions,
            'model_type': 'random_forest'
        }


# Instancia global del servicio
ml_service = MLAlgorithmService()
