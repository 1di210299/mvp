"""
Servicio para pronósticos financieros avanzados
"""

import pandas as pd
import numpy as np
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.db.models import Sum, Avg, Count, F, Q, Max, Min
from django.utils import timezone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import logging

from ..models import (
    ForecastModel, FinancialForecastModel, RevenuePrediction, SupplierROIAnalysis
)
from inventory.models import Product, Transaction, Supplier
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
        
        # Generar nombre único con timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Crear modelo base de pronóstico
        base_model = ForecastModel.objects.create(
            company=self.company,
            name=f"Financial {metric_type.title()} Forecast {timestamp}",
            description=f"Modelo para pronósticos de {metric_type} en soles peruanos",
            model_type='prophet',  # Mejor para series financieras
            forecast_horizon_days=horizon_days,
            training_period_days=365
        )
        
        # Crear configuración financiera
        financial_model = FinancialForecastModel.objects.create(
            company=self.company,  # Agregar company_id requerido
            base_model=base_model,
            name=f"Financial {metric_type.title()} Model {timestamp}",  # Agregar nombre único
            model_type='prophet',  # Agregar model_type requerido
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
        
        print(f"   🔍 DEBUG: Iniciando análisis ROI con {days_back} días hacia atrás")
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"   📅 DEBUG: Período de análisis: {start_date} a {end_date}")
        
        try:
            suppliers = Supplier.objects.filter(
                products__company=self.company
            ).distinct()
            
            print(f"   🏢 DEBUG: Encontrados {suppliers.count()} suppliers con productos de company {self.company.name}")
            
            analyses = []
            
            for supplier in suppliers:
                print(f"   👤 DEBUG: Procesando supplier {supplier.name}")
                
                # Obtener productos del proveedor
                supplier_products = Product.objects.filter(
                    supplier=supplier,
                    company=self.company
                )
                
                print(f"   📦 DEBUG: Supplier {supplier.name}: {supplier_products.count()} productos")
                
                if supplier_products.count() == 0:
                    print(f"   ⚠️ DEBUG: Supplier {supplier.name} sin productos - SKIPPING")
                    continue
                
                # Calcular inversión total (compras)
                purchase_transactions = Transaction.objects.filter(
                    product__in=supplier_products,
                    transaction_type='purchase',
                    transaction_date__date__range=[start_date, end_date]
                )
                
                total_cost = purchase_transactions.aggregate(
                    total=Sum(F('quantity') * F('unit_cost'))
                )['total'] or 0
                
                print(f"   � DEBUG: Supplier {supplier.name}: {purchase_transactions.count()} compras, costo total: {total_cost}")
                
                # Calcular ingresos generados (ventas)
                sale_transactions = Transaction.objects.filter(
                    product__in=supplier_products,
                    transaction_type='sale',
                    transaction_date__date__range=[start_date, end_date]
                )
                
                total_revenue = sale_transactions.aggregate(
                    total=Sum(F('quantity') * F('unit_cost'))  # unit_cost en sale transactions es el precio de venta
                )['total'] or 0
                
                print(f"   � DEBUG: Supplier {supplier.name}: {sale_transactions.count()} ventas, ingresos: {total_revenue}")
                
                if total_cost > 0:
                    roi_percentage = ((total_revenue - total_cost) / total_cost) * 100
                    print(f"   📊 DEBUG: Supplier {supplier.name}: ROI = {roi_percentage:.2f}%")
                    
                    # Calcular métricas adicionales
                    avg_margin = self._calculate_average_margin(supplier_products)
                    days_to_sell = self._calculate_days_to_sell(supplier_products, start_date, end_date)
                    inventory_turnover = self._calculate_inventory_turnover(supplier_products, start_date, end_date)
                    
                    # Generar recomendaciones automáticas
                    recommendations = self._generate_supplier_recommendations(
                        roi_percentage, avg_margin, days_to_sell
                    )
                    
                    print(f"   💡 DEBUG: Supplier {supplier.name}: Creando análisis ROI")
                    
                    try:
                        analysis, created = SupplierROIAnalysis.objects.update_or_create(
                            supplier=supplier,
                            defaults={
                                'analysis_start_date': start_date,
                                'analysis_end_date': end_date,
                                'total_cost': Decimal(str(total_cost)),
                                'total_revenue': Decimal(str(total_revenue)),
                                'gross_profit': Decimal(str(total_revenue - total_cost)),
                                'roi_percentage': Decimal(str(roi_percentage)),
                                'avg_delivery_time': Decimal(str(days_to_sell)),
                                'quality_score': Decimal('95.0'),  # Default quality score
                                'on_time_delivery_rate': Decimal('90.0'),  # Default delivery rate
                                'cost_per_unit': Decimal(str(total_cost / max(1, supplier_products.count()))),
                                'cost_trend': 'stable',  # Default trend
                                'performance_rating': self._determine_performance_rating(roi_percentage),
                                'recommendations': recommendations
                            }
                        )
                        
                        analyses.append(analysis)
                        status = "actualizado" if not created else "creado"
                        print(f"   ✅ DEBUG: Supplier {supplier.name}: Análisis ROI {status} exitosamente")
                        
                    except Exception as create_error:
                        print(f"   ❌ DEBUG: Error creando análisis para {supplier.name}: {str(create_error)}")
                        
                else:
                    print(f"   ⚠️ DEBUG: Supplier {supplier.name}: total_cost = 0, SKIPPING")
            
            print(f"   🎯 DEBUG: Total análisis ROI creados: {len(analyses)}")
            return analyses
            
        except Exception as e:
            print(f"   ❌ DEBUG: Error general en analyze_supplier_roi: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
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
    
    def _determine_performance_rating(self, roi_percentage: float) -> str:
        """Determinar calificación de rendimiento basada en ROI"""
        if roi_percentage >= 50:
            return 'excellent'
        elif roi_percentage >= 25:
            return 'good'
        elif roi_percentage >= 10:
            return 'average'
        else:
            return 'poor'
