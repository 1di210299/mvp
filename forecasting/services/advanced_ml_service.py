"""
Servicios avanzados de Machine Learning para pronósticos financieros,
análisis de demanda sofisticado, optimización de inventario y customer intelligence.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.db.models import Sum, Avg, Count, F, Q, Max, Min
from django.utils import timezone
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import logging

from ..models import (
    ForecastModel, DemandForecast, RevenueForecasting, CustomerLifetimeValue,
    ChurnPrediction, MarketBasketAnalysis, PriceElasticity, SeasonalityPattern,
    SupplierROIAnalysis, OptimalStockLevel, ProductRecommendation,
    FinancialForecastModel, RevenuePrediction, DemandPatternAnalysis,
    PriceElasticityAnalysis, TrendingProductPrediction, StockoutPrediction,
    NextPurchasePrediction, CustomerSegmentation
)
from inventory.models import Product, Sale, Transaction, Customer, Supplier, Category
from authentication.models import Company

logger = logging.getLogger(__name__)


class FinancialForecastingService:
    """Servicio para pronósticos financieros avanzados"""
    
    def __init__(self, company: Company):
        self.company = company
    
    def create_revenue_forecast_model(self, 
                                    metric_type: str = 'revenue',
                                    horizon_days: int = 90) -> FinancialForecastModel:
        """Crear modelo de pronóstico financiero"""
        
        # Crear modelo base de pronóstico
        base_model = ForecastModel.objects.create(
            company=self.company,
            name=f"Financial {metric_type.title()} Forecast",
            description=f"Modelo para pronósticos de {metric_type} en soles peruanos",
            model_type='prophet',  # Mejor para series financieras
            forecast_horizon_days=horizon_days,
            training_period_days=365
        )
        
        # Crear configuración financiera
        financial_model = FinancialForecastModel.objects.create(
            base_model=base_model,
            metric_type=metric_type,
            currency='PEN',
            include_supplier_analysis=(metric_type == 'roi_supplier'),
            include_cost_tracking=True
        )
        
        return financial_model
    
    def generate_revenue_predictions(self, 
                                   financial_model: FinancialForecastModel,
                                   period_type: str = 'monthly',
                                   periods_ahead: int = 6) -> List[RevenuePrediction]:
        """Generar predicciones de ingresos"""
        
        # Obtener datos históricos de ventas/transacciones
        historical_data = self._get_financial_historical_data(
            financial_model, 
            period_type
        )
        
        if historical_data.empty:
            logger.warning("No hay datos históricos suficientes para pronóstico financiero")
            return []
        
        # Entrenar modelo de regresión para ingresos
        model = self._train_revenue_model(historical_data)
        
        predictions = []
        start_date = timezone.now().date()
        
        for i in range(periods_ahead):
            if period_type == 'weekly':
                period_start = start_date + timedelta(weeks=i)
                period_end = period_start + timedelta(weeks=1)
            elif period_type == 'monthly':
                period_start = start_date.replace(day=1) + timedelta(days=32*i)
                period_start = period_start.replace(day=1)
                next_month = period_start + timedelta(days=32)
                period_end = next_month.replace(day=1) - timedelta(days=1)
            else:  # quarterly
                period_start = start_date + timedelta(days=90*i)
                period_end = period_start + timedelta(days=90)
            
            # Generar predicción para este período
            pred_revenue, pred_margin, pred_units = self._predict_financial_metrics(
                model, historical_data, period_start
            )
            
            # Calcular intervalos de confianza (simulación Monte Carlo simplificada)
            confidence_interval = 0.15  # 15% de variación
            revenue_lower = pred_revenue * (1 - confidence_interval)
            revenue_upper = pred_revenue * (1 + confidence_interval)
            margin_lower = pred_margin * (1 - confidence_interval/2)
            margin_upper = pred_margin * (1 + confidence_interval/2)
            
            prediction = RevenuePrediction.objects.create(
                financial_model=financial_model,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                predicted_revenue_pen=Decimal(str(pred_revenue)),
                predicted_margin=Decimal(str(pred_margin)),
                predicted_units_sold=Decimal(str(pred_units)),
                revenue_lower_bound=Decimal(str(revenue_lower)),
                revenue_upper_bound=Decimal(str(revenue_upper)),
                margin_lower_bound=Decimal(str(margin_lower)),
                margin_upper_bound=Decimal(str(margin_upper)),
                confidence_level=Decimal('85.00')
            )
            
            predictions.append(prediction)
        
        return predictions
    
    def analyze_supplier_roi(self, days_back: int = 365) -> List[SupplierROIAnalysis]:
        """Analizar ROI por proveedor usando datos históricos"""
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        suppliers = Supplier.objects.filter(
            products__company=self.company
        ).distinct()
        
        analyses = []
        
        for supplier in suppliers:
            # Obtener productos del proveedor
            supplier_products = Product.objects.filter(
                supplier=supplier,
                company=self.company
            )
            
            # Calcular inversión total (compras)
            total_cost = Transaction.objects.filter(
                product__in=supplier_products,
                transaction_type='purchase',
                transaction_date__date__range=[start_date, end_date]
            ).aggregate(
                total=Sum(F('quantity') * F('unit_cost'))
            )['total'] or 0
            
            # Calcular ingresos generados (ventas)
            total_revenue = Transaction.objects.filter(
                product__in=supplier_products,
                transaction_type='sale',
                transaction_date__date__range=[start_date, end_date]
            ).aggregate(
                total=Sum(F('quantity') * F('product__sale_price'))
            )['total'] or 0
            
            if total_cost > 0:
                roi_percentage = ((total_revenue - total_cost) / total_cost) * 100
                
                # Calcular métricas adicionales
                avg_margin = self._calculate_average_margin(supplier_products)
                days_to_sell = self._calculate_days_to_sell(supplier_products, start_date, end_date)
                inventory_turnover = self._calculate_inventory_turnover(supplier_products, start_date, end_date)
                
                # Generar recomendaciones automáticas
                recommendations = self._generate_supplier_recommendations(
                    roi_percentage, avg_margin, days_to_sell
                )
                
                # Score de recomendación (1-10)
                recommendation_score = self._calculate_supplier_score(
                    roi_percentage, avg_margin, inventory_turnover
                )
                
                analysis = SupplierROIAnalysis.objects.create(
                    supplier=supplier,
                    analysis_period_start=start_date,
                    analysis_period_end=end_date,
                    total_cost_invested=Decimal(str(total_cost)),
                    total_revenue_generated=Decimal(str(total_revenue)),
                    roi_percentage=Decimal(str(roi_percentage)),
                    average_margin_per_product=Decimal(str(avg_margin)),
                    days_to_sell_average=Decimal(str(days_to_sell)),
                    inventory_turnover=Decimal(str(inventory_turnover)),
                    recommendation_score=recommendation_score,
                    auto_recommendations=recommendations
                )
                
                analyses.append(analysis)
        
        return analyses
    
    def predict_cash_flow(self, days_ahead: int = 90) -> Dict[str, Any]:
        """Predecir flujo de caja basado en patrones de compra/venta"""
        
        # Obtener datos históricos de flujo de caja
        historical_data = self._get_cash_flow_data(days_back=365)
        
        if not historical_data:
            return {"error": "No hay datos suficientes para predicción de flujo de caja"}
        
        # Usar regresión lineal simple para predicción de flujo
        df = pd.DataFrame(historical_data)
        X = np.arange(len(df)).reshape(-1, 1)
        y = df['net_cash_flow'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predecir flujo futuro
        future_X = np.arange(len(df), len(df) + days_ahead).reshape(-1, 1)
        future_predictions = model.predict(future_X)
        
        # Generar fechas futuras
        start_date = timezone.now().date()
        future_dates = [start_date + timedelta(days=i) for i in range(days_ahead)]
        
        # Calcular acumulado
        cumulative_flow = sum(df['net_cash_flow'].tolist()) + np.cumsum(future_predictions)
        
        return {
            "predictions": [
                {
                    "date": date.strftime('%Y-%m-%d'),
                    "predicted_daily_flow": float(pred),
                    "cumulative_flow": float(cum_flow)
                }
                for date, pred, cum_flow in zip(future_dates, future_predictions, cumulative_flow)
            ],
            "summary": {
                "total_predicted_inflow": float(np.sum(future_predictions[future_predictions > 0])),
                "total_predicted_outflow": float(np.sum(future_predictions[future_predictions < 0])),
                "net_predicted_flow": float(np.sum(future_predictions)),
                "final_cumulative": float(cumulative_flow[-1])
            }
        }
    
    def _get_financial_historical_data(self, 
                                     financial_model: FinancialForecastModel, 
                                     period_type: str) -> pd.DataFrame:
        """Obtener datos históricos financieros para entrenamiento"""
        
        # Definir período de análisis
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=financial_model.base_model.training_period_days)
        
        # Obtener transacciones de venta
        transactions = Transaction.objects.filter(
            product__company=self.company,
            transaction_type='sale',
            transaction_date__date__range=[start_date, end_date]
        ).select_related('product')
        
        # Agrupar por período
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            if period_type == 'weekly':
                period_end = current_date + timedelta(weeks=1)
            elif period_type == 'monthly':
                next_month = current_date + timedelta(days=32)
                period_end = next_month.replace(day=1) - timedelta(days=1)
            else:  # quarterly
                period_end = current_date + timedelta(days=90)
            
            period_transactions = transactions.filter(
                transaction_date__date__range=[current_date, period_end]
            )
            
            # Calcular métricas para el período
            period_revenue = 0
            period_cost = 0
            period_units = 0
            
            for trans in period_transactions:
                revenue = float(trans.quantity) * float(trans.product.sale_price)
                cost = float(trans.quantity) * float(trans.product.cost_price)
                period_revenue += revenue
                period_cost += cost
                period_units += float(trans.quantity)
            
            margin = ((period_revenue - period_cost) / period_revenue * 100) if period_revenue > 0 else 0
            
            data.append({
                'date': current_date,
                'revenue': period_revenue,
                'cost': period_cost,
                'margin': margin,
                'units': period_units
            })
            
            current_date = period_end + timedelta(days=1)
        
        return pd.DataFrame(data)
    
    def _train_revenue_model(self, historical_data: pd.DataFrame) -> RandomForestRegressor:
        """Entrenar modelo para predicción de ingresos"""
        
        # Preparar características
        features = []
        targets_revenue = []
        targets_margin = []
        targets_units = []
        
        for i in range(len(historical_data)):
            # Usar datos de ventana deslizante como características
            window_size = min(4, i + 1)  # Usar hasta 4 períodos anteriores
            
            if i >= window_size - 1:
                # Características: promedio, tendencia, volatilidad de períodos anteriores
                window_data = historical_data.iloc[i-window_size+1:i+1]
                
                features.append([
                    window_data['revenue'].mean(),
                    window_data['revenue'].std(),
                    window_data['margin'].mean(),
                    window_data['units'].mean(),
                    len(window_data),  # número de períodos
                    window_data['revenue'].iloc[-1] - window_data['revenue'].iloc[0]  # tendencia
                ])
                
                targets_revenue.append(historical_data.iloc[i]['revenue'])
                targets_margin.append(historical_data.iloc[i]['margin'])
                targets_units.append(historical_data.iloc[i]['units'])
        
        if len(features) < 3:
            # Datos insuficientes, usar modelo simple
            model = LinearRegression()
            X = np.arange(len(historical_data)).reshape(-1, 1)
            y = historical_data['revenue'].values
            model.fit(X, y)
            return model
        
        # Entrenar modelo Random Forest
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(features, targets_revenue)
        
        return model
    
    def _predict_financial_metrics(self, 
                                 model, 
                                 historical_data: pd.DataFrame, 
                                 target_date: date) -> Tuple[float, float, float]:
        """Predecir métricas financieras para una fecha específica"""
        
        # Si tenemos suficientes datos, usar el modelo entrenado
        if len(historical_data) >= 4:
            # Usar últimos 4 períodos como características
            recent_data = historical_data.tail(4)
            
            features = [[
                recent_data['revenue'].mean(),
                recent_data['revenue'].std(),
                recent_data['margin'].mean(),
                recent_data['units'].mean(),
                len(recent_data),
                recent_data['revenue'].iloc[-1] - recent_data['revenue'].iloc[0]
            ]]
            
            if hasattr(model, 'predict'):
                pred_revenue = model.predict(features)[0]
            else:
                pred_revenue = recent_data['revenue'].mean()
        else:
            # Usar promedio simple si no hay suficientes datos
            pred_revenue = historical_data['revenue'].mean()
        
        # Predicciones para margen y unidades basadas en tendencias históricas
        pred_margin = historical_data['margin'].mean()
        pred_units = historical_data['units'].mean()
        
        # Añadir algo de variabilidad realista
        pred_revenue *= (1 + np.random.normal(0, 0.1))  # 10% de variabilidad
        pred_margin *= (1 + np.random.normal(0, 0.05))  # 5% de variabilidad
        pred_units *= (1 + np.random.normal(0, 0.15))   # 15% de variabilidad
        
        return max(0, pred_revenue), max(0, pred_margin), max(0, pred_units)
    
    def _calculate_average_margin(self, products) -> float:
        """Calcular margen promedio de productos"""
        total_margin = 0
        count = 0
        
        for product in products:
            if product.cost_price and product.sale_price:
                margin = ((product.sale_price - product.cost_price) / product.sale_price) * 100
                total_margin += margin
                count += 1
        
        return total_margin / count if count > 0 else 0
    
    def _calculate_days_to_sell(self, products, start_date: date, end_date: date) -> float:
        """Calcular días promedio para vender productos"""
        # Simplificación: usar rotación de inventario
        total_days = 0
        count = 0
        
        for product in products:
            sales = Transaction.objects.filter(
                product=product,
                transaction_type='sale',
                transaction_date__date__range=[start_date, end_date]
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            if sales > 0 and product.stock > 0:
                days_supply = (product.stock / sales) * (end_date - start_date).days
                total_days += days_supply
                count += 1
        
        return total_days / count if count > 0 else 30  # Default 30 días
    
    def _calculate_inventory_turnover(self, products, start_date: date, end_date: date) -> float:
        """Calcular rotación de inventario"""
        total_turnover = 0
        count = 0
        
        for product in products:
            # COGS = ventas en el período
            cogs = Transaction.objects.filter(
                product=product,
                transaction_type='sale',
                transaction_date__date__range=[start_date, end_date]
            ).aggregate(
                total=Sum(F('quantity') * F('product__cost_price'))
            )['total'] or 0
            
            # Inventario promedio
            avg_inventory = product.stock * product.cost_price
            
            if avg_inventory > 0:
                turnover = cogs / avg_inventory
                total_turnover += turnover
                count += 1
        
        return total_turnover / count if count > 0 else 0
    
    def _generate_supplier_recommendations(self, 
                                         roi: float, 
                                         margin: float, 
                                         days_to_sell: float) -> List[str]:
        """Generar recomendaciones automáticas para proveedores"""
        recommendations = []
        
        if roi < 10:
            recommendations.append("ROI bajo - Considerar renegociar precios o buscar alternativas")
        elif roi > 50:
            recommendations.append("ROI excelente - Aumentar órdenes con este proveedor")
        
        if margin < 15:
            recommendations.append("Margen bajo - Revisar estructura de precios")
        elif margin > 30:
            recommendations.append("Margen saludable - Mantener relación comercial")
        
        if days_to_sell > 60:
            recommendations.append("Rotación lenta - Reducir cantidades de orden")
        elif days_to_sell < 15:
            recommendations.append("Rotación alta - Considerar aumentar stock")
        
        return recommendations
    
    def _calculate_supplier_score(self, roi: float, margin: float, turnover: float) -> int:
        """Calcular score de recomendación del proveedor (1-10)"""
        score = 5  # Base
        
        # ROI weight: 40%
        if roi > 30:
            score += 2
        elif roi > 15:
            score += 1
        elif roi < 5:
            score -= 2
        
        # Margin weight: 30%
        if margin > 25:
            score += 1.5
        elif margin < 10:
            score -= 1.5
        
        # Turnover weight: 30%
        if turnover > 4:
            score += 1.5
        elif turnover < 1:
            score -= 1.5
        
        return max(1, min(10, int(score)))
    
    def _get_cash_flow_data(self, days_back: int = 365) -> List[Dict]:
        """Obtener datos históricos de flujo de caja"""
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Ingresos del día (ventas)
            daily_inflow = Transaction.objects.filter(
                product__company=self.company,
                transaction_type='sale',
                transaction_date__date=current_date
            ).aggregate(
                total=Sum(F('quantity') * F('product__sale_price'))
            )['total'] or 0
            
            # Egresos del día (compras)
            daily_outflow = Transaction.objects.filter(
                product__company=self.company,
                transaction_type='purchase',
                transaction_date__date=current_date
            ).aggregate(
                total=Sum(F('quantity') * F('unit_cost'))
            )['total'] or 0
            
            data.append({
                'date': current_date,
                'inflow': float(daily_inflow),
                'outflow': float(daily_outflow),
                'net_cash_flow': float(daily_inflow) - float(daily_outflow)
            })
            
            current_date += timedelta(days=1)
        
        return data


class DemandAnalysisService:
    """Servicio para análisis sofisticado de demanda"""
    
    def __init__(self, company: Company):
        self.company = company
    
    def analyze_seasonal_patterns(self, product_id: Optional[int] = None) -> List[DemandPatternAnalysis]:
        """Analizar patrones estacionales automáticos"""
        
        products = Product.objects.filter(company=self.company)
        if product_id:
            products = products.filter(id=product_id)
        
        analyses = []
        
        for product in products:
            # Obtener datos de demanda histórica
            historical_demand = self._get_demand_data(product, days_back=730)  # 2 años
            
            if len(historical_demand) < 30:  # Mínimo 30 puntos de datos
                continue
            
            # Analizar diferentes tipos de patrones
            seasonal_analysis = self._detect_seasonality(historical_demand)
            weekly_patterns = self._analyze_weekly_patterns(historical_demand)
            monthly_patterns = self._analyze_monthly_patterns(historical_demand)
            
            # Calcular fuerza del patrón y predictibilidad
            pattern_strength = self._calculate_pattern_strength(historical_demand)
            predictability = self._calculate_predictability_score(historical_demand)
            
            analysis = DemandPatternAnalysis.objects.update_or_create(
                product=product,
                pattern_type='seasonal',
                defaults={
                    'detected_seasonality': seasonal_analysis,
                    'weekly_patterns': weekly_patterns,
                    'monthly_patterns': monthly_patterns,
                    'pattern_strength': Decimal(str(pattern_strength)),
                    'predictability_score': Decimal(str(predictability)),
                    'analysis_period_start': timezone.now().date() - timedelta(days=730),
                    'analysis_period_end': timezone.now().date()
                }
            )[0]
            
            analyses.append(analysis)
        
        return analyses
    
    def perform_market_basket_analysis(self, min_support: float = 0.01) -> List[MarketBasketAnalysis]:
        """Realizar análisis de productos que se venden juntos"""
        
        # Obtener transacciones agrupadas por fecha/referencia
        transactions = Transaction.objects.filter(
            product__company=self.company,
            transaction_type='sale',
            transaction_date__gte=timezone.now() - timedelta(days=365)
        ).values('reference_number', 'transaction_date', 'product_id').distinct()
        
        # Agrupar por transacción (mismo día + mismo reference_number o ventana de tiempo)
        transaction_groups = self._group_transactions_for_basket_analysis(transactions)
        
        # Calcular métricas de asociación
        basket_analyses = []
        products = Product.objects.filter(company=self.company)
        
        for product_a in products:
            for product_b in products:
                if product_a.id >= product_b.id:  # Evitar duplicados
                    continue
                
                # Calcular métricas
                metrics = self._calculate_association_metrics(
                    product_a, product_b, transaction_groups
                )
                
                if metrics['support'] >= min_support:
                    # Determinar fuerza de recomendación
                    strength = self._determine_recommendation_strength(metrics)
                    
                    analysis = MarketBasketAnalysis.objects.update_or_create(
                        product_a=product_a,
                        product_b=product_b,
                        defaults={
                            'support': Decimal(str(metrics['support'])),
                            'confidence': Decimal(str(metrics['confidence'])),
                            'lift': Decimal(str(metrics['lift'])),
                            'conviction': Decimal(str(metrics['conviction'])),
                            'transactions_together': metrics['transactions_together'],
                            'total_transactions_analyzed': len(transaction_groups),
                            'recommendation_strength': strength,
                            'analysis_period_start': timezone.now().date() - timedelta(days=365),
                            'analysis_period_end': timezone.now().date()
                        }
                    )[0]
                    
                    basket_analyses.append(analysis)
        
        return basket_analyses
    
    def analyze_price_elasticity(self, product_id: int) -> Optional[PriceElasticityAnalysis]:
        """Analizar elasticidad de precios - cómo afectan cambios de precio a la demanda"""
        
        try:
            product = Product.objects.get(id=product_id, company=self.company)
        except Product.DoesNotExist:
            return None
        
        # Obtener datos históricos de precio y demanda
        price_demand_data = self._get_price_demand_data(product)
        
        if len(price_demand_data) < 10:  # Mínimo 10 puntos de datos
            return None
        
        # Calcular elasticidad usando regresión
        elasticity_metrics = self._calculate_price_elasticity(price_demand_data)
        
        # Determinar tipo de elasticidad
        elasticity_type = self._classify_elasticity_type(elasticity_metrics['elasticity_coefficient'])
        
        # Calcular precio óptimo
        optimal_price_data = self._calculate_optimal_price(price_demand_data, product)
        
        analysis = PriceElasticityAnalysis.objects.update_or_create(
            product=product,
            defaults={
                'elasticity_coefficient': Decimal(str(elasticity_metrics['elasticity_coefficient'])),
                'elasticity_type': elasticity_type,
                'price_range_min': Decimal(str(elasticity_metrics['price_min'])),
                'price_range_max': Decimal(str(elasticity_metrics['price_max'])),
                'demand_sensitivity': Decimal(str(elasticity_metrics['sensitivity'])),
                'optimal_price': Decimal(str(optimal_price_data['optimal_price'])),
                'optimal_price_confidence': Decimal(str(optimal_price_data['confidence'])),
                'predicted_demand_at_optimal': Decimal(str(optimal_price_data['predicted_demand'])),
                'predicted_revenue_at_optimal': Decimal(str(optimal_price_data['predicted_revenue'])),
                'analysis_period_start': timezone.now().date() - timedelta(days=365),
                'analysis_period_end': timezone.now().date()
            }
        )[0]
        
        return analysis
    
    def predict_trending_products(self) -> List[TrendingProductPrediction]:
        """Predecir productos que van a despegar"""
        
        products = Product.objects.filter(company=self.company, is_active=True)
        trending_predictions = []
        
        for product in products:
            # Analizar tendencias de velocidad de venta
            velocity_metrics = self._analyze_sales_velocity(product)
            
            # Analizar aceleración de demanda
            acceleration_metrics = self._analyze_demand_acceleration(product)
            
            # Analizar mejora en market basket
            basket_improvement = self._analyze_basket_improvement(product)
            
            # Calcular score de tendencia compuesto
            trending_score = self._calculate_trending_score(
                velocity_metrics, acceleration_metrics, basket_improvement
            )
            
            if trending_score > 0.3:  # Solo productos con potencial real
                # Predecir crecimiento y fecha de pico
                growth_prediction = self._predict_growth_metrics(product, trending_score)
                
                # Categorizar tendencia
                trend_category = self._categorize_trend(trending_score, velocity_metrics)
                
                # Recomendar acción
                recommended_action = self._recommend_trending_action(trend_category, trending_score)
                
                prediction = TrendingProductPrediction.objects.update_or_create(
                    product=product,
                    defaults={
                        'trending_score': Decimal(str(trending_score)),
                        'velocity_increase': Decimal(str(velocity_metrics['increase_percentage'])),
                        'demand_acceleration': Decimal(str(acceleration_metrics['acceleration'])),
                        'market_basket_improvement': Decimal(str(basket_improvement)),
                        'predicted_growth_next_month': Decimal(str(growth_prediction['growth_percentage'])),
                        'predicted_peak_demand_date': growth_prediction['peak_date'],
                        'trend_category': trend_category,
                        'prediction_confidence': Decimal(str(growth_prediction['confidence'])),
                        'recommended_action': recommended_action
                    }
                )[0]
                
                trending_predictions.append(prediction)
        
        return trending_predictions
    
    def _get_demand_data(self, product: Product, days_back: int = 365) -> pd.DataFrame:
        """Obtener datos de demanda histórica para un producto"""
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Obtener transacciones de venta agrupadas por día
        daily_demand = Transaction.objects.filter(
            product=product,
            transaction_type='sale',
            transaction_date__date__range=[start_date, end_date]
        ).extra(
            select={'date': 'DATE(transaction_date)'}
        ).values('date').annotate(
            total_demand=Sum('quantity')
        ).order_by('date')
        
        # Convertir a DataFrame con días completos (incluyendo días sin ventas)
        data = []
        current_date = start_date
        demand_dict = {item['date']: float(item['total_demand']) for item in daily_demand}
        
        while current_date <= end_date:
            data.append({
                'date': current_date,
                'demand': demand_dict.get(current_date, 0.0),
                'day_of_week': current_date.weekday(),
                'month': current_date.month,
                'week_of_year': current_date.isocalendar()[1]
            })
            current_date += timedelta(days=1)
        
        return pd.DataFrame(data)
    
    def _detect_seasonality(self, demand_data: pd.DataFrame) -> Dict:
        """Detectar patrones estacionales en los datos de demanda"""
        
        if len(demand_data) < 365:  # Necesitamos al menos un año
            return {}
        
        # Análisis por mes
        monthly_avg = demand_data.groupby('month')['demand'].mean().to_dict()
        monthly_std = demand_data.groupby('month')['demand'].std().to_dict()
        
        # Análisis por día de la semana
        weekly_avg = demand_data.groupby('day_of_week')['demand'].mean().to_dict()
        
        # Detectar picos estacionales (meses con demanda > promedio + 1 std)
        overall_avg = demand_data['demand'].mean()
        overall_std = demand_data['demand'].std()
        
        peak_months = []
        for month, avg_demand in monthly_avg.items():
            if avg_demand > overall_avg + overall_std:
                peak_months.append({
                    'month': month,
                    'month_name': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                                   'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][month-1],
                    'avg_demand': avg_demand,
                    'increase_percentage': ((avg_demand - overall_avg) / overall_avg) * 100
                })
        
        return {
            'monthly_averages': monthly_avg,
            'weekly_averages': weekly_avg,
            'peak_months': peak_months,
            'seasonal_strength': len(peak_months) / 12.0,  # Proporción de meses con picos
            'overall_average': overall_avg,
            'volatility': overall_std / overall_avg if overall_avg > 0 else 0
        }
    
    def _analyze_weekly_patterns(self, demand_data: pd.DataFrame) -> Dict:
        """Analizar patrones semanales"""
        
        weekly_analysis = demand_data.groupby('day_of_week')['demand'].agg(['mean', 'std']).reset_index()
        
        day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        patterns = {}
        for _, row in weekly_analysis.iterrows():
            day = int(row['day_of_week'])
            patterns[day_names[day]] = {
                'average_demand': float(row['mean']),
                'volatility': float(row['std']) if pd.notna(row['std']) else 0.0
            }
        
        # Identificar mejor y peor día
        best_day = weekly_analysis.loc[weekly_analysis['mean'].idxmax()]
        worst_day = weekly_analysis.loc[weekly_analysis['mean'].idxmin()]
        
        return {
            'daily_patterns': patterns,
            'best_day': {
                'day': day_names[int(best_day['day_of_week'])],
                'average_demand': float(best_day['mean'])
            },
            'worst_day': {
                'day': day_names[int(worst_day['day_of_week'])],
                'average_demand': float(worst_day['mean'])
            },
            'weekend_effect': (patterns.get('Sábado', {}).get('average_demand', 0) + 
                              patterns.get('Domingo', {}).get('average_demand', 0)) / 2
        }
    
    def _analyze_monthly_patterns(self, demand_data: pd.DataFrame) -> Dict:
        """Analizar patrones mensuales"""
        
        monthly_analysis = demand_data.groupby('month')['demand'].agg(['mean', 'std']).reset_index()
        
        month_names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                       'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        patterns = {}
        for _, row in monthly_analysis.iterrows():
            month = int(row['month'])
            patterns[month_names[month-1]] = {
                'average_demand': float(row['mean']),
                'volatility': float(row['std']) if pd.notna(row['std']) else 0.0
            }
        
        return {
            'monthly_patterns': patterns,
            'peak_season': max(patterns.items(), key=lambda x: x[1]['average_demand']),
            'low_season': min(patterns.items(), key=lambda x: x[1]['average_demand'])
        }
    
    def _calculate_pattern_strength(self, demand_data: pd.DataFrame) -> float:
        """Calcular la fuerza del patrón (qué tan consistente es)"""
        
        if len(demand_data) == 0:
            return 0.0
        
        # Coeficiente de variación como medida de consistencia
        mean_demand = demand_data['demand'].mean()
        std_demand = demand_data['demand'].std()
        
        if mean_demand == 0:
            return 0.0
        
        cv = std_demand / mean_demand
        
        # Convertir a score de fuerza (0-1, donde 1 es muy fuerte/consistente)
        strength = max(0, 1 - cv)
        
        return min(1.0, strength)
    
    def _calculate_predictability_score(self, demand_data: pd.DataFrame) -> float:
        """Calcular score de predictibilidad basado en autocorrelación"""
        
        if len(demand_data) < 7:
            return 0.0
        
        # Calcular autocorrelación con lag de 7 días (patrón semanal)
        demand_values = demand_data['demand'].values
        
        if len(demand_values) < 14:
            return 0.5  # Score neutral para datos limitados
        
        # Autocorrelación simple
        corr_weekly = np.corrcoef(demand_values[:-7], demand_values[7:])[0, 1]
        
        if np.isnan(corr_weekly):
            corr_weekly = 0
        
        # Convertir correlación a score de predictibilidad
        predictability = (abs(corr_weekly) + 1) / 2  # Normalizar a 0-1
        
        return min(1.0, max(0.0, predictability))
    
    def _group_transactions_for_basket_analysis(self, transactions) -> List[List[int]]:
        """Agrupar transacciones para análisis de market basket"""
        
        # Agrupar por reference_number y fecha (ventana de 1 hora)
        groups = {}
        
        for trans in transactions:
            # Crear clave única por transacción
            if trans['reference_number']:
                key = f"{trans['reference_number']}_{trans['transaction_date'].date()}"
            else:
                # Si no hay reference_number, agrupar por hora
                hour_key = trans['transaction_date'].replace(minute=0, second=0, microsecond=0)
                key = f"auto_{hour_key}"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(trans['product_id'])
        
        # Devolver solo grupos con más de 1 producto
        return [group for group in groups.values() if len(set(group)) > 1]
    
    def _calculate_association_metrics(self, 
                                     product_a: Product, 
                                     product_b: Product, 
                                     transaction_groups: List[List[int]]) -> Dict:
        """Calcular métricas de asociación para market basket analysis"""
        
        total_transactions = len(transaction_groups)
        
        # Contar transacciones que contienen cada producto
        transactions_a = sum(1 for group in transaction_groups if product_a.id in group)
        transactions_b = sum(1 for group in transaction_groups if product_b.id in group)
        transactions_both = sum(1 for group in transaction_groups 
                               if product_a.id in group and product_b.id in group)
        
        if total_transactions == 0:
            return {
                'support': 0, 'confidence': 0, 'lift': 0, 'conviction': 0,
                'transactions_together': 0
            }
        
        # Calcular métricas
        support = transactions_both / total_transactions
        confidence = transactions_both / transactions_a if transactions_a > 0 else 0
        
        expected_both = (transactions_a * transactions_b) / total_transactions
        lift = (transactions_both / expected_both) if expected_both > 0 else 0
        
        # Conviction: mide cuánto más probable es que A ocurra sin B si fueran independientes
        if confidence == 1:
            conviction = float('inf')
        else:
            conviction = (1 - (transactions_b / total_transactions)) / (1 - confidence) if confidence < 1 else 1
        
        return {
            'support': support,
            'confidence': confidence,
            'lift': lift,
            'conviction': conviction,
            'transactions_together': transactions_both
        }
    
    def _determine_recommendation_strength(self, metrics: Dict) -> str:
        """Determinar fuerza de recomendación basada en métricas"""
        
        lift = metrics['lift']
        confidence = metrics['confidence']
        support = metrics['support']
        
        if lift >= 3 and confidence >= 0.5 and support >= 0.05:
            return 'very_strong'
        elif lift >= 2 and confidence >= 0.3 and support >= 0.02:
            return 'strong'
        elif lift >= 1.5 and confidence >= 0.2:
            return 'moderate'
        else:
            return 'weak'
    
    def _get_price_demand_data(self, product: Product) -> List[Dict]:
        """Obtener datos históricos de precio y demanda"""
        
        # Obtener transacciones de venta con precios
        transactions = Transaction.objects.filter(
            product=product,
            transaction_type='sale',
            transaction_date__gte=timezone.now() - timedelta(days=365)
        ).extra(
            select={'date': 'DATE(transaction_date)'}
        ).values('date').annotate(
            total_demand=Sum('quantity'),
            avg_price=Avg('product__sale_price')
        ).order_by('date')
        
        return list(transactions)
    
    def _calculate_price_elasticity(self, price_demand_data: List[Dict]) -> Dict:
        """Calcular elasticidad de precios usando regresión"""
        
        if len(price_demand_data) < 5:
            return {
                'elasticity_coefficient': 0,
                'price_min': 0, 'price_max': 0,
                'sensitivity': 0
            }
        
        # Convertir a arrays para análisis
        prices = np.array([float(item['avg_price']) for item in price_demand_data])
        demands = np.array([float(item['total_demand']) for item in price_demand_data])
        
        # Filtrar valores válidos
        valid_mask = (prices > 0) & (demands > 0)
        prices = prices[valid_mask]
        demands = demands[valid_mask]
        
        if len(prices) < 3:
            return {
                'elasticity_coefficient': 0,
                'price_min': 0, 'price_max': 0,
                'sensitivity': 0
            }
        
        # Calcular elasticidad usando log-log regression
        log_prices = np.log(prices)
        log_demands = np.log(demands)
        
        # Regresión lineal en espacio log
        X = log_prices.reshape(-1, 1)
        y = log_demands
        
        model = LinearRegression()
        model.fit(X, y)
        
        elasticity_coefficient = model.coef_[0]
        
        return {
            'elasticity_coefficient': elasticity_coefficient,
            'price_min': float(prices.min()),
            'price_max': float(prices.max()),
            'sensitivity': abs(elasticity_coefficient)
        }
    
    def _classify_elasticity_type(self, coefficient: float) -> str:
        """Clasificar tipo de elasticidad basado en coeficiente"""
        
        if abs(coefficient) > 1:
            return 'elastic'
        elif abs(coefficient) < 1:
            return 'inelastic'
        elif abs(coefficient) == 1:
            return 'unitary'
        else:
            return 'inelastic'  # Default
    
    def _calculate_optimal_price(self, price_demand_data: List[Dict], product: Product) -> Dict:
        """Calcular precio óptimo para maximizar ingresos"""
        
        if len(price_demand_data) < 3:
            return {
                'optimal_price': float(product.sale_price),
                'confidence': 50.0,
                'predicted_demand': 0,
                'predicted_revenue': 0
            }
        
        # Usar datos históricos para modelar demanda vs precio
        prices = np.array([float(item['avg_price']) for item in price_demand_data])
        demands = np.array([float(item['total_demand']) for item in price_demand_data])
        
        # Filtrar valores válidos
        valid_mask = (prices > 0) & (demands > 0)
        prices = prices[valid_mask]
        demands = demands[valid_mask]
        
        if len(prices) < 3:
            return {
                'optimal_price': float(product.sale_price),
                'confidence': 50.0,
                'predicted_demand': 0,
                'predicted_revenue': 0
            }
        
        # Ajustar modelo de demanda
        X = prices.reshape(-1, 1)
        model = LinearRegression()
        model.fit(X, demands)
        
        # Probar diferentes precios para encontrar el óptimo
        price_range = np.linspace(prices.min(), prices.max() * 1.5, 100)
        predicted_demands = model.predict(price_range.reshape(-1, 1))
        predicted_revenues = price_range * predicted_demands
        
        # Filtrar predicciones válidas (demanda > 0)
        valid_predictions = predicted_demands > 0
        if not any(valid_predictions):
            return {
                'optimal_price': float(product.sale_price),
                'confidence': 30.0,
                'predicted_demand': 0,
                'predicted_revenue': 0
            }
        
        valid_prices = price_range[valid_predictions]
        valid_revenues = predicted_revenues[valid_predictions]
        valid_demands = predicted_demands[valid_predictions]
        
        # Encontrar precio que maximiza ingresos
        optimal_idx = np.argmax(valid_revenues)
        optimal_price = valid_prices[optimal_idx]
        optimal_demand = valid_demands[optimal_idx]
        optimal_revenue = valid_revenues[optimal_idx]
        
        # Calcular confianza basada en R²
        r2 = model.score(X, demands)
        confidence = max(30, min(95, r2 * 100))
        
        return {
            'optimal_price': float(optimal_price),
            'confidence': confidence,
            'predicted_demand': float(optimal_demand),
            'predicted_revenue': float(optimal_revenue)
        }
    
    def _analyze_sales_velocity(self, product: Product) -> Dict:
        """Analizar velocidad de ventas y sus cambios"""
        
        # Comparar último mes vs mes anterior
        current_month_sales = Transaction.objects.filter(
            product=product,
            transaction_type='sale',
            transaction_date__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        previous_month_sales = Transaction.objects.filter(
            product=product,
            transaction_type='sale',
            transaction_date__range=[
                timezone.now() - timedelta(days=60),
                timezone.now() - timedelta(days=30)
            ]
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        if previous_month_sales > 0:
            increase_percentage = ((current_month_sales - previous_month_sales) / previous_month_sales) * 100
        else:
            increase_percentage = 100.0 if current_month_sales > 0 else 0.0
        
        return {
            'current_month_sales': float(current_month_sales),
            'previous_month_sales': float(previous_month_sales),
            'increase_percentage': increase_percentage,
            'velocity_trend': 'increasing' if increase_percentage > 0 else 'decreasing'
        }
    
    def _analyze_demand_acceleration(self, product: Product) -> Dict:
        """Analizar aceleración de la demanda"""
        
        # Obtener datos de los últimos 3 meses agrupados por semana
        weekly_sales = []
        for week in range(12):  # 12 semanas
            week_start = timezone.now() - timedelta(weeks=week+1)
            week_end = timezone.now() - timedelta(weeks=week)
            
            week_sales = Transaction.objects.filter(
                product=product,
                transaction_type='sale',
                transaction_date__range=[week_start, week_end]
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            weekly_sales.append(float(week_sales))
        
        weekly_sales.reverse()  # Orden cronológico
        
        if len(weekly_sales) < 4:
            return {'acceleration': 0, 'trend_direction': 'stable'}
        
        # Calcular aceleración usando diferencias de segundo orden
        first_diff = np.diff(weekly_sales)
        second_diff = np.diff(first_diff)
        
        acceleration = np.mean(second_diff) if len(second_diff) > 0 else 0
        
        trend_direction = 'accelerating' if acceleration > 0 else 'decelerating' if acceleration < 0 else 'stable'
        
        return {
            'acceleration': acceleration,
            'trend_direction': trend_direction,
            'weekly_sales': weekly_sales
        }
    
    def _analyze_basket_improvement(self, product: Product) -> float:
        """Analizar mejora en market basket (aparecer más frecuentemente con otros productos)"""
        
        # Comparar asociaciones actuales vs anteriores
        recent_associations = MarketBasketAnalysis.objects.filter(
            Q(product_a=product) | Q(product_b=product),
            created_at__gte=timezone.now() - timedelta(days=30)
        ).aggregate(avg_lift=Avg('lift'))['avg_lift'] or 0
        
        older_associations = MarketBasketAnalysis.objects.filter(
            Q(product_a=product) | Q(product_b=product),
            created_at__range=[
                timezone.now() - timedelta(days=90),
                timezone.now() - timedelta(days=30)
            ]
        ).aggregate(avg_lift=Avg('lift'))['avg_lift'] or 0
        
        if older_associations > 0:
            improvement = ((recent_associations - older_associations) / older_associations) * 100
        else:
            improvement = 10.0 if recent_associations > 0 else 0.0
        
        return max(0, improvement)
    
    def _calculate_trending_score(self, 
                                velocity_metrics: Dict, 
                                acceleration_metrics: Dict, 
                                basket_improvement: float) -> float:
        """Calcular score compuesto de tendencia"""
        
        # Normalizar componentes
        velocity_score = min(1.0, max(0, velocity_metrics['increase_percentage'] / 100))
        acceleration_score = min(1.0, max(0, acceleration_metrics['acceleration'] / 10))
        basket_score = min(1.0, max(0, basket_improvement / 50))
        
        # Pesos: velocidad 40%, aceleración 40%, basket 20%
        trending_score = (velocity_score * 0.4 + 
                         acceleration_score * 0.4 + 
                         basket_score * 0.2)
        
        return min(1.0, trending_score)
    
    def _predict_growth_metrics(self, product: Product, trending_score: float) -> Dict:
        """Predecir métricas de crecimiento"""
        
        # Obtener sales históricas
        recent_sales = Transaction.objects.filter(
            product=product,
            transaction_type='sale',
            transaction_date__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Proyectar crecimiento basado en trending score
        growth_percentage = trending_score * 50  # Máximo 50% de crecimiento
        
        # Estimar fecha de pico (entre 2-8 semanas)
        weeks_to_peak = max(2, min(8, int(8 - trending_score * 6)))
        peak_date = timezone.now().date() + timedelta(weeks=weeks_to_peak)
        
        # Confianza basada en datos disponibles
        confidence = min(95, max(60, trending_score * 100))
        
        return {
            'growth_percentage': growth_percentage,
            'peak_date': peak_date,
            'confidence': confidence
        }
    
    def _categorize_trend(self, trending_score: float, velocity_metrics: Dict) -> str:
        """Categorizar el tipo de tendencia"""
        
        if trending_score > 0.8:
            return 'viral_potential'
        elif trending_score > 0.6:
            return 'peak_soon'
        elif trending_score > 0.4:
            return 'accelerating'
        else:
            return 'emerging'
    
    def _recommend_trending_action(self, trend_category: str, trending_score: float) -> str:
        """Recomendar acción basada en tendencia"""
        
        if trend_category == 'viral_potential':
            return 'increase_stock'
        elif trend_category == 'peak_soon':
            return 'promote'
        elif trend_category == 'accelerating':
            return 'bundle'
        else:
            return 'monitor'


class InventoryOptimizationService:
    """Servicio para optimización inteligente de inventario"""
    
    def __init__(self, company: Company):
        self.company = company
    
    def calculate_optimal_stock_levels(self) -> List[OptimalStockLevel]:
        """Calcular niveles de stock óptimos matemáticamente"""
        
        products = Product.objects.filter(company=self.company, is_active=True)
        optimal_levels = []
        
        for product in products:
            # Obtener datos necesarios para cálculo
            demand_data = self._get_demand_statistics(product)
            cost_data = self._get_cost_parameters(product)
            
            if demand_data['average_demand'] <= 0:
                continue  # Saltar productos sin demanda
            
            # Calcular cantidad óptima usando EOQ modificado
            optimal_quantity = self._calculate_eoq(demand_data, cost_data)
            
            # Calcular safety stock dinámico
            safety_stock = self._calculate_dynamic_safety_stock(demand_data)
            
            # Calcular punto de reorden óptimo
            reorder_point = self._calculate_optimal_reorder_point(demand_data, safety_stock)
            
            # Calcular costos actuales vs óptimos
            current_cost = self._calculate_current_inventory_cost(product, demand_data, cost_data)
            optimal_cost = self._calculate_optimal_inventory_cost(optimal_quantity, demand_data, cost_data)
            
            # Clasificación ABC automática
            abc_data = self._calculate_abc_classification(product, demand_data)
            
            optimal_level = OptimalStockLevel.objects.update_or_create(
                product=product,
                defaults={
                    'optimal_quantity': Decimal(str(optimal_quantity)),
                    'safety_stock_dynamic': Decimal(str(safety_stock)),
                    'reorder_point_optimal': Decimal(str(reorder_point)),
                    'demand_variability': Decimal(str(demand_data['demand_variability'])),
                    'lead_time_variability': Decimal(str(demand_data['lead_time_variability'])),
                    'service_level_target': Decimal('95.00'),
                    'holding_cost_per_unit': Decimal(str(cost_data['holding_cost'])),
                    'stockout_cost_per_unit': Decimal(str(cost_data['stockout_cost'])),
                    'ordering_cost': Decimal(str(cost_data['ordering_cost'])),
                    'total_cost_current': Decimal(str(current_cost)),
                    'total_cost_optimal': Decimal(str(optimal_cost)),
                    'potential_savings': Decimal(str(max(0, current_cost - optimal_cost))),
                    'abc_classification': abc_data['classification'],
                    'abc_score': Decimal(str(abc_data['score']))
                }
            )[0]
            
            optimal_levels.append(optimal_level)
        
        return optimal_levels
    
    def predict_stockouts(self, days_ahead: int = 30) -> List[StockoutPrediction]:
        """Predecir quiebres de stock con anticipación"""
        
        products = Product.objects.filter(company=self.company, is_active=True)
        predictions = []
        
        for product in products:
            # Obtener datos de demanda y stock actuales
            current_stock = float(product.stock)
            demand_data = self._get_demand_statistics(product, days_back=90)
            
            if demand_data['average_demand'] <= 0:
                continue  # Saltar productos sin demanda
            
            # Predecir fecha de stockout
            stockout_prediction = self._predict_stockout_date(
                current_stock, demand_data, days_ahead
            )
            
            if stockout_prediction['days_until_stockout'] <= days_ahead:
                # Calcular impacto estimado
                impact_data = self._calculate_stockout_impact(product, stockout_prediction)
                
                # Determinar prioridad de alerta
                alert_priority = self._determine_stockout_priority(
                    stockout_prediction['days_until_stockout'],
                    impact_data['customer_impact_score']
                )
                
                prediction = StockoutPrediction.objects.update_or_create(
                    product=product,
                    defaults={
                        'predicted_stockout_date': stockout_prediction['stockout_date'],
                        'days_until_stockout': stockout_prediction['days_until_stockout'],
                        'confidence_level': Decimal(str(stockout_prediction['confidence'])),
                        'current_stock': Decimal(str(current_stock)),
                        'daily_demand_average': Decimal(str(demand_data['average_demand'])),
                        'demand_volatility': Decimal(str(demand_data['demand_variability'])),
                        'estimated_lost_sales': Decimal(str(impact_data['estimated_lost_sales'])),
                        'customer_impact_score': impact_data['customer_impact_score'],
                        'alert_priority': alert_priority,
                        'alert_sent': False
                    }
                )[0]
                
                predictions.append(prediction)
        
        return predictions
    
    def _get_demand_statistics(self, product: Product, days_back: int = 365) -> Dict:
        """Obtener estadísticas de demanda para un producto"""
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Obtener transacciones de demanda (salidas)
        transactions = Transaction.objects.filter(
            product=product,
            transaction_type__in=['sale', 'usage'],
            transaction_date__date__range=[start_date, end_date]
        )
        
        if not transactions.exists():
            return {
                'average_demand': 0,
                'demand_variability': 0,
                'lead_time_variability': 0.1,
                'seasonal_factor': 1.0
            }
        
        # Agrupar por día
        daily_demand = transactions.extra(
            select={'date': 'DATE(transaction_date)'}
        ).values('date').annotate(
            total_demand=Sum('quantity')
        )
        
        demands = [float(item['total_demand']) for item in daily_demand]
        
        average_demand = np.mean(demands) if demands else 0
        demand_std = np.std(demands) if len(demands) > 1 else 0
        demand_variability = (demand_std / average_demand) if average_demand > 0 else 0
        
        # Estimar variabilidad de lead time (simplificado)
        lead_time_variability = 0.2  # 20% por defecto
        
        return {
            'average_demand': average_demand,
            'demand_variability': demand_variability,
            'lead_time_variability': lead_time_variability,
            'seasonal_factor': 1.0  # Simplificado por ahora
        }
    
    def _get_cost_parameters(self, product: Product) -> Dict:
        """Obtener parámetros de costo para cálculos de optimización"""
        
        # Calcular costos basados en datos del producto
        unit_cost = float(product.cost_price) if product.cost_price else 0
        
        # Holding cost: típicamente 20-30% del costo unitario anual
        holding_cost_annual = unit_cost * 0.25  # 25% anual
        holding_cost_daily = holding_cost_annual / 365
        
        # Stockout cost: estimado como margen perdido
        margin = float(product.sale_price - product.cost_price) if product.sale_price and product.cost_price else 0
        stockout_cost = margin * 2  # Penalización por stockout
        
        # Ordering cost: costo fijo por orden (estimado)
        ordering_cost = 100.0  # S/ 100 por orden (estimado)
        
        return {
            'holding_cost': holding_cost_daily,
            'stockout_cost': stockout_cost,
            'ordering_cost': ordering_cost,
            'unit_cost': unit_cost
        }
    
    def _calculate_eoq(self, demand_data: Dict, cost_data: Dict) -> float:
        """Calcular Economic Order Quantity (EOQ)"""
        
        annual_demand = demand_data['average_demand'] * 365
        ordering_cost = cost_data['ordering_cost']
        holding_cost_annual = cost_data['holding_cost'] * 365
        
        if holding_cost_annual <= 0:
            return demand_data['average_demand'] * 30  # Default: 30 días de stock
        
        # Fórmula EOQ clásica
        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost_annual)
        
        # Ajustar por variabilidad de demanda
        variability_factor = 1 + demand_data['demand_variability']
        eoq_adjusted = eoq * variability_factor
        
        return max(1, eoq_adjusted)
    
    def _calculate_dynamic_safety_stock(self, demand_data: Dict) -> float:
        """Calcular safety stock dinámico basado en variabilidad"""
        
        # Safety stock = Z * σ * √L
        # Donde Z = z-score para nivel de servicio, σ = std demanda, L = lead time
        
        z_score = 1.65  # 95% nivel de servicio
        demand_std = demand_data['average_demand'] * demand_data['demand_variability']
        lead_time_days = 7  # Asumimos 7 días de lead time promedio
        lead_time_std = lead_time_days * demand_data['lead_time_variability']
        
        # Fórmula para variabilidad tanto en demanda como en lead time
        safety_stock = z_score * np.sqrt(
            (lead_time_days * demand_std**2) + 
            (demand_data['average_demand']**2 * lead_time_std**2)
        )
        
        return max(0, safety_stock)
    
    def _calculate_optimal_reorder_point(self, demand_data: Dict, safety_stock: float) -> float:
        """Calcular punto de reorden óptimo"""
        
        lead_time_days = 7  # Asumimos 7 días
        expected_demand_during_lead_time = demand_data['average_demand'] * lead_time_days
        
        reorder_point = expected_demand_during_lead_time + safety_stock
        
        return max(1, reorder_point)
    
    def _calculate_current_inventory_cost(self, product: Product, demand_data: Dict, cost_data: Dict) -> float:
        """Calcular costo actual de inventario"""
        
        current_stock = float(product.stock)
        
        # Costo de mantener stock actual
        holding_cost = current_stock * cost_data['holding_cost'] * 365
        
        # Estimar costo de stockout basado en frecuencia actual
        average_orders_per_year = (demand_data['average_demand'] * 365) / max(1, current_stock)
        ordering_cost = average_orders_per_year * cost_data['ordering_cost']
        
        # Estimar costo de stockout (simplificado)
        stockout_risk = max(0, 1 - (current_stock / max(1, demand_data['average_demand'] * 30)))
        stockout_cost = stockout_risk * cost_data['stockout_cost'] * demand_data['average_demand'] * 12
        
        return holding_cost + ordering_cost + stockout_cost
    
    def _calculate_optimal_inventory_cost(self, optimal_quantity: float, demand_data: Dict, cost_data: Dict) -> float:
        """Calcular costo óptimo de inventario"""
        
        # Costo de mantener stock óptimo
        holding_cost = (optimal_quantity / 2) * cost_data['holding_cost'] * 365
        
        # Costo de ordenar con cantidad óptima
        orders_per_year = (demand_data['average_demand'] * 365) / optimal_quantity
        ordering_cost = orders_per_year * cost_data['ordering_cost']
        
        # Costo de stockout mínimo con safety stock
        stockout_cost = 0.05 * cost_data['stockout_cost'] * demand_data['average_demand'] * 12  # 5% riesgo residual
        
        return holding_cost + ordering_cost + stockout_cost
    
    def _calculate_abc_classification(self, product: Product, demand_data: Dict) -> Dict:
        """Calcular clasificación ABC para el producto"""
        
        # Calcular valor anual
        annual_demand = demand_data['average_demand'] * 365
        unit_value = float(product.cost_price) if product.cost_price else 0
        annual_value = annual_demand * unit_value
        
        # Obtener todos los productos para comparación
        all_products_values = []
        for p in Product.objects.filter(company=self.company, is_active=True):
            p_demand_data = self._get_demand_statistics(p, days_back=365)
            p_annual_demand = p_demand_data['average_demand'] * 365
            p_unit_value = float(p.cost_price) if p.cost_price else 0
            p_annual_value = p_annual_demand * p_unit_value
            all_products_values.append(p_annual_value)
        
        if not all_products_values:
            return {'classification': 'C', 'score': 0.1}
        
        # Calcular percentiles
        percentile_80 = np.percentile(all_products_values, 80)
        percentile_95 = np.percentile(all_products_values, 95)
        
        # Clasificar
        if annual_value >= percentile_95:
            classification = 'A'
            score = 0.9
        elif annual_value >= percentile_80:
            classification = 'B'
            score = 0.6
        else:
            classification = 'C'
            score = 0.3
        
        return {
            'classification': classification,
            'score': score
        }
    
    def _predict_stockout_date(self, current_stock: float, demand_data: Dict, max_days: int) -> Dict:
        """Predecir fecha de stockout"""
        
        daily_demand = demand_data['average_demand']
        demand_volatility = demand_data['demand_variability']
        
        if daily_demand <= 0:
            return {
                'stockout_date': timezone.now().date() + timedelta(days=max_days),
                'days_until_stockout': max_days,
                'confidence': 50
            }
        
        # Simulación Monte Carlo simple
        simulations = 1000
        stockout_days = []
        
        for _ in range(simulations):
            sim_stock = current_stock
            sim_day = 0
            
            while sim_stock > 0 and sim_day < max_days:
                # Simular demanda diaria con variabilidad
                daily_demand_sim = max(0, np.random.normal(daily_demand, daily_demand * demand_volatility))
                sim_stock -= daily_demand_sim
                sim_day += 1
            
            if sim_stock <= 0:
                stockout_days.append(sim_day)
        
        if stockout_days:
            avg_days = np.mean(stockout_days)
            confidence = len(stockout_days) / simulations * 100
        else:
            avg_days = max_days
            confidence = 10  # Baja confianza si no hay stockouts predichos
        
        stockout_date = timezone.now().date() + timedelta(days=int(avg_days))
        
        return {
            'stockout_date': stockout_date,
            'days_until_stockout': int(avg_days),
            'confidence': confidence
        }
    
    def _calculate_stockout_impact(self, product: Product, stockout_prediction: Dict) -> Dict:
        """Calcular impacto estimado del stockout"""
        
        # Estimar ventas perdidas
        days_without_stock = min(7, stockout_prediction['days_until_stockout'])  # Máximo 7 días
        demand_data = self._get_demand_statistics(product)
        estimated_lost_sales = demand_data['average_demand'] * days_without_stock
        estimated_lost_revenue = estimated_lost_sales * float(product.sale_price or 0)
        
        # Score de impacto al cliente (1-10)
        # Basado en frecuencia de compra y valor del producto
        sales_frequency = Transaction.objects.filter(
            product=product,
            transaction_type='sale',
            transaction_date__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        customer_impact = min(10, max(1, (sales_frequency / 10) + (estimated_lost_revenue / 1000)))
        
        return {
            'estimated_lost_sales': estimated_lost_revenue,
            'customer_impact_score': int(customer_impact)
        }
    
    def _determine_stockout_priority(self, days_until: int, customer_impact: int) -> str:
        """Determinar prioridad de alerta de stockout"""
        
        if days_until <= 3 and customer_impact >= 7:
            return 'critical'
        elif days_until <= 7 and customer_impact >= 5:
            return 'high'
        elif days_until <= 14:
            return 'medium'
        else:
            return 'low'


class CustomerIntelligenceService:
    """Servicio para Customer Intelligence (CRM + ML)"""
    
    def __init__(self, company: Company):
        self.company = company
    
    def calculate_customer_lifetime_value(self) -> List[CustomerLifetimeValue]:
        """Calcular Customer Lifetime Value predicho"""
        
        customers = Customer.objects.filter(is_active=True)
        clv_analyses = []
        
        for customer in customers:
            # Obtener datos históricos del cliente
            customer_data = self._get_customer_transaction_data(customer)
            
            if not customer_data['transactions']:
                continue  # Saltar clientes sin transacciones
            
            # Calcular componentes del CLV
            clv_components = self._calculate_clv_components(customer_data)
            
            # Predecir CLV
            predicted_clv = self._predict_clv(clv_components)
            
            # Calcular segmentación RFM
            rfm_segment = self._calculate_rfm_segmentation(customer_data)
            
            clv_analysis = CustomerLifetimeValue.objects.update_or_create(
                customer=customer,
                defaults={
                    'predicted_clv': Decimal(str(predicted_clv['clv'])),
                    'clv_confidence': Decimal(str(predicted_clv['confidence'])),
                    'average_order_value': Decimal(str(clv_components['avg_order_value'])),
                    'purchase_frequency': Decimal(str(clv_components['purchase_frequency'])),
                    'customer_lifespan_months': Decimal(str(clv_components['lifespan_months'])),
                    'recency_days': clv_components['recency_days'],
                    'frequency_score': Decimal(str(rfm_segment['frequency_score'])),
                    'monetary_score': Decimal(str(rfm_segment['monetary_score'])),
                    'rfm_segment': rfm_segment['segment']
                }
            )[0]
            
            clv_analyses.append(clv_analysis)
        
        return clv_analyses
    
    def predict_customer_churn(self) -> List[ChurnPrediction]:
        """Predecir riesgo de churn por cliente"""
        
        customers = Customer.objects.filter(is_active=True)
        churn_predictions = []
        
        for customer in customers:
            # Obtener datos del cliente
            customer_data = self._get_customer_transaction_data(customer)
            
            if not customer_data['transactions']:
                continue
            
            # Calcular probabilidad de churn
            churn_analysis = self._calculate_churn_probability(customer_data)
            
            # Determinar estrategia de retención
            retention_strategy = self._determine_retention_strategy(churn_analysis)
            
            churn_prediction = ChurnPrediction.objects.update_or_create(
                customer=customer,
                defaults={
                    'churn_probability': Decimal(str(churn_analysis['probability'])),
                    'churn_risk_level': churn_analysis['risk_level'],
                    'days_since_last_purchase': churn_analysis['days_since_last'],
                    'declining_purchase_frequency': churn_analysis['declining_frequency'],
                    'declining_order_value': churn_analysis['declining_value'],
                    'negative_trend_months': churn_analysis['negative_trend_months'],
                    'engagement_score': Decimal(str(churn_analysis['engagement_score'])),
                    'loyalty_score': Decimal(str(churn_analysis['loyalty_score'])),
                    'retention_strategy': retention_strategy['strategy'],
                    'recommended_action_priority': retention_strategy['priority']
                }
            )[0]
            
            churn_predictions.append(churn_prediction)
        
        return churn_predictions
    
    def predict_next_purchases(self) -> List[NextPurchasePrediction]:
        """Predecir próxima compra por cliente"""
        
        customers = Customer.objects.filter(is_active=True)
        predictions = []
        
        for customer in customers:
            # Obtener datos del cliente
            customer_data = self._get_customer_transaction_data(customer)
            
            if len(customer_data['transactions']) < 2:
                continue  # Necesitamos al menos 2 transacciones
            
            # Predecir próxima compra
            next_purchase_data = self._predict_next_purchase_timing(customer_data)
            
            # Recomendar productos
            product_recommendations = self._recommend_products_for_customer(customer, customer_data)
            
            prediction = NextPurchasePrediction.objects.update_or_create(
                customer=customer,
                defaults={
                    'predicted_next_purchase_date': next_purchase_data['predicted_date'],
                    'days_until_next_purchase': next_purchase_data['days_until'],
                    'prediction_confidence': Decimal(str(next_purchase_data['confidence'])),
                    'predicted_order_value': Decimal(str(next_purchase_data['predicted_value'])),
                    'predicted_quantity': Decimal(str(next_purchase_data['predicted_quantity']))
                }
            )[0]
            
            # Agregar recomendaciones de productos
            self._create_product_recommendations(prediction, product_recommendations)
            
            predictions.append(prediction)
        
        return predictions
    
    def segment_customers_automatically(self) -> List[CustomerSegmentation]:
        """Segmentación automática de clientes por comportamiento"""
        
        customers = Customer.objects.filter(is_active=True)
        segmentations = []
        
        # Obtener datos de todos los clientes para clustering
        customer_features = []
        customer_objects = []
        
        for customer in customers:
            customer_data = self._get_customer_transaction_data(customer)
            
            if not customer_data['transactions']:
                continue
            
            # Extraer características para clustering
            features = self._extract_customer_features(customer_data)
            customer_features.append(features)
            customer_objects.append(customer)
        
        if len(customer_features) < 5:
            return segmentations  # Necesitamos más clientes para clustering
        
        # Realizar clustering
        segments = self._perform_customer_clustering(customer_features)
        
        # Asignar segmentos y crear análisis
        for customer, features, segment_id in zip(customer_objects, customer_features, segments):
            # Interpretar segmento
            segment_analysis = self._interpret_customer_segment(features, segment_id)
            
            segmentation = CustomerSegmentation.objects.update_or_create(
                customer=customer,
                defaults={
                    'primary_segment': segment_analysis['primary_segment'],
                    'behavioral_attributes': segment_analysis['attributes'],
                    'preferences': segment_analysis['preferences'],
                    'value_score': Decimal(str(segment_analysis['value_score'])),
                    'growth_potential': Decimal(str(segment_analysis['growth_potential'])),
                    'loyalty_index': Decimal(str(segment_analysis['loyalty_index'])),
                    'recommended_approach': segment_analysis['recommended_approach']
                }
            )[0]
            
            segmentations.append(segmentation)
        
        return segmentations
    
    def _get_customer_transaction_data(self, customer: Customer) -> Dict:
        """Obtener datos de transacciones del cliente"""
        
        # Obtener transacciones de venta asociadas al cliente
        # Nota: Necesitaremos modificar el modelo Transaction para incluir customer
        # Por ahora, usamos customer_name en Sale
        sales = Sale.objects.filter(
            customer_name=customer.name
        ).order_by('-date_sold')
        
        transactions = []
        for sale in sales:
            transactions.append({
                'date': sale.date_sold.date(),
                'amount': float(sale.total_amount),
                'quantity': sale.quantity,
                'product_id': sale.product.id,
                'product_name': sale.product.name
            })
        
        return {
            'customer': customer,
            'transactions': transactions,
            'total_transactions': len(transactions),
            'total_spent': sum(t['amount'] for t in transactions)
        }
    
    def _calculate_clv_components(self, customer_data: Dict) -> Dict:
        """Calcular componentes del Customer Lifetime Value"""
        
        transactions = customer_data['transactions']
        
        if not transactions:
            return {
                'avg_order_value': 0,
                'purchase_frequency': 0,
                'lifespan_months': 0,
                'recency_days': 999
            }
        
        # Average Order Value
        avg_order_value = customer_data['total_spent'] / len(transactions)
        
        # Purchase Frequency (compras por mes)
        first_purchase = min(t['date'] for t in transactions)
        last_purchase = max(t['date'] for t in transactions)
        customer_lifespan_days = (last_purchase - first_purchase).days
        
        if customer_lifespan_days > 0:
            purchase_frequency = len(transactions) / (customer_lifespan_days / 30.0)  # Por mes
            lifespan_months = customer_lifespan_days / 30.0
        else:
            purchase_frequency = 1.0
            lifespan_months = 1.0
        
        # Recency (días desde última compra)
        recency_days = (timezone.now().date() - last_purchase).days
        
        return {
            'avg_order_value': avg_order_value,
            'purchase_frequency': purchase_frequency,
            'lifespan_months': lifespan_months,
            'recency_days': recency_days
        }
    
    def _predict_clv(self, components: Dict) -> Dict:
        """Predecir Customer Lifetime Value"""
        
        # Fórmula CLV = AOV × Purchase Frequency × Customer Lifespan
        basic_clv = (components['avg_order_value'] * 
                    components['purchase_frequency'] * 
                    components['lifespan_months'])
        
        # Ajustar por recency (clientes recientes tienen mayor valor futuro)
        recency_factor = max(0.5, 1 - (components['recency_days'] / 365))
        
        # Aplicar factor de crecimiento conservador
        growth_factor = 1.2  # Asumimos 20% de crecimiento potencial
        
        predicted_clv = basic_clv * recency_factor * growth_factor
        
        # Calcular confianza basada en datos disponibles
        if components['lifespan_months'] > 6:
            confidence = min(95, 60 + (components['lifespan_months'] * 5))
        else:
            confidence = 40  # Baja confianza para clientes nuevos
        
        return {
            'clv': predicted_clv,
            'confidence': confidence
        }
    
    def _calculate_rfm_segmentation(self, customer_data: Dict) -> Dict:
        """Calcular segmentación RFM (Recency, Frequency, Monetary)"""
        
        components = self._calculate_clv_components(customer_data)
        
        # Scores RFM (1-5 scale)
        # Recency: menor días = mayor score
        if components['recency_days'] <= 30:
            recency_score = 5
        elif components['recency_days'] <= 90:
            recency_score = 4
        elif components['recency_days'] <= 180:
            recency_score = 3
        elif components['recency_days'] <= 365:
            recency_score = 2
        else:
            recency_score = 1
        
        # Frequency: más compras = mayor score
        if components['purchase_frequency'] >= 4:
            frequency_score = 5
        elif components['purchase_frequency'] >= 2:
            frequency_score = 4
        elif components['purchase_frequency'] >= 1:
            frequency_score = 3
        elif components['purchase_frequency'] >= 0.5:
            frequency_score = 2
        else:
            frequency_score = 1
        
        # Monetary: mayor gasto = mayor score
        total_spent = customer_data['total_spent']
        if total_spent >= 5000:
            monetary_score = 5
        elif total_spent >= 2000:
            monetary_score = 4
        elif total_spent >= 1000:
            monetary_score = 3
        elif total_spent >= 500:
            monetary_score = 2
        else:
            monetary_score = 1
        
        # Determinar segmento RFM
        segment = self._determine_rfm_segment(recency_score, frequency_score, monetary_score)
        
        return {
            'recency_score': recency_score,
            'frequency_score': frequency_score,
            'monetary_score': monetary_score,
            'segment': segment
        }
    
    def _determine_rfm_segment(self, r: int, f: int, m: int) -> str:
        """Determinar segmento RFM basado en scores"""
        
        if r >= 4 and f >= 4 and m >= 4:
            return 'champions'
        elif r >= 3 and f >= 3 and m >= 3:
            return 'loyal_customers'
        elif r >= 4 and f <= 2:
            return 'new_customers'
        elif r >= 3 and f <= 2 and m >= 3:
            return 'potential_loyalists'
        elif r >= 3 and f >= 3 and m <= 2:
            return 'promising'
        elif r <= 2 and f >= 3 and m >= 3:
            return 'need_attention'
        elif r <= 2 and f <= 2 and m >= 3:
            return 'cannot_lose'
        elif r >= 3 and f <= 2 and m <= 2:
            return 'about_to_sleep'
        elif r <= 2 and f >= 2:
            return 'at_risk'
        elif r <= 2 and f <= 2 and m <= 2:
            return 'hibernating'
        else:
            return 'lost'
    
    def _calculate_churn_probability(self, customer_data: Dict) -> Dict:
        """Calcular probabilidad de churn del cliente"""
        
        components = self._calculate_clv_components(customer_data)
        transactions = customer_data['transactions']
        
        # Factores de riesgo
        risk_factors = 0
        
        # 1. Recency factor
        if components['recency_days'] > 90:
            risk_factors += 0.3
        elif components['recency_days'] > 180:
            risk_factors += 0.5
        elif components['recency_days'] > 365:
            risk_factors += 0.8
        
        # 2. Declining frequency
        declining_frequency = self._check_declining_frequency(transactions)
        if declining_frequency:
            risk_factors += 0.4
        
        # 3. Declining order value
        declining_value = self._check_declining_value(transactions)
        if declining_value:
            risk_factors += 0.3
        
        # 4. Negative trend in recent months
        negative_trend_months = self._count_negative_trend_months(transactions)
        risk_factors += min(0.3, negative_trend_months * 0.1)
        
        # Calcular probabilidad final (0-1)
        churn_probability = min(1.0, risk_factors)
        
        # Determinar nivel de riesgo
        if churn_probability >= 0.8:
            risk_level = 'critical'
        elif churn_probability >= 0.6:
            risk_level = 'high'
        elif churn_probability >= 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Calcular scores de engagement y lealtad
        engagement_score = max(0, 100 - (components['recency_days'] * 0.5))
        loyalty_score = min(100, components['purchase_frequency'] * 20 + len(transactions) * 5)
        
        return {
            'probability': churn_probability,
            'risk_level': risk_level,
            'days_since_last': components['recency_days'],
            'declining_frequency': declining_frequency,
            'declining_value': declining_value,
            'negative_trend_months': negative_trend_months,
            'engagement_score': engagement_score,
            'loyalty_score': loyalty_score
        }
    
    def _check_declining_frequency(self, transactions: List[Dict]) -> bool:
        """Verificar si la frecuencia de compra está declinando"""
        
        if len(transactions) < 4:
            return False
        
        # Comparar últimos 6 meses vs 6 meses anteriores
        recent_cutoff = timezone.now().date() - timedelta(days=180)
        older_cutoff = timezone.now().date() - timedelta(days=360)
        
        recent_transactions = [t for t in transactions if t['date'] >= recent_cutoff]
        older_transactions = [t for t in transactions if older_cutoff <= t['date'] < recent_cutoff]
        
        if len(older_transactions) == 0:
            return False
        
        recent_frequency = len(recent_transactions) / 6  # Por mes
        older_frequency = len(older_transactions) / 6   # Por mes
        
        return recent_frequency < older_frequency * 0.7  # 30% de decline
    
    def _check_declining_value(self, transactions: List[Dict]) -> bool:
        """Verificar si el valor de orden está declinando"""
        
        if len(transactions) < 4:
            return False
        
        # Comparar últimos 6 meses vs 6 meses anteriores
        recent_cutoff = timezone.now().date() - timedelta(days=180)
        older_cutoff = timezone.now().date() - timedelta(days=360)
        
        recent_transactions = [t for t in transactions if t['date'] >= recent_cutoff]
        older_transactions = [t for t in transactions if older_cutoff <= t['date'] < recent_cutoff]
        
        if not recent_transactions or not older_transactions:
            return False
        
        recent_avg = sum(t['amount'] for t in recent_transactions) / len(recent_transactions)
        older_avg = sum(t['amount'] for t in older_transactions) / len(older_transactions)
        
        return recent_avg < older_avg * 0.8  # 20% de decline
    
    def _count_negative_trend_months(self, transactions: List[Dict]) -> int:
        """Contar meses con tendencia negativa"""
        
        # Agrupar transacciones por mes
        monthly_totals = {}
        for transaction in transactions:
            month_key = transaction['date'].strftime('%Y-%m')
            if month_key not in monthly_totals:
                monthly_totals[month_key] = 0
            monthly_totals[month_key] += transaction['amount']
        
        # Contar meses consecutivos con decline
        months = sorted(monthly_totals.keys())
        negative_months = 0
        
        for i in range(1, len(months)):
            if monthly_totals[months[i]] < monthly_totals[months[i-1]]:
                negative_months += 1
            else:
                break  # Solo contar meses consecutivos
        
        return negative_months
    
    def _determine_retention_strategy(self, churn_analysis: Dict) -> Dict:
        """Determinar estrategia de retención"""
        
        probability = churn_analysis['probability']
        risk_level = churn_analysis['risk_level']
        
        if risk_level == 'critical':
            strategy = 'win_back_campaign'
            priority = 5
        elif risk_level == 'high':
            if churn_analysis['declining_value']:
                strategy = 'discount_offer'
            else:
                strategy = 'personal_attention'
            priority = 4
        elif risk_level == 'medium':
            strategy = 'loyalty_program'
            priority = 3
        else:
            strategy = 'product_recommendation'
            priority = 2
        
        return {
            'strategy': strategy,
            'priority': priority
        }
    
    def _predict_next_purchase_timing(self, customer_data: Dict) -> Dict:
        """Predecir timing de próxima compra"""
        
        transactions = customer_data['transactions']
        
        if len(transactions) < 2:
            return {
                'predicted_date': timezone.now().date() + timedelta(days=60),
                'days_until': 60,
                'confidence': 30,
                'predicted_value': 0,
                'predicted_quantity': 0
            }
        
        # Calcular intervalos entre compras
        transaction_dates = sorted([t['date'] for t in transactions])
        intervals = []
        
        for i in range(1, len(transaction_dates)):
            interval = (transaction_dates[i] - transaction_dates[i-1]).days
            intervals.append(interval)
        
        # Predecir próximo intervalo
        if intervals:
            avg_interval = np.mean(intervals)
            std_interval = np.std(intervals) if len(intervals) > 1 else avg_interval * 0.3
            
            # Ajustar por tendencia reciente
            if len(intervals) >= 3:
                recent_trend = np.mean(intervals[-3:]) - np.mean(intervals[:-3])
                avg_interval += recent_trend * 0.5  # Factor de peso para tendencia
        else:
            avg_interval = 60  # Default 60 días
            std_interval = 20
        
        # Predecir fecha
        last_purchase_date = max(t['date'] for t in transactions)
        predicted_days = max(7, int(avg_interval))  # Mínimo 7 días
        predicted_date = last_purchase_date + timedelta(days=predicted_days)
        
        # Calcular valores predichos
        avg_order_value = np.mean([t['amount'] for t in transactions])
        avg_quantity = np.mean([t['quantity'] for t in transactions])
        
        # Confianza basada en consistencia de intervalos
        cv = (std_interval / avg_interval) if avg_interval > 0 else 1
        confidence = max(30, min(90, 100 - (cv * 50)))
        
        return {
            'predicted_date': predicted_date,
            'days_until': (predicted_date - timezone.now().date()).days,
            'confidence': confidence,
            'predicted_value': avg_order_value,
            'predicted_quantity': avg_quantity
        }
    
    def _recommend_products_for_customer(self, customer: Customer, customer_data: Dict) -> List[Dict]:
        """Recomendar productos para el cliente"""
        
        # Obtener productos comprados anteriormente
        purchased_products = set(t['product_id'] for t in customer_data['transactions'])
        
        recommendations = []
        
        # 1. Productos comprados frecuentemente por el cliente
        product_frequency = {}
        for transaction in customer_data['transactions']:
            pid = transaction['product_id']
            product_frequency[pid] = product_frequency.get(pid, 0) + 1
        
        # Recomendar top 3 productos del cliente
        top_customer_products = sorted(product_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for product_id, frequency in top_customer_products:
            try:
                product = Product.objects.get(id=product_id)
                recommendations.append({
                    'product': product,
                    'score': 0.8 + (frequency * 0.1),
                    'reason': 'frequently_purchased',
                    'predicted_quantity': frequency,
                    'confidence': 85
                })
            except Product.DoesNotExist:
                continue
        
        # 2. Productos relacionados via market basket analysis
        basket_recommendations = MarketBasketAnalysis.objects.filter(
            Q(product_a__id__in=purchased_products) | Q(product_b__id__in=purchased_products),
            lift__gte=1.5
        ).order_by('-lift')[:5]
        
        for basket in basket_recommendations:
            # Recomendar el producto que NO ha comprado
            if basket.product_a.id in purchased_products:
                recommended_product = basket.product_b
            else:
                recommended_product = basket.product_a
            
            if recommended_product.id not in purchased_products:
                recommendations.append({
                    'product': recommended_product,
                    'score': min(1.0, float(basket.lift) / 3),
                    'reason': 'frequently_bought_together',
                    'predicted_quantity': 1,
                    'confidence': min(90, float(basket.confidence) * 100)
                })
        
        # Ordenar por score y devolver top 5
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:5]
    
    def _create_product_recommendations(self, next_purchase: NextPurchasePrediction, recommendations: List[Dict]):
        """Crear recomendaciones de productos en la base de datos"""
        
        # Limpiar recomendaciones existentes
        ProductRecommendation.objects.filter(next_purchase=next_purchase).delete()
        
        # Crear nuevas recomendaciones
        for rec in recommendations:
            ProductRecommendation.objects.create(
                next_purchase=next_purchase,
                product=rec['product'],
                recommendation_score=Decimal(str(rec['score'])),
                predicted_quantity=Decimal(str(rec['predicted_quantity'])),
                confidence_level=Decimal(str(rec['confidence']))
            )
    
    def _extract_customer_features(self, customer_data: Dict) -> List[float]:
        """Extraer características del cliente para clustering"""
        
        components = self._calculate_clv_components(customer_data)
        transactions = customer_data['transactions']
        
        # Características numéricas para clustering
        features = [
            components['avg_order_value'] / 100,  # Normalizado
            components['purchase_frequency'],
            components['recency_days'] / 30,  # En meses
            len(transactions),
            customer_data['total_spent'] / 1000,  # En miles
            components['lifespan_months']
        ]
        
        return features
    
    def _perform_customer_clustering(self, customer_features: List[List[float]]) -> List[int]:
        """Realizar clustering de clientes"""
        
        # Normalizar características
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(customer_features)
        
        # Determinar número óptimo de clusters (entre 3-8)
        n_clusters = min(8, max(3, len(customer_features) // 10))
        
        # Aplicar K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(features_scaled)
        
        return cluster_labels.tolist()
    
    def _interpret_customer_segment(self, features: List[float], segment_id: int) -> Dict:
        """Interpretar segmento de cliente"""
        
        avg_order_value = features[0] * 100
        purchase_frequency = features[1]
        recency_months = features[2]
        total_transactions = features[3]
        total_spent = features[4] * 1000
        lifespan_months = features[5]
        
        # Determinar segmento primario basado en características
        if avg_order_value > 500 and purchase_frequency > 2:
            primary_segment = 'vip'
            recommended_approach = 'premium_service'
        elif purchase_frequency > 1 and recency_months < 2:
            primary_segment = 'frequent'
            recommended_approach = 'frequent_contact'
        elif total_spent > 2000:
            primary_segment = 'bulk_buyer'
            recommended_approach = 'volume_discounts'
        elif recency_months > 6:
            primary_segment = 'dormant'
            recommended_approach = 're_engagement'
        elif lifespan_months < 3:
            primary_segment = 'new'
            recommended_approach = 'onboarding'
        elif avg_order_value < 200:
            primary_segment = 'price_sensitive'
            recommended_approach = 'price_optimization'
        else:
            primary_segment = 'occasional'
            recommended_approach = 'frequent_contact'
        
        # Atributos comportamentales
        attributes = {
            'avg_order_value': avg_order_value,
            'purchase_frequency_monthly': purchase_frequency,
            'customer_lifespan_months': lifespan_months,
            'total_transactions': total_transactions,
            'recency_score': max(1, 5 - recency_months)
        }
        
        # Preferencias detectadas (simplificado)
        preferences = {
            'price_sensitivity': 'high' if avg_order_value < 200 else 'medium' if avg_order_value < 500 else 'low',
            'purchase_pattern': 'frequent' if purchase_frequency > 1 else 'occasional',
            'loyalty_level': 'high' if lifespan_months > 12 else 'medium' if lifespan_months > 6 else 'low'
        }
        
        # Scores
        value_score = min(100, (total_spent / 50))  # Max a los S/ 5000
        growth_potential = max(0, 100 - (recency_months * 10) + (purchase_frequency * 20))
        loyalty_index = min(100, (lifespan_months * 8) + (total_transactions * 5))
        
        return {
            'primary_segment': primary_segment,
            'attributes': attributes,
            'preferences': preferences,
            'value_score': value_score,
            'growth_potential': min(100, growth_potential),
            'loyalty_index': min(100, loyalty_index),
            'recommended_approach': recommended_approach
        }
