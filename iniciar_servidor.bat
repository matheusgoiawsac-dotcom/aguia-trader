@echo off
title Águia Trader - Servidor Python 3.11
cd /d "%~dp0"
cls
echo =================================================================
echo   [Águia Trader] Iniciando Servidor Python 3.11...
echo =================================================================
echo.
echo Abrindo dashboard no navegador padrao em http://localhost:8000 ...
start "" http://localhost:8000
echo.
python app.py
pause
