"""Local conversion engine. Commands are argument arrays, never shell strings."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from typing import Callable

IMAGE_TYPES = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif', '.gif'}
OFFICE_TYPES = {'.doc', '.docx', '.odt', '.ppt', '.pptx', '.odp', '.xls', '.xlsx', '.ods', '.rtf'}
VIDEO_TYPES = {'.mp4', '.mkv', '.mov', '.webm', '.avi', '.m4v'}
AUDIO_TYPES = {'.mp3', '.m4a', '.wav', '.flac', '.ogg', '.opus', '.aac', '.wma'}
SUPPORTED_OUTPUTS = {
    'image': ['PNG', 'JPG', 'WEBP', 'BMP', 'PDF'],
    'pdf': ['DOCX', 'PNG', 'JPG', 'TXT'],
    'office': ['PDF'],
    'video': ['MP4', 'MKV', 'WEBM', 'MP3', 'M4A', 'WAV', 'GIF'],
    'audio': ['MP3', 'M4A', 'WAV', 'FLAC', 'OGG'],
}


class ConversionError(Exception):
    pass


class Cancelled(Exception):
    pass


def classify_file(path: str | Path) -> str | None:
    suffix = Path(path).suffix.lower()
    if suffix == '.pdf': return 'pdf'
    if suffix in IMAGE_TYPES: return 'image'
    if suffix in OFFICE_TYPES: return 'office'
    if suffix in VIDEO_TYPES: return 'video'
    if suffix in AUDIO_TYPES: return 'audio'
    return None


def tool_path(name: str) -> str | None:
    """Prefer a binary beside the installed app; fall back to PATH."""
    bases = [Path(sys.executable).parent, Path(__file__).resolve().parent.parent / 'bin']
    if getattr(sys, '_MEIPASS', None): bases.insert(0, Path(sys._MEIPASS) / 'bin')
    options = {'ffmpeg': ['ffmpeg.exe', 'ffmpeg'], 'ffprobe': ['ffprobe.exe', 'ffprobe'],
               'soffice': ['soffice.exe', 'soffice', 'libreoffice']}
    for base in bases:
        for opt in options.get(name, [name]):
            p = base / opt
            if p.is_file(): return str(p)
    p = shutil.which(name)
    if p: return p
    if name == 'soffice' and os.name == 'nt':
        for root in [os.getenv('PROGRAMFILES'), os.getenv('PROGRAMFILES(X86)')]:
            if root:
                p = Path(root) / 'LibreOffice' / 'program' / 'soffice.exe'
                if p.exists(): return str(p)
    return None


def check_dependencies() -> dict[str, bool]:
    return {'FFmpeg': bool(tool_path('ffmpeg')),
            'LibreOffice': bool(tool_path('soffice')),
            'yt-dlp': bool(importlib.util.find_spec('yt_dlp')),
            'Pillow': bool(importlib.util.find_spec('PIL')),
            'PyMuPDF': bool(importlib.util.find_spec('fitz')),
            'pdf2docx': bool(importlib.util.find_spec('pdf2docx'))}


def unique_path(path: Path) -> Path:
    if not path.exists(): return path
    i = 2
    while True:
        p = path.with_name(f'{path.stem} ({i}){path.suffix}')
        if not p.exists(): return p
        i += 1


def validate_output_dir(value: str | Path) -> Path:
    dest = Path(value).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    if not dest.is_dir(): raise ConversionError('O destino não é uma pasta válida.')
    return dest


def run_process(args: list[str], cancel: threading.Event | None = None, progress: Callable[[str], None] | None = None) -> None:
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, errors='replace', bufsize=1, creationflags=flags)
    lines = []
    try:
        for line in proc.stdout:
            if cancel and cancel.is_set():
                proc.terminate()
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired: proc.kill()
                raise Cancelled('Tarefa cancelada.')
            lines.append(line.rstrip())
            if len(lines) > 35: lines.pop(0)
            if progress: progress(line.strip())
        code = proc.wait()
        if cancel and cancel.is_set(): raise Cancelled('Tarefa cancelada.')
        if code:
            raise ConversionError('\n'.join(lines[-6:]) or f'O processo terminou com código {code}.')
    finally:
        if proc.poll() is None: proc.kill()
        if proc.stdout: proc.stdout.close()


def convert_image(source: Path, fmt: str, dest: Path) -> list[Path]:
    from PIL import Image, ImageOps
    if fmt not in SUPPORTED_OUTPUTS['image']: raise ConversionError('Formato não suportado.')
    target = unique_path(dest / (source.stem + '.' + ('jpg' if fmt == 'JPG' else fmt.lower())))
    with Image.open(source) as original:
        img = ImageOps.exif_transpose(original)
        if fmt in ('JPG', 'PDF'):
            if img.mode in ('RGBA', 'LA') or ('transparency' in img.info):
                canvas = Image.new('RGB', img.size, '#ffffff')
                canvas.paste(img.convert('RGBA'), mask=img.convert('RGBA').getchannel('A'))
                img = canvas
            else: img = img.convert('RGB')
        if fmt == 'BMP': img = img.convert('RGB')
        kwargs = {'quality': 92} if fmt in ('JPG', 'WEBP') else {}
        img.save(target, format={'JPG':'JPEG'}.get(fmt,fmt), **kwargs)
    return [target]


def convert_pdf(source: Path, fmt: str, dest: Path, cancel=None) -> list[Path]:
    import fitz
    if fmt == 'DOCX':
        try: from pdf2docx import Converter
        except ImportError as e: raise ConversionError('Instale pdf2docx para converter PDF em Word.') from e
        target = unique_path(dest / (source.stem + '.docx'))
        cv = Converter(str(source))
        try: cv.convert(str(target), start=0, end=None, multi_processing=False)
        finally: cv.close()
        if cancel and cancel.is_set():
            target.unlink(missing_ok=True)
            raise Cancelled('Tarefa cancelada.')
        return [target]
    doc = fitz.open(str(source))
    outputs = []
    try:
        if fmt == 'TXT':
            target = unique_path(dest / (source.stem + '.txt'))
            target.write_text('\n\n'.join(p.get_text() for p in doc), encoding='utf-8')
            return [target]
        if fmt not in ('PNG','JPG'): raise ConversionError('Formato não suportado.')
        ext = 'jpg' if fmt == 'JPG' else 'png'
        for i, page in enumerate(doc, 1):
            if cancel and cancel.is_set(): raise Cancelled('Tarefa cancelada.')
            target = unique_path(dest / f'{source.stem} - pagina {i:03d}.{ext}')
            pix = page.get_pixmap(matrix=fitz.Matrix(2,2), alpha=False)
            pix.save(str(target)) if fmt == 'PNG' else pix.pil_save(str(target), format='JPEG', quality=90)
            outputs.append(target)
        return outputs
    except Exception:
        for p in outputs: p.unlink(missing_ok=True)
        raise
    finally: doc.close()


def convert_office(source: Path, fmt: str, dest: Path, cancel=None, progress=None) -> list[Path]:
    if fmt != 'PDF': raise ConversionError('Documentos Office: a saída suportada é PDF.')
    binary = tool_path('soffice')
    if not binary: raise ConversionError('LibreOffice não encontrado. Instale-o para converter Word, PowerPoint e Excel em PDF.')
    import tempfile
    # An isolated profile prevents conflicts with an open LibreOffice.
    with tempfile.TemporaryDirectory(prefix='conversorhub-lo-') as tmp:
        staged = Path(tmp) / source.name
        shutil.copy2(source, staged)
        outdir = Path(tmp) / 'out'; outdir.mkdir()
        profile = (Path(tmp) / 'profile').as_uri()
        run_process([binary, f'-env:UserInstallation={profile}', '--headless', '--convert-to', 'pdf',
                     '--outdir', str(outdir), str(staged)], cancel, progress)
        candidate = outdir / (source.stem + '.pdf')
        if not candidate.exists(): raise ConversionError('O LibreOffice não gerou o PDF. Verifique se o documento é válido.')
        result = unique_path(dest / candidate.name)
        shutil.move(str(candidate), str(result))
    return [result]


def convert_media(source: Path, fmt: str, dest: Path, cancel=None, progress=None) -> list[Path]:
    ffmpeg = tool_path('ffmpeg')
    if not ffmpeg: raise ConversionError('FFmpeg não encontrado. Instale-o para converter áudio e vídeo.')
    kind = classify_file(source)
    if fmt not in SUPPORTED_OUTPUTS.get(kind, []): raise ConversionError('Formato de saída inválido para este arquivo.')
    ext = fmt.lower()
    result = unique_path(dest / f'{source.stem}.{ext}')
    args = [ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', str(source)]
    if fmt == 'MP3': args += ['-vn', '-codec:a', 'libmp3lame', '-q:a', '2']
    elif fmt == 'M4A': args += ['-vn', '-codec:a', 'aac', '-b:a', '192k']
    elif fmt == 'WAV': args += ['-vn', '-codec:a', 'pcm_s16le']
    elif fmt == 'FLAC': args += ['-vn', '-codec:a', 'flac']
    elif fmt == 'OGG': args += ['-vn', '-codec:a', 'libvorbis', '-q:a', '5']
    elif fmt == 'GIF': args += ['-vf', 'fps=10,scale=640:-1:flags=lanczos', '-loop', '0']
    elif fmt == 'WEBM': args += ['-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '34', '-c:a', 'libopus']
    elif fmt in ('MP4','MKV'): args += ['-c:v','libx264','-crf','23','-preset','medium','-c:a','aac','-b:a','192k']
    args.append(str(result))
    try:
        run_process(args, cancel, progress)
    except Exception:
        result.unlink(missing_ok=True)
        raise
    return [result]


def convert_file(source: str | Path, fmt: str, destination: str | Path, cancel=None, progress=None) -> list[Path]:
    path = Path(source).expanduser().resolve()
    if not path.is_file(): raise ConversionError('Arquivo de origem não encontrado.')
    kind = classify_file(path)
    if not kind: raise ConversionError('Tipo de arquivo não suportado.')
    fmt = fmt.upper()
    if fmt not in SUPPORTED_OUTPUTS[kind]: raise ConversionError(f'Não é possível converter {path.suffix} para {fmt}.')
    dest = validate_output_dir(destination)
    if cancel and cancel.is_set(): raise Cancelled('Tarefa cancelada.')
    if kind == 'image': return convert_image(path, fmt, dest)
    if kind == 'pdf': return convert_pdf(path, fmt, dest, cancel)
    if kind == 'office': return convert_office(path, fmt, dest, cancel, progress)
    return convert_media(path, fmt, dest, cancel, progress)


def download_media(url: str, destination: str | Path, output: str, quality: str,
                   cancel: threading.Event | None = None, progress=None) -> list[Path]:
    if not re.match(r'^https?://[^\s/]+(?:/|$)', url.strip(), re.I):
        raise ConversionError('Informe um endereço HTTP ou HTTPS válido.')
    if not importlib.util.find_spec('yt_dlp'): raise ConversionError('yt-dlp não está instalado.')
    from yt_dlp import YoutubeDL
    dest = validate_output_dir(destination)
    mode = output.upper()
    if mode not in ('VIDEO MP4', 'ÁUDIO MP3', 'ÁUDIO M4A', 'VÍDEO ORIGINAL'):
        raise ConversionError('Formato de download inválido.')
    ff = tool_path('ffmpeg')
    if mode != 'VÍDEO ORIGINAL' and not ff: raise ConversionError('FFmpeg é necessário para MP4/MP3/M4A.')
    percent = re.compile(r'(\d+(?:[.,]\d+)?)%')
    def hook(data):
        if cancel and cancel.is_set(): raise Cancelled('Download cancelado.')
        if progress and data.get('status') == 'downloading':
            downloaded = data.get('downloaded_bytes', 0)
            total = data.get('total_bytes') or data.get('total_bytes_estimate') or 0
            progress(f'{100*downloaded/total:.1f}%' if total else 'Baixando…')
        elif progress and data.get('status') == 'finished': progress('Finalizando arquivo…')
    opts = {
        'paths': {'home': str(dest)},
        'outtmpl': '%(title).160B [%(id)s].%(ext)s',
        'windowsfilenames': True, 'noplaylist': True, 'quiet': True, 'no_warnings': True,
        'progress_hooks': [hook], 'overwrites': False,
        'socket_timeout': 30, 'retries': 3,
    }
    if ff: opts['ffmpeg_location'] = str(Path(ff).parent)
    if mode == 'ÁUDIO MP3':
        opts.update(format='bestaudio/best', postprocessors=[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}])
    elif mode == 'ÁUDIO M4A':
        opts.update(format='bestaudio/best', postprocessors=[{'key':'FFmpegExtractAudio','preferredcodec':'m4a','preferredquality':'192'}])
    elif mode == 'VÍDEO ORIGINAL': opts['format'] = 'best'
    else:
        size = {'Melhor disponível': None, '1080p': 1080, '720p': 720, '480p': 480}.get(quality)
        constraint = f'[height<={size}]' if size else ''
        opts['format'] = f'bestvideo{constraint}+bestaudio/best{constraint}'
        opts['merge_output_format'] = 'mp4'
        opts['postprocessors'] = [{'key':'FFmpegVideoRemuxer', 'preferedformat':'mp4'}]
    try:
        with YoutubeDL(opts) as yd:
            info = yd.extract_info(url.strip(), download=True)
    except Cancelled: raise
    except Exception as ex: raise ConversionError(f'Não foi possível baixar o conteúdo: {ex}') from ex
    if cancel and cancel.is_set(): raise Cancelled('Download cancelado.')
    # yt-dlp computes the final path; return existing match for opening in Explorer.
    identifier = str(info.get('id') or '')
    matches = [p for p in dest.iterdir() if p.is_file() and identifier and f'[{identifier}]' in p.name and not p.name.endswith('.part')]
    return sorted(matches, key=lambda p:p.stat().st_mtime, reverse=True)[:1]
