#!/usr/bin/env python
"""
Script para inicializar la base de datos con datos de prueba.
Este script crea productos de muestra para poder probar el bot.
"""

import sys
import os
from datetime import datetime

# Añadir la ruta del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine, Base, get_db
from app.db.models import Product
from sqlalchemy.orm import Session

def seed_products():
    """
    Crea productos de prueba en la base de datos.
    """
    # Crear una sesión
    db = next(get_db())
    
    # Verificar si ya existen productos
    existing_products = db.query(Product).count()
    if existing_products > 0:
        print(f"Ya existen {existing_products} productos en la base de datos.")
        choice = input("¿Deseas eliminar los productos existentes y crear nuevos? (s/n): ")
        if choice.lower() != 's':
            print("Operación cancelada.")
            return
        
        # Eliminar productos existentes
        db.query(Product).delete()
        db.commit()
        print("Productos existentes eliminados.")
    
    # Lista de productos de muestra
    sample_products = [
        {
            "name": "Pizza Familiar",
            "code": "A01",
            "price": 45.90,
            "description": "Pizza grande (8 porciones) con hasta 3 ingredientes a elección",
            "stock": 100,
            "is_active": True
        },
        {
            "name": "Pizza Mediana",
            "code": "A02",
            "price": 35.90,
            "description": "Pizza mediana (6 porciones) con hasta 2 ingredientes a elección",
            "stock": 100,
            "is_active": True
        },
        {
            "name": "Pizza Personal",
            "code": "A03",
            "price": 19.90,
            "description": "Pizza personal (4 porciones) con 1 ingrediente a elección",
            "stock": 100,
            "is_active": True
        },
        {
            "name": "Lasagna de Carne",
            "code": "B01",
            "price": 28.90,
            "description": "Porción individual de lasagna de carne con salsa boloñesa",
            "stock": 50,
            "is_active": True
        },
        {
            "name": "Spaghetti Carbonara",
            "code": "B02",
            "price": 24.90,
            "description": "Spaghetti con salsa carbonara, tocino y queso parmesano",
            "stock": 50,
            "is_active": True
        },
        {
            "name": "Gaseosa 1L",
            "code": "C01",
            "price": 7.90,
            "description": "Gaseosa de 1 litro (Coca-Cola, Inca Kola, Sprite)",
            "stock": 200,
            "is_active": True
        },
        {
            "name": "Agua Mineral 500ml",
            "code": "C02",
            "price": 3.90,
            "description": "Botella de agua mineral sin gas de 500ml",
            "stock": 200,
            "is_active": True
        }
    ]
    
    # Insertar productos en la base de datos
    for product_data in sample_products:
        product = Product(**product_data)
        db.add(product)
    
    db.commit()
    print(f"Se han creado {len(sample_products)} productos de muestra en la base de datos.")

def init_db():
    """
    Inicializa la base de datos creando las tablas definidas en los modelos.
    """
    Base.metadata.create_all(bind=engine)
    print("Base de datos inicializada.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Inicializa la base de datos con datos de prueba")
    parser.add_argument("--only-schema", action="store_true", help="Solo crear el esquema sin datos de prueba")
    
    args = parser.parse_args()
    
    # Inicializar la base de datos (crear tablas)
    init_db()
    
    # Si no se especificó --only-schema, también crear datos de prueba
    if not args.only_schema:
        seed_products()