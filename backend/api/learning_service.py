# api/learning_service.py
import numpy as np
import pandas as pd
from django.utils import timezone
from django.db.models import Avg, Count, Sum, F, Q
from .models import Dataset, BusinessRule, MonitoringLog, AgentAction, AgentLearningLog
from .decision_engine import DecisionEngine

class AdaptiveLearningService:
    """
    Servicio de aprendizaje adaptativo que mejora las decisiones
    del agente IA basado en resultados pasados.
    """
    
    def __init__(self, user=None):
        self.user = user
        self.insights = []
        self.recommendation_count = 0
        self.decision_engine = None
    
    def analyze_performance(self, time_period='all'):
        """
        Analiza el rendimiento de las decisiones pasadas del agente.
        
        Args:
            time_period: Período de tiempo para analizar ('week', 'month', 'quarter', 'all')
            
        Returns:
            Análisis detallado del rendimiento
        """
        try:
            # 1. Filtrar acciones según período de tiempo
            query_filter = {}
            if time_period == 'week':
                query_filter['executed_at__gte'] = timezone.now() - timezone.timedelta(days=7)
            elif time_period == 'month':
                query_filter['executed_at__gte'] = timezone.now() - timezone.timedelta(days=30)
            elif time_period == 'quarter':
                query_filter['executed_at__gte'] = timezone.now() - timezone.timedelta(days=90)
                
            # Filtrar por usuario si está disponible
            if self.user:
                query_filter['dataset__owner'] = self.user
                
            # 2. Obtener acciones y sus resultados
            executed_actions = AgentAction.objects.filter(
                status__in=['executed', 'failed'],
                **query_filter
            )
            
            learning_logs = AgentLearningLog.objects.filter(
                action__in=executed_actions
            )
            
            # 3. Calcular métricas de rendimiento
            total_actions = executed_actions.count()
            successful_actions = learning_logs.filter(success_score__gt=0).count()
            failed_actions = learning_logs.filter(success_score__lt=0).count()
            neutral_actions = total_actions - successful_actions - failed_actions
            
            success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
            
            avg_success_score = learning_logs.aggregate(Avg('success_score'))['success_score__avg'] or 0
            
            # 4. Analizar por tipo de acción
            action_type_performance = {}
            for action_type in executed_actions.values_list('action_type', flat=True).distinct():
                type_actions = executed_actions.filter(action_type=action_type)
                type_logs = learning_logs.filter(action__action_type=action_type)
                
                type_success_rate = (type_logs.filter(success_score__gt=0).count() / type_actions.count() * 100) if type_actions.count() > 0 else 0
                type_avg_score = type_logs.aggregate(Avg('success_score'))['success_score__avg'] or 0
                
                action_type_performance[action_type] = {
                    'count': type_actions.count(),
                    'success_rate': type_success_rate,
                    'avg_score': type_avg_score
                }
                
            # 5. Identificar tendencias temporales
            time_series = []
            if time_period != 'all' and executed_actions.exists():
                # Agrupar por semana o mes según período
                grouping = 'week' if time_period == 'week' else 'month'
                
                # Simulamos datos temporales para demo
                earliest = executed_actions.order_by('executed_at').first().executed_at
                latest = executed_actions.order_by('-executed_at').first().executed_at
                
                periods = []
                current = earliest
                while current <= latest:
                    periods.append(current)
                    if grouping == 'week':
                        current += timezone.timedelta(days=7)
                    else:
                        # Avanzar aproximadamente un mes
                        current += timezone.timedelta(days=30)
                
                for period_start in periods:
                    period_end = period_start + timezone.timedelta(days=7 if grouping == 'week' else 30)
                    period_actions = executed_actions.filter(
                        executed_at__gte=period_start,
                        executed_at__lt=period_end
                    )
                    period_logs = learning_logs.filter(action__in=period_actions)
                    
                    period_success_rate = (period_logs.filter(success_score__gt=0).count() / period_actions.count() * 100) if period_actions.count() > 0 else 0
                    
                    time_series.append({
                        'period': period_start.strftime('%Y-%m-%d'),
                        'count': period_actions.count(),
                        'success_rate': period_success_rate
                    })
            
            # 6. Generar insights
            insights = self._generate_performance_insights(
                total_actions, success_rate, avg_success_score,
                action_type_performance, time_series
            )
            
            return {
                'summary': {
                    'total_actions': total_actions,
                    'successful_actions': successful_actions,
                    'failed_actions': failed_actions,
                    'neutral_actions': neutral_actions,
                    'success_rate': success_rate,
                    'avg_success_score': avg_success_score
                },
                'action_type_performance': action_type_performance,
                'time_series': time_series,
                'insights': insights,
                'learning_level': self._calculate_learning_level()
            }
            
        except Exception as e:
            return {
                'error': f"Error analizando rendimiento: {str(e)}"
            }
    
    def adapt_decision_parameters(self):
        """
        Adapta los parámetros de decisión basados en el rendimiento histórico.
        
        Returns:
            Resultados del proceso de adaptación
        """
        try:
            if not self.decision_engine:
                self.decision_engine = DecisionEngine(user=self.user)
                
            # 1. Obtener logs de aprendizaje
            learning_logs = AgentLearningLog.objects.filter(
                action__dataset__owner=self.user if self.user else Q()
            ).order_by('-created_at')[:100]  # Usar los 100 más recientes
            
            if not learning_logs.exists():
                return {
                    "success": True,
                    "message": "No hay suficientes datos de aprendizaje para adaptar parámetros",
                    "parameters_updated": 0
                }
                
            # 2. Agrupar por tipo de acción
            action_types = {}
            for log in learning_logs:
                action_type = log.action.action_type
                if action_type not in action_types:
                    action_types[action_type] = []
                    
                action_types[action_type].append({
                    'action_data': log.action.action_data,
                    'success_score': log.success_score,
                    'metrics_before': log.metrics_before,
                    'metrics_after': log.metrics_after
                })
                
            # 3. Para cada tipo de acción, identificar patrones exitosos
            successful_patterns = {}
            failing_patterns = {}
            
            for action_type, logs in action_types.items():
                # Separar por éxito y fracaso
                successful = [log for log in logs if log['success_score'] > 0.3]
                failing = [log for log in logs if log['success_score'] < -0.3]
                
                # Identificar patrones en acciones exitosas
                if successful:
                    successful_patterns[action_type] = self._identify_success_patterns(successful)
                    
                # Identificar patrones en acciones fallidas
                if failing:
                    failing_patterns[action_type] = self._identify_failure_patterns(failing)
            
            # 4. Adaptar reglas del motor de decisiones
            parameters_updated = self._update_decision_parameters(
                successful_patterns, failing_patterns
            )
            
            # 5. Actualizar reglas de negocio automáticas si es apropiado
            rules_updated = self._update_business_rules(
                successful_patterns, failing_patterns
            )
            
            return {
                "success": True,
                "parameters_updated": parameters_updated,
                "rules_updated": rules_updated,
                "successful_patterns": successful_patterns,
                "failing_patterns": failing_patterns
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error adaptando parámetros: {str(e)}"
            }
    
    def _identify_success_patterns(self, successful_logs):
        """Identifica patrones comunes en acciones exitosas."""
        # Simplificado para la demostración
        patterns = {}
        
        # Contar ocurrencias de valores para diferentes campos
        field_counts = {}
        
        for log in successful_logs:
            action_data = log['action_data']
            if not isinstance(action_data, dict):
                continue
                
            for key, value in action_data.items():
                if key not in field_counts:
                    field_counts[key] = {}
                    
                str_value = str(value)
                if str_value not in field_counts[key]:
                    field_counts[key][str_value] = 0
                    
                field_counts[key][str_value] += 1
        
        # Identificar valores frecuentes
        for field, counts in field_counts.items():
            total = sum(counts.values())
            for value, count in counts.items():
                if count / total > 0.6:  # Si aparece en más del 60% de los casos exitosos
                    if 'frequent_values' not in patterns:
                        patterns['frequent_values'] = {}
                        
                    patterns['frequent_values'][field] = value
        
        # Identificar rangos numéricos exitosos
        numeric_ranges = {}
        
        for log in successful_logs:
            action_data = log['action_data']
            if not isinstance(action_data, dict):
                continue
                
            for key, value in action_data.items():
                try:
                    # Intentar convertir a número
                    num_value = float(value)
                    
                    if key not in numeric_ranges:
                        numeric_ranges[key] = []
                        
                    numeric_ranges[key].append(num_value)
                except (ValueError, TypeError):
                    continue
        
        # Calcular rangos para valores numéricos
        for field, values in numeric_ranges.items():
            if len(values) >= 3:  # Necesitamos suficientes puntos
                low = min(values)
                high = max(values)
                mean = sum(values) / len(values)
                
                if 'numeric_ranges' not in patterns:
                    patterns['numeric_ranges'] = {}
                    
                patterns['numeric_ranges'][field] = {
                    'min': low,
                    'max': high,
                    'mean': mean,
                    'std': np.std(values)
                }
        
        # Calcular score promedio
        avg_score = sum(log['success_score'] for log in successful_logs) / len(successful_logs)
        patterns['avg_success_score'] = avg_score
        patterns['sample_size'] = len(successful_logs)
        
        return patterns
    
    def _identify_failure_patterns(self, failing_logs):
        """Identifica patrones comunes en acciones fallidas."""
        # Similar al método anterior, pero para acciones fallidas
        patterns = {}
        
        # Contar ocurrencias de valores para diferentes campos
        field_counts = {}
        
        for log in failing_logs:
            action_data = log['action_data']
            if not isinstance(action_data, dict):
                continue
                
            for key, value in action_data.items():
                if key not in field_counts:
                    field_counts[key] = {}
                    
                str_value = str(value)
                if str_value not in field_counts[key]:
                    field_counts[key][str_value] = 0
                    
                field_counts[key][str_value] += 1
        
        # Identificar valores frecuentes
        for field, counts in field_counts.items():
            total = sum(counts.values())
            for value, count in counts.items():
                if count / total > 0.5:  # Si aparece en más del 50% de los casos fallidos
                    if 'problematic_values' not in patterns:
                        patterns['problematic_values'] = {}
                        
                    patterns['problematic_values'][field] = value
        
        # Identificar rangos numéricos problemáticos
        numeric_ranges = {}
        
        for log in failing_logs:
            action_data = log['action_data']
            if not isinstance(action_data, dict):
                continue
                
            for key, value in action_data.items():
                try:
                    # Intentar convertir a número
                    num_value = float(value)
                    
                    if key not in numeric_ranges:
                        numeric_ranges[key] = []
                        
                    numeric_ranges[key].append(num_value)
                except (ValueError, TypeError):
                    continue
        
        # Calcular rangos para valores numéricos
        for field, values in numeric_ranges.items():
            if len(values) >= 3:  # Necesitamos suficientes puntos
                low = min(values)
                high = max(values)
                
                if 'problematic_ranges' not in patterns:
                    patterns['problematic_ranges'] = {}
                    
                patterns['problematic_ranges'][field] = {
                    'min': low,
                    'max': high,
                    'mean': sum(values) / len(values),
                    'std': np.std(values)
                }
        
        # Contexto común en fallos
        metric_changes = {}
        
        for log in failing_logs:
            before = log['metrics_before']
            after = log['metrics_after']
            
            if not isinstance(before, dict) or not isinstance(after, dict):
                continue
                
            # Identificar métricas que empeoraron
            for key in before:
                if key in after:
                    try:
                        before_val = float(before[key])
                        after_val = float(after[key])
                        
                        if key not in metric_changes:
                            metric_changes[key] = []
                            
                        # Calcular cambio porcentual
                        change = ((after_val - before_val) / before_val * 100) if before_val != 0 else 0
                        metric_changes[key].append(change)
                    except (ValueError, TypeError):
                        continue
        
        # Identificar métricas que consistentemente empeoraron
        for metric, changes in metric_changes.items():
            if len(changes) >= 3:
                avg_change = sum(changes) / len(changes)
                
                if avg_change < -10:  # Empeoramiento de al menos 10%
                    if 'impacted_metrics' not in patterns:
                        patterns['impacted_metrics'] = {}
                        
                    patterns['impacted_metrics'][metric] = avg_change
        
        # Calcular score promedio
        avg_score = sum(log['success_score'] for log in failing_logs) / len(failing_logs)
        patterns['avg_failure_score'] = avg_score
        patterns['sample_size'] = len(failing_logs)
        
        return patterns
    
    def _update_decision_parameters(self, successful_patterns, failing_patterns):
        """Actualiza parámetros del motor de decisiones basado en patrones identificados."""
        # Esta implementación sería más compleja en un sistema real
        # En este caso, contamos cuántos parámetros se actualizarían
        parameter_count = 0
        
        # Procesar patrones exitosos
        for action_type, patterns in successful_patterns.items():
            # 1. Actualizar pesos para factores exitosos
            if 'frequent_values' in patterns:
                for field, value in patterns['frequent_values'].items():
                    # Aquí, en un sistema real, ajustaríamos los pesos
                    # en el motor de decisiones para favorecer estos valores
                    parameter_count += 1
                    
            # 2. Actualizar rangos para valores numéricos
            if 'numeric_ranges' in patterns:
                for field, range_info in patterns['numeric_ranges'].items():
                    # Ajustar rangos preferidos en el motor de decisiones
                    parameter_count += 1
        
        # Procesar patrones fallidos
        for action_type, patterns in failing_patterns.items():
            # 1. Reducir probabilidad de valores problemáticos
            if 'problematic_values' in patterns:
                for field, value in patterns['problematic_values'].items():
                    # Ajustar pesos para penalizar estos valores
                    parameter_count += 1
                    
            # 2. Evitar rangos problemáticos
            if 'problematic_ranges' in patterns:
                for field, range_info in patterns['problematic_ranges'].items():
                    # Ajustar rangos en el motor de decisiones
                    parameter_count += 1
                    
            # 3. Tener en cuenta métricas impactadas
            if 'impacted_metrics' in patterns:
                for metric, impact in patterns['impacted_metrics'].items():
                    # Ajustar factores para tener en cuenta estas métricas
                    parameter_count += 1
        
        return parameter_count
    
    def _update_business_rules(self, successful_patterns, failing_patterns):
        """Actualiza o crea reglas de negocio basadas en patrones aprendidos."""
        # En un sistema real, esto crearía o modificaría reglas en la BD
        # Para esta demo, simulamos el conteo de reglas que se actualizarían
        if not self.user:
            return 0  # No podemos actualizar reglas sin usuario
            
        rules_count = 0
        
        # Crear reglas basadas en patrones exitosos
        for action_type, patterns in successful_patterns.items():
            if 'numeric_ranges' in patterns and patterns['sample_size'] >= 5:
                # Para ciertos campos, crear regla de umbral
                for field, range_info in patterns['numeric_ranges'].items():
                    if field in ['percentage', 'discount', 'amount']:
                        # Ejemplo: Crear regla para mantener descuentos dentro del rango exitoso
                        # En realidad, esto crearía la regla en la base de datos
                        
                        # BusinessRule.objects.create(
                        #     name=f"Mantener {field} óptimo para {action_type}",
                        #     description=f"Regla creada automáticamente basada en aprendizaje",
                        #     rule_type="threshold",
                        #     metric=field,
                        #     condition="range",
                        #     threshold_value=range_info['mean'],
                        #     threshold_min=range_info['min'],
                        #     threshold_max=range_info['max'],
                        #     action_type="suggest",
                        #     action_data={
                        #         "action_type": action_type,
                        #         "suggested_value": range_info['mean'],
                        #         "reason": "Valor optimizado mediante aprendizaje automático"
                        #     },
                        #     priority=7,
                        #     is_active=True,
                        #     owner=self.user
                        # )
                        
                        rules_count += 1
        
        # Crear reglas para evitar patrones fallidos
        for action_type, patterns in failing_patterns.items():
            if 'problematic_ranges' in patterns and patterns['sample_size'] >= 5:
                for field, range_info in patterns['problematic_ranges'].items():
                    if field in ['percentage', 'discount', 'amount']:
                        # Ejemplo: Crear regla para evitar valores problemáticos
                        
                        # BusinessRule.objects.create(
                        #     name=f"Evitar {field} problemático para {action_type}",
                        #     description=f"Regla creada automáticamente para evitar valores problemáticos",
                        #     rule_type="risk",
                        #     metric=field,
                        #     condition="outside_range",
                        #     threshold_min=range_info['min'],
                        #     threshold_max=range_info['max'],
                        #     action_type="suggest",
                        #     action_data={
                        #         "action_type": "warning",
                        #         "message": f"Valor de {field} en zona de riesgo basado en resultados históricos",
                        #         "reason": "Valor identificado como problemático mediante aprendizaje"
                        #     },
                        #     priority=8,
                        #     is_active=True,
                        #     owner=self.user
                        # )
                        
                        rules_count += 1
                        
            # Crear alertas para métricas impactadas
            if 'impacted_metrics' in patterns:
                for metric, impact in patterns['impacted_metrics'].items():
                    if abs(impact) > 15:  # Solo para impactos significativos
                        # Ejemplo: Crear regla para alertar cuando la métrica cambia significativamente
                        
                        # BusinessRule.objects.create(
                        #     name=f"Alertar cambios en {metric}",
                        #     description=f"Alerta cuando {metric} cambia significativamente",
                        #     rule_type="anomaly",
                        #     metric=metric,
                        #     condition="change",
                        #     threshold_value=10,  # Alertar con cambios mayores al 10%
                        #     action_type="notify",
                        #     action_data={
                        #         "action_type": "warning",
                        #         "message": f"Cambio significativo detectado en {metric}",
                        #         "reason": "Métrica asociada con resultados negativos"
                        #     },
                        #     priority=6,
                        #     is_active=True,
                        #     owner=self.user
                        # )
                        
                        rules_count += 1
        
        return rules_count
    
    def _generate_performance_insights(self, total_actions, success_rate, avg_success_score,
                                      action_type_performance, time_series):
        """Genera insights sobre el rendimiento del agente IA."""
        insights = []
        
        # Insight general sobre rendimiento
        if total_actions > 0:
            if success_rate > 75:
                insights.append(
                    "El agente IA está teniendo un excelente desempeño con una alta tasa de éxito. "
                    "Las decisiones y recomendaciones han sido en general muy acertadas."
                )
            elif success_rate > 50:
                insights.append(
                    "El agente IA está operando con un rendimiento aceptable, pero hay oportunidades "
                    "para mejorar la tasa de éxito mediante ajustes en los parámetros de decisión."
                )
            else:
                insights.append(
                    "El rendimiento del agente IA está por debajo de lo esperado. Es recomendable "
                    "revisar las reglas de negocio y los parámetros del motor de decisiones."
                )
        
        # Insights sobre tipos de acciones específicas
        best_action_type = None
        worst_action_type = None
        best_rate = 0
        worst_rate = 100
        
        for action_type, performance in action_type_performance.items():
            if performance['count'] >= 3:  # Solo considerar tipos con suficientes acciones
                if performance['success_rate'] > best_rate:
                    best_rate = performance['success_rate']
                    best_action_type = action_type
                    
                if performance['success_rate'] < worst_rate:
                    worst_rate = performance['success_rate']
                    worst_action_type = action_type
        
        if best_action_type and best_rate > 70:
            insights.append(
                f"Las acciones de tipo '{best_action_type}' han tenido un desempeño sobresaliente "
                f"con una tasa de éxito del {best_rate:.1f}%. El agente muestra especial aptitud para "
                f"este tipo de decisiones."
            )
            
        if worst_action_type and worst_rate < 40:
            insights.append(
                f"Las acciones de tipo '{worst_action_type}' han mostrado un desempeño inferior "
                f"con una tasa de éxito de solo {worst_rate:.1f}%. Se recomienda revisar los "
                f"parámetros y reglas para este tipo de decisiones."
            )
        
        # Insights sobre tendencias temporales
        if len(time_series) >= 3:
            # Verificar si hay tendencia de mejora o empeoramiento
            recent_rates = [period['success_rate'] for period in time_series[-3:]]
            early_rates = [period['success_rate'] for period in time_series[:3]]
            
            if sum(recent_rates)/3 > sum(early_rates)/3 + 10:  # Mejora de más del 10%
                insights.append(
                    "Se observa una tendencia positiva en el rendimiento del agente a lo largo del tiempo. "
                    "El aprendizaje automático está mejorando la calidad de las decisiones."
                )
            elif sum(recent_rates)/3 < sum(early_rates)/3 - 10:  # Deterioro de más del 10%
                insights.append(
                    "Existe una tendencia negativa en el rendimiento reciente. Es recomendable "
                    "revisar los cambios recientes en los parámetros del sistema o en las condiciones "
                    "de operación."
                )
        
        # Guardar insights para uso futuro
        self.insights = insights
        self.recommendation_count = total_actions
        
        return insights
    
    def _calculate_learning_level(self):
        """Calcula el nivel de aprendizaje del sistema basado en la cantidad de datos."""
        # Obtener conteo de logs de aprendizaje
        learning_count = AgentLearningLog.objects.count()
        
        if learning_count > 100:
            return {
                'level': 'avanzado',
                'progress': 90,
                'description': 'El sistema ha acumulado suficientes datos para tomar decisiones muy informadas.'
            }
        elif learning_count > 50:
            return {
                'level': 'intermedio',
                'progress': 60,
                'description': 'El sistema está aprendiendo activamente y mejorando sus decisiones.'
            }
        elif learning_count > 20:
            return {
                'level': 'básico',
                'progress': 30,
                'description': 'El sistema ha comenzado a aprender de sus acciones pasadas.'
            }
        else:
            return {
                'level': 'inicial',
                'progress': 10,
                'description': 'El sistema está comenzando a recopilar datos de aprendizaje.'
            }
    
    def get_recommendation_insights(self):
        """Obtiene insights para mejorar las recomendaciones del agente."""
        # Análisis de rendimiento
        performance = self.analyze_performance()
        
        # Adaptación de parámetros
        adaptation = self.adapt_decision_parameters()
        
        # Generar recomendaciones para mejorar el sistema
        recommendations = []
        
        # Recomendaciones basadas en rendimiento
        if 'summary' in performance and performance['summary']['total_actions'] > 0:
            if performance['summary']['success_rate'] < 60:
                recommendations.append({
                    'area': 'reglas_de_negocio',
                    'action': 'revisar',
                    'description': 'Revisar y ajustar las reglas de negocio para mejorar la precisión de las decisiones.',
                    'priority': 'alta'
                })
                
            # Recomendar enfoque en tipos de acciones con bajo rendimiento
            if 'action_type_performance' in performance:
                for action_type, perf in performance['action_type_performance'].items():
                    if perf['count'] >= 3 and perf['success_rate'] < 40:
                        recommendations.append({
                            'area': 'tipo_accion',
                            'action_type': action_type,
                            'action': 'optimizar',
                            'description': f'Optimizar parámetros para acciones de tipo "{action_type}" que tienen bajo rendimiento.',
                            'priority': 'alta'
                        })
        
        # Recomendaciones basadas en nivel de aprendizaje
        learning_level = self._calculate_learning_level()
        if learning_level['level'] in ['inicial', 'básico']:
            recommendations.append({
                'area': 'datos_aprendizaje',
                'action': 'aumentar',
                'description': 'Aumentar la cantidad de datos de aprendizaje proporcionando feedback para más acciones del agente.',
                'priority': 'media'
            })
            
        # Recomendaciones basadas en patrones
        if 'successful_patterns' in adaptation:
            for action_type, patterns in adaptation.get('successful_patterns', {}).items():
                if 'numeric_ranges' in patterns and patterns['sample_size'] >= 5:
                    # Sugerir automatización de valores exitosos
                    recommendations.append({
                        'area': 'automatizacion',
                        'action_type': action_type,
                        'action': 'automatizar',
                        'description': f'Considerar automatizar acciones de tipo "{action_type}" con valores que han demostrado éxito.',
                        'priority': 'media'
                    })
        
        return {
            'performance_summary': performance.get('summary', {}),
            'learning_level': learning_level,
            'recommendations': recommendations,
            'insights': self.insights
        }