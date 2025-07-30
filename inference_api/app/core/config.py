import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuración de la aplicación."""
    
    SUPABASE_URL: str = os.getenv('SUPABASE_URL')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY')
    
    RAY_HOST: str = '0.0.0.0'
    RAY_PORT: int = 8001
    
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

settings = Settings()