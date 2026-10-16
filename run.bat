@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha ao instalar dependencias. Verifique se Python 3.11/3.12 esta instalado.
  pause
  exit /b 1
)
py -3 src\app.py
