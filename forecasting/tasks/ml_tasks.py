"""
Tareas avanzadas de Machine Learning
"""

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from decimal import Decimal
import os

from ..models import ForecastModel, DemandForecast, ModelTrainingJob
from inventory.models import Product, Transaction, Location
from authentication.models import User, Company
from ..ml_algorithms import ModelTrainer, ModelEvaluator, ProphetForecaster, ARIMAForecaster, EnsembleForecaster
from .utils import get_training_data_for_model

logger = logging.getLogger(__name__)


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
