# filepath: /Users/juandiegogutierrezcortez/mvp/app/routes/products.py
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import logging
import shutil
from pathlib import Path
from datetime import datetime
import os

from app.db.session import get_db
from app.db import repositories, models

router = APIRouter()
logger = logging.getLogger(__name__)

# Directorio para almacenar documentación/archivos subidos
UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/", response_model=List[Dict[str, Any]])
async def get_products(
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de productos disponibles desde la base de datos
    """
    products = repositories.get_all_active_products(db)
    result = []
    
    for product in products:
        result.append({
            "id": product.id,
            "code": product.code,
            "name": product.name,
            "price": product.price,
            "description": product.description,
            "stock": product.stock,
            "is_active": product.is_active,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None
        })
    
    return result

@router.get("/{product_id}", response_model=Dict[str, Any])
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene información detallada de un producto
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    return {
        "id": product.id,
        "code": product.code,
        "name": product.name,
        "price": product.price,
        "description": product.description,
        "stock": product.stock,
        "is_active": product.is_active,
        "image_url": product.image_url,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None
    }

@router.post("/upload-documentation", response_model=Dict[str, Any])
async def upload_documentation(
    company_info: Optional[UploadFile] = File(None),
    products_list: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Sube documentación de la empresa y/o lista de productos para actualizar el catálogo.
    
    Args:
        company_info: Archivo con información de la empresa (opcional, JSON o CSV)
        products_list: Archivo con lista de productos (opcional, JSON o CSV)
    
    Returns:
        dict: Resultado de la importación
    """
    if not company_info and not products_list:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Debe proporcionar al menos un archivo (información de empresa o lista de productos)"
            }
        )
    
    # Crear directorio para la fecha actual (organización de archivos por fecha)
    date_dir = UPLOAD_DIR / datetime.now().strftime("%Y-%m-%d")
    date_dir.mkdir(exist_ok=True)
    
    company_info_path = None
    products_path = None
    
    # Guardar archivo de información de la empresa si se proporciona
    if company_info:
        company_file_path = date_dir / f"company_info_{datetime.now().strftime('%H%M%S')}{Path(company_info.filename).suffix}"
        
        with open(company_file_path, "wb") as buffer:
            shutil.copyfileobj(company_info.file, buffer)
        
        company_info_path = str(company_file_path)
        logger.info(f"Archivo de información de empresa guardado: {company_info_path}")
    
    # Guardar archivo de productos si se proporciona
    if products_list:
        products_file_path = date_dir / f"products_{datetime.now().strftime('%H%M%S')}{Path(products_list.filename).suffix}"
        
        with open(products_file_path, "wb") as buffer:
            shutil.copyfileobj(products_list.file, buffer)
        
        products_path = str(products_file_path)
        logger.info(f"Archivo de productos guardado: {products_path}")
    
    # Importar productos desde los archivos
    import_result = repositories.import_products_from_documentation(
        db=db,
        company_info_path=company_info_path,
        products_path=products_path
    )
    
    return {
        "status": "success",
        "message": "Documentación procesada correctamente",
        "details": import_result
    }

@router.get("/updates", response_model=Dict[str, Any])
async def get_product_updates(
    since: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene productos actualizados desde una fecha específica.
    
    Args:
        since: Fecha desde la cual buscar actualizaciones (formato ISO: YYYY-MM-DDTHH:MM:SS)
    
    Returns:
        dict: Lista de productos actualizados desde la fecha especificada
    """
    since_date = None
    if since:
        try:
            since_date = datetime.fromisoformat(since)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Formato de fecha inválido. Use el formato ISO: YYYY-MM-DDTHH:MM:SS"
                }
            )
    
    products = repositories.get_product_updates(db, since_date)
    
    return {
        "status": "success",
        "count": len(products),
        "products": products
    }

@router.post("/batch-update", response_model=Dict[str, Any])
async def batch_update_products(
    products: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """
    Actualiza múltiples productos en una sola operación.
    
    Args:
        products: Lista de diccionarios con datos de productos
        
    Returns:
        dict: Resultado de la actualización
    """
    stats = {
        "updated": 0,
        "created": 0,
        "skipped": 0,
        "errors": 0
    }
    
    error_details = []
    
    for item in products:
        try:
            # Validar datos mínimos requeridos
            if not item.get('code') or not item.get('name') or not item.get('price'):
                stats["skipped"] += 1
                error_details.append({
                    "code": item.get('code', 'Unknown'),
                    "error": "Datos mínimos requeridos no proporcionados (code, name, price)"
                })
                continue
            
            # Verificar si el producto ya existe
            existing_product = db.query(models.Product).filter(models.Product.code == item.get('code')).first()
            
            if existing_product:
                # Actualizar producto existente
                existing_product.name = item.get('name')
                existing_product.description = item.get('description', existing_product.description)
                existing_product.price = float(item.get('price'))
                existing_product.stock = int(item.get('stock', existing_product.stock))
                existing_product.image_url = item.get('image_url', existing_product.image_url)
                existing_product.is_active = item.get('is_active', True) in [True, 'true', 'True', '1', 1]
                existing_product.updated_at = datetime.utcnow()
                stats["updated"] += 1
            else:
                # Crear nuevo producto
                new_product = models.Product(
                    code=item.get('code'),
                    name=item.get('name'),
                    description=item.get('description', ''),
                    price=float(item.get('price')),
                    stock=int(item.get('stock', 0)),
                    image_url=item.get('image_url', None),
                    is_active=item.get('is_active', True) in [True, 'true', 'True', '1', 1],
                )
                db.add(new_product)
                stats["created"] += 1
                
        except Exception as e:
            stats["errors"] += 1
            error_details.append({
                "code": item.get('code', 'Unknown'),
                "error": str(e)
            })
    
    # Guardar cambios en la base de datos
    db.commit()
    
    return {
        "status": "success",
        "message": "Actualización por lotes completada",
        "stats": stats,
        "errors": error_details if stats["errors"] > 0 else None
    }