# Verificação realizada no ambiente atual (Linux)

- `python -m compileall src`: OK
- `pytest tests`: 4 testes OK
- PNG com transparência → JPG: OK
- PNG → PDF: OK
- PDF → PNG: OK
- PDF → TXT: OK
- DOCX → PDF via LibreOffice headless: OK, documento real de teste
- WAV → MP3 via FFmpeg: OK, arquivo real de teste

## Não validado ainda

- Executável `.exe` / instalador em um Windows físico (a compilação Windows requer ambiente Windows).
- Interface gráfica aberta (ambiente sem desktop gráfico e sem CustomTkinter).
- PDF → DOCX (a dependência pdf2docx não está instalada neste ambiente).
- Downloads em plataformas externas (ambiente sem acesso à internet para teste).
- PPTX/XLSX para PDF, formatos alternativos, arquivos corrompidos, arquivos grandes e autenticação de sites.

**Aprovação para distribuição pública requer testes em Windows limpo.**
