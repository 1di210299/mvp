#!/bin/bash

# Script para iniciar Django con configuración optimizada para ngrok

echo "🚀 Iniciando Django con configuración ngrok optimizada..."

# Exportar variables de entorno para ngrok
export DJANGO_DEBUG=True
export DJANGO_ALLOWED_HOSTS="*"

# Iniciar servidor Django
echo "🔧 Configuración:"
echo "   - DEBUG: $DJANGO_DEBUG"
echo "   - ALLOWED_HOSTS: $DJANGO_ALLOWED_HOSTS"
echo "   - Puerto: 8000"
echo ""

# Aplicar migraciones si es necesario
echo "📦 Verificando migraciones..."
python manage.py migrate --run-syncdb

echo ""
echo "🌐 Servidor disponible en:"
echo "   - Local: http://localhost:8000"
echo "   - Ngrok: https://016e520d8ade.ngrok-free.app"
echo ""
echo "📡 APIs n8n disponibles:"
echo "   - POST /api/inventory/api/orders/"
echo "   - POST /api/inventory/api/orders/callback/"
echo "   - GET/PUT /api/inventory/api/tenant/config/"
echo ""

# Iniciar servidor
python manage.py runserver 0.0.0.0:8000
