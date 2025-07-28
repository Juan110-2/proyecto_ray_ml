from fastapi import FastAPI
from ray import serve
from app.core.middleware import setup_middleware
from app.api.routes import router as inference_router
from app.api.plot_routes import router as plot_router  # NUEVO
from app.core.config import settings

app = FastAPI(title="Inference API", version="1.0.0")

# Configurar middlewares
setup_middleware(app)

# Incluir rutas
app.include_router(inference_router)
app.include_router(plot_router)  # NUEVO

@serve.deployment
@serve.ingress(app)
class InferenceAPI:
    """Clase principal de despliegue para Ray Serve."""
    pass

if __name__ == "__main__":
    serve.start(
        detached=True, 
        http_options={
            'host': settings.RAY_HOST,
            'port': settings.RAY_PORT
        }
    )
    serve.run(
        InferenceAPI.bind(),
        route_prefix='/inference',
        blocking=True
    )