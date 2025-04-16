import os
import logging.config
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de entorno
APP_ENV = os.getenv("APP_ENV", "development")

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Configuración del servidor
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
API_PREFIX = os.getenv("API_PREFIX", "/api")
PROJECT_NAME = os.getenv("PROJECT_NAME", "Ventas WhatsApp")
VERSION = os.getenv("VERSION", "0.1.0")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Credenciales de Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", TWILIO_WHATSAPP_NUMBER)  # Añadido para compatibilidad

# Configuración de Seguridad
MIN_SUSPICIOUS_SCORE = float(os.getenv("MIN_SUSPICIOUS_SCORE", "0.7"))  # Score mínimo para considerar un mensaje sospechoso
THREAT_SCORE_THRESHOLD = float(os.getenv("THREAT_SCORE_THRESHOLD", "0.85"))  # Aumentado para reducir falsos positivos
ENABLE_AUTO_BLOCKING = os.getenv("ENABLE_AUTO_BLOCKING", "False").lower() in ("true", "1", "t")  # Desactivado por defecto

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Configuración para seguridad
BLACKLIST_PATH = os.getenv("BLACKLIST_PATH", "static/data/blacklist.csv")
SUSPICIOUS_WORDS_PATH = os.getenv("SUSPICIOUS_WORDS_PATH", "static/data/suspicious_words.txt")
THREAT_SCORE_THRESHOLD = float(os.getenv("THREAT_SCORE_THRESHOLD", "0.7"))

# Configuración de notificaciones
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Configuración de pasarelas de pago
CULQI_PUBLIC_KEY = os.getenv("CULQI_PUBLIC_KEY", "")
CULQI_PRIVATE_KEY = os.getenv("CULQI_PRIVATE_KEY", "")
NIUBIZ_MERCHANT_ID = os.getenv("NIUBIZ_MERCHANT_ID", "")
NIUBIZ_ACCESS_KEY = os.getenv("NIUBIZ_ACCESS_KEY", "")
IZIPAY_API_KEY = os.getenv("IZIPAY_API_KEY", "")

# Función para verificar si todas las variables de entorno necesarias están configuradas
def is_env_ready():
    """
    Verifica si todas las variables de entorno críticas están configuradas.
    
    Returns:
        bool: True si todas las variables críticas están configuradas, False en caso contrario
    """
    critical_vars = [
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
        TWILIO_WHATSAPP_NUMBER,
        OPENAI_API_KEY,
        ADMIN_EMAIL
    ]
    
    return all(var for var in critical_vars)

# Rutas de directorios
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = STATIC_DIR / "data"
TEMPLATES_DIR = STATIC_DIR / "templates"

# Configuración de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": LOG_LEVEL,
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": LOG_LEVEL,
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "app.log"),
            "mode": "a",
        },
        "debug_file": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "webhook_debug.log"),
            "mode": "a",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default", "file"],
            "level": LOG_LEVEL,
            "propagate": True
        },
        "app": {
            "handlers": ["default", "file"],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "webhook_debug": {
            "handlers": ["default", "debug_file"],
            "level": "DEBUG",
            "propagate": False
        },
    }
}

# Configuración de la aplicación
class Settings:
    PROJECT_NAME = PROJECT_NAME
    VERSION = VERSION
    API_PREFIX = API_PREFIX
    DEBUG = DEBUG
    HOST = HOST
    PORT = PORT
    DATABASE_URL = DATABASE_URL
    TWILIO_ACCOUNT_SID = TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN = TWILIO_AUTH_TOKEN
    TWILIO_WHATSAPP_NUMBER = TWILIO_WHATSAPP_NUMBER
    TWILIO_PHONE_NUMBER = TWILIO_PHONE_NUMBER
    OPENAI_API_KEY = OPENAI_API_KEY
    OPENAI_MODEL = OPENAI_MODEL
    MIN_SUSPICIOUS_SCORE = MIN_SUSPICIOUS_SCORE
    THREAT_SCORE_THRESHOLD = THREAT_SCORE_THRESHOLD
    ENABLE_AUTO_BLOCKING = ENABLE_AUTO_BLOCKING
    
    # Método para actualizar la configuración en tiempo de ejecución
    @classmethod
    def update_config(cls, **kwargs):
        """Actualiza dinámicamente la configuración de la aplicación"""
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
                # Actualizar también la variable global correspondiente si existe
                if key in globals():
                    globals()[key] = value

# Instancia de configuración para usar en la aplicación
settings = Settings()

# Configurar logging
logging.config.dictConfig(LOGGING_CONFIG)

# Whitelist de números para evitar que sean bloqueados
WHITELISTED_NUMBERS = set(phone.strip() for phone in os.getenv("WHITELISTED_NUMBERS", "").split(",") if phone.strip())
BLOCKED_NUMBERS = set()  # Lista dinámica de números bloqueados

def is_whitelisted(phone_number):
    """Verifica si un número está en la whitelist"""
    if not phone_number:
        return False
    
    # Normalizar el número (eliminar espacios, '+', etc.)
    normalized = ''.join(c for c in phone_number if c.isdigit())
    
    # Comprobar si el número normalizado está en la whitelist
    for white in WHITELISTED_NUMBERS:
        white_normalized = ''.join(c for c in white if c.isdigit())
        if normalized.endswith(white_normalized) or white_normalized.endswith(normalized):
            return True
    
    return False

def add_to_whitelist(phone_number):
    """Añade un número a la whitelist"""
    global WHITELISTED_NUMBERS
    if not phone_number:
        return False
    
    WHITELISTED_NUMBERS.add(phone_number)
    
    # Si estaba en la lista de bloqueados, lo quitamos
    if phone_number in BLOCKED_NUMBERS:
        BLOCKED_NUMBERS.remove(phone_number)
    
    return True

def block_number(phone_number, reason="Sistema de detección de amenazas"):
    """Añade un número a la lista de bloqueados"""
    global BLOCKED_NUMBERS
    if not phone_number or is_whitelisted(phone_number):
        return False
    
    BLOCKED_NUMBERS.add(phone_number)
    return True

def is_blocked(phone_number):
    """Verifica si un número está bloqueado"""
    if not phone_number:
        return False
    
    # Si está en la whitelist, nunca está bloqueado
    if is_whitelisted(phone_number):
        return False
    
    return phone_number in BLOCKED_NUMBERS

def get_blocked_numbers():
    """Retorna la lista de números bloqueados"""
    return list(BLOCKED_NUMBERS)