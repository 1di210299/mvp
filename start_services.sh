#!/bin/bash

# Script para iniciar todos los servicios de DataLens de forma escalable
# Uso: ./start_services.sh

echo "🚀 Iniciando servicios de DataLens..."

# Activar entorno virtual
source .venv/bin/activate

# Crear directorios de logs si no existen
mkdir -p logs/celery

# Función para verificar si un puerto está en uso
check_port() {
    lsof -ti:$1 >/dev/null 2>&1
}

# Función para iniciar Redis
start_redis() {
    echo "📡 Iniciando Redis..."
    if ! pgrep -f redis-server > /dev/null; then
        redis-server --daemonize yes
        sleep 2
        if pgrep -f redis-server > /dev/null; then
            echo "✅ Redis iniciado correctamente"
        else
            echo "❌ Error al iniciar Redis"
            exit 1
        fi
    else
        echo "✅ Redis ya está ejecutándose"
    fi
}

# Función para iniciar Celery Worker
start_celery_worker() {
    echo "👷 Iniciando Celery Worker..."
    if ! pgrep -f "celery.*worker" > /dev/null; then
        nohup python -m celery -A datalens_backend worker \
            --loglevel=info \
            --concurrency=4 \
            --logfile=logs/celery/worker.log \
            --pidfile=logs/celery/worker.pid > /dev/null 2>&1 &
        sleep 3
        if pgrep -f "celery.*worker" > /dev/null; then
            echo "✅ Celery Worker iniciado correctamente"
        else
            echo "❌ Error al iniciar Celery Worker"
        fi
    else
        echo "✅ Celery Worker ya está ejecutándose"
    fi
}

# Función para iniciar Celery Beat (tareas programadas)
start_celery_beat() {
    echo "⏰ Iniciando Celery Beat..."
    if ! pgrep -f "celery.*beat" > /dev/null; then
        nohup python -m celery -A datalens_backend beat \
            --loglevel=info \
            --logfile=logs/celery/beat.log \
            --pidfile=logs/celery/beat.pid > /dev/null 2>&1 &
        sleep 3
        if pgrep -f "celery.*beat" > /dev/null; then
            echo "✅ Celery Beat iniciado correctamente"
        else
            echo "❌ Error al iniciar Celery Beat"
        fi
    else
        echo "✅ Celery Beat ya está ejecutándose"
    fi
}

# Función para iniciar Django
start_django() {
    echo "🌐 Iniciando servidor Django..."
    if ! check_port 8081; then
        nohup python manage.py runserver 0.0.0.0:8081 > logs/django.log 2>&1 &
        sleep 3
        if check_port 8081; then
            echo "✅ Servidor Django iniciado en puerto 8081"
        else
            echo "❌ Error al iniciar servidor Django"
        fi
    else
        echo "✅ Servidor Django ya está ejecutándose en puerto 8081"
    fi
}

# Función para verificar el estado de los servicios
check_services() {
    echo ""
    echo "📊 Estado de los servicios:"
    
    if pgrep -f redis-server > /dev/null; then
        echo "✅ Redis: Ejecutándose"
    else
        echo "❌ Redis: No ejecutándose"
    fi
    
    if pgrep -f "celery.*worker" > /dev/null; then
        echo "✅ Celery Worker: Ejecutándose"
    else
        echo "❌ Celery Worker: No ejecutándose"
    fi
    
    if pgrep -f "celery.*beat" > /dev/null; then
        echo "✅ Celery Beat: Ejecutándose"
    else
        echo "❌ Celery Beat: No ejecutándose"
    fi
    
    if check_port 8081; then
        echo "✅ Django: Ejecutándose en puerto 8081"
    else
        echo "❌ Django: No ejecutándose"
    fi
}

# Ejecutar funciones
cd "$(dirname "$0")"

start_redis
start_celery_worker
start_celery_beat
start_django

check_services

echo ""
echo "🎉 Todos los servicios han sido iniciados!"
echo "📝 Logs disponibles en:"
echo "   - Django: logs/django.log"
echo "   - Celery Worker: logs/celery/worker.log"
echo "   - Celery Beat: logs/celery/beat.log"
echo ""
echo "🔗 URLs:"
echo "   - API Backend: http://localhost:8081"
echo "   - Admin Django: http://localhost:8081/admin"
echo "   - API Docs: http://localhost:8081/api/schema/swagger-ui/"
echo ""
echo "⏹️  Para detener todos los servicios: ./stop_services.sh"