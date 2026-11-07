@echo off
title MarkFlow Office - Lanzador v1.23.2
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "APP_NAME=MarkFlow Office"
set "ABREV=MFO"
set "VERSION=v1.23.2"
set "ROOT_DIR=%~dp0"
set "VENV_DIR=%ROOT_DIR%.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "HOST_IP=127.0.0.1"
set "PORT=8320"

echo ============================================================================
echo   %APP_NAME% %VERSION% [%ABREV%] - Suite de documentos con IA
echo   Arranque seguro con deteccion dinamica de entorno y puerto libre
echo ============================================================================

:: Deteccion de entorno de ejecucion (3.15 -> 3.10) con else-if correcto
set "PYTHON_CMD=python"
if exist "C:\Python315\python.exe" (
    set "PYTHON_CMD=C:\Python315\python.exe"
) else if exist "C:\Python314\python.exe" (
    set "PYTHON_CMD=C:\Python314\python.exe"
) else if exist "C:\Python313\python.exe" (
    set "PYTHON_CMD=C:\Python313\python.exe"
) else if exist "C:\Python312\python.exe" (
    set "PYTHON_CMD=C:\Python312\python.exe"
) else if exist "C:\Python311\python.exe" (
    set "PYTHON_CMD=C:\Python311\python.exe"
) else if exist "C:\Python310\python.exe" (
    set "PYTHON_CMD=C:\Python310\python.exe"
)

if exist "%PYTHON_EXE%" set "PYTHON_CMD=%PYTHON_EXE%"

:: Verificacion preventiva de dependencias
"%PYTHON_CMD%" -c "import fastapi, uvicorn, jinja2, docx" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [INFO] Instalando dependencias...
    "%PYTHON_CMD%" -m pip install -q --upgrade pip >nul 2>&1
    "%PYTHON_CMD%" -m pip install -r "%ROOT_DIR%requirements.txt"
)

:: Puerto libre
:find_free_port
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul 2>&1
if !ERRORLEVEL! equ 0 (set /a PORT+=1 & goto find_free_port)

echo [INFO] Puerto libre: %PORT%
echo [INFO] URL: http://%HOST_IP%:%PORT%/

:: Abrir navegador (tras 2 segundos)
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process http://%HOST_IP%:%PORT%/"

:: Lanzamiento directo (evita errores de Windows Terminal con rutas anidadas)
title %APP_NAME%
"%PYTHON_CMD%" -X utf8 -m uvicorn app.principal:app --host %HOST_IP% --port %PORT%
endlocal