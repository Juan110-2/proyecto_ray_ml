FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Instala gcc si algún paquete necesita compilar
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia primero requirements para cachear bien las capas
COPY requirements.txt .

# Instala dependencias
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código
COPY . .

# Expone el puerto si aplica
EXPOSE 8001

# Ejecuta el script como módulo
CMD ["python", "-m", "app.main"]