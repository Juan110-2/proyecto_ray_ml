# serve_app.py

from fastapi import FastAPI
from ray import serve

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from Ray Serve + FastAPI"}

# ❌ NO uses route_prefix aquí
@serve.deployment
@serve.ingress(app)
class FastAPIWrapper:
    pass

# ✅ Define el app con nombre que usarás en el CLI
serve_app = FastAPIWrapper.bind()
