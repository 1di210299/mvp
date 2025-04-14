# Import settings from your main config module
from .settings import (
    APP_ENV,
    DEBUG,
    is_env_ready,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    ADMIN_EMAIL,
    ADMIN_PHONE,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    WEBHOOK_URL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    # Security settings
    SUSPICIOUS_WORDS_PATH,
    MIN_SUSPICIOUS_SCORE,
    THREAT_SCORE_THRESHOLD
)

# This makes the config directory a proper Python package
# Now you can access these variables from app.config directly
