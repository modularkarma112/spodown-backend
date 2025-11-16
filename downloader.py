#!/usr/bin/env python3
"""
Descargador robusto usando yt-dlp con FFmpeg
Usa cookies de YouTube para evitar restricciones de bot
"""
import sys
import json
import os
from pathlib import Path
import yt_dlp
from mutagen.id3 import ID3, TIT2, TPE1, TALB
from mutagen.mp3 import MP3
import base64
import tempfile

def get_cookies_file():
    """
    Busca archivo de cookies en múltiples ubicaciones:
    1. Variable de entorno YOUTUBE_COOKIES_BASE64 (Base64)
    2. Archivo /etc/youtube_cookies.txt (Render)
    3. Archivo youtube_cookies.txt en directorio actual
    """
    # Intentar desde variable de entorno (Base64)
    cookies_base64 = os.environ.get('YOUTUBE_COOKIES_BASE64')
    if cookies_base64:
        try:
            cookies_content = base64.b64decode(cookies_base64).decode('utf-8')
            cookies_file = os.path.join(tempfile.gettempdir(), 'yt_cookies.txt')
            with open(cookies_file, 'w') as f:
                f.write(cookies_content)
            print(json.dumps({'type': 'info', 'message': '🍪 Usando cookies desde variable de entorno'}), flush=True)
            return cookies_file
        except Exception as e:
            print(json.dumps({'type': 'warning', 'message': f'Error al decodificar cookies Base64: {e}'}), flush=True)
    
    # Intentar desde /etc (Render)
    if os.path.exists('/etc/youtube_cookies.txt'):
        print(json.dumps({'type': 'info', 'message': '🍪 Usando cookies desde /etc/youtube_cookies.txt'}), flush=True)
        return '/etc/youtube_cookies.txt'
    
    # Intentar desde directorio actual
    local_cookies = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
    if os.path.exists(local_cookies):
        print(json.dumps({'type': 'info', 'message': '🍪 Usando cookies desde archivo local'}), flush=True)
        return local_cookies
    
    print(json.dumps({'type': 'warning', 'message': '⚠️ No se encontraron cookies, intentando sin autenticación'}), flush=True)
    return None

def download_audio(video_id, title, artist, output_dir):
    """
    Descarga audio priorizando SoundCloud para mejor velocidad y calidad
    """
    # Sanitizar nombre de archivo - formato: Artista - Titulo.mp3
    safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_artist = safe_artist.replace('  ', ' ')
    safe_title = safe_title.replace('  ', ' ')
    
    file_name = f"{safe_artist} - {safe_title}"
    output_path = os.path.join(output_dir, file_name)
    
    # Configuración optimizada para velocidad y calidad
    base_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',  # Máxima calidad
        }],
        'outtmpl': output_path + '.%(ext)s',
        'quiet': True,  # Menos output para más velocidad
        'no_warnings': True,
        'extract_flat': False,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'logtostderr': False,
        'no_color': True,
        'progress_hooks': [progress_hook],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
        'socket_timeout': 20,  # Timeout más corto
        'retries': 3,
        'fragment_retries': 3,
    }
    
    # Priorizar SoundCloud, luego YouTube Music, luego YouTube directo
    sources = [
        {
            'name': 'SoundCloud',
            'url': f'scsearch1:"{artist} {title}"',  # Tomar solo el primer resultado
            'opts': base_opts
        },
        {
            'name': 'YouTube Music',
            'url': f'ytsearch1:"{artist} {title} audio"',
            'opts': base_opts
        },
        {
            'name': 'YouTube',
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'opts': {
                **base_opts,
                'cookiefile': get_cookies_file(),
                'extractor_args': {
                    'youtube': {
                        'player_client': ['tv_embedded', 'web'],
                        'player_skip': ['webpage', 'configs'],
                    }
                },
            }
        },
    ]
    
    last_error = None
    
    for source in sources:
        try:
            print(json.dumps({
                'type': 'info',
                'message': f'🔄 Buscando en {source["name"]}...'
            }), flush=True)
            
            with yt_dlp.YoutubeDL(source['opts']) as ydl:
                info = ydl.extract_info(source['url'], download=True)
                
                # Encontrar el archivo MP3 generado
                mp3_file = output_path + '.mp3'
                
                if os.path.exists(mp3_file) and os.path.getsize(mp3_file) > 100000:  # Verificar que sea válido (>100KB)
                    # Agregar metadatos ID3
                    try:
                        audio = MP3(mp3_file, ID3=ID3)
                        if audio.tags is None:
                            audio.add_tags()
                        
                        audio.tags.add(TIT2(encoding=3, text=title))
                        audio.tags.add(TPE1(encoding=3, text=artist))
                        audio.tags.add(TALB(encoding=3, text='Spodown'))
                        audio.save()
                    except Exception as meta_error:
                        print(json.dumps({'type': 'warning', 'message': f'Metadatos: {meta_error}'}), flush=True)
                    
                    file_size = os.path.getsize(mp3_file)
                    size_mb = file_size / (1024 * 1024)
                    
                    print(json.dumps({
                        'type': 'complete',
                        'success': True,
                        'source': source['name'],
                        'fileName': os.path.basename(mp3_file),
                        'filePath': mp3_file,
                        'size': file_size,
                        'sizeMB': round(size_mb, 2),
                        'title': info.get('title', file_name) if isinstance(info, dict) else file_name,
                        'duration': info.get('duration', 0) if isinstance(info, dict) else 0,
                    }), flush=True)
                    
                    return True
                    
        except Exception as e:
            last_error = str(e)
            print(json.dumps({
                'type': 'info',
                'message': f'⏩ Intentando siguiente fuente...'
            }), flush=True)
            continue
    
    # Si todas las fuentes fallaron
    print(json.dumps({
        'type': 'error',
        'success': False,
        'error': f'No se pudo descargar desde ninguna fuente. Último error: {last_error}'
    }), flush=True)
    return False

def progress_hook(d):
    """Hook para reportar progreso en tiempo real"""
    if d['status'] == 'downloading':
        try:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                progress = (downloaded / total) * 100
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                print(json.dumps({
                    'type': 'progress',
                    'progress': round(progress, 2),
                    'downloaded': downloaded,
                    'total': total,
                    'speed': speed,
                    'eta': eta
                }), flush=True)
        except:
            pass
    elif d['status'] == 'finished':
        print(json.dumps({
            'type': 'converting',
            'message': 'Convirtiendo a MP3...'
        }), flush=True)

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print(json.dumps({
            'type': 'error',
            'success': False,
            'error': 'Uso: python downloader.py <video_id> <title> <artist> <output_dir>'
        }), flush=True)
        sys.exit(1)
    
    video_id = sys.argv[1]
    title = sys.argv[2]
    artist = sys.argv[3]
    output_dir = sys.argv[4]
    
    # Crear directorio si no existe
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    success = download_audio(video_id, title, artist, output_dir)
    sys.exit(0 if success else 1)
