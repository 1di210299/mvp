import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db.session import engine, get_db
from app.db import models
from app.api import routes, webhooks
from app.config import is_env_ready, APP_ENV, DEBUG

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="WhatsApp Sales Bot",
    description="Sistema de ventas automatizado por WhatsApp con prevención de extorsiones",
    version="0.1.0",
    debug=DEBUG,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(routes.router, prefix="/api", tags=["API"])
app.include_router(webhooks.router, prefix="/webhook", tags=["Webhooks"])

@app.get("/")
async def root():
    """Endpoint de prueba para verificar que la API está funcionando."""
    return {
        "message": "WhatsApp Sales Bot API está en funcionamiento",
        "environment": APP_ENV,
        "status": "ready" if is_env_ready else "configuration_needed"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Endpoint para verificar la salud de la aplicación."""
    try:
        # Verificar conexión a BD
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "environment": APP_ENV
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)