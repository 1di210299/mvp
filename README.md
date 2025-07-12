# DataLens MVP - Plataforma de Gestión de Inventarios

DataLens es una plataforma integral de análisis y gestión de inventarios para pequeñas y medianas empresas. Utiliza modelos avanzados de machine learning para ofrecer insights detallados sobre rotación de inventario, predicción de demanda, rendimiento de productos y sugerencias automáticas de reabastecimiento.

## 🚀 Características Principales

### MVP (Versión 1.0)
- ✅ **Sistema de Autenticación**: JWT con roles (Superadmin, Admin, Analista)
- ✅ **Gestión de Inventarios**: Productos, categorías, ubicaciones, proveedores
- ✅ **Transacciones**: Control de movimientos de stock
- ✅ **API REST**: Endpoints documentados con Swagger/OpenAPI
- 🚧 **Dashboard Operativo**: Métricas y KPIs en tiempo real
- 🚧 **Pronóstico de Demanda**: Modelos Prophet/ARIMA para predicción
- 🚧 **Sistema de Alertas**: Notificaciones automáticas de stock
- 🚧 **Reportes**: Generación automática de reportes PDF/CSV

## 🏗️ Arquitectura del Sistema

```
[Frontend React] <--> [Django REST API] --> [SQLite/PostgreSQL]
                            |                    
                            --> [ML Service] --> [Prophet/ARIMA Models]
                            |
                            --> [Celery Tasks] --> [Redis]
```

## 📋 Requisitos del Sistema

- Python 3.11+
- Django 4.2+
- Node.js 18+ (para el frontend)
- PostgreSQL (Producción) / SQLite (Desarrollo)
- Redis (Para Celery)
- Git

## 🛠️ Stack Tecnológico

### Backend
- **Django 4.2** - Framework web Python
- **Django REST Framework** - API REST
- **SQLite/PostgreSQL** - Base de datos
- **Celery** - Tareas asíncronas
- **Redis** - Cache y broker de mensajes
- **Prophet/ARIMA** - Modelos de ML para pronósticos

### Frontend
- **React 18** - Biblioteca de interfaz de usuario
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Framework de estilos
- **React Router** - Navegación
- **Recharts** - Gráficos y visualizaciones

## 🛠️ Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd mvp
```

### 2. Configurar Backend
```bash
# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver 0.0.0.0:8080
```

### 3. Configurar Frontend
```bash
cd datalens_frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
# Crear archivo .env
echo "REACT_APP_API_URL=http://localhost:8080/api" > .env

# Iniciar desarrollo
npm start
```

### 4. Variables de Entorno
Crear archivo `.env` en la raíz del proyecto:

```env
# Django Configuration
DEBUG=True
SECRET_KEY=django-insecure-datalens-mvp-2025-development-key
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3

# Redis Configuration (para Celery)
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@datalens.com
```

## 📚 Documentación de la API

### Endpoints Principales

#### Autenticación
- `POST /api/auth/login/` - Iniciar sesión (JWT)
- `POST /api/auth/refresh/` - Renovar token
- `POST /api/auth/register/` - Registrar nueva empresa/usuario
- `GET /api/auth/profile/` - Obtener perfil de usuario

#### Inventario
- `GET /api/inventory/products/` - Listar productos
- `POST /api/inventory/products/` - Crear producto
- `GET /api/inventory/dashboard/` - Dashboard principal
- `GET /api/inventory/low-stock/` - Productos con stock bajo
- `POST /api/inventory/upload/` - Subir archivo CSV

#### Alertas
- `GET /api/alerts/alerts/` - Listar alertas
- `POST /api/alerts/rules/` - Crear regla de alerta
- `POST /api/alerts/check-alerts/` - Verificar alertas

#### Pronósticos
- `POST /api/forecasting/predict/` - Generar pronóstico
- `GET /api/forecasting/forecasts/` - Listar pronósticos
- `POST /api/forecasting/train-model/` - Entrenar modelo

#### Reportes
- `POST /api/reports/generate/` - Generar reporte
- `GET /api/reports/reports/` - Listar reportes
- `GET /api/reports/kpis/` - Obtener KPIs

### Documentación Interactiva

- **Swagger UI**: http://localhost:8080/api/docs/
- **ReDoc**: http://localhost:8080/api/redoc/
- **Frontend**: http://localhost:3000

## 🗃️ Estructura del Proyecto

```
mvp/
├── datalens_backend/          # Configuración principal de Django
├── datalens_frontend/         # Frontend React + TypeScript
├── authentication/           # Sistema de autenticación
├── inventory/               # Gestión de inventarios
├── forecasting/             # Módulo de pronósticos ML
├── alerts/                  # Sistema de alertas
├── reports/                 # Generación de reportes
├── data_import/            # Importación de datos
├── static/                  # Archivos estáticos
├── media/                   # Archivos subidos
├── logs/                    # Logs del sistema
├── requirements.txt         # Dependencias Python
└── manage.py               # Comando de Django
```

## 🔐 Roles y Permisos

### Superadmin
- Acceso total al sistema
- Gestión de empresas y usuarios
- Configuración global

### Administrador
- Gestión completa de su empresa
- Crear/editar usuarios, productos, alertas
- Acceso a todos los reportes

### Analista
- Visualización de dashboards
- Generación de reportes
- Solo lectura de inventarios

## 🔍 Modelos de Datos Principales

### Company (Empresa)
- Información básica de la empresa
- Configuración de suscripción
- Límites de usuarios

### Product (Producto)
- SKU, nombre, descripción
- Precios, categorías, proveedores
- Configuración de stock (min/max)

### InventoryItem (Item de Inventario)
- Stock por ubicación
- Control de lotes y vencimientos
- Costos promedio ponderado

### Transaction (Transacción)
- Historial de movimientos
- Compras, ventas, ajustes
- Trazabilidad completa

## 🤖 Machine Learning

### Modelos Implementados
- **Prophet**: Para series temporales con estacionalidad
- **ARIMA**: Para análisis de tendencias
- **Regresión Lineal**: Para pronósticos simples
- **Random Forest**: Para predicciones complejas

### Características ML
- Entrenamiento automático semanal
- Métricas de precisión (MAE, MAPE, RMSE)
- Intervalos de confianza
- Evaluación automática de modelos

## 📊 KPIs y Métricas

### Indicadores Principales
- **Rotación de Inventario**: Veces que rota el stock por período
- **Días de Inventario**: Días de cobertura con stock actual
- **Nivel de Servicio**: % de pedidos atendidos sin faltantes
- **Costo de Inventario**: Valor total del stock
- **Productos de Baja Rotación**: SKUs con movimiento lento

### Alertas Automáticas
- Stock por debajo del mínimo
- Productos próximos a vencer
- Demanda proyectada vs stock disponible
- Productos sin movimiento

## 🚀 Despliegue

### Desarrollo Local
```bash
# Backend
python manage.py runserver 0.0.0.0:8080

# Frontend (nueva terminal)
cd datalens_frontend
npm start
```

### Producción (Docker)
```bash
docker build -t datalens-backend .
docker run -p 8000:8000 datalens-backend
```

## 🧪 Testing

```bash
# Ejecutar todas las pruebas
python manage.py test

# Ejecutar pruebas con coverage
coverage run --source='.' manage.py test
coverage report
```

## 📝 Próximas Funcionalidades

### Fase 2
- [ ] Dashboard interactivo con gráficos en tiempo real
- [ ] Integración con ERPs (SAP, Odoo, Bsale)
- [ ] Alertas por WhatsApp/SMS/Email
- [ ] Pronósticos por ML avanzado (LSTM)
- [ ] Optimización automática de inventarios

### Fase 3
- [ ] Módulo de compras automáticas
- [ ] Integración con proveedores
- [ ] Analytics avanzado con BI
- [ ] Progressive Web App (PWA)
- [ ] API pública para integraciones

## 🌐 URLs de Acceso

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **Admin Django**: http://localhost:8080/admin/
- **Documentación API**: http://localhost:8080/api/docs/

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte técnico o consultas:
- Email: soporte@datalens.com
- Documentación: [docs.datalens.com](https://docs.datalens.com)
- Issues: [GitHub Issues](https://github.com/datalens/issues)

---

**DataLens MVP v1.0** - Transformando la gestión de inventarios con inteligencia artificial 🚀