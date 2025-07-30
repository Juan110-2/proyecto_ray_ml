#!/bin/bash

# deploy-to-ec2.sh
# Script para desplegar la aplicación Quant Visor en EC2

set -e

echo "🚀 Iniciando despliegue de Quant Visor en EC2..."

# Variables de configuración
EC2_HOST=${EC2_HOST:-""}
EC2_USER=${EC2_USER:-"ubuntu"}
APP_DIR="/home/$EC2_USER/quant_visor"
KEY_PATH=${KEY_PATH:-"~/.ssh/your-key.pem"}

# Validar variables
if [ -z "$EC2_HOST" ]; then
    echo "❌ Error: EC2_HOST no está definido"
    echo "Uso: EC2_HOST=tu-instancia.amazonaws.com ./deploy-to-ec2.sh"
    exit 1
fi

# Función para ejecutar comandos en EC2
remote_exec() {
    ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" "$@"
}

# 1. Preparar archivos localmente
echo "📦 Preparando archivos..."
tar -czf quant_visor.tar.gz \
    --exclude='venv311' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='data/*' \
    --exclude='model_cache/*' \
    .

# 2. Copiar archivos a EC2
echo "📤 Copiando archivos a EC2..."
scp -i "$KEY_PATH" quant_visor.tar.gz "$EC2_USER@$EC2_HOST:/tmp/"

# 3. Configurar EC2
echo "🔧 Configurando EC2..."
remote_exec << 'EOF'
    # Actualizar sistema
    sudo apt-get update
    sudo apt-get upgrade -y

    # Instalar Docker si no está instalado
    if ! command -v docker &> /dev/null; then
        echo "🐳 Instalando Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
    fi

    # Instalar Docker Compose si no está instalado
    if ! command -v docker-compose &> /dev/null; then
        echo "🐳 Instalando Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi

    # Crear directorio de la aplicación
    mkdir -p ~/quant_visor
    cd ~/quant_visor

    # Extraer archivos
    tar -xzf /tmp/quant_visor.tar.gz
    rm /tmp/quant_visor.tar.gz

    # Crear directorios necesarios
    mkdir -p data model_cache

    # Configurar firewall
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8000/tcp
    sudo ufw allow 8265/tcp
EOF

# 4. Construir y ejecutar con Docker Compose
echo "🏗️ Construyendo y ejecutando aplicación..."
remote_exec << 'EOF'
    cd ~/quant_visor
    
    # Detener servicios existentes
    docker-compose down || true
    
    # Construir imagen
    docker-compose build
    
    # Iniciar servicios
    docker-compose up -d
    
    # Verificar estado
    sleep 10
    docker-compose ps
    
    # Mostrar logs
    docker-compose logs --tail=50
EOF

# 5. Verificar despliegue
echo "✅ Verificando despliegue..."
sleep 5

# Verificar health endpoint
if curl -f "http://$EC2_HOST:8000/health" > /dev/null 2>&1; then
    echo "✅ API está funcionando correctamente"
else
    echo "❌ Error: API no responde"
    remote_exec "cd ~/quant_visor && docker-compose logs"
    exit 1
fi

# Limpiar archivo temporal
rm -f quant_visor.tar.gz

echo "🎉 Despliegue completado exitosamente!"
echo ""
echo "📋 URLs disponibles:"
echo "   - API: http://$EC2_HOST:8000"
echo "   - Ray Dashboard: http://$EC2_HOST:8265"
echo "   - Documentación: http://$EC2_HOST:8000/docs"
echo ""
echo "💡 Comandos útiles:"
echo "   - Ver logs: ssh -i $KEY_PATH $EC2_USER@$EC2_HOST 'cd ~/quant_visor && docker-compose logs -f'"
echo "   - Reiniciar: ssh -i $KEY_PATH $EC2_USER@$EC2_HOST 'cd ~/quant_visor && docker-compose restart'"
echo "   - Detener: ssh -i $KEY_PATH $EC2_USER@$EC2_HOST 'cd ~/quant_visor && docker-compose down'"