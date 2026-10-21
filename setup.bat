@echo off
chcp 65001 >nul
title Águia Trader - Instalação e Configuração

cd /d "%~dp0"
echo =================================================================
echo   [Águia Trader] Configurando Ambiente Python 3.11...
echo =================================================================
echo.

py -3.11 --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python 3.11 nao encontrado no sistema.
    echo Instale o Python 3.11 para continuar.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [*] Criando ambiente virtual .venv...
    py -3.11 -m venv .venv
)

echo [*] Ativando ambiente virtual...
call .\.venv\Scripts\activate.bat

echo [*] Atualizando pip e instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

if not exist "vendor" mkdir vendor
if not exist "vendor\Kronos\.git" (
    echo [*] Clonando repositorio Kronos no vendor...
    git clone https://github.com/shiyu-coder/Kronos vendor\Kronos
)

echo.
echo =================================================================
echo   [Águia Trader] Instalacao concluida com sucesso!
echo =================================================================
echo.
pause
