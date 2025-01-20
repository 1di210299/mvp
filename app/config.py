from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "InsightFlow Perú"
    DATA_FILE_PATH: str = "data/your_data.csv"
    
    # Configuraciones adicionales según necesites
    ANALYSIS_WINDOW_DAYS: int = 30
    MIN_TRANSACTIONS_FOR_ANALYSIS: int = 5

settings = Settings()