@echo off
echo =========================================
echo   Iniciant el Classificador de Peixos...
echo =========================================

:: Comprova si l'entorn virtual ja existeix. Si no, el crea i instal·la Panel.
IF NOT EXIST "venv\Scripts\activate" (
    echo.
    echo [!] Es la primera vegada que s'obre l'app.
    echo [!] Configurant el sistema per al papa... Aixo trigara un minutet.
    echo.
    python -m venv venv
    call venv\Scripts\activate
    pip install panel
) ELSE (
    :: Si ja existeix, simplement l'activa
    call venv\Scripts\activate
)

echo.
echo Obrint l'aplicacio al navegador...
panel serve main.py --show

pause
