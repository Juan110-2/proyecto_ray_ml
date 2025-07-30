# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ray import serve

from app.core.middleware import setup_middleware
from app.api.routes import router as inference_router
from app.core.config import settings

app = FastAPI(title="Inference API", version="1.0.0")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
setup_middleware(app)
app.include_router(inference_router)

# Prepara una ruta raíz para el pre‑flight y para pruebas rápidas
@app.get("/")
async def root():
    return {"msg": "Inference API running"}

# Ingreso a Ray Serve
@serve.deployment
@serve.ingress(app)
class InferenceAPI:
    pass

if __name__ == "__main__":
    serve.start(
        detached=False,
        http_options={"host": settings.RAY_HOST, "port": settings.RAY_PORT},
    )
    # Mantén el prefijo /inference
    serve.run(InferenceAPI.bind(), route_prefix="/", blocking=True)
