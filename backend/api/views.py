from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import DataConnection, Dataset
from .serializers import DataConnectionSerializer, DatasetSerializer

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connectors import sql

@api_view(['POST'])
def test_connection(request):
    """
    API endpoint para probar una conexión a una base de datos externa.
    """
    connection_type = request.data.get('connectionType')
    connection_string = request.data.get('connectionString')
    username = request.data.get('username')
    password = request.data.get('password')
    query = request.data.get('query')
    
    if not connection_type or not connection_string:
        return Response(
            {"error": "Connection type and connection string are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Llamar al conector apropiado según el tipo
        if connection_type == 'sql':
            metadata = sql.test_sql_connection(connection_string, username, password, query)
        elif connection_type == 'aws':
            # Implementar para aws
            metadata = {"connected": True, "message": "AWS connection successful"}
        elif connection_type == 'bigquery':
            # Implementar para bigquery
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