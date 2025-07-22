# 🚀 Guía Completa: Finalizar tu Flujo N8N

## 📋 Estado Actual de tu Flujo
```
✅ Webhook (recibe datos)
✅ Get Config (obtiene configuraciones del tenant)  
✅ HTTP Request (conecta con tu API)
❌ Decision Logic (falta)
❌ WhatsApp Node (falta)
❌ Email Node (falta)
❌ Success Logging (falta)
```

## 🎯 PASO A PASO: Completar el Flujo

### **PASO 1: Verificar tu HTTP Request actual**

**URL debe ser:**
```
https://c6dd629ae13d.ngrok-free.app/api/auth/tenants/{{$json.tenant_id}}/communication-configs/{{$json.event_type}}/
```

**Headers:**
```json
{
  "Authorization": "Bearer {{$json.tenantJwt}}",
  "Content-Type": "application/json"
}
```

### **PASO 2: Agregar IF Decision Node**

Después de tu HTTP Request, agrega un **IF Node** con:

**Condición:**
```javascript
{{ $json.channel_preference === "whatsapp_only" || $json.channel_preference === "both_whatsapp_primary" || $json.channel_preference === "both_email_primary" }}
```

**True Branch:** Continúa a WhatsApp
**False Branch:** Continúa a Email solo

### **PASO 3: Agregar WhatsApp Business Cloud API Node**

**Tipo:** HTTP Request
**Method:** POST
**URL:** 
```
https://graph.facebook.com/v17.0/{{$('HTTP Request').first().json.whatsapp_phone_id || '119363331321000'}}/messages
```

**Headers:**
```json
{
  "Authorization": "Bearer {{$('HTTP Request').first().json.wa_token}}",
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "messaging_product": "whatsapp",
  "to": "{{$('Webhook').first().json.body.phone || $('Webhook').first().json.body.whatsapp_number}}",
  "type": "text",
  "text": {
    "body": "{{$('HTTP Request').first().json.custom_message_template || 'Hola! Te informamos que tu ' + $('Webhook').first().json.body.event_type + ' ha sido procesado exitosamente.'}}"
  }
}
```

### **PASO 4: Agregar Gmail API Node (paralelo o secuencial)**

**Tipo:** HTTP Request  
**Method:** POST
**URL:**
```
https://gmail.googleapis.com/gmail/v1/users/me/messages/send
```

**Headers:**
```json
{
  "Authorization": "Bearer {{$('HTTP Request').first().json.gsuite_token}}",
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "raw": "{{$base64('From: ' + $('HTTP Request').first().json.email_address + '\nTo: ' + $('Webhook').first().json.body.email + '\nSubject: ' + $('HTTP Request').first().json.event_type_display + '\n\n' + $('HTTP Request').first().json.custom_message_template)}}"
}
```

### **PASO 5: Agregar Success Logging Node**

**Tipo:** HTTP Request
**Method:** POST  
**URL:**
```
https://c6dd629ae13d.ngrok-free.app/api/auth/log-communication/
```

**Headers:**
```json
{
  "Authorization": "Bearer {{$('Webhook').first().json.body.tenantJwt}}",
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "tenant_id": "{{$('HTTP Request').first().json.tenant_id}}",
  "event_type": "{{$('Webhook').first().json.body.event_type}}",
  "event_id": "{{$('Webhook').first().json.body.event_id || $randomString(10)}}",
  "recipient_phone": "{{$('Webhook').first().json.body.phone}}",
  "recipient_email": "{{$('Webhook').first().json.body.email}}",
  "channels_used": ["whatsapp", "email"],
  "status": "success",
  "message_sent": true,
  "execution_time": "{{$now}}",
  "n8n_execution_id": "{{$execution.id}}"
}
```

## 🧪 TESTING DEL FLUJO COMPLETO

### Test Data para el Webhook:
```json
{
  "tenantJwt": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "tenant_id": "f0b2cefd-1814-4d00-90c4-0e40cd283de1",
  "event_type": "order_confirmed",
  "event_id": "order_12345",
  "customer_data": {
    "name": "Juan Pérez",
    "phone": "521234567890",
    "email": "juan@email.com"
  },
  "order_data": {
    "order_id": "12345",
    "total": "$150.00",
    "items": ["Pizza Margherita", "Coca Cola"]
  },
  "callback_url": "https://c6dd629ae13d.ngrok-free.app/api/auth"
}
```

## 🔧 CONFIGURACIONES CRÍTICAS

### En tu Backend Django, asegúrate de tener:

1. **Endpoint para logging:**
```python
# authentication/urls.py
path('log-communication/', views.CommunicationLogView.as_view(), name='log-communication'),
```

2. **Variables de entorno activas:**
```bash
WHATSAPP_ACCESS_TOKEN=tu_token_real
GOOGLE_SERVICE_ACCOUNT_KEY=tu_key_real
NGROK_URL=https://c6dd629ae13d.ngrok-free.app
```

## 🎯 RESULTADO ESPERADO

### Cuando funcione correctamente:
1. ✅ Webhook recibe datos del tenant
2. ✅ Get Config obtiene configuraciones específicas  
3. ✅ Decision node decide qué canales usar
4. ✅ WhatsApp envía mensaje personalizado
5. ✅ Email envía copia/versión diferente
6. ✅ Success log registra la actividad
7. ✅ Tenant puede ver métricas en dashboard

### El tenant podrá:
- Ver mensajes enviados en tiempo real
- Configurar preferencias por tipo de evento  
- Personalizar mensajes con IA
- Monitorear tasas de entrega
- Gestionar múltiples canales desde un panel

## 🚨 SIGUIENTES PASOS INMEDIATOS:

1. **Agrega los nodos faltantes** en este orden
2. **Testa con datos reales** usando tu tenant actual
3. **Configura error handling** para casos fallidos
4. **Implementa retry logic** para reintentos automáticos
5. **Añade conditional routing** para casos especiales

¿Quieres que te ayude a configurar algún nodo específico o tienes dudas sobre alguna parte?
