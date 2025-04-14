# api/nlp_processor.py
import requests
import json
import re
import os
from typing import Dict, List, Any, Optional

class DeepseekNLPProcessor:
    """
    NLP processor using Deepseek API with enhanced capabilities for Peruvian Spanish
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Deepseek NLP processor"""
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("Deepseek API key is required. Set it as DEEPSEEK_API_KEY environment variable or pass directly.")
        
        self.api_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Peruvian slang and expressions dictionary
        self.peruvian_expressions = {
            "chamba": "trabajo",
            "plata": "dinero",
            "pata": "amigo",
            "chévere": "bueno",
            "manya": "entiende",
            "bacán": "excelente",
            "mosca": "atento",
            "paltearse": "avergonzarse",
            "pituco": "adinerado",
            "huacho": "hijo",
            "chancar": "estudiar mucho",
            "jato": "casa",
            "tela": "dinero",
            "causa": "amigo",
            "michi": "gato",
            "luca": "sol peruano",
            "yapa": "adicional gratis"
        }
    
    def normalize_peruvian_text(self, text: str) -> str:
        """Normalize Peruvian slang and expressions to standard Spanish"""
        for slang, standard in self.peruvian_expressions.items():
            text = re.sub(r'\b' + slang + r'\b', standard, text, flags=re.IGNORECASE)
        return text
    
    def _call_deepseek_api(self, endpoint: str, payload: Dict) -> Dict:
        """Make a call to the Deepseek API"""
        try:
            response = requests.post(
                f"{self.api_url}/{endpoint}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Deepseek API: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
    
    def analyze_sentiment(self, text: str, include_peruvian_context: bool = True) -> Dict:
        """Analyze sentiment in Spanish text with Peruvian context awareness"""
        if include_peruvian_context:
            text = self.normalize_peruvian_text(text)
        
        prompt = f"""
        Analiza el sentimiento del siguiente texto en español. 
        Clasifícalo como positivo, negativo o neutral.
        Proporciona una puntuación de confianza entre 0 y 1.
        Texto: "{text}"
        
        Responde en formato JSON con las siguientes claves:
        - sentiment: "positive", "negative", o "neutral"
        - score: puntuación de confianza (0-1)
        - key_phrases: lista de frases clave
        - explanation: explicación breve del análisis
        """
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        result = self._call_deepseek_api("chat/completions", payload)
        
        try:
            analysis = json.loads(result["choices"][0]["message"]["content"])
            return {
                "original_text": text,
                "sentiment": analysis.get("sentiment", "neutral"),
                "score": analysis.get("score", 0.5),
                "key_phrases": analysis.get("key_phrases", []),
                "explanation": analysis.get("explanation", ""),
                "analysis": {
                    "is_peruvian_context": include_peruvian_context,
                    "processed_text": text if not include_peruvian_context else self.normalize_peruvian_text(text)
                }
            }
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing Deepseek API response: {str(e)}")
            return {
                "original_text": text,
                "sentiment": "neutral",
                "score": 0.5,
                "error": f"Failed to parse API response: {str(e)}"
            }
    
    def extract_key_phrases(self, text: str, include_peruvian_context: bool = True) -> List[str]:
        """Extract key phrases from text"""
        if include_peruvian_context:
            text = self.normalize_peruvian_text(text)
        
        prompt = f"""
        Extrae las frases clave y entidades importantes del siguiente texto en español.
        Texto: "{text}"
        
        Responde solo con una lista de frases clave en formato JSON.
        """
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        result = self._call_deepseek_api("chat/completions", payload)
        
        try:
            key_phrases = json.loads(result["choices"][0]["message"]["content"])
            return key_phrases.get("key_phrases", [])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing key phrases from API response: {str(e)}")
            return []
    
    def classify_customer_feedback(self, text: str) -> Dict:
        """Classify customer feedback into categories with Peruvian business context"""
        normalized_text = self.normalize_peruvian_text(text)
        
        prompt = f"""
        Clasifica el siguiente comentario de cliente en español peruano en categorías de negocio.
        Texto: "{normalized_text}"
        
        Categorías posibles: Producto, Servicio, Precio, Entrega, Calidad, Atención al Cliente, App/Sitio Web, Otros
        
        Responde en formato JSON con las siguientes claves:
        - main_category: categoría principal
        - sub_categories: lista de subcategorías (máximo 2)
        - confidence: nivel de confianza (0-1)
        - sentiment: "positive", "negative", o "neutral"
        - business_impact: impacto para el negocio ("high", "medium", "low")
        - recommendation: acción recomendada
        """
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        result = self._call_deepseek_api("chat/completions", payload)
        
        try:
            classification = json.loads(result["choices"][0]["message"]["content"])
            return {
                "original_text": text,
                "main_category": classification.get("main_category", "Otros"),
                "sub_categories": classification.get("sub_categories", []),
                "confidence": classification.get("confidence", 0.5),
                "sentiment": classification.get("sentiment", "neutral"),
                "business_impact": classification.get("business_impact", "low"),
                "recommendation": classification.get("recommendation", ""),
                "peruvian_context": True
            }
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing classification from API response: {str(e)}")
            return {
                "original_text": text,
                "main_category": "Otros",
                "sub_categories": [],
                "confidence": 0.0,
                "error": f"Failed to parse API response: {str(e)}"
            }
    
    def analyze_business_text(self, text: str, business_type: str = "retail") -> Dict:
        """
        Analyze business text with Peruvian context
        
        business_type can be: retail, restaurant, finance, agriculture, manufacturing, services
        """
        normalized_text = self.normalize_peruvian_text(text)
        
        prompt = f"""
        Analiza el siguiente texto de negocio en español peruano para un negocio de {business_type}.
        Texto: "{normalized_text}"
        
        Proporciona un análisis completo en formato JSON con las siguientes claves:
        - key_findings: conclusiones principales (lista)
        - business_opportunities: oportunidades de negocio identificadas (lista)
        - risks: riesgos identificados (lista)
        - customer_sentiment: sentimiento general del cliente
        - action_items: acciones recomendadas (lista)
        - peruvian_market_context: observaciones específicas del mercado peruano
        """
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        result = self._call_deepseek_api("chat/completions", payload)
        
        try:
            analysis = json.loads(result["choices"][0]["message"]["content"])
            return analysis
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing business analysis from API response: {str(e)}")
            return {
                "error": f"Failed to parse API response: {str(e)}",
                "key_findings": ["Error en el análisis"]
            }
    
    def financial_term_explanation(self, text: str) -> Dict:
        """Explain financial terms in Peruvian context"""
        prompt = f"""
        Explica los siguientes términos financieros en el contexto de negocios peruanos.
        Términos: "{text}"
        
        Proporciona explicaciones claras y sencillas para empresarios de MYPES peruanas.
        Responde en formato JSON con un diccionario donde las claves son los términos
        y los valores son las explicaciones.
        """
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        result = self._call_deepseek_api("chat/completions", payload)
        
        try:
            explanations = json.loads(result["choices"][0]["message"]["content"])
            return explanations
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing financial term explanations: {str(e)}")
            return {
                "error": f"Failed to parse API response: {str(e)}"
            }