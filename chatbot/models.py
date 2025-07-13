from django.db import models
from django.contrib.auth import get_user_model
from authentication.models import Company
import json

User = get_user_model()

class ChatbotSession(models.Model):
    """Sesión de conversación con el chatbot"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_sessions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='chatbot_sessions', null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True)
    context_data = models.JSONField(default=dict, help_text="Datos de contexto de la sesión actual")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sesión de Chatbot"
        verbose_name_plural = "Sesiones de Chatbot"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sesión {self.session_id} - {self.user.email}"


class ChatMessage(models.Model):
    """Mensaje individual en una conversación de chatbot"""
    MESSAGE_TYPES = [
        ('user', 'Usuario'),
        ('assistant', 'Asistente'),
        ('system', 'Sistema'),
    ]
    
    session = models.ForeignKey(ChatbotSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, help_text="Metadatos adicionales del mensaje")
    tokens_used = models.IntegerField(default=0, help_text="Tokens utilizados por OpenAI")
    response_time = models.FloatField(null=True, blank=True, help_text="Tiempo de respuesta en segundos")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Mensaje del Chat"
        verbose_name_plural = "Mensajes del Chat"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."


class ChatbotKnowledgeBase(models.Model):
    """Base de conocimiento para el chatbot específica de DataLens"""
    category = models.CharField(max_length=100, help_text="Categoría del conocimiento")
    title = models.CharField(max_length=255)
    content = models.TextField()
    keywords = models.JSONField(default=list, help_text="Palabras clave para búsqueda")
    context_type = models.CharField(max_length=50, help_text="Tipo de contexto (dashboard, products, reports, etc.)")
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1, help_text="Prioridad para búsqueda (1=alta, 5=baja)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Base de Conocimiento"
        verbose_name_plural = "Base de Conocimiento"
        ordering = ['priority', '-created_at']
    
    def __str__(self):
        return f"{self.category} - {self.title}"


class ChatbotAnalytics(models.Model):
    """Analytics y métricas del chatbot"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='chatbot_analytics', null=True, blank=True)
    date = models.DateField()
    total_sessions = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    most_asked_topics = models.JSONField(default=list)
    satisfaction_rating = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Analytics del Chatbot"
        verbose_name_plural = "Analytics del Chatbot"
        unique_together = ['company', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics {self.date} - {self.company.name if self.company else 'Global'}"
