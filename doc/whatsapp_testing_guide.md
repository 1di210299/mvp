# Guía de Pruebas para la Integración de WhatsApp

Esta guía te ayudará a probar el funcionamiento completo de la integración de WhatsApp con tu aplicación.

## Requisitos Previos

1. Tener la aplicación funcionando localmente
2. Tener ngrok iniciado para exponer la aplicación a Internet
3. Tener una cuenta de Twilio configurada con el sandbox de WhatsApp
4. Un teléfono móvil con WhatsApp instalado

## Proceso de Prueba

### 1. Preparación del Entorno

1. Inicia tu aplicación:
   ```bash
   cd /Users/juandiegogutierrezcortez/mvp
   python -m uvicorn app.main:app --reload
   ```

2. En otra terminal, inicia ngrok:
   ```bash
   ngrok http 8000
   ```

3. Copia la URL de ngrok (https://xxxx-xxxx-xxxx-xxxx.ngrok-free.app)

4. Accede a la consola de Twilio y verifica que la URL del webhook coincide con tu URL de ngrok actual:
   - URL del webhook debe ser: https://xxxx-xxxx-xxxx-xxxx.ngrok-free.app/api/webhooks/twilio

### 2. Activación del Sandbox

1. Desde tu teléfono, envía el mensaje "join move-weather" (o el código de tu sandbox) al número +14155238886
2. Deberías recibir un mensaje de confirmación del sandbox

### 3. Pruebas Básicas

1. Accede a la página de diagnóstico:
   ```
   https://xxxx-xxxx-xxxx-xxxx.ngrok-free.app/help/whatsapp
   ```

2. Realiza las pruebas en el siguiente orden:
   - Verificar Estado General
   - Verificar Configuración de Webhooks
   - Verificar Estado de tu Número
   - Enviar Mensaje de Prueba

### 4. Pruebas de Flujo Completo

1. Envía un mensaje de texto simple desde tu teléfono al número del sandbox
2. Verifica en los logs de la aplicación si se recibe correctamente:
   ```
   2025-04-14 16:XX:XX,XXX [INFO] app.main: REQUEST: POST /api/webhooks/twilio
   ```

3. Comprueba si recibes una respuesta automática en tu teléfono

### 5. Diagnóstico de Problemas

Si no recibes respuestas a tus mensajes, verifica lo siguiente:

1. **Webhook mal configurado**: 
   - Usa la herramienta "Verificar Configuración de Webhooks" en la página de ayuda
   - Asegúrate que la URL en Twilio coincide exactamente con: https://xxxx-xxxx-xxxx-xxxx.ngrok-free.app/api/webhooks/twilio

2. **Sesión expirada**:
   - Las sesiones del sandbox expiran después de 72 horas
   - Envía nuevamente "join move-weather" al número del sandbox

3. **Problemas de ngrok**:
   - Cada vez que reinicies ngrok, obtendrás una nueva URL
   - Actualiza la URL del webhook en Twilio cada vez que reinicies ngrok

4. **Verificación de logs**:
   - Revisa los logs en la terminal donde está corriendo la aplicación
   - Busca errores relacionados con Twilio o problemas de procesamiento de mensajes

### 6. Solucionar Problemas de Bloqueo de Números

Si recibes el mensaje "Lo sentimos, este número ha sido bloqueado por motivos de seguridad" cuando intentas interactuar con el bot, sigue estos pasos:

1. **Verificar si tu número está en la lista de bloqueados**:
   ```bash
   curl -X GET "http://localhost:8000/api/security/blocked_numbers"
   ```

2. **Desbloquear tu número**:
   ```bash
   curl -X POST "http://localhost:8000/api/security/unblock_number" \
     -H "Content-Type: application/json" \
     -d '{"phone_number":"+TU_NUMERO", "reason":"Mi número personal"}'
   ```

3. **Ajustar la configuración de seguridad**:
   Si sigues experimentando bloqueos, puedes ajustar los parámetros de seguridad:
   ```bash
   curl -X POST "http://localhost:8000/api/security/update_security_config" \
     -H "Content-Type: application/json" \
     -d '{"enable_auto_blocking": false, "threat_score_threshold": 0.9}'
   ```

4. **Añadir tu número a la whitelist**:
   También puedes añadir tu número a la whitelist en el archivo `.env`:
   ```
   WHITELISTED_NUMBERS="+TU_NUMERO,+OTRO_NUMERO"
   ```

5. **Reiniciar la aplicación**:
   Después de hacer cambios en la configuración, reinicia la aplicación para que surtan efecto.

## Consejos Adicionales

- El WhatsApp Sandbox es solo para pruebas y tiene limitaciones
- Para un entorno de producción, necesitarás solicitar acceso a la API oficial de WhatsApp Business
- Twilio proporciona un panel de control donde puedes ver todos los mensajes enviados y recibidos
- La URL de ngrok es temporal y cambia cada vez que reinicies ngrok (a menos que tengas una cuenta de pago)
