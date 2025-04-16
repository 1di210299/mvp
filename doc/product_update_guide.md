# Guía para actualizar el catálogo de productos

Esta guía explica cómo utilizar el sistema para actualizar el catálogo de productos y la información de la empresa a través de archivos CSV o JSON.

## Características implementadas

- Actualización de productos mediante archivos CSV o JSON
- Carga de información de la empresa
- Seguimiento de cambios con fechas de actualización
- API REST para integración con otros sistemas
- Herramienta de línea de comandos para actualizaciones rápidas

## Formato de archivos

### Información de la empresa (JSON)

```json
{
  "company_name": "Nombre de la Empresa",
  "description": "Descripción de la empresa",
  "contact_email": "contacto@empresa.com",
  "website": "https://www.empresa.com",
  "phone": "+51955743403",
  "last_updated": "2025-04-15T10:00:00"
}
```

### Lista de productos (JSON)

```json
[
  {
    "code": "P001",
    "name": "Nombre del producto",
    "description": "Descripción detallada",
    "price": 29.99,
    "stock": 50,
    "is_active": true,
    "image_url": "https://ejemplo.com/imagen.jpg"
  },
  // Más productos...
]
```

### Lista de productos (CSV)

Debe incluir las siguientes columnas (el orden no importa):

```
code,name,description,price,stock,is_active,image_url
P001,Nombre del producto,Descripción detallada,29.99,50,true,https://ejemplo.com/imagen.jpg
```

## Métodos de actualización

### 1. Interfaz web

Acceda a la sección de administración y utilice el formulario de carga de archivos:

1. Vaya a http://localhost:8000/admin/products
2. Haga clic en "Cargar documentación"
3. Seleccione los archivos a cargar
4. Haga clic en "Procesar"

### 2. Herramienta de línea de comandos

Se ha creado un script de utilidad que permite actualizar productos directamente desde la línea de comandos:

```bash
# Ver opciones disponibles
python scripts/update_products.py --help

# Subir documentación de empresa y productos
python scripts/update_products.py upload --company ruta/archivo_empresa.json --products ruta/productos.json

# Actualizar productos directamente
python scripts/update_products.py update ruta/productos.json

# Verificar productos actualizados recientemente
python scripts/update_products.py check --since 2025-04-10T00:00:00
```

### 3. API REST

Para integración con otros sistemas, utilice los endpoints de la API REST:

- **POST /api/products/upload-documentation**: Carga archivos de documentación
- **POST /api/products/batch-update**: Actualiza múltiples productos
- **GET /api/products/updates**: Obtiene productos actualizados recientemente

## Ejemplos de uso

### Ejemplo 1: Actualización periódica de precios

1. Exporte sus productos actualizados desde su sistema de gestión a un archivo CSV
2. Ejecute el comando:
```bash
python scripts/update_products.py update productos_actualizados.csv
```

### Ejemplo 2: Actualización completa desde su ERP

1. Configure su ERP para exportar productos automáticamente
2. Programe una tarea que ejecute:
```bash
python scripts/update_products.py upload --company informacion_empresa.json --products productos_actualizados.json
```

### Ejemplo 3: Consultar productos modificados recientemente

```bash
python scripts/update_products.py check --since 2025-04-01T00:00:00 --output productos_actualizados.json
```

## Archivos de ejemplo

Se proporcionan archivos de ejemplo en el directorio `static/examples/`:

- `company_info_example.json`: Ejemplo de información de empresa
- `products_example.json`: Ejemplo de lista de productos en formato JSON

## Solución de problemas

Si encuentra errores durante la actualización:

1. Verifique que los archivos tienen el formato correcto (CSV o JSON)
2. Asegúrese de que todos los campos obligatorios estén presentes (code, name, price)
3. Compruebe que los valores numéricos sean válidos
4. Revise los logs para mensajes de error detallados