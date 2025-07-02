#!/bin/bash

echo "========================================"
echo "   DataLens Frontend - Iniciando..."
echo "========================================"
echo

# Cambiar al directorio del script
cd "$(dirname "$0")"

echo "Verificando Node.js..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js no está instalado."
    echo "Por favor, instala Node.js desde https://nodejs.org/"
    exit 1
fi

echo "Verificando npm..."
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm no está disponible."
    exit 1
fi

echo
echo "Verificando dependencias..."
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias..."
    npm install
    if [ $? -ne 0 ]; then
        echo "ERROR: Falló la instalación de dependencias."
        exit 1
    fi
fi

echo
echo "========================================"
echo "   Iniciando servidor de desarrollo..."
echo "========================================"
echo
echo "La aplicación se abrirá en: http://localhost:3000"
echo "Backend debe estar corriendo en: http://localhost:8080"
echo
echo "Para detener el servidor, presiona Ctrl+C"
echo

npm start
