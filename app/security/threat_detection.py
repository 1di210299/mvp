import re
import logging
from typing import Dict, Any, List, Set

from app.services.openai_service import detect_threats

# Configurar logging
logger = logging.getLogger(__name__)

# Lista de palabras clave sospechosas (argot peruano para extorsiones)
SUSPICIOUS_KEYWORDS = {
    # Términos generales de extorsión
    "extorsión", "amenaza", "matar", "secuestrar", "dañar", "familia", "atentado",
    "bomba", "explosivo", "arma", "pistola", "revólver", "cuchillo",
    
    # Términos de extorsión comunes en Perú
    "cupo", "protección", "colaboración", "vacuna", "aporte", "encargo",
    "tío", "primo", "hermano", "familia", "apoyo", "favor", "préstamo",
    
    # Referencias a organizaciones criminales
    "clan", "banda", "mafia", "organización", "grupo", "barrio",
    
    # Términos relativos a pagos forzados
    "pagar", "depositar", "transferir", "yape", "plin", "billetera", "cuenta",
    "transferencia", "banco", "efectivo", "dinero", "plata", "lucas", "luca",
    
    # Términos de presión y urgencia
    "urgente", "inmediato", "ahora", "ya", "rápido", "hoy", "mañana",
    
    # Amenazas específicas
    "atentado", "disparar", "quemar", "incendiar", "romper", "destruir",
    "negocio", "tienda", "local", "casa", "carro", "auto", "familia",
    
    # Jerga peruana relacionada con extorsión
    "tombo", "rati", "rata", "gil", "causa", "brother", "hermano", "choro",
    "marcas", "cogotear", "apretar", "cagar", "joder", "fregar"
}

def keyword_match(text: str) -> Dict[str, Any]:
    """
    Analiza un texto en busca de palabras clave sospechosas.
    
    Args:
        text: Texto a analizar
        
    Returns:
        dict: Resultado del análisis con score y palabras encontradas
    """
    # Normalizar texto: minúsculas y eliminar tildes
    text_normalized = text.lower()
    
    # Buscar coincidencias
    found_keywords: Set[str] = set()
    
    for keyword in SUSPICIOUS_KEYWORDS:
        # Buscar la palabra completa con fronteras de palabra
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_normalized):
            found_keywords.add(keyword)
    
    # Calcular score basado en la cantidad de palabras encontradas
    # y su relevancia (por ahora todas tienen el mismo peso)
    count = len(found_keywords)
    max_score = min(1.0, count / 5)  # 5+ palabras = score 1.0
    
    return {
        "score": max_score,
        "is_threat": max_score >= 0.4,  # Umbral arbitrario
        "keywords": list(found_keywords),
        "method": "keyword_match"
    }

def analyze_message(text: str) -> Dict[str, Any]:
    """
    Analiza un mensaje en busca de amenazas o contenido sospechoso.
    
    Combina análisis simple de palabras clave con análisis de IA
    para mayor precisión.
    
    Args:
        text: Texto a analizar
        
    Returns:
        dict: Resultado del análisis
    """
    # Resultado por defecto (en caso de error)
    default_result = {
        "score": 0.0,
        "is_threat": False,
        "threat_type": "ninguna",
        "keywords": [],
        "explanation": "Análisis no disponible"
    }
    
    try:
        # 1. Primero análisis rápido con palabras clave
        keyword_result = keyword_match(text)
        
        # Si el texto es muy corto o no tiene palabras clave, evitamos llamar a la API
        if len(text.strip()) < 10 or not keyword_result["keywords"]:
            return {
                "score": 0.0,
                "is_threat": False,
                "threat_type": "ninguna",
                "keywords": [],
                "explanation": "Mensaje demasiado corto o sin contenido sospechoso",
                "method": "keyword_only"
            }
        
        # 2. Si hay palabras clave sospechosas, usar IA para análisis profundo
        if keyword_result["score"] > 0.2:
            try:
                # Obtener análisis de OpenAI
                ai_result = detect_threats(text)
                
                # Combinar ambos resultados (dando más peso al análisis de IA)
                combined_score = (ai_result.get("score", 0) * 0.7) + (keyword_result["score"] * 0.3)
                
                # Preparar resultado combinado
                result = {
                    "score": min(1.0, combined_score),  # Asegurar max 1.0
                    "is_threat": ai_result.get("is_threat", False) or (combined_score >= 0.5),
                    "threat_type": ai_result.get("threat_type", "posible"),
                    "keywords": list(set(ai_result.get("keywords", []) + keyword_result["keywords"])),
                    "explanation": ai_result.get("explanation", "Análisis automático detectó contenido sospechoso"),
                    "method": "combined"
                }
                
                logger.info(f"Análisis de amenaza completado: Score {result['score']:.2f}")
                return result
                
            except Exception as e:
                logger.error(f"Error en análisis IA: {str(e)}")
                # En caso de error con IA, usar solo análisis de palabras clave
                return {
                    "score": keyword_result["score"],
                    "is_threat": keyword_result["is_threat"],
                    "threat_type": "posible" if keyword_result["is_threat"] else "ninguna",
                    "keywords": keyword_result["keywords"],
                    "explanation": "Análisis simple detectó palabras clave sospechosas",
                    "method": "keyword_fallback"
                }
        
        # Si no hay suficientes palabras clave, devolver resultado simple
        return {
            "score": keyword_result["score"],
            "is_threat": keyword_result["is_threat"],
            "threat_type": "posible" if keyword_result["is_threat"] else "ninguna",
            "keywords": keyword_result["keywords"],
            "explanation": "Mensaje de bajo riesgo",
            "method": "keyword_only"
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de amenazas: {str(e)}")
        return default_result