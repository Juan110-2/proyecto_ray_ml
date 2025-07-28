import os
import logging
import tempfile
import pandas as pd
from pathlib import Path
from typing import Any, Optional, Dict, List, Union, Tuple
from datetime import datetime, timedelta
from functools import wraps
from time import perf_counter
import numpy as np
from supabase import Client
from dotenv import load_dotenv
import yfinance as yf
import ray

# Configuración básica de logging
logger = logging.getLogger(__name__)

# Carga variables de entorno
load_dotenv()

# --------------------------
# Decoradores de utilidad
# --------------------------

def timer(func):
    """Decorador para medir tiempo de ejecución de funciones"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        result = func(*args, **kwargs)
        end_time = perf_counter()
        elapsed = end_time - start_time
        logger.debug(f"{func.__name__} executed in {elapsed:.4f} seconds")
        return result
    return wrapper

def retry(max_retries: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    """Decorador para reintentar operaciones fallidas"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise
                    logger.warning(f"Attempt {attempt} failed for {func.__name__}. Retrying...")
                    time.sleep(delay * attempt)
        return wrapper
    return decorator

# --------------------------
# Manejo de archivos y datos
# --------------------------

def save_to_tempfile(
    data: Union[pd.DataFrame, Dict[str, Any]], 
    prefix: str = "portfolio_",
    suffix: str = ".parquet"
) -> Path:
    """
    Guarda datos en un archivo temporal seguro.
    
    Args:
        data: DataFrame o diccionario a guardar
        prefix: Prefijo del nombre del archivo
        suffix: Sufijo/extensión del archivo
    
    Returns:
        Path al archivo temporal creado
    """
    try:
        temp_file = tempfile.NamedTemporaryFile(
            prefix=prefix,
            suffix=suffix,
            delete=False
        )
        file_path = Path(temp_file.name)
        
        if isinstance(data, pd.DataFrame):
            data.to_parquet(file_path)
        else:
            pd.DataFrame(data).to_parquet(file_path)
            
        logger.info(f"Data saved to temporary file: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving temp file: {str(e)}")
        raise

def load_from_supabase(
    supabase: Client,
    bucket: str,
    file_path: str,
    local_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Descarga un archivo desde Supabase Storage.
    
    Args:
        supabase: Cliente de Supabase
        bucket: Nombre del bucket
        file_path: Ruta al archivo en el bucket
        local_path: Ruta local opcional para guardar
        
    Returns:
        DataFrame con los datos cargados
    """
    try:
        logger.info(f"Downloading {file_path} from {bucket}")
        response = supabase.storage.from_(bucket).download(file_path)
        
        if local_path:
            with open(local_path, 'wb') as f:
                f.write(response)
            logger.info(f"File saved to {local_path}")
            return pd.read_parquet(local_path)
        
        return pd.read_parquet(io.BytesIO(response))
    except Exception as e:
        logger.error(f"Error downloading from Supabase: {str(e)}")
        raise

# --------------------------
# Manejo de fechas
# --------------------------

def validate_date_range(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    max_days: int = 365 * 3  # 3 años por defecto
) -> Tuple[datetime, datetime]:
    """
    Valida y parsea un rango de fechas.
    
    Args:
        start_date: Fecha de inicio (str o datetime)
        end_date: Fecha de fin (str o datetime)
        max_days: Máximo número de días permitido
    
    Returns:
        Tuple con (start_date, end_date) como datetime objects
    
    Raises:
        ValueError: Si las fechas son inválidas
    """
    try:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date).date()
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date).date()
            
        if start_date >= end_date:
            raise ValueError("End date must be after start date")
            
        delta = end_date - start_date
        if delta.days > max_days:
            raise ValueError(f"Date range exceeds maximum of {max_days} days")
            
        return start_date, end_date
    except Exception as e:
        logger.error(f"Date validation failed: {str(e)}")
        raise

# --------------------------
# Funciones para Yahoo Finance
# --------------------------

@retry(max_retries=3, delay=1.0)
def safe_yfinance_download(
    tickers: List[str],
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    **kwargs
) -> pd.DataFrame:
    """
    Descarga segura de datos de Yahoo Finance con reintentos.
    
    Args:
        tickers: Lista de símbolos
        start_date: Fecha de inicio
        end_date: Fecha de fin
        **kwargs: Argumentos adicionales para yfinance
        
    Returns:
        DataFrame con los datos descargados
    """
    try:
        logger.info(f"Downloading {len(tickers)} tickers from Yahoo Finance")
        data = yf.download(
            tickers=tickers,
            start=start_date,
            end=end_date,
            **kwargs
        )
        if data.empty:
            raise ValueError("No data returned from Yahoo Finance")
        return data
    except Exception as e:
        logger.error(f"Yahoo Finance download failed: {str(e)}")
        raise

# --------------------------
# Utilidades para Ray
# --------------------------

def initialize_ray(
    num_cpus: Optional[int] = None,
    num_gpus: Optional[int] = None,
    object_store_memory: Optional[int] = None,
    **kwargs
) -> None:
    """
    Inicializa Ray con configuración segura.
    
    Args:
        num_cpus: Número de CPUs a usar
        num_gpus: Número de GPUs a usar
        object_store_memory: Memoria para object store (en bytes)
        **kwargs: Argumentos adicionales para ray.init
    """
    try:
        if not ray.is_initialized():
            ray.init(
                num_cpus=num_cpus or os.cpu_count(),
                num_gpus=num_gpus or 0,
                object_store_memory=object_store_memory or 200 * 1024 * 1024,  # 200MB
                **kwargs
            )
            logger.info("Ray initialized successfully")
    except Exception as e:
        logger.error(f"Ray initialization failed: {str(e)}")
        raise

# --------------------------
# Funciones de transformación
# --------------------------

def normalize_returns(returns: pd.Series) -> pd.Series:
    """
    Normaliza una serie de retornos financieros.
    
    Args:
        returns: Serie de retornos
        
    Returns:
        Serie normalizada
    """
    return (returns - returns.mean()) / returns.std()

def calculate_volatility(returns: pd.Series, window: int = 21) -> pd.Series:
    """
    Calcula volatilidad rolling anualizada.
    
    Args:
        returns: Serie de retornos
        window: Ventana de cálculo (días)
        
    Returns:
        Serie de volatilidad
    """
    return returns.rolling(window).std() * np.sqrt(252)

# --------------------------
# Funciones de validación
# --------------------------

def validate_tickers(tickers: List[str], valid_tickers: List[str]) -> List[str]:
    """
    Filtra tickers válidos de una lista.
    
    Args:
        tickers: Lista de tickers a validar
        valid_tickers: Lista de tickers válidos
        
    Returns:
        Lista de tickers filtrados
    """
    valid = [t for t in tickers if t in valid_tickers]
    if len(valid) != len(tickers):
        logger.warning(f"Filtered out {len(tickers) - len(valid)} invalid tickers")
    return valid