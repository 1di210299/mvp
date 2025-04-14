import os
from dotenv import load_dotenv

# Cargar variables de entorno si no se han cargado aún
load_dotenv()

# Configuraciones de Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+14155238886")  # Número por defecto del sandbox

# URL de Webhook - útil para verificar si coincide con lo configurado en Twilio
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://58ee-2800-200-efb8-10f-f501-fef7-81aa-d05.ngrok-free.app/api/webhooks/twilio")

# Verificación de configuración
def is_twilio_configured():
    """Verifica si las credenciales de Twilio están configuradas"""
    return all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER])
