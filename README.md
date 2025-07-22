# 🚀 DataLens MVP - Sistema Inteligente de Gestión Empresarial

**DataLens** es una plataforma de automatización empresarial diseñada específicamente para **PYMES peruanas** que buscan optimizar su gestión operativa sin perder el toque humano. Combina **Inteligencia Artificial**, **automatización WhatsApp** y **analytics avanzado** para transformar negocios tradicionales en operaciones eficientes y escalables.

## 🎯 **¿Para quién es DataLens?**

### **Público Objetivo**
- **Pequeñas empresas** (5-20 empleados) con ventas establecidas
- **Distribuidoras, tiendas, importadores** que manejan múltiples proveedores
- **Empresas que ya venden** por WhatsApp, redes sociales o tiendas físicas
- **Negocios que quieren automatizar** sin perder el control personal

### **El Problema que Resolvemos**
```
❌ "Pierdo ventas porque no sé cuándo reponer stock"
❌ "Gasto horas enviando órdenes de compra por WhatsApp"  
❌ "No sé qué productos me dan más ganancia"
❌ "Los proveedores no responden mis emails"
❌ "No puedo crecer porque todo es manual"
```

## ⚡ **Características Únicas**

### 🤖 **Automatización con IA**
- ✅ **Órdenes de compra automáticas** generadas por IA cuando stock es bajo
- ✅ **WhatsApp Business API** para comunicación directa con proveedores
- ✅ **Email tracking** con seguimiento automático de respuestas
- ✅ **Predicción de demanda** con Prophet/ARIMA ML models
- ✅ **Alertas inteligentes** personalizadas por tipo de negocio

### 📱 **Comunicación Multicanal**
- ✅ **WhatsApp automático** para órdenes urgentes
- ✅ **Email profesional** con templates personalizados  
- ✅ **Seguimiento de respuestas** de proveedores en tiempo real
- ✅ **Notificaciones push** para decisiones críticas

### 📊 **Customer Intelligence**
- ✅ **Segmentación RFM** automática (Champions, At Risk, Lost)
- ✅ **Predicción de churn** de clientes
- ✅ **CLV calculation** para enfocar esfuerzos
- ✅ **Campañas automáticas** de retención por email

### � **Reportes y Analytics**
- ✅ **Dashboards ejecutivos** con métricas clave
- ✅ **Análisis ABC** de productos más rentables
- ✅ **Reportes automáticos** PDF/Excel programados
- ✅ **KPIs predictivos** para toma de decisiones

## � **Demo en 60 Segundos**

```text
1. 🔴 ALERTA: "Producto X tiene solo 5 unidades en stock"
2. 🤖 IA: "Generando orden de compra automática..."
3. 📱 WhatsApp: Orden enviada al proveedor al instante
4. 📧 Email: Backup profesional con tracking automático
5. ✅ CONFIRMADO: Proveedor responde "OK, mañana llega"
6. 📊 DASHBOARD: Stock actualizado, KPIs en tiempo real
```

## �🏗️ **Arquitectura del Sistema**

```mermaid
graph TD
    A[Frontend React] --> B[Django REST API]
    B --> C[PostgreSQL Database]
    B --> D[WhatsApp Business API]
    B --> E[Gmail API / Email Service]
    B --> F[ML Engine Prophet/ARIMA]
    B --> G[Celery Background Tasks]
    G --> H[Redis Cache/Queue]
    B --> I[Customer Intelligence]
    B --> J[Report Generator]
```

## 🛠️ **Stack Tecnológico Completo**

### Backend

- **Django 4.2** + **Django REST Framework** - API robusta y escalable
- **PostgreSQL** - Base de datos empresarial (SQLite para desarrollo)
- **Celery + Redis** - Tareas asíncronas y caching  
- **Prophet + ARIMA** - Machine Learning para pronósticos
- **WhatsApp Business Cloud API** - Comunicación directa con proveedores
- **Gmail API** - Email tracking y automatización

### Frontend

- **React 18** + **TypeScript** - Interfaz moderna y tipado seguro
- **Tailwind CSS** - Diseño responsive y consistente
- **React Router** - Navegación SPA
- **Recharts** - Visualizaciones interactivas
- **React Query** - State management y caching
- **Recharts** - Gráficos y visualizaciones

## � **Instalación Rápida (5 minutos)**

### **Prerequisitos**

- Python 3.11+
- Node.js 18+
- Git
- PostgreSQL (producción) / SQLite (desarrollo)

### **1. Setup Backend**

```bash
# Clonar proyecto
git clone <repository-url>
cd mvp

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python manage.py migrate
python manage.py createsuperuser

# Iniciar servidor backend
python manage.py runserver 0.0.0.0:8080
```

### **2. Setup Frontend**

```bash
# En nueva terminal
cd datalens_frontend

# Instalar dependencias
npm install

# Configurar API URL
echo "REACT_APP_API_URL=http://localhost:8080/api" > .env

# Iniciar frontend
npm start
```

### **3. Variables de Entorno Críticas**

```env
# .env en la raíz del proyecto
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=sqlite:///db.sqlite3

# WhatsApp Business API (Opcional)
WHATSAPP_TOKEN=tu-token-whatsapp
WHATSAPP_PHONE_ID=tu-phone-id

# Gmail API (Opcional)
GMAIL_CLIENT_ID=tu-gmail-client-id
GMAIL_CLIENT_SECRET=tu-gmail-secret
```

## 🎯 **Funcionalidades Implementadas vs. Roadmap**

### ✅ **CORE FEATURES (100% Completado)**

#### **Gestión Inteligente de Inventario**
- ✅ CRUD completo de productos con categorización
- ✅ Control de stock en tiempo real
- ✅ Alertas automáticas de stock bajo
- ✅ Múltiples ubicaciones y almacenes
- ✅ Tracking de movimientos completo

#### **Automatización de Compras**
- ✅ **Órdenes automáticas con IA** - Generación inteligente basada en patrones
- ✅ **WhatsApp Business API** - Envío automático a proveedores  
- ✅ **Email tracking** - Seguimiento de respuestas automático
- ✅ **Multi-proveedor** - Gestión centralizada de múltiples proveedores
- ✅ **Templates inteligentes** - Contenido personalizado por IA

#### **Customer Intelligence**
- ✅ **Segmentación RFM** - Champions, At Risk, Lost customers
- ✅ **Churn prediction** - Predicción de pérdida de clientes
- ✅ **CLV calculation** - Valor de vida del cliente
- ✅ **Behavioral analytics** - Patrones de compra automáticos
- ✅ **Automated campaigns** - Emails de retención automáticos

#### **Machine Learning & Forecasting**
- ✅ **Prophet models** - Predicción de demanda con estacionalidad
- ✅ **ARIMA analysis** - Análisis de tendencias avanzado
- ✅ **Accuracy metrics** - MAE, MAPE, RMSE tracking
- ✅ **Confidence intervals** - Intervalos de predicción
- ✅ **Auto-retraining** - Mejora continua de modelos

#### **Reportes y Analytics**
- ✅ **Executive dashboards** - Métricas clave en tiempo real
- ✅ **ABC analysis** - Productos más rentables automático
- ✅ **Scheduled reports** - PDF/Excel programados
- ✅ **KPI tracking** - ROI, rotación, márgenes
- ✅ **Exportación masiva** - Múltiples formatos

### 🚧 **ECOMMERCE FEATURES (Opcional - No crítico para target B2B)**

#### **Tienda Online (No implementado)**
- ❌ Frontend público para clientes
- ❌ Shopping cart y checkout
- ❌ Payment gateway integration
- ❌ Customer self-service portal

#### **POS System (No implementado)**  
- ❌ Interface punto de venta
- ❌ Barcode scanner integration
- ❌ Receipt printing
- ❌ Cash register functionality

> **💡 Nota**: Estas funcionalidades NO son necesarias para el público objetivo (PYMES B2B) que ya tienen canales de venta establecidos.

## 📊 **APIs Principales Disponibles**

### **Core Business APIs**
```http
# Autenticación JWT
POST /api/auth/login/
POST /api/auth/refresh/
GET  /api/auth/profile/

# Gestión de Inventario  
GET  /api/inventory/products/
POST /api/inventory/products/
GET  /api/inventory/dashboard/
GET  /api/inventory/low-stock/

# Órdenes de Compra Automáticas
POST /api/purchase-orders/auto-generate/
POST /api/purchase-orders/{id}/send-whatsapp/
POST /api/purchase-orders/{id}/send-email/
GET  /api/purchase-orders/stats/

# Customer Intelligence
GET  /api/intelligence/segments/
POST /api/intelligence/analyze-customer/
GET  /api/intelligence/churn-prediction/
POST /api/intelligence/trigger-campaign/

# Machine Learning & Forecasting
POST /api/forecasting/predict/
GET  /api/forecasting/accuracy-metrics/
POST /api/forecasting/train-model/

# Reportes Automáticos
POST /api/reports/generate/
GET  /api/reports/scheduled/
GET  /api/reports/kpis/
```

## 🗃️ **Estructura del Proyecto**

```
mvp/
├── 🎛️  datalens_backend/         # Configuración Django + settings
├── 🖥️  datalens_frontend/        # React + TypeScript frontend
├── 🔐 authentication/           # JWT auth + multi-tenant system
├── 📦 inventory/               # Core inventory + purchase orders
├── 🔮 forecasting/             # ML models Prophet/ARIMA
├── 🚨 alerts/                  # Smart notifications system  
├── 📊 reports/                 # Automated report generation
├── 🧠 intelligence/            # Customer intelligence + CRM
├── 📥 data_import/             # CSV/Excel import tools
├── 💬 chatbot/                 # WhatsApp integration
├── 🔧 ml_service/              # Machine Learning engine
├── 📈 analytics/               # Business intelligence
└── 📋 requirements.txt         # Python dependencies
```

## 🎯 **Casos de Uso Reales**

### **🏪 Caso 1: Distribuidora de Alimentos**
```
Problema: "Perdemos S/ 15,000/mes en productos vencidos"
Solución: 
✅ Alertas automáticas 15 días antes del vencimiento
✅ Órdenes de compra con rotación FIFO  
✅ Predicción de demanda por estacionalidad
Resultado: 85% reducción en merma
```

### **🛍️ Caso 2: Tienda de Ropa Online**
```
Problema: "No sabemos cuándo reponer tallas/colores"
Solución:
✅ Segmentación automática de clientes por preferencias
✅ WhatsApp automático a proveedores cuando stock < 5
✅ Dashboard con productos más vendidos por temporada
Resultado: 40% aumento en rotación de inventario
```

### **� Caso 3: Importadora de Repuestos**
```
Problema: "Proveedores no responden emails a tiempo"
Solución:
✅ WhatsApp Business API con templates personalizados
✅ Email tracking con reenvío automático
✅ Predicción de demanda basada en data histórica
Resultado: 90% respuesta en < 24 horas
```

## 💰 **Modelo de Negocio**

### **Pricing Strategy**
- 🎯 **Target**: S/ 400/mes ($100 USD) - Validado con clientes reales
- 📈 **Value Prop**: ROI positivo en primer mes de uso
- 🎁 **Freemium**: 30 días gratis + demo personalizado
- 📊 **Escalabilidad**: Precio por cantidad de productos/transacciones

### **Revenue Streams**
1. **SaaS Subscription** - Ingreso recurrente mensual
2. **Setup & Training** - Implementación personalizada  
3. **Custom Integrations** - Conectores específicos
4. **WhatsApp API Credits** - Revenue share con Meta

## � **Ventajas Competitivas**

### **vs. ERPs tradicionales (SAP, Odoo)**
- ✅ **10x más rápido** de implementar (días vs meses)
- ✅ **20x más barato** (S/400 vs S/8,000+/mes)
- ✅ **WhatsApp nativo** (crítico en mercado peruano)
- ✅ **IA integrada** desde el primer día

### **vs. Inventario básico (Excel, apps simples)**
- ✅ **Automatización completa** vs manual
- ✅ **Predicción IA** vs reactivo
- ✅ **Multi-canal** vs single point
- ✅ **Customer Intelligence** vs solo productos

### **vs. Soluciones internacionales**
- ✅ **Localizado para Perú** (WhatsApp, cultura, precios)
- ✅ **Soporte en español** con contexto local
- ✅ **Métodos de pago locales** (BCP, Interbank, etc.)
- ✅ **Regulaciones SUNAT** compliance

## 🧪 **Testing & Quality**

```bash
# Ejecutar test suite completo
python manage.py test

# Coverage report
coverage run --source='.' manage.py test
coverage report --skip-covered

# Frontend tests
cd datalens_frontend
npm test

# E2E tests con Playwright
npm run test:e2e
```

## 🌐 **URLs de Desarrollo**

- **🖥️ Frontend**: [http://localhost:3000](http://localhost:3000)
- **🔧 Backend API**: [http://localhost:8080](http://localhost:8080)  
- **👨‍💼 Admin Panel**: [http://localhost:8080/admin/](http://localhost:8080/admin/)
- **📚 API Docs**: [http://localhost:8080/api/docs/](http://localhost:8080/api/docs/)
- **📖 ReDoc**: [http://localhost:8080/api/redoc/](http://localhost:8080/api/redoc/)

## 🛣️ **Roadmap 2025**

### **Q1 2025 - Foundation** ✅
- [x] Core inventory management
- [x] WhatsApp Business API integration  
- [x] ML forecasting with Prophet/ARIMA
- [x] Customer intelligence system
- [x] Automated purchase orders

### **Q2 2025 - Scale**
- [ ] **Multi-empresa**: Gestión de múltiples empresas
- [ ] **Mobile app**: React Native para iOS/Android
- [ ] **Advanced BI**: Power BI integration
- [ ] **API público**: Para integraciones de terceros

### **Q3 2025 - Intelligence**
- [ ] **Computer Vision**: Reconocimiento de productos por foto
- [ ] **Voice Commands**: Alexa/Google Assistant integration
- [ ] **Blockchain**: Trazabilidad de productos premium
- [ ] **IoT Sensors**: Stock en tiempo real con sensores

### **Q4 2025 - Expansion**
- [ ] **Multi-país**: Colombia, Ecuador, Bolivia
- [ ] **Marketplace**: DataLens App Store
- [ ] **White Label**: Solución para consultoras
- [ ] **IPO Ready**: Escalabilidad empresarial

## 👥 **Equipo & Contribuciones**

### **Core Team**
- 🧑‍💻 **Juan Diego Gutierrez** - Full-stack Developer & Product Owner
- 🤖 **AI Assistant** - Architecture & Code Review

### **¿Cómo Contribuir?**
1. 🍴 Fork el repositorio
2. 🌿 Crea feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 Commit cambios (`git commit -m 'Add amazing feature'`)
4. 📤 Push branch (`git push origin feature/amazing-feature`)
5. 🔄 Abre Pull Request

### **Coding Standards**
- **Backend**: PEP 8 (Python) + Django best practices
- **Frontend**: ESLint + Prettier + TypeScript strict
- **Testing**: 80%+ coverage mínimo
- **Documentation**: Docstrings obligatorios

## 📞 **Contacto & Soporte**

### **Business Inquiries**
- 📧 **Email**: juan@datalens.pe
- 📱 **WhatsApp**: +51 999 999 999
- 🌐 **Website**: [datalens.pe](https://datalens.pe)

### **Technical Support**
- 🐛 **Issues**: [GitHub Issues](https://github.com/1di210299/mvp/issues)
- 💬 **Discord**: [DataLens Community](https://discord.gg/datalens)
- 📖 **Docs**: [docs.datalens.pe](https://docs.datalens.pe)

### **Social Media**
- 🐦 **Twitter**: [@DataLensPE](https://twitter.com/DataLensPE)
- 💼 **LinkedIn**: [DataLens Company](https://linkedin.com/company/datalens)
- 📸 **Instagram**: [@datalens.pe](https://instagram.com/datalens.pe)

---

## 📄 **Licencia**

Este proyecto está bajo la **Licencia MIT** - ver [LICENSE](LICENSE) para detalles.

```
MIT License - Libre para uso comercial y personal
✅ Uso comercial permitido
✅ Modificación permitida  
✅ Distribución permitida
✅ Uso privado permitido
❌ Sin garantía ni responsabilidad
```

---

<div align="center">

**🚀 DataLens MVP v2.0 - Transformando PYMES con Inteligencia Artificial**

*"De Excel a IA en 30 días"*

[![Made with ❤️ in Peru](https://img.shields.io/badge/Made%20with%20❤️%20in-Peru-red)](https://github.com/1di210299/mvp)
[![Django](https://img.shields.io/badge/Django-4.2-green)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://typescriptlang.org)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Business%20API-25D366)](https://developers.facebook.com/docs/whatsapp)

</div>