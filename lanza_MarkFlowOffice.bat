@echo off
setlocal
cd /d "%~dp0"
title MarkFlow Office — v1.13.0

echo ============================================================================
echo   MarkFlow Office v1.13.0 — Suite de documentos con IA (offline-first)
echo   Motor MarkFlow + nucleo GenOffice + editor visual ProseMirror
echo ============================================================================
echo.

set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    if exist "C:\Python314\python.exe" (
        set "PYTHON_EXE=C:\Python314\python.exe"
    ) else if exist "C:\Python313\python.exe" (
        set "PYTHON_EXE=C:\Python313\python.exe"
    ) else if exist "C:\Python312\python.exe" (
        set "PYTHON_EXE=C:\Python312\python.exe"
    ) else (
        set "PYTHON_EXE=python"
    )
)

set "PORT=8320"

REM Liberar puerto 8320 si quedo ocupado por una instancia previa zombi
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r /c:":8320 .*LISTENING"') do (
    echo [Office] Liberando puerto 8320 ocupado por proceso previo PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo [Office] Servidor iniciando en: http://127.0.0.1:%PORT%/
echo [Office] Shell Office: / · Motor clasico MarkFlow: /clasico
echo [Office] Abriendo navegador predeterminado...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process http://127.0.0.1:%PORT%/"
echo [Office] Para detener la aplicacion, presiona Ctrl+C o cierra esta ventana.
echo.

"%PYTHON_EXE%" -X utf8 -m uvicorn app.principal:app --host 127.0.0.1 --port %PORT%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [Office] ERROR: El servidor se ha detenido con codigo de salida %ERRORLEVEL%.
    pause
)
endlocal
