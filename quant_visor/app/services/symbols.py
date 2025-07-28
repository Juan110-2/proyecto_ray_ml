import pandas as pd
from typing import List

class SymbolFetcher:
    """Clase para obtener listados de símbolos de diferentes índices bursátiles"""
    
    @staticmethod
    def sp500() -> List[str]:
        """Obtiene los símbolos actuales del S&P 500"""
        print("[INFO] Descargando datos del S&P 500...")
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        print(f"[INFO] Filas descargadas S&P500: {len(sp500)}")
        
        sp500['Symbol'] = sp500['Symbol'].str.replace('.', '-')
        symbols = sp500['Symbol'].unique().tolist()
        print(f"[INFO] Símbolos únicos antes del filtro: {len(symbols)}")

        excluded = ['SOLV', 'GEV', 'SW', 'VLTO']
        symbols = [s for s in symbols if s not in excluded]
        print(f"[INFO] Símbolos únicos después del filtro: {len(symbols)}")

        return symbols

    @staticmethod
    def down_jones() -> List[str]:
        """Símbolos del Dow Jones Industrial Average"""
        print("[INFO] Cargando símbolos del Dow Jones")
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'BRK-B', 'JPM', 'JNJ', 'V', 'PG',
            'MA', 'UNH', 'DIS', 'HD', 'VZ', 'NVDA', 'PYPL', 'BAC', 'ADBE', 'CMCSA',
            'NFLX', 'NKE', 'KO', 'PEP', 'MRK', 'PFE', 'XOM', 'CVX', 'WMT', 'T'
        ]

    @staticmethod
    def nasdaq100() -> List[str]:
        """Obtiene los símbolos del NASDAQ-100"""
        print("[INFO] Descargando datos del Nasdaq 100...")
        nasdaq = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100#External_links')[4]
        print(f"[INFO] Filas descargadas Nasdaq 100: {len(nasdaq)}")

        nasdaq['Ticker'] = nasdaq['Ticker'].str.replace('.', '-')
        symbols = nasdaq['Ticker'].dropna().unique().tolist()
        print(f"[INFO] Símbolos únicos Nasdaq: {len(symbols)}")

        return symbols

    @staticmethod
    def tsxcomposite() -> List[str]:
        """Obtiene los símbolos del S&P/TSX Composite (Canadá)"""
        print("[INFO] Descargando datos del TSX Composite...")
        tsx = pd.read_html('https://en.wikipedia.org/wiki/S%26P/TSX_Composite_Index')[3]
        print(f"[INFO] Filas descargadas TSX: {len(tsx)}")

        tsx['Ticker'] = tsx['Ticker'].str.replace('.', '-')
        symbols = tsx['Ticker'].dropna().unique().tolist()
        print(f"[INFO] Símbolos únicos TSX antes del filtro: {len(symbols)}")

        deslisted = [
            'ABX', 'ADN', 'AE', 'AGI', 'AH', 'AIM', 'AKG', 'AMM', 'ANX', 'AR',
            # ... (lista completa de símbolos deslistados)
        ]
        symbols = [s for s in symbols if s not in deslisted]
        print(f"[INFO] Símbolos únicos TSX después del filtro: {len(symbols)}")

        return symbols

    @staticmethod
    def ftse100() -> List[str]:
        """Obtiene los símbolos del FTSE 100 (UK)"""
        print("[INFO] Descargando datos del FTSE 100...")
        ftse = pd.read_html('https://en.wikipedia.org/wiki/FTSE_100_Index')[4]
        print(f"[INFO] Filas descargadas FTSE 100: {len(ftse)}")

        ftse['Ticker'] = ftse['Ticker'].str.replace('.', '-')
        symbols = ftse['Ticker'].dropna().unique().tolist()
        print(f"[INFO] Símbolos únicos FTSE antes del filtro: {len(symbols)}")

        deslisted = [
            'AAL', 'ABF', 'ADM', 'AHT', 'ANTO', 'AV', 'AZN', 'BA', 'BARC', 'BATS',
            # ... (lista completa de símbolos deslistados)
        ]
        symbols = [s for s in symbols if s not in deslisted]
        print(f"[INFO] Símbolos únicos FTSE después del filtro: {len(symbols)}")

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
    print(f"[INFO] Obteniendo lista de símbolos para el índice: {index}")
    
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
        print("[ERROR] Índice no reconocido.")
        raise ValueError(f"Índice no soportado: {index}")