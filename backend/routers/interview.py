from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from database import get_db
from schemas import InterviewCreate, InterviewMessage, InterviewResponse, InterviewChat
from models import Interview as InterviewModel, User as UserModel
from routers.auth import get_current_user
from openai_service import openai_service

router = APIRouter()

def check_premium_access(current_user: UserModel):
    """Verificar acceso premium para entrevistas"""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta función requiere suscripción premium. Actualiza tu plan para continuar."
        )

@router.post("/start", response_model=InterviewResponse)
async def start_interview(
    interview_data: InterviewCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Iniciar una nueva entrevista simulada (requiere premium)"""
    
    # Verificar acceso premium
    check_premium_access(current_user)
    
    # Crear registro en la base de datos
    db_interview = InterviewModel(
        user_id=current_user.id,
        job_title=interview_data.job_title,
        company_name=interview_data.company_name,
        conversation_history="[]",
        status="active"
    )
    
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    
    try:
        # Obtener primera pregunta de OpenAI
        ai_result = await openai_service.conduct_interview(
            job_title=interview_data.job_title,
            conversation_history=[],
            user_response=None
        )
        
        # Actualizar con la primera pregunta
        db_interview.current_question = ai_result.get("question", "¡Hola! Cuéntame sobre ti y por qué te interesa este puesto.")
        
        db.commit()
        db.refresh(db_interview)
        
        return db_interview
        
    except Exception as e:
        # Actualizar estado en caso de error
        db_interview.status = "error"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar la entrevista"
        )

@router.post("/{interview_id}/respond", response_model=InterviewChat)
async def respond_to_interview(
    interview_id: int,
    message: InterviewMessage,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Responder a una pregunta de entrevista"""
    
    # Verificar acceso premium
    check_premium_access(current_user)
    
    # Obtener la entrevista
    interview = db.query(InterviewModel).filter(
        InterviewModel.id == interview_id,
        InterviewModel.user_id == current_user.id,
        InterviewModel.status == "active"
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrevista no encontrada o inactiva"
        )
    
    try:
        # Obtener historial de conversación
        conversation_history = json.loads(interview.conversation_history) if interview.conversation_history else []
        
        # Agregar la respuesta actual al historial
        conversation_history.append({
            "question": interview.current_question,
            "response": message.user_response
        })
        
        # Obtener siguiente pregunta y feedback de OpenAI
        ai_result = await openai_service.conduct_interview(
            job_title=interview.job_title,
            conversation_history=conversation_history,
            user_response=message.user_response
        )
        
        # Actualizar la entrevista
        interview.conversation_history = json.dumps(conversation_history)
        interview.current_question = ai_result.get("question", "")
        interview.feedback = ai_result.get("feedback", "")
        
        db.commit()
        
        return InterviewChat(
            question=ai_result.get("question", ""),
            feedback=ai_result.get("feedback", ""),
            next_question=ai_result.get("question", "")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar la respuesta"
        )

@router.put("/{interview_id}/finish")
async def finish_interview(
    interview_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finalizar una entrevista"""
    
    interview = db.query(InterviewModel).filter(
        InterviewModel.id == interview_id,
        InterviewModel.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrevista no encontrada"
        )
    
    interview.status = "completed"
    db.commit()
    
    return {"message": "Entrevista finalizada exitosamente"}

@router.get("/history", response_model=List[InterviewResponse])
async def get_interview_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener historial de entrevistas del usuario"""
    interviews = db.query(InterviewModel).filter(
        InterviewModel.user_id == current_user.id
    ).order_by(InterviewModel.created_at.desc()).all()
    return interviews

@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener entrevista específica"""
    interview = db.query(InterviewModel).filter(
        InterviewModel.id == interview_id,
        InterviewModel.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrevista no encontrada"
        )
    
    return interview

@router.delete("/{interview_id}")
async def delete_interview(
    interview_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar entrevista"""
    interview = db.query(InterviewModel).filter(
        InterviewModel.id == interview_id,
        InterviewModel.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrevista no encontrada"
        )
    
    db.delete(interview)
    db.commit()
    
    return {"message": "Entrevista eliminada exitosamente"}