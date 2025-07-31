# main.py
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from ray import serve
from app.api.endpoints import TrainAPI
from app.core.config import settings
import logging, os, ray, sys, signal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class PortfolioService:
    def __init__(self):
        # La app FastAPI sólo la usamos para /health local
        self.app = FastAPI(
            title="Portfolio Optimization API",
            description="API for portfolio optimization using Ray Serve",
            version="1.0.0",
        )

        @self.app.get("/health", include_in_schema=False)
        async def health_check():
            return {
                "status": "healthy",
                "ray_initialized": ray.is_initialized(),
            }

    # ---------- configuración ray ----------
    def configure_ray(self):
        return {
            "num_cpus": int(os.getenv("RAY_NUM_CPUS", os.cpu_count() or 4)),
            "num_gpus": int(os.getenv("RAY_NUM_GPUS", 0)),
            "object_store_memory": int(
                os.getenv("RAY_OBJECT_STORE_MEMORY", 200 * 1024 * 1024)
            ),
            "ignore_reinit_error": True,
            "include_dashboard": False,
        }

    # ---------- arranque ----------
    def start_services(self):
        try:
            logger.info("🔧 Inicializando Ray …")
            ray.init(**self.configure_ray())

            logger.info("🚀 Iniciando Ray Serve con CORS global …")
            serve.start(
                http_options={
                    "host": settings.HOST,
                    "port": settings.PORT,
                    "location": "EveryNode",
                    # *** CORS a nivel de proxy HTTP ***
                    "http_middlewares": [
                        (
                            StarletteCORSMiddleware,
                            {
                                "allow_origins": ["*"],
                                "allow_credentials": True,
                                "allow_methods": ["*"],
                                "allow_headers": ["*"],
                            },
                        )
                    ],
                }
            )

            logger.info("📦 Desplegando TrainAPI en /train …")
            serve.run(TrainAPI.bind(), route_prefix="/train", name="train_api")

            logger.info(
                f"✅ Servicio disponible en http://{settings.HOST}:{settings.PORT}"
            )

        except Exception as e:
            logger.error(f"Error al iniciar servicios: {e}")
            raise

    # ---------- apagado ----------
    def shutdown_services(self):
        logger.info("🛑 Deteniendo servicios …")
        try:
            serve.shutdown()
        except Exception:
            logger.warning("Ray Serve ya estaba detenido o no inicializado.")
        if ray.is_initialized():
            ray.shutdown()
        logger.info("Servicios detenidos correctamente")

def main():
    service = PortfolioService()

    def _handle_signal(signum, _):
        logger.info(f"⚠️  Recibida señal {signum}, apagando servicios …")
        service.shutdown_services()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        service.start_services()
        if sys.stdin.isatty():
            input("⏳ Pulsa Enter para detener los servicios …\n")
        else:
            signal.pause()
    except Exception as e:
        logger.error(f"Error fatal: {e}")
    finally:
        service.shutdown_services()
        logger.info("🔚 Aplicación terminada")

if __name__ == "__main__":
    main()
