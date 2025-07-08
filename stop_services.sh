#!/bin/bash

# Script para detener todos los servicios de DataLens
# Uso: ./stop_services.sh

echo "🛑 Deteniendo servicios de DataLens..."

# Función para detener Django
stop_django() {
    echo "🌐 Deteniendo servidor Django..."
    pkill -f "manage.py runserver"
    if ! lsof -ti:8081 >/dev/null 2>&1; then
        echo "✅ Servidor Django detenido"
    else
        echo "⚠️ El puerto 8081 aún está en uso"
    fi
}

# Función para detener Celery Worker
stop_celery_worker() {
    echo "👷 Deteniendo Celery Worker..."
    if [ -f logs/celery/worker.pid ]; then
        celery -A datalens_backend control shutdown
        rm -f logs/celery/worker.pid
    fi
    pkill -f "celery.*worker"
    if ! pgrep -f "celery.*worker" > /dev/null; then
        echo "✅ Celery Worker detenido"
    else
        echo "⚠️ Celery Worker aún ejecutándose"
    fi
}

# Función para detener Celery Beat
stop_celery_beat() {
    echo "⏰ Deteniendo Celery Beat..."
    if [ -f logs/celery/beat.pid ]; then
        kill $(cat logs/celery/beat.pid) 2>/dev/null
        rm -f logs/celery/beat.pid
    fi
    pkill -f "celery.*beat"
    if ! pgrep -f "celery.*beat" > /dev/null; then
        echo "✅ Celery Beat detenido"
    else
        echo "⚠️ Celery Beat aún ejecutándose"
    fi
}

# Función para detener Redis (opcional)
stop_redis() {
    read -p "¿Detener Redis también? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📡 Deteniendo Redis..."
        redis-cli shutdown 2>/dev/null || pkill redis-server
        if ! pgrep -f redis-server > /dev/null; then
            echo "✅ Redis detenido"
        else
            echo "⚠️ Redis aún ejecutándose"
        fi
    else
        echo "📡 Redis mantenido ejecutándose"
    fi
}

# Función para verificar el estado
check_services() {
    echo ""
    echo "📊 Estado final de los servicios:"
    
    if pgrep -f redis-server > /dev/null; then
        echo "✅ Redis: Ejecutándose"
    else
        echo "❌ Redis: Detenido"
    fi
    
    if pgrep -f "celery.*worker" > /dev/null; then
        echo "⚠️ Celery Worker: Aún ejecutándose"
    else
        echo "❌ Celery Worker: Detenido"
    fi
    
    if pgrep -f "celery.*beat" > /dev/null; then
        echo "⚠️ Celery Beat: Aún ejecutándose"
    else
        echo "❌ Celery Beat: Detenido"
    fi
    
    if lsof -ti:8081 >/dev/null 2>&1; then
        echo "⚠️ Django: Aún ejecutándose en puerto 8081"
    else
        echo "❌ Django: Detenido"
    fi
}

# Ejecutar funciones
cd "$(dirname "$0")"

stop_celery_worker
stop_celery_beat
stop_django
stop_redis

check_services

echo ""
echo "✅ Servicios detenidos!"
echo "🚀 Para reiniciar: ./start_services.sh"