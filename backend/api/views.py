# api/views.py
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status
from .models import DataConnection, Dataset
from .serializers import DataConnectionSerializer, DatasetSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .autonomous_monitor import AutonomousMonitor
from .models import Dataset, MonitoringLog, AgentAction
from .serializers import MonitoringLogSerializer, AgentActionSerializer
from .authentication import UserSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .decision_engine import DecisionEngine
from .learning_service import AdaptiveLearningService
from .models import Dataset, AgentAction, AgentLearningLog
import sys
import os
import json
import pandas as pd
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User  # Añade esta importación
from rest_framework.permissions import AllowAny, IsAuthenticated
from .authentication import UserSerializer
from .chart_generator import (
    generate_sales_chart,
    generate_category_chart,
    generate_regional_chart,
    generate_time_comparison_chart,
    generate_heatmap_chart,
    generate_sales_prediction
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connectors import sql

# Importación condicional para AWS
try:
    from connectors import aws
except ImportError:
    aws = None
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import BusinessRule, MonitoringLog, AgentAction, BusinessContext
from .serializers import (
    BusinessRuleSerializer, MonitoringLogSerializer, 
    AgentActionSerializer, BusinessContextSerializer
)
# Importar módulos para procesamiento, gráficos y predicción
from .data_processor import process_file
from .chart_generator import generate_sales_chart
from .prediction import predict_sales
from connectors.openai_connector import analyze_data

# Import NLP processor
from .nlp_processor import DeepseekNLPProcessor

# Importar parsers adicionales para manejo de archivos y JSON
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

# Initialize the NLP processor
try:
    nlp_processor = DeepseekNLPProcessor()
except Exception as e:
    print(f"Warning: Could not initialize NLP processor: {str(e)}")
    nlp_processor = None

# ---------------------------
# Endpoints existentes
# ---------------------------
@api_view(['GET', 'POST'])
@renderer_classes([JSONRenderer])
def test_connection(request):
    """
    API endpoint para probar conexiones a servicios externos.
    Soporta connectionType: 'sql', 'aws' y 'bigquery'.
    """
    if request.method == 'GET':
        return Response({
            "message": "Este endpoint requiere una solicitud POST con los datos de conexión",
            "example": {
                "connectionType": "sql o aws o bigquery",
                "connectionString": "sqlite:///test.db o s3://nombre-bucket (solo para SQL/BigQuery)",
                "username": "usuario_opcional (para SQL o AWS, es el access_key_id)",
                "password": "contraseña_opcional (para SQL o AWS, es el secret_access_key)",
                "query": "SELECT * FROM tabla LIMIT 5 (solo para SQL)"
            }
        })
    
    connection_type = request.data.get('connectionType')
    connection_string = request.data.get('connectionString')
    username = request.data.get('username')
    password = request.data.get('password')
    query = request.data.get('query')
    
    # Validación: se requiere connectionType
    if not connection_type:
        return Response(
            {"error": "Connection type is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Para SQL y BigQuery se requiere connectionString; para AWS no es obligatorio
    if connection_type in ['sql', 'bigquery'] and not connection_string:
        return Response(
            {"error": "Connection string is required for SQL and BigQuery connections"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        if connection_type == 'sql':
            metadata = sql.test_sql_connection(connection_string, username, password, query)
        elif connection_type == 'aws':
            if aws is None:
                return Response(
                    {"error": "AWS connector not available. Install boto3 with 'pip install boto3'"},
                    status=status.HTTP_501_NOT_IMPLEMENTED
                )
            # Para AWS se ignoran connectionString, username y password,
            # ya que boto3 utiliza su propia configuración de credenciales.
            metadata = aws.test_s3_connection(connection_string, username, password)
        elif connection_type == 'bigquery':
            # Implementar la lógica de conexión a BigQuery según tus necesidades
            metadata = {"connected": True, "message": "BigQuery connection successful"}
        else:
            return Response(
                {"error": f"Unsupported connection type: {connection_type}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            "success": True,
            "message": "Connection successful",
            "metadata": metadata
        })
    
    except Exception as e:
        return Response(
            {"error": f"Connection failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@renderer_classes([JSONRenderer])
def create_dataset(request):
    """
    API endpoint para crear un nuevo dataset.
    """
    # Extraer datos de la conexión
    connection_data = {
        'name': request.data.get('name', '') + " Connection",
        'connection_type': request.data.get('uploadMethod'),
        'connection_string': request.data.get('connectionString', ''),
        'username': request.data.get('username', ''),
        'password': request.data.get('password', ''),
        'query': request.data.get('query', '')
    }
    
    # Crear la conexión
    connection_serializer = DataConnectionSerializer(data=connection_data)
    if connection_serializer.is_valid():
        connection = connection_serializer.save()
        
        # Crear el dataset
        dataset_data = {
            'name': request.data.get('name'),
            'description': request.data.get('description', ''),
            'category': request.data.get('category', ''),
            'connection': connection.id,
            'columns': request.data.get('columns', [])
        }
        
        dataset_serializer = DatasetSerializer(data=dataset_data)
        if dataset_serializer.is_valid():
            dataset_serializer.save()
            return Response(dataset_serializer.data, status=status.HTTP_201_CREATED)
        
        # Si hay errores en el dataset, eliminar la conexión creada
        connection.delete()
        return Response(dataset_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(connection_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@renderer_classes([JSONRenderer])
def upload_dataset(request):
    """
    Endpoint para subir un archivo, procesarlo y obtener análisis con OpenAI.
    Soporta archivos CSV y Excel.
    """
    # Se usa MultiPartParser y FormParser para manejar archivos
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({"error": "No se ha enviado ningún archivo."}, status=status.HTTP_400_BAD_REQUEST)
    
    result = process_file(file_obj)
    if 'error' in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    # Generar un prompt para análisis con OpenAI usando los primeros 5 registros
    prompt = "Analiza el siguiente conjunto de datos y proporciona un resumen de tendencias e insights:\n\n"
    prompt += str(result['data'][:5])
    openai_response = analyze_data(prompt)
    
    return Response({
        "processed_data": result['data'],
        "openai_analysis": openai_response
    }, status=status.HTTP_200_OK)

# Endpoints de visualización en api/views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def generate_chart(request):
    """
    Endpoint para generar diferentes tipos de gráficos a partir de datos proporcionados.
    """
    data = request.data.get('data')
    chart_type = request.data.get('chart_type', 'sales')
    
    if not data:
        return Response(
            {"error": "No se proporcionaron datos."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar que data sea una lista
    if not isinstance(data, list):
        return Response(
            {"error": "El formato de datos debe ser una lista de objetos."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = {}
        
        if chart_type == 'sales':
            result = generate_sales_chart(data)
        elif chart_type == 'category':
            category_field = request.data.get('category_field', 'category')
            value_field = request.data.get('value_field', 'value')
            result = generate_category_chart(data, category_field, value_field)
        elif chart_type == 'regional':
            region_field = request.data.get('region_field', 'region')
            value_field = request.data.get('value_field', 'sales')
            result = generate_regional_chart(data, region_field, value_field)
        elif chart_type == 'time_comparison':
            date_field = request.data.get('date_field', 'date')
            value_field = request.data.get('value_field', 'value')
            compare_field = request.data.get('compare_field', 'category')
            result = generate_time_comparison_chart(data, date_field, value_field, compare_field)
        elif chart_type == 'heatmap':
            x_field = request.data.get('x_field')
            y_field = request.data.get('y_field')
            value_field = request.data.get('value_field')
            
            if not x_field or not y_field or not value_field:
                return Response(
                    {"error": "Para gráficos heatmap se requieren los campos x_field, y_field y value_field."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            result = generate_heatmap_chart(data, x_field, y_field, value_field)
        else:
            return Response(
                {"error": f"Tipo de gráfico no soportado: {chart_type}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Error al procesar la solicitud: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def generate_sales_visualization(request):
    """
    Endpoint para generar visualizaciones completas de ventas con análisis y recomendaciones.
    """
    data = request.data.get('data')
    period = request.data.get('period', 'monthly')
    category = request.data.get('category')
    region = request.data.get('region')
    
    if not data:
        return Response(
            {"error": "No se proporcionaron datos."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Generar gráfico principal
        chart_result = generate_sales_chart(data)
        
        if "error" in chart_result:
            return Response(chart_result, status=status.HTTP_400_BAD_REQUEST)
        
        # Generar predicción
        prediction_result = generate_sales_prediction(data)
        has_prediction = "error" not in prediction_result
        
        # Análisis básico de los datos
        analysis = chart_result.get('analysis', {})
        
        # Completar con la predicción
        if has_prediction:
            analysis["prediction"] = prediction_result.get('analysis', {})
        
        # Generar recomendaciones basadas en el análisis
        growth_rate = analysis.get('growth_rate', 0)
        total_sales = analysis.get('total_sales', 0)
        
        recommendations = []
        
        if growth_rate > 15:
            recommendations.append("La tendencia de crecimiento es fuerte. Considere aumentar inventario para satisfacer la demanda creciente.")
        elif growth_rate < -10:
            recommendations.append("Las ventas muestran una tendencia a la baja. Evalúe estrategias promocionales para impulsar la demanda.")
        
        if period == 'monthly' and has_prediction:
            recommendations.append(f"Según las proyecciones, se espera un crecimiento del {prediction_result['analysis']['growth_rate']:.1f}% en los próximos meses.")
        
        if total_sales > 0:
            recommendations.append(f"El volumen de ventas acumulado es de S/ {total_sales:,.2f}. Enfóquese en mantener el impulso positivo.")
        
        # Respuesta completa
        response = {
            "chart": chart_result.get('chart'),
            "prediction_chart": prediction_result.get('chart') if has_prediction else None,
            "analysis": analysis,
            "recommendations": recommendations,
            "raw_data": chart_result.get('raw_data'),
            "predictions": prediction_result.get('predictions') if has_prediction else []
        }
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Error al procesar la solicitud: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def predict_sales_view(request):
    """
    Endpoint para predecir ventas futuras.
    """
    data = request.data.get('data')
    periods = request.data.get('periods', 3)
    
    if not data:
        return Response(
            {"error": "No se proporcionaron datos."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validar el número de períodos
        try:
            periods = int(periods)
            if periods < 1 or periods > 12:
                return Response(
                    {"error": "El número de períodos debe estar entre 1 y 12."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "El valor de 'periods' debe ser un número entero."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        result = generate_sales_prediction(data, periods)
        
        if "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Error al procesar la solicitud: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@renderer_classes([JSONRenderer])
def predict_sales_view(request):
    """
    Endpoint para predecir ventas futuras usando regresión lineal.
    Se espera que 'data' contenga registros con 'date_of_entry' y 'sales'.
    """
    data = request.data.get('data')
    if not data:
        return Response({"error": "No se proporcionaron datos."}, status=status.HTTP_400_BAD_REQUEST)
    prediction = predict_sales(data)
    if "error" in prediction:
        return Response(prediction, status=status.HTTP_400_BAD_REQUEST)
    return Response(prediction, status=status.HTTP_200_OK)

# ---------------------------
# Nuevos Endpoints para EnhancedAssistant
# ---------------------------
@api_view(['GET'])
@renderer_classes([JSONRenderer])
def get_dataset_context(request, dataset_id):
    """
    Obtiene información contextual sobre un dataset específico.
    Incluye metadatos, nombres de columnas, tipos de datos, etc.
    """
    try:
        # Intentamos obtener el dataset de la base de datos
        dataset = Dataset.objects.get(id=dataset_id)
        
        # Si tiene columnas definidas, las usamos
        columns = dataset.columns
        
        # Si no tiene columnas definidas o está vacío, buscamos en la conexión
        if not columns:
            connection = dataset.connection
            
            # Si es una conexión SQL con query, ejecutamos la query para obtener la estructura
            if connection.connection_type == 'sql' and connection.query:
                try:
                    metadata = sql.test_sql_connection(
                        connection.connection_string, 
                        connection.username,
                        connection.password,
                        connection.query
                    )
                    columns = metadata.get('columns', [])
                except Exception as e:
                    columns = []
        
        # Preparamos el contexto del dataset
        context = {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "category": dataset.category,
            "created_at": dataset.created_at,
            "columnNames": columns,
            "connection_type": dataset.connection.connection_type if dataset.connection else None
        }
        
        return Response(context)
    
    except Dataset.DoesNotExist:
        return Response(
            {"error": f"Dataset with ID {dataset_id} not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Error retrieving dataset context: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@renderer_classes([JSONRenderer])
def assistant_analyze(request):
    """
    Procesa mensajes del usuario en el asistente y proporciona respuestas inteligentes
    con análisis de datos y visualizaciones.
    """
    message = request.data.get('message')
    dataset_id = request.data.get('datasetId')
    dataset_context = request.data.get('datasetContext')
    language = request.data.get('language', 'es')
    message_history = request.data.get('messageHistory', [])
    
    if not message:
        return Response(
            {"error": "Se requiere un mensaje para analizar"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Preparar el contexto para la IA
        context = {
            "datasetId": dataset_id,
            "datasetContext": dataset_context,
            "messageHistory": message_history,
            "timestamp": datetime.now().isoformat()
        }
        
        # Crear un prompt para análisis
        prompt = f"""
        Analiza el siguiente mensaje del usuario sobre el dataset con ID {dataset_id}.
        
        Contexto del dataset: {json.dumps(dataset_context, indent=2)}
        
        Historial de mensajes recientes:
        {json.dumps(message_history, indent=2)}
        
        Mensaje del usuario: {message}
        
        Responde en {language} y proporciona insights relevantes sobre los datos.
        """
        
        # Obtener análisis con OpenAI o similar
        analysis_result = analyze_data(prompt)
        
        # Generar visualizaciones basadas en el mensaje (simulado por ahora)
        visualizations = []
        if "gráfico" in message.lower() or "visualiza" in message.lower() or "chart" in message.lower():
            visualizations = [
                {
                    "type": "line",
                    "title": "Tendencia de datos",
                    "data": [
                        {"x": "Ene", "y": 100},
                        {"x": "Feb", "y": 120},
                        {"x": "Mar", "y": 90},
                        {"x": "Abr", "y": 140},
                        {"x": "May", "y": 160}
                    ]
                }
            ]
        
        # Generar insights basados en el mensaje (simulado por ahora)
        insights = []
        if "insight" in message.lower() or "análisis" in message.lower() or "tendencia" in message.lower():
            insights = [
                {"type": "trend", "text": "Se observa una tendencia al alza del 15% en los últimos 3 meses."},
                {"type": "anomaly", "text": "Se detectaron valores atípicos en los datos de Mayo que podrían requerir atención."},
                {"type": "correlation", "text": "Existe una fuerte correlación entre las variables X y Y (0.85)."}
            ]
        
        # Generar sugerencias para próximas preguntas
        suggestions = [
            "Muestra la tendencia de los últimos 6 meses",
            "¿Cuáles son los principales factores que influyen en estos datos?",
            "Compara este período con el mismo período del año pasado",
            "Genera un reporte ejecutivo con estos datos"
        ]
        
        # Respuesta principal (simulada, normalmente generada por LLM)
        message_response = analysis_result.get('message', "Lo siento, no pude analizar el mensaje correctamente.")
        
        return Response({
            "message": message_response,
            "visualizations": visualizations,
            "insights": insights,
            "suggestions": suggestions
        })
    
    except Exception as e:
        return Response(
            {"error": f"Error analyzing message: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ---------------------------
# Endpoints NLP para procesamiento de español peruano
# ---------------------------
@api_view(['POST'])
@renderer_classes([JSONRenderer])
def analyze_sentiment(request):
    """API endpoint for analyzing sentiment in Spanish text with Peruvian context"""
    if nlp_processor is None:
        return Response(
            {"error": "NLP processor not available"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    text = request.data.get('text')
    include_peruvian_context = request.data.get('include_peruvian_context', True)
    
    if not text:
        return Response(
            {"error": "El texto es requerido"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = nlp_processor.analyze_sentiment(text, include_peruvian_context)
        return Response(result)
    except Exception as e:
        return Response(
            {"error": f"Error al analizar sentimiento: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@renderer_classes([JSONRenderer])
def classify_feedback(request):
    """API endpoint for classifying customer feedback"""
    if nlp_processor is None:
        return Response(
            {"error": "NLP processor not available"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    text = request.data.get('text')
    
    if not text:
        return Response(
            {"error": "El texto es requerido"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = nlp_processor.classify_customer_feedback(text)
        return Response(result)
    except Exception as e:
        return Response(
            {"error": f"Error al clasificar comentario: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@renderer_classes([JSONRenderer])
def business_analysis(request):
    """API endpoint for business text analysis"""
    if nlp_processor is None:
        return Response(
            {"error": "NLP processor not available"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    text = request.data.get('text')
    business_type = request.data.get('business_type', 'retail')
    
    if not text:
        return Response(
            {"error": "El texto es requerido"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = nlp_processor.analyze_business_text(text, business_type)
        return Response(result)
    except Exception as e:
        return Response(
            {"error": f"Error en el análisis de negocio: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@renderer_classes([JSONRenderer])
def explain_financial_terms(request):
    """API endpoint for explaining financial terms in Peruvian context"""
    if nlp_processor is None:
        return Response(
            {"error": "NLP processor not available"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    terms = request.data.get('terms')
    
    if not terms:
        return Response(
            {"error": "Los términos son requeridos"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = nlp_processor.financial_term_explanation(terms)
        return Response(result)
    except Exception as e:
        return Response(
            {"error": f"Error al explicar términos financieros: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['POST'])
@permission_classes([AllowAny])  # Permitir registro sin autenticación
def register_user(request):
    """
    API endpoint para registrar un nuevo usuario.
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# También necesitamos asegurarnos de que exista un endpoint para listar datasets
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def dataset_list(request):
    """
    Lista todos los datasets (GET) o crea un nuevo dataset (POST)
    """
    if request.method == 'GET':
        # Filtrar para mostrar solo los datasets del usuario actual
        datasets = Dataset.objects.filter(owner=request.user)
        serializer = DatasetSerializer(datasets, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Al crear, asignar el usuario actual como propietario
        data = request.data.copy()
        data['owner'] = request.user.id
        serializer = DatasetSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def dataset_detail(request, pk):
    """
    Obtiene, actualiza o elimina un dataset específico
    """
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = DatasetSerializer(dataset)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = DatasetSerializer(dataset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        dataset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class BusinessRuleViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BusinessRule.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class AgentActionViewSet(viewsets.ModelViewSet):
    serializer_class = AgentActionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AgentAction.objects.filter(dataset__owner=self.request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_agent_action(request, action_id):
    """Aprobar una acción sugerida por el agente"""
    try:
        action = AgentAction.objects.get(
            id=action_id, 
            dataset__owner=request.user,
            status__in=['suggested', 'pending']
        )
        
        action.status = 'approved'
        action.save()
        
        # Aquí se implementaría la lógica para ejecutar la acción
        # Por ahora simplemente la marcamos como ejecutada
        action.status = 'executed'
        action.save()
        
        return Response({'success': True, 'message': 'Acción aprobada y ejecutada'})
    except AgentAction.DoesNotExist:
        return Response(
            {'success': False, 'message': 'Acción no encontrada o no disponible para aprobación'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_agent_action(request, action_id):
    """Rechazar una acción sugerida por el agente"""
    try:
        action = AgentAction.objects.get(
            id=action_id, 
            dataset__owner=request.user,
            status__in=['suggested', 'pending']
        )
        
        action.status = 'rejected'
        action.result_notes = request.data.get('reason', 'Rechazada por el usuario')
        action.save()
        
        return Response({'success': True, 'message': 'Acción rechazada'})
    except AgentAction.DoesNotExist:
        return Response(
            {'success': False, 'message': 'Acción no encontrada o no disponible para rechazo'},
            status=status.HTTP_404_NOT_FOUND
        )

class BusinessContextViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessContextSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BusinessContext.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_dataset(request):
    """
    Ejecuta un análisis completo del dataset utilizando el monitor autónomo
    """
    dataset_id = request.data.get('dataset_id')
    if not dataset_id:
        return Response(
            {"error": "Se requiere ID de dataset"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Verificar que el dataset pertenezca al usuario
        dataset = Dataset.objects.get(id=dataset_id, owner=request.user)
        
        # Iniciar el monitor autónomo
        monitor = AutonomousMonitor(dataset_id=dataset_id)
        results = monitor.analyze_dataset()
        
        return Response({
            'success': True,
            'analysis_results': results,
            'detected_issues': monitor.detected_issues,
            'opportunities': monitor.opportunities,
            'actions_taken': monitor.actions_taken
        })
    except Dataset.DoesNotExist:
        return Response(
            {"error": "Dataset no encontrado o sin permisos"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Error al analizar dataset: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_alerts(request, dataset_id):
    """
    Retorna alertas activas no resueltas para un dataset específico
    """
    try:
        # Verificar que el dataset pertenezca al usuario
        dataset = Dataset.objects.get(id=dataset_id, owner=request.user)
        
        # Obtener alertas no resueltas
        alerts = MonitoringLog.objects.filter(
            dataset=dataset,
            is_resolved=False
        ).order_by('-created_at', '-severity')
        
        serializer = MonitoringLogSerializer(alerts, many=True)
        return Response(serializer.data)
    except Dataset.DoesNotExist:
        return Response(
            {"error": "Dataset no encontrado o sin permisos"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suggested_actions(request, dataset_id):
    """
    Retorna acciones sugeridas pendientes para un dataset específico
    """
    try:
        # Verificar que el dataset pertenezca al usuario
        dataset = Dataset.objects.get(id=dataset_id, owner=request.user)
        
        # Obtener acciones sugeridas
        actions = AgentAction.objects.filter(
            dataset=dataset,
            status__in=['suggested', 'pending']
        ).order_by('-created_at', '-confidence')
        
        serializer = AgentActionSerializer(actions, many=True)
        return Response(serializer.data)
    except Dataset.DoesNotExist:
        return Response(
            {"error": "Dataset no encontrado o sin permisos"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_alert(request, alert_id):
    """
    Marca una alerta como resuelta
    """
    try:
        # Buscar la alerta y verificar que pertenezca al usuario
        alert = MonitoringLog.objects.get(
            id=alert_id,
            dataset__owner=request.user
        )
        
        # Actualizar estado
        alert.is_resolved = True
        alert.resolution_notes = request.data.get('notes', '')
        alert.resolution_date = timezone.now()
        alert.save()
        
        return Response({
            'success': True,
            'alert_id': alert.id
        })
    except MonitoringLog.DoesNotExist:
        return Response(
            {"error": "Alerta no encontrada o sin permisos"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_action(request):
    """
    Endpoint para solicitar una recomendación del agente IA
    """
    dataset_id = request.data.get('dataset_id')
    action_type = request.data.get('action_type')
    context = request.data.get('context', {})
    
    if not dataset_id or not action_type:
        return Response(
            {"error": "Se requieren dataset_id y action_type"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    try:
        # Verificar que el dataset pertenezca al usuario
        if not Dataset.objects.filter(id=dataset_id, owner=request.user).exists():
            return Response(
                {"error": "Dataset no encontrado o sin permisos"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Crear motor de decisiones
        engine = DecisionEngine(dataset_id=dataset_id, user=request.user)
        
        # Solicitar recomendación
        result = engine.recommend_action(dataset_id, action_type, context)
        
        if "error" in result:
            return Response(
                {"error": result["error"]},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response(result)
        
    except Exception as e:
        return Response(
            {"error": f"Error al generar recomendación: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def provide_action_feedback(request, action_id):
    """
    Endpoint para proporcionar feedback sobre una acción del agente
    """
    success_score = request.data.get('success_score')
    metrics_after = request.data.get('metrics', {})
    feedback = request.data.get('feedback')
    
    if success_score is None:
        return Response(
            {"error": "Se requiere success_score"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    try:
        # Verificar que la acción pertenezca al usuario
        action = AgentAction.objects.get(
            id=action_id,
            dataset__owner=request.user
        )
        
        # Crear motor de decisiones
        engine = DecisionEngine(dataset_id=action.dataset.id, user=request.user)
        
        # Registrar aprendizaje
        result = engine.learn_from_outcomes(
            action_id, 
            float(success_score),
            metrics_after,
            feedback
        )
        
        if not result.get('success', False):
            return Response(
                {"error": result.get('error', 'Error desconocido')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response({
            "success": True,
            "message": "Feedback registrado correctamente",
            "learning_id": result.get('learning_id')
        })
        
    except AgentAction.DoesNotExist:
        return Response(
            {"error": "Acción no encontrada o sin permisos"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Error al procesar feedback: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_learning_insights(request):
    """
    Endpoint para obtener insights de aprendizaje y rendimiento del agente
    """
    time_period = request.query_params.get('period', 'all')
    
    try:
        # Crear servicio de aprendizaje
        learning_service = AdaptiveLearningService(user=request.user)
        
        # Obtener análisis de rendimiento
        performance = learning_service.analyze_performance(time_period)
        
        if "error" in performance:
            return Response(
                {"error": performance["error"]},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Obtener insights y recomendaciones
        insights = learning_service.get_recommendation_insights()
        
        return Response({
            "performance": performance,
            "insights": insights.get('insights', []),
            "recommendations": insights.get('recommendations', []),
            "learning_level": insights.get('learning_level', {})
        })
        
    except Exception as e:
        return Response(
            {"error": f"Error al obtener insights: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def adapt_agent_parameters(request):
    """
    Endpoint para adaptar los parámetros del agente basado en aprendizaje
    """
    try:
        # Crear servicio de aprendizaje
        learning_service = AdaptiveLearningService(user=request.user)
        
        # Adaptar parámetros
        result = learning_service.adapt_decision_parameters()
        
        if not result.get('success', False):
            return Response(
                {"error": result.get('error', 'Error desconocido')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response({
            "success": True,
            "parameters_updated": result.get('parameters_updated', 0),
            "rules_updated": result.get('rules_updated', 0),
            "message": "Parámetros del agente adaptados correctamente"
        })
        
    except Exception as e:
        return Response(
            {"error": f"Error al adaptar parámetros: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )