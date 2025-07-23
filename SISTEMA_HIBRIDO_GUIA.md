# Configuración rápida para pruebas

Para probar el sistema híbrido de detección (Patrones + OpenAI), sigue estos pasos:

## 1. Configura tu API Key de OpenAI (opcional)

Edita el archivo `.env` en la raíz del proyecto:

```bash
# Otras configuraciones...
OPENAI_API_KEY=sk-tu-api-key-aqui
```

## 2. Archivos de prueba

Puedes probar con archivos que tengan estos nombres:

### Para Productos:
- `productos_catalogo.xlsx`
- `inventario_productos.csv`
- `PRODUCTOS STOCK.xlsx` (tu archivo actual)

### Para Ventas:
- `ventas_enero.xlsx`
- `facturas_2025.csv`
- `boletas_comerciales.xlsx`

### Para Clientes:
- `base_clientes.xlsx`
- `contactos_comerciales.csv`

### Para Proveedores:
- `proveedores_activos.xlsx`
- `distribuidores.csv`

## 3. Funcionamiento del sistema híbrido

1. **Sin OpenAI**: Usa solo patrones de nombres de archivos
2. **Con OpenAI**: Combina patrones + análisis inteligente con contexto peruano
3. **Resultado**: El sistema elige la mejor detección o combina ambas

## 4. Ventajas para empresas peruanas

- Reconoce terminología local: "boleta", "factura", "RUC"
- Entiende contexto de negocio peruano
- Maneja tanto nombres en español como inglés
- Fallback automático si OpenAI no está disponible

¡El sistema está listo para probar! 🇵🇪✨
