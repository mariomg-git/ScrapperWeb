@echo off
echo ============================================================
echo            SISTEMA DE WEB SCRAPING
echo ============================================================
echo.

cd /d "%~dp0"

if exist venv\Scripts\python.exe (
    echo Usando entorno virtual...
    venv\Scripts\python.exe main.py
) else (
    echo Usando Python del sistema...
    python main.py
)

echo.
pause
