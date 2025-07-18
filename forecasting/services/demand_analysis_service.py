"""
Servicio para análisis sofisticado de demanda
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.db.models import Sum, Avg, Count, F, Q, Max, Min
from django.utils import timezone
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics.pairwise import cosine_similarity
import logging

from ..models import (
    SeasonalityPattern, PriceElasticityAnalysis, TrendingProductPrediction,
    MarketBasketAnalysis, ProductRecommendation, PriceElasticity
)
from inventory.models import Product, Sale, Transaction
from authentication.models import Company

logger = logging.getLogger(__name__)


class DemandAnalysisService:
    """Servicio para análisis sofisticado de demanda"""
    
    def __init__(self, company: Company):
        self.company = company
    
    def analyze_seasonal_patterns(self, product_id: int = None) -> List[SeasonalityPattern]:
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
            
            # Crear patrón estacional usando SeasonalityPattern
            analysis = SeasonalityPattern.objects.update_or_create(
                company=self.company,  # Agregar company requerido
                product=product,
                pattern_type='monthly',  # Usar uno de los tipos válidos
                defaults={
                    'pattern_strength': Decimal(str(pattern_strength)),
                    'peak_periods': monthly_patterns.get('peak_months', []),
                    'low_periods': monthly_patterns.get('low_months', []),
                    'seasonal_multipliers': seasonal_analysis,
                    'data_points_analyzed': len(historical_demand),
                    'pattern_confidence': Decimal(str(predictability * 100)),
                    'next_peak_date': None,  # Se puede calcular después
                    'next_low_date': None
                }
            )[0]
            
            analyses.append(analysis)
        
        return analyses
    
    def perform_market_basket_analysis(self, min_support: float = 0.01) -> List[MarketBasketAnalysis]:
        """Realizar análisis de productos que se venden juntos"""
        
        # Obtener ventas agrupadas por fecha/hora exacta y cliente
        sales = Sale.objects.filter(
            product__company=self.company,
            date_sold__gte=timezone.now() - timedelta(days=365)
        ).values('date_sold', 'customer_name', 'product_id').distinct()
        
        # Agrupar por transacción (mismo timestamp exacto + mismo cliente)
        transaction_groups = self._group_sales_for_basket_analysis(sales)
        
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
                    
                    analysis, created = MarketBasketAnalysis.objects.get_or_create(
                        product_a=product_a,
                        product_b=product_b,
                        company=self.company,
                        analysis_start_date=timezone.now().date() - timedelta(days=365),
                        analysis_end_date=timezone.now().date(),
                        defaults={
                            'support': Decimal(str(metrics['support'])),
                            'confidence': Decimal(str(metrics['confidence'])),
                            'lift': Decimal(str(metrics['lift'])),
                            'transactions_with_both': metrics['transactions_together'],
                            'transactions_with_a': metrics.get('transactions_a', metrics['transactions_together']),
                            'total_transactions': len(transaction_groups),
                            'recommendation_strength': strength,
                        }
                    )
                    
                    # Actualizar si ya existe
                    if not created:
                        analysis.support = Decimal(str(metrics['support']))
                        analysis.confidence = Decimal(str(metrics['confidence']))
                        analysis.lift = Decimal(str(metrics['lift']))
                        analysis.transactions_with_both = metrics['transactions_together']
                        analysis.transactions_with_a = metrics.get('transactions_a', metrics['transactions_together'])
                        analysis.total_transactions = len(transaction_groups)
                        analysis.recommendation_strength = strength
                        analysis.save()
                    
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
    
    def _group_sales_for_basket_analysis(self, sales) -> List[List[int]]:
        """Agrupar ventas para análisis de market basket"""
        
        # Agrupar por timestamp exacto y cliente
        groups = {}
        
        for sale in sales:
            # Crear clave única por transacción (mismo momento + mismo cliente)
            key = f"{sale['customer_name']}_{sale['date_sold']}"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(sale['product_id'])
        
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
            'transactions_together': transactions_both,
            'transactions_a': transactions_a
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
    
    def calculate_price_elasticity(self) -> List[PriceElasticity]:
        """Calcular elasticidad precio-demanda para productos"""
        
        products = Product.objects.filter(company=self.company)
        elasticity_analyses = []
        
        for product in products:
            # Obtener datos históricos de precios y ventas
            price_demand_data = self._get_price_demand_data(product)
            
            if len(price_demand_data) < 10:  # Mínimo 10 puntos de datos
                continue
            
            # Calcular elasticidad precio-demanda
            elasticity_coefficient = self._calculate_elasticity_coefficient(price_demand_data)
            
            # Determinar categoría de elasticidad
            elasticity_category = self._categorize_elasticity(elasticity_coefficient)
            
            # Calcular precio óptimo sugerido
            optimal_price = self._calculate_optimal_price(product, elasticity_coefficient)
            
            analysis = PriceElasticity.objects.update_or_create(
                product=product,
                defaults={
                    'elasticity_coefficient': Decimal(str(elasticity_coefficient)),
                    'demand_sensitivity': elasticity_category,
                    'optimal_price': Decimal(str(optimal_price)),
                    'current_price': product.sale_price or Decimal('0'),
                    'recommended_price_change': Decimal(str((optimal_price / float(product.sale_price or 1) - 1) * 100)),
                    'estimated_demand_change': Decimal(str(elasticity_coefficient * 10)),  # Estimación simple
                    'estimated_revenue_impact': Decimal(str(optimal_price * 100)),  # Estimación simple
                    'analysis_period_days': 365,
                    'price_points_analyzed': len(price_demand_data)
                }
            )[0]
            
            elasticity_analyses.append(analysis)
        
        return elasticity_analyses
    
    def _get_price_demand_data(self, product: Product) -> List[Dict]:
        """Obtener datos históricos de precio y demanda"""
        
        # Obtener ventas históricas
        sales_data = Sale.objects.filter(
            product=product,
            date_sold__gte=timezone.now().date() - timedelta(days=365)
        ).order_by('date_sold')
        
        price_demand_points = []
        for sale in sales_data:
            price_demand_points.append({
                'price': float(sale.unit_price),
                'quantity': sale.quantity,
                'date': sale.date_sold
            })
        
        return price_demand_points
    
    def _calculate_elasticity_coefficient(self, price_demand_data: List[Dict]) -> float:
        """Calcular coeficiente de elasticidad precio-demanda"""
        
        if len(price_demand_data) < 2:
            return 0.0
        
        # Calcular elasticidad usando correlación entre precio y cantidad
        prices = [point['price'] for point in price_demand_data]
        quantities = [point['quantity'] for point in price_demand_data]
        
        # Elasticidad simplificada: correlación negativa entre precio y cantidad
        try:
            correlation = np.corrcoef(prices, quantities)[0, 1]
            elasticity = abs(correlation) if not np.isnan(correlation) else 0.0
            return min(2.0, max(0.0, elasticity))  # Limitar entre 0 y 2
        except:
            return 0.0
    
    def _categorize_elasticity(self, elasticity_coefficient: float) -> str:
        """Categorizar elasticidad"""
        
        if elasticity_coefficient > 1.0:
            return 'elastic'
        elif elasticity_coefficient > 0.5:
            return 'unit_elastic'
        else:
            return 'inelastic'
    
    def _calculate_optimal_price(self, product: Product, elasticity: float) -> float:
        """Calcular precio óptimo sugerido"""
        
        current_price = float(product.sale_price or 0)
        if current_price == 0:
            return 0
        
        # Ajuste simple basado en elasticidad
        if elasticity > 1.0:  # Elástico - reducir precio
            return current_price * 0.95
        elif elasticity < 0.5:  # Inelástico - aumentar precio
            return current_price * 1.05
        else:  # Elasticidad unitaria - mantener precio
            return current_price
