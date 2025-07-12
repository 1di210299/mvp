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
                # FIX: Location no tiene campo company, usar todas las ubicaciones activas
                target_locations = Location.objects.filter(is_active=True)
            else:
                target_locations = locations
            
            forecasts_created = 0
            
            with transaction.atomic():
                # FIX: Eliminar pronósticos existentes que puedan entrar en conflicto
                # No solo de este modelo, sino cualquier pronóstico para las mismas combinaciones
                start_date = predictions.index[0].date()
                end_date = predictions.index[-1].date()
                
                # Eliminar pronósticos existentes para evitar conflictos UNIQUE
                for product in target_products:
                    for location in target_locations:
                        DemandForecast.objects.filter(
                            product=product,
                            location=location,
                            forecast_date__range=(start_date, end_date),
                            forecast_type='ml_prediction'  # Solo eliminar pronósticos ML
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
                            
                            # Verificar si ya existe un pronóstico para esta combinación específica
                            existing_forecast = DemandForecast.objects.filter(
                                product=product,
                                location=location,
                                forecast_date=date.date(),
                                forecast_type='ml_prediction'
                            ).first()
                            
                            if existing_forecast:
                                # Actualizar pronóstico existente en lugar de crear nuevo
                                existing_forecast.model = forecast_model
                                existing_forecast.predicted_demand = Decimal(str(adjusted_demand))
                                existing_forecast.lower_bound = Decimal(str(adjusted_lower))
                                existing_forecast.upper_bound = Decimal(str(adjusted_upper))
                                existing_forecast.confidence_level = Decimal(str(confidence_interval * 100))
                                existing_forecast.seasonality_factor = Decimal(str(row.get('seasonality', 1.0)))
                                existing_forecast.trend_factor = Decimal(str(row.get('trend', 1.0)))
                                existing_forecast.external_factors = self._get_external_factors(product, date.date())
                                existing_forecast.save()
                            else:
                                # Crear el pronóstico nuevo
                                DemandForecast.objects.create(
                                    model=forecast_model,
                                    product=product,
                                    location=location,
                                    forecast_date=date.date(),
                                    predicted_demand=Decimal(str(adjusted_demand)),
                                    lower_bound=Decimal(str(adjusted_lower)),
                                    upper_bound=Decimal(str(adjusted_upper)),
                                    confidence_level=Decimal(str(confidence_interval * 100)),
                                    forecast_type='ml_prediction',
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
            print(f"🏢 Generando recomendaciones para empresa: {company.name}")
            
            # Determina productos a analizar
            if products is None:
                target_products = Product.objects.filter(company=company)
                print(f"📦 Productos de la empresa encontrados: {target_products.count()}")
            else:
                target_products = products
                print(f"📦 Productos específicos a procesar: {len(target_products)}")
            
            # FIX: Location no tiene campo company, usar todas las ubicaciones activas
            if locations is None:
                target_locations = Location.objects.filter(is_active=True)
                print(f"📍 Ubicaciones activas encontradas: {target_locations.count()}")
            else:
                target_locations = locations
                print(f"📍 Ubicaciones específicas a procesar: {len(target_locations)}")
            
            if not target_products.exists():
                print("❌ No hay productos para procesar")
                return []
                
            if not target_locations.exists():
                print("❌ No hay ubicaciones para procesar")
                return []
            
            recommendations = []
            
            for i, product in enumerate(target_products):
                print(f"📈 Procesando producto {i+1}/{target_products.count()}: {product.name}")
                
                for j, location in enumerate(target_locations):
                    try:
                        print(f"  📍 Ubicación {j+1}/{target_locations.count()}: {location.name}")
                        
                        # Obtiene stock actual
                        current_stock = self._get_current_stock(product, location)
                        print(f"  📊 Stock actual: {current_stock}")
                        
                        # Obtiene pronósticos futuros
                        future_demand = self._get_future_demand(
                            product=product,
                            location=location,
                            days_ahead=lead_time_days + safety_stock_days
                        )
                        print(f"  📈 Demanda futura: {future_demand}")
                        
                        if future_demand <= 0:
                            print(f"  ⚠️ Sin demanda futura para {product.name} en {location.name}")
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
                            print(f"  ✅ Recomendación creada para {product.name} en {location.name}")
                        else:
                            print(f"  ℹ️ No se requiere reorden para {product.name} en {location.name}")
                            
                    except Exception as e:
                        print(f"  ❌ Error procesando {product.sku} en {location.name}: {str(e)}")
                        logger.warning(f"Error procesando recomendación para {product.sku} en {location.name}: {str(e)}")
                        continue
            
            print(f"🎯 Recomendaciones generadas: {len(recommendations)} para empresa {company.name}")
            logger.info(f"Generadas {len(recommendations)} recomendaciones de reorden para empresa {company_id}")
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Error generando recomendaciones de reorden: {str(e)}")
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
        Obtiene la demanda proyectada futura con cálculo más realista
        """
        try:
            end_date = timezone.now().date() + timedelta(days=days_ahead)
            
            # Primero buscar pronósticos específicos para esta ubicación
            demand_specific = DemandForecast.objects.filter(
                product=product,
                location=location,
                forecast_date__range=(timezone.now().date() + timedelta(days=1), end_date)
            ).aggregate(total=models.Sum('predicted_demand'))['total']
            
            if demand_specific and demand_specific > 0:
                print(f"    📊 Demanda específica encontrada para {location.name}: {demand_specific}")
                return float(demand_specific)
            
            # Si no hay pronósticos específicos, buscar pronósticos generales (location=None)
            demand_general = DemandForecast.objects.filter(
                product=product,
                location__isnull=True,
                forecast_date__range=(timezone.now().date() + timedelta(days=1), end_date)
            ).aggregate(total=models.Sum('predicted_demand'))['total']
            
            if demand_general and demand_general > 0:
                print(f"    📊 Demanda general encontrada: {demand_general}")
                # Aplicar factor de ubicación a la demanda general
                location_factor = self._get_location_factor(product, location)
                adjusted_demand = float(demand_general) * location_factor
                print(f"    📊 Demanda ajustada para {location.name}: {adjusted_demand} (factor: {location_factor})")
                return adjusted_demand
            
            # Como último recurso, buscar cualquier pronóstico para este producto
            demand_any = DemandForecast.objects.filter(
                product=product,
                forecast_date__range=(timezone.now().date() + timedelta(days=1), end_date)
            ).aggregate(total=models.Sum('predicted_demand'))['total']
            
            if demand_any and demand_any > 0:
                print(f"    📊 Demanda cualquier ubicación encontrada: {demand_any}")
                # Dividir por número de ubicaciones activas como aproximación
                active_locations_count = Location.objects.filter(is_active=True).count()
                estimated_demand = float(demand_any) / max(active_locations_count, 1)
                print(f"    📊 Demanda estimada para {location.name}: {estimated_demand}")
                return estimated_demand
            
            print(f"    ⚠️ No se encontraron pronósticos para {product.name} en {location.name}")
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error obteniendo demanda futura: {str(e)}")
            print(f"    ❌ Error obteniendo demanda futura: {str(e)}")
            return 0.0
    
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
            # FIX: Convertir todo a float para evitar errores de tipos
            current_stock = float(current_stock)
            projected_demand = float(projected_demand)
            lead_time_days = int(lead_time_days)
            safety_stock_days = int(safety_stock_days)
            
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
                cost_price = float(product.cost_price or 0)
                estimated_cost = recommended_quantity * cost_price
                
                # Calcula ventas potenciales perdidas (usando sale_price del modelo Product)
                sale_price = float(product.sale_price or 0)
                potential_lost_sales = max(0, projected_demand - current_stock) * sale_price
                
                # Genera razón detallada
                justification = f"Stock actual ({current_stock:.1f}) por debajo del punto de reorden ({reorder_point:.1f}). " \
                               f"Demanda proyectada: {projected_demand:.1f} unidades en {lead_time_days + safety_stock_days} días. " \
                               f"Se requieren {recommended_quantity:.1f} unidades para mantener {safety_stock_days} días de stock de seguridad."
                
                # Crea la recomendación
                recommendation = ReorderRecommendation.objects.create(
                    product=product,
                    location=location,
                    recommended_quantity=Decimal(str(round(recommended_quantity, 2))),
                    current_stock=Decimal(str(round(current_stock, 2))),
                    projected_demand=Decimal(str(round(projected_demand, 2))),
                    recommended_order_date=recommended_order_date,
                    expected_stockout_date=expected_stockout_date,
                    lead_time_days=lead_time_days,
                    priority=priority,
                    estimated_cost=Decimal(str(round(estimated_cost, 2))),
                    potential_lost_sales=Decimal(str(round(potential_lost_sales, 2))),
                    justification=justification  # FIX: Usar 'justification' que es el campo correcto en el modelo
                )
                
                return recommendation
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculando recomendación de reorden: {str(e)}")
            return None
        
    def generate_forecasts(self, product, forecast_horizon=30, include_confidence=True):
        """
        Genera pronósticos usando el sistema ML robusto implementado
        """
        try:
            from datetime import datetime, timedelta
            from decimal import Decimal
            from django.utils import timezone
            
            print(f"📈 Generando pronósticos ML para {product.name}")
            
            # 1. Obtener o crear modelo ML entrenado para este producto
            forecast_model = self._get_or_create_model_for_product(product)
            
            if not forecast_model:
                print(f"  ❌ No se pudo obtener modelo para {product.name}")
                return []
            
            print(f"  🤖 Usando modelo: {forecast_model.name} ({forecast_model.model_type})")
            
            # 2. Cargar el modelo ML entrenado
            try:
                ml_model = self.ml_service.load_trained_model(forecast_model.id)
                print(f"  ✅ Modelo ML cargado exitosamente")
            except Exception as e:
                print(f"  ⚠️ Error cargando modelo, entrenando nuevo: {str(e)}")
                # Si no se puede cargar, entrenar un nuevo modelo
                forecast_model = self._retrain_model_for_product(product)
                if not forecast_model:
                    print(f"  ❌ No se pudo entrenar modelo para {product.name}")
                    return self._generate_base_forecasts(product, forecast_horizon, include_confidence)
                ml_model = self.ml_service.load_trained_model(forecast_model.id)
            
            # 3. Generar predicciones usando el modelo ML
            try:
                # Obtener datos recientes para contexto
                training_data = self._get_training_data_for_product(product)
                print(f"  📊 Datos de entrenamiento: {len(training_data)} observaciones")
                
                if training_data.empty:
                    print(f"  ⚠️ Sin datos históricos, usando predicciones base")
                    return self._generate_base_forecasts(product, forecast_horizon, include_confidence)
                
                # Generar predicciones ML
                predictions = ml_model.predict(periods=forecast_horizon)
                print(f"  🎯 Predicciones ML generadas: {len(predictions)} períodos")
                
            except Exception as e:
                print(f"  ❌ Error generando pronósticos ML para {product.name}: {str(e)}")
                logger.error(f"Error generando pronósticos ML para {product.sku}: {str(e)}")
                # Fallback a predicciones base
                return self._generate_base_forecasts(product, forecast_horizon, include_confidence)
            
            # 4. Crear registros de DemandForecast usando get_or_create para evitar duplicados
            forecasts_created = []
            locations = Location.objects.filter(is_active=True)
            
            for location in locations:
                print(f"    📍 Creando pronósticos para {location.name}")
                
                for i, (date_idx, row) in enumerate(predictions.iterrows()):
                    forecast_date = timezone.now().date() + timedelta(days=i+1)
                    
                    # Extraer valores de la predicción ML
                    predicted_demand = max(0, float(row.get('predicted_demand', row.get('yhat', 0))))
                    
                    if include_confidence:
                        lower_bound = max(0, float(row.get('lower_bound', row.get('yhat_lower', predicted_demand * 0.7))))
                        upper_bound = float(row.get('upper_bound', row.get('yhat_upper', predicted_demand * 1.3)))
                    else:
                        lower_bound = predicted_demand * 0.8
                        upper_bound = predicted_demand * 1.2
                    
                    # Ajustar predicción según ubicación específica
                    location_factor = self._get_location_factor(product, location)
                    adjusted_demand = predicted_demand * location_factor
                    adjusted_lower = lower_bound * location_factor
                    adjusted_upper = upper_bound * location_factor
                    
                    # FIX: Usar get_or_create para evitar error UNIQUE constraint
                    forecast, created = DemandForecast.objects.get_or_create(
                        product=product,
                        location=location,
                        forecast_date=forecast_date,
                        forecast_type='ml_prediction',
                        defaults={
                            'model': forecast_model,
                            'predicted_demand': Decimal(str(round(adjusted_demand, 2))),
                            'lower_bound': Decimal(str(round(adjusted_lower, 2))),
                            'upper_bound': Decimal(str(round(adjusted_upper, 2))),
                            'confidence_level': Decimal('85.0'),
                            'seasonality_factor': Decimal(str(round(row.get('seasonality', 1.0), 2))),
                            'trend_factor': Decimal(str(round(row.get('trend', 1.0), 2))),
                            'external_factors': {
                                'algorithm': forecast_model.model_type,
                                'model_metrics': {
                                    'mae': float(forecast_model.mae or 0),
                                    'mape': float(forecast_model.mape or 0),
                                    'rmse': float(forecast_model.rmse or 0)
                                },
                                'location_factor': location_factor
                            }
                        }
                    )
                    
                    if not created:
                        # Si ya existe, actualizarlo con nuevos valores
                        forecast.model = forecast_model
                        forecast.predicted_demand = Decimal(str(round(adjusted_demand, 2)))
                        forecast.lower_bound = Decimal(str(round(adjusted_lower, 2)))
                        forecast.upper_bound = Decimal(str(round(adjusted_upper, 2)))
                        forecast.confidence_level = Decimal('85.0')
                        forecast.save()
                        print(f"      🔄 Pronóstico actualizado para {forecast_date}")
                    else:
                        print(f"      ✅ Pronóstico creado para {forecast_date}")
                    
                    forecasts_created.append(forecast)
            
            # Actualizar timestamp de última predicción
            forecast_model.last_prediction_at = timezone.now()
            forecast_model.save()
            
            print(f"  ✅ {len(forecasts_created)} pronósticos ML procesados para {product.name}")
            return forecasts_created
            
        except Exception as e:
            print(f"  ❌ Error generando pronósticos ML para {product.name}: {str(e)}")
            logger.error(f"Error generando pronósticos ML para {product.sku}: {str(e)}")
            # Fallback a predicciones base
            return self._generate_base_forecasts(product, forecast_horizon, include_confidence)
    
    def _get_or_create_model_for_product(self, product):
        """
        Obtiene o crea un modelo ML para el producto usando MLModelService
        """
        try:
            # Buscar modelo existente activo
            existing_model = ForecastModel.objects.filter(
                company=product.company,
                status='active',
                products=product
            ).first()
            
            if existing_model:
                print(f"    📋 Usando modelo existente: {existing_model.name}")
                return existing_model
            
            # Buscar modelo general de la empresa
            company_model = ForecastModel.objects.filter(
                company=product.company,
                status='active'
            ).first()
            
            if company_model:
                print(f"    📋 Usando modelo de empresa: {company_model.name}")
                # Asociar producto al modelo existente
                company_model.products.add(product)
                return company_model
            
            # Crear nuevo modelo específico para el producto usando MLModelService
            print(f"    🔧 Creando nuevo modelo ML para {product.name}")
            return self.ml_service.train_model_for_product(
                product=product,
                algorithm='prophet',  # Usar Prophet como default
                retrain_existing=False
            )
            
        except Exception as e:
            print(f"    ❌ Error obteniendo/creando modelo: {str(e)}")
            return None
    
    def _retrain_model_for_product(self, product):
        """
        Re-entrena un modelo existente para el producto
        """
        try:
            existing_model = ForecastModel.objects.filter(
                company=product.company,
                products=product
            ).first()
            
            if existing_model:
                print(f"    🔄 Re-entrenando modelo existente: {existing_model.name}")
                return self.ml_service.retrain_model(existing_model.id)
            else:
                print(f"    🔧 Creando nuevo modelo (no existe previo)")
                return self.ml_service.train_model_for_product(
                    product=product,
                    algorithm='prophet',
                    retrain_existing=False
                )
                
        except Exception as e:
            print(f"    ❌ Error re-entrenando modelo: {str(e)}")
            return None
    
    def _get_training_data_for_product(self, product, days_back=180):
        """
        Obtiene datos históricos para entrenar/predecir
        """
        try:
            from django.db import models
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Obtener transacciones agregadas por día
            transactions = Transaction.objects.filter(
                product=product,
                transaction_date__gte=start_date,
                transaction_type__in=['sale', 'usage']
            ).extra(
                select={'date': 'DATE(transaction_date)'}
            ).values('date').annotate(
                total_quantity=models.Sum('quantity')
            ).order_by('date')
            
            if not transactions.exists():
                return pd.DataFrame()
            
            # Convertir a DataFrame
            df = pd.DataFrame(list(transactions))
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df['quantity'] = df['total_quantity'].abs()  # Asegurar valores positivos
            
            # Rellenar fechas faltantes con 0
            full_date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            df = df.reindex(full_date_range, fill_value=0)
            
            return df[['quantity']]
            
        except Exception as e:
            print(f"    ❌ Error obteniendo datos de entrenamiento: {str(e)}")
            return pd.DataFrame()
    
    def _generate_base_forecasts(self, product, forecast_horizon, include_confidence):
        """
        Genera pronósticos base cuando ML no está disponible
        """
        try:
            print(f"    📊 Generando pronósticos base para {product.name}")
            
            # Usar datos históricos simples
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=90)
            
            avg_daily_demand = Transaction.objects.filter(
                product=product,
                transaction_date__range=(start_date, end_date),
                transaction_type__in=['sale', 'usage']
            ).aggregate(
                avg=models.Avg('quantity')
            )['avg'] or 5.0
            
            avg_daily_demand = abs(float(avg_daily_demand))
            
            forecasts_created = []
            locations = Location.objects.filter(is_active=True)
            
            # Obtener modelo base o crear uno temporal
            base_model = ForecastModel.objects.filter(
                company=product.company,
                status='active'
            ).first()
            
            for location in locations:
                current_stock = self._get_current_stock(product, location)
                if current_stock == 0:
                    continue
                
                for days_ahead in range(1, forecast_horizon + 1):
                    forecast_date = end_date + timedelta(days=days_ahead)
                    
                    # Demanda base con variación estacional
                    base_demand = avg_daily_demand
                    
                    # Factor de día de semana
                    if forecast_date.weekday() >= 5:  # Fin de semana
                        base_demand *= 0.7
                    
                    # Factor de ubicación
                    location_factor = self._get_location_factor(product, location)
                    predicted_demand = base_demand * location_factor
                    
                    if include_confidence:
                        lower_bound = predicted_demand * 0.7
                        upper_bound = predicted_demand * 1.3
                    else:
                        lower_bound = predicted_demand * 0.8
                        upper_bound = predicted_demand * 1.2
                    
                    forecast = DemandForecast.objects.create(
                        model=base_model,
                        product=product,
                        location=location,
                        forecast_date=forecast_date,
                        predicted_demand=Decimal(str(round(predicted_demand, 2))),
                        lower_bound=Decimal(str(round(lower_bound, 2))),
                        upper_bound=Decimal(str(round(upper_bound, 2))),
                        confidence_level=Decimal('70.0'),
                        forecast_type='base_statistical',
                        seasonality_factor=Decimal('0.7' if forecast_date.weekday() >= 5 else '1.0'),
                        trend_factor=Decimal('1.0'),
                        external_factors={
                            'method': 'historical_average',
                            'data_points': 90,
                            'location_factor': location_factor
                        }
                    )
                    forecasts_created.append(forecast)
            
            return forecasts_created
            
        except Exception as e:
            print(f"    ❌ Error generando pronósticos base: {str(e)}")
            return []
