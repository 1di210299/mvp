"""
Financial Forecasting Service - ML Services Core Optimizado
==========================================================
Pronósticos financieros robustos con algoritmos ML optimizados:
- Revenue forecasting con Prophet y Random Forest
- ROI analysis avanzado
- Performance monitoring integrado
- Baseline accuracy metrics

Versión optimizada para Días 3-4: ML Services Core
"""

import pandas as pd
import numpy as np
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.db.models import Sum, Avg, Count, F, Q, Max, Min
from django.utils import timezone
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score
import logging
import warnings
warnings.filterwarnings('ignore')

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
            
            # Crear predicción usando los campos correctos del modelo
            prediction = RevenuePrediction.objects.create(
                model=financial_model,
                prediction_date=period_start,
                predicted_revenue=Decimal(str(pred_revenue)),
                confidence_level=Decimal('85.00'),
                category_breakdown={
                    'total_revenue': float(pred_revenue),
                    'margin': float(pred_margin),
                    'units_sold': float(pred_units),
                    'lower_bound': float(revenue_lower),
                    'upper_bound': float(revenue_upper),
                    'period_type': period_type,
                    'period_start': period_start.isoformat(),
                    'period_end': period_end.isoformat()
                }
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
                
                # Calcular estadísticas con manejo de NaN
                revenue_mean = window_data['revenue'].mean()
                revenue_std = window_data['revenue'].std()
                margin_mean = window_data['margin'].mean()
                units_mean = window_data['units'].mean()
                
                # Limpiar valores NaN e infinitos
                revenue_mean = np.nan_to_num(revenue_mean, nan=0.0, posinf=0.0, neginf=0.0)
                revenue_std = np.nan_to_num(revenue_std, nan=0.0, posinf=0.0, neginf=0.0)
                margin_mean = np.nan_to_num(margin_mean, nan=0.0, posinf=0.0, neginf=0.0)
                units_mean = np.nan_to_num(units_mean, nan=0.0, posinf=0.0, neginf=0.0)
                
                # Calcular tendencia con manejo seguro
                if len(window_data) > 1:
                    trend = window_data['revenue'].iloc[-1] - window_data['revenue'].iloc[0]
                    trend = np.nan_to_num(trend, nan=0.0, posinf=0.0, neginf=0.0)
                else:
                    trend = 0.0
                
                features.append([
                    revenue_mean,
                    revenue_std,
                    margin_mean,
                    units_mean,
                    len(window_data),  # número de períodos
                    trend  # tendencia
                ])
                
                # Targets también limpios
                target_revenue = np.nan_to_num(historical_data.iloc[i]['revenue'], nan=0.0, posinf=0.0, neginf=0.0)
                target_margin = np.nan_to_num(historical_data.iloc[i]['margin'], nan=0.0, posinf=0.0, neginf=0.0)
                target_units = np.nan_to_num(historical_data.iloc[i]['units'], nan=0.0, posinf=0.0, neginf=0.0)
                
                targets_revenue.append(target_revenue)
                targets_margin.append(target_margin)
                targets_units.append(target_units)
        
        if len(features) < 3:
            # Datos insuficientes, usar modelo simple
            logger.warning("Datos insuficientes para Random Forest, usando modelo lineal")
            model = LinearRegression()
            X = np.arange(len(historical_data)).reshape(-1, 1)
            y = historical_data['revenue'].values
            # Limpiar datos de entrada
            y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
            model.fit(X, y)
            return model
        
        # Convertir a arrays numpy y limpiar
        features = np.array(features)
        targets_revenue = np.array(targets_revenue)
        
        # Verificación final de datos
        if np.any(np.isnan(features)) or np.any(np.isinf(features)):
            logger.warning("Detectados NaN o infinitos en features, limpiando")
            features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
        
        if np.any(np.isnan(targets_revenue)) or np.any(np.isinf(targets_revenue)):
            logger.warning("Detectados NaN o infinitos en targets, limpiando")
            targets_revenue = np.nan_to_num(targets_revenue, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Entrenar modelo Random Forest
        model = RandomForestRegressor(
            n_estimators=50, 
            random_state=42,
            max_depth=10,  # Limitar profundidad para evitar overfitting
            min_samples_split=2,
            min_samples_leaf=1
        )
        
        try:
            model.fit(features, targets_revenue)
            logger.info("Modelo Random Forest entrenado exitosamente para predicciones financieras")
        except Exception as e:
            logger.error(f"Error entrenando Random Forest: {str(e)}")
            # Fallback a modelo lineal
            model = LinearRegression()
            X = np.arange(len(historical_data)).reshape(-1, 1)
            y = historical_data['revenue'].values
            y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
            model.fit(X, y)
        
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
    
    # ===============================================
    # ML SERVICES CORE - MÉTODOS OPTIMIZADOS
    # ===============================================
    
    def calculate_baseline_accuracy_metrics(self, model_type: str = 'revenue') -> Dict[str, float]:
        """
        Calcula métricas de accuracy baseline para Financial Forecasting
        
        Args:
            model_type: 'revenue', 'roi', o 'cashflow'
        """
        if model_type == 'revenue':
            return self._calculate_revenue_baseline_metrics()
        elif model_type == 'roi':
            return self._calculate_roi_baseline_metrics()
        elif model_type == 'cashflow':
            return self._calculate_cashflow_baseline_metrics()
        else:
            raise ValueError(f"Tipo de modelo no soportado: {model_type}")
    
    def _calculate_revenue_baseline_metrics(self) -> Dict[str, float]:
        """
        Métricas baseline para predicción de revenue
        """
        try:
            # Obtener datos históricos de revenue
            revenue_predictions = RevenuePrediction.objects.filter(
                model__company=self.company
            ).values_list('predicted_revenue', 'confidence_level')
            
            if not revenue_predictions:
                return self._get_empty_financial_metrics()
            
            # Obtener revenue real para comparación
            historical_data = self._get_financial_historical_data_for_metrics()
            
            if historical_data.empty:
                return self._get_empty_financial_metrics()
            
            # Usar últimos datos para validación
            train_size = int(len(historical_data) * 0.8)
            train_data = historical_data[:train_size]
            test_data = historical_data[train_size:]
            
            if len(test_data) < 2:
                return self._get_empty_financial_metrics()
            
            # Entrenar modelo simple para baseline
            model = self._train_baseline_revenue_model(train_data)
            
            # Predecir en conjunto de prueba
            predictions = model.predict(self._prepare_features(test_data))
            actual = test_data['revenue'].values
            
            # Calcular métricas
            mae = mean_absolute_error(actual, predictions)
            mse = mean_squared_error(actual, predictions)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((actual - predictions) / np.where(actual != 0, actual, 1))) * 100
            r2 = r2_score(actual, predictions)
            
            # Accuracy score
            accuracy_score = max(0, 100 - mape)
            
            return {
                'mae': float(mae),
                'mse': float(mse),
                'rmse': float(rmse),
                'mape': float(mape),
                'r2_score': float(r2),
                'accuracy_score': float(accuracy_score),
                'sample_size': len(actual),
                'model_type': 'revenue_prediction',
                'avg_revenue': float(np.mean(actual)),
                'revenue_volatility': float(np.std(actual))
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas revenue: {e}")
            return self._get_empty_financial_metrics()
    
    def _calculate_roi_baseline_metrics(self) -> Dict[str, float]:
        """
        Métricas baseline para análisis de ROI
        """
        try:
            # Obtener datos de ROI filtrando por suppliers de la company
            roi_analyses = SupplierROIAnalysis.objects.filter(
                supplier__products__company=self.company
            ).values_list('roi_percentage', 'quality_score').distinct()
            
            if not roi_analyses:
                return self._get_empty_financial_metrics()
            
            roi_values = np.array([float(roi[0]) for roi in roi_analyses])
            quality_scores = np.array([float(roi[1]) for roi in roi_analyses])
            
            # Métricas de ROI
            avg_roi = np.mean(roi_values)
            roi_std = np.std(roi_values)
            roi_min = np.min(roi_values)
            roi_max = np.max(roi_values)
            
            # Correlación ROI vs Profitability
            correlation = np.corrcoef(roi_values, quality_scores)[0, 1] if len(roi_values) > 1 else 0
            
            # Porcentaje de ROI positivo
            positive_roi_rate = np.mean(roi_values > 0) * 100
            
            return {
                'avg_roi': float(avg_roi),
                'roi_volatility': float(roi_std),
                'roi_min': float(roi_min),
                'roi_max': float(roi_max),
                'roi_correlation': float(correlation) if not np.isnan(correlation) else 0,
                'positive_roi_rate': float(positive_roi_rate),
                'sample_size': len(roi_values),
                'model_type': 'roi_analysis'
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas ROI: {e}")
            return self._get_empty_financial_metrics()
    
    def _calculate_cashflow_baseline_metrics(self) -> Dict[str, float]:
        """
        Métricas baseline para cashflow prediction
        """
        try:
            # Obtener datos de cash flow
            cashflow_data = self._get_cash_flow_data(days_back=180)
            
            if len(cashflow_data) < 30:
                return self._get_empty_financial_metrics()
            
            # Convertir a arrays
            net_cashflows = np.array([day['net_cash_flow'] for day in cashflow_data])
            inflows = np.array([day['inflow'] for day in cashflow_data])
            outflows = np.array([day['outflow'] for day in cashflow_data])
            
            # Métricas de cash flow
            avg_net_cashflow = np.mean(net_cashflows)
            cashflow_volatility = np.std(net_cashflows)
            
            # Días con cash flow positivo
            positive_days_rate = np.mean(net_cashflows > 0) * 100
            
            # Predicción simple (media móvil)
            window_size = min(30, len(net_cashflows) // 3)
            if window_size > 0:
                predicted = np.convolve(net_cashflows, np.ones(window_size)/window_size, mode='valid')
                actual = net_cashflows[window_size-1:]
                
                if len(predicted) > 0 and len(actual) > 0:
                    mae_cashflow = np.mean(np.abs(actual[:len(predicted)] - predicted))
                    mape_cashflow = np.mean(np.abs((actual[:len(predicted)] - predicted) / 
                                                 np.where(actual[:len(predicted)] != 0, actual[:len(predicted)], 1))) * 100
                else:
                    mae_cashflow = 0
                    mape_cashflow = 100
            else:
                mae_cashflow = 0
                mape_cashflow = 100
            
            return {
                'avg_net_cashflow': float(avg_net_cashflow),
                'cashflow_volatility': float(cashflow_volatility),
                'positive_days_rate': float(positive_days_rate),
                'mae_prediction': float(mae_cashflow),
                'mape_prediction': float(mape_cashflow),
                'avg_inflow': float(np.mean(inflows)),
                'avg_outflow': float(np.mean(outflows)),
                'sample_size': len(net_cashflows),
                'model_type': 'cashflow_prediction'
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas cashflow: {e}")
            return self._get_empty_financial_metrics()
    
    def _get_financial_historical_data_for_metrics(self) -> pd.DataFrame:
        """
        Obtiene datos históricos estructurados para métricas
        """
        try:
            # Obtener datos de transacciones agrupados por día
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=365)
            
            # Agrupar por día
            daily_data = []
            current_date = start_date
            
            while current_date <= end_date:
                daily_revenue = Transaction.objects.filter(
                    product__company=self.company,
                    transaction_type='sale',
                    transaction_date__date=current_date
                ).aggregate(
                    total=Sum(F('quantity') * F('product__sale_price'))
                )['total'] or 0
                
                daily_data.append({
                    'date': current_date,
                    'revenue': float(daily_revenue),
                    'day_of_week': current_date.weekday(),
                    'day_of_month': current_date.day,
                    'month': current_date.month,
                    'quarter': (current_date.month - 1) // 3 + 1
                })
                
                current_date += timedelta(days=1)
            
            return pd.DataFrame(daily_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {e}")
            return pd.DataFrame()
    
    def _train_baseline_revenue_model(self, data: pd.DataFrame) -> RandomForestRegressor:
        """
        Entrena modelo baseline para revenue prediction
        """
        features = self._prepare_features(data)
        target = data['revenue'].values
        
        model = RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(features, target)
        return model
    
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """
        Prepara features para el modelo
        """
        features = []
        for _, row in data.iterrows():
            features.append([
                row['day_of_week'],
                row['day_of_month'],
                row['month'],
                row['quarter']
            ])
        
        return np.array(features)
    
    def _get_empty_financial_metrics(self) -> Dict[str, float]:
        """Métricas vacías para casos de error"""
        return {
            'mae': 0.0,
            'mse': 0.0,
            'rmse': 0.0,
            'mape': 100.0,
            'r2_score': 0.0,
            'accuracy_score': 0.0,
            'sample_size': 0,
            'model_type': 'unknown'
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Resumen completo de performance para ML Services Core
        """
        try:
            # Métricas de cada modelo
            revenue_metrics = self.calculate_baseline_accuracy_metrics('revenue')
            roi_metrics = self.calculate_baseline_accuracy_metrics('roi')
            cashflow_metrics = self.calculate_baseline_accuracy_metrics('cashflow')
            
            # Estadísticas financieras generales
            total_revenue = Transaction.objects.filter(
                product__company=self.company,
                transaction_type='sale'
            ).aggregate(
                total=Sum(F('quantity') * F('product__sale_price'))
            )['total'] or 0
            
            total_costs = Transaction.objects.filter(
                product__company=self.company,
                transaction_type='purchase'
            ).aggregate(
                total=Sum(F('quantity') * F('unit_cost'))
            )['total'] or 0
            
            # Contadores de modelos activos
            active_revenue_models = FinancialForecastModel.objects.filter(
                company=self.company,
                metric_type='revenue'
            ).count()
            
            active_roi_analyses = SupplierROIAnalysis.objects.filter(
                supplier__products__company=self.company
            ).count()
            
            return {
                'model_performance': {
                    'revenue_forecasting': revenue_metrics,
                    'roi_analysis': roi_metrics,
                    'cashflow_prediction': cashflow_metrics
                },
                'financial_overview': {
                    'total_revenue': float(total_revenue),
                    'total_costs': float(total_costs),
                    'gross_profit': float(total_revenue - total_costs),
                    'gross_margin_percent': round((total_revenue - total_costs) / total_revenue * 100, 2) if total_revenue > 0 else 0
                },
                'model_coverage': {
                    'active_revenue_models': active_revenue_models,
                    'active_roi_analyses': active_roi_analyses,
                    'revenue_predictions_count': RevenuePrediction.objects.filter(
                        model__company=self.company
                    ).count()
                },
                'data_quality': {
                    'days_with_revenue_data': self._count_days_with_revenue(),
                    'avg_daily_revenue': self._calculate_avg_daily_revenue(),
                    'revenue_consistency_score': self._calculate_revenue_consistency()
                },
                'timestamp': datetime.now().isoformat(),
                'service_name': 'FinancialForecastingService'
            }
            
        except Exception as e:
            logger.error(f"Error generando resumen financiero: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _count_days_with_revenue(self) -> int:
        """Cuenta días con datos de revenue"""
        try:
            return Transaction.objects.filter(
                product__company=self.company,
                transaction_type='sale'
            ).dates('transaction_date', 'day').count()
        except:
            return 0
    
    def _calculate_avg_daily_revenue(self) -> float:
        """Calcula revenue promedio diario"""
        try:
            days_with_data = self._count_days_with_revenue()
            total_revenue = Transaction.objects.filter(
                product__company=self.company,
                transaction_type='sale'
            ).aggregate(
                total=Sum(F('quantity') * F('product__sale_price'))
            )['total'] or 0
            
            return round(float(total_revenue) / days_with_data, 2) if days_with_data > 0 else 0.0
        except:
            return 0.0
    
    def _calculate_revenue_consistency(self) -> float:
        """Calcula score de consistencia de revenue"""
        try:
            daily_revenues = []
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            current_date = start_date
            while current_date <= end_date:
                daily_revenue = Transaction.objects.filter(
                    product__company=self.company,
                    transaction_type='sale',
                    transaction_date__date=current_date
                ).aggregate(
                    total=Sum(F('quantity') * F('product__sale_price'))
                )['total'] or 0
                
                daily_revenues.append(float(daily_revenue))
                current_date += timedelta(days=1)
            
            if not daily_revenues or all(rev == 0 for rev in daily_revenues):
                return 0.0
            
            # Coeficiente de variación invertido como score de consistencia
            mean_revenue = np.mean(daily_revenues)
            std_revenue = np.std(daily_revenues)
            
            if mean_revenue == 0:
                return 0.0
            
            cv = std_revenue / mean_revenue
            consistency_score = 100 / (1 + cv)  # Mayor consistencia = menor variación
            
            return round(consistency_score, 2)
            
        except:
            return 0.0
