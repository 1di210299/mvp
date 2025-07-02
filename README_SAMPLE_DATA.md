# Generador de Datos de Prueba - Productos Peruanos

Este conjunto de scripts genera datos de prueba realistas para el sistema DataLens, utilizando productos típicos peruanos.

## Contenido Generado

### 1. Empresa de Prueba
- **Distribuidora Lima SAC** (RUC: 20123456789)
- Datos completos de contacto y configuración premium

### 2. Categorías de Productos
- **Alimentos y Bebidas**
  - Granos y Cereales
  - Condimentos y Especias
  - Conservas
  - Bebidas
  - Lácteos
  - Carnes y Embutidos
- **Textiles**
  - Algodón Pima
  - Alpaca
  - Prendas Tradicionales
  - Accesorios
- **Artesanías**
  - Cerámica
  - Textiles Artesanales
  - Joyería
  - Decoración
- **Productos Naturales**
  - Hierbas Medicinales
  - Superalimentos
  - Cosméticos Naturales

### 3. Proveedores Peruanos
- Agroexportadora Los Andes SAC (Lima)
- Textiles Cusco EIRL (Cusco)
- Cooperativa Agraria Café del Norte (Cajamarca)
- Artesanías Shipibo SAC (Ucayali)
- Superfoods Perú Export SAC (Lima)

### 4. Productos Típicos (16 productos)
- **Superalimentos**: Quinua, Kiwicha, Maca, Camu Camu, Lúcuma
- **Condimentos**: Ají amarillo, Ají panca
- **Textiles**: Ponchos y bufandas de alpaca, camisetas Pima
- **Artesanías**: Cerámica Shipibo, tapices ayacuchanos
- **Otros**: Café orgánico, espárragos, aceitunas

### 5. Ubicaciones de Almacén
- Recepción
- Alimentos Secos
- Refrigerados
- Textiles
- Artesanías
- Expedición

### 6. Inventario Inicial
- Stock inicial aleatorio para cada producto
- Control de lotes para productos perecederos
- Fechas de vencimiento automáticas
- Valor total aproximado: S/ 50,000-80,000

## Formas de Ejecutar

### Opción 1: Script Directo
```bash
# Desde el directorio del proyecto
python manage.py shell < generate_sample_data.py
```

### Opción 2: Comando de Django
```bash
# Generar datos
python manage.py generate_sample_data

# Limpiar y generar datos nuevos
python manage.py generate_sample_data --clean
```

### Opción 3: Shell de Django
```bash
python manage.py shell
>>> exec(open('generate_sample_data.py').read())
```

## Limpiar Datos

Para eliminar todos los datos generados:
```bash
python manage.py shell < clean_sample_data.py
```

## Características Especiales

### Control de Lotes
Los productos perecederos incluyen:
- Números de lote automáticos
- Fechas de fabricación
- Fechas de vencimiento basadas en vida útil

### Productos con Vencimiento
- Quinua: 2 años
- Maca: 3 años
- Ají amarillo: 1 año
- Café: 2 años
- Conservas: 3 años

### Precios Realistas
- Precios en soles peruanos
- Margen de ganancia del 50%
- Basados en precios reales del mercado

### Stock Inteligente
- Stock inicial entre mínimo y máximo
- Puntos de reorden configurados
- Ubicaciones apropiadas por tipo de producto

## Estructura de Datos

Los datos generados incluyen todas las relaciones necesarias:
- Empresa → Categorías, Proveedores, Ubicaciones, Productos
- Productos → Categoría, Proveedor
- Inventario → Producto, Ubicación

## Notas Importantes

1. **Transacciones**: Todos los datos se crean dentro de transacciones para mantener consistencia
2. **Duplicados**: El script maneja duplicados automáticamente usando `get_or_create()`
3. **Códigos de Barras**: Se generan códigos de barras simulados automáticamente
4. **RUCs**: Los RUCs de proveedores son ficticios pero tienen formato válido

## Extensión

Para agregar más productos, edita la lista `products_data` en `generate_sample_data.py` con:
- SKU único
- Nombre y descripción
- Categoría y proveedor existentes
- Precios y configuración de stock
- Configuración de lotes y vencimiento

## Troubleshooting

Si encuentras errores:

1. **Error de importación**: Asegúrate de estar en el directorio correcto del proyecto
2. **Error de base de datos**: Verifica que las migraciones estén aplicadas
3. **Error de permisos**: Ejecuta desde un entorno virtual con Django instalado

```bash
# Verificar instalación
python manage.py check

# Aplicar migraciones si es necesario
python manage.py migrate
```
