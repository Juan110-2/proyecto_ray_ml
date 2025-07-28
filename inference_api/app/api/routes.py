from fastapi import APIRouter, Depends
from app.api.models import Item_t
from app.services.portfolio_service import PortfolioService

router = APIRouter()

def get_portfolio_service() -> PortfolioService:
    """Dependency injection para el servicio de portfolio."""
    return PortfolioService()

@router.post('/')
def get_portfolio_returns_to_visualize(
    item: Item_t,
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """Endpoint para obtener los retornos del portfolio para visualización."""
    return portfolio_service.get_portfolio_returns_to_visualize(item)