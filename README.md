# Proyecto Final - Infraestructuras Paralelas y Distribuidas

## Tecnologías Usadas
- Python + Ray para paralelismo
- Flask para APIs REST
- HTML + JS para cliente web
- Docker + Compose para contenerización

## Estructura
```
ray_backend/     # Código con funciones paralelas (Ray)
api_flask/       # API REST con Flask
client_web/      # Interfaz web
deployment/      # Archivos Docker
```

## Cómo ejecutar localmente
```bash
git clone <repo>
cd proyecto_ray_ml
docker-compose -f deployment/docker-compose.yml up --build
```

Luego abre `http://localhost:5000` para probar la API, o accede a la interfaz web en el cliente.

## Próximos pasos
- Despliegue en AWS EC2
- Benchmarking paralelo vs secuencial
- Informe técnico y presentación