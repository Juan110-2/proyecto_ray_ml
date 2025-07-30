#!/bin/bash

# setup-ec2.sh
# Script para configurar una instancia EC2 nueva para Quant Visor

set -e

echo "🔧 Configurando instancia EC2 para Quant Visor..."

# Actualizar sistema
sudo apt-get update && sudo apt-get upgrade -y

# Instalar dependencias básicas
sudo apt-get install -y \
    curl \
    git \
    htop \
    vim \
    ufw \
    nginx \
    certbot \
    python3-certbot-nginx

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configurar límites del sistema para Ray
sudo bash -c 'cat >> /etc/security/limits.conf << EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
EOF'

# Configurar sysctl para mejor rendimiento
sudo bash -c 'cat >> /etc/sysctl.conf << EOF
# Optimizaciones para Ray y aplicaciones de ML
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
vm.overcommit_memory = 1
EOF'

sudo sysctl -p

# Configurar firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 8265/tcp
sudo ufw --force enable

# Crear estructura de directorios
mkdir -p ~/quant_visor/{data,model_cache,logs,ssl}

# Configurar swap (útil para instancias con poca RAM)
if [ ! -f /swapfile ]; then
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# Instalar CloudWatch Agent (opcional, para monitoreo)
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
rm amazon-cloudwatch-agent.deb

echo "✅ Configuración inicial completada"
echo "📝 Siguiente paso: Ejecutar el script de despliegue deploy-to-ec2.sh"