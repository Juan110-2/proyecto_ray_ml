import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuración de la aplicación."""
    
    SUPABASE_URL: str = os.getenv('SUPABASE_URL')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY')

    HOST: str = os.getenv('HOST', '127.0.0.1')  # valor por defecto por si no existe
    PORT: int = int(os.getenv('PORT', 8000))    # asegúrate de castear a int

    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

settings = Settings()
