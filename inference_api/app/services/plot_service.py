import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import numpy as np
import io
from fastapi.responses import StreamingResponse
from app.services.storage_service import StorageService
from app.api.models import URLItem
from fastapi.responses import JSONResponse

class PlotService:
    """Servicio para generar gráficas."""
    
    def __init__(self):
        self.storage_service = StorageService()
    
    async def generate_graph(self, item: URLItem) -> StreamingResponse:
        """Genera una gráfica a partir de una URL de Supabase."""
        try:
            # Descargar datos usando el storage service existente
            response = (
                self.storage_service.supabase.storage
                .from_("datasets")
                .download(item.url)
            )

            # Procesar datos
            df = pd.read_csv(io.StringIO(response.decode('utf-8')))
            df = df.set_index('Date')
            df.index = pd.to_datetime(df.index, format='%Y-%m-%d')
            df = df.sort_index()

            # Generar gráfica
            plt.style.use('ggplot')
            portfolio_cumulative_return = np.exp(np.log1p(df).cumsum()) - 1
            portfolio_cumulative_return[:'2023-09-29'].plot(figsize=(16, 6))

            plt.title('Unsupervised Learning Trading Strategy Returns Over Time')
            plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1))
            plt.ylabel('Return')

            # Convertir a bytes
            portfolio_cumulative_return = portfolio_cumulative_return[:'2023-09-29']
            result = [
                {"date": date.strftime('%Y-%m-%d'), **row.dropna().to_dict()}
                for date, row in portfolio_cumulative_return.iterrows()
            ]

            return JSONResponse(content=result)

        except Exception as e:
            raise Exception(f"Error generating plot: {str(e)}")