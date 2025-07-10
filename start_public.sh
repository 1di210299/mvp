#!/bin/bash
# Script para exponer tu app local con ngrok
echo "🚀 Iniciando DataLens con exposición pública..."

# Instalar ngrok si no existe
if ! command -v ngrok &> /dev/null; then
    echo "📦 Instalando ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update && sudo apt install ngrok
fi

# Iniciar servicios
./start_services.sh &

# Esperar que el servidor esté listo
sleep 10

# Exponer con ngrok
echo "🌐 Exponiendo backend en puerto 8081..."
ngrok http 8081 --log=stdout > ngrok.log &

# Mostrar URL pública
sleep 3
curl -s localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['tunnels']:
    print('✅ Backend público en:', data['tunnels'][0]['public_url'])
else:
    print('❌ Error al obtener URL pública')
"

# Mantener ejecutándose
wait