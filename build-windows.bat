@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -r requirements-build.txt
if errorlevel 1 exit /b 1
py -3 -m PyInstaller --noconfirm --clean --windowed --name ConversorHub --paths src --collect-all customtkinter --collect-all yt_dlp --collect-all fitz --collect-all pdf2docx --collect-all PIL src\app.py
if errorlevel 1 exit /b 1
if exist bin\ffmpeg.exe copy bin\ffmpeg.exe dist\ConversorHub\ffmpeg.exe
if exist bin\ffprobe.exe copy bin\ffprobe.exe dist\ConversorHub\ffprobe.exe
echo Build gerado em dist\ConversorHub\ConversorHub.exe
pause
