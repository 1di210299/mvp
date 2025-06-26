from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas import CoverLetterCreate, CoverLetterResponse
from models import CoverLetter as CoverLetterModel, User as UserModel
from routers.auth import get_current_user
from openai_service import openai_service

router = APIRouter()

def check_premium_access(current_user: UserModel):
    """Verificar acceso premium para cartas de presentación"""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta función requiere suscripción premium. Actualiza tu plan para continuar."
        )

@router.post("/generate", response_model=CoverLetterResponse)
async def generate_cover_letter(
    letter_data: CoverLetterCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generar carta de presentación con IA (requiere premium)"""
    
    # Verificar acceso premium
    check_premium_access(current_user)
    
    # Crear registro en la base de datos
    db_letter = CoverLetterModel(
        user_id=current_user.id,
        job_title=letter_data.job_title,
        company_name=letter_data.company_name,
        job_description=letter_data.job_description,
        user_experience=letter_data.user_experience,
        status="processing"
    )
    
    db.add(db_letter)
    db.commit()
    db.refresh(db_letter)
    
    try:
        # Llamar al servicio de OpenAI
        ai_result = await openai_service.generate_cover_letter(
            job_title=letter_data.job_title,
            company_name=letter_data.company_name,
            job_description=letter_data.job_description,
            user_experience=letter_data.user_experience
        )
        
        # Actualizar el registro con los resultados
        db_letter.generated_content = ai_result.get("cover_letter", "")
        db_letter.status = "completed"
        
        db.commit()
        db.refresh(db_letter)
        
        return db_letter
        
    except Exception as e:
        # Actualizar estado en caso de error
        db_letter.status = "error"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar la carta de presentación"
        )

@router.get("/history", response_model=List[CoverLetterResponse])
async def get_cover_letter_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener historial de cartas de presentación del usuario"""
    letters = db.query(CoverLetterModel).filter(
        CoverLetterModel.user_id == current_user.id
    ).order_by(CoverLetterModel.created_at.desc()).all()
    return letters

@router.get("/{letter_id}", response_model=CoverLetterResponse)
async def get_cover_letter(
    letter_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener carta de presentación específica"""
    letter = db.query(CoverLetterModel).filter(
        CoverLetterModel.id == letter_id,
        CoverLetterModel.user_id == current_user.id
    ).first()
    
    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carta de presentación no encontrada"
        )
    
    return letter

@router.delete("/{letter_id}")
async def delete_cover_letter(
    letter_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar carta de presentación"""
    letter = db.query(CoverLetterModel).filter(
        CoverLetterModel.id == letter_id,
        CoverLetterModel.user_id == current_user.id
    ).first()
    
    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carta de presentación no encontrada"
        )
    
    db.delete(letter)
    db.commit()
    
    return {"message": "Carta de presentación eliminada exitosamente"}