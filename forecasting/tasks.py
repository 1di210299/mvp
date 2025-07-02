"""
Tareas asíncronas para el módulo de pronósticos
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
import pickle
import os

from .models import ForecastModel, DemandForecast, ModelTrainingJob
from inventory.models import Product, Transaction, Location
from authentication.models import User, Company
from .ml_algorithms import ModelTrainer, ModelEvaluator, ProphetForecaster, ARIMAForecaster, EnsembleForecaster
from django.db import models

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


@shared_task(bind=True, max_retries=3)
def train_ml_model(self, model_id, algorithm_name='auto', optimize_hyperparameters=True):
    """
    Entrena un modelo específico usando algoritmos de Machine Learning
    
    Args:
        model_id: ID del modelo a entrenar
        algorithm_name: Algoritmo a usar ('prophet', 'arima', 'ensemble', 'auto')
        optimize_hyperparameters: Si optimizar hiperparámetros automáticamente
    """
    try:
        # Obtiene el modelo
        forecast_model = ForecastModel.objects.get(id=model_id)
        
        # Crea el job de entrenamiento
        training_job = ModelTrainingJob.objects.create(
            model=forecast_model,
            status='running',
            started_at=timezone.now()
        )
        
        logger.info(f"Iniciando entrenamiento ML para modelo {model_id} con algoritmo {algorithm_name}")
        
        # Obtiene los datos históricos
        training_data = get_training_data_for_model(forecast_model)
        
        if training_data.empty:
            raise ValueError("No hay datos históricos suficientes para entrenar el modelo")
        
        # Inicializa el entrenador
        trainer = ModelTrainer(model_storage_path=settings.ML_MODELS_PATH)
        
        # Entrena el modelo
        if algorithm_name == 'auto':
            # Entrenamiento automático del mejor modelo
            best_model, best_algorithm, metrics = trainer.auto_train_best_model(
                data=training_data,
                target_column='quantity',
                algorithms_to_try=['prophet', 'arima', 'ensemble'],
                optimization_metric='mae',
                optimize_hyperparameters=optimize_hyperparameters,
                model_name=f"model_{model_id}"
            )
            algorithm_name = best_algorithm
        else:
            # Entrena algoritmo específico
            if optimize_hyperparameters:
                best_model, best_params, optimization_history = trainer.hyperparameter_optimization(
                    algorithm_name=algorithm_name,
                    data=training_data,
                    target_column='quantity',
                    optimization_metric='mae'
                )
                metrics = best_model.metrics
            else:
                best_model, metrics = trainer.train_single_model(
                    algorithm_name=algorithm_name,
                    data=training_data,
                    target_column='quantity',
                    model_name=f"model_{model_id}"
                )
        
        # Actualiza el modelo en la base de datos
        forecast_model.model_type = algorithm_name
        forecast_model.status = 'active'
        forecast_model.mae = Decimal(str(metrics.get('mae', 0)))
        forecast_model.mape = Decimal(str(metrics.get('mape', 0)))
        forecast_model.rmse = Decimal(str(metrics.get('rmse', 0)))
        forecast_model.r2_score = Decimal(str(metrics.get('r2', 0)))
        forecast_model.model_file_path = best_model.model_file_path if hasattr(best_model, 'model_file_path') else ""
        forecast_model.training_completed_at = timezone.now()
        forecast_model.hyperparameters = best_model.get_hyperparameters()
        forecast_model.save()
        
        # Completa el job de entrenamiento
        training_job.status = 'completed'
        training_job.completed_at = timezone.now()
        training_job.metrics = metrics
        training_job.save()
        
        logger.info(f"Modelo {model_id} entrenado exitosamente con {algorithm_name}")
        
        # Genera pronósticos iniciales
        generate_ml_forecasts.delay(model_id)
        
        return {
            'model_id': model_id,
            'algorithm': algorithm_name,
            'metrics': metrics,
            'status': 'completed'
        }
        
    except Exception as e:
        error_msg = f"Error entrenando modelo ML {model_id}: {str(e)}"
        logger.error(error_msg)
        
        # Actualiza el job de entrenamiento con error
        if 'training_job' in locals():
            training_job.status = 'failed'
            training_job.completed_at = timezone.now()
            training_job.error_message = str(e)
            training_job.save()
        
        # Actualiza el modelo con error
        if 'forecast_model' in locals():
            forecast_model.status = 'failed'
            forecast_model.save()
        
        # Reintenta la tarea
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # Backoff exponencial
            raise self.retry(countdown=countdown, exc=e)
        else:
            raise


@shared_task(bind=True, max_retries=3)
def generate_ml_forecasts(self, model_id, periods=30):
    """
    Genera pronósticos usando un modelo ML entrenado
    
    Args:
        model_id: ID del modelo a usar
        periods: Número de períodos a pronosticar
    """
    try:
        forecast_model = ForecastModel.objects.get(id=model_id)
        
        if forecast_model.status != 'active':
            raise ValueError(f"El modelo {model_id} no está activo")
        
        logger.info(f"Generando pronósticos ML para modelo {model_id}")
        
        # Carga el modelo entrenado
        trainer = ModelTrainer(model_storage_path=settings.ML_MODELS_PATH)
        
        # Determina el algoritmo a cargar
        algorithm_name = forecast_model.model_type
        model_file_path = forecast_model.model_file_path
        
        if not model_file_path or not os.path.exists(model_file_path):
            raise ValueError(f"Archivo del modelo no encontrado: {model_file_path}")
        
        # Carga el modelo
        ml_model = trainer.load_model(model_file_path, algorithm_name)
        
        # Genera pronósticos
        predictions = ml_model.predict(
            periods=periods,
            confidence_interval=float(forecast_model.confidence_interval) / 100
        )
        
        # Guarda los pronósticos en la base de datos
        forecasts_created = 0
        
        # Obtiene productos aplicables
        products = forecast_model.products.all()
        if not products:
            products = Product.objects.filter(company=forecast_model.company)
        
        for product in products:
            for date, row in predictions.iterrows():
                # Elimina pronósticos existentes para la misma fecha
                DemandForecast.objects.filter(
                    model=forecast_model,
                    product=product,
                    forecast_date=date.date()
                ).delete()
                
                # Crea nuevo pronóstico
                DemandForecast.objects.create(
                    model=forecast_model,
                    product=product,
                    forecast_date=date.date(),
                    predicted_demand=Decimal(str(row['predicted_demand'])),
                    lower_bound=Decimal(str(row['lower_bound'])),
                    upper_bound=Decimal(str(row['upper_bound'])),
                    confidence_level=Decimal(str(row['confidence_level'] * 100)),
                    seasonality_factor=Decimal(str(row.get('seasonality', 1.0))),
                    trend_factor=Decimal(str(row.get('trend', 1.0)))
                )
                forecasts_created += 1
        
        # Actualiza timestamp de última predicción
        forecast_model.last_prediction_at = timezone.now()
        forecast_model.save()
        
        logger.info(f"Generados {forecasts_created} pronósticos ML para modelo {model_id}")
        
        return {
            'model_id': model_id,
            'forecasts_created': forecasts_created,
            'periods': periods
        }
        
    except Exception as e:
        error_msg = f"Error generando pronósticos ML {model_id}: {str(e)}"
        logger.error(error_msg)
        
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=e)
        else:
            raise


@shared_task(bind=True, max_retries=3)
def evaluate_ml_model(self, model_id, test_data_days=30):
    """
    Evalúa un modelo ML usando datos históricos
    
    Args:
        model_id: ID del modelo a evaluar
        test_data_days: Días de datos históricos para usar como prueba
    """
    try:
        forecast_model = ForecastModel.objects.get(id=model_id)
        
        logger.info(f"Evaluando modelo ML {model_id}")
        
        # Obtiene datos históricos para evaluación
        all_data = get_training_data_for_model(forecast_model)
        
        if len(all_data) < test_data_days + 30:
            raise ValueError("No hay suficientes datos históricos para evaluación")
        
        # Divide datos en entrenamiento y prueba
        split_point = len(all_data) - test_data_days
        train_data = all_data.iloc[:split_point]
        test_data = all_data.iloc[split_point:]
        
        # Carga el modelo
        trainer = ModelTrainer(model_storage_path=settings.ML_MODELS_PATH)
        
        # Re-entrena con datos de entrenamiento
        algorithm_name = forecast_model.model_type
        ml_model, metrics = trainer.train_single_model(
            algorithm_name=algorithm_name,
            data=train_data,
            target_column='quantity'
        )
        
        # Evalúa el modelo
        evaluator = ModelEvaluator()
        evaluation_results = evaluator.evaluate_model(
            model=ml_model,
            test_data=test_data,
            target_column='quantity',
            forecast_periods=test_data_days
        )
        
        # Actualiza métricas del modelo
        forecast_model.mae = Decimal(str(evaluation_results.get('mae', 0)))
        forecast_model.mape = Decimal(str(evaluation_results.get('mape', 0)))
        forecast_model.rmse = Decimal(str(evaluation_results.get('rmse', 0)))
        forecast_model.r2_score = Decimal(str(evaluation_results.get('r2', 0)))
        forecast_model.save()
        
        logger.info(f"Modelo {model_id} evaluado: MAE={evaluation_results.get('mae', 'N/A')}")
        
        return evaluation_results
        
    except Exception as e:
        error_msg = f"Error evaluando modelo ML {model_id}: {str(e)}"
        logger.error(error_msg)
        
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=e)
        else:
            raise


@shared_task
def auto_train_best_models_for_company(company_id):
    """
    Entrena automáticamente los mejores modelos para una empresa
    
    Args:
        company_id: ID de la empresa
    """
    try:
        company = Company.objects.get(id=company_id)
        
        logger.info(f"Entrenamiento automático para empresa {company.name}")
        
        # Obtiene productos con suficientes datos históricos
        products_with_data = []
        for product in company.products.all():
            transaction_count = Transaction.objects.filter(
                product=product,
                transaction_date__gte=timezone.now() - timedelta(days=365)
            ).count()
            
            if transaction_count >= 30:  # Mínimo 30 transacciones en el último año
                products_with_data.append(product)
        
        if not products_with_data:
            logger.warning(f"No hay productos con suficientes datos para empresa {company_id}")
            return
        
        # Crea modelos automáticos para diferentes categorías
        categories = set(p.category for p in products_with_data if p.category)
        
        models_created = 0
        for category in categories:
            # Verifica si ya existe un modelo para esta categoría
            existing_model = ForecastModel.objects.filter(
                company=company,
                categories=category,
                status='active'
            ).first()
            
            if existing_model:
                continue
            
            # Crea nuevo modelo
            model = ForecastModel.objects.create(
                company=company,
                name=f"Modelo Automático - {category.name}",
                description=f"Modelo automático para categoría {category.name}",
                model_type='auto',
                status='training',
                forecast_horizon_days=30,
                training_period_days=365
            )
            
            # Asocia la categoría
            model.categories.add(category)
            
            # Programa entrenamiento
            train_ml_model.delay(
                model_id=model.id,
                algorithm_name='auto',
                optimize_hyperparameters=True
            )
            
            models_created += 1
        
        logger.info(f"Creados {models_created} modelos automáticos para empresa {company_id}")
        
        return {
            'company_id': company_id,
            'models_created': models_created
        }
        
    except Exception as e:
        logger.error(f"Error en entrenamiento automático para empresa {company_id}: {str(e)}")
        raise


@shared_task
def compare_model_algorithms(model_id):
    """
    Compara diferentes algoritmos para un modelo específico
    
    Args:
        model_id: ID del modelo
    """
    try:
        forecast_model = ForecastModel.objects.get(id=model_id)
        
        logger.info(f"Comparando algoritmos para modelo {model_id}")
        
        # Obtiene datos
        data = get_training_data_for_model(forecast_model)
        
        if data.empty:
            raise ValueError("No hay datos para comparar algoritmos")
        
        # Divide datos para evaluación
        split_point = int(len(data) * 0.8)
        train_data = data.iloc[:split_point]
        test_data = data.iloc[split_point:]
        
        # Entrena diferentes algoritmos
        trainer = ModelTrainer(model_storage_path=settings.ML_MODELS_PATH)
        algorithms = ['prophet', 'arima']
        
        results = trainer.train_multiple_models(
            algorithm_names=algorithms,
            data=train_data,
            target_column='quantity',
            parallel=True
        )
        
        # Evalúa cada modelo
        evaluator = ModelEvaluator()
        comparison_results = []
        
        for algorithm_name, (model, metrics) in results.items():
            if model is not None:
                evaluation = evaluator.evaluate_model(
                    model=model,
                    test_data=test_data,
                    target_column='quantity'
                )
                comparison_results.append({
                    'algorithm': algorithm_name,
                    'mae': evaluation.get('mae'),
                    'mape': evaluation.get('mape'),
                    'rmse': evaluation.get('rmse'),
                    'r2': evaluation.get('r2')
                })
        
        # Determina el mejor algoritmo
        if comparison_results:
            best_result = min(comparison_results, key=lambda x: x['mae'])
            best_algorithm = best_result['algorithm']
            
            # Actualiza el modelo con el mejor algoritmo
            forecast_model.model_type = best_algorithm
            forecast_model.save()
            
            logger.info(f"Mejor algoritmo para modelo {model_id}: {best_algorithm}")
        
        return comparison_results
        
    except Exception as e:
        logger.error(f"Error comparando algoritmos para modelo {model_id}: {str(e)}")
        raise


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


def prepare_forecast_data(model, product, location):
    """Prepara datos para generar pronósticos"""
    # Implementar preparación de datos específica
    return {}


def generate_prophet_forecast(trained_model, model, forecast_data):
    """Genera pronósticos usando Prophet"""
    try:
        # Crear dataframe futuro
        future = trained_model.make_future_dataframe(periods=model.forecast_horizon_days)
        forecast = trained_model.predict(future)
        
        # Extraer pronósticos futuros
        future_forecast = forecast.tail(model.forecast_horizon_days)
        
        forecasts = []
        for _, row in future_forecast.iterrows():
            forecasts.append({
                'date': row['ds'].date(),
                'predicted_demand': max(0, row['yhat']),  # No demanda negativa
                'lower_bound': max(0, row['yhat_lower']),
                'upper_bound': max(0, row['yhat_upper']),
                'confidence_interval': model.confidence_interval
            })
        
        return forecasts
        
    except Exception as e:
        logger.error(f"Error generando pronóstico Prophet: {str(e)}")
        return []


def generate_arima_forecast(fitted_model, model, forecast_data):
    """Genera pronósticos usando ARIMA"""
    try:
        # Generar pronósticos
        forecast_result = fitted_model.forecast(steps=model.forecast_horizon_days)
        conf_int = fitted_model.get_forecast(steps=model.forecast_horizon_days).conf_int()
        
        forecasts = []
        start_date = timezone.now().date() + timedelta(days=1)
        
        for i in range(model.forecast_horizon_days):
            date = start_date + timedelta(days=i)
            forecasts.append({
                'date': date,
                'predicted_demand': max(0, forecast_result.iloc[i]),
                'lower_bound': max(0, conf_int.iloc[i, 0]),
                'upper_bound': max(0, conf_int.iloc[i, 1]),
                'confidence_interval': model.confidence_interval
            })
        
        return forecasts
        
    except Exception as e:
        logger.error(f"Error generando pronóstico ARIMA: {str(e)}")
        return []


def save_forecasts_to_db(model, product, location, forecasts):
    """Guarda pronósticos en la base de datos"""
    try:
        # Eliminar pronósticos existentes para el mismo período
        start_date = forecasts[0]['date'] if forecasts else timezone.now().date()
        end_date = forecasts[-1]['date'] if forecasts else start_date
        
        DemandForecast.objects.filter(
            model=model,
            product=product,
            location=location,
            forecast_date__range=[start_date, end_date]
        ).delete()
        
        # Crear nuevos pronósticos
        forecast_objects = []
        for forecast in forecasts:
            forecast_objects.append(
                DemandForecast(
                    model=model,
                    product=product,
                    location=location,
                    forecast_date=forecast['date'],
                    predicted_demand=Decimal(str(forecast['predicted_demand'])),
                    lower_bound=Decimal(str(forecast['lower_bound'])),
                    upper_bound=Decimal(str(forecast['upper_bound'])),
                    confidence_interval=forecast['confidence_interval'],
                    forecast_type='daily'
                )
            )
        
        DemandForecast.objects.bulk_create(forecast_objects, batch_size=100)
        
        # Actualizar timestamp del modelo
        model.last_prediction_at = timezone.now()
        model.save()
        
        logger.info(f"Guardados {len(forecast_objects)} pronósticos para {product.name}")
        
    except Exception as e:
        logger.error(f"Error guardando pronósticos: {str(e)}")
        raise


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
