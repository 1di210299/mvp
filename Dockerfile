# Dockerfile optimizado para el sistema de ventas por WhatsApp
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.4.2

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Copiar archivos de configuración de dependencias
COPY pyproject.toml poetry.lock* /app/

# Instalar dependencias
RUN poetry install --no-dev --no-interaction --no-ansi

# Copiar el resto del código
COPY . /app/

# Scripts de entrada
COPY scripts/entrypoint.sh scripts/wait-for-it.sh /app/
RUN chmod +x /app/scripts/entrypoint.sh /app/scripts/wait-for-it.sh

# Puerto donde se expone la aplicación
EXPOSE 8000

# Comando por defecto para ejecutar la aplicación
CMD ["/app/scripts/entrypoint.sh"]