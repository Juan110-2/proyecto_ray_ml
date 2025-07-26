import ray
import time

@ray.remote
def slow_double(x):
    time.sleep(1)  # Simula cómputo pesado
    return x * 2

@ray.remote
def slow_sum(arr):
    time.sleep(2)
    return sum(arr)


# === ray_backend/serve_api.py ===
from ray import serve
from fastapi import FastAPI

app = FastAPI()
serve.start(detached=True)

@serve.deployment(route_prefix="/double")
@serve.ingress(app)
class DoubleService:
    @app.get("/")
    async def double(self, x: int):
        return {"result": x * 2}

DoubleService.deploy()
