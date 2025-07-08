"""
Servicio para generación y gestión de pronósticos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.db import transaction, models

from ..models import ForecastModel, DemandForecast, ReorderRecommendation
from ..services.ml_model_service import MLModelService
from inventory.models import Product, Location, Transaction
from authentication.models import Company

logger = logging.getLogger(__name__)


class ForecastService:
    """
    Servicio para generación y gestión de pronósticos de demanda
    """
    
    def __init__(self):
        """
        Inicializa el servicio de pronósticos
        """
        self.ml_service = MLModelService()
    
    def generate_forecasts_for_model(self,
                                   model_id: int,
                                   periods: int = 30,
                                   products: Optional[List[Product]] = None,
                                   locations: Optional[List[Location]] = None,
                                   confidence_interval: Optional[float] = None) -> Dict[str, Any]:
        """
        Genera pronósticos para un modelo específico
        
        Args:
            model_id: ID del modelo a usar
            periods: Número de períodos a pronosticar
            products: Lista de productos (si None, usa los del modelo)
            locations: Lista de ubicaciones
            confidence_interval: Nivel de confianza (si None, usa el del modelo)
            
        Returns:
            Diccionario con resultados de la generación
        """
        try:
            forecast_model = ForecastModel.objects.get(id=model_id)
            
            if forecast_model.status != 'active':
                raise ValueError(f"El modelo {model_id} no está activo")
            
            logger.info(f"Generando pronósticos para modelo {model_id}")
            
            # Carga el modelo ML
            ml_model = self.ml_service.load_trained_model(model_id)
            
            # Determina nivel de confianza
            if confidence_interval is None:
                confidence_interval = float(forecast_model.confidence_interval) / 100
            
            # Genera predicciones
            predictions = ml_model.predict(
                periods=periods,
                confidence_interval=confidence_interval
            )
            
            # Determina productos objetivo
            if products is None:
                target_products = forecast_model.products.all()
                if not target_products:
                    target_products = Product.objects.filter(company=forecast_model.company)
            else:
                target_products = products
            
            # Determina ubicaciones objetivo
            if locations is None:
                target_locations = Location.objects.filter(company=forecast_model.company)
            else:
                target_locations = locations
            
            forecasts_created = 0
            
            with transaction.atomic():
                # Elimina pronósticos existentes para el período
                start_date = predictions.index[0].date()
                end_date = predictions.index[-1].date()
                
                DemandForecast.objects.filter(
                    model=forecast_model,
                    product__in=target_products,
                    forecast_date__range=(start_date, end_date)
                ).delete()
                
                # Crea nuevos pronósticos
                for product in target_products:
                    for location in target_locations:
                        for date, row in predictions.iterrows():
                            # Ajusta la predicción según características del producto
                            adjusted_demand = self._adjust_prediction_for_product(
                                base_prediction=row['predicted_demand'],
                                product=product,
                                location=location,
                                forecast_date=date.date()
                            )
                            
                            # Calcula límites ajustados
                            adjustment_factor = adjusted_demand / row['predicted_demand'] if row['predicted_demand'] > 0 else 1
                            adjusted_lower = max(0, row['lower_bound'] * adjustment_factor)
                            adjusted_upper = row['upper_bound'] * adjustment_factor
                            
                            # Crea el pronóstico
                            DemandForecast.objects.create(
                                model=forecast_model,
                                product=product,
                                location=location,
                                forecast_date=date.date(),
                                predicted_demand=Decimal(str(adjusted_demand)),
                                lower_bound=Decimal(str(adjusted_lower)),
                                upper_bound=Decimal(str(adjusted_upper)),
                                confidence_level=Decimal(str(confidence_interval * 100)),
                                seasonality_factor=Decimal(str(row.get('seasonality', 1.0))),
                                trend_factor=Decimal(str(row.get('trend', 1.0))),
                                external_factors=self._get_external_factors(product, date.date())
                            )
                            forecasts_created += 1
            
            # Actualiza timestamp de última predicción
            forecast_model.last_prediction_at = timezone.now()
            forecast_model.save()
            
            logger.info(f"Generados {forecasts_created} pronósticos para modelo {model_id}")
            
            return {
                'model_id': model_id,
                'forecasts_created': forecasts_created,
                'periods': periods,
                'products_count': len(target_products),
                'locations_count': len(target_locations),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generando pronósticos para modelo {model_id}: {str(e)}")
            raise
    
    def get_forecasts_for_product(self,
                                product_id: int,
                                days_ahead: int = 30,
                                location_id: Optional[int] = None,
                                model_type: Optional[str] = None) -> pd.DataFrame:
        """
        Obtiene pronósticos para un producto específico
        
        Args:
            product_id: ID del producto
            days_ahead: Días hacia adelante a obtener
            location_id: ID de ubicación específica
            model_type: Tipo de modelo específico
            
        Returns:
            DataFrame con pronósticos
        """
        try:
            product = Product.objects.get(id=product_id)
            
            # Construye filtros
            filters = {
                'product': product,
                'forecast_date__gte': timezone.now().date(),
                'forecast_date__lte': timezone.now().date() + timedelta(days=days_ahead)
            }
            
            if location_id:
                filters['location_id'] = location_id
            
            if model_type:
                filters['model__model_type'] = model_type
            
            # Obtiene pronósticos
            forecasts = DemandForecast.objects.filter(**filters).select_related('model', 'location').order_by('forecast_date', 'model__created_at')
            
            if not forecasts.exists():
                return pd.DataFrame()
            
            # Convierte a DataFrame
            data = []
            for forecast in forecasts:
                data.append({
                    'date': forecast.forecast_date,
                    'predicted_demand': float(forecast.predicted_demand),
                    'lower_bound': float(forecast.lower_bound),
                    'upper_bound': float(forecast.upper_bound),
                    'confidence_level': float(forecast.confidence_level),
                    'model_name': forecast.model.name,
                    'model_type': forecast.model.model_type,
                    'location': forecast.location.name if forecast.location else 'General',
                    'seasonality_factor': float(forecast.seasonality_factor or 1.0),
                    'trend_factor': float(forecast.trend_factor or 1.0)
                })
            
            df = pd.DataFrame(data)
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo pronósticos para producto {product_id}: {str(e)}")
            raise
    
    def get_aggregated_forecasts(self,
                               company_id: int,
                               aggregation_level: str = 'daily',
                               days_ahead: int = 30,
                               category_ids: Optional[List[int]] = None,
                               location_ids: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Obtiene pronósticos agregados para una empresa
        
        Args:
            company_id: ID de la empresa
            aggregation_level: Nivel de agregación ('daily', 'weekly', 'monthly')
            days_ahead: Días hacia adelante
            category_ids: IDs de categorías específicas
            location_ids: IDs de ubicaciones específicas
            
        Returns:
            DataFrame con pronósticos agregados
        """
        try:
            # Construye filtros
            filters = {
                'model__company_id': company_id,
                'forecast_date__gte': timezone.now().date(),
                'forecast_date__lte': timezone.now().date() + timedelta(days=days_ahead)
            }
            
            if category_ids:
                filters['product__category_id__in'] = category_ids
            
            if location_ids:
                filters['location_id__in'] = location_ids
            
            # Obtiene pronósticos
            forecasts = DemandForecast.objects.filter(**filters).values(
                'forecast_date',
                'product__category__name'
            ).annotate(
                total_predicted_demand=models.Sum('predicted_demand'),
                total_lower_bound=models.Sum('lower_bound'),
                total_upper_bound=models.Sum('upper_bound'),
                avg_confidence_level=models.Avg('confidence_level'),
                products_count=models.Count('product', distinct=True)
            ).order_by('forecast_date')
            
            if not forecasts:
                return pd.DataFrame()
            
            # Convierte a DataFrame
            df = pd.DataFrame(list(forecasts))
            df['forecast_date'] = pd.to_datetime(df['forecast_date'])
            
            # Aplica agregación temporal
            df = df.set_index('forecast_date')
            
            if aggregation_level == 'weekly':
                df = df.groupby([pd.Grouper(freq='W'), 'product__category__name']).agg({
                    'total_predicted_demand': 'sum',
                    'total_lower_bound': 'sum',
                    'total_upper_bound': 'sum',
                    'avg_confidence_level': 'mean',
                    'products_count': 'max'
                }).reset_index()
            elif aggregation_level == 'monthly':
                df = df.groupby([pd.Grouper(freq='M'), 'product__category__name']).agg({
                    'total_predicted_demand': 'sum',
                    'total_lower_bound': 'sum',
                    'total_upper_bound': 'sum',
                    'avg_confidence_level': 'mean',
                    'products_count': 'max'
                }).reset_index()
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo pronósticos agregados para empresa {company_id}: {str(e)}")
            raise
    
    def generate_reorder_recommendations(self,
                                       company_id: int,
                                       products: Optional[List[Product]] = None,
                                       locations: Optional[List[Location]] = None,
                                       lead_time_days: int = 7,
                                       safety_stock_days: int = 3) -> List[ReorderRecommendation]:
        """
        Genera recomendaciones de reorden basadas en pronósticos
        
        Args:
            company_id: ID de la empresa
            products: Productos específicos a analizar
            locations: Ubicaciones específicas
            lead_time_days: Días de tiempo de entrega
            safety_stock_days: Días de stock de seguridad
            
        Returns:
            Lista de recomendaciones creadas
        """
        try:
            company = Company.objects.get(id=company_id)
            
            # Determina productos a analizar
            if products is None:
                target_products = Product.objects.filter(company=company)
            else:
                target_products = products
            
            # Determina ubicaciones
            if locations is None:
                target_locations = Location.objects.filter(company=company)
            else:
                target_locations = locations
            
            recommendations = []
            
            for product in target_products:
                for location in target_locations:
                    try:
                        # Obtiene stock actual
                        current_stock = self._get_current_stock(product, location)
                        
                        # Obtiene pronósticos futuros
                        future_demand = self._get_future_demand(
                            product=product,
                            location=location,
                            days_ahead=lead_time_days + safety_stock_days
                        )
                        
                        if future_demand <= 0:
                            continue
                        
                        # Calcula recomendación
                        recommendation = self._calculate_reorder_recommendation(
                            product=product,
                            location=location,
                            current_stock=current_stock,
                            projected_demand=future_demand,
                            lead_time_days=lead_time_days,
                            safety_stock_days=safety_stock_days
                        )
                        
                        if recommendation:
                            recommendations.append(recommendation)
                            
                    except Exception as e:
                        logger.warning(f"Error procesando recomendación para {product.sku} en {location.name}: {str(e)}")
                        continue
            
            logger.info(f"Generadas {len(recommendations)} recomendaciones de reorden para empresa {company_id}")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones de reorden: {str(e)}")
            raise
    
    def _adjust_prediction_for_product(self,
                                     base_prediction: float,
                                     product: Product,
                                     location: Location,
                                     forecast_date: datetime.date) -> float:
        """
        Ajusta la predicción base según características específicas del producto
        """
        try:
            adjusted_prediction = base_prediction
            
            # Factor de ubicación (si hay datos históricos específicos)
            location_factor = self._get_location_factor(product, location)
            adjusted_prediction *= location_factor
            
            # Factor estacional específico del producto
            seasonal_factor = self._get_product_seasonal_factor(product, forecast_date)
            adjusted_prediction *= seasonal_factor
            
            # Factor de tendencia del producto
            trend_factor = self._get_product_trend_factor(product)
            adjusted_prediction *= trend_factor
            
            # Asegura que no sea negativo
            return max(0, adjusted_prediction)
            
        except Exception as e:
            logger.warning(f"Error ajustando predicción para {product.sku}: {str(e)}")
            return base_prediction
    
    def _get_location_factor(self, product: Product, location: Location) -> float:
        """
        Calcula factor de ajuste por ubicación
        """
        try:
            # Obtiene ventas promedio por ubicación en los últimos 3 meses
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=90)
            
            location_sales = Transaction.objects.filter(
                product=product,
                location=location,
                transaction_date__range=(start_date, end_date),
                transaction_type__in=['sale', 'usage']
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            total_sales = Transaction.objects.filter(
                product=product,
                transaction_date__range=(start_date, end_date),
                transaction_type__in=['sale', 'usage']
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            if total_sales > 0:
                return location_sales / total_sales
            else:
                return 1.0
                
        except Exception:
            return 1.0
    
    def _get_product_seasonal_factor(self, product: Product, forecast_date: datetime.date) -> float:
        """
        Calcula factor estacional específico del producto
        """
        try:
            # Análisis estacional simple basado en el mes
            month = forecast_date.month
            
            # Obtiene ventas del mismo mes en años anteriores
            historical_sales = Transaction.objects.filter(
                product=product,
                transaction_date__month=month,
                transaction_date__year__lt=forecast_date.year,
                transaction_type__in=['sale', 'usage']
            ).aggregate(avg=models.Avg('quantity'))['avg'] or 0
            
            # Obtiene promedio general
            general_avg = Transaction.objects.filter(
                product=product,
                transaction_date__year__lt=forecast_date.year,
                transaction_type__in=['sale', 'usage']
            ).aggregate(avg=models.Avg('quantity'))['avg'] or 0
            
            if general_avg > 0:
                return historical_sales / general_avg
            else:
                return 1.0
                
        except Exception:
            return 1.0
    
    def _get_product_trend_factor(self, product: Product) -> float:
        """
        Calcula factor de tendencia del producto
        """
        try:
            # Compara últimos 3 meses vs 3 meses anteriores
            end_date = timezone.now().date()
            recent_start = end_date - timedelta(days=90)
            old_start = recent_start - timedelta(days=90)
            old_end = recent_start
            
            recent_sales = Transaction.objects.filter(
                product=product,
                transaction_date__range=(recent_start, end_date),
                transaction_type__in=['sale', 'usage']
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            old_sales = Transaction.objects.filter(
                product=product,
                transaction_date__range=(old_start, old_end),
                transaction_type__in=['sale', 'usage']
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            if old_sales > 0:
                trend = recent_sales / old_sales
                # Limita el factor de tendencia a un rango razonable
                return max(0.5, min(2.0, trend))
            else:
                return 1.0
                
        except Exception:
            return 1.0
    
    def _get_external_factors(self, product: Product, forecast_date: datetime.date) -> Dict[str, Any]:
        """
        Obtiene factores externos que pueden afectar la demanda
        """
        factors = {}
        
        try:
            # Factor de día de la semana
            factors['day_of_week'] = forecast_date.weekday()
            
            # Factor de temporada
            month = forecast_date.month
            if month in [12, 1, 2]:
                factors['season'] = 'winter'
            elif month in [3, 4, 5]:
                factors['season'] = 'spring'
            elif month in [6, 7, 8]:
                factors['season'] = 'summer'
            else:
                factors['season'] = 'fall'
            
            # Factor de fin de mes
            factors['end_of_month'] = forecast_date.day > 25
            
        except Exception as e:
            logger.warning(f"Error obteniendo factores externos: {str(e)}")
        
        return factors
    
    def _get_current_stock(self, product: Product, location: Location) -> float:
        """
        Obtiene el stock actual de un producto en una ubicación
        """
        try:
            # Suma todas las transacciones para obtener stock actual
            stock = Transaction.objects.filter(
                product=product,
                location=location
            ).aggregate(
                inbound=models.Sum('quantity', filter=models.Q(transaction_type__in=['purchase', 'adjustment_in', 'return'])),
                outbound=models.Sum('quantity', filter=models.Q(transaction_type__in=['sale', 'usage', 'adjustment_out']))
            )
            
            inbound = stock['inbound'] or 0
            outbound = stock['outbound'] or 0
            
            return max(0, inbound - outbound)
            
        except Exception as e:
            logger.warning(f"Error obteniendo stock actual: {str(e)}")
            return 0
    
    def _get_future_demand(self, product: Product, location: Location, days_ahead: int) -> float:
        """
        Obtiene la demanda proyectada futura
        """
        try:
            end_date = timezone.now().date() + timedelta(days=days_ahead)
            
            demand = DemandForecast.objects.filter(
                product=product,
                location=location,
                forecast_date__range=(timezone.now().date(), end_date)
            ).aggregate(total=models.Sum('predicted_demand'))['total'] or 0
            
            return float(demand)
            
        except Exception as e:
            logger.warning(f"Error obteniendo demanda futura: {str(e)}")
            return 0
    
    def _calculate_reorder_recommendation(self,
                                        product: Product,
                                        location: Location,
                                        current_stock: float,
                                        projected_demand: float,
                                        lead_time_days: int,
                                        safety_stock_days: int) -> Optional[ReorderRecommendation]:
        """
        Calcula recomendación de reorden específica
        """
        try:
            # Calcula stock de seguridad
            daily_demand = projected_demand / (lead_time_days + safety_stock_days)
            safety_stock = daily_demand * safety_stock_days
            
            # Calcula punto de reorden
            reorder_point = (daily_demand * lead_time_days) + safety_stock
            
            # Verifica si necesita reorden
            if current_stock <= reorder_point:
                # Calcula cantidad recomendada
                # Usa EOQ simplificado o cantidad para cubrir demanda + seguridad
                recommended_quantity = max(
                    projected_demand + safety_stock - current_stock,
                    daily_demand * 30  # Mínimo para 30 días
                )
                
                # Calcula fechas
                days_until_stockout = int(current_stock / daily_demand) if daily_demand > 0 else 999
                expected_stockout_date = timezone.now().date() + timedelta(days=days_until_stockout)
                recommended_order_date = timezone.now().date()
                
                # Determina prioridad
                if days_until_stockout <= lead_time_days:
                    priority = 'urgent'
                elif days_until_stockout <= lead_time_days + 3:
                    priority = 'high'
                elif days_until_stockout <= lead_time_days + 7:
                    priority = 'medium'
                else:
                    priority = 'low'
                
                # Calcula costo estimado (usando cost_price del modelo Product)
                estimated_cost = recommended_quantity * float(product.cost_price or 0)
                
                # Calcula ventas potenciales perdidas (usando sale_price del modelo Product)
                potential_lost_sales = max(0, projected_demand - current_stock) * float(product.sale_price or 0)
                
                # Crea la recomendación
                recommendation = ReorderRecommendation.objects.create(
                    product=product,
                    location=location,
                    recommended_quantity=Decimal(str(recommended_quantity)),
                    current_stock=Decimal(str(current_stock)),
                    projected_demand=Decimal(str(projected_demand)),
                    recommended_order_date=recommended_order_date,
                    expected_stockout_date=expected_stockout_date,
                    lead_time_days=lead_time_days,
                    priority=priority,
                    estimated_cost=Decimal(str(estimated_cost)),
                    potential_lost_sales=Decimal(str(potential_lost_sales)),
                    justification=f"Stock actual ({current_stock:.1f}) por debajo del punto de reorden ({reorder_point:.1f})"
                )
                
                return recommendation
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculando recomendación de reorden: {str(e)}")
            return None
