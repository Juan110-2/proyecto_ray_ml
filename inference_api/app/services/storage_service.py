import io
import tempfile
import uuid
import pandas as pd
from supabase import create_client
from storage3.utils import StorageException
from app.core.config import settings
from app.utils.exceptions import FileNotFoundError, UploadError

class StorageService:
    """Servicio para manejar operaciones de almacenamiento con Supabase."""
    
    def __init__(self):
        self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    def download_data(self, index: str) -> pd.DataFrame:
        """Descarga datos del índice desde Supabase storage."""
        try:
            response = (
                self.supabase.storage
                .from_("datasets")
                .download(f"train/{index}.csv")
            )

            df = pd.read_csv(io.StringIO(response.decode('utf-8')))
            df = df.set_index('Date')
            df.index = pd.to_datetime(df.index, format='%Y-%m-%d')
            df = df.sort_index()
                       
            return df
            
        except StorageException as e:
            if getattr(e, 'error', None) and e.error.get("statusCode") == 404:
                raise FileNotFoundError("train.csv not found in Supabase storage")
            else:
                raise Exception(f"Download failed: {e}")
    
    def store_portfolio(self, portfolio_returns: pd.DataFrame, ticker: str) -> dict:
        """Almacena los resultados del portfolio en Supabase storage."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                temp_path = tmp.name
                portfolio_returns.to_csv(temp_path, index=True)
    
            file_id = uuid.uuid4()
            with open(temp_path, "rb") as f:
                response = (
                    self.supabase.storage
                    .from_("datasets")
                    .upload(
                        file=f,
                        path=f"inference/inference_{ticker}_{file_id}.csv",
                        file_options={"cache-control": "3600", "upsert": "true"}
                    )
                )
            return response
        except Exception as e:
            raise UploadError(f"Failed to upload portfolio data: {e}")