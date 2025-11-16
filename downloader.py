#!/usr/bin/env python3
"""
Descargador simple y rápido usando solo SoundCloud
Optimizado para archivos pequeños y velocidad máxima
"""
import sys
import json
import os
from pathlib import Path
import yt_dlp
from mutagen.id3 import ID3, TIT2, TPE1, TALB
from mutagen.mp3 import MP3

def progress_hook(d):
    """Hook minimalista de progreso"""
    if d['status'] == 'downloading':
        try:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                progress = (downloaded / total) * 100
                print(json.dumps({
                    'type': 'progress',
                    'progress': round(progress, 1),
                }), flush=True)
        except:
            pass
    elif d['status'] == 'finished':
        print(json.dumps({'type': 'converting'}), flush=True)

def download_audio(video_id, title, artist, output_dir):
    """
    Descarga SOLO desde SoundCloud - Simple y rápido
    """
    try:
        # Nombre de archivo simple
        safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
        file_name = f"{safe_artist} - {safe_title}"
        output_path = os.path.join(output_dir, file_name)
        
        print(json.dumps({'type': 'info', 'message': '🎵 Buscando en SoundCloud...'}), flush=True)
        
        # Configuración ultra-simple optimizada para velocidad
        opts = {
            'format': 'worst',  # Calidad más baja = más rápido
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',  # 64kbps
            }],
            'outtmpl': output_path + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'progress_hooks': [progress_hook],
            'socket_timeout': 15,
            'retries': 2,
            'fragment_retries': 2,
        }
        
        # SOLO buscar en SoundCloud (primer resultado)
        url = f'scsearch1:{artist} {title}'
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            mp3_file = output_path + '.mp3'
            
            if os.path.exists(mp3_file):
                file_size = os.path.getsize(mp3_file)
                
                # Validar tamaño
                if file_size < 50000:  # Muy pequeño
                    os.remove(mp3_file)
                    raise Exception('Archivo inválido')
                
                if file_size > 15 * 1024 * 1024:  # >15MB
                    os.remove(mp3_file)
                    raise Exception('Archivo muy grande')
                
                # Agregar metadatos
                try:
                    audio = MP3(mp3_file, ID3=ID3)
                    if audio.tags is None:
                        audio.add_tags()
                    audio.tags.add(TIT2(encoding=3, text=title))
                    audio.tags.add(TPE1(encoding=3, text=artist))
                    audio.tags.add(TALB(encoding=3, text='Spodown'))
                    audio.save()
                except:
                    pass
                
                print(json.dumps({
                    'type': 'complete',
                    'success': True,
                    'source': 'SoundCloud',
                    'fileName': os.path.basename(mp3_file),
                    'filePath': mp3_file,
                    'size': file_size,
                    'sizeMB': round(file_size / (1024 * 1024), 2),
                    'title': title,
                    'duration': info.get('duration', 0) if isinstance(info, dict) else 0,
                }), flush=True)
                return True
        
        raise Exception('No se encontró en SoundCloud')
        
    except Exception as e:
        print(json.dumps({
            'type': 'error',
            'success': False,
            'error': f'Error: {str(e)}'
        }), flush=True)
        return False

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
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    success = download_audio(video_id, title, artist, output_dir)
    sys.exit(0 if success else 1)
