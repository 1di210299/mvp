# 🇵🇪 Coach de Empleo con IA - MVP

Una plataforma completa de coaching laboral powered by IA, especializada en el mercado peruano. Ayuda a profesionales a mejorar sus CVs, crear cartas de presentación personalizadas y practicar entrevistas laborales.

## 🚀 Características Principales

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