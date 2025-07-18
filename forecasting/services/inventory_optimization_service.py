"""
Servicio de Optimización de Inventario - DataLens
Algoritmos avanzados para optimización inteligente de inventario, predicción de stockouts
y análisis EOQ con clasificación ABC automática.

FIXED VERSION - Usa los modelos correctos que existen en la BD
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
# FIX: Usar los modelos correctos que SÍ existen
from forecasting.models import (
    StockLevelRecommendation, InventoryOptimizationModel
)


class InventoryOptimizationService:
    """Servicio para optimización inteligente de inventario"""
    
    def __init__(self, company: Company):
        self.company = company
    
    def calculate_optimal_stock_levels(self) -> List[StockLevelRecommendation]:
        """Calcular niveles de stock óptimos matemáticamente"""
        
        products = Product.objects.filter(company=self.company, is_active=True)
        optimal_levels = []
        
        # FIX: Crear o usar un modelo de optimización por defecto
        optimization_model, created = InventoryOptimizationModel.objects.get_or_create(
            company=self.company,
            model_type='eoq_optimization',
            defaults={
                'optimization_algorithm': 'Enhanced EOQ with Safety Stock',
                'is_active': True,
                'parameters': {
                    'service_level': 95.0,
                    'lead_time_days': 7,
                    'holding_cost_rate': 0.25,
                    'ordering_cost': 100.0
                }
            }
        )
        
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
            
            # Clasificación ABC automática
            abc_data = self._calculate_abc_classification(product, demand_data)
            
            # Determinar prioridad de recomendación
            current_stock = float(product.stock or 0)
            if current_stock <= reorder_point:
                priority = 'high' if current_stock <= safety_stock else 'medium'
            else:
                priority = 'low'
            
            # FIX: Usar StockLevelRecommendation en lugar de OptimalStockLevel
            optimal_level = StockLevelRecommendation.objects.update_or_create(
                product=product,
                model=optimization_model,
                defaults={
                    'recommendation_type': 'eoq_optimization',
                    'recommended_stock': float(optimal_quantity),
                    'current_stock': current_stock,
                    'safety_stock': float(safety_stock),
                    'priority': priority
                }
            )[0]
            
            # Agregar atributos adicionales para compatibilidad
            optimal_level.abc_classification = abc_data['classification']
            optimal_level.reorder_point = reorder_point
            optimal_level.economic_order_quantity = optimal_quantity
            
            optimal_levels.append(optimal_level)
        
        return optimal_levels
    
    def predict_stockouts(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Predecir quiebres de stock con anticipación
        FIX: Retorna diccionarios en lugar de objetos DB que no existen
        """
        
        products = Product.objects.filter(company=self.company, is_active=True)
        predictions = []
        
        for product in products:
            # Obtener datos de demanda y stock actuales
            current_stock = float(product.stock or 0)
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
                
                # FIX: Crear diccionario de predicción en lugar de objeto DB
                prediction_dict = {
                    'product_id': product.id,
                    'product_name': product.name,
                    'prediction_date': timezone.now().date(),
                    'predicted_stockout_date': stockout_prediction['stockout_date'],
                    'stockout_probability': stockout_prediction['confidence'] / 100,
                    'days_until_stockout': stockout_prediction['days_until_stockout'],
                    'current_stock': current_stock,
                    'predicted_demand': demand_data['average_demand'] * days_ahead,
                    'priority': alert_priority,
                    'estimated_lost_revenue': impact_data['estimated_lost_sales'],
                    'customer_impact_score': impact_data['customer_impact_score']
                }
                
                predictions.append(prediction_dict)
        
        return predictions
    
    def comprehensive_inventory_optimization(self, company: Company, **kwargs) -> Dict[str, Any]:
        """
        FIX: Método que faltaba en el servicio original
        Análisis completo de optimización de inventario
        """
        try:
            # Calcular niveles de stock óptimos
            stock_levels = self.calculate_optimal_stock_levels()
            
            # Predecir stockouts
            stockout_predictions = self.predict_stockouts(
                days_ahead=kwargs.get('days_ahead', 30)
            )
            
            # Análisis de clasificación ABC
            abc_analysis = self._perform_abc_analysis()
            
            # Calcular métricas de resumen
            summary_metrics = self._calculate_optimization_summary(
                stock_levels, stockout_predictions, abc_analysis
            )
            
            # Recomendaciones de acción
            action_recommendations = self._generate_action_recommendations(
                stock_levels, stockout_predictions
            )
            
            return {
                'stock_levels': [self._serialize_stock_level(level) for level in stock_levels],
                'stockout_predictions': stockout_predictions,
                'abc_analysis': abc_analysis,
                'summary_metrics': summary_metrics,
                'action_recommendations': action_recommendations,
                'optimization_date': timezone.now().date(),
                'total_products_analyzed': len(stock_levels),
                'high_priority_alerts': len([p for p in stockout_predictions if p['priority'] in ['critical', 'high']])
            }
            
        except Exception as e:
            logger.error(f"Error en optimización completa: {str(e)}")
            raise
    
    def _serialize_stock_level(self, stock_level: StockLevelRecommendation) -> Dict[str, Any]:
        """Serializar recomendación de stock a diccionario"""
        return {
            'product_id': stock_level.product.id,
            'product_name': stock_level.product.name,
            'recommendation_type': stock_level.recommendation_type,
            'recommended_stock': float(stock_level.recommended_stock),
            'current_stock': float(stock_level.current_stock),
            'safety_stock': float(stock_level.safety_stock),
            'priority': stock_level.priority,
            'abc_classification': getattr(stock_level, 'abc_classification', 'C'),
            'reorder_point': getattr(stock_level, 'reorder_point', 0),
            'economic_order_quantity': getattr(stock_level, 'economic_order_quantity', 0)
        }
    
    def _perform_abc_analysis(self) -> Dict[str, Any]:
        """Realizar análisis ABC completo"""
        products = Product.objects.filter(company=self.company, is_active=True)
        
        abc_counts = {'A': 0, 'B': 0, 'C': 0}
        total_value = 0
        product_values = []
        
        for product in products:
            demand_data = self._get_demand_statistics(product)
            abc_data = self._calculate_abc_classification(product, demand_data)
            
            abc_counts[abc_data['classification']] += 1
            
            annual_demand = demand_data['average_demand'] * 365
            unit_value = float(product.cost_price) if product.cost_price else 0
            annual_value = annual_demand * unit_value
            total_value += annual_value
            
            product_values.append({
                'product_id': product.id,
                'product_name': product.name,
                'classification': abc_data['classification'],
                'annual_value': annual_value,
                'annual_demand': annual_demand
            })
        
        return {
            'classification_counts': abc_counts,
            'total_annual_value': total_value,
            'product_details': sorted(product_values, key=lambda x: x['annual_value'], reverse=True)
        }
    
    def _calculate_optimization_summary(self, stock_levels, stockout_predictions, abc_analysis) -> Dict[str, Any]:
        """Calcular métricas de resumen de optimización"""
        
        # Calcular ahorros potenciales
        total_current_cost = 0
        total_optimal_cost = 0
        
        for level in stock_levels:
            product = level.product
            demand_data = self._get_demand_statistics(product)
            cost_data = self._get_cost_parameters(product)
            
            current_cost = self._calculate_current_inventory_cost(product, demand_data, cost_data)
            optimal_cost = self._calculate_optimal_inventory_cost(
                getattr(level, 'economic_order_quantity', level.recommended_stock),
                demand_data, cost_data
            )
            
            total_current_cost += current_cost
            total_optimal_cost += optimal_cost
        
        potential_savings = max(0, total_current_cost - total_optimal_cost)
        
        # Calcular estadísticas de stockout
        critical_stockouts = len([p for p in stockout_predictions if p['priority'] == 'critical'])
        high_stockouts = len([p for p in stockout_predictions if p['priority'] == 'high'])
        
        return {
            'total_products': len(stock_levels),
            'products_needing_reorder': len([l for l in stock_levels if l.priority in ['high', 'medium']]),
            'potential_annual_savings': potential_savings,
            'current_annual_cost': total_current_cost,
            'optimal_annual_cost': total_optimal_cost,
            'critical_stockout_alerts': critical_stockouts,
            'high_priority_stockout_alerts': high_stockouts,
            'abc_class_a_products': abc_analysis['classification_counts']['A'],
            'abc_class_b_products': abc_analysis['classification_counts']['B'],
            'abc_class_c_products': abc_analysis['classification_counts']['C']
        }
    
    def _generate_action_recommendations(self, stock_levels, stockout_predictions) -> List[Dict[str, Any]]:
        """Generar recomendaciones de acción específicas"""
        
        recommendations = []
        
        # Recomendaciones de reorden urgente
        urgent_reorders = [l for l in stock_levels if l.priority == 'high']
        for level in urgent_reorders[:5]:  # Top 5 más urgentes
            recommendations.append({
                'type': 'urgent_reorder',
                'priority': 'high',
                'product_name': level.product.name,
                'action': f'Ordenar {level.recommended_stock:.0f} unidades inmediatamente',
                'reason': f'Stock actual ({level.current_stock:.0f}) por debajo del punto de reorden'
            })
        
        # Recomendaciones de stockout crítico
        critical_stockouts = [p for p in stockout_predictions if p['priority'] == 'critical']
        for pred in critical_stockouts[:3]:  # Top 3 más críticos
            recommendations.append({
                'type': 'critical_stockout',
                'priority': 'critical',
                'product_name': pred['product_name'],
                'action': f'Acción inmediata requerida - agotamiento en {pred["days_until_stockout"]} días',
                'reason': f'Alto impacto al cliente (score: {pred["customer_impact_score"]})'
            })
        
        # Recomendaciones de optimización
        if len(recommendations) < 10:
            overstock_items = [l for l in stock_levels if l.current_stock > l.recommended_stock * 1.5]
            for level in overstock_items[:3]:
                recommendations.append({
                    'type': 'reduce_stock',
                    'priority': 'medium',
                    'product_name': level.product.name,
                    'action': f'Considerar reducir stock a {level.recommended_stock:.0f} unidades',
                    'reason': f'Sobrepobación actual: {level.current_stock:.0f} vs recomendado: {level.recommended_stock:.0f}'
                })
        
        return recommendations[:10]  # Máximo 10 recomendaciones
    
    # ==================== MÉTODOS AUXILIARES (sin cambios) ====================
    
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
        
        current_stock = float(product.stock or 0)
        
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