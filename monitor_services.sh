#!/bin/bash

# Script para monitorear el estado de los servicios de DataLens
# Uso: ./monitor_services.sh

echo "📊 Monitor de Servicios DataLens"
echo "================================="

# Función para verificar Redis
check_redis() {
    echo -n "📡 Redis: "
    if pgrep -f redis-server > /dev/null; then
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Ejecutándose y respondiendo"
        else
            echo "⚠️ Ejecutándose pero no responde"
        fi
    else
        echo "❌ No ejecutándose"
    fi
}

# Función para verificar Celery Worker
check_celery_worker() {
    echo -n "👷 Celery Worker: "
    if pgrep -f "celery.*worker" > /dev/null; then
        # Verificar si está procesando tareas
        worker_status=$(celery -A datalens_backend inspect active 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "✅ Ejecutándose y conectado"
        else
            echo "⚠️ Ejecutándose pero desconectado"
        fi
    else
        echo "❌ No ejecutándose"
    fi
}

# Función para verificar Celery Beat
check_celery_beat() {
    echo -n "⏰ Celery Beat: "
    if pgrep -f "celery.*beat" > /dev/null; then
        if [ -f logs/celery/beat.log ]; then
            last_beat=$(tail -1 logs/celery/beat.log 2>/dev/null | grep "beat:" | wc -l)
            if [ "$last_beat" -gt 0 ]; then
                echo "✅ Ejecutándose y programando tareas"
            else
                echo "⚠️ Ejecutándose pero sin actividad reciente"
            fi
        else
            echo "⚠️ Ejecutándose pero sin log"
        fi
    else
        echo "❌ No ejecutándose"
    fi
}

# Función para verificar Django
check_django() {
    echo -n "🌐 Django: "
    if lsof -ti:8081 >/dev/null 2>&1; then
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/api/ | grep -q "200\|404"; then
            echo "✅ Ejecutándose y respondiendo en puerto 8081"
        else
            echo "⚠️ Puerto ocupado pero no responde correctamente"
        fi
    else
        echo "❌ No ejecutándose en puerto 8081"
    fi
}

# Función para verificar conectividad de tareas
check_task_connectivity() {
    echo ""
    echo "🔗 Verificando conectividad de tareas..."
    
    if pgrep -f redis-server > /dev/null && pgrep -f "celery.*worker" > /dev/null; then
        echo -n "   Probando tarea de prueba: "
        # Intentar ejecutar la tarea de debug
        task_result=$(python -c "
import sys
sys.path.append('.')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
import django
django.setup()
from datalens_backend.celery import debug_task
try:
    result = debug_task.delay()
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
        
        if echo "$task_result" | grep -q "SUCCESS"; then
            echo "✅ Tareas funcionando correctamente"
        else
            echo "❌ Error en las tareas: $task_result"
        fi
    else
        echo "   ⚠️ Redis o Worker no disponibles para prueba"
    fi
}

# Función para mostrar estadísticas
show_stats() {
    echo ""
    echo "📈 Estadísticas:"
    
    if [ -f logs/celery/worker.log ]; then
        total_tasks=$(grep -c "Task.*succeeded" logs/celery/worker.log 2>/dev/null || echo "0")
        failed_tasks=$(grep -c "Task.*failed" logs/celery/worker.log 2>/dev/null || echo "0")
        echo "   📝 Tareas completadas: $total_tasks"
        echo "   ❌ Tareas fallidas: $failed_tasks"
    fi
    
    if [ -f logs/django.log ]; then
        recent_requests=$(tail -100 logs/django.log 2>/dev/null | grep -c "HTTP" || echo "0")
        echo "   🌐 Requests recientes (últimas 100 líneas): $recent_requests"
    fi
}

# Función para mostrar recursos
show_resources() {
    echo ""
    echo "💻 Uso de recursos:"
    
    # Memoria de Redis
    if pgrep -f redis-server > /dev/null; then
        redis_pid=$(pgrep -f redis-server)
        redis_mem=$(ps -o rss= -p $redis_pid 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')
        echo "   📡 Redis: $redis_mem"
    fi
    
    # Memoria de Celery Worker
    if pgrep -f "celery.*worker" > /dev/null; then
        celery_pid=$(pgrep -f "celery.*worker")
        celery_mem=$(ps -o rss= -p $celery_pid 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')
        echo "   👷 Celery Worker: $celery_mem"
    fi
    
    # Memoria de Django
    if lsof -ti:8081 >/dev/null 2>&1; then
        django_pid=$(lsof -ti:8081)
        django_mem=$(ps -o rss= -p $django_pid 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')
        echo "   🌐 Django: $django_mem"
    fi
}

# Ejecutar todas las verificaciones
check_redis
check_celery_worker
check_celery_beat
check_django
check_task_connectivity
show_stats
show_resources

echo ""
echo "🔄 Para actualizar: ./monitor_services.sh"
echo "🚀 Para reiniciar servicios: ./start_services.sh"
echo "🛑 Para detener servicios: ./stop_services.sh"