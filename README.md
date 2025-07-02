# DataLens MVP - Backend

DataLens es una plataforma integral de análisis y gestión de inventarios para pequeñas y medianas empresas peruanas. Utiliza modelos avanzados de machine learning para ofrecer insights detallados sobre rotación de inventario, predicción de demanda, rendimiento de productos y sugerencias automáticas de reabastecimiento.

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
[Frontend React] <--> [API Gateway] --> [Django REST API] --> [PostgreSQL/SQLite]
                                          |                    
                                          --> [ML Service] --> [Prophet/ARIMA Models]
                                          |
                                          --> [Celery Tasks] --> [Redis]
```

## 📋 Requisitos del Sistema

- Python 3.11+
- Django 4.2+
- PostgreSQL (Producción) / SQLite (Desarrollo)
- Redis (Para Celery)
- Git

## 🛠️ Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd mvp
```

### 2. Crear Entorno Virtual
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Copia el archivo `.env` y configura las variables:

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

### 5. Ejecutar Migraciones
```bash
python manage.py migrate
```

### 6. Crear Superusuario (Opcional)
```bash
python manage.py createsuperuser
```

### 7. Iniciar Servidor de Desarrollo

**Opción 1 - Usar script:**
```bash
# Windows
start_server.bat

# Linux/Mac
chmod +x start_server.sh
./start_server.sh
```

**Opción 2 - Comando manual:**
```bash
python manage.py runserver 0.0.0.0:8080
```

El servidor estará disponible en: http://0.0.0.0:8080/ (accesible desde cualquier IP de tu red)

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

- **Swagger UI**: http://0.0.0.0:8080/api/docs/
- **ReDoc**: http://0.0.0.0:8080/api/redoc/
- **Schema JSON**: http://0.0.0.0:8080/api/schema/

## 🗃️ Estructura del Proyecto

```
mvp/
├── datalens_backend/          # Configuración principal de Django
│   ├── settings.py           # Configuraciones
│   ├── urls.py              # URLs principales
│   └── wsgi.py              # WSGI para producción
├── authentication/           # Sistema de autenticación
│   ├── models.py            # Modelos de Usuario y Empresa
│   ├── views.py             # Vistas de autenticación
│   ├── serializers.py       # Serializers DRF
│   └── urls.py              # URLs de autenticación
├── inventory/               # Gestión de inventarios
│   ├── models.py            # Modelos de productos, stock, etc.
│   ├── views.py             # Vistas de inventario
│   ├── serializers.py       # Serializers de inventario
│   └── urls.py              # URLs de inventario
├── forecasting/             # Módulo de pronósticos ML
│   ├── models.py            # Modelos de pronóstico
│   ├── views.py             # Vistas de ML
│   └── urls.py              # URLs de pronósticos
├── alerts/                  # Sistema de alertas
│   ├── models.py            # Modelos de alertas
│   ├── views.py             # Vistas de alertas
│   └── urls.py              # URLs de alertas
├── reports/                 # Generación de reportes
│   ├── models.py            # Modelos de reportes
│   ├── views.py             # Vistas de reportes
│   └── urls.py              # URLs de reportes
├── static/                  # Archivos estáticos
├── media/                   # Archivos subidos
├── logs/                    # Logs del sistema
├── requirements.txt         # Dependencias Python
├── manage.py               # Comando de Django
└── README.md               # Este archivo
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

### User (Usuario)
- Extensión del modelo User de Django
- Roles y permisos
- Preferencias personalizadas

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

### Características ML
- Entrenamiento automático semanal
- Versionado de modelos con MLflow
- Métricas de precisión (MAE, MAPE, RMSE)
- Intervalos de confianza

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
# Usar script personalizado
start_server.bat  # Windows
./start_server.sh # Linux/Mac

# O comando manual
python manage.py runserver 0.0.0.0:8080
```

### Producción (Docker)
```bash
docker build -t datalens-backend .
docker run -p 8000:8000 datalens-backend
```

### Variables de Entorno para Producción
```env
DEBUG=False
SECRET_KEY=<secret-key-production>
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://redis-host:6379/0
EMAIL_HOST=smtp.mailserver.com
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
- [ ] Dashboard interactivo con gráficos
- [ ] Integración con ERPs (SAP, Odoo)
- [ ] Alertas por WhatsApp/SMS
- [ ] Pronósticos por ML avanzado (LSTM)
- [ ] Optimización de inventarios

### Fase 3
- [ ] Módulo de compras automáticas
- [ ] Integración con proveedores
- [ ] Analytics avanzado
- [ ] Mobile app (React Native)
- [ ] Inteligencia artificial conversacional

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## � Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte técnico o consultas:
- Email: soporte@datalens.com
- Documentación: [docs.datalens.com](https://docs.datalens.com)
- Issues: [GitHub Issues](https://github.com/datalens/issues)

---

**DataLens MVP v1.0** - Transformando la gestión de inventarios con inteligencia artificial 🚀

### ✅ **Editor Inteligente de CV** (Gratuito)
- Mejora automática de currículums con IA
- Optimización para ATS (Applicant Tracking Systems)
- Feedback personalizado para el mercado peruano
- Historial de versiones

### 👑 **Generador de Cartas de Presentación** (Premium)
- Cartas personalizadas por puesto y empresa
- Tono profesional adaptado al contexto peruano
- Integración con descripciones de trabajo
- Generación ilimitada

### 🎭 **Simulador de Entrevistas** (Premium)
- Entrevistas simuladas con IA
- Feedback inmediato y detallado
- Preguntas adaptadas al mercado laboral peruano
- Práctica ilimitada

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL/SQLite** - Base de datos
- **OpenAI GPT-4** - Motor de IA
- **JWT** - Autenticación segura

### Frontend
- **React 18** - Biblioteca de interfaz de usuario
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Framework de estilos
- **React Router** - Navegación
- **Axios** - Cliente HTTP

## 📦 Instalación y Configuración

### Prerrequisitos
- Node.js 18+ y npm
- Python 3.8+
- Cuenta de OpenAI con API key

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd mvp
```

### 2. Configurar el Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones (especialmente OPENAI_API_KEY)

# Crear base de datos
python -c "from database import engine, Base; Base.metadata.create_all(bind=engine)"

# Ejecutar servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Configurar el Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar aplicación
npm start
```

## 🌐 URLs de Acceso

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 🔑 Variables de Entorno Importantes

### Backend (.env)
```bash
SECRET_KEY=tu_clave_secreta_muy_segura
OPENAI_API_KEY=sk-tu_api_key_de_openai
DATABASE_URL=sqlite:///./coach_empleo_ia.db
FRONTEND_URL=http://localhost:3000
```

## 📱 Uso de la Aplicación

### Para Usuarios Gratuitos
1. Regístrate en la plataforma
2. Accede al **Editor de CV**
3. Pega o escribe tu CV actual
4. Haz clic en "Mejorar con IA"
5. Descarga tu CV optimizado

### Para Usuarios Premium
1. Actualiza a cualquier plan premium
2. Accede a todas las funciones:
   - **Cartas de Presentación**: Crea cartas personalizadas
   - **Simulador de Entrevistas**: Practica con IA
   - **Análisis Avanzado**: Feedback detallado

## 🏗️ Arquitectura del Proyecto

```
mvp/
├── backend/                 # API FastAPI
│   ├── main.py             # Punto de entrada
│   ├── models.py           # Modelos de base de datos
│   ├── schemas.py          # Esquemas Pydantic
│   ├── database.py         # Configuración DB
│   ├── auth_utils.py       # Utilidades de autenticación
│   ├── openai_service.py   # Servicio de OpenAI
│   └── routers/            # Endpoints organizados
│       ├── auth.py         # Autenticación
│       ├── cv.py           # Editor de CV
│       ├── cover_letter.py # Cartas de presentación
│       ├── interview.py    # Simulador de entrevistas
│       └── payments.py     # Sistema de pagos
├── frontend/               # App React
│   ├── src/
│   │   ├── components/     # Componentes reutilizables
│   │   ├── contexts/       # Contextos React
│   │   ├── pages/          # Páginas principales
│   │   ├── services/       # Servicios API
│   │   ├── types/          # Tipos TypeScript
│   │   └── utils/          # Utilidades
│   └── public/             # Archivos estáticos
└── README.md               # Este archivo
```

## 🎯 Funcionalidades Específicas para Perú

### Editor de CV
- Formatos preferidos por empresas peruanas
- Terminología laboral local
- Optimización para ATS populares en Perú

### Cartas de Presentación
- Tono formal apropiado para el mercado peruano
- Referencias a empresas locales conocidas
- Estructura valorada por reclutadores peruanos

### Simulador de Entrevistas
- Preguntas típicas del mercado laboral peruano
- Escenarios de empresas locales
- Feedback cultural y profesional específico

## 💰 Modelo de Precios

- **Gratuito**: Editor de CV ilimitado
- **Prueba Premium (S/ 9.90)**: 7 días, todas las funciones
- **Mensual (S/ 29.90)**: Plan completo mensual
- **Anual (S/ 299.90)**: Plan completo anual (17% descuento)

## 🔐 Seguridad y Privacidad

- Autenticación JWT segura
- Encriptación de contraseñas con bcrypt
- Datos almacenados localmente (no compartidos)
- API de OpenAI con prompts optimizados

## 🚀 Próximas Funcionalidades

- [ ] Integración con LinkedIn
- [ ] Análisis de mercado laboral en tiempo real
- [ ] Red de networking profesional
- [ ] Sesiones de coaching 1:1
- [ ] Integración con portales de empleo peruanos

## 🤝 Contribución

Este es un MVP en desarrollo. Para contribuir:

1. Fork el proyecto
2. Crea una branch para tu feature
3. Commit tus cambios
4. Push a la branch
5. Abre un Pull Request

## 📞 Soporte

Para soporte técnico y preguntas:
- Email: soporte@coachempleo.pe
- Website: https://coachempleo.pe

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

**Desarrollado con ❤️ para el mercado laboral peruano**

¿Listo para impulsar tu carrera profesional? ¡Comienza ahora! 🚀