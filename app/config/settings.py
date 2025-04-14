import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application environment settings
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = APP_ENV == "development"

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+14155238886")  # Default Sandbox number

# Admin notification settings
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "gjuandiego213@gmail.com")
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "+51955743403")  # Added ADMIN_PHONE with a default value

# Telegram notification settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")  # Add your Telegram bot token here
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")  # Add your Telegram chat ID here

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Security settings
SUSPICIOUS_WORDS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "suspicious_words.json")
MIN_SUSPICIOUS_SCORE = float(os.getenv("MIN_SUSPICIOUS_SCORE", "0.3"))  # Minimum score to flag as suspicious
THREAT_SCORE_THRESHOLD = float(os.getenv("THREAT_SCORE_THRESHOLD", "0.7"))  # Threshold for high-risk threats

# Current ngrok URL - update this when you restart ngrok
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://85f6-2800-200-efb8-10f-f501-fef7-81aa-d05.ngrok-free.app/api/webhooks/twilio")

def is_env_ready():
    """Check if critical environment variables are set"""
    required_vars = [
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
        TWILIO_PHONE_NUMBER
    ]
    return all(required_vars)
