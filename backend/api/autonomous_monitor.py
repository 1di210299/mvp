# api/autonomous_monitor.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Sum, Count, F, Q
from .models import Dataset, BusinessRule, MonitoringLog, AgentAction, BusinessContext

class AutonomousMonitor:
    """
    Sistema de monitoreo autónomo que analiza datos continuamente,
    detecta anomalías y oportunidades, y toma decisiones proactivas.
    """
    
    def __init__(self, dataset_id=None):
        self.dataset_id = dataset_id
        self.analysis_results = {}
        self.detected_issues = []
        self.opportunities = []
        self.actions_taken = []
        
    def analyze_dataset(self, dataset_id=None):
        """Analiza un dataset específico buscando anomalías y patrones."""
        if dataset_id:
            self.dataset_id = dataset_id
            
        if not self.dataset_id:
            raise ValueError("Se requiere un ID de dataset para el análisis")
            
        try:
            dataset = Dataset.objects.get(id=self.dataset_id)
            # Obtener datos del dataset
            data = self._get_dataset_data(dataset)
            
            # Ejecutar diferentes tipos de análisis
            self.analysis_results = {
                'trends': self._analyze_trends(data),
                'anomalies': self._detect_anomalies(data),
                'opportunities': self._identify_opportunities(data, dataset),
                'forecasts': self._generate_forecasts(data)
            }
            
            # Verificar reglas de negocio aplicables
            self._check_business_rules(dataset, data)
            
            return self.analysis_results
            
        except Dataset.DoesNotExist:
            raise ValueError(f"Dataset con ID {self.dataset_id} no encontrado")
        except Exception as e:
            raise Exception(f"Error analizando dataset: {str(e)}")
    
    def _get_dataset_data(self, dataset):
        """Obtiene y prepara los datos del dataset para análisis."""
        # Esta implementación dependerá de cómo almacenas los datos
        # Para este ejemplo, asumiremos que los datos están disponibles a través de una API o servicio
        
        try:
            # Implementa tu lógica de acceso a datos aquí
            # Por ejemplo:
            # from .data_service import get_dataset_data
            # return get_dataset_data(dataset.id)
            
            # Para este ejemplo, simulamos datos
            return self._simulate_dataset_data(dataset)
            
        except Exception as e:
            raise Exception(f"Error obteniendo datos del dataset: {str(e)}")
    
    def _simulate_dataset_data(self, dataset):
        """Simula datos para propósitos de demostración."""
        # En una implementación real, este método se reemplazaría con
        # el código para obtener los datos reales del dataset
        
        # Simulamos datos de ventas
        dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
        sales = np.random.normal(1000, 200, size=90)  # Ventas con algo de variabilidad
        
        # Añadimos algunas anomalías para probar la detección
        sales[30] = sales[30] * 2.5  # Un día con ventas excepcionalmente altas
        sales[60:65] = sales[60:65] * 0.4  # Período de ventas bajas
        
        # Creamos un dataframe
        df = pd.DataFrame({
            'date': dates,
            'sales': sales,
            'units_sold': (sales / np.random.uniform(20, 50, size=90)).astype(int),
            'customer_count': (sales / np.random.uniform(50, 100, size=90)).astype(int)
        })
        
        # Añadimos algunas columnas categóricas si el dataset lo requiere
        if 'category' in dataset.name.lower() or 'categoría' in dataset.name.lower():
            categories = ['Electrónicos', 'Ropa', 'Hogar', 'Alimentos', 'Otros']
            df['category'] = np.random.choice(categories, size=90)
            
        if 'region' in dataset.name.lower() or 'región' in dataset.name.lower():
            regions = ['Lima', 'Arequipa', 'Cusco', 'Trujillo', 'Piura']
            df['region'] = np.random.choice(regions, size=90)
            
        return df
    
    def _analyze_trends(self, data):
        """Analiza tendencias en los datos."""
        trends = {}
        
        # Verificar que 'date' y 'sales' estén en los datos
        if 'date' in data.columns and 'sales' in data.columns:
            # Análisis de tendencia de ventas
            data_sorted = data.sort_values('date')
            data_sorted['rolling_avg'] = data_sorted['sales'].rolling(window=7).mean()
            
            # Calcular cambio porcentual
            data_sorted['pct_change'] = data_sorted['sales'].pct_change(periods=7) * 100
            
            # Determinar tendencia general
            recent_trend = data_sorted['pct_change'].iloc[-7:].mean()
            
            if recent_trend > 5:
                trend_label = "fuerte_crecimiento"
            elif recent_trend > 2:
                trend_label = "crecimiento_moderado"
            elif recent_trend > -2:
                trend_label = "estable"
            elif recent_trend > -5:
                trend_label = "declive_moderado"
            else:
                trend_label = "declive_fuerte"
            
            # Guardar resultados
            trends['sales_trend'] = {
                'label': trend_label,
                'recent_change_pct': recent_trend,
                'last_value': data_sorted['sales'].iloc[-1],
                'avg_last_week': data_sorted['sales'].iloc[-7:].mean(),
                'avg_last_month': data_sorted['sales'].iloc[-30:].mean()
            }
            
        # Análisis de otros campos numéricos si están disponibles
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col != 'sales' and col != 'date':
                trends[f'{col}_trend'] = {
                    'last_value': data[col].iloc[-1] if not data[col].empty else None,
                    'avg_last_week': data[col].iloc[-7:].mean() if len(data) >= 7 else None,
                    'avg_last_month': data[col].iloc[-30:].mean() if len(data) >= 30 else None
                }
        
        return trends
    
    def _detect_anomalies(self, data):
        """Detecta anomalías en los datos usando métodos estadísticos."""
        anomalies = {}
        
        # Verificar campos numéricos
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Método simple: detectar valores fuera de 3 desviaciones estándar
            mean = data[col].mean()
            std = data[col].std()
            
            lower_bound = mean - 3 * std
            upper_bound = mean + 3 * std
            
            # Identificar anomalías
            anomalies_low = data[data[col] < lower_bound]
            anomalies_high = data[data[col] > upper_bound]
            
            if not anomalies_low.empty or not anomalies_high.empty:
                # Si tenemos 'date', usar esa columna para identificar cuándo ocurrieron
                if 'date' in data.columns:
                    anomalies[col] = {
                        'low': [{'date': str(date), 'value': value} for date, value in 
                                zip(anomalies_low['date'], anomalies_low[col])],
                        'high': [{'date': str(date), 'value': value} for date, value in 
                                 zip(anomalies_high['date'], anomalies_high[col])]
                    }
                else:
                    anomalies[col] = {
                        'low': anomalies_low[col].tolist(),
                        'high': anomalies_high[col].tolist()
                    }
        
        return anomalies
    
    def _identify_opportunities(self, data, dataset):
        """Identifica oportunidades de negocio en los datos."""
        opportunities = {}
        
        # Verificar si podemos identificar oportunidades basadas en tendencias de ventas
        if 'date' in data.columns and 'sales' in data.columns:
            # Analizar patrones estacionales (simplificado)
            data_sorted = data.sort_values('date')
            
            # Buscar días de la semana con mejor rendimiento
            if len(data_sorted) >= 14:  # Necesitamos al menos 2 semanas de datos
                data_sorted['dayofweek'] = data_sorted['date'].dt.dayofweek
                day_performance = data_sorted.groupby('dayofweek')['sales'].mean()
                
                best_day_idx = day_performance.idxmax()
                best_day_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][best_day_idx]
                
                opportunities['best_day'] = {
                    'day': best_day_name,
                    'avg_sales': day_performance[best_day_idx],
                    'insight': f"Los {best_day_name}s tienen el mejor rendimiento de ventas en promedio."
                }
            
        # Identificar oportunidades por categoría si está disponible
        if 'category' in data.columns and 'sales' in data.columns:
            category_performance = data.groupby('category')['sales'].mean().sort_values(ascending=False)
            
            opportunities['category_insights'] = {
                'best_category': category_performance.index[0],
                'best_category_sales': category_performance.iloc[0],
                'worst_category': category_performance.index[-1],
                'worst_category_sales': category_performance.iloc[-1],
                'insight': f"La categoría {category_performance.index[0]} tiene el mejor desempeño, mientras que {category_performance.index[-1]} tiene el menor."
            }
            
        # Identificar oportunidades por región si está disponible
        if 'region' in data.columns and 'sales' in data.columns:
            region_performance = data.groupby('region')['sales'].mean().sort_values(ascending=False)
            
            opportunities['region_insights'] = {
                'best_region': region_performance.index[0],
                'best_region_sales': region_performance.iloc[0],
                'worst_region': region_performance.index[-1],
                'worst_region_sales': region_performance.iloc[-1],
                'insight': f"La región {region_performance.index[0]} tiene el mejor desempeño, mientras que {region_performance.index[-1]} tiene el menor."
            }
            
        return opportunities
    
    def _generate_forecasts(self, data):
        """Genera pronósticos simples basados en tendencias históricas."""
        forecasts = {}
        
        # Verificar si podemos hacer pronósticos de ventas
        if 'date' in data.columns and 'sales' in data.columns:
            # Ordenar por fecha
            data_sorted = data.sort_values('date')
            
            # Pronóstico simple usando la tendencia reciente
            if len(data_sorted) >= 30:  # Necesitamos al menos un mes de datos
                # Usar últimos 30 días para pronosticar próximos 7 días
                recent_data = data_sorted.iloc[-30:]
                
                # Modelo muy simple: tendencia lineal
                x = np.arange(len(recent_data))
                y = recent_data['sales'].values
                
                # Ajustar línea de tendencia
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                
                # Proyectar próximos 7 días
                future_x = np.arange(len(recent_data), len(recent_data) + 7)
                future_y = p(future_x)
                
                # Crear fechas futuras
                last_date = recent_data['date'].iloc[-1]
                future_dates = [last_date + timedelta(days=i+1) for i in range(7)]
                
                # Guardar pronóstico
                forecasts['sales_next_7_days'] = [
                    {'date': str(date), 'predicted_sales': max(0, sales)}
                    for date, sales in zip(future_dates, future_y)
                ]
                
                # Calcular cambio porcentual esperado
                avg_last_week = data_sorted['sales'].iloc[-7:].mean()
                avg_next_week = np.mean(future_y)
                pct_change = ((avg_next_week / avg_last_week) - 1) * 100 if avg_last_week > 0 else 0
                
                forecasts['expected_change_pct'] = pct_change
                
                # Determinar sentimiento del pronóstico
                if pct_change > 10:
                    forecast_sentiment = "muy_positivo"
                elif pct_change > 5:
                    forecast_sentiment = "positivo"
                elif pct_change > -5:
                    forecast_sentiment = "estable"
                elif pct_change > -10:
                    forecast_sentiment = "negativo"
                else:
                    forecast_sentiment = "muy_negativo"
                    
                forecasts['forecast_sentiment'] = forecast_sentiment
                
        return forecasts
    
    def _check_business_rules(self, dataset, data):
        """Verifica las reglas de negocio configuradas y genera alertas/acciones."""
        # Obtener reglas activas para este usuario/dataset
        rules = BusinessRule.objects.filter(
            owner=dataset.owner,
            is_active=True
        )
        
        for rule in rules:
            # Verificar si la métrica está disponible en los datos
            metric = rule.metric
            if metric not in data.columns:
                continue
                
            # Obtener el valor actual de la métrica
            current_value = None
            if 'date' in data.columns:
                # Si hay fechas, usar el valor más reciente
                latest_data = data.sort_values('date', ascending=False).iloc[0]
                current_value = latest_data[metric]
            else:
                # Si no hay fechas, usar promedio o último valor
                current_value = data[metric].mean()
                
            # Aplicar la condición de la regla
            rule_triggered = False
            
            if rule.condition == 'gt' and current_value > rule.threshold_value:
                rule_triggered = True
            elif rule.condition == 'lt' and current_value < rule.threshold_value:
                rule_triggered = True
            elif rule.condition == 'eq' and current_value == rule.threshold_value:
                rule_triggered = True
            elif rule.condition == 'change':
                # Para cambio porcentual, necesitamos datos históricos
                if 'date' in data.columns and len(data) > 1:
                    data_sorted = data.sort_values('date')
                    if len(data_sorted) >= 2:
                        previous_value = data_sorted[metric].iloc[-2]
                        if previous_value != 0:
                            percent_change = ((current_value / previous_value) - 1) * 100
                            if abs(percent_change) > rule.threshold_value:
                                rule_triggered = True
            
            # Si la regla se activó, registrar y posiblemente tomar acción
            if rule_triggered:
                # Registrar en el log de monitoreo
                severity = 'medium'  # Por defecto
                if rule.priority >= 8:
                    severity = 'critical'
                elif rule.priority >= 5:
                    severity = 'high'
                elif rule.priority <= 3:
                    severity = 'low'
                    
                log_entry = MonitoringLog.objects.create(
                    dataset=dataset,
                    rule=rule,
                    log_type='anomaly' if rule.rule_type in ['threshold', 'anomaly'] else 'opportunity',
                    description=f"Regla '{rule.name}' activada: {metric} {rule.condition} {rule.threshold_value}",
                    metrics={
                        'current_value': float(current_value),
                        'threshold': float(rule.threshold_value),
                        'condition': rule.condition
                    },
                    severity=severity
                )
                
                # Determinar si se debe tomar acción automática
                if rule.action_type == 'auto':
                    self._execute_rule_action(rule, dataset, log_entry, current_value)
                elif rule.action_type == 'suggest':
                    self._suggest_rule_action(rule, dataset, log_entry, current_value)
    
    def _execute_rule_action(self, rule, dataset, log_entry, current_value):
        """Ejecuta una acción automática basada en una regla."""
        # Crear registro de acción
        action = AgentAction.objects.create(
            action_type=rule.action_data.get('action_type', 'operational'),
            status='executed',
            description=f"Acción automática basada en regla '{rule.name}'",
            action_data=rule.action_data,
            expected_impact=rule.action_data.get('expected_impact', ''),
            confidence=0.85,  # Alta confianza porque es una regla predefinida
            executed_at=timezone.now(),
            dataset=dataset,
            rule=rule,
            monitoring_log=log_entry
        )
        
        # Aquí iría la lógica para ejecutar la acción real, como:
        # - Enviar correos electrónicos
        # - Hacer llamadas a APIs externas
        # - Actualizar registros en bases de datos
        # - etc.
        
        self.actions_taken.append({
            'id': action.id,
            'type': action.action_type,
            'description': action.description,
            'executed_at': action.executed_at
        })
        
        return action
    
    def _suggest_rule_action(self, rule, dataset, log_entry, current_value):
        """Sugiere una acción basada en una regla pero no la ejecuta automáticamente."""
        # Crear registro de acción sugerida
        action = AgentAction.objects.create(
            action_type=rule.action_data.get('action_type', 'operational'),
            status='suggested',
            description=f"Acción sugerida basada en regla '{rule.name}'",
            action_data=rule.action_data,
            expected_impact=rule.action_data.get('expected_impact', ''),
            confidence=0.85,  # Alta confianza porque es una regla predefinida
            dataset=dataset,
            rule=rule,
            monitoring_log=log_entry
        )
        
        self.opportunities.append({
            'id': action.id,
            'type': action.action_type,
            'description': action.description,
            'confidence': action.confidence
        })
        
        return action
    
    def get_active_alerts(self):
        """Retorna alertas activas no resueltas."""
        if not self.dataset_id:
            return []
            
        try:
            dataset = Dataset.objects.get(id=self.dataset_id)
            
            # Obtener alertas recientes no resueltas
            alerts = MonitoringLog.objects.filter(
                dataset=dataset,
                is_resolved=False
            ).order_by('-created_at', '-severity')
            
            return list(alerts.values(
                'id', 'log_type', 'description', 'created_at', 'severity',
                'rule__name', 'metrics'
            ))
            
        except Dataset.DoesNotExist:
            return []
            
    def get_suggested_actions(self):
        """Retorna acciones sugeridas pendientes de aprobación."""
        if not self.dataset_id:
            return []
            
        try:
            dataset = Dataset.objects.get(id=self.dataset_id)
            
            # Obtener acciones sugeridas pendientes
            actions = AgentAction.objects.filter(
                dataset=dataset,
                status__in=['suggested', 'pending']
            ).order_by('-created_at', '-confidence')
            
            return list(actions.values(
                'id', 'action_type', 'description', 'created_at', 'confidence',
                'expected_impact', 'rule__name'
            ))
            
        except Dataset.DoesNotExist:
            return []