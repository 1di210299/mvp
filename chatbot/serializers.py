from rest_framework import serializers
from .models import ChatbotSession, ChatMessage, ChatbotKnowledgeBase, ChatbotAnalytics


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensajes de chat"""
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'message_type', 'content', 'metadata', 'tokens_used', 'response_time', 'created_at']
        read_only_fields = ['id', 'tokens_used', 'response_time', 'created_at']


class ChatbotSessionSerializer(serializers.ModelSerializer):
    """Serializer para sesiones de chatbot"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    messages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatbotSession
        fields = ['id', 'session_id', 'context_data', 'is_active', 'created_at', 'updated_at', 'messages', 'messages_count']
        read_only_fields = ['id', 'session_id', 'created_at', 'updated_at', 'messages', 'messages_count']
    
    def get_messages_count(self, obj):
        return obj.messages.count()


class ChatRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de chat"""
    message = serializers.CharField(max_length=2000)
    session_id = serializers.CharField(max_length=255, required=False)
    context_page = serializers.CharField(max_length=100, required=False)
    context_data = serializers.JSONField(required=False, default=dict)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de chat"""
    message = serializers.CharField()
    session_id = serializers.CharField()
    tokens_used = serializers.IntegerField()
    response_time = serializers.FloatField()
    suggested_actions = serializers.ListField(child=serializers.DictField(), required=False)


class ChatbotKnowledgeBaseSerializer(serializers.ModelSerializer):
    """Serializer para base de conocimiento"""
    
    class Meta:
        model = ChatbotKnowledgeBase
        fields = ['id', 'category', 'title', 'content', 'keywords', 'context_type', 'is_active', 'priority', 'created_at', 'updated_at']


class ChatbotAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer para analytics del chatbot"""
    
    class Meta:
        model = ChatbotAnalytics
        fields = ['id', 'date', 'total_sessions', 'total_messages', 'total_tokens_used', 
                 'average_response_time', 'most_asked_topics', 'satisfaction_rating', 'created_at']


class ChatHistorySerializer(serializers.Serializer):
    """Serializer para historial de chat simplificado"""
    session_id = serializers.CharField()
    last_message = serializers.CharField()
    message_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ChatSessionCreateSerializer(serializers.Serializer):
    """Serializer para crear nueva sesión de chat"""
    context_page = serializers.CharField(max_length=100, required=False)
    initial_context = serializers.JSONField(required=False, default=dict)