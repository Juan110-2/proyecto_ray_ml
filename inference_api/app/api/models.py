from pydantic import BaseModel

class Item_t(BaseModel):
    """Modelo para los datos de entrada del portfolio."""
    ticker: str
    start_date: str
    end_date: str
    index: str

class URLItem(BaseModel):
    """Modelo para generar gráficas desde URL."""
    url: str