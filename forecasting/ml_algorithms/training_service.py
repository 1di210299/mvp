"""
Servicio de entrenamiento de modelos ML
Integra con Django models y maneja el ciclo de vida del entrenamiento
"""

from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from inventory.models import Sale, Product
from ..models import ForecastModel, DemandForecast
from .ml_service import ml_service

logger = logging.getLogger(__name__)


class ModelTrainingService:
    """Servicio para entrenar y manejar modelos ML"""
    
    def train_model(self, forecast_model: ForecastModel) -> Dict[str, Any]:
        """Entrenar un modelo de forecasting"""
        try:
            logger.info(f"Iniciando entrenamiento del modelo {forecast_model.name}")
            
            # Obtener datos de entrenamiento
            training_data = self._get_training_data(forecast_model)
            
            if not training_data:
                return {
                    'success': False,
                    'error': 'No hay datos suficientes para entrenar el modelo'
                }
            
            # Preparar datos para ML
            prepared_data = ml_service.prepare_data(training_data)
            
            if prepared_data.empty:
                return {
                    'success': False,
                    'error': 'Error preparando datos para entrenamiento'
                }
            
            # Entrenar según el tipo de modelo
            result = self._train_by_type(forecast_model, prepared_data)
            
            if result['success']:
                # Actualizar estado del modelo
                forecast_model.status = 'active'
                forecast_model.last_trained = timezone.now()
                forecast_model.save()
                
                logger.info(f"Modelo {forecast_model.name} entrenado exitosamente")
            else:
                forecast_model.status = 'failed'
                forecast_model.save()
                
                logger.error(f"Error entrenando modelo {forecast_model.name}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en entrenamiento: {e}")
            forecast_model.status = 'failed'
            forecast_model.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_training_data(self, forecast_model: ForecastModel) -> List[Dict]:
        """Obtener datos históricos para entrenar"""
        try:
            # Calcular fecha de inicio
            end_date = timezone.now()
            start_date = end_date - timedelta(days=forecast_model.training_period_days)
            
            # Query base para ventas
            sales_query = Sale.objects.filter(
                date_sold__gte=start_date,
                date_sold__lte=end_date
            )
            
            # Filtrar por productos si están especificados
            if forecast_model.products.exists():
                sales_query = sales_query.filter(product__in=forecast_model.products.all())
            elif forecast_model.categories.exists():
                sales_query = sales_query.filter(product__category__in=forecast_model.categories.all())
            else:
                # Si no hay filtros específicos, usar productos de la empresa
                sales_query = sales_query.filter(product__company=forecast_model.company)
            
            # Convertir a lista de diccionarios
            training_data = list(sales_query.values(
                'date_sold',
                'quantity',
                'product__name',
                'product_id'
            ))
            
            logger.info(f"Obtenidos {len(training_data)} registros de ventas para entrenamiento")
            return training_data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de entrenamiento: {e}")
            return []
    
    def _train_by_type(self, forecast_model: ForecastModel, data) -> Dict[str, Any]:
        """Entrenar según el tipo de modelo"""
        model_type = forecast_model.model_type.lower()
        
        # Obtener hiperparámetros
        hyperparams = forecast_model.hyperparameters or {}
        hyperparams['confidence_interval'] = float(forecast_model.confidence_interval)
        
        if model_type == 'prophet':
            return ml_service.train_prophet(data, **hyperparams)
        elif model_type == 'arima':
            return ml_service.train_arima(data, **hyperparams)
        elif model_type in ['random_forest', 'randomforest']:
            return ml_service.train_random_forest(data, **hyperparams)
        elif model_type == 'lstm':
            # LSTM no implementado completamente aún
            return {
                'success': False,
                'error': 'LSTM no está completamente implementado'
            }
        else:
            return {
                'success': False,
                'error': f'Tipo de modelo {model_type} no soportado'
            }
    
    def generate_predictions(self, forecast_model: ForecastModel, periods: int = None) -> Dict[str, Any]:
        """Generar predicciones con un modelo entrenado"""
        try:
            if forecast_model.status != 'active':
                return {
                    'success': False,
                    'error': 'Modelo no está activo o entrenado'
                }
            
            periods = periods or forecast_model.forecast_horizon_days
            model_type = forecast_model.model_type.lower()
            
            # Generar predicciones
            result = ml_service.predict(model_type, periods)
            
            if result['success']:
                # Guardar predicciones en la base de datos
                self._save_predictions(forecast_model, result['forecast'])
                
                logger.info(f"Generadas {len(result['forecast'])} predicciones para {forecast_model.name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando predicciones: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_predictions(self, forecast_model: ForecastModel, predictions: List[Dict]):
        """Guardar predicciones en la base de datos"""
        try:
            # Limpiar predicciones anteriores del mismo período
            DemandForecast.objects.filter(
                model=forecast_model,
                forecast_date__gte=timezone.now().date()
            ).delete()
            
            # Obtener productos para este modelo
            if forecast_model.products.exists():
                products = forecast_model.products.all()
            elif forecast_model.categories.exists():
                from inventory.models import Product
                products = Product.objects.filter(category__in=forecast_model.categories.all())
            else:
                from inventory.models import Product
                products = Product.objects.filter(company=forecast_model.company)[:1]  # Al menos un producto
            
            # Crear nuevas predicciones para cada producto
            forecasts_to_create = []
            for product in products:
                for pred in predictions:
                    forecast = DemandForecast(
                        model=forecast_model,
                        product=product,
                        forecast_date=pred['date'],
                        predicted_demand=pred['predicted_value'],
                        lower_bound=pred.get('lower_bound', pred['predicted_value'] * 0.8),
                        upper_bound=pred.get('upper_bound', pred['predicted_value'] * 1.2),
                        confidence_level=forecast_model.confidence_interval,
                        created_at=timezone.now()
                    )
                    forecasts_to_create.append(forecast)
            
            # Bulk create para eficiencia
            DemandForecast.objects.bulk_create(forecasts_to_create)
            
        except Exception as e:
            logger.error(f"Error guardando predicciones: {e}")


# Instancia global del servicio
training_service = ModelTrainingService()
