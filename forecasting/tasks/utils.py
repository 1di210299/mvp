"""
Utilidades y funciones de apoyo para las tareas de forecasting
"""

from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from decimal import Decimal
import pickle
import os
from django.db import models

from ..models import ForecastModel, DemandForecast, ModelTrainingJob
from inventory.models import Product, Transaction, Location
from authentication.models import Company

logger = logging.getLogger(__name__)


def should_retrain_model(model):
    """Determina si un modelo necesita reentrenamiento"""
    if not model.training_completed_at:
        return True
    
    # Reentrenar si han pasado más de 30 días
    days_since_training = (timezone.now() - model.training_completed_at).days
    return days_since_training > 30


def prepare_training_data(model):
    """Prepara los datos de entrenamiento para el modelo"""
    try:
        # Obtener datos históricos de transacciones
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=model.training_period_days)
        
        products = get_applicable_products_for_model(model)
        
        # Crear DataFrame con datos de demanda
        data_list = []
        for product in products:
            locations = get_applicable_locations_for_model(model, product)
            
            for location in locations:
                transactions = Transaction.objects.filter(
                    product=product,
                    location=location,
                    transaction_type='sale',  # Solo salidas (demanda)
                    transaction_date__date__range=[start_date, end_date]
                ).values('transaction_date', 'quantity')
                
                for transaction in transactions:
                    data_list.append({
                        'ds': transaction['transaction_date'].date(),  # fecha (nomenclatura Prophet)
                        'y': transaction['quantity'],  # cantidad (nomenclatura Prophet)
                        'product_id': product.id,
                        'location_id': location.id if location else None,
                    })
        
        if not data_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(data_list)
        
        # Agrupar por fecha para obtener demanda diaria total
        if 'product_id' in df.columns:
            df = df.groupby(['ds', 'product_id', 'location_id'])['y'].sum().reset_index()
        
        return df
        
    except Exception as e:
        logger.error(f"Error preparando datos de entrenamiento: {str(e)}")
        return pd.DataFrame()


def save_trained_model(model, trained_model):
    """Guarda el modelo entrenado en disco"""
    try:
        # Crear directorio si no existe
        models_dir = os.path.join(settings.MEDIA_ROOT, 'forecast_models')
        os.makedirs(models_dir, exist_ok=True)
        
        # Nombre del archivo
        filename = f"model_{model.id}_{model.version}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        file_path = os.path.join(models_dir, filename)
        
        # Guardar modelo
        with open(file_path, 'wb') as f:
            pickle.dump(trained_model, f)
        
        # Calcular tamaño del archivo
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        model.model_size_mb = Decimal(str(round(file_size_mb, 2)))
        
        return file_path
        
    except Exception as e:
        logger.error(f"Error guardando modelo: {str(e)}")
        raise


def load_trained_model(model):
    """Carga un modelo entrenado desde disco"""
    try:
        if not model.model_file_path or not os.path.exists(model.model_file_path):
            return None
        
        with open(model.model_file_path, 'rb') as f:
            trained_model = pickle.load(f)
        
        return trained_model
        
    except Exception as e:
        logger.error(f"Error cargando modelo {model.id}: {str(e)}")
        return None


def get_applicable_products_for_model(model):
    """Obtiene productos aplicables para un modelo"""
    if model.products.exists():
        return model.products.filter(is_active=True)
    elif model.categories.exists():
        return Product.objects.filter(
            category__in=model.categories.all(),
            is_active=True,
            company=model.company
        )
    else:
        return Product.objects.filter(is_active=True, company=model.company)


def get_applicable_locations_for_model(model, product):
    """Obtiene ubicaciones aplicables para un modelo y producto"""
    # Por ahora, retorna todas las ubicaciones activas de la empresa
    return Location.objects.filter(is_active=True, company=model.company)


def generate_product_forecast(model, trained_model, product, location):
    """Genera pronóstico para un producto específico"""
    try:
        # Preparar datos para predicción
        from .forecast_generation import prepare_forecast_data, generate_prophet_forecast, generate_arima_forecast, save_forecasts_to_db
        
        forecast_data = prepare_forecast_data(model, product, location)
        
        if model.model_type == 'prophet':
            forecasts = generate_prophet_forecast(trained_model, model, forecast_data)
        elif model.model_type == 'arima':
            forecasts = generate_arima_forecast(trained_model, model, forecast_data)
        else:
            # Para otros modelos, implementar según necesidad
            logger.warning(f"Generación de pronóstico no implementada para {model.model_type}")
            return False
        
        # Guardar pronósticos en la base de datos
        save_forecasts_to_db(model, product, location, forecasts)
        
        return True
        
    except Exception as e:
        logger.error(f"Error generando pronóstico para {product.name}: {str(e)}")
        return False


def calculate_model_accuracy(model):
    """Calcula la precisión del modelo comparando con datos reales"""
    try:
        # Obtener pronósticos de hace 30 días
        comparison_date = timezone.now().date() - timedelta(days=30)
        
        forecasts = DemandForecast.objects.filter(
            model=model,
            forecast_date=comparison_date
        )
        
        if not forecasts.exists():
            return None
        
        total_error = 0
        count = 0
        
        for forecast in forecasts:
            # Obtener demanda real para esa fecha
            actual_demand = Transaction.objects.filter(
                product=forecast.product,
                location=forecast.location,
                transaction_type='sale',
                transaction_date__date=comparison_date
            ).aggregate(
                total=models.Sum('quantity')
            )['total'] or 0
            
            # Calcular error porcentual
            if actual_demand > 0:
                error = abs(float(forecast.predicted_demand) - actual_demand) / actual_demand
                total_error += error
                count += 1
        
        if count > 0:
            mape = (total_error / count) * 100
            accuracy = max(0, 100 - mape)
            return accuracy
        
        return None
        
    except Exception as e:
        logger.error(f"Error calculando precisión del modelo {model.id}: {str(e)}")
        return None


def get_training_data_for_model(forecast_model):
    """
    Obtiene datos de entrenamiento para un modelo específico
    
    Args:
        forecast_model: Instancia del modelo
        
    Returns:
        DataFrame con datos históricos
    """
    try:
        # Calcula fecha de inicio
        start_date = timezone.now().date() - timedelta(days=forecast_model.training_period_days)
        
        # Obtiene productos aplicables
        products = forecast_model.products.all()
        if not products:
            products = Product.objects.filter(company=forecast_model.company)
        
        # Obtiene categorías aplicables
        categories = forecast_model.categories.all()
        if categories:
            products = products.filter(category__in=categories)
        
        # Obtiene transacciones
        transactions = Transaction.objects.filter(
            product__in=products,
            transaction_date__gte=start_date,
            transaction_type__in=['sale', 'usage']
        ).values('transaction_date', 'product__sku').annotate(
            quantity=models.Sum('quantity')
        ).order_by('transaction_date')
        
        if not transactions:
            return pd.DataFrame()
        
        # Convierte a DataFrame
        df = pd.DataFrame(list(transactions))
        
        # Agrupa por fecha
        daily_data = df.groupby('transaction_date')['quantity'].sum().reset_index()
        daily_data['date'] = pd.to_datetime(daily_data['transaction_date'])
        daily_data = daily_data.set_index('date')
        daily_data = daily_data[['quantity']]
        
        # Rellena fechas faltantes
        full_date_range = pd.date_range(start=start_date, end=timezone.now().date(), freq='D')
        daily_data = daily_data.reindex(full_date_range, fill_value=0)
        
        return daily_data
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de entrenamiento: {str(e)}")
        return pd.DataFrame()
