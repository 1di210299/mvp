"""
Servicio de Optimización de Inventario - DataLens
Algoritmos avanzados para optimización inteligente de inventario, predicción de stockouts
y análisis EOQ con clasificación ABC automática.
"""

import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from django.utils import timezone
from django.db.models import Sum, Avg, Q

# Imports from Django models
from authentication.models import Company
from inventory.models import Product, Transaction
from forecasting.models import (
    OptimalStockLevel, StockoutPrediction
)


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
                    'optimal_stock': Decimal(str(optimal_quantity)),
                    'safety_stock': Decimal(str(safety_stock)),
                    'reorder_point': Decimal(str(reorder_point)),
                    'economic_order_quantity': Decimal(str(optimal_quantity)),
                    'holding_cost_rate': Decimal(str(cost_data['holding_cost'] / float(product.cost_price or 1))),
                    'ordering_cost': Decimal(str(cost_data['ordering_cost'])),
                    'stockout_cost': Decimal(str(cost_data['stockout_cost'])),
                    'avg_daily_demand': Decimal(str(demand_data['average_demand'])),
                    'demand_variability': Decimal(str(demand_data['demand_variability'])),
                    'lead_time_variability': Decimal(str(demand_data['lead_time_variability'])),
                    'expected_stockout_frequency': Decimal('0.05'),  # 5% target
                    'expected_annual_cost': Decimal(str(optimal_cost)),
                    'service_level': Decimal('95.00')
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
                    prediction_date=timezone.now().date(),
                    defaults={
                        'predicted_stockout_date': stockout_prediction['stockout_date'],
                        'stockout_probability': Decimal(str(stockout_prediction['confidence'] / 100)),
                        'days_until_stockout': stockout_prediction['days_until_stockout'],
                        'current_stock': Decimal(str(current_stock)),
                        'predicted_demand': Decimal(str(demand_data['average_demand'] * days_ahead))
                    }
                )[0]
                
                predictions.append(prediction)
        
        return predictions
    
    def _get_demand_statistics(self, product: Product, days_back: int = 365) -> Dict:
        """Obtener estadísticas de demanda para un producto"""
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Obtener ventas del producto (usar Sale en lugar de Transaction)
        from inventory.models import Sale
        sales = Sale.objects.filter(
            product=product,
            date_sold__range=[start_date, end_date]
        )
        
        if not sales.exists():
            return {
                'average_demand': 0,
                'demand_variability': 0,
                'lead_time_variability': 0.1,
                'seasonal_factor': 1.0
            }
        
        # Agrupar por día
        daily_demand = sales.extra(
            select={'date': 'DATE(date_sold)'}
        ).values('date').annotate(
            total_demand=Sum('quantity')
        )
        
        demands = [float(item['total_demand']) for item in daily_demand if item['total_demand'] is not None]
        
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
        from inventory.models import Sale
        sales_frequency = Sale.objects.filter(
            product=product,
            date_sold__gte=timezone.now().date() - timedelta(days=30)
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
