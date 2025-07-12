#!/bin/bash

# Script para configurar la base de datos completa con datos de prueba

echo "🚀 Iniciando configuración de la base de datos..."

# Salir del shell de Python si está activo
python -c "exit()" 2>/dev/null || true

# Navegar al directorio del proyecto
cd /Users/juandiegogutierrezcortez/mvp

echo "📝 Creando migraciones para nuevos modelos..."
python manage.py makemigrations inventory

echo "🔄 Aplicando migraciones..."
python manage.py migrate

echo "👤 Asegurando que existe un superusuario..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='superadmin@datalens.com').exists():
    User.objects.create_superuser(
        email='superadmin@datalens.com',
        password='admin123',
        first_name='Super',
        last_name='Admin'
    )
    print('✅ Superusuario creado')
else:
    print('✅ Superusuario ya existe')
"

echo "🏗️ Creando datos de prueba..."
python create_test_data.py

echo "🎉 ¡Configuración completada!"
echo ""
echo "📊 Tu sistema ahora tiene:"
echo "   - Base de datos migrada"
echo "   - Superusuario: superadmin@datalens.com / admin123"
echo "   - Datos de prueba completos"
echo ""
echo "🚀 Para iniciar el servidor:"
echo "   python manage.py runserver 0.0.0.0:8080"
echo ""
echo "🌐 Accede a:"
echo "   - Frontend: http://localhost:8081"
echo "   - Backend API: http://localhost:8080"
echo "   - Admin Django: http://localhost:8080/admin"