@echo off
chcp 65001 >nul
title Águia Trader - Atualização de Dados de Mercado

cd /d "%~dp0"
cls
echo =================================================================
echo   [Águia Trader] Atualizador de Dados B3
echo =================================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente .venv nao encontrado. Execute setup.bat primeiro.
    pause
    exit /b 1
)

call .\.venv\Scripts\activate.bat

echo [*] Executando rotina de atualizacao...
python -m aguia.jobs.refresh --tf 1d %*

echo.
echo =================================================================
echo   [Águia Trader] Concluido.
echo =================================================================
pause
