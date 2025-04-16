# WhatsApp Sales Bot

Un sistema de ventas automatizado a través de WhatsApp con características avanzadas de prevención de extorsiones y detección de amenazas.

## Características principales

- **Bot de ventas por WhatsApp**: Automatiza el proceso de ventas completo a través de WhatsApp.
- **Detección de amenazas**: Sistema avanzado de detección de extorsiones y mensajes sospechosos.
- **Honeypot**: Mecanismo para detectar y rastrear intentos de extorsión.
- **Panel de administración**: Interface web para gestionar productos, órdenes y clientes.
- **API completa**: Endpoints para integración con otros sistemas.
- **Monitoreo en tiempo real**: Integración con Prometheus y Grafana para métricas.
- **Múltiples métodos de pago**: Integración con diversas pasarelas de pago (Culqi, Yape, etc.)

## Estructura del proyecto

```
app/                  # Directorio principal de la aplicación
  ├── api/            # API endpoints y webhooks
  ├── bot/            # Lógica del bot de conversación
  ├── config/         # Configuraciones
  ├── data/           # Datos estáticos
  ├── db/             # Modelos de base de datos y sesiones
  ├── payments/       # Integración con pasarelas de pago
  ├── routes/         # Rutas web
  ├── security/       # Mecanismos de seguridad y detección de amenazas
  ├── services/       # Servicios compartidos
  ├── static/         # Archivos estáticos para web
  ├── templates/      # Plantillas Jinja2
  ├── utils/          # Utilidades
  └── main.py         # Punto de entrada principal

admin/                # Panel de administración con Streamlit
alembic/              # Migraciones de base de datos
docs/                 # Documentación
scripts/              # Scripts de utilidad
tests/                # Pruebas automatizadas
```

## Requisitos

- Python 3.9+
- Base de datos SQLite (por defecto) o PostgreSQL
- Cuenta de Twilio con WhatsApp Business API habilitado
- Claves de API para servicios de pago (opcional)
- Cuenta de OpenAI para análisis de texto (opcional)

## Instalación

1. Clona el repositorio:
   ```
   git clone https://github.com/tu-usuario/whatsapp-sales-bot.git
   cd whatsapp-sales-bot
   ```

2. Crea un entorno virtual:
   ```
   python -m venv venv
   source venv/bin/activate   # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Copia el archivo de variables de entorno y configúralo:
   ```
   cp .env.example .env
   # Edita el archivo .env con tus configuraciones
   ```

5. Configura la base de datos:
   ```
   python scripts/setup_db.py
   ```

## Configuración

El sistema utiliza variables de entorno para la configuración. Las principales son:

| Variable | Descripción | Valor por defecto |
|----------|-------------|------------------|
| `APP_ENV` | Entorno de la aplicación | `development` |
| `DEBUG` | Modo de depuración | `True` |
| `DATABASE_URL` | URL de conexión a la base de datos | `sqlite:///whatsapp_sales.db` |
| `TWILIO_ACCOUNT_SID` | SID de cuenta Twilio | - |
| `TWILIO_AUTH_TOKEN` | Token de autenticación Twilio | - |
| `TWILIO_PHONE_NUMBER` | Número de WhatsApp en formato `whatsapp:+123456789` | - |
| `OPENAI_API_KEY` | Clave API de OpenAI | - |
| `ADMIN_EMAIL` | Email para notificaciones administrativas | - |
| `ADMIN_PHONE` | Teléfono para notificaciones administrativas | - |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram para notificaciones | - |
| `TELEGRAM_CHAT_ID` | ID del chat de Telegram para notificaciones | - |
| `CULQI_PUBLIC_KEY` | Clave pública para Culqi | - |
| `CULQI_PRIVATE_KEY` | Clave privada para Culqi | - |

Consulta `.env.example` para ver todas las variables disponibles.

## Ejecución

### Iniciar la aplicación principal

```
uvicorn app.main:app --reload --port 8000
```

### Iniciar el panel de administración

```
streamlit run admin/app.py
```

### Iniciar monitoreo con Prometheus y Grafana

```
docker-compose up -d
```

## Endpoints principales

- `POST /api/webhooks/whatsapp`: Endpoint para webhooks de WhatsApp
- `GET /api/products`: Listado de productos
- `GET /api/client/dashboard/stats`: Estadísticas para el dashboard
- `GET /api/client/orders`: Listado de órdenes
- `GET /api/security/incidents`: Listado de incidentes de seguridad
- `GET /health`: Verificación de estado del sistema

La documentación completa de la API está disponible en `/docs` o `/redoc` cuando la aplicación está en ejecución.

## Sistema de seguridad

El sistema incluye múltiples capas de seguridad:

1. **Detección de mensajes sospechosos**: Analiza el contenido de los mensajes para detectar patrones de extorsión.
2. **Lista negra de números**: Bloquea automáticamente números con historial de comportamiento sospechoso.
3. **Honeypot**: Crea enlaces especiales para rastrear posibles atacantes.
4. **Monitoreo de actividad**: Detecta patrones inusuales de mensajes.
5. **Integración con IA**: Utiliza modelos de OpenAI para análisis avanzado de texto.

## Monitoreo y métricas

El sistema está integrado con Prometheus y Grafana para monitoreo en tiempo real. Las métricas principales incluyen:

- Mensajes de WhatsApp recibidos y enviados
- Intentos de pago (exitosos y fallidos)
- Actividades sospechosas detectadas
- Tiempos de respuesta de la API
- Uso de recursos del sistema

## Pruebas

Para ejecutar las pruebas unitarias:

```
pytest
```

Para pruebas específicas:

```
pytest tests/test_security.py
```

## Guía de contribución

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/amazing-feature`)
3. Realiza tus cambios y confirma (`git commit -m 'Add some amazing feature'`)
4. Empuja a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Juan Diego Gutiérrez - juandiegogutierrez@example.com

Enlace del proyecto: [https://github.com/tu-usuario/whatsapp-sales-bot](https://github.com/tu-usuario/whatsapp-sales-bot)