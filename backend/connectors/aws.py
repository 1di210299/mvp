import boto3
from botocore.exceptions import ClientError

def test_s3_connection(bucket_name, access_key, secret_key, region='us-east-1'):
    """
    Prueba una conexión a AWS S3 y devuelve metadatos sobre el bucket.

    Parámetros:
      bucket_name (str): Nombre del bucket. Puede incluir o no el prefijo "s3://".
      access_key (str): Clave de acceso de AWS.
      secret_key (str): Clave secreta de AWS.
      region (str): Región de AWS (por defecto 'us-east-1').

    Retorna:
      dict: Diccionario con el estado de la conexión, nombre del bucket, región y una lista de archivos de muestra.

    Lanza:
      Exception: Con mensajes descriptivos en caso de error en la conexión o validación.
    """
    if not bucket_name:
        raise Exception("El nombre del bucket es obligatorio")
    
    # Eliminar el prefijo "s3://" si está presente
    if bucket_name.startswith('s3://'):
        bucket_name = bucket_name[5:]
    
    try:
        # Crear cliente S3 con las credenciales y región especificadas
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Verificar que el bucket existe mediante head_bucket
        s3_client.head_bucket(Bucket=bucket_name)
        
        # Listar hasta 5 objetos en el bucket
        objects_response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        
        metadata = {
            "connected": True,
            "bucket": bucket_name,
            "region": region,
            "sample_files": []
        }
        
        # Si hay objetos en el bucket, se agregan a sample_files
        if 'Contents' in objects_response:
            for obj in objects_response['Contents']:
                metadata["sample_files"].append({
                    "key": obj.get('Key'),
                    "size": obj.get('Size'),
                    "last_modified": obj.get('LastModified').strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return metadata
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            raise Exception(f"El bucket {bucket_name} no existe")
        elif error_code == '403':
            raise Exception("Acceso denegado. Verifica tus credenciales AWS")
        else:
            raise Exception(f"Error AWS: {str(e)}")
    except Exception as e:
        raise Exception(f"Error al conectar con AWS S3: {str(e)}")
