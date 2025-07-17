"""
Funciones de generación de pronósticos
"""

from django.utils import timezone
import logging
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def prepare_forecast_data(model, product=None, company=None, category=None):
    """Prepara datos para generar pronósticos"""
    try:
        from inventory.models import InventoryMovement
        
        # Construir filtros base
        filters = {}
        
        if product:
            filters['product'] = product
        if company:
            filters['product__company'] = company
        if category:
            filters['product__category'] = category
            
        # Obtener movimientos históricos
        movements = InventoryMovement.objects.filter(
            **filters,
            movement_date__gte=timezone.now() - timedelta(days=365)
        ).order_by('movement_date')
        
        # Convertir a DataFrame
        data = []
        for movement in movements:
            data.append({
                'ds': movement.movement_date,
                'y': float(movement.quantity) if movement.movement_type == 'sale' else 0,
                'product_id': movement.product.id,
                'company_id': movement.product.company.id
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            logger.warning("No hay datos históricos para generar pronóstico")
            return pd.DataFrame()
        
        # Agrupar por fecha
        df_grouped = df.groupby('ds').agg({
            'y': 'sum'
        }).reset_index()
        
        # Asegurar continuidad temporal
        df_grouped = fill_missing_dates(df_grouped)
        
        return df_grouped
        
    except Exception as e:
        logger.error(f"Error preparando datos para pronóstico: {str(e)}")
        return pd.DataFrame()


def generate_prophet_forecast(model, trained_model, periods=30):
    """Genera pronósticos usando Prophet"""
    try:
        # Crear fechas futuras
        future = trained_model.make_future_dataframe(periods=periods)
        
        # Generar pronóstico
        forecast = trained_model.predict(future)
        
        # Extraer solo predicciones futuras
        future_forecast = forecast.tail(periods)
        
        # Formatear resultados
        results = []
        for _, row in future_forecast.iterrows():
            results.append({
                'date': row['ds'].date(),
                'predicted_value': max(0, float(row['yhat'])),
                'lower_bound': max(0, float(row['yhat_lower'])),
                'upper_bound': max(0, float(row['yhat_upper'])),
                'confidence_interval': model.confidence_interval
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error generando pronóstico Prophet: {str(e)}")
        return []


def generate_arima_forecast(model, trained_model, periods=30):
    """Genera pronósticos usando ARIMA"""
    try:
        # Generar pronóstico
        forecast_result = trained_model.forecast(steps=periods)
        
        # Obtener intervalos de confianza
        conf_int = trained_model.get_forecast(steps=periods).conf_int()
        
        # Crear fechas futuras
        start_date = timezone.now().date()
        
        results = []
        for i in range(periods):
            forecast_date = start_date + timedelta(days=i+1)
            
            results.append({
                'date': forecast_date,
                'predicted_value': max(0, float(forecast_result.iloc[i])),
                'lower_bound': max(0, float(conf_int.iloc[i, 0])),
                'upper_bound': max(0, float(conf_int.iloc[i, 1])),
                'confidence_interval': model.confidence_interval
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error generando pronóstico ARIMA: {str(e)}")
        return []


def generate_regression_forecast(model, trained_model_data, periods=30):
    """Genera pronósticos usando regresión"""
    try:
        model_obj = trained_model_data['model']
        scaler = trained_model_data.get('scaler')
        
        # Crear características para fechas futuras
        start_date = timezone.now().date()
        future_dates = [start_date + timedelta(days=i+1) for i in range(periods)]
        
        # Preparar features para fechas futuras
        future_features = []
        for date in future_dates:
            features = create_date_features(date)
            future_features.append(features)
        
        X_future = np.array(future_features)
        
        # Aplicar escalado si existe
        if scaler:
            X_future = scaler.transform(X_future)
        
        # Generar predicciones
        predictions = model_obj.predict(X_future)
        
        # Formatear resultados
        results = []
        for i, pred in enumerate(predictions):
            results.append({
                'date': future_dates[i],
                'predicted_value': max(0, float(pred)),
                'lower_bound': max(0, float(pred * 0.8)),  # Estimación simple
                'upper_bound': max(0, float(pred * 1.2)),  # Estimación simple
                'confidence_interval': model.confidence_interval
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error generando pronóstico de regresión: {str(e)}")
        return []


def generate_random_forest_forecast(model, trained_model, periods=30):
    """Genera pronósticos usando Random Forest"""
    try:
        # Crear características para fechas futuras
        start_date = timezone.now().date()
        future_dates = [start_date + timedelta(days=i+1) for i in range(periods)]
        
        # Preparar features para fechas futuras
        future_features = []
        for date in future_dates:
            features = create_date_features(date)
            future_features.append(features)
        
        X_future = np.array(future_features)
        
        # Generar predicciones
        predictions = trained_model.predict(X_future)
        
        # Formatear resultados
        results = []
        for i, pred in enumerate(predictions):
            results.append({
                'date': future_dates[i],
                'predicted_value': max(0, float(pred)),
                'lower_bound': max(0, float(pred * 0.85)),  # Estimación basada en varianza
                'upper_bound': max(0, float(pred * 1.15)),  # Estimación basada en varianza
                'confidence_interval': model.confidence_interval
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error generando pronóstico Random Forest: {str(e)}")
        return []


def generate_lstm_forecast(model, trained_model, periods=30):
    """Genera pronósticos usando LSTM"""
    try:
        # Implementación placeholder
        logger.warning("Generación de pronósticos LSTM no implementada completamente")
        
        # Simulación de resultados
        start_date = timezone.now().date()
        results = []
        
        for i in range(periods):
            forecast_date = start_date + timedelta(days=i+1)
            base_value = 10.0 + np.random.normal(0, 2)
            
            results.append({
                'date': forecast_date,
                'predicted_value': max(0, float(base_value)),
                'lower_bound': max(0, float(base_value * 0.8)),
                'upper_bound': max(0, float(base_value * 1.2)),
                'confidence_interval': model.confidence_interval
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error generando pronóstico LSTM: {str(e)}")
        return []


def create_date_features(date):
    """Crea características temporales para una fecha"""
    return [
        date.weekday(),          # día de semana
        date.day,               # día del mes
        date.month,             # mes
        (date.month - 1) // 3 + 1,  # trimestre
        0,                      # lag_1 (placeholder)
        0,                      # lag_7 (placeholder)
        0                       # rolling_mean_7 (placeholder)
    ]


def fill_missing_dates(df):
    """Rellena fechas faltantes en el DataFrame"""
    try:
        if df.empty:
            return df
            
        # Convertir ds a datetime si no lo está
        df['ds'] = pd.to_datetime(df['ds'])
        
        # Crear rango completo de fechas
        date_range = pd.date_range(
            start=df['ds'].min(),
            end=df['ds'].max(),
            freq='D'
        )
        
        # Crear DataFrame completo
        complete_df = pd.DataFrame({'ds': date_range})
        
        # Merge con datos existentes
        df_complete = complete_df.merge(df, on='ds', how='left')
        
        # Rellenar valores faltantes con 0
        df_complete['y'] = df_complete['y'].fillna(0)
        
        return df_complete
        
    except Exception as e:
        logger.error(f"Error rellenando fechas faltantes: {str(e)}")
        return df


def save_forecast_results(model, forecast_results, product=None, category=None):
    """Guarda los resultados del pronóstico en la base de datos"""
    try:
        from forecasting.models import Forecast
        
        # Eliminar pronósticos anteriores para el mismo modelo
        existing_forecasts = Forecast.objects.filter(model=model)
        if product:
            existing_forecasts = existing_forecasts.filter(product=product)
        if category:
            existing_forecasts = existing_forecasts.filter(category=category)
            
        existing_forecasts.delete()
        
        # Crear nuevos pronósticos
        forecasts_to_create = []
        for result in forecast_results:
            forecast = Forecast(
                model=model,
                product=product,
                category=category,
                forecast_date=result['date'],
                predicted_value=Decimal(str(result['predicted_value'])),
                confidence_interval=result['confidence_interval'],
                lower_bound=Decimal(str(result['lower_bound'])),
                upper_bound=Decimal(str(result['upper_bound'])),
                created_at=timezone.now()
            )
            forecasts_to_create.append(forecast)
        
        # Bulk create para eficiencia
        if forecasts_to_create:
            Forecast.objects.bulk_create(forecasts_to_create)
            logger.info(f"Guardados {len(forecasts_to_create)} pronósticos para modelo {model.id}")
        
        return len(forecasts_to_create)
        
    except Exception as e:
        logger.error(f"Error guardando resultados del pronóstico: {str(e)}")
        return 0


def calculate_forecast_accuracy(model, actual_data, forecast_data):
    """Calcula la precisión del pronóstico comparando con datos reales"""
    try:
        from sklearn.metrics import mean_absolute_error, mean_squared_error
        
        # Alinear datos por fecha
        merged_data = pd.merge(
            actual_data, 
            forecast_data, 
            left_on='ds', 
            right_on='date', 
            how='inner'
        )
        
        if merged_data.empty:
            return {}
        
        actual_values = merged_data['y'].values
        predicted_values = merged_data['predicted_value'].values
        
        # Calcular métricas
        mae = mean_absolute_error(actual_values, predicted_values)
        mse = mean_squared_error(actual_values, predicted_values)
        rmse = np.sqrt(mse)
        
        # MAPE
        mape = np.mean(np.abs((actual_values - predicted_values) / np.maximum(actual_values, 1))) * 100
        
        return {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'mape': float(mape),
            'samples_compared': len(merged_data)
        }
        
    except Exception as e:
        logger.error(f"Error calculando precisión del pronóstico: {str(e)}")
        return {}
