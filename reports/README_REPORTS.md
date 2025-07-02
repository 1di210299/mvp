# Sistema de Reportes DataLens

## Características Implementadas

- ✅ Generación de PDFs con ReportLab
- ✅ Exportación a CSV/Excel utilizando pandas y openpyxl
- ✅ Reportes programados con Celery
- ✅ Distribución automática por email

## Tipos de Reportes

El sistema soporta varios tipos de reportes predefinidos:

1. **Resumen de Inventario**: Estado actual del inventario con estadísticas clave
2. **Movimiento de Stock**: Histórico de transacciones de entrada y salida
3. **Análisis ABC**: Clasificación de productos por valor o movimiento
4. **Análisis de Rotación**: Métricas de rotación de inventario
5. **Precisión de Pronósticos**: Comparación entre demanda pronosticada y real
6. **Resumen de Alertas**: Historial de alertas generadas
7. **Rendimiento de Proveedores**: Métricas de rendimiento de proveedores
8. **Rendimiento de Productos**: Análisis de rendimiento por producto
9. **Análisis de Costos**: Información sobre costos de inventario

## Formatos Disponibles

- PDF
- Excel
- CSV
- JSON

## Frecuencia de Programación

- Bajo demanda
- Diario
- Semanal
- Mensual
- Trimestral

## Guía de Uso

### 1. Creación de Plantillas

Para crear una nueva plantilla de reporte:

```
POST /api/reports/templates/
{
    "name": "Reporte de Inventario Diario",
    "description": "Resumen diario del estado del inventario",
    "report_type": "inventory_summary",
    "default_format": "pdf",
    "frequency": "daily",
    "auto_send": true,
    "recipients": [1, 2],  // IDs de usuarios
    "additional_emails": "externo@ejemplo.com,otro@ejemplo.com"
}
```

### 2. Generación Manual de Reportes

Para generar un reporte manualmente:

```
POST /api/reports/generate/
{
    "template_id": 1,
    "date_from": "2025-06-01",
    "date_to": "2025-06-30",
    "format": "pdf",
    "filters": {
        "category": "Productos A",
        "location": "Almacén Central"
    },
    "send_email": false
}
```

### 3. Programación de Reportes

Para programar un reporte:

```
POST /api/reports/schedules/
{
    "template": 1,
    "name": "Reporte Semanal",
    "schedule_type": "weekly",
    "hour": 8,
    "minute": 0,
    "day_of_week": 1  // 0=Lunes, 6=Domingo
}
```

### 4. Exportación de Datos

Para exportar datos en diferentes formatos:

```
POST /api/reports/export/
{
    "data_type": "products",
    "format": "excel",
    "date_from": "2025-06-01",
    "date_to": "2025-06-30",
    "filters": {
        "category": "Productos A",
        "active_only": true
    }
}
```

## Requisitos

- Python 3.10+
- Django 4.2+
- ReportLab 4.0+
- WeasyPrint 60.2+
- openpyxl 3.1+
- XlsxWriter 3.1+
- pandas 2.1+
- Celery 5.3+

## Instalación

1. Instalar dependencias:

```
pip install -r requirements.txt
```

2. Ejecutar migraciones:

```
python manage.py migrate
```

3. Configurar Celery para reportes programados:

```python
# En settings.py
CELERY_BEAT_SCHEDULE = {
    'process-scheduled-reports': {
        'task': 'reports.services.scheduled_reports.process_scheduled_reports',
        'schedule': crontab(minute='*/10'),  # Cada 10 minutos
    },
    'cleanup-expired-reports': {
        'task': 'reports.services.scheduled_reports.cleanup_expired_reports',
        'schedule': crontab(hour=2, minute=0),  # Diariamente a las 2 AM
    },
}
```
