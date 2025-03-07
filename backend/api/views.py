# api/views.py
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status
from .models import DataConnection, Dataset
from .serializers import DataConnectionSerializer, DatasetSerializer

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connectors import sql

# Importación condicional para AWS
try:
    from connectors import aws
except ImportError:
    aws = None

# Importar nuevos módulos para procesamiento, gráficos y predicción
from .data_processor import process_file
from .chart_generator import generate_sales_chart
from .prediction import predict_sales
from connectors.openai_connector import analyze_data

# Importar parsers adicionales para manejo de archivos y JSON
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

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

# ---------------------------
# Nuevos Endpoints
# ---------------------------
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

@api_view(['POST'])
@renderer_classes([JSONRenderer])
def generate_chart(request):
    """
    Endpoint para generar un gráfico de ventas a partir de datos proporcionados.
    Se espera que 'data' contenga registros con 'date_of_entry' y 'sales'.
    """
    data = request.data.get('data')
    if not data:
        return Response({"error": "No se proporcionaron datos."}, status=status.HTTP_400_BAD_REQUEST)
    chart_json = generate_sales_chart(data)
    if "error" in chart_json:
        return Response(chart_json, status=status.HTTP_400_BAD_REQUEST)
    return Response(chart_json, status=status.HTTP_200_OK)

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
