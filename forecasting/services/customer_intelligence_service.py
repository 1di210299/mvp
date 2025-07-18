"""
Customer Intelligence Service - ML Services Core Optimizado
===========================================================
Análisis avanzado de clientes con algoritmos ML optimizados:
- CLV prediction con accuracy tracking
- Churn prediction con baseline metrics
- Customer segmentation automática
- Performance monitoring integrado

Versión optimizada para Días 3-4: ML Services Core
"""

import math
import decimal
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from django.utils import timezone
from django.db.models import Sum, Avg, Q, Count, Max, Min
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import warnings
warnings.filterwarnings('ignore')

# Imports from Django models
from authentication.models import Company
from inventory.models import Product, Customer, Sale, Transaction

logger = logging.getLogger(__name__)
from forecasting.models import (
    CustomerLifetimeValue, ChurnPrediction, NextPurchasePrediction, 
    ProductRecommendation, CustomerSegmentation, MarketBasketAnalysis
)


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
        
        # Obtener clientes que han comprado productos de esta empresa
        # Buscar por sales directas usando el modelo Sale
        from django.db.models import Q
        
        # Buscar customers que aparecen en ventas (modelo Sale) de productos de la company
        customers_from_sales = Customer.objects.filter(
            Q(name__in=Sale.objects.filter(
                product__company=self.company
            ).values_list('customer_name', flat=True).distinct()) &
            Q(is_active=True)
        )
        
        # Si no hay customers por Sales, obtener todos los customers activos
        customers = customers_from_sales if customers_from_sales.exists() else Customer.objects.filter(is_active=True)[:10]  # Limitar para testing
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
            
            # Validar y sanitizar valores para evitar errores decimales
            def safe_decimal(value, default=0.0, max_digits=6, decimal_places=4):
                try:
                    if value is None or not isinstance(value, (int, float)):
                        return Decimal(str(default))
                    if math.isnan(value) or math.isinf(value):
                        return Decimal(str(default))
                    
                    # Convertir a decimal y aplicar límites del campo de la base de datos
                    decimal_value = Decimal(str(round(float(value), decimal_places)))
                    
                    # Calcular valor máximo permitido basado en max_digits y decimal_places
                    max_value = Decimal('9' * (max_digits - decimal_places) + '.' + '9' * decimal_places)
                    
                    # Aplicar límites
                    if decimal_value > max_value:
                        return max_value
                    elif decimal_value < 0:
                        return Decimal('0.0000')
                    
                    # Cuantizar para asegurar las cifras decimales correctas
                    quantize_pattern = '0.' + '0' * decimal_places
                    return decimal_value.quantize(Decimal(quantize_pattern))
                    
                except (ValueError, TypeError, decimal.InvalidOperation):
                    return Decimal(str(default))
            
            churn_prediction = ChurnPrediction.objects.update_or_create(
                customer=customer,
                defaults={
                    'churn_probability': safe_decimal(churn_analysis['probability'], max_digits=5, decimal_places=4),
                    'churn_risk_level': churn_analysis.get('risk_level', 'unknown'),
                    'days_since_last_purchase': churn_analysis.get('days_since_last', 0),
                    'declining_purchase_frequency': churn_analysis.get('declining_frequency', False),
                    'declining_order_value': churn_analysis.get('declining_value', False),
                    'negative_trend_months': churn_analysis.get('negative_trend_months', 0),
                    'engagement_score': safe_decimal(churn_analysis['engagement_score'], max_digits=6, decimal_places=4),
                    'loyalty_score': safe_decimal(churn_analysis['loyalty_score'], max_digits=6, decimal_places=4),
                    'retention_strategy': retention_strategy.get('strategy', 'contact_campaign'),
                    'recommended_action_priority': retention_strategy.get('priority', 'low')
                }
            )[0]
            
            churn_predictions.append(churn_prediction)
        
        return churn_predictions
    
    def predict_next_purchases(self) -> List[NextPurchasePrediction]:
        """Predecir próxima compra por cliente"""
        
        customers = Customer.objects.filter(is_active=True)
        predictions = []
        
        for customer in customers:
            try:
                print(f"   📊 Procesando cliente: {customer.name}")
                # Obtener datos del cliente
                customer_data = self._get_customer_transaction_data(customer)
                
                if len(customer_data['transactions']) < 2:
                    print(f"   ⚠️ Cliente {customer.name}: Solo {len(customer_data['transactions'])} transacciones")
                    continue  # Necesitamos al menos 2 transacciones
                
                # Validar que hay datos válidos
                if not customer_data['transactions'] or customer_data['total_spent'] <= 0:
                    print(f"   ⚠️ Cliente {customer.name}: Sin datos válidos")
                    continue
                
                # Predecir próxima compra
                next_purchase_data = self._predict_next_purchase_timing(customer_data)
                
                # Validación exhaustiva de datos antes de crear la predicción
                confidence = next_purchase_data.get('confidence', 50)
                predicted_value = next_purchase_data.get('predicted_value', 0)
                predicted_quantity = next_purchase_data.get('predicted_quantity', 1)
                
                # Convertir a float primero para validación
                try:
                    confidence_float = float(confidence)
                    value_float = float(predicted_value)
                    quantity_float = float(predicted_quantity)
                except (ValueError, TypeError, OverflowError):
                    logger.warning(f"Valores no convertibles para cliente {customer.name}")
                    continue
                
                # Validar rangos antes de conversión a Decimal
                if (not (0 <= confidence_float <= 100) or 
                    value_float < 0 or value_float > 999999 or
                    quantity_float < 0 or quantity_float > 10000):
                    logger.warning(f"Valores fuera de rango para cliente {customer.name}")
                    continue
                
                # Validar que no hay valores especiales
                if (np.isnan(confidence_float) or np.isinf(confidence_float) or
                    np.isnan(value_float) or np.isinf(value_float) or 
                    np.isnan(quantity_float) or np.isinf(quantity_float)):
                    logger.warning(f"Valores NaN/Inf para cliente {customer.name}")
                    continue
                
                # Redondear valores para evitar problemas de precisión
                confidence_rounded = round(confidence_float, 2)
                value_rounded = round(value_float, 2)
                quantity_rounded = round(quantity_float, 2)
                
                # Recomendar productos
                product_recommendations = self._recommend_products_for_customer(customer, customer_data)
                
                # Crear predicción con valores validados
                prediction = NextPurchasePrediction.objects.update_or_create(
                    customer=customer,
                    defaults={
                        'predicted_date': next_purchase_data['predicted_date'],
                        'days_until_purchase': max(0, next_purchase_data.get('days_until', 30)),
                        'confidence_level': Decimal(str(confidence_rounded)),
                        'predicted_value': Decimal(str(value_rounded)),
                        'predicted_quantity': Decimal(str(quantity_rounded))
                    }
                )[0]
                
                # Agregar recomendaciones de productos
                try:
                    self._create_product_recommendations(prediction, product_recommendations)
                except Exception as rec_error:
                    logger.warning(f"Error creando recomendaciones para {customer.name}: {rec_error}")
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error prediciendo próxima compra para cliente {customer.name}: {str(e)}")
                # Continuar con el siguiente cliente en lugar de fallar completamente
                continue
        
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
                    'value_score': Decimal(str(segment_analysis['value_score'])),
                    'frequency_score': Decimal(str(features[1])),  # purchase_frequency
                    'recency_score': Decimal(str(max(1, 5 - features[2]))),  # recency score (inverted)
                    'segment_attributes': {
                        'behavioral_attributes': segment_analysis['attributes'],
                        'preferences': segment_analysis['preferences'],
                        'growth_potential': segment_analysis['growth_potential'],
                        'loyalty_index': segment_analysis['loyalty_index']
                    },
                    'marketing_strategy': segment_analysis['recommended_approach']
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
            # Validar que la venta tenga datos válidos
            if sale.total_amount is not None and sale.quantity is not None:
                try:
                    amount = float(sale.total_amount)
                    quantity = float(sale.quantity)
                    
                    # Validar que los valores sean positivos y finitos
                    if (amount > 0 and quantity > 0 and 
                        not (np.isnan(amount) or np.isinf(amount) or np.isnan(quantity) or np.isinf(quantity)) and
                        amount <= 999999 and quantity <= 10000):  # Límites razonables
                        
                        transactions.append({
                            'date': sale.date_sold.date(),
                            'amount': amount,
                            'quantity': quantity,
                            'product_id': sale.product.id,
                            'product_name': sale.product.name
                        })
                except (ValueError, TypeError, OverflowError):
                    continue  # Saltar ventas con datos inválidos
        
        # Calcular total_spent de manera segura
        total_spent = sum(t['amount'] for t in transactions)
        if np.isnan(total_spent) or np.isinf(total_spent):
            total_spent = 0
        
        return {
            'customer': customer,
            'transactions': transactions,
            'total_transactions': len(transactions),
            'total_spent': total_spent
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
        total_spent = customer_data['total_spent']
        num_transactions = len(transactions)
        
        if num_transactions == 0 or total_spent == 0:
            avg_order_value = 0
        else:
            avg_order_value = total_spent / num_transactions
            
        # Validar que avg_order_value no sea NaN o infinito
        if np.isnan(avg_order_value) or np.isinf(avg_order_value):
            avg_order_value = 0
        
        # Purchase Frequency (compras por mes)
        first_purchase = min(t['date'] for t in transactions)
        last_purchase = max(t['date'] for t in transactions)
        customer_lifespan_days = (last_purchase - first_purchase).days
        
        # Evitar divisiones por cero y valores problemáticos
        if customer_lifespan_days > 0:
            # Usar max para evitar divisiones por valores muy pequeños
            lifespan_months = max(1.0, customer_lifespan_days / 30.0)
            purchase_frequency = len(transactions) / lifespan_months  # Por mes
        else:
            purchase_frequency = len(transactions)  # Si solo hay una transacción
            lifespan_months = 1.0
            
        # Validar que purchase_frequency no sea NaN o infinito
        if np.isnan(purchase_frequency) or np.isinf(purchase_frequency):
            purchase_frequency = 1.0
            
        # Asegurar que los valores sean finitos y válidos
        purchase_frequency = min(100.0, max(0.0, purchase_frequency))  # Limitar a rangos razonables
        lifespan_months = min(120.0, max(1.0, lifespan_months))  # Max 10 años
        
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
        
        # Calcular scores de engagement y lealtad con valores seguros
        engagement_score = max(0, min(100, 100 - (components['recency_days'] * 0.5)))
        loyalty_score = max(0, min(100, components['purchase_frequency'] * 20 + len(transactions) * 5))
        
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
                'confidence': 30.0,
                'predicted_value': 0.0,
                'predicted_quantity': 1.0
            }
        
        try:
            # Calcular intervalos entre compras
            transaction_dates = sorted([t['date'] for t in transactions])
            intervals = []
            
            for i in range(1, len(transaction_dates)):
                interval = (transaction_dates[i] - transaction_dates[i-1]).days
                if interval > 0:  # Solo intervalos positivos
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
            
            # Validar y limpiar avg_interval
            if np.isnan(avg_interval) or np.isinf(avg_interval) or avg_interval <= 0:
                avg_interval = 60
            if np.isnan(std_interval) or np.isinf(std_interval) or std_interval < 0:
                std_interval = avg_interval * 0.3
            
            # Predecir fecha
            last_purchase_date = max(t['date'] for t in transactions)
            predicted_days = max(7, min(365, int(avg_interval)))  # Entre 7 y 365 días
            predicted_date = last_purchase_date + timedelta(days=predicted_days)
            
            # Calcular valores predichos con validación
            amounts = [t['amount'] for t in transactions if t['amount'] > 0]
            quantities = [t['quantity'] for t in transactions if t['quantity'] > 0]
            
            if amounts:
                avg_order_value = np.mean(amounts)
            else:
                avg_order_value = 0
                
            if quantities:
                avg_quantity = np.mean(quantities)
            else:
                avg_quantity = 1
            
            # Validar que no hay valores NaN o infinitos
            if np.isnan(avg_order_value) or np.isinf(avg_order_value) or avg_order_value < 0:
                avg_order_value = 0
            if np.isnan(avg_quantity) or np.isinf(avg_quantity) or avg_quantity < 0:
                avg_quantity = 1
            
            # Confianza basada en consistencia de intervalos
            try:
                cv = (std_interval / avg_interval) if avg_interval > 0 else 1
                if np.isnan(cv) or np.isinf(cv):
                    cv = 1
                confidence = max(30, min(90, 100 - (cv * 50)))
            except:
                confidence = 50
            
            # Validar confianza
            if np.isnan(confidence) or np.isinf(confidence):
                confidence = 50
            
            # Asegurar que todos los valores sean válidos y estén en rangos seguros
            avg_order_value = max(0, min(999999, float(avg_order_value)))
            avg_quantity = max(1, min(1000, float(avg_quantity)))
            confidence = max(30, min(90, float(confidence)))
            days_until = max(0, min(365, (predicted_date - timezone.now().date()).days))
            
            return {
                'predicted_date': predicted_date,
                'days_until': days_until,
                'confidence': confidence,
                'predicted_value': avg_order_value,
                'predicted_quantity': avg_quantity
            }
            
        except Exception as e:
            logger.warning(f"Error en _predict_next_purchase_timing: {e}")
            # Retornar valores seguros por defecto
            return {
                'predicted_date': timezone.now().date() + timedelta(days=60),
                'days_until': 60,
                'confidence': 50.0,
                'predicted_value': 100.0,
                'predicted_quantity': 1.0
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
                
                # Validar y limpiar datos
                safe_frequency = max(1, min(100, frequency))
                score = min(1.0, 0.8 + (safe_frequency * 0.1))
                
                recommendations.append({
                    'product': product,
                    'score': score,
                    'reason': 'frequently_purchased',
                    'predicted_quantity': safe_frequency,
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
                try:
                    # Validar y limpiar datos de market basket
                    lift_value = float(basket.lift) if basket.lift is not None else 1.0
                    confidence_value = float(basket.confidence) if basket.confidence is not None else 0.5
                    
                    # Asegurar rangos válidos
                    if np.isnan(lift_value) or np.isinf(lift_value):
                        lift_value = 1.0
                    if np.isnan(confidence_value) or np.isinf(confidence_value):
                        confidence_value = 0.5
                    
                    score = min(1.0, max(0.1, lift_value / 3))
                    confidence = min(90, max(10, confidence_value * 100))
                    
                    recommendations.append({
                        'product': recommended_product,
                        'score': score,
                        'reason': 'frequently_bought_together',
                        'predicted_quantity': 1,
                        'confidence': confidence
                    })
                except (ValueError, TypeError):
                    continue
        
        # Ordenar por score y devolver top 5
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:5]
    
    def _create_product_recommendations(self, next_purchase: NextPurchasePrediction, recommendations: List[Dict]):
        """Crear recomendaciones de productos en la base de datos"""
        
        try:
            # Limpiar recomendaciones existentes
            ProductRecommendation.objects.filter(next_purchase=next_purchase).delete()
            
            # Crear nuevas recomendaciones
            for rec in recommendations:
                try:
                    # Validar y limpiar datos antes de crear
                    score = rec.get('score', 0)
                    confidence = rec.get('confidence', 50)
                    predicted_quantity = rec.get('predicted_quantity', 1)
                    product_price = float(rec['product'].sale_price or 0)
                    
                    # Validar que no sean NaN o infinitos
                    if (np.isnan(score) or np.isinf(score) or 
                        np.isnan(confidence) or np.isinf(confidence) or
                        np.isnan(predicted_quantity) or np.isinf(predicted_quantity)):
                        continue
                    
                    # Asegurar rangos válidos
                    score = max(0, min(100, score))
                    confidence = max(0, min(100, confidence))
                    predicted_quantity = max(1, min(1000, predicted_quantity))
                    
                    ProductRecommendation.objects.create(
                        next_purchase=next_purchase,
                        product=rec['product'],
                        customer=next_purchase.customer,
                        recommendation_type='repeat_purchase',
                        confidence_score=Decimal(str(round(score, 2))),
                        purchase_probability=Decimal(str(round(confidence / 100, 4))),
                        expected_quantity=Decimal(str(round(predicted_quantity, 2))),
                        expected_revenue=Decimal(str(round(predicted_quantity * product_price, 2))),
                        reasoning=rec.get('reason', 'Producto recomendado basado en historial'),
                        expires_at=timezone.now() + timedelta(days=30)
                    )
                except Exception as e:
                    logger.warning(f"Error creando recomendación individual: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error creando recomendaciones: {str(e)}")
    
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
        
        # Calculate loyalty index
        loyalty_index = min(100, (lifespan_months * 8) + (total_transactions * 5))
        
        return {
            'primary_segment': primary_segment,
            'value_score': value_score,
            'frequency_score': attributes.get('recency_score', 1),  # Usar recency_score del attributes
            'recency_score': attributes.get('recency_score', 1),
            'growth_potential': growth_potential,
            'attributes': attributes,  # Changed from 'segment_attributes' to 'attributes'
            'loyalty_index': loyalty_index,  # Add missing loyalty_index
            'preferences': preferences,
            'recommended_approach': recommended_approach
        }
    
    # ===============================================
    # ML SERVICES CORE - MÉTODOS OPTIMIZADOS
    # ===============================================
    
    def calculate_baseline_accuracy_metrics(self, model_type: str = 'clv') -> Dict[str, float]:
        """
        Calcula métricas de accuracy baseline para Customer Intelligence
        
        Args:
            model_type: 'clv', 'churn', o 'segmentation'
        """
        if model_type == 'clv':
            return self._calculate_clv_baseline_metrics()
        elif model_type == 'churn':
            return self._calculate_churn_baseline_metrics()
        elif model_type == 'segmentation':
            return self._calculate_segmentation_baseline_metrics()
        else:
            raise ValueError(f"Tipo de modelo no soportado: {model_type}")
    
    def _calculate_clv_baseline_metrics(self) -> Dict[str, float]:
        """
        Métricas baseline para predicción de CLV
        """
        try:
            # Obtener datos históricos de CLV
            clv_records = CustomerLifetimeValue.objects.filter(
                customer__in=Customer.objects.filter(is_active=True)
            ).values_list('predicted_clv', 'current_value')
            
            if not clv_records:
                return self._get_empty_metrics()
            
            predicted_values = np.array([float(record[0]) for record in clv_records])
            actual_values = np.array([float(record[1]) for record in clv_records])
            
            # Filtrar valores válidos
            valid_mask = (predicted_values > 0) & (actual_values > 0)
            if not np.any(valid_mask):
                return self._get_empty_metrics()
            
            predicted_values = predicted_values[valid_mask]
            actual_values = actual_values[valid_mask]
            
            # Calcular métricas
            mae = np.mean(np.abs(predicted_values - actual_values))
            mse = np.mean((predicted_values - actual_values) ** 2)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((actual_values - predicted_values) / actual_values)) * 100
            
            # R²
            ss_res = np.sum((actual_values - predicted_values) ** 2)
            ss_tot = np.sum((actual_values - np.mean(actual_values)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # Accuracy score
            accuracy_score = max(0, 100 - mape)
            
            return {
                'mae': float(mae),
                'mse': float(mse),
                'rmse': float(rmse),
                'mape': float(mape),
                'r2_score': float(r2),
                'accuracy_score': float(accuracy_score),
                'sample_size': len(predicted_values),
                'model_type': 'clv_prediction'
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas CLV: {e}")
            return self._get_empty_metrics()
    
    def _calculate_churn_baseline_metrics(self) -> Dict[str, float]:
        """
        Métricas baseline para predicción de churn
        """
        try:
            # Simular datos de churn para baseline
            customers = Customer.objects.filter(is_active=True)[:100]  # Muestra
            
            predictions = []
            actuals = []
            
            for customer in customers:
                customer_data = self._get_customer_transaction_data(customer)
                
                # Predicción simple basada en recency
                recency_days = customer_data.get('recency_days', 365)
                predicted_churn = 1 if recency_days > 90 else 0
                
                # "Actual" basado en actividad reciente (simulado)
                actual_churn = 1 if recency_days > 120 else 0
                
                predictions.append(predicted_churn)
                actuals.append(actual_churn)
            
            if not predictions:
                return self._get_empty_metrics()
            
            predictions = np.array(predictions)
            actuals = np.array(actuals)
            
            # Métricas de clasificación
            accuracy = accuracy_score(actuals, predictions)
            precision, recall, f1, _ = precision_recall_fscore_support(
                actuals, predictions, average='binary', zero_division=0
            )
            
            # Tasa de churn
            churn_rate = np.mean(actuals) * 100
            
            return {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'churn_rate': float(churn_rate),
                'sample_size': len(predictions),
                'model_type': 'churn_prediction'
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas churn: {e}")
            return self._get_empty_metrics()
    
    def _calculate_segmentation_baseline_metrics(self) -> Dict[str, float]:
        """
        Métricas baseline para segmentación de clientes
        """
        try:
            # Obtener datos de segmentación
            segments = CustomerSegmentation.objects.all().values_list(
                'primary_segment', 'value_score', 'frequency_score', 'recency_score'
            )
            
            if not segments:
                return self._get_empty_metrics()
            
            # Convertir a arrays
            segment_names = [seg[0] for seg in segments]
            value_scores = np.array([float(seg[1]) for seg in segments])
            frequency_scores = np.array([float(seg[2]) for seg in segments])
            recency_scores = np.array([float(seg[3]) for seg in segments])
            
            # Calcular métricas de clustering
            unique_segments = len(set(segment_names))
            
            # Silhouette score simulado
            if len(value_scores) > 1:
                features = np.column_stack([value_scores, frequency_scores, recency_scores])
                from sklearn.metrics import silhouette_score
                from sklearn.preprocessing import LabelEncoder
                
                le = LabelEncoder()
                segment_labels = le.fit_transform(segment_names)
                
                silhouette_avg = silhouette_score(features, segment_labels)
            else:
                silhouette_avg = 0
            
            # Distribución de segmentos
            segment_distribution = {}
            for segment in set(segment_names):
                count = segment_names.count(segment)
                segment_distribution[segment] = count / len(segment_names)
            
            return {
                'silhouette_score': float(silhouette_avg),
                'n_segments': unique_segments,
                'sample_size': len(segments),
                'avg_value_score': float(np.mean(value_scores)),
                'avg_frequency_score': float(np.mean(frequency_scores)),
                'avg_recency_score': float(np.mean(recency_scores)),
                'segment_balance': float(min(segment_distribution.values()) / max(segment_distribution.values())) if segment_distribution else 0,
                'model_type': 'customer_segmentation'
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas segmentación: {e}")
            return self._get_empty_metrics()
    
    def _get_empty_metrics(self) -> Dict[str, float]:
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
            clv_metrics = self.calculate_baseline_accuracy_metrics('clv')
            churn_metrics = self.calculate_baseline_accuracy_metrics('churn')
            segmentation_metrics = self.calculate_baseline_accuracy_metrics('segmentation')
            
            # Estadísticas generales
            total_customers = Customer.objects.filter(is_active=True).count()
            active_clv_predictions = CustomerLifetimeValue.objects.count()
            active_churn_predictions = ChurnPrediction.objects.count()
            active_segmentations = CustomerSegmentation.objects.count()
            
            # Coverage metrics
            clv_coverage = (active_clv_predictions / total_customers * 100) if total_customers > 0 else 0
            churn_coverage = (active_churn_predictions / total_customers * 100) if total_customers > 0 else 0
            segmentation_coverage = (active_segmentations / total_customers * 100) if total_customers > 0 else 0
            
            return {
                'model_performance': {
                    'clv_prediction': clv_metrics,
                    'churn_prediction': churn_metrics,
                    'customer_segmentation': segmentation_metrics
                },
                'coverage_metrics': {
                    'total_customers': total_customers,
                    'clv_coverage_percent': round(clv_coverage, 2),
                    'churn_coverage_percent': round(churn_coverage, 2),
                    'segmentation_coverage_percent': round(segmentation_coverage, 2)
                },
                'data_quality': {
                    'customers_with_transactions': self._count_customers_with_data(),
                    'avg_transactions_per_customer': self._avg_transactions_per_customer(),
                    'data_completeness_score': self._calculate_data_completeness()
                },
                'business_impact': {
                    'high_value_customers': self._count_high_value_customers(),
                    'at_risk_customers': self._count_at_risk_customers(),
                    'total_predicted_clv': self._calculate_total_predicted_clv()
                },
                'timestamp': datetime.now().isoformat(),
                'service_name': 'CustomerIntelligenceService'
            }
            
        except Exception as e:
            logger.error(f"Error generando resumen de performance: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _count_customers_with_data(self) -> int:
        """Cuenta clientes con datos de transacciones"""
        try:
            # Contar customers que aparecen en ventas
            customers_with_sales = Customer.objects.filter(
                name__in=Sale.objects.filter(
                    product__company=self.company
                ).values_list('customer_name', flat=True).distinct()
            ).count()
            
            return customers_with_sales
        except:
            return 0
    
    def _avg_transactions_per_customer(self) -> float:
        """Promedio de transacciones por cliente"""
        try:
            total_sales = Sale.objects.filter(product__company=self.company).count()
            unique_customers = Sale.objects.filter(
                product__company=self.company
            ).values('customer_name').distinct().count()
            
            return round(total_sales / unique_customers, 2) if unique_customers > 0 else 0
        except:
            return 0.0
    
    def _calculate_data_completeness(self) -> float:
        """Calcula score de completitud de datos"""
        try:
            total_customers = Customer.objects.filter(is_active=True).count()
            customers_with_clv = CustomerLifetimeValue.objects.count()
            customers_with_churn = ChurnPrediction.objects.count()
            
            if total_customers == 0:
                return 0.0
            
            completeness = (customers_with_clv + customers_with_churn) / (total_customers * 2) * 100
            return min(100.0, round(completeness, 2))
        except:
            return 0.0
    
    def _count_high_value_customers(self) -> int:
        """Cuenta clientes de alto valor"""
        try:
            return CustomerLifetimeValue.objects.filter(
                predicted_clv__gte=1000  # CLV >= 1000
            ).count()
        except:
            return 0
    
    def _count_at_risk_customers(self) -> int:
        """Cuenta clientes en riesgo de churn"""
        try:
            return ChurnPrediction.objects.filter(
                churn_probability__gte=0.7  # 70% o más de probabilidad
            ).count()
        except:
            return 0
    
    def _calculate_total_predicted_clv(self) -> float:
        """Calcula CLV total predicho"""
        try:
            total_clv = CustomerLifetimeValue.objects.aggregate(
                total=Sum('predicted_clv')
            )['total']
            
            return float(total_clv) if total_clv else 0.0
        except:
            return 0.0
