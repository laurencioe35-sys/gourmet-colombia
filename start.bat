@echo off
title GourmetPOS ERP - Iniciando...
cd /d "%~dp0"

echo.
echo ================================================
echo   GourmetPOS ERP v2.0
echo   Backend FastAPI + Frontend + WhatsApp Bot
echo ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado.
    echo Instala Python desde https://python.org
    pause
    exit /b 1
)

if not exist ".env" (
    echo Creando archivo .env desde plantilla...
    copy ".env.example" ".env" >nul
)

echo Verificando dependencias...
pip install fastapi "uvicorn[standard]" sqlalchemy pydantic python-dotenv httpx aiofiles --quiet 2>nul

:: Detectar puerto libre
set PORT=8000
netstat -an | find "0.0.0.0:8000" >nul 2>&1
if not errorlevel 1 (
    set PORT=8001
    echo Puerto 8000 ocupado, usando 8001...
)

for /f "usebackq delims=" %%i in (`powershell -NoLogo -NoProfile -Command "$ips = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notmatch '127.0.0.1' -and $_.IPAddress -notmatch '^169\.254\.' }; if ($ips) { $ips[0].IPAddress } else { 'localhost' }" 2^>nul`) do set LAN_IP=%%i

if not defined LAN_IP set LAN_IP=localhost

set OPEN_URL=http://%LAN_IP%:%PORT%

if "%LAN_IP%"=="localhost" set OPEN_URL=http://localhost:%PORT%

echo.
echo ------------------------------------------------
echo   Red local:  %OPEN_URL%
echo   Dashboard:  %OPEN_URL%
echo   POS:        %OPEN_URL%/pos.html
echo   Cocina:     %OPEN_URL%/cocina.html
echo   Reportes:   %OPEN_URL%/reportes.html
echo   WhatsApp:   %OPEN_URL%/whatsapp.html
echo   API Docs:   %OPEN_URL%/docs
echo ------------------------------------------------
echo.
echo Presiona Ctrl+C para detener
echo.

start /b cmd /c "timeout /t 3 /nobreak >nul && start %OPEN_URL%"

python -m uvicorn backend.main:app --host 0.0.0.0 --port %PORT% --reload

pause
