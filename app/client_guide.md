# Guía de Uso: Verificador de Conexión de WhatsApp

## Verificar el estado de WhatsApp

### Usando el navegador:

1. Visita la siguiente URL en tu navegador:
   ```
   http://tu-servidor:8000/api/whatsapp/status
   ```

2. Verás una respuesta JSON con la siguiente información:
   ```json
   {
     "whatsapp_status": "connected", 
     "last_active": "2023-05-15T14:30:22.123456",
     "details": "Cuenta Twilio activa: Tu Nombre de Cuenta"
   }
   ```

### Usando curl desde la terminal:

```bash
curl http://tu-servidor:8000/api/whatsapp/status
```

### Usando el endpoint de health check:

```bash
curl http://tu-servidor:8000/health
```

## Interpretación de resultados:

- **status: "connected"** - La conexión de WhatsApp está activa
- **status: "inactive"** - La cuenta de Twilio está inactiva
- **status: "not_configured"** - Faltan las credenciales de Twilio
- **status: "error"** - Hubo un error al verificar la conexión
- **last_active** - Fecha/hora de la última actividad registrada
- **last_message_received** - Fecha/hora del último mensaje recibido
- **last_message_sent** - Fecha/hora del último mensaje enviado

## Solución de problemas:

Si el estado muestra "error" o "inactive":

1. Verifica que las credenciales de Twilio estén correctamente configuradas
2. Asegúrate de que tu cuenta de Twilio esté activa
3. Revisa los logs en `/logs/app.log` para más detalles sobre posibles errores
