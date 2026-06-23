@echo off
chcp 65001 >nul
title Construindo DocumentadorPBIX.exe...

echo ==========================================================
echo   Documentador de PBIX 1.0 — Gerador de EXE
echo ==========================================================
echo.

REM Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado.
    echo Instale o Python 3.10+ em https://www.python.org/downloads/
    echo Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo [1/4] Atualizando pip...
python -m pip install --upgrade pip --quiet

echo [2/4] Instalando dependencias...
python -m pip install pbixray "reportlab>=4.0" "graphviz>=0.20" "Pillow>=10.0" pandas numpy pyinstaller --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias. Verifique sua conexao com a internet.
    pause
    exit /b 1
)

echo [2b/4] Removendo bindings Qt conflitantes...
python -m pip uninstall PyQt5 PyQt5-sip PyQt5-Qt5 PyQt6 PyQt6-sip PyQt6-Qt6 -y --quiet 2>nul

echo [3/4] Gerando EXE com PyInstaller...
pyinstaller DocumentadorPBIX.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [ERRO] PyInstaller falhou. Veja as mensagens acima.
    pause
    exit /b 1
)

echo [4/4] Concluido!
echo.
echo ==========================================================
echo   EXE gerado em: dist\DocumentadorPBIX.exe
echo ==========================================================
echo.
echo Voce pode enviar o arquivo "DocumentadorPBIX.exe" para seus colegas.
echo Eles nao precisam ter Python instalado para usar.
echo.

REM Abre a pasta dist automaticamente
if exist "dist\DocumentadorPBIX.exe" (
    explorer dist
)

pause
