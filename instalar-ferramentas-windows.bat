@echo off
setlocal
ECHO Instalando dependencias externas do ConversorHub...
ECHO FFmpeg: conversao de video e audio.
winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
ECHO LibreOffice: Word, Excel e PowerPoint para PDF.
winget install --id TheDocumentFoundation.LibreOffice -e --accept-package-agreements --accept-source-agreements
ECHO Pronto. Feche e reabra o ConversorHub para detectar as ferramentas.
pause
