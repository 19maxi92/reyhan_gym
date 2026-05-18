@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  build.bat — Genera SistemaReyhan.exe
REM  Ejecutar desde la carpeta del proyecto (donde está main.py)
REM  Requiere: Python 3.8+ instalado y en el PATH
REM ═══════════════════════════════════════════════════════════════════════════

echo.
echo  ██████╗ ███████╗██╗   ██╗██╗  ██╗ █████╗ ███╗   ██╗
echo  ██╔══██╗██╔════╝╚██╗ ██╔╝██║  ██║██╔══██╗████╗  ██║
echo  ██████╔╝█████╗   ╚████╔╝ ███████║███████║██╔██╗ ██║
echo  ██╔══██╗██╔══╝    ╚██╔╝  ██╔══██║██╔══██║██║╚██╗██║
echo  ██║  ██║███████╗   ██║   ██║  ██║██║  ██║██║ ╚████║
echo  ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
echo  Sistema de Gestión — Build Script
echo.

echo [1/3] Instalando dependencias...
pip install pyinstaller python-dateutil pyserial screeninfo pillow --quiet
if %errorlevel% neq 0 (
    echo ERROR: Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo [2/3] Generando ejecutable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "SistemaReyhan" ^
    --icon "icon\reyhan.ico" ^
    --add-data "db;db" ^
    --add-data "ui;ui" ^
    --add-data "core;core" ^
    --add-data "icon;icon" ^
    --hidden-import "screeninfo" ^
    --hidden-import "serial" ^
    --hidden-import "dateutil" ^
    main.py

if %errorlevel% neq 0 (
    echo ERROR: Fallo la generacion del ejecutable.
    pause
    exit /b 1
)

echo [3/3] Listo.
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   Ejecutable generado en:  dist\SistemaReyhan.exe
echo.
echo   Para instalar en la notebook del gym:
echo   1. Copiar  dist\SistemaReyhan.exe  a la notebook
echo   2. Doble click para ejecutar (crea gym.db y C:\backup_gym solo)
echo   3. Crear acceso directo en el escritorio
echo   4. Opcional: agregar al inicio de Windows para que arranque solo
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
