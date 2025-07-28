import yfinance as yf
import numpy as np
import pandas as pd

class DataService:
    """Servicio para manejar la descarga y procesamiento de datos financieros."""
    
    @staticmethod
    def download_ticker_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Descarga datos de un ticker específico usando yfinance."""
        data = yf.download(
            tickers=ticker,
            start=start_date,
            end=end_date, 
            auto_adjust=False
        )
        data.columns = data.columns.droplevel(1)
        
        data_ret = np.log(data[['Adj Close']]).diff().dropna().rename(
            {'Adj Close': f'{ticker} Buy&Hold'}, axis=1
        )
        
        return data_ret