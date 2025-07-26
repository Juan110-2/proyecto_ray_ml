import ray
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle

# Inicializamos Ray solo si no está iniciado (esto lo haces en main si no usas ray start --head)
if not ray.is_initialized():
    ray.init()

@ray.remote
def train_model():
    # Cargar datos de ejemplo (Iris)
    data = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        data.data, data.target, test_size=0.2, random_state=42
    )

    # Entrenar modelo
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    # Guardar modelo como bytes
    model_bytes = pickle.dumps(model)
    return model_bytes

@ray.remote
def predict(model_bytes, input_data):
    # Cargar modelo desde bytes
    model = pickle.loads(model_bytes)

    # Convertir input_data a np.array si es necesario
    X = np.array(input_data)

    # Realizar predicción
    prediction = model.predict(X)
    return prediction.tolist()
