# api/decision_engine.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Dataset, BusinessRule, MonitoringLog, AgentAction, BusinessContext, AgentLearningLog
from .autonomous_monitor import AutonomousMonitor

class DecisionEngine:
    """
    Motor de decisiones inteligente que evalúa alternativas, 
    calcula probabilidades y toma decisiones optimizadas basadas en datos.
    """
    
    def __init__(self, dataset_id=None, user=None, context_id=None):
        self.dataset_id = dataset_id
        self.user = user
        self.monitor = AutonomousMonitor(dataset_id) if dataset_id else None
        self.business_context = self._load_business_context(context_id)
        self.historic_decisions = []
        self.decision_factors = {}
        self.decision_weights = {}
        self.learning_data = []
        
    def _load_business_context(self, context_id=None):
        """Carga el contexto de negocio para mejorar decisiones."""
        if not self.user:
            return None
            
        try:
            if context_id:
                return BusinessContext.objects.get(id=context_id, owner=self.user)
            else:
                # Cargar el contexto más relevante
                return BusinessContext.objects.filter(owner=self.user).first()
        except BusinessContext.DoesNotExist:
            return None
            
    def analyze_options(self, situation_data, options, objective='optimize_sales'):
        """
        Analiza múltiples opciones para una situación dada y determina la mejor.
        
        Args:
            situation_data: Datos sobre la situación actual
            options: Lista de alternativas a evaluar
            objective: Objetivo a optimizar ('optimize_sales', 'reduce_costs', etc.)
            
        Returns:
            Opción recomendada con análisis detallado
        """
        if not options or len(options) == 0:
            return {"error": "No se proporcionaron opciones para evaluar"}
            
        try:
            results = []
            
            # 1. Establecer factores relevantes según el objetivo
            self._set_decision_factors(objective)
            
            # 2. Evaluar cada opción con múltiples factores
            for option in options:
                evaluation = self._evaluate_option(option, situation_data, objective)
                results.append({
                    "option": option,
                    "score": evaluation["total_score"],
                    "confidence": evaluation["confidence"],
                    "factors": evaluation["factor_scores"],
                    "expected_outcome": evaluation["expected_outcome"],
                    "risks": evaluation["risks"]
                })
                
            # 3. Ordenar opciones por puntaje
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # 4. Enriquecer con contexto de negocio
            if self.business_context:
                for result in results:
                    self._apply_business_context(result, objective)
                    
            # 5. Guardar decisión para aprendizaje futuro
            self.historic_decisions.append({
                "timestamp": timezone.now(),
                "situation": situation_data,
                "options": options,
                "results": results,
                "objective": objective
            })
            
            # Retornar resultados completos
            return {
                "recommended_option": results[0]["option"],
                "all_options": results,
                "objective": objective,
                "reasoning": self._generate_reasoning(results[0], situation_data, objective)
            }
            
        except Exception as e:
            return {"error": f"Error en el análisis de opciones: {str(e)}"}
            
    def _set_decision_factors(self, objective):
        """Define factores de decisión y sus pesos según el objetivo."""
        if objective == 'optimize_sales':
            self.decision_factors = {
                "revenue_impact": "Impacto en ingresos",
                "customer_satisfaction": "Satisfacción del cliente",
                "market_share": "Participación de mercado",
                "brand_impact": "Impacto en la marca",
                "operational_complexity": "Complejidad operativa"
            }
            
            self.decision_weights = {
                "revenue_impact": 0.4,
                "customer_satisfaction": 0.3,
                "market_share": 0.15,
                "brand_impact": 0.1,
                "operational_complexity": 0.05
            }
            
        elif objective == 'reduce_costs':
            self.decision_factors = {
                "cost_savings": "Ahorro de costos",
                "efficiency_improvement": "Mejora de eficiencia",
                "implementation_cost": "Costo de implementación",
                "time_to_implement": "Tiempo de implementación",
                "quality_impact": "Impacto en calidad"
            }
            
            self.decision_weights = {
                "cost_savings": 0.4,
                "efficiency_improvement": 0.2,
                "implementation_cost": 0.2,
                "time_to_implement": 0.1,
                "quality_impact": 0.1
            }
            
        elif objective == 'expand_market':
            self.decision_factors = {
                "new_customer_potential": "Potencial de nuevos clientes",
                "competitive_advantage": "Ventaja competitiva",
                "investment_required": "Inversión requerida",
                "risk_level": "Nivel de riesgo",
                "long_term_potential": "Potencial a largo plazo"
            }
            
            self.decision_weights = {
                "new_customer_potential": 0.35,
                "competitive_advantage": 0.25,
                "investment_required": 0.15,
                "risk_level": 0.15,
                "long_term_potential": 0.1
            }
        else:
            # Objetivo genérico
            self.decision_factors = {
                "benefit": "Beneficio",
                "cost": "Costo",
                "risk": "Riesgo",
                "time": "Tiempo",
                "alignment": "Alineación estratégica"
            }
            
            self.decision_weights = {
                "benefit": 0.3,
                "cost": 0.25,
                "risk": 0.2,
                "time": 0.15,
                "alignment": 0.1
            }
            
    def _evaluate_option(self, option, situation_data, objective):
        """Evalúa una opción asignando puntajes para cada factor."""
        # 1. Inicializar puntajes vacíos
        factor_scores = {}
        
        # 2. Evaluar cada factor
        for factor, weight in self.decision_weights.items():
            # Esta es una implementación simplificada
            # En un sistema real, cada factor tendría su propia lógica de evaluación
            
            # Simular evaluación para cada factor
            if factor == "revenue_impact":
                # Lógica para estimar impacto en ingresos
                score = self._estimate_revenue_impact(option, situation_data)
            elif factor == "customer_satisfaction":
                score = self._estimate_customer_satisfaction(option, situation_data)
            else:
                # Factores genéricos
                score = self._general_factor_evaluation(factor, option, situation_data)
                
            factor_scores[factor] = score
            
        # 3. Calcular puntaje ponderado total
        total_score = sum(factor_scores[factor] * weight 
                          for factor, weight in self.decision_weights.items())
        
        # 4. Determinar confianza basada en calidad de datos y factores
        data_quality = self._assess_data_quality(situation_data)
        factor_coverage = len(factor_scores) / len(self.decision_weights)
        confidence = 0.4 * data_quality + 0.6 * factor_coverage
        
        # 5. Evaluar resultados esperados y riesgos
        expected_outcome = self._project_outcome(option, factor_scores, situation_data)
        risks = self._identify_risks(option, factor_scores, situation_data)
        
        return {
            "factor_scores": factor_scores,
            "total_score": total_score,
            "confidence": confidence,
            "expected_outcome": expected_outcome,
            "risks": risks
        }
    
    def _estimate_revenue_impact(self, option, situation_data):
        """Estima el impacto en ingresos de una opción."""
        # En una implementación real, esto utilizaría modelos de predicción
        # y análisis de datos históricos para estimar el impacto
        
        # Obtener datos históricos relevantes
        if self.dataset_id:
            try:
                dataset = Dataset.objects.get(id=self.dataset_id)
                historic_data = self._get_historic_data()
                
                # Análisis de tendencias
                if historic_data is not None and 'sales' in historic_data:
                    # Calcular impacto potencial basado en tendencias históricas
                    # Implementación simplificada
                    avg_growth = historic_data['sales'].pct_change().mean()
                    impact_modifier = 1.0
                    
                    # Ajustar según el tipo de opción
                    if 'price_increase' in option:
                        impact_modifier = 0.8  # Aumento de precio podría reducir volumen
                    elif 'discount' in option:
                        impact_modifier = 1.2  # Descuentos tienden a aumentar volumen
                    elif 'expansion' in option:
                        impact_modifier = 1.5  # Expansión tiene alto potencial
                        
                    # Calcular puntaje (normalizado entre 0-1)
                    base_impact = avg_growth * impact_modifier
                    return min(max(0.5 + base_impact, 0), 1)
            except Exception:
                pass
                
        # Fallback a evaluación básica si no hay suficientes datos
        if 'price_increase' in option:
            return 0.6
        elif 'discount' in option:
            return 0.7
        elif 'expansion' in option:
            return 0.8
        else:
            return 0.5
    
    def _estimate_customer_satisfaction(self, option, situation_data):
        """Estima el impacto en satisfacción del cliente."""
        # Implementación simplificada
        if 'price_increase' in option:
            return 0.3  # Aumento de precio suele reducir satisfacción
        elif 'quality_improvement' in option:
            return 0.9  # Mejoras de calidad aumentan satisfacción
        elif 'discount' in option:
            return 0.8  # Descuentos generalmente son bien recibidos
        else:
            return 0.5
    
    def _general_factor_evaluation(self, factor, option, situation_data):
        """Evaluación genérica para otros factores."""
        # En producción, cada factor tendría su lógica especializada
        
        # Para esta demo, valores medios con variaciones
        base_score = 0.5
        
        # Ajustes basados en tipo de opción
        if 'high_risk' in option:
            if factor == 'risk_level':
                base_score = 0.2  # Mayor riesgo = puntaje bajo
        elif 'expansion' in option:
            if factor in ['market_share', 'new_customer_potential']:
                base_score = 0.8
        elif 'cost_cutting' in option:
            if factor in ['cost_savings', 'efficiency_improvement']:
                base_score = 0.85
            elif factor == 'quality_impact':
                base_score = 0.4  # Reducción de costos puede afectar calidad
                
        # Variabilidad controlada
        variance = 0.1
        score = base_score + (np.random.random() * 2 - 1) * variance
        
        # Asegurar rango 0-1
        return min(max(score, 0), 1)
    
    def _assess_data_quality(self, situation_data):
        """Evalúa la calidad de los datos de situación."""
        # Si no hay datos, confianza mínima
        if not situation_data:
            return 0.3
            
        # Verificar completitud (campos clave presentes)
        expected_fields = ['period', 'metrics', 'trends']
        completeness = sum(1 for field in expected_fields if field in situation_data) / len(expected_fields)
        
        # Verificar actualidad
        recency = 0.5  # Valor por defecto
        if 'timestamp' in situation_data:
            age_days = (timezone.now() - situation_data['timestamp']).days
            recency = max(0, min(1, 1 - (age_days / 30)))  # Datos de menos de 30 días
            
        # Verificar volumen de datos
        volume = 0.5  # Valor por defecto
        if 'metrics' in situation_data and isinstance(situation_data['metrics'], dict):
            volume = min(1, len(situation_data['metrics']) / 5)  # Al menos 5 métricas para máxima confianza
            
        # Ponderación final
        return 0.4 * completeness + 0.4 * recency + 0.2 * volume
    
    def _project_outcome(self, option, factor_scores, situation_data):
        """Proyecta el resultado esperado de implementar la opción."""
        # Determinar métricas clave según factores
        key_metrics = {}
        
        # Modelar impacto en métricas clave
        if 'revenue_impact' in factor_scores:
            revenue_score = factor_scores['revenue_impact']
            # Traducir a impacto porcentual (-10% a +25%)
            revenue_impact = -10 + (revenue_score * 35)
            key_metrics['revenue_change'] = f"{revenue_impact:+.1f}%"
            
        if 'customer_satisfaction' in factor_scores:
            satisfaction_score = factor_scores['customer_satisfaction']
            # Traducir a cambio en NPS (-20 a +20)
            nps_change = -20 + (satisfaction_score * 40)
            key_metrics['nps_change'] = f"{nps_change:+.0f} puntos"
            
        if 'cost_savings' in factor_scores:
            savings_score = factor_scores['cost_savings']
            # Traducir a reducción de costos (0% a 20%)
            cost_reduction = savings_score * 20
            key_metrics['cost_reduction'] = f"{cost_reduction:.1f}%"
            
        # Generar descripción narrativa
        narrative = self._generate_outcome_narrative(option, key_metrics)
            
        return {
            "key_metrics": key_metrics,
            "narrative": narrative,
            "timeframe": "corto plazo" if option.get('timeframe') == 'short' else "mediano plazo"
        }
    
    def _identify_risks(self, option, factor_scores, situation_data):
        """Identifica riesgos potenciales de la opción."""
        risks = []
        
        # Riesgos basados en puntajes bajos
        for factor, score in factor_scores.items():
            if score < 0.3:
                risks.append({
                    "factor": self.decision_factors.get(factor, factor),
                    "severity": "alta" if score < 0.2 else "media",
                    "description": f"Bajo rendimiento en {self.decision_factors.get(factor, factor)}"
                })
                
        # Riesgos específicos por tipo de opción
        if 'price_increase' in option:
            risks.append({
                "factor": "Retención de clientes",
                "severity": "media",
                "description": "Posible pérdida de clientes sensibles al precio"
            })
            
        if 'new_market' in option:
            risks.append({
                "factor": "Conocimiento del mercado",
                "severity": "alta",
                "description": "Incertidumbre por falta de datos históricos en nuevo mercado"
            })
            
        if 'cost_cutting' in option:
            risks.append({
                "factor": "Calidad del servicio",
                "severity": "media",
                "description": "Posible impacto en calidad si la reducción de costos es demasiado agresiva"
            })
            
        return risks
    
    def _generate_outcome_narrative(self, option, key_metrics):
        """Genera una descripción narrativa del resultado esperado."""
        description = f"La implementación de esta opción se espera que "
        
        # Agregar efectos en ingresos
        if 'revenue_change' in key_metrics:
            change = float(key_metrics['revenue_change'].replace('%', '').replace('+', ''))
            if change > 0:
                description += f"incremente los ingresos en aproximadamente un {key_metrics['revenue_change']} "
            elif change < 0:
                description += f"cause una reducción temporal de ingresos de {key_metrics['revenue_change']} "
            else:
                description += "mantenga los ingresos en niveles actuales "
                
        # Agregar efectos en satisfacción
        if 'nps_change' in key_metrics:
            change = float(key_metrics['nps_change'].replace(' puntos', '').replace('+', ''))
            if change > 0:
                description += f"y mejore la satisfacción del cliente con un incremento de NPS de {key_metrics['nps_change']}. "
            elif change < 0:
                description += f"con un posible impacto en la satisfacción del cliente de {key_metrics['nps_change']} en NPS. "
            else:
                description += "sin afectar significativamente la satisfacción del cliente. "
                
        # Agregar efectos en costos
        if 'cost_reduction' in key_metrics:
            description += f"Se proyecta una reducción de costos del {key_metrics['cost_reduction']}. "
            
        # Agregar cierre
        if option.get('timeframe') == 'short':
            description += "Los resultados deberían ser visibles en un plazo de 30-60 días."
        else:
            description += "Se espera que los efectos completos se materialicen en 3-6 meses."
            
        return description
            
    def _apply_business_context(self, result, objective):
        """Ajusta los resultados basándose en el contexto de negocio."""
        if not self.business_context:
            return
            
        # Ajuste por temporada
        if hasattr(self.business_context, 'seasonality_data'):
            current_month = timezone.now().month
            
            # Verificar si estamos en temporada alta
            is_high_season = False
            if isinstance(self.business_context.seasonality_data, dict):
                if str(current_month) in self.business_context.seasonality_data.get('high_season', []):
                    is_high_season = True
                    
            # Ajustar score según temporada
            if is_high_season:
                # En temporada alta, favorecer opciones de expansión
                if 'expansion' in result['option'] or 'growth' in result['option']:
                    result['score'] *= 1.2
                    result['factors']['seasonal_context'] = "Temporada alta favorable para crecimiento"
                    
        # Ajuste por tendencias de mercado
        if hasattr(self.business_context, 'market_trends'):
            market_trends = self.business_context.market_trends
            
            if isinstance(market_trends, dict):
                # Verificar tendencias relevantes
                if 'growing_categories' in market_trends and isinstance(market_trends['growing_categories'], list):
                    for category in market_trends['growing_categories']:
                        if category.lower() in str(result['option']).lower():
                            result['score'] *= 1.15
                            result['factors']['market_trend'] = f"Alineado con tendencia de mercado: {category}"
                            break
    
    def _generate_reasoning(self, top_option, situation_data, objective):
        """Genera una explicación detallada del razonamiento detrás de la recomendación."""
        factor_explanations = []
        
        # Explicar los principales factores
        for factor, score in top_option['factors'].items():
            if factor in self.decision_factors:
                weight = self.decision_weights.get(factor, 0)
                importance = "alta" if weight > 0.3 else "media" if weight > 0.15 else "baja"
                
                factor_explanations.append({
                    "factor": self.decision_factors[factor],
                    "score": score,
                    "weight": weight,
                    "importance": importance,
                    "contribution": score * weight,
                    "explanation": self._explain_factor_score(factor, score, top_option['option'])
                })
                
        # Ordenar factores por contribución
        factor_explanations.sort(key=lambda x: x['contribution'], reverse=True)
        
        # Generar explicación narrativa
        narrative = self._compose_reasoning_narrative(top_option, factor_explanations, objective)
        
        return {
            "factor_explanations": factor_explanations,
            "narrative": narrative,
            "confidence_explanation": self._explain_confidence(top_option['confidence']),
            "business_context": self._explain_business_context(top_option)
        }
    
    def _explain_factor_score(self, factor, score, option):
        """Genera una explicación para el puntaje de un factor específico."""
        if factor == "revenue_impact":
            if score > 0.8:
                return "Se proyecta un impacto muy positivo en los ingresos basado en el análisis de tendencias históricas y el tipo de acción propuesta."
            elif score > 0.6:
                return "Se espera un impacto positivo moderado en los ingresos según análisis de datos."
            elif score > 0.4:
                return "El impacto en ingresos se proyecta como neutral o ligeramente positivo."
            else:
                return "Existe riesgo de impacto negativo en los ingresos a corto plazo, aunque podría haber beneficios a largo plazo."
                
        elif factor == "customer_satisfaction":
            if score > 0.8:
                return "La acción propuesta tiende a aumentar significativamente la satisfacción del cliente según datos históricos."
            elif score > 0.6:
                return "Se espera un efecto positivo en la satisfacción del cliente."
            elif score > 0.4:
                return "El impacto en la satisfacción del cliente será probablemente neutral."
            else:
                return "Existe riesgo de impacto negativo en la satisfacción del cliente, lo que requeriría acciones mitigantes."
                
        # Explicaciones genéricas para otros factores
        elif score > 0.7:
            return f"El desempeño es muy bueno para este factor, lo que contribuye positivamente a la evaluación general."
        elif score > 0.5:
            return f"El desempeño es adecuado para este factor."
        else:
            return f"Este factor presenta un desempeño inferior al ideal, lo que reduce la puntuación general."
    
    def _explain_confidence(self, confidence):
        """Explica el nivel de confianza en la recomendación."""
        if confidence > 0.8:
            return "Alta confianza basada en datos históricos sólidos y análisis completo de todos los factores relevantes."
        elif confidence > 0.6:
            return "Confianza moderada. La recomendación se basa en un buen análisis, aunque con algunas limitaciones en los datos disponibles."
        elif confidence > 0.4:
            return "Confianza moderada-baja. Existen importantes incertidumbres en los datos o factores analizados."
        else:
            return "Baja confianza. Esta recomendación debe considerarse preliminar debido a la limitada disponibilidad de datos relevantes."
    
    def _explain_business_context(self, option):
        """Proporciona contexto de negocio para la recomendación."""
        if not self.business_context:
            return "No se ha proporcionado contexto de negocio específico para esta evaluación."
            
        context_explanation = f"Esta recomendación considera el contexto de negocio para {self.business_context.name}"
        
        # Añadir información de temporalidad
        current_month = timezone.now().month
        season_info = ""
        
        if hasattr(self.business_context, 'seasonality_data') and isinstance(self.business_context.seasonality_data, dict):
            if str(current_month) in self.business_context.seasonality_data.get('high_season', []):
                season_info = "Actualmente en temporada alta, lo que favorece acciones de crecimiento."
            elif str(current_month) in self.business_context.seasonality_data.get('low_season', []):
                season_info = "Actualmente en temporada baja, lo que puede ser apropiado para acciones de optimización interna."
                
        if season_info:
            context_explanation += f". {season_info}"
            
        # Añadir información de mercado
        if hasattr(self.business_context, 'market_trends') and isinstance(self.business_context.market_trends, dict):
            if 'market_state' in self.business_context.market_trends:
                context_explanation += f" El mercado está en estado {self.business_context.market_trends['market_state']}."
                
        return context_explanation
    
    def _compose_reasoning_narrative(self, top_option, factor_explanations, objective):
        """Compone una narrativa que explica el razonamiento del agente."""
        # Introducción adaptada al objetivo
        narrative = "Basado en el análisis de los datos disponibles"
        
        if self.business_context:
            narrative += f" y el contexto de negocio para {self.business_context.business_type} en {self.business_context.region}"
            
        narrative += f", recomiendo {top_option['option']} como la mejor opción para {objective.replace('_', ' ')}.\n\n"
        
        # Explicación de los principales factores
        narrative += "Esta recomendación se basa principalmente en los siguientes factores:\n\n"
        
        # Tomar los 3 factores más importantes
        top_factors = factor_explanations[:3]
        for i, factor in enumerate(top_factors):
            narrative += f"{i+1}. {factor['factor']}: {factor['explanation']}\n"
            
        # Añadir información sobre riesgos
        if top_option['risks']:
            narrative += "\nSin embargo, es importante considerar los siguientes riesgos:\n\n"
            
            for i, risk in enumerate(top_option['risks']):
                narrative += f"- {risk['description']} (Severidad: {risk['severity']})\n"
                
        # Cerrar con resultado esperado
        narrative += f"\n{top_option['expected_outcome']['narrative']}"
        
        return narrative
    
    def _get_historic_data(self):
        """Obtiene datos históricos para análisis."""
        if not self.dataset_id:
            return None
            
        try:
            # En implementación real, obtendría datos reales
            # Para esta demo, simulamos un dataframe con datos
            
            # Simular fechas y ventas para los últimos 12 meses
            dates = pd.date_range(end=datetime.now(), periods=12, freq='M')
            sales = np.random.normal(10000, 2000, size=12) * np.linspace(0.9, 1.1, 12)  # Tendencia creciente
            
            return pd.DataFrame({
                'date': dates,
                'sales': sales
            })
        except Exception:
            return None
    
    def recommend_action(self, dataset_id, action_type, context=None):
        """
        Recomienda una acción específica basada en el tipo y contexto.
        
        Args:
            dataset_id: ID del dataset sobre el que recomendar
            action_type: Tipo de acción ('pricing', 'inventory', 'marketing', etc.)
            context: Contexto adicional para la recomendación
            
        Returns:
            Acción recomendada con análisis
        """
        self.dataset_id = dataset_id
        
        try:
            # 1. Obtener análisis del monitor autónomo
            if not self.monitor or self.monitor.dataset_id != dataset_id:
                self.monitor = AutonomousMonitor(dataset_id)
                
            analysis = self.monitor.analyze_dataset()
            
            # 2. Preparar opciones según el tipo de acción solicitada
            if action_type == 'pricing':
                options = self._generate_pricing_options(analysis)
            elif action_type == 'inventory':
                options = self._generate_inventory_options(analysis)
            elif action_type == 'marketing':
                options = self._generate_marketing_options(analysis)
            else:
                return {"error": f"Tipo de acción no soportado: {action_type}"}
                
            # 3. Si no hay opciones, retornar mensaje
            if not options or len(options) == 0:
                return {"error": "No se pudieron generar opciones válidas con los datos disponibles"}
                
            # 4. Elegir objetivo apropiado según tipo de acción
            objective = {
                'pricing': 'optimize_sales',
                'inventory': 'reduce_costs',
                'marketing': 'expand_market'
            }.get(action_type, 'optimize_sales')
            
            # 5. Analizar opciones y recomendar la mejor
            situation_data = {
                'analysis': analysis,
                'timestamp': timezone.now(),
                'context': context
            }
            
            result = self.analyze_options(situation_data, options, objective)
            
            # 6. Registrar la acción recomendada en la base de datos
            if 'recommended_option' in result and not 'error' in result:
                self._register_recommended_action(dataset_id, action_type, result)
                
            return result
            
        except Exception as e:
            return {"error": f"Error generando recomendación: {str(e)}"}
    
    def _generate_pricing_options(self, analysis):
        """Genera opciones de precio basadas en el análisis."""
        options = []
        
        # Verificar si tenemos datos de tendencia de ventas
        if 'trends' in analysis and 'sales_trend' in analysis['trends']:
            trend = analysis['trends']['sales_trend']
            
            # Estrategias basadas en tendencia
            if trend['label'] == 'fuerte_crecimiento':
                # En crecimiento fuerte, podemos aumentar precios
                options.append({
                    'action': 'price_increase',
                    'description': 'Aumentar precios en 5-8% aprovechando la fuerte demanda',
                    'percentage': 6.5,
                    'timeframe': 'short'
                })
                options.append({
                    'action': 'tiered_pricing',
                    'description': 'Introducir nivel premium con características adicionales',
                    'premium_uplift': 20,
                    'timeframe': 'medium'
                })
                
            elif trend['label'] in ['crecimiento_moderado', 'estable']:
                # En crecimiento moderado, optimizar estructura
                options.append({
                    'action': 'price_increase',
                    'description': 'Aumentar precios selectivamente en 3-5%',
                    'percentage': 4,
                    'timeframe': 'short'
                })
                options.append({
                    'action': 'price_optimization',
                    'description': 'Optimizar precios por segmento de cliente',
                    'segments': ['alto valor', 'ocasional', 'nuevo'],
                    'timeframe': 'medium'
                })
                
            elif trend['label'] in ['declive_moderado', 'declive_fuerte']:
                # En declive, estrategias de retención
                options.append({
                    'action': 'discount_promotion',
                    'description': 'Ofrecer descuentos temporales de 10-15%',
                    'percentage': 12,
                    'duration_days': 30,
                    'timeframe': 'short'
                })
                options.append({
                    'action': 'value_bundling',
                    'description': 'Crear paquetes de valor con productos complementarios',
                    'discount': 8,
                    'timeframe': 'medium'
                })
                
        # Añadir siempre algunas estrategias genéricas
        options.append({
            'action': 'competitive_match',
            'description': 'Ajustar precios para coincidir con la competencia directa',
            'timeframe': 'short'
        })
        options.append({
            'action': 'psychological_pricing',
            'description': 'Implementar precios psicológicos (ej. S/99 en lugar de S/100)',
            'timeframe': 'short'
        })
        
        return options
    
    def _generate_inventory_options(self, analysis):
        """Genera opciones de inventario basadas en el análisis."""
        options = []
        
        # Verificar tendencias y forecast
        trends_available = 'trends' in analysis and 'sales_trend' in analysis['trends']
        forecast_available = 'forecasts' in analysis and 'expected_change_pct' in analysis['forecasts']
        
        if trends_available and forecast_available:
            trend = analysis['trends']['sales_trend']['label']
            forecast_change = analysis['forecasts']['expected_change_pct']
            
            # Crecimiento proyectado significativo
            if forecast_change > 10:
                options.append({
                    'action': 'increase_inventory',
                    'description': 'Aumentar niveles de inventario en 20-25%',
                    'percentage': 22,
                    'timeframe': 'short'
                })
                options.append({
                    'action': 'supplier_agreement',
                    'description': 'Negociar acuerdos con proveedores para entregas más frecuentes',
                    'frequency': 'semanal',
                    'timeframe': 'medium'
                })
                
            # Crecimiento moderado o estable
            elif forecast_change > -5:
                options.append({
                    'action': 'optimize_inventory',
                    'description': 'Optimizar niveles de inventario con análisis ABC',
                    'categories': ['A', 'B', 'C'],
                    'timeframe': 'medium'
                })
                options.append({
                    'action': 'just_in_time',
                    'description': 'Implementar sistema Just-In-Time para productos de alta rotación',
                    'timeframe': 'medium'
                })
                
            # Declive proyectado
            else:
                options.append({
                    'action': 'reduce_inventory',
                    'description': 'Reducir niveles de inventario en 15-20%',
                    'percentage': 17,
                    'timeframe': 'short'
                })
                options.append({
                    'action': 'clearance_sale',
                    'description': 'Liquidar inventario de baja rotación con descuentos',
                    'discount': 30,
                    'timeframe': 'short'
                })
        
        # Opciones genéricas
        options.append({
            'action': 'inventory_audit',
            'description': 'Realizar auditoría completa de inventario',
            'timeframe': 'short'
        })
        options.append({
            'action': 'inventory_software',
            'description': 'Implementar sistema de gestión de inventario',
            'timeframe': 'medium'
        })
        
        return options
    
    def _generate_marketing_options(self, analysis):
        """Genera opciones de marketing basadas en el análisis."""
        options = []
        
        # Verificar si tenemos datos de oportunidades
        opportunities_available = 'opportunities' in analysis
        
        if opportunities_available:
            # Opciones basadas en categorías
            if 'category_insights' in analysis['opportunities']:
                best_category = analysis['opportunities']['category_insights'].get('best_category')
                worst_category = analysis['opportunities']['category_insights'].get('worst_category')
                
                if best_category:
                    options.append({
                        'action': 'category_promotion',
                        'description': f'Campaña promocional para categoría de alto rendimiento: {best_category}',
                        'category': best_category,
                        'budget_allocation': 60,
                        'timeframe': 'short'
                    })
                
                if worst_category:
                    options.append({
                        'action': 'category_revitalization',
                        'description': f'Campaña de revitalización para categoría de bajo rendimiento: {worst_category}',
                        'category': worst_category,
                        'budget_allocation': 40,
                        'timeframe': 'medium'
                    })
                    
            # Opciones basadas en regiones
            if 'region_insights' in analysis['opportunities']:
                best_region = analysis['opportunities']['region_insights'].get('best_region')
                worst_region = analysis['opportunities']['region_insights'].get('worst_region')
                
                if best_region:
                    options.append({
                        'action': 'regional_expansion',
                        'description': f'Expandir presencia en región de alto rendimiento: {best_region}',
                        'region': best_region,
                        'expansion_type': 'intensiva',
                        'timeframe': 'medium'
                    })
                
                if worst_region:
                    options.append({
                        'action': 'regional_focus',
                        'description': f'Campaña focalizada para región de bajo rendimiento: {worst_region}',
                        'region': worst_region,
                        'campaign_type': 'awareness',
                        'timeframe': 'short'
                    })
        
        # Opciones genéricas
        options.append({
            'action': 'digital_campaign',
            'description': 'Lanzar campaña digital en redes sociales',
            'channels': ['Facebook', 'Instagram', 'Google'],
            'timeframe': 'short'
        })
        options.append({
            'action': 'loyalty_program',
            'description': 'Implementar programa de fidelización',
            'benefits': ['descuentos', 'puntos', 'regalos'],
            'timeframe': 'medium'
        })
        options.append({
            'action': 'email_marketing',
            'description': 'Optimizar campaña de email marketing',
            'segments': ['clientes activos', 'inactivos', 'potenciales'],
            'timeframe': 'short'
        })
        
        return options
    
    def _register_recommended_action(self, dataset_id, action_type, result):
        """Registra la acción recomendada en la base de datos."""
        try:
            dataset = Dataset.objects.get(id=dataset_id)
            
            # Preparar datos de la acción
            recommended = result['recommended_option']
            confidence = next((opt['confidence'] for opt in result['all_options'] 
                              if opt['option'] == recommended), 0.7)
            
            # Crear registro de acción
            AgentAction.objects.create(
                action_type=action_type,
                status='suggested',
                description=recommended.get('description', str(recommended)),
                action_data=recommended,
                expected_impact=result.get('reasoning', {}).get('narrative', ''),
                confidence=confidence,
                dataset=dataset
            )
        except Exception as e:
            # Registrar error pero no interrumpir el flujo
            print(f"Error registrando acción recomendada: {str(e)}")
    
    def learn_from_outcomes(self, action_id, success_score, metrics_after, feedback=None):
        """
        Aprende de los resultados de acciones pasadas para mejorar decisiones futuras.
        
        Args:
            action_id: ID de la acción previamente recomendada
            success_score: Puntaje de éxito (-1 a 1)
            metrics_after: Métricas después de implementar la acción
            feedback: Feedback cualitativo opcional
        
        Returns:
            Resultado del proceso de aprendizaje
        """
        try:
            # 1. Obtener la acción de la base de datos
            action = AgentAction.objects.get(id=action_id)
            
            # 2. Crear registro de aprendizaje
            learning_log = AgentLearningLog.objects.create(
                action=action,
                success_score=success_score,
                metrics_before=action.action_data.get('metrics_before', {}),
                metrics_after=metrics_after,
                insights=feedback or "Retroalimentación automática basada en métricas",
                feedback_source='user' if feedback else 'auto'
            )
            
            # 3. Actualizar factores de decisión basados en el aprendizaje
            self._update_decision_model(action, success_score, metrics_after)
            
            return {
                "success": True,
                "learning_id": learning_log.id,
                "summary": "Aprendizaje registrado correctamente y modelo actualizado"
            }
            
        except AgentAction.DoesNotExist:
            return {
                "success": False,
                "error": f"Acción con ID {action_id} no encontrada"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error en proceso de aprendizaje: {str(e)}"
            }
    
    def _update_decision_model(self, action, success_score, metrics_after):
        """Actualiza el modelo interno de decisión basado en resultados."""
        # En implementación real, esto podría:
        # 1. Ajustar pesos de factores
        # 2. Añadir reglas nuevas
        # 3. Actualizar umbrales
        # 4. Entrenar modelos de ML con nuevos datos
        
        # Simulación simple de aprendizaje
        action_type = action.action_type
        action_data = action.action_data
        
        # Guardar datos de aprendizaje para uso futuro
        self.learning_data.append({
            'action_type': action_type,
            'action_data': action_data,
            'success_score': success_score,
            'metrics_after': metrics_after
        })
        
        # El sistema real implementaría algoritmos de aprendizaje por refuerzo
        # o ajuste bayesiano de parámetros basado en estos datos