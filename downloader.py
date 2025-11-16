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
    Descarga audio de YouTube usando yt-dlp con cookies y Node.js runtime
    """
    try:
        # Sanitizar nombre de archivo - formato: Artista - Titulo.mp3
        safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_artist = safe_artist.replace('  ', ' ')
        safe_title = safe_title.replace('  ', ' ')
        
        file_name = f"{safe_artist} - {safe_title}"
        output_path = os.path.join(output_dir, file_name)
        
        # Obtener archivo de cookies
        cookies_file = get_cookies_file()
        
        # Ruta del archivo de configuración
        config_file = os.path.join(os.path.dirname(__file__), 'yt-dlp.conf')
        
        # Configuración base de yt-dlp
        base_opts = {
            # Intentar múltiples formatos, priorizando audio
            'format': 'bestaudio/best',
            # Fallback a formatos más compatibles si los mejores no están disponibles
            'format_sort': ['acodec:aac', 'acodec:mp3', 'ext:m4a:m4a', 'ext:webm:webm'],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_path + '.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'no_color': True,
            'progress_hooks': [progress_hook],
            # Headers para evitar bloqueos
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            # Usar solo cliente web con cookies (android/ios no soportan cookies)
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'tv_embedded'],  # tv_embedded como fallback
                    'player_skip': ['webpage'],
                }
            },
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
        }
        
        # Agregar cookies si están disponibles
        if cookies_file and os.path.exists(cookies_file):
            base_opts['cookiefile'] = cookies_file
        
        # Agregar archivo de configuración si existe
        if os.path.exists(config_file):
            print(json.dumps({'type': 'info', 'message': f'📝 Usando configuración desde {config_file}'}), flush=True)
            base_opts['config_location'] = config_file
        
        # Descargar desde YouTube
        url = f'https://www.youtube.com/watch?v={video_id}'
        
        print(json.dumps({
            'type': 'info',
            'message': 'Descargando desde YouTube...'
        }), flush=True)
        
        with yt_dlp.YoutubeDL(base_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Encontrar el archivo MP3 generado
            mp3_file = output_path + '.mp3'
            
            if os.path.exists(mp3_file):
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
                    'source': 'YouTube',
                    'fileName': os.path.basename(mp3_file),
                    'filePath': mp3_file,
                    'size': file_size,
                    'sizeMB': round(size_mb, 2),
                    'title': info.get('title', file_name),
                    'duration': info.get('duration', 0),
                }), flush=True)
                
                return True
            else:
                raise Exception("Archivo MP3 no generado")
                
    except Exception as e:
        print(json.dumps({
            'type': 'error',
            'success': False,
            'error': str(e)
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
