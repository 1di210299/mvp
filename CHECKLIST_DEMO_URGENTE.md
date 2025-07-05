# ⚡ CHECKLIST URGENTE - DEMO PARA SOCIO

## 🎯 **OBJETIVO**: Tener demo funcional en 24-48 horas

---

## ✅ **LO QUE YA FUNCIONA (NO TOCAR)**

- ✅ Backend Django completamente operativo
- ✅ Base de datos con productos reales peruanos
- ✅ Sistema campos personalizados implementado y funcionando
- ✅ API REST completa con endpoints de IA
- ✅ Scripts de demo (`demo_custom_fields.py`, `demo_ecommerce.py`)
- ✅ Documentación técnica completa

---

## 🚨 **ARREGLAR URGENTE (Para demo básico)**

### **1. FRONTEND REACT - PRIORIDAD MÁXIMA**

#### A. Instalar dependencias faltantes
```bash
cd datalens_frontend
npm install
# Si hay errores, verificar package.json
```

#### B. Conectar con backend
- ✅ Verificar URLs de API en `services/api.ts`
- ✅ Configurar CORS en Django para puerto 3000
- ✅ Ajustar endpoints para nueva estructura

#### C. Páginas críticas para demo
- ✅ **Login page**: Entrada al sistema
- ✅ **Dashboard**: Vista general con gráficos
- ✅ **Products page**: CRUD con campos personalizados
- ✅ **Custom Fields page**: Gestión de campos nuevos

### **2. CONFIGURACIÓN BÁSICA**

#### A. Variables de entorno
```bash
# Backend
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Frontend  
REACT_APP_API_URL=http://localhost:8000/api
```

#### B. Base de datos con datos demo
```bash
python manage.py migrate
python demo_custom_fields.py  # Poblar con datos
```

### **3. SCRIPTS DE INICIO AUTOMÁTICO**

#### Crear `start_demo.bat`:
```bash
@echo off
echo "🚀 Iniciando DataLens Demo..."
start "Backend" cmd /k "cd /d C:\...\mvp && python manage.py runserver"
timeout /t 5
start "Frontend" cmd /k "cd /d C:\...\mvp\datalens_frontend && npm start"
echo "✅ Demo listo en http://localhost:3000"
pause
```

---

## 📋 **ARREGLAR DESPUÉS (Para MVP completo)**

### **4. UI/UX PROFESIONAL**
- ⏳ Tema visual consistente
- ⏳ Loading states y spinners  
- ⏳ Manejo de errores elegante
- ⏳ Responsive design
- ⏳ Animaciones suaves

### **5. FUNCIONALIDADES AVANZADAS**
- ⏳ Conectar endpoints de IA real
- ⏳ Dashboard con insights automáticos
- ⏳ Reportes y gráficos avanzados
- ⏳ Exportación de datos

### **6. DEPLOYMENT PROFESIONAL**
- ⏳ Docker containers
- ⏳ Variables de entorno seguras
- ⏳ Base de datos PostgreSQL
- ⏳ Hosting en cloud (DigitalOcean/AWS)

---

## 🎬 **GUION DE DEMO (15 minutos)**

### **PREPARACIÓN PRE-DEMO**
```bash
1. Tener ambos servidores corriendo
2. Datos de demo cargados
3. Navegador listo en localhost:3000
4. Backend funcionando en localhost:8000
5. Documentos de propuesta impresos
```

### **SCRIPT DE PRESENTACIÓN**

#### **MINUTO 1-2: Problema**
> "Mira, todos los ecommerce tienen el mismo problema: sus sistemas de inventario son muy básicos. No pueden agregar información específica de su negocio..."

#### **MINUTO 3-7: Solución (Demo live)**
> "DataLens resuelve esto con campos personalizados. Mira..."
- Mostrar productos básicos
- Agregar campos ecommerce (tallas, colores, rating, etc.)
- Demostrar cómo se adapta a cada negocio

#### **MINUTO 8-11: IA en acción**
> "Pero lo que nos diferencia es la inteligencia artificial..."
- Ejecutar `python demo_ecommerce.py` 
- Mostrar insights automáticos
- Explicar predicciones y recomendaciones

#### **MINUTO 12-14: Oportunidad**
> "El mercado está listo. 10,000+ ecommerce en Perú necesitan esto..."
- Mostrar análisis de mercado
- Explicar modelo de negocio
- Presentar proyecciones financieras

#### **MINUTO 15: Call to action**
> "¿Qué te parece? ¿Te sumas para transformar este mercado?"

---

## ⏰ **TIMELINE RECOMENDADO**

### **HOY (4-6 horas)**
- ✅ Arreglar frontend básico
- ✅ Verificar conexión backend-frontend  
- ✅ Probar flujo completo
- ✅ Preparar datos de demo

### **MAÑANA (2-3 horas)**
- ✅ Pulir documentos de propuesta
- ✅ Preparar presentación
- ✅ Practicar demo
- ✅ Agendar reunión con socio

### **PASADO MAÑANA**
- 🎯 **DEMO CON SOCIO**

---

## 🎯 **CRITERIO DE ÉXITO**

### **DEMO EXITOSO SI:**
- ✅ Frontend carga sin errores
- ✅ Puede crear/editar productos  
- ✅ Campos personalizados funcionan
- ✅ Dashboard muestra gráficos básicos
- ✅ Backend responde a todas las consultas

### **NO ES NECESARIO PARA DEMO:**
- ❌ UI súper pulida
- ❌ Todas las funcionalidades
- ❌ IA conectada en vivo
- ❌ Deploy en producción

**OBJETIVO**: Mostrar el POTENCIAL, no el producto terminado.

---

## 🚀 **ACCIÓN INMEDIATA**

¿Empezamos con el frontend ahora mismo?

1. **Revisar errores en datalens_frontend**
2. **Conectar con API backend** 
3. **Hacer funcionar páginas básicas**
4. **Preparar demo para mañana**

**¿Cuál atacamos primero?**
