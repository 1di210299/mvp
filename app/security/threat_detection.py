import re
import json
import logging
from typing import Dict, Any, List, Set, Tuple
from app.services.openai_service import detect_threats
from app.config import SUSPICIOUS_WORDS_PATH, MIN_SUSPICIOUS_SCORE, THREAT_SCORE_THRESHOLD, settings
from app.security.access_control import is_whitelisted

# Configurar logging
logger = logging.getLogger("app.security.threat_detection")

# Cargar palabras sospechosas desde archivo
def load_suspicious_words() -> Set[str]:
    """
    Carga la lista de palabras sospechosas desde un archivo.
    
    Returns:
        Set[str]: Conjunto de palabras sospechosas
    """
    try:
        with open(SUSPICIOUS_WORDS_PATH, 'r', encoding='utf-8') as file:
            return {word.strip().lower() for word in file if word.strip()}
    except Exception as e:
        logger.error(f"Error cargando palabras sospechosas: {str(e)}")
        # Lista básica de palabras sospechosas en caso de error
        return {
            "amenaza", "matar", "extorsión", "plomo", "disparar", "muerte", "dinero",
            "cupo", "protección", "bomba", "explotar", "familia", "cuidado", "peligro",
            "seguimiento", "vigilando", "sabemos", "conocemos", "ubicación", "dirección",
            "hijo", "hija", "esposa", "padres", "colaboración", "pagar", "consecuencias",
            "enterrar", "mafia", "banda", "clan", "grupo", "norte", "pulpo", "venganza",
            "quemar", "incendiar", "cerrar", "negocio", "eliminar", "advertencia", "última",
            "plazo", "tiempo", "inmediato", "urgente", "rápido", "atento", "visita",
            "marcar", "apuntar", "lamentar", "sufrir", "decidir", "responsable", "vives",
            "donde", "casa", "dónde", "trabajo", "encontrar", "visitar"
        }

# Singleton para mantener las palabras cargadas
_suspicious_words = None

def get_suspicious_words() -> Set[str]:
    """
    Obtiene el conjunto de palabras sospechosas, cargándolo si es necesario.
    
    Returns:
        Set[str]: Conjunto de palabras sospechosas
    """
    global _suspicious_words
    if _suspicious_words is None:
        _suspicious_words = load_suspicious_words()
    return _suspicious_words

def keyword_match_score(text: str) -> Tuple[float, List[str]]:
    """
    Calcula un score de sospecha basado en palabras clave.
    
    Args:
        text: Texto a analizar
        
    Returns:
        tuple: (score, palabras_encontradas)
    """
    suspicious_words = get_suspicious_words()
    
    # Normalizar el texto (minúsculas, sin acentos)
    normalized_text = text.lower()
    
    # Buscar palabras sospechosas
    found_words = [word for word in suspicious_words if word in normalized_text]
    
    # Calcular score básico: proporción de palabras encontradas
    if not found_words:
        return 0.0, []
    
    # Score ponderado por la cantidad y densidad de palabras encontradas
    words_in_text = len(re.findall(r'\b\w+\b', normalized_text))
    if words_in_text == 0:
        return 0.0, []
    
    # Calcular puntuación basada en:
    # 1. Número de palabras sospechosas diferentes encontradas
    # 2. Densidad de palabras sospechosas en el texto
    word_count_factor = min(len(found_words) / 10, 1.0)  # Máximo 10 palabras distintas
    density_factor = min(len(found_words) / words_in_text, 1.0)
    
    # Combinar factores para obtener score final
    score = 0.3 * word_count_factor + 0.7 * density_factor
    
    return min(score, 1.0), found_words

def pattern_based_detection(text: str) -> Dict[str, Any]:
    """
    Detecta patrones comunes de amenazas o extorsiones mediante regex.
    
    Args:
        text: Texto a analizar
        
    Returns:
        dict: Resultados del análisis
    """
    patterns = {
        "dinero_y_amenaza": r'(?i)((pagar|dinero|soles|dólares|lucas|billete|transferir|depositar).{1,30}(o|caso contrario|sino|de lo contrario|o si no))',
        "plazo_tiempo": r'(?i)((tiempo|plazo|horas|minutos|días|fecha).{1,20}(terminado|acabado|cumplido|vencido))',
        "datos_personales": r'(?i)(sabemos|conocemos).{1,30}(donde|dirección|casa|vives|trabajo|familia|hijo|hija|esposa|esposo|padres)',
        "violencia_explicita": r'(?i)(matar|disparar|plomo|muerte|sangre|romper|quebrar|golpear|eliminar|desaparecer)',
        "extorsion_directa": r'(?i)(colabora|cupo|cuota|protección|seguridad).{1,30}(negocio|tienda|local|familia)',
    }
    
    findings = {}
    matches_found = False
    
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            matches_found = True
            findings[pattern_name] = matches
    
    # Calcular score basado en los patrones encontrados
    pattern_score = min(len(findings) / len(patterns), 1.0) if matches_found else 0.0
    
    return {
        "patterns_found": findings,
        "score": pattern_score,
        "matches_found": matches_found
    }

def analyze_message(message: str, phone_number: str = None) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Analyzes a message to detect possible threats or extortion attempts
    
    Args:
        message: The message to analyze
        phone_number: Sender's phone number (optional)
    
    Returns:
        Tuple with:
        - is_threat: If the message is a threat
        - score: Threat score (0-1)
        - details: Additional details about the analysis
    """
    # Check if the number is whitelisted
    if phone_number and is_whitelisted(phone_number):
        logger.info(f"Number {phone_number} is whitelisted, skipping threat analysis")
        return False, 0.0, {"whitelisted": True, "analysis": None}
    
    # If the message is very short, it's unlikely to be a threat
    if len(message) < 5:
        return False, 0.0, {"reason": "message too short", "analysis": None}
    
    try:
        # Try to analyze with OpenAI
        analysis = detect_threats(message)
        score = analysis.get("threat_score", 0.0)
        
        # Determine if it's a threat based on the configured threshold
        is_threat = score >= THREAT_SCORE_THRESHOLD
        
        # Check if auto-blocking is enabled
        enable_auto_blocking = getattr(settings, "ENABLE_AUTO_BLOCKING", True)
        
        if is_threat and not enable_auto_blocking:
            logger.warning(f"Message detected as threat (score: {score}) but auto-blocking is disabled")
            is_threat = False  # Don't block if auto-blocking is disabled
        
        return is_threat, score, {"analysis": analysis}
        
    except Exception as e:
        logger.error(f"Error analyzing message: {str(e)}")
        # In case of error, don't block the message
        return False, 0.0, {"error": str(e), "analysis": None}