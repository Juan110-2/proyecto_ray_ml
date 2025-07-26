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