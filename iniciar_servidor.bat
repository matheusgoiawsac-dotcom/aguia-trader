@echo off
chcp 65001 >nul
title Águia Trader - Servidor Quantitativo B3

cd /d "%~dp0"
cls
echo =================================================================
echo   [Águia Trader] Inicializando Servidor Local (127.0.0.1:8000)...
echo =================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [AVISO] Ambiente .venv nao encontrado. Executando setup.bat primeiro...
    call setup.bat
)

echo [*] Iniciando backend Python 3.11...
start "AguiaTraderBackend" /min "%~dp0.venv\Scripts\python.exe" "%~dp0app.py"

echo [*] Aguardando prontidao do servidor em http://127.0.0.1:8000/api/status...
powershell -NoProfile -Command "$ready = $false; for ($i=0; $i -lt 30; $i++) { try { $res = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/status' -TimeoutSec 1; if ($res.status -eq 'online') { $ready = $true; break } } catch {}; Start-Sleep -Milliseconds 500 }; if ($ready) { Write-Host ' [*] Servidor pronto!' -ForegroundColor Green } else { Write-Host ' [!] Timeout aguardando servidor.' -ForegroundColor Yellow }"

echo [*] Abrindo dashboard no navegador padrao...
start "" http://127.0.0.1:8000

echo.
echo =================================================================
echo   Servidor ativo em http://127.0.0.1:8000 (ou http://localhost:8000)
echo   Deixe esta janela aberta enquanto utiliza o dashboard.
echo =================================================================
echo.
pause
