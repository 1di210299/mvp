# N8N Workflow Completo - Comunicaciones Multi-Canal

## 🎯 Flujo Actual vs Flujo Completo

### Tu Flujo Actual:
```
Webhook → Get Config → HTTP Request
```

### Flujo Completo Recomendado:
```
Webhook → Get Config → IF Decision → [WhatsApp Node] + [Email Node] → Log Success
```

## 🔧 Configuraciones de Nodos Faltantes:

### 1. 🤔 **IF Decision Node** (después de HTTP Request)
```javascript
// Condición para decidir canal
{{ $json.channel_preference === "whatsapp_only" || $json.channel_preference === "both_whatsapp_primary" }}
```

### 2. 📱 **WhatsApp Business Cloud API Node**
```json
{
  "method": "POST",
  "url": "https://graph.facebook.com/v17.0/{{$('Get Config').first().json.whatsapp_phone_id}}/messages",
  "headers": {
    "Authorization": "Bearer {{$('Get Config').first().json.wa_token}}",
    "Content-Type": "application/json"
  },
  "body": {
    "messaging_product": "whatsapp",
    "to": "{{$('Webhook').first().json.body.phone}}",
    "type": "text",
    "text": {
      "body": "{{$('Get Config').first().json.custom_message_template || 'Mensaje por defecto'}}"
    }
  }
}
```

### 3. 📧 **Gmail API Node**
```json
{
  "method": "POST",
  "url": "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
  "headers": {
    "Authorization": "Bearer {{$('Get Config').first().json.gsuite_token}}",
    "Content-Type": "application/json"
  },
  "body": {
    "raw": "{{$base64(
      'From: ' + $('Get Config').first().json.email_address + '\n' +
      'To: ' + $('Webhook').first().json.body.email + '\n' +
      'Subject: ' + $('Get Config').first().json.event_type_display + '\n\n' +
      $('Get Config').first().json.custom_message_template
    )}}"
  }
}
```

### 4. 📊 **Log Success Node** (HTTP Request final)
```json
{
  "method": "POST",
  "url": "{{$('Webhook').first().json.body.callback_url}}/log",
  "headers": {
    "Authorization": "Bearer {{$('Webhook').first().json.body.tenantJwt}}",
    "Content-Type": "application/json"
  },
  "body": {
    "event_id": "{{$('Webhook').first().json.body.event_id}}",
    "tenant_id": "{{$('Get Config').first().json.tenant_id}}",
    "channels_used": ["whatsapp", "email"],
    "status": "success",
    "timestamp": "{{$now}}"
  }
}
```

## 🚀 Próximos Pasos Inmediatos:

1. **Agregar IF Node** después de tu HTTP Request actual
2. **Configurar WhatsApp Node** con credenciales dinámicas
3. **Configurar Email Node** con Gmail API
4. **Agregar Logging Node** para métricas
5. **Configurar Error Handling** para reintentos

## 🔑 Variables Críticas a Configurar:

### En el Header Authorization del HTTP Request:
```
Bearer {{$('Webhook').first().json.body.tenantJwt}}
```

### Para acceder a configuraciones:
```javascript
// Token WhatsApp
{{$('Get Config').first().json.wa_token}}

// Email del tenant
{{$('Get Config').first().json.email_address}}

// Preferencia de canal
{{$('Get Config').first().json.channel_preference}}

// Usar IA
{{$('Get Config').first().json.use_ai_personalization}}
```

## 🎯 Testing del Flujo Completo:

1. **Test Webhook** con datos reales
2. **Verificar Get Config** retorna configuraciones
3. **Test WhatsApp** con número real
4. **Test Email** con Gmail configurado
5. **Verificar Logs** en backend Django

¿Quieres que te ayude a configurar alguno de estos nodos específicos?
