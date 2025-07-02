@echo off
echo ========================================
echo    DataLens Frontend - Iniciando...
echo ========================================
echo.

cd /d "%~dp0"

echo Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no está instalado.
    echo Por favor, instala Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

echo Verificando npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: npm no está disponible.
    pause
    exit /b 1
)

echo.
echo Verificando dependencias...
if not exist "node_modules" (
    echo Instalando dependencias...
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Falló la instalación de dependencias.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo   Iniciando servidor de desarrollo...
echo ========================================
echo.
echo La aplicación se abrirá en: http://localhost:3000
echo Backend debe estar corriendo en: http://localhost:8080
echo.
echo Para detener el servidor, presiona Ctrl+C
echo.

npm start

pause
