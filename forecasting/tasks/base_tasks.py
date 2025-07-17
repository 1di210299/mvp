"""
Tareas base de entrenamiento y predicción de modelos
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from decimal import Decimal

from ..models import ForecastModel, DemandForecast, ModelTrainingJob
from inventory.models import Product, Transaction, Location
from authentication.models import User, Company
from .utils import (
    should_retrain_model, prepare_training_data, save_trained_model,
    load_trained_model, get_applicable_products_for_model,
    get_applicable_locations_for_model, generate_product_forecast,
    calculate_model_accuracy
)
from .training_algorithms import (
    train_prophet_model, train_arima_model, train_linear_regression_model,
    train_random_forest_model, train_lstm_model
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def train_all_models(self):
    """
    Tarea principal para entrenar todos los modelos activos
    Se ejecuta semanalmente según la configuración de Celery Beat
    """
    try:
        logger.info("Iniciando entrenamiento de modelos de pronóstico")
        
        # Obtener modelos que necesitan reentrenamiento
        models_to_train = ForecastModel.objects.filter(
            status__in=['active', 'deprecated'],
            company__is_active=True
        )
        
        jobs_created = 0
        for model in models_to_train:
            try:
                # Verificar si necesita reentrenamiento
                if should_retrain_model(model):
                    train_forecast_model.delay(model.id)
                    jobs_created += 1
            except Exception as e:
                logger.error(f"Error al programar entrenamiento para modelo {model.id}: {str(e)}")
        
        logger.info(f"Se programaron {jobs_created} trabajos de entrenamiento")
        return f"Scheduled {jobs_created} training jobs"
        
    except Exception as exc:
        logger.error(f"Error en train_all_models: {str(exc)}")
        self.retry(countdown=60 * 10, exc=exc)


@shared_task(bind=True, max_retries=2)
def train_forecast_model(self, model_id):
    """
    Entrena un modelo de pronóstico específico
    """
    training_job = None
    try:
        model = ForecastModel.objects.get(id=model_id)
        logger.info(f"Iniciando entrenamiento del modelo: {model.name}")
        
        # Crear registro de entrenamiento
        training_job = ModelTrainingJob.objects.create(
            model=model,
            status='running',
            started_at=timezone.now()
        )
        
        # Actualizar estado del modelo
        model.status = 'training'
        model.training_started_at = timezone.now()
        model.save()
        
        # Obtener datos de entrenamiento
        training_data = prepare_training_data(model)
        
        if training_data.empty:
            raise ValueError("No hay suficientes datos para entrenamiento")
        
        # Entrenar según el tipo de modelo
        trained_model, metrics = None, {}
        
        if model.model_type == 'prophet':
            trained_model, metrics = train_prophet_model(model, training_data)
        elif model.model_type == 'arima':
            trained_model, metrics = train_arima_model(model, training_data)
        elif model.model_type == 'linear_regression':
            trained_model, metrics = train_linear_regression_model(model, training_data)
        elif model.model_type == 'random_forest':
            trained_model, metrics = train_random_forest_model(model, training_data)
        elif model.model_type == 'lstm':
            trained_model, metrics = train_lstm_model(model, training_data)
        else:
            raise ValueError(f"Tipo de modelo no soportado: {model.model_type}")
        
        # Guardar modelo entrenado
        model_path = save_trained_model(model, trained_model)
        
        # Actualizar métricas y estado
        model.mae = metrics.get('mae')
        model.mape = metrics.get('mape')
        model.rmse = metrics.get('rmse')
        model.r2_score = metrics.get('r2_score')
        model.model_file_path = model_path
        model.status = 'active'
        model.training_completed_at = timezone.now()
        model.save()
        
        # Actualizar trabajo de entrenamiento
        training_job.status = 'completed'
        training_job.completed_at = timezone.now()
        training_job.metrics = metrics
        training_job.save()
        
        # Generar pronósticos iniciales
        generate_forecasts_for_model.delay(model.id)
        
        logger.info(f"Modelo {model.name} entrenado exitosamente. MAE: {metrics.get('mae', 'N/A')}")
        return f"Model {model.name} trained successfully"
        
    except ForecastModel.DoesNotExist:
        logger.warning(f"Modelo {model_id} no encontrado")
        return f"Model {model_id} not found"
    except Exception as exc:
        logger.error(f"Error entrenando modelo {model_id}: {str(exc)}")
        
        # Actualizar estado en caso de error
        if training_job:
            training_job.status = 'failed'
            training_job.error_message = str(exc)
            training_job.completed_at = timezone.now()
            training_job.save()
        
        try:
            model = ForecastModel.objects.get(id=model_id)
            model.status = 'failed'
            model.save()
        except:
            pass
        
        self.retry(countdown=60 * 30, exc=exc)


@shared_task(bind=True, max_retries=3)
def generate_forecasts_for_model(self, model_id):
    """
    Genera pronósticos para todos los productos de un modelo
    """
    try:
        model = ForecastModel.objects.get(id=model_id, status='active')
        logger.info(f"Generando pronósticos para modelo: {model.name}")
        
        # Cargar modelo entrenado
        trained_model = load_trained_model(model)
        if not trained_model:
            raise ValueError("No se pudo cargar el modelo entrenado")
        
        # Obtener productos aplicables
        products = get_applicable_products_for_model(model)
        forecasts_generated = 0
        
        for product in products:
            locations = get_applicable_locations_for_model(model, product)
            
            for location in locations:
                try:
                    # Generar pronóstico para producto-ubicación
                    success = generate_product_forecast(model, trained_model, product, location)
                    if success:
                        forecasts_generated += 1
                except Exception as e:
                    logger.error(f"Error generando pronóstico para {product.name} en {location.name}: {str(e)}")
        
        logger.info(f"Generados {forecasts_generated} pronósticos para modelo {model.name}")
        return f"Generated {forecasts_generated} forecasts"
        
    except ForecastModel.DoesNotExist:
        logger.warning(f"Modelo {model_id} no encontrado o inactivo")
        return f"Model {model_id} not found or inactive"
    except Exception as exc:
        logger.error(f"Error generando pronósticos para modelo {model_id}: {str(exc)}")
        self.retry(countdown=60 * 5, exc=exc)


@shared_task(bind=True, max_retries=3)
def generate_product_forecast_task(self, model_id, product_id, location_id=None):
    """
    Genera pronóstico para un producto específico
    """
    try:
        model = ForecastModel.objects.get(id=model_id, status='active')
        product = Product.objects.get(id=product_id)
        location = Location.objects.get(id=location_id) if location_id else None
        
        trained_model = load_trained_model(model)
        if not trained_model:
            raise ValueError("No se pudo cargar el modelo entrenado")
        
        success = generate_product_forecast(model, trained_model, product, location)
        
        if success:
            logger.info(f"Pronóstico generado para {product.name}")
            return f"Forecast generated for {product.name}"
        else:
            return f"Failed to generate forecast for {product.name}"
        
    except Exception as exc:
        logger.error(f"Error en generate_product_forecast_task: {str(exc)}")
        self.retry(countdown=60 * 2, exc=exc)


@shared_task
def cleanup_old_forecasts():
    """
    Limpia pronósticos antiguos
    """
    try:
        # Eliminar pronósticos más antiguos de 6 meses
        cutoff_date = timezone.now().date() - timedelta(days=180)
        deleted_count = DemandForecast.objects.filter(
            forecast_date__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Eliminados {deleted_count} pronósticos antiguos")
        return f"Cleaned up {deleted_count} old forecasts"
        
    except Exception as e:
        logger.error(f"Error en cleanup_old_forecasts: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def evaluate_model_accuracy():
    """
    Evalúa la precisión de los modelos comparando pronósticos con datos reales
    """
    try:
        models = ForecastModel.objects.filter(status='active')
        evaluated_models = 0
        
        for model in models:
            try:
                accuracy_score = calculate_model_accuracy(model)
                if accuracy_score is not None:
                    # Actualizar score de precisión en el modelo
                    # Esto podría ser un campo adicional en el modelo
                    logger.info(f"Modelo {model.name}: precisión {accuracy_score:.2f}%")
                    evaluated_models += 1
            except Exception as e:
                logger.error(f"Error evaluando modelo {model.name}: {str(e)}")
        
        return f"Evaluated {evaluated_models} models"
        
    except Exception as e:
        logger.error(f"Error en evaluate_model_accuracy: {str(e)}")
        return f"Error: {str(e)}"
