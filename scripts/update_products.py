#!/usr/bin/env python3
"""
Utilidad para actualizar productos desde archivos CSV o JSON

Este script permite a la empresa actualizar su catálogo de productos
y/o información corporativa a partir de archivos externos.
"""

import sys
import os
import argparse
import json
import csv
import requests
import logging
from pathlib import Path
from datetime import datetime

# Añadir el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('update_products')

def upload_documentation(api_url, company_file=None, products_file=None):
    """
    Sube documentación a través de la API REST
    
    Args:
        api_url: URL base de la API
        company_file: Ruta al archivo con información de empresa (JSON o CSV)
        products_file: Ruta al archivo con lista de productos (JSON o CSV)
    
    Returns:
        dict: Respuesta del servidor
    """
    endpoint = f"{api_url}/products/upload-documentation"
    
    files = {}
    if company_file:
        files['company_info'] = (
            os.path.basename(company_file),
            open(company_file, 'rb'),
            'application/octet-stream'
        )
    
    if products_file:
        files['products_list'] = (
            os.path.basename(products_file),
            open(products_file, 'rb'),
            'application/octet-stream'
        )
    
    try:
        response = requests.post(endpoint, files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error al subir documentación: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"Error al subir documentación: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        logger.error(f"Error de conexión: {str(e)}")
        return {
            "status": "error",
            "message": f"Error de conexión: {str(e)}"
        }

def batch_update_products(api_url, products_data):
    """
    Actualiza productos en lote a través de la API REST
    
    Args:
        api_url: URL base de la API
        products_data: Lista de diccionarios con datos de productos
    
    Returns:
        dict: Respuesta del servidor
    """
    endpoint = f"{api_url}/products/batch-update"
    
    try:
        response = requests.post(
            endpoint, 
            json=products_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error al actualizar productos: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"Error al actualizar productos: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        logger.error(f"Error de conexión: {str(e)}")
        return {
            "status": "error",
            "message": f"Error de conexión: {str(e)}"
        }

def load_products_from_file(file_path):
    """
    Carga productos desde un archivo CSV o JSON
    
    Args:
        file_path: Ruta al archivo de productos
    
    Returns:
        list: Lista de productos
    """
    try:
        path = Path(file_path)
        if not path.exists():
            logger.error(f"El archivo {file_path} no existe")
            return None
        
        file_extension = path.suffix.lower()
        products_data = []
        
        # Procesar según el tipo de archivo
        if file_extension == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                products_data = json.load(f)
        elif file_extension == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                products_data = list(reader)
        else:
            logger.error(f"Formato de archivo no soportado: {file_extension}. Use CSV o JSON.")
            return None
        
        return products_data
    
    except Exception as e:
        logger.error(f"Error cargando productos desde archivo: {str(e)}")
        return None

def get_product_updates(api_url, since_date=None):
    """
    Obtiene productos actualizados desde la API REST
    
    Args:
        api_url: URL base de la API
        since_date: Fecha desde la cual buscar actualizaciones (formato ISO)
    
    Returns:
        dict: Respuesta del servidor con productos actualizados
    """
    endpoint = f"{api_url}/products/updates"
    
    params = {}
    if since_date:
        params["since"] = since_date
    
    try:
        response = requests.get(endpoint, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error al obtener actualizaciones: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"Error al obtener actualizaciones: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        logger.error(f"Error de conexión: {str(e)}")
        return {
            "status": "error",
            "message": f"Error de conexión: {str(e)}"
        }

def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Herramienta para actualizar productos desde archivos CSV o JSON"
    )
    
    parser.add_argument(
        "--api", 
        default="http://localhost:8000/api",
        help="URL base de la API"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: upload
    upload_parser = subparsers.add_parser(
        "upload", 
        help="Subir documentación de empresa y/o productos"
    )
    upload_parser.add_argument(
        "--company", 
        help="Archivo con información de la empresa (JSON o CSV)"
    )
    upload_parser.add_argument(
        "--products", 
        help="Archivo con lista de productos (JSON o CSV)"
    )
    
    # Comando: update
    update_parser = subparsers.add_parser(
        "update", 
        help="Actualizar productos directamente"
    )
    update_parser.add_argument(
        "file", 
        help="Archivo con datos de productos a actualizar (JSON o CSV)"
    )
    
    # Comando: check
    check_parser = subparsers.add_parser(
        "check", 
        help="Verificar productos actualizados recientemente"
    )
    check_parser.add_argument(
        "--since", 
        help="Fecha desde la cual buscar actualizaciones (formato ISO: YYYY-MM-DDTHH:MM:SS)"
    )
    check_parser.add_argument(
        "--output", 
        help="Archivo donde guardar los resultados (JSON)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Ejecutar comando según la opción seleccionada
    if args.command == "upload":
        if not args.company and not args.products:
            logger.error("Debe proporcionar al menos un archivo (--company o --products)")
            sys.exit(1)
        
        result = upload_documentation(
            api_url=args.api,
            company_file=args.company,
            products_file=args.products
        )
        
        print(json.dumps(result, indent=2))
    
    elif args.command == "update":
        products_data = load_products_from_file(args.file)
        
        if not products_data:
            logger.error("No se pudieron cargar productos desde el archivo")
            sys.exit(1)
        
        result = batch_update_products(args.api, products_data)
        print(json.dumps(result, indent=2))
    
    elif args.command == "check":
        result = get_product_updates(args.api, args.since)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"Resultados guardados en {args.output}")
        else:
            print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()