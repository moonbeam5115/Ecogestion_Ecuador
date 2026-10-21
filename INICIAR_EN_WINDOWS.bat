@echo off
setlocal
cd /d "%~dp0"
echo.
echo  EcoGestion EC - Prototipo local
 echo  ------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual de Python...
    py -3 -m venv .venv 2>nul
    if errorlevel 1 python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Instala Python 3.10 o superior y vuelve a intentar.
    pause
    exit /b 1
)
echo Instalando o comprobando dependencias...
".venv\Scripts\python.exe" -m pip --isolated install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar dependencias. Revisa la conexion a Internet.
    pause
    exit /b 1
)
echo Abriendo la aplicacion local... (Ctrl+C para detener)
".venv\Scripts\python.exe" -m streamlit run app.py
pause
