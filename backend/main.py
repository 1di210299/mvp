from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import os
from dotenv import load_dotenv

from database import get_db
from routers import auth, cv, cover_letter, interview, payments
from models import Base
from database import engine

load_dotenv()

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Coach de Empleo con IA - API",
    description="API para MVP de aplicación de coaching laboral con IA para el mercado peruano",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(cv.router, prefix="/api/cv", tags=["cv"])
app.include_router(cover_letter.router, prefix="/api/cover-letter", tags=["cover-letter"])
app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])

@app.get("/")
async def root():
    return {"message": "Coach de Empleo con IA - API funcionando correctamente"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "coach-empleo-ia"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)