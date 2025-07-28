from fastapi import FastAPI
from ray import serve
from app.api.endpoints import TrainAPI
from app.core.config import settings
import logging
import os
import ray

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PortfolioService:
    def __init__(self):
        self.app = FastAPI(
            title="Portfolio Optimization API",
            description="API for portfolio optimization using Ray Serve",
            version="1.0.0"
        )
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "ray_initialized": ray.is_initialized()
            }

    def configure_ray(self):
        """Configura los parámetros de Ray"""
        return {
            'num_cpus': int(os.getenv('RAY_NUM_CPUS', os.cpu_count() or 4)),
            'num_gpus': int(os.getenv('RAY_NUM_GPUS', 0)),
            'object_store_memory': int(os.getenv('RAY_OBJECT_STORE_MEMORY', 200 * 1024 * 1024)),
            'ignore_reinit_error': True,
            'include_dashboard': False
        }

    def start_services(self):
        """Inicia todos los servicios integrados"""
        try:
            logger.info("Inicializando Ray...")
            ray.init(**self.configure_ray())

            logger.info("Iniciando Ray Serve...")
            serve.start(
                http_options={
                    'host': settings.HOST,
                    'port': settings.PORT,
                    'location': 'EveryNode'
                }
            )

            logger.info("Desplegando TrainAPI...")
            serve.run(
                TrainAPI.bind(),
                route_prefix='/train',
                name="train_api"
            )

            logger.info(f"Servicio iniciado en http://{settings.HOST}:{settings.PORT}")

        except Exception as e:
            logger.error(f"Error al iniciar servicios: {e}")
            raise

    def shutdown_services(self):
        """Apaga los servicios correctamente"""
        logger.info("Deteniendo servicios...")
        serve.shutdown()
        if ray.is_initialized():
            ray.shutdown()
        logger.info("Servicios detenidos correctamente")


if __name__ == '__main__':
    service = PortfolioService()

    try:
        service.start_services()
        input("⏳ Presiona Enter para detener los servicios...\n")

    except KeyboardInterrupt:
        logger.info("Recibida señal de interrupción")

    except Exception as e:
        logger.error(f"Error fatal: {e}")

    finally:
        service.shutdown_services()
        logger.info("Aplicación terminada")
