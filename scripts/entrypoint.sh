#!/bin/bash
set -e

# Script de entrada para la aplicación Docker

# Esperar a que la base de datos esté disponible si se usa una base de datos externa
if [ ! -z "$DATABASE_URL" ] && [[ "$DATABASE_URL" != sqlite* ]]; then
    echo "Esperando a que la base de datos esté disponible..."
    
    # Extraer host y puerto de DATABASE_URL
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    
    if [ -z "$DB_PORT" ]; then
        if [[ "$DATABASE_URL" == postgres* ]]; then
            DB_PORT=5432
        elif [[ "$DATABASE_URL" == mysql* ]]; then
            DB_PORT=3306
        fi
    fi
    
    if [ ! -z "$DB_HOST" ] && [ ! -z "$DB_PORT" ]; then
        echo "Esperando a $DB_HOST:$DB_PORT..."
        ./scripts/wait-for-it.sh "$DB_HOST:$DB_PORT" -t 60
        echo "Base de datos disponible."
    fi
fi

# Ejecutar migraciones si existen
if [ -d "/app/alembic" ]; then
    echo "Ejecutando migraciones de base de datos..."
    alembic upgrade head
    echo "Migraciones completadas."
fi

# Determinar el comando a ejecutar según el rol
if [ "$APP_ROLE" = "admin" ]; then
    echo "Iniciando panel de administración..."
    exec streamlit run admin/app.py
elif [ "$APP_ROLE" = "worker" ]; then
    echo "Iniciando worker..."
    exec python -m app.worker
else
    # Por defecto, iniciar la aplicación web
    echo "Iniciando aplicación web..."
    
    if [ "$APP_ENV" = "development" ]; then
        exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    else
        exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-4}
    fi
fi