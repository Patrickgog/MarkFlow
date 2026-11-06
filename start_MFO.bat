@echo off
title MarkFlow Office — Lanzador v1.13.0
setlocal enabledelayedexpansion

:: Desplazarse al directorio del script
cd /d "%~dp0"

set "APP_NAME=MarkFlow Office"
set "ABREV=MFO"
set "VERSION=v1.13.0"
set "ROOT_DIR=%~dp0"
set "VENV_DIR=%ROOT_DIR%.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

echo ============================================================================
echo   %APP_NAME% %VERSION% [%ABREV%] — Suite de documentos con IA
echo   Arranque seguro con deteccion dinamica de entorno y puerto libre
echo ============================================================================
echo.

:: ============================================================================
:: 1. Deteccion de entorno de ejecucion exhaustiva (3.15 -> 3.10)
:: ============================================================================
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

:: Si existe .venv local, priorizar su intérprete
if exist "%PYTHON_EXE%" (
    set "PYTHON_CMD=%PYTHON_EXE%"
) else (
    echo [INFO] No se encontro entorno virtual en .venv. Creando entorno nuevo...
    "%PYTHON_CMD%" -m venv "%VENV_DIR%"
    if !ERRORLEVEL! equ 0 (
        set "PYTHON_CMD=%PYTHON_EXE%"
        echo [OK] Entorno virtual creado exitosamente.
    ) else (
        echo [ADVERTENCIA] No se pudo crear el entorno virtual; usando Python global.
    )
)

:: ============================================================================
:: 2. Verificacion preventiva de dependencias
:: ============================================================================
echo [1/3] Verificando dependencias criticas de MarkFlow Office...
"%PYTHON_CMD%" -c "import fastapi, uvicorn, jinja2, docx, bs4" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [ALERTA] Faltan librerias requeridas. Instalando dependencias desatendidas...
    "%PYTHON_CMD%" -m pip install -q --upgrade pip >nul 2>&1
    "%PYTHON_CMD%" -m pip install -r "%ROOT_DIR%requirements.txt"
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Fallo la instalacion de dependencias. Verifique conexion a internet.
        pause
        exit /b 1
    )
    echo [OK] Dependencias instaladas satisfactoriamente.
) else (
    echo [OK] Dependencias verificadas y listas.
)

:: ============================================================================
:: 3. Control y escaneo de puertos dinamico
:: ============================================================================
set "HOST_IP=127.0.0.1"
set "PORT=8320"

:find_free_port
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul 2>&1
if !ERRORLEVEL! equ 0 (
    set /a PORT+=1
    goto find_free_port
)

echo.
echo [2/3] Puerto libre localizado: %PORT%
echo [3/3] Servidor iniciando en: http://%HOST_IP%:%PORT%/
echo       - Interfaz Shell Office:   http://%HOST_IP%:%PORT%/
echo       - Motor clasico MarkFlow:  http://%HOST_IP%:%PORT%/clasico
echo.

:: ============================================================================
:: 4. Apertura asistida de navegador
:: ============================================================================
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process http://%HOST_IP%:%PORT%/"

:: ============================================================================
:: 5. Ejecucion segura de servidor ASGI FastAPI
:: ============================================================================
echo [INFO] Servidor activo. Presione Ctrl+C o cierre esta ventana para detener.
echo.

"%PYTHON_CMD%" -X utf8 -m uvicorn app.principal:app --host %HOST_IP% --port %PORT%

if !ERRORLEVEL! neq 0 (
    echo.
    echo [ERROR] El servidor finalizo con codigo de error !ERRORLEVEL!.
    pause
)

endlocal
