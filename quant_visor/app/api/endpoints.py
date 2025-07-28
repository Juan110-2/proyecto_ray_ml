import logging
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.schemas import TwitterAnalysisParams as TwitterParams
from ray import serve
from supabase import create_client
from storage3.exceptions import StorageException
import pandas as pd
import tempfile
from dotenv import load_dotenv
import io

# Schemas
from app.api.schemas import Item
# Services
from app.services.portfolio import PortfolioOptimizer
from app.services.symbols import get_symbols as symbolsList

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carga variables de entorno
load_dotenv()

app = FastAPI(
    title="Portfolio Optimization API",
    description="API for portfolio optimization using Rolling OLS and ML techniques",
    version="1.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@serve.deployment
@serve.ingress(app)
class TrainAPI:
    def __init__(self):
        """Inicializa la conexión con Supabase"""
        self._init_supabase()
        
    def _init_supabase(self):
        try:
            logger.info("Initializing Supabase connection...")
            self.supabase = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_KEY')
            )
            logger.info("Supabase client successfully initialized")
        except Exception as e:
            logger.error(f"Supabase initialization failed: {str(e)}")
            raise RuntimeError("Failed to initialize Supabase client")

    @app.post(
        "/yahoofinance",
        response_model=dict,
        status_code=status.HTTP_201_CREATED,
        summary="Optimize portfolio using Yahoo Finance data",
        tags=["Portfolio Optimization"]
    )
    async def store_portfolio_returns(self, item: Item):
        try:
            logger.info(f"Processing request for index: {item.index}")
            symbols = self._get_symbols(item.index)
            portfolio_returns = self._train_model(symbols, item)
            result = self._store_results(portfolio_returns, item.index)
            return {
                "status": "success",
                "message": "Portfolio optimized and stored successfully",
                "data": result
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Portfolio optimization process failed"
            )

    def _get_symbols(self, index: str) -> list:
        logger.info(f"Getting symbols for index: {index}")
        try:
            symbols = symbolsList(index)
            if not symbols:
                raise ValueError(f"No symbols found for index: {index}")
            logger.info(f"Retrieved {len(symbols)} symbols")
            return symbols
        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid index or symbol error: {str(e)}"
            )

    def _train_model(self, symbols: list, item: Item) -> pd.DataFrame:
        logger.info("Starting portfolio optimization training...")
        try:
            model = PortfolioOptimizer(
                symbols_list=symbols,
                start_date=item.start_date,
                end_date=item.end_date
            )
            return model.optimize(batch_size=item.batch_size)
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Model training error: {str(e)}"
            )
    def symbolsList(index):
        print(f"[INFO] Obteniendo lista de símbolos para el índice: {index}")
        
        # Normalizar el nombre del índice
        normalized_index = index.lower().replace("indextype.", "").replace("&", "")
        
        match normalized_index:
            case 'sp500':
                return sp500()
            case 'downjones' | 'dowjones':  # Acepta ambas variantes
                return down_jones()
            case 'nasdaq100':
                return nasdaq100()
            case 'tsxcomposite':
                return tsxcomposite()
            case 'ftse100':
                return ftse100()
            case _:
                print(f"[ERROR] Índice no reconocido: {index}")
                return []
    def _store_results(self, portfolio_returns: pd.DataFrame, index: str) -> dict:
        logger.info("Storing portfolio results...")
        
        # Nombre del archivo será exactamente el index que recibimos
        filename = f"{index.lower()}.csv"  # o usar la normalización si prefieres
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                temp_path = tmp.name
                portfolio_returns.to_csv(temp_path, index=True)
                
            with open(temp_path, "rb") as f:
                response = self.supabase.storage.from_("datasets").upload(
                    file=f,
                    path=f'train/{filename}',
                    file_options={
                        "cache-control": "3600",
                        "upsert": "true"
                    }
                )
                
            logger.info("Portfolio results stored successfully")
            return {
                "bucket": "datasets",
                "path": f"train/{filename}",
                "size": os.path.getsize(temp_path)
            }
        except StorageException as e:
            logger.error(f"Supabase storage error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to store results in database"
            )
        except Exception as e:
            logger.error(f"Storage process failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save portfolio results"
            )
        finally:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

    @app.get("/health", include_in_schema=False)
    async def health_check(self):
        return {
            "status": "healthy",
            "supabase_connected": hasattr(self, 'supabase') and self.supabase is not None
        }
    

    def _download_twitter_data(self) -> pd.DataFrame:
        """Descarga datos de Twitter desde Supabase"""
        try:
            logger.info("Downloading Twitter data from Supabase")
            response = self.supabase.storage.from_("datasets").download(
                "twitter-data/sentiment_data.csv"
            )
            df = pd.read_csv(io.StringIO(response.decode('utf-8')))
            
            # Convertir fecha y asegurar columnas requeridas
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            required_cols = {'date', 'symbol', 'text', 'twitterComments', 'twitterLikes'}
            if not required_cols.issubset(df.columns):
                raise ValueError("Missing required columns in Twitter data")
                
            return df
            
        except StorageException as e:
            logger.error(f"Supabase download error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Twitter data file not found in storage"
            )
        except Exception as e:
            logger.error(f"Error processing Twitter data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid Twitter data format: {str(e)}"
            )

    @app.post(
    "/twitter",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Optimize portfolio using Twitter sentiment data",
    description="""
    Performs portfolio optimization based on Twitter sentiment analysis.
    The service will:
    1. Download Twitter data from Supabase storage
    2. Process and analyze sentiment
    3. Generate optimal portfolio based on sentiment signals
    4. Store results back to Supabase
    """,
    tags=["Portfolio Optimization"],
    responses={
        201: {"description": "Analysis completed successfully"},
        404: {"description": "Twitter data not found"},
        422: {"description": "Invalid data format or processing error"},
        500: {"description": "Internal server error"}
    }
    )
    async def twitter_sentiment_analysis(self, params: TwitterParams):
        """
        Perform Twitter sentiment analysis and portfolio optimization.
        
        - **start_date**: Start date for analysis (YYYY-MM-DD)
        - **end_date**: End date for analysis (YYYY-MM-DD)
        - **batch_size**: Batch size for parallel processing (default: 5)
        - **min_likes**: Minimum likes threshold (default: 20)
        - **min_comments**: Minimum comments threshold (default: 10)
        """
        try:
            logger.info(f"Starting Twitter analysis from {params.start_date} to {params.end_date}")
            
            # 1. Descargar datos con filtrado por fecha
            twitter_data = self._download_twitter_data()
            twitter_data = twitter_data[
                (twitter_data['date'] >= params.start_date.strftime('%Y-%m-%d')) &
                (twitter_data['date'] <= params.end_date.strftime('%Y-%m-%d'))
            ]
            
            if twitter_data.empty:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No data available for the selected date range"
                )

            # 2. Procesar datos
            service = TwitterSentimentAnalyzer(twitter_data)
            portfolio_returns = service.full_pipeline(
                min_likes=params.min_likes,
                min_comments=params.min_comments
            )
            
            # 3. Almacenar resultados
            result = self._store_results(
                portfolio_returns, 
                f'twitter/sentiment_{params.start_date}_{params.end_date}.csv'
            )
            
            return {
                "status": "success",
                "message": "Twitter analysis completed successfully",
                "data": {
                    "period": f"{params.start_date} to {params.end_date}",
                    "portfolio_stats": portfolio_returns.describe().to_dict(),
                    "storage_info": result
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Twitter analysis failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Twitter analysis failed: {str(e)}"
            )