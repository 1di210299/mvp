import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import time
import os
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
# Importaciones para métricas
from starlette_exporter import PrometheusMiddleware, handle_metrics
import prometheus_client as prom

# Create necessary directories before configuring logging
os.makedirs("logs", exist_ok=True)

from app.db.session import engine, get_db
from app.db import models
from app.api import routes, webhooks, client
from app.config import is_env_ready, APP_ENV, DEBUG
from app.utils.whatsapp import check_whatsapp_connection
from app.utils.diagnose_whatsapp import diagnose_twilio_configuration, test_send_message
from app.utils.check_number_status import check_whatsapp_number_status

# Contadores para métricas personalizadas
whatsapp_messages_received = prom.Counter(
    'whatsapp_messages_received_total', 
    'Total number of WhatsApp messages received'
)
whatsapp_messages_sent = prom.Counter(
    'whatsapp_messages_sent_total', 
    'Total number of WhatsApp messages sent'
)
suspicious_activities = prom.Counter(
    'suspicious_activities_total', 
    'Total number of suspicious activities detected'
)
payment_attempts = prom.Counter(
    'payment_attempts_total', 
    'Total number of payment attempts',
    ['provider', 'status']
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join("logs", "app.log"), encoding="utf-8")
    ]
)

logger = logging.getLogger("app.main")

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Setup static files directory for CSS, JS, etc.
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="WhatsApp Sales Bot",
    description="Sistema de ventas automatizado por WhatsApp con prevención de extorsiones",
    version="1.0.0",
    debug=DEBUG,
)

# Middleware para métricas Prometheus
app.add_middleware(
    PrometheusMiddleware,
    app_name="whatsapp_sales",
    group_paths=True,
    prefix="whatsapp_sales",
    buckets=[0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint para métricas
app.add_route("/metrics", handle_metrics)

# Middleware para loguear todas las solicitudes (para depuración)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client = forwarded.split(",")[0]
    else:
        client = request.client.host if request.client else "unknown"
    
    logger.info(f"REQUEST: {request.method} {request.url.path} - Client: {client}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"RESPONSE: {request.method} {request.url.path} - Status: {response.status_code}")
    
    return response

# Incluir routers - using only the existing ones to avoid import errors
app.include_router(routes.router, prefix="/api", tags=["API"])
# Cambiar de /webhook a /api/webhooks para coincidir con la URL que espera Twilio
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
# Incluir el nuevo router para la API del cliente web
app.include_router(client.router, prefix="/api/client", tags=["Client API"])

# Importar y registrar el router de productos
from app.routes import products as products_router
app.include_router(products_router.router, prefix="/api/products", tags=["Products"])

# Importar y registrar el router de honeypot
from app.routes import honeypot as honeypot_router
app.include_router(honeypot_router.router, prefix="/api/security", tags=["Security"])

@app.get("/")
async def root(request: Request):
    """Endpoint principal que muestra una página de bienvenida con enlaces a herramientas de diagnóstico."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_title": "WhatsApp Sales Bot",
        "environment": APP_ENV,
        "status": "ready" if is_env_ready() else "configuration_needed"
    })

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Endpoint para verificar la salud de la aplicación."""
    try:
        # Verificar conexión a BD
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Verificar conexión de WhatsApp
    whatsapp_status = check_whatsapp_connection()
    
    return {
        "status": "healthy",
        "database": db_status,
        "environment": APP_ENV,
        "whatsapp": whatsapp_status
    }

@app.get("/api/whatsapp/status")
async def whatsapp_status():
    """Endpoint para verificar el estado de la conexión de WhatsApp."""
    status = check_whatsapp_connection()
    
    return {
        "whatsapp_status": status["status"],
        "last_active": status["last_active"],
        "details": status["details"],
        "last_message_received": status["last_message_received"],
        "last_message_sent": status["last_message_sent"]
    }

@app.get("/api/whatsapp/diagnose")
async def whatsapp_diagnosis():
    """Endpoint para realizar un diagnóstico completo de la conexión de WhatsApp/Twilio."""
    results = diagnose_twilio_configuration()
    return results

@app.get("/api/whatsapp/test-send")
@app.post("/api/whatsapp/test-send")
async def test_whatsapp_send(phone_number: str):
    """Endpoint para enviar un mensaje de prueba a un número específico."""
    if not phone_number:
        return {"error": "Debe proporcionar un número de teléfono", "success": False}
    
    if not phone_number.startswith("+"):
        return {"error": "El número debe comenzar con '+' seguido del código de país y número", "success": False}
    
    result = test_send_message(phone_number)
    return result

@app.get("/api/whatsapp/check-number/{phone_number}")
async def check_number_status(phone_number: str):
    """Verifica el estado de un número específico de WhatsApp."""
    if not phone_number or not phone_number.startswith("+"):
        return {"error": "Formato de número inválido. Debe comenzar con '+' seguido del código de país y número"}
    
    results = check_whatsapp_number_status(phone_number)
    return results

@app.get("/help/whatsapp", response_class=HTMLResponse)
async def whatsapp_help(request: Request):
    """Página de ayuda para solucionar problemas de WhatsApp."""
    return templates.TemplateResponse("whatsapp_help.html", {"request": request})

@app.get("/admin/products", response_class=HTMLResponse)
async def product_manager(request: Request):
    """Página para gestionar productos mediante interfaz gráfica"""
    return templates.TemplateResponse("product_manager.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)