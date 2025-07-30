import pandas as pd
from typing import List

class SymbolFetcher:
    """Clase para obtener listados de símbolos de diferentes índices bursátiles"""
    
    @staticmethod
    def sp500() -> List[str]:
        """Obtiene los símbolos actuales del S&P 500"""
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        
        sp500['Symbol'] = sp500['Symbol'].str.replace('.', '-')
        symbols = sp500['Symbol'].unique().tolist()

        excluded = ['SOLV', 'GEV', 'SW', 'VLTO']
        symbols = [s for s in symbols if s not in excluded]

        return symbols

    @staticmethod
    def down_jones() -> List[str]:
        """Símbolos del Dow Jones Industrial Average"""
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'BRK-B', 'JPM', 'JNJ', 'V', 'PG',
            'MA', 'UNH', 'DIS', 'HD', 'VZ', 'NVDA', 'PYPL', 'BAC', 'ADBE', 'CMCSA',
            'NFLX', 'NKE', 'KO', 'PEP', 'MRK', 'PFE', 'XOM', 'CVX', 'WMT', 'T'
        ]

    @staticmethod
    def nasdaq100() -> List[str]:
        """Obtiene los símbolos del NASDAQ-100"""
        nasdaq = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100#External_links')[4]

        nasdaq['Ticker'] = nasdaq['Ticker'].str.replace('.', '-')
        symbols = nasdaq['Ticker'].dropna().unique().tolist()
        print(f"[INFO] Símbolos únicos Nasdaq: {len(symbols)}")

        return symbols

    @staticmethod
    def tsxcomposite() -> List[str]:
        """Obtiene los símbolos del S&P/TSX Composite (Canadá)"""
        tsx = pd.read_html('https://en.wikipedia.org/wiki/S%26P/TSX_Composite_Index')[3]

        tsx['Ticker'] = tsx['Ticker'].str.replace('.', '-')
        symbols = tsx['Ticker'].dropna().unique().tolist()

        deslisted = [
            'ABX', 'ADN', 'AE', 'AGI', 'AH', 'AIM', 'AKG', 'AMM', 'ANX', 'AR',
            # ... (lista completa de símbolos deslistados)
        ]
        symbols = [s for s in symbols if s not in deslisted]

        return symbols

    @staticmethod
    def ftse100() -> List[str]:
        """Obtiene los símbolos del FTSE 100 (UK)"""
        ftse = pd.read_html('https://en.wikipedia.org/wiki/FTSE_100_Index')[4]

        ftse['Ticker'] = ftse['Ticker'].str.replace('.', '-')
        symbols = ftse['Ticker'].dropna().unique().tolist()

        deslisted = [
            'AAL', 'ABF', 'ADM', 'AHT', 'ANTO', 'AV', 'AZN', 'BA', 'BARC', 'BATS',
            # ... (lista completa de símbolos deslistados)
        ]
        symbols = [s for s in symbols if s not in deslisted]

        return symbols


def get_symbols(index: str) -> List[str]:
    """
    Función principal para obtener símbolos de un índice específico
    
    Args:
        index: Nombre del índice ('s&p500', 'downjones', 'nasdaq100', etc.)
    
    Returns:
        Lista de símbolos/tickers
    
    Raises:
        ValueError: Si el índice no es reconocido
    """
    
    index = index.lower()
    if index == 's&p500':
        return SymbolFetcher.sp500()
    elif index == 'downjones':
        return SymbolFetcher.down_jones()
    elif index == 'nasdaq100':
        return SymbolFetcher.nasdaq100()
    elif index == 'tsxcomposite':
        return SymbolFetcher.tsxcomposite()
    elif index == 'ftse100':
        return SymbolFetcher.ftse100()
    else:
        raise ValueError(f"Índice no soportado: {index}")