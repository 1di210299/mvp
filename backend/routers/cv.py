from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas import CVCreate, CVResponse
from models import CV as CVModel, User as UserModel
from routers.auth import get_current_user
from openai_service import openai_service

router = APIRouter()

@router.post("/improve", response_model=CVResponse)
async def improve_cv(
    cv_data: CVCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mejorar CV con IA"""
    
    # Crear registro en la base de datos
    db_cv = CVModel(
        user_id=current_user.id,
        original_content=cv_data.original_content,
        status="processing"
    )
    
    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)
    
    try:
        # Llamar al servicio de OpenAI
        ai_result = await openai_service.improve_cv(cv_data.original_content)
        
        # Actualizar el registro con los resultados
        db_cv.improved_content = ai_result.get("improved_cv", "")
        db_cv.feedback = f"Feedback: {ai_result.get('feedback', '')}\n\nSugerencias:\n" + \
                        "\n".join([f"• {suggestion}" for suggestion in ai_result.get('suggestions', [])])
        db_cv.status = "completed"
        
        db.commit()
        db.refresh(db_cv)
        
        return db_cv
        
    except Exception as e:
        # Actualizar estado en caso de error
        db_cv.status = "error"
        db_cv.feedback = f"Error al procesar: {str(e)}"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar el CV"
        )

@router.get("/history", response_model=List[CVResponse])
async def get_cv_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener historial de CVs del usuario"""
    cvs = db.query(CVModel).filter(CVModel.user_id == current_user.id).order_by(CVModel.created_at.desc()).all()
    return cvs

@router.get("/{cv_id}", response_model=CVResponse)
async def get_cv(
    cv_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener CV específico"""
    cv = db.query(CVModel).filter(
        CVModel.id == cv_id,
        CVModel.user_id == current_user.id
    ).first()
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV no encontrado"
        )
    
    return cv

@router.delete("/{cv_id}")
async def delete_cv(
    cv_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar CV"""
    cv = db.query(CVModel).filter(
        CVModel.id == cv_id,
        CVModel.user_id == current_user.id
    ).first()
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV no encontrado"
        )
    
    db.delete(cv)
    db.commit()
    
    return {"message": "CV eliminado exitosamente"}