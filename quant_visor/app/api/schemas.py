from datetime import date
from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

class IndexType(str, Enum):
    """Enumeración de los índices soportados"""
    SP500 = 's&p500'
    DOW_JONES = 'downjones'
    NASDAQ = 'nasdaq100'
    TSX = 'tsxcomposite'
    FTSE = 'ftse100'

class Item(BaseModel):
    """
    Modelo principal para requests de optimización de portafolio
    
    Attributes:
        index: Índice bursátil a utilizar
        start_date: Fecha de inicio en formato YYYY-MM-DD
        end_date: Fecha de fin en formato YYYY-MM-DD
        batch_size: Tamaño del batch para procesamiento paralelo (1-100)
    """
    index: IndexType = Field(..., example="s&p500", description="Índice bursátil a analizar")
    start_date: date = Field(..., example="2020-01-01", description="Fecha de inicio del análisis")
    end_date: date = Field(..., example="2023-01-01", description="Fecha de fin del análisis")
    batch_size: int = Field(10, gt=0, le=100, example=10, description="Tamaño del batch para procesamiento paralelo")

    @validator('end_date')
    def validate_dates(cls, end_date, values):
        """Valida que la fecha de fin sea posterior a la de inicio"""
        if 'start_date' in values and end_date <= values['start_date']:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio")
        return end_date

    class Config:
        schema_extra = {
            "example": {
                "index": "s&p500",
                "start_date": "2020-01-01",
                "end_date": "2023-01-01",
                "batch_size": 10
            }
        }

class TwitterSourceType(str, Enum):
    """Enumeración de fuentes de datos para Twitter"""
    SUPABASE = 'supabase'
    API = 'api'
    CSV = 'csv'

class TwitterSentimentThresholds(BaseModel):
    """
    Umbrales para el análisis de sentimiento en Twitter
    
    Attributes:
        min_likes: Mínimo de likes para considerar un tweet
        min_comments: Mínimo de comentarios para considerar un tweet
        min_engagement_ratio: Ratio mínimo de engagement (comentarios/likes)
    """
    min_likes: int = Field(20, gt=0, description="Mínimo de likes requeridos")
    min_comments: int = Field(10, gt=0, description="Mínimo de comentarios requeridos")
    min_engagement_ratio: float = Field(0.1, ge=0, description="Ratio mínimo de engagement")

class TwitterAnalysisParams(BaseModel):
    """
    Parámetros para el análisis de sentimiento en Twitter
    
    Attributes:
        start_date: Fecha de inicio del análisis
        end_date: Fecha de fin del análisis
        source_type: Fuente de los datos de Twitter
        batch_size: Tamaño del batch para procesamiento paralelo
        thresholds: Umbrales para filtrar tweets
        symbols: Lista opcional de símbolos a filtrar
    """
    start_date: date = Field(..., description="Fecha de inicio del análisis")
    end_date: date = Field(..., description="Fecha de fin del análisis")
    source_type: TwitterSourceType = Field(
        TwitterSourceType.SUPABASE,
        description="Fuente de los datos de Twitter"
    )
    batch_size: int = Field(
        5, gt=0, le=20,
        description="Tamaño del batch para procesamiento paralelo"
    )
    thresholds: TwitterSentimentThresholds = Field(
        default_factory=TwitterSentimentThresholds,
        description="Umbrales para el análisis"
    )
    symbols: Optional[List[str]] = Field(
        None,
        description="Lista opcional de símbolos específicos a analizar"
    )

    @validator('end_date')
    def validate_dates(cls, end_date, values):
        """Valida que la fecha de fin sea posterior a la de inicio"""
        if 'start_date' in values and end_date <= values['start_date']:
            raise ValueError("End date must be after start date")
        return end_date

    class Config:
        schema_extra = {
            "example": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "source_type": "supabase",
                "batch_size": 5,
                "thresholds": {
                    "min_likes": 20,
                    "min_comments": 10,
                    "min_engagement_ratio": 0.1
                },
                "symbols": ["AAPL", "MSFT", "GOOGL"]
            }
        }

class TwitterSentimentResults(BaseModel):
    """
    Resultados del análisis de sentimiento en Twitter
    
    Attributes:
        symbol: Símbolo del activo
        positive_tweets: Cantidad de tweets positivos
        negative_tweets: Cantidad de tweets negativos
        avg_sentiment: Sentimiento promedio (-1 a 1)
        engagement_score: Puntaje de engagement
    """
    symbol: str = Field(..., description="Símbolo del activo")
    positive_tweets: int = Field(..., ge=0, description="Cantidad de tweets positivos")
    negative_tweets: int = Field(..., ge=0, description="Cantidad de tweets negativos")
    avg_sentiment: float = Field(..., ge=-1, le=1, description="Sentimiento promedio")
    engagement_score: float = Field(..., ge=0, description="Puntaje de engagement")

class TwitterPortfolioResult(BaseModel):
    """
    Resultados del portafolio basado en Twitter
    
    Attributes:
        date: Fecha del cálculo
        strategy_return: Retorno de la estrategia
        top_positive: Lista de activos más positivos
        top_negative: Lista de activos más negativos
        sentiment_stats: Estadísticas agregadas
    """
    date: datetime = Field(..., description="Fecha del cálculo")
    strategy_return: float = Field(..., description="Retorno porcentual")
    top_positive: List[TwitterSentimentResults] = Field(
        ..., 
        description="Top activos con mejor sentimiento"
    )
    top_negative: List[TwitterSentimentResults] = Field(
        ..., 
        description="Top activos con peor sentimiento"
    )
    sentiment_stats: Dict[str, float] = Field(
        ..., 
        description="Estadísticas agregadas de sentimiento"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }


class PortfolioResult(BaseModel):
    """
    Modelo para los resultados del portafolio optimizado
    
    Attributes:
        date: Fecha del resultado
        strategy_return: Retorno de la estrategia en porcentaje
        sharpe_ratio: Ratio de Sharpe (opcional)
        volatility: Volatilidad anualizada (opcional)
    """
    date: datetime = Field(..., description="Fecha del cálculo")
    strategy_return: float = Field(..., ge=-100, le=100, description="Retorno porcentual de la estrategia")
    sharpe_ratio: Optional[float] = Field(None, description="Ratio de Sharpe anualizado")
    volatility: Optional[float] = Field(None, ge=0, description="Volatilidad anualizada en porcentaje")

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

class ErrorResponse(BaseModel):
    """
    Modelo estandarizado para respuestas de error
    
    Attributes:
        error: Tipo de error
        message: Mensaje descriptivo
        details: Información adicional opcional
    """
    error: str = Field(..., example="validation_error", description="Tipo de error")
    message: str = Field(..., example="Invalid date range", description="Mensaje de error descriptivo")
    details: Optional[dict] = Field(None, description="Detalles adicionales del error")

class HealthCheckResponse(BaseModel):
    """
    Modelo para respuestas de health check
    
    Attributes:
        status: Estado del servicio
        version: Versión de la API
        timestamp: Fecha y hora de la verificación
    """
    status: str = Field(..., example="healthy", description="Estado del servicio")
    version: str = Field(..., example="1.0.0", description="Versión de la API")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora del check")

class BatchProcessResponse(BaseModel):
    """
    Modelo para respuestas de procesos batch
    
    Attributes:
        job_id: ID del proceso
        status: Estado actual
        progress: Porcentaje de completado
        result_url: URL para obtener resultados (opcional)
    """
    job_id: str = Field(..., description="Identificador único del proceso")
    status: str = Field(..., description="Estado del proceso (pending|running|completed|failed)")
    progress: float = Field(0, ge=0, le=100, description="Porcentaje de completado")
    result_url: Optional[str] = Field(None, description="URL para acceder a los resultados cuando esté completo")


class TwitterProcessResponse(BatchProcessResponse):
    """
    Respuesta extendida para procesos de Twitter
    
    Attributes:
        analyzed_tweets: Cantidad total de tweets analizados
        time_elapsed: Tiempo transcurrido en segundos
    """
    analyzed_tweets: int = Field(..., ge=0, description="Tweets analizados")
    time_elapsed: float = Field(..., ge=0, description="Tiempo en segundos")