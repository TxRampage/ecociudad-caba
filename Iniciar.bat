@echo off
title EcoCiudad CABA - Scanner de Residuos IA
cd /d "%~dp0"

echo =======================================================
echo    EcoCiudad CABA - Scanner de Residuos con IA
echo    IFTS N 11 - Tecnicatura en Ciencia de Datos e IA
echo =======================================================
echo.
echo Iniciando servidor Streamlit en http://localhost:8501 ...
echo.

python -m streamlit run app.py --server.port 8501

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al intentar iniciar Streamlit.
    echo Asegurate de tener instaladas las dependencias con:
    echo pip install -r requirements.txt
    echo.
    pause
)