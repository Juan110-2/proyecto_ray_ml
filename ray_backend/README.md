# 🧠 Ray Backend - Proyecto de Machine Learning Distribuido

Este repositorio contiene el backend del proyecto de Machine Learning usando [Ray](https://www.ray.io/) 
para ejecutar tareas distribuidas. Está desarrollado en Python y sirve como API para gestionar los modelos 
y tareas paralelas con FastAPI.

---

## 📁 Estructura del Proyecto

```
ray_backend/
│
├── app/                                # Código fuente principal del backend
│   ├── __init__.py
│   ├── main.py                         # Inicializa la aplicación Ray + FastAPI
│   ├── serve_start.py                  # Ejecuta el servidor Ray Serve con FastAPI
│   ├── core/                           # Lógica de negocio (ML distribuido, Ray tasks, etc.)
│   │   ├── __init__.py
│   │   └── model_runner.py             # Lógica principal del modelo ML distribuido
│   ├── api/                            # Lógica de enrutamiento y controladores FastAPI
│   │   ├── __init__.py
│   │   └── routes.py                   # Define endpoints de la API
│   ├── config/                         # Archivos de configuración
│   │   ├── __init__.py
│   │   └── serve_config.yaml           # Configuración de Ray Serve
│   └── utils/                          # Utilidades compartidas
│       ├── __init__.py
│       └── logger.py                   # Configuración de logs, etc.
│
├── venv/                               # Entorno virtual (excluir del repo)
├── requirements.txt                    # Dependencias del proyecto
└── README.md                           # Documentación del backend
```

---

## 🚀 Requisitos

Antes de comenzar, asegúrate de tener instalado:

- Python 3.10 o superior
- [Ray](https://docs.ray.io/en/latest/)
- FastAPI

---

## ⚙️ Instalación

### 1. Crear entorno virtual

```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## ▶️ Uso

### 1. Iniciar el clúster de Ray local

```bash
ray start --head
```

### 2. Detener el clúster de Ray

```bash
ray stop
```

### 3. Iniciar servidor de API

```bash
python app/main.py
```

### 4. Desplegar con Ray Serve

```bash
serve run app.config.serve_config
```

---

## 🔍 Endpoints de prueba

Puedes probar el backend accediendo a:

- Documentación interactiva Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Documentación alternativa ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
