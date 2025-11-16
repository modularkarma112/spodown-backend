#!/usr/bin/env python3
"""
Descargador robusto usando yt-dlp con FFmpeg
Similar a convertidores de YouTube a MP3 de código abierto
"""
import sys
import json
import os
from pathlib import Path
import yt_dlp
from mutagen.id3 import ID3, TIT2, TPE1, TALB
from mutagen.mp3 import MP3

def download_audio(video_id, title, artist, output_dir):
    """
    Descarga audio de YouTube usando yt-dlp con las mejores prácticas
    """
    try:
        # Sanitizar nombre de archivo - formato: Artista - Titulo.mp3
        safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_artist = safe_artist.replace('  ', ' ')
        safe_title = safe_title.replace('  ', ' ')
        
        file_name = f"{safe_artist} - {safe_title}"
        output_path = os.path.join(output_dir, file_name)
        
        # Ruta a FFmpeg local
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_location = os.path.join(script_dir, 'ffmpeg', 'bin')
        
        # Configuración óptima de yt-dlp (usado por convertidores populares)
        ydl_opts = {
            'format': 'bestaudio/best',
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
            'ffmpeg_location': ffmpeg_location,  # Usar FFmpeg local
            # Headers para evitar bloqueos
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            # Opciones adicionales para evitar errores
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
        }
        
        url = f'https://www.youtube.com/watch?v={video_id}'
        
        print(json.dumps({
            'type': 'start',
            'message': f'Iniciando descarga: {file_name}',
            'url': url
        }), flush=True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Encontrar el archivo MP3 generado
            mp3_file = output_path + '.mp3'
            
            if os.path.exists(mp3_file):
                # Agregar metadatos ID3
                try:
                    audio = MP3(mp3_file, ID3=ID3)
                    
                    # Crear tags si no existen
                    if audio.tags is None:
                        audio.add_tags()
                    
                    # Escribir metadatos
                    audio.tags.add(TIT2(encoding=3, text=title))  # Título
                    audio.tags.add(TPE1(encoding=3, text=artist))  # Artista
                    audio.tags.add(TALB(encoding=3, text='Spodown'))  # Álbum
                    
                    audio.save()
                    print(json.dumps({'type': 'info', 'message': 'Metadatos ID3 agregados'}), flush=True)
                except Exception as meta_error:
                    print(json.dumps({'type': 'warning', 'message': f'No se pudieron escribir metadatos: {meta_error}'}), flush=True)
                
                file_size = os.path.getsize(mp3_file)
                size_mb = file_size / (1024 * 1024)
                
                print(json.dumps({
                    'type': 'complete',
                    'success': True,
                    'fileName': os.path.basename(mp3_file),
                    'filePath': mp3_file,
                    'size': file_size,
                    'sizeMB': round(size_mb, 2),
                    'title': info.get('title', file_name),
                    'duration': info.get('duration', 0),
                }), flush=True)
                
                return True
            else:
                raise Exception(f"Archivo MP3 no encontrado: {mp3_file}")
                
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
