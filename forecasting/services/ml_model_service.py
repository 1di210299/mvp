"""
Servicio para gestión de modelos de Machine Learning
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.db import transaction, models as django_models

from ..models import ForecastModel, ModelTrainingJob, DemandForecast
from ..ml_algorithms.model_trainer import ModelTrainer
from ..ml_algorithms.prophet_forecaster import ProphetForecaster
from ..ml_algorithms.arima_forecaster import ARIMAForecaster
from ..ml_algorithms.ensemble_forecaster import EnsembleForecaster
from inventory.models import Product, Transaction, Category
from authentication.models import Company

logger = logging.getLogger(__name__)


class MLModelService:
    """
    Servicio para gestión y operaciones de modelos de Machine Learning
    """
    
    def __init__(self):
        """
        Inicializa el servicio de modelos ML
        """
        self.model_storage_path = getattr(settings, 'ML_MODELS_PATH', 'models/')
        self.trainer = ModelTrainer(self.model_storage_path)
        
        # Asegura que el directorio existe
        os.makedirs(self.model_storage_path, exist_ok=True)
    
    def create_and_train_model(self,
                             company: Company,
                             name: str,
                             description: str = "",
                             model_type: str = 'auto',
                             products: Optional[List[Product]] = None,
                             categories: Optional[List[Category]] = None,
                             hyperparameters: Optional[Dict[str, Any]] = None,
                             optimize_hyperparameters: bool = True,
                             forecast_horizon_days: int = 30,
                             training_period_days: int = 365) -> ForecastModel:
        """
        Crea y entrena un nuevo modelo de pronóstico
        
        Args:
            company: Empresa propietaria del modelo
            name: Nombre del modelo
            description: Descripción del modelo
            model_type: Tipo de modelo ('prophet', 'arima', 'ensemble', 'auto')
            products: Lista de productos aplicables
            categories: Lista de categorías aplicables
            hyperparameters: Hiperparámetros específicos
            optimize_hyperparameters: Si optimizar hiperparámetros automáticamente
            forecast_horizon_days: Días de pronóstico
            training_period_days: Días de datos históricos para entrenamiento
            
        Returns:
            Modelo creado y entrenado
        """
        try:
            with transaction.atomic():
                # Crea el modelo en la base de datos
                forecast_model = ForecastModel.objects.create(
                    company=company,
                    name=name,
                    description=description,
                    model_type=model_type,
                    status='training',
                    forecast_horizon_days=forecast_horizon_days,
                    training_period_days=training_period_days,
                    hyperparameters=hyperparameters or {},
                    training_started_at=timezone.now()
                )
                
                # Asocia productos si se especifican
                if products:
                    forecast_model.products.set(products)
                
                # Asocia categorías si se especifican
                if categories:
                    forecast_model.categories.set(categories)
                
                # Crea job de entrenamiento
                training_job = ModelTrainingJob.objects.create(
                    model=forecast_model,
                    status='running',
                    started_at=timezone.now()
                )
            
            # Obtiene datos de entrenamiento
            training_data = self._get_training_data(forecast_model)
            
            if training_data.empty:
                raise ValueError("No hay datos históricos suficientes para entrenar el modelo")
            
            logger.info(f"Entrenando modelo {name} con {len(training_data)} observaciones")
            
            # Entrena el modelo
            if model_type == 'auto':
                best_model, best_algorithm, metrics = self._train_best_model(
                    training_data=training_data,
                    model_name=name,
                    optimize_hyperparameters=optimize_hyperparameters
                )
                actual_model_type = best_algorithm
            else:
                best_model, metrics = self._train_specific_model(
                    algorithm_name=model_type,
                    training_data=training_data,
                    hyperparameters=hyperparameters,
                    model_name=name,
                    optimize_hyperparameters=optimize_hyperparameters
                )
                actual_model_type = model_type
            
            # Actualiza el modelo con los resultados
            with transaction.atomic():
                forecast_model.model_type = actual_model_type
                forecast_model.status = 'active'
                forecast_model.mae = Decimal(str(metrics.get('mae', 0)))
                forecast_model.mape = Decimal(str(metrics.get('mape', 0)))
                forecast_model.rmse = Decimal(str(metrics.get('rmse', 0)))
                forecast_model.r2_score = Decimal(str(metrics.get('r2', 0)))
                forecast_model.hyperparameters = best_model.get_hyperparameters()
                forecast_model.training_completed_at = timezone.now()
                
                # Guarda ruta del archivo del modelo
                model_filename = f"model_{forecast_model.id}_{actual_model_type}.joblib"
                model_path = os.path.join(self.model_storage_path, model_filename)
                if best_model.save_model(model_path):
                    forecast_model.model_file_path = model_path
                    forecast_model.model_size_mb = Decimal(str(os.path.getsize(model_path) / (1024 * 1024)))
                
                forecast_model.save()
                
                # Actualiza job de entrenamiento
                training_job.status = 'completed'
                training_job.completed_at = timezone.now()
                training_job.metrics = metrics
                training_job.save()
            
            logger.info(f"Modelo {name} entrenado exitosamente con {actual_model_type}")
            
            return forecast_model
            
        except Exception as e:
            error_msg = f"Error creando y entrenando modelo {name}: {str(e)}"
            logger.error(error_msg)
            
            # Actualiza el estado a fallido
            if 'forecast_model' in locals():
                forecast_model.status = 'failed'
                forecast_model.save()
            
            if 'training_job' in locals():
                training_job.status = 'failed'
                training_job.completed_at = timezone.now()
                training_job.error_message = str(e)
                training_job.save()
            
            raise
    
    def retrain_model(self, model_id: int, optimize_hyperparameters: bool = True) -> ForecastModel:
        """
        Re-entrena un modelo existente
        
        Args:
            model_id: ID del modelo a re-entrenar
            optimize_hyperparameters: Si optimizar hiperparámetros
            
        Returns:
            Modelo re-entrenado
        """
        try:
            forecast_model = ForecastModel.objects.get(id=model_id)
            
            logger.info(f"Re-entrenando modelo {model_id}")
            
            # Actualiza estado
            forecast_model.status = 'training'
            forecast_model.training_started_at = timezone.now()
            forecast_model.save()
            
            # Crea job de entrenamiento
            training_job = ModelTrainingJob.objects.create(
                model=forecast_model,
                status='running',
                started_at=timezone.now()
            )
            
            # Obtiene datos actualizados
            training_data = self._get_training_data(forecast_model)
            
            if training_data.empty:
                raise ValueError("No hay datos históricos suficientes para re-entrenar el modelo")
            
            # Re-entrena usando el mismo algoritmo
            best_model, metrics = self._train_specific_model(
                algorithm_name=forecast_model.model_type,
                training_data=training_data,
                hyperparameters=forecast_model.hyperparameters,
                model_name=forecast_model.name,
                optimize_hyperparameters=optimize_hyperparameters
            )
            
            # Actualiza el modelo
            forecast_model.status = 'active'
            forecast_model.mae = Decimal(str(metrics.get('mae', 0)))
            forecast_model.mape = Decimal(str(metrics.get('mape', 0)))
            forecast_model.rmse = Decimal(str(metrics.get('rmse', 0)))
            forecast_model.r2_score = Decimal(str(metrics.get('r2', 0)))
            forecast_model.hyperparameters = best_model.get_hyperparameters()
            forecast_model.training_completed_at = timezone.now()
            
            # Actualiza archivo del modelo
            model_filename = f"model_{forecast_model.id}_{forecast_model.model_type}.joblib"
            model_path = os.path.join(self.model_storage_path, model_filename)
            if best_model.save_model(model_path):
                forecast_model.model_file_path = model_path
                forecast_model.model_size_mb = Decimal(str(os.path.getsize(model_path) / (1024 * 1024)))
            
            forecast_model.save()
            
            # Completa job
            training_job.status = 'completed'
            training_job.completed_at = timezone.now()
            training_job.metrics = metrics
            training_job.save()
            
            logger.info(f"Modelo {model_id} re-entrenado exitosamente")
            
            return forecast_model
            
        except Exception as e:
            logger.error(f"Error re-entrenando modelo {model_id}: {str(e)}")
            
            if 'forecast_model' in locals():
                forecast_model.status = 'failed'
                forecast_model.save()
            
            if 'training_job' in locals():
                training_job.status = 'failed'
                training_job.completed_at = timezone.now()
                training_job.error_message = str(e)
                training_job.save()
            
            raise
    
    def load_trained_model(self, model_id: int):
        """
        Carga un modelo entrenado desde archivo
        
        Args:
            model_id: ID del modelo a cargar
            
        Returns:
            Instancia del modelo ML cargado
        """
        try:
            forecast_model = ForecastModel.objects.get(id=model_id)
            
            if forecast_model.status != 'active':
                raise ValueError(f"El modelo {model_id} no está activo")
            
            if not forecast_model.model_file_path or not os.path.exists(forecast_model.model_file_path):
                raise ValueError(f"Archivo del modelo no encontrado: {forecast_model.model_file_path}")
            
            # Carga el modelo según su tipo
            algorithm_name = forecast_model.model_type
            ml_model = self.trainer.load_model(forecast_model.model_file_path, algorithm_name)
            
            return ml_model
            
        except Exception as e:
            logger.error(f"Error cargando modelo {model_id}: {str(e)}")
            raise
    
    def compare_algorithms(self, 
                          company: Company,
                          products: Optional[List[Product]] = None,
                          categories: Optional[List[Category]] = None,
                          algorithms: Optional[List[str]] = None,
                          training_period_days: int = 365) -> Dict[str, Dict[str, float]]:
        """
        Compara diferentes algoritmos para los mismos datos
        
        Args:
            company: Empresa
            products: Productos a analizar
            categories: Categorías a analizar
            algorithms: Lista de algoritmos a comparar
            training_period_days: Días de datos para entrenamiento
            
        Returns:
            Diccionario con métricas por algoritmo
        """
        if algorithms is None:
            algorithms = ['prophet', 'arima', 'ensemble']
        
        try:
            # Crea modelo temporal para obtener datos
            temp_model = ForecastModel(
                company=company,
                training_period_days=training_period_days
            )
            
            # Obtiene datos
            data = self._get_training_data(temp_model, products, categories)
            
            if data.empty:
                raise ValueError("No hay datos suficientes para comparar algoritmos")
            
            # Divide datos para evaluación
            split_point = int(len(data) * 0.8)
            train_data = data.iloc[:split_point]
            test_data = data.iloc[split_point:]
            
            # Entrena múltiples modelos
            results = self.trainer.train_multiple_models(
                algorithm_names=algorithms,
                data=train_data,
                target_column='quantity',
                parallel=True
            )
            
            # Evalúa cada modelo
            from ..ml_algorithms import ModelEvaluator
            evaluator = ModelEvaluator()
            
            comparison_results = {}
            
            for algorithm_name, (model, train_metrics) in results.items():
                if model is not None:
                    try:
                        eval_metrics = evaluator.evaluate_model(
                            model=model,
                            test_data=test_data,
                            target_column='quantity'
                        )
                        
                        comparison_results[algorithm_name] = {
                            'train_mae': train_metrics.get('mae', 0),
                            'train_mape': train_metrics.get('mape', 0),
                            'test_mae': eval_metrics.get('mae', 0),
                            'test_mape': eval_metrics.get('mape', 0),
                            'test_rmse': eval_metrics.get('rmse', 0),
                            'test_r2': eval_metrics.get('r2', 0)
                        }
                    except Exception as e:
                        logger.warning(f"Error evaluando {algorithm_name}: {str(e)}")
                        comparison_results[algorithm_name] = {'error': str(e)}
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error comparando algoritmos: {str(e)}")
            raise
    
    def get_model_performance(self, model_id: int) -> Dict[str, Any]:
        """
        Obtiene métricas de rendimiento de un modelo
        
        Args:
            model_id: ID del modelo
            
        Returns:
            Diccionario con métricas de rendimiento
        """
        try:
            forecast_model = ForecastModel.objects.get(id=model_id)
            
            performance = {
                'model_id': model_id,
                'model_name': forecast_model.name,
                'algorithm': forecast_model.model_type,
                'status': forecast_model.status,
                'mae': float(forecast_model.mae or 0),
                'mape': float(forecast_model.mape or 0),
                'rmse': float(forecast_model.rmse or 0),
                'r2_score': float(forecast_model.r2_score or 0),
                'accuracy_score': forecast_model.accuracy_score,
                'training_duration': forecast_model.training_duration,
                'last_prediction': forecast_model.last_prediction_at,
                'model_size_mb': float(forecast_model.model_size_mb or 0)
            }
            
            # Añade estadísticas de pronósticos recientes
            recent_forecasts = DemandForecast.objects.filter(
                model=forecast_model,
                created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            performance['recent_forecasts_count'] = recent_forecasts.count()
            
            if recent_forecasts.exists():
                performance['avg_predicted_demand'] = float(
                    recent_forecasts.aggregate(avg=django_models.Avg('predicted_demand'))['avg'] or 0
                )
                performance['avg_confidence_interval_width'] = float(
                    recent_forecasts.aggregate(
                        avg=django_models.Avg(django_models.F('confidence_interval__upper') - django_models.F('confidence_interval__lower'))
                    )['avg'] or 0
                )
            
            return performance
            
        except Exception as e:
            logger.error(f"Error obteniendo rendimiento del modelo {model_id}: {str(e)}")
            raise
    
    def _get_training_data(self, 
                          forecast_model: ForecastModel,
                          products: Optional[List[Product]] = None,
                          categories: Optional[List[Category]] = None) -> pd.DataFrame:
        """
        Obtiene datos de entrenamiento para un modelo
        """
        try:
            # Calcula fecha de inicio
            start_date = timezone.now().date() - timedelta(days=forecast_model.training_period_days)
            
            # Determina productos a analizar
            if products:
                target_products = products
            else:
                target_products = forecast_model.products.all()
                if not target_products:
                    # Si no hay productos específicos, usa todos los de la empresa
                    target_products = Product.objects.filter(company=forecast_model.company)
            
            # Filtra por categorías si se especifican
            if categories:
                target_products = target_products.filter(category__in=categories)
            elif forecast_model.categories.exists():
                target_products = target_products.filter(category__in=forecast_model.categories.all())
            
            # Obtiene transacciones
            from django.db import models
            transactions = Transaction.objects.filter(
                product__in=target_products,
                transaction_date__gte=start_date,
                transaction_type__in=['sale', 'usage']
            ).values('transaction_date').annotate(
                quantity=models.Sum('quantity')
            ).order_by('transaction_date')
            
            if not transactions.exists():
                return pd.DataFrame()
            
            # Convierte a DataFrame
            df = pd.DataFrame(list(transactions))
            df['date'] = pd.to_datetime(df['transaction_date'])
            df = df.set_index('date')
            df = df[['quantity']]
            
            # Rellena fechas faltantes
            full_date_range = pd.date_range(start=start_date, end=timezone.now().date(), freq='D')
            df = df.reindex(full_date_range, fill_value=0)
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de entrenamiento: {str(e)}")
            return pd.DataFrame()
    
    def _train_best_model(self, 
                         training_data: pd.DataFrame,
                         model_name: str,
                         optimize_hyperparameters: bool = True) -> Tuple[Any, str, Dict[str, float]]:
        """
        Entrena automáticamente el mejor modelo
        """
        return self.trainer.auto_train_best_model(
            data=training_data,
            target_column='quantity',
            algorithms_to_try=['prophet', 'arima', 'ensemble'],
            optimization_metric='mae',
            optimize_hyperparameters=optimize_hyperparameters,
            model_name=model_name
        )
    
    def _train_specific_model(self,
                            algorithm_name: str,
                            training_data: pd.DataFrame,
                            hyperparameters: Optional[Dict[str, Any]],
                            model_name: str,
                            optimize_hyperparameters: bool = True) -> Tuple[Any, Dict[str, float]]:
        """
        Entrena un modelo específico
        """
        if optimize_hyperparameters and algorithm_name in ['prophet', 'arima']:
            best_model, best_params, optimization_history = self.trainer.hyperparameter_optimization(
                algorithm_name=algorithm_name,
                data=training_data,
                target_column='quantity',
                optimization_metric='mae'
            )
            return best_model, best_model.metrics
        else:
            return self.trainer.train_single_model(
                algorithm_name=algorithm_name,
                data=training_data,
                target_column='quantity',
                hyperparameters=hyperparameters,
                model_name=model_name
            )
