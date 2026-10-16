<div align="center">

# ConversorHub

**Um aplicativo gratuito para Windows que reúne downloads autorizados e conversões de documentos, imagens, áudio e vídeo em um só lugar.**

Desenvolvido para funcionar no computador do usuário, sem conta, assinatura ou envio de arquivos a servidores do ConversorHub.

**Status: versão 0.1 em desenvolvimento — ainda não há instalador público homologado.**

</div>

---

## O que é o ConversorHub?

O **ConversorHub** é uma ferramenta de desktop com interface em português e processamento local. Você seleciona um arquivo ou fornece um link compatível, escolhe o formato de saída e define a pasta de destino.

### Funcionalidades implementadas no código

| Categoria | Conversões / operações |
| --- | --- |
| Downloads autorizados | Links compatíveis com yt-dlp para vídeo MP4/original e áudio MP3/M4A |
| Documentos Office | DOC, DOCX, PPT, PPTX, XLS, XLSX, ODT, ODP, ODS e RTF → PDF |
| PDF | PDF → DOCX (aproximado), TXT, PNG ou JPG |
| Imagens | PNG, JPG, WEBP, BMP e outros → PNG, JPG, WEBP, BMP ou PDF |
| Áudio | MP3, WAV, FLAC, OGG, M4A e outros formatos suportados pelo FFmpeg |
| Vídeo | MP4, MKV, WEBM, MP3, M4A, WAV e GIF, conforme codecs disponíveis |
| Aplicativo | Fila sequencial, histórico local, seleção de pasta e conversões em lote por categoria |

> **Importante:** implementar uma opção não significa que ela já foi homologada em todos os formatos. Consulte [TESTES-REALIZADOS.md](TESTES-REALIZADOS.md) para ver exatamente o que foi verificado.

## Como será a instalação para o público

A proposta da versão de distribuição é:

1. Baixar **ConversorHub-Setup.exe** pela área de *Releases* deste repositório.
2. Executar o instalador e seguir os passos na tela.
3. Abrir o ConversorHub pelo menu Iniciar.
4. Escolher os arquivos e a pasta onde salvar o resultado.

**O instalador completo ainda está em desenvolvimento e não está disponível nesta versão.** A meta é não exigir que o usuário instale Python, FFmpeg, yt-dlp ou LibreOffice manualmente. O Python poderá ser empacotado junto ao aplicativo; os demais componentes exigirão empacotamento/instalação apropriados, compatíveis com suas licenças.

**Pasta do aplicativo:** `%ProgramFiles%\ConversorHub` (meta para a versão instalável). **Pasta dos arquivos convertidos:** escolhida livremente pelo usuário e armazenada nas preferências locais; não é a pasta de instalação.

## Executar o projeto hoje (desenvolvedores/testadores)

A versão 0.1 exige **Windows 10/11, Python 3.11/3.12 de 64 bits** e as dependências para os recursos desejados.

```powershell
# Depois de extrair/clonar o repositório:
.\run.bat
```

- **FFmpeg:** necessário para conversões de áudio/vídeo e combinação de áudio e vídeo baixados.
- **LibreOffice:** necessário para converter arquivos do Word, Excel e PowerPoint para PDF.
- O script `instalar-ferramentas-windows.bat` auxilia na instalação desses programas em um PC de desenvolvimento; **não é um instalador final para consumidores**.
- A pasta de saída inicial do aplicativo é `Vídeos\ConversorHub` e pode ser alterada na interface.

### Gerar uma versão executável de teste

Em uma máquina Windows com Python configurado:

```bat
build-windows.bat
```

O PyInstaller prepara `dist\ConversorHub\ConversorHub.exe` e as bibliotecas Python. **Isso não cria um instalador de clique único e ainda não inclui automaticamente o LibreOffice.** Consulte as notas no código e valide os componentes externos antes de distribuir.

## Tecnologias

- **Python + CustomTkinter:** interface desktop.
- **yt-dlp:** acesso a links de plataformas compatíveis, quando o download é permitido.
- **FFmpeg:** processamento multimídia.
- **LibreOffice:** conversão de formatos Office para PDF.
- **Pillow, PyMuPDF e pdf2docx:** conversões de imagem e PDF.
- **PyInstaller:** empacotamento do executável de teste.

## Segurança e privacidade

- Conversões locais; sem exigência de conta ou upload para servidor próprio.
- Processos externos chamados sem `shell=True`.
- Histórico e preferências mantidos no computador do usuário.
- Não há promessa de contornar DRM, restrições de acesso ou proteções de plataformas.
- Baixe somente conteúdo próprio ou que você tenha autorização para usar, respeitando direitos autorais e termos de serviço.

## Limitações atuais

- PDFs digitalizados não recebem OCR automaticamente; PDF → Word pode perder fidelidade visual.
- Nem todos os formatos e codecs estão disponíveis em todos os builds do FFmpeg.
- A interface e o `.exe` ainda precisam de homologação em um Windows limpo.
- Não existe instalador final, atualizador automático nem assinatura digital nesta versão.
- Recursos e disponibilidade de plataformas externas podem mudar.

## Testes

```bash
python -m pytest -q tests
```

Resultados realizados e pendências: [TESTES-REALIZADOS.md](TESTES-REALIZADOS.md).

## Estrutura do repositório

```text
ConversorHub/
├── src/                      # Interface e mecanismo de conversão
├── tests/                    # Testes automatizados
├── run.bat                   # Executa no ambiente de desenvolvimento
├── build-windows.bat         # Gera executável de teste no Windows
├── instalar-ferramentas-windows.bat
├── requirements.txt
├── requirements-build.txt
├── TESTES-REALIZADOS.md
└── README.md
```

## Contribuições e licença

Sugestões e relatos de problemas podem ser enviados pelas *Issues* do repositório quando ele for publicado.

**Licença de distribuição do código ainda não definida.** Antes de disponibilizar publicamente, escolha e adicione um arquivo `LICENSE` (MIT, Apache-2.0, GPL etc., conforme a sua intenção). Sem licença explícita, publicar o código no GitHub **não** autoriza automaticamente terceiros a copiar, modificar ou redistribuir o projeto. As licenças dos componentes de terceiros também precisam ser respeitadas.

---

<div align="center">Feito para simplificar tarefas no Windows — sem complicação.</div>
