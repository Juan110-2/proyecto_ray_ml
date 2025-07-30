import pandas as pd
from app.services.storage_service import StorageService
from app.services.data_service import DataService
from app.api.models import Item_t

class PortfolioService:
    """Servicio principal para manejar operaciones de portfolio."""
    
    def __init__(self):
        self.storage_service = StorageService()
        self.data_service = DataService()
    
    def get_portfolio_returns_to_visualize(self, item: Item_t) -> dict:
        """Procesa los datos del portfolio y los almacena para visualización."""

        portfolio_df = self.storage_service.download_data(item.index)
        
        data_ret = self.data_service.download_ticker_data(
            item.ticker, 
            item.start_date, 
            item.end_date
        )
        
        portfolio_df = portfolio_df.merge(
            data_ret,
            left_index=True,
            right_index=True
        )
        
        response = self.storage_service.store_portfolio(portfolio_df, item.ticker)
        return response