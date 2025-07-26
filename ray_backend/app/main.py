# app/main.py

from ray import serve
from fastapi import FastAPI, Request

from app.core import model_runner

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from Ray Serve!"}

@serve.deployment
@serve.ingress(app)
class MLModelDeployment:
    def __init__(self):
        # Aquí podrías precargar el modelo entrenado
        self.model_bytes = None

    @app.post("/train")
    async def train(self):
        self.model_bytes = await model_runner.train_model.remote()
        return {"message": "Modelo entrenado y almacenado en memoria"}

    @app.post("/predict")
    async def predict(self, request: Request):
        if not self.model_bytes:
            return {"error": "Primero entrena el modelo con /train"}

        input_data = await request.json()
        prediction = await model_runner.predict.remote(self.model_bytes, input_data)
        return {"prediction": prediction}

# Este es el entrypoint que leerá serve
entrypoint = MLModelDeployment.bind()
