import os
from pathlib import Path
from pydantic import AnyUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import logging

# Configura logging básico para la carga de configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carga variables de entorno desde .env en el directorio raíz
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    """
    Configuración principal de la aplicación usando pydantic.BaseSettings.
    Valida y carga automáticamente las variables de entorno.
    """
    
    # Configuración básica
    APP_NAME: str = "Portfolio Optimization API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # 'development', 'staging', 'production'
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    WORKERS: int = os.cpu_count() or 1
    RELOAD: bool = False
    
    # Ray Config
    RAY_NUM_CPUS: int = os.cpu_count() or 4
    RAY_NUM_GPUS: int = 0
    RAY_OBJECT_STORE_MEMORY: int = 200 * 1024 * 1024  # 200MB
    
    # Supabase
    SUPABASE_URL: AnyUrl
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str = "datasets"
    
    # Yahoo Finance
    YAHOO_TIMEOUT: int = 30
    YAHOO_MAX_RETRIES: int = 3
    
    # CORS
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rutas
    DATA_DIR: Path = Path(__file__).parents[2] / "data"
    MODEL_CACHE_DIR: Path = Path(__file__).parents[2] / "model_cache"
    
    # Validadores (actualizados para Pydantic v2)
    @field_validator('ENVIRONMENT')
    def validate_environment(cls, v):
        if v not in {'development', 'staging', 'production'}:
            raise ValueError("Environment must be development, staging or production")
        return v
    
    @field_validator('DATA_DIR', 'MODEL_CACHE_DIR')
    def create_dirs_if_not_exist(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator('CORS_ALLOW_ORIGINS', mode='before')
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = {
        "env_file": env_path,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "secrets_dir": "/run/secrets"  # Para Docker Secrets
    }

# Instancia singleton de configuración
try:
    settings = Settings()
    logger.info(f"Configuración cargada para entorno: {settings.ENVIRONMENT}")
except Exception as e:
    logger.error(f"Error cargando configuración: {e}")
    raise