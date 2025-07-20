# 📋 DOCUMENTACIÓN DE ESTRUCTURA DE URLs - INVENTORY

## 🎯 **OBJETIVO**
Mantener una estructura organizada y clara de URLs para evitar confusiones futuras.

## 📁 **ESTRUCTURA REAL (Como funciona Django)**

```
inventory/
├── urls_backup.py             # � Backup del archivo anterior
└── urls/
    ├── __init__.py           # � PUNTO DE ENTRADA PRINCIPAL (Django lo carga automáticamente)
    ├── api_urls.py           # 🚀 ViewSets del router principal
    ├── dashboard_urls.py     # 📊 APIs de dashboard
    ├── whatsapp_urls.py      # 📱 Webhooks y APIs de WhatsApp
    ├── email_tracking_urls.py # 📧 APIs de tracking de emails
    ├── gmail_webhook_urls.py # 🔗 Webhooks de Gmail
    └── pdf_automation_urls.py # 📄 APIs de análisis de PDFs
```

## 🔗 **FLUJO DE CARGA (Como funciona realmente)**

1. **Django busca:** `inventory.urls` 
2. **Encuentra directorio:** `inventory/urls/` 
3. **Carga automáticamente:** `inventory/urls/__init__.py` 
4. **Resultado:** URLs organizadas por funcionalidad

## 📝 **RESPONSABILIDADES**

### 🔥 `inventory/urls/__init__.py` (Principal - REAL)

- **PUNTO DE ENTRADA ÚNICO** (Django lo carga automáticamente)
- Rutas individuales específicas
- Inclusión de módulos especializados
- Orden correcto de URLs
- Punto de entrada único
- Rutas individuales específicas
- Inclusión de módulos especializados
- Orden correcto de URLs

### 🚀 `inventory/urls/api_urls.py`
- Todos los ViewSets del router principal
- CategoryViewSet, ProductViewSet, etc.
- PurchaseOrderViewSet y relacionados
- PurchaseOrderTestViewSet (AI + WhatsApp)

### 📊 `inventory/urls/dashboard_urls.py`
- APIs específicas de dashboard
- Métricas y estadísticas
- Reportes especializados

### 📱 `inventory/urls/whatsapp_urls.py`
- Webhooks de WhatsApp
- Procesamiento de mensajes
- Análisis con IA

### 📧 `inventory/urls/email_tracking_urls.py`
- Tracking de emails enviados
- Webhooks de respuestas
- Análisis de engagement

## ⚠️ **REGLAS IMPORTANTES**

1. **SIEMPRE** agregar nuevos ViewSets en `api_urls.py`
2. **NUNCA** modificar `urls/__init__.py` (está vacío intencionalmente)
3. **ORGANIZAR** URLs especializadas en archivos separados
4. **MANTENER** el orden: rutas específicas → includes → router
5. **DOCUMENTAR** cambios en este archivo

## 🔧 **PARA AGREGAR NUEVOS VIEWSETS**

```python
# En inventory/urls/api_urls.py
from ..views.nuevo_views import NuevoViewSet

# Registrar en el router
router.register(r'nuevo-endpoint', NuevoViewSet, basename='nuevo-endpoint')
```

## 🔧 **PARA AGREGAR NUEVOS MÓDULOS**

1. Crear archivo: `inventory/urls/nuevo_modulo_urls.py`
2. Agregar include en `inventory/urls.py`:
   ```python
   path('nuevo-modulo/', include('inventory.urls.nuevo_modulo_urls')),
   ```

## 📋 **VIEWSETS ACTUALES EN API_URLS.PY**

- ✅ categories
- ✅ suppliers  
- ✅ products
- ✅ sales
- ✅ alerts
- ✅ inventory-history
- ✅ transactions
- ✅ customers
- ✅ leads
- ✅ locations
- ✅ inventory-items
- ✅ opportunities
- ✅ purchase-orders
- ✅ purchase-order-tracking
- ✅ purchase-order-emails
- ✅ purchase-orders-ai-test (🤖 AI + WhatsApp)

---
**Última actualización:** 2025-07-20  
**Versión:** 1.0  
**Responsable:** Sistema de organización de URLs
