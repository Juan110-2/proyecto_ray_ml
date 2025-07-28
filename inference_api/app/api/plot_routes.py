from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.api.models import URLItem
from app.services.plot_service import PlotService

router = APIRouter(prefix="/plot", tags=["plots"])

def get_plot_service() -> PlotService:
    """Dependency injection para el servicio de gráficas."""
    return PlotService()

@router.post('/')
async def generate_graph(
    item: URLItem,
    plot_service: PlotService = Depends(get_plot_service)
) -> StreamingResponse:
    """Endpoint para generar gráficas desde URL de Supabase."""
    try:
        return await plot_service.generate_graph(item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))