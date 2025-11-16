const express = require('express');
const cors = require('cors');
const http = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');
const NodeID3 = require('node-id3');
const axios = require('axios');

// Detectar comando de Python según el sistema operativo
const PYTHON_CMD = os.platform() === 'win32' ? 'python' : 'python3';

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3001;

// Configuración de CORS más permisiva
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  credentials: true
}));

app.use(express.json());

// Socket.IO con CORS
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Directorio de descargas
const DOWNLOAD_DIR = path.join(__dirname, 'downloads');
if (!fs.existsSync(DOWNLOAD_DIR)) {
  fs.mkdirSync(DOWNLOAD_DIR, { recursive: true });
}

// Obtener IP local (priorizar WiFi sobre VPN)
function getLocalIP() {
  const interfaces = os.networkInterfaces();
  let vpnIP = null;
  
  // Buscar primero interfaces WiFi
  for (const name of Object.keys(interfaces)) {
    if (name.toLowerCase().includes('wi-fi') || name.toLowerCase().includes('wlan')) {
      for (const iface of interfaces[name]) {
        if (iface.family === 'IPv4' && !iface.internal) {
          return iface.address;
        }
      }
    }
  }
  
  // Si no hay WiFi, buscar cualquier IPv4 no interna
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        // Guardar VPN como fallback
        if (name.toLowerCase().includes('vpn') || name.toLowerCase().includes('nord')) {
          vpnIP = iface.address;
        } else {
          return iface.address;
        }
      }
    }
  }
  
  return vpnIP || 'localhost';
}

const localIP = getLocalIP();

// Socket.IO para comunicación en tiempo real
io.on('connection', (socket) => {
  console.log(`✅ Cliente conectado: ${socket.id}`);

  socket.on('disconnect', () => {
    console.log(`❌ Cliente desconectado: ${socket.id}`);
  });

  // Evento de ping para verificar conexión
  socket.on('ping', () => {
    socket.emit('pong', { timestamp: Date.now() });
  });
});

// Endpoint de salud (para Render)
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Servidor funcionando correctamente',
    timestamp: new Date().toISOString()
  });
});

// Endpoint de salud (legacy)
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Servidor funcionando correctamente',
    ip: localIP,
    port: PORT,
    timestamp: new Date().toISOString()
  });
});

// Endpoint para obtener IP del servidor
app.get('/api/info', (req, res) => {
  res.json({
    ip: localIP,
    port: PORT,
    downloadDir: DOWNLOAD_DIR,
    platform: os.platform(),
    hostname: os.hostname()
  });
});

// Endpoint para buscar en YouTube (usando yt-dlp Python para mejor compatibilidad)
app.post('/api/search', async (req, res) => {
  try {
    const { query } = req.body;
    console.log(`\n🔍 Búsqueda: ${query}`);

    // Usar Python con yt-dlp para búsqueda más confiable
    const pythonSearch = spawn(PYTHON_CMD, [
      '-c',
      `
import yt_dlp
import json
import sys

query = sys.argv[1]
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Buscar múltiples resultados para filtrar
        result = ydl.extract_info(f"ytsearch5:{query}", download=False)
        
        if result and 'entries' in result and len(result['entries']) > 0:
            videos = result['entries']
            
            # Priorizar videos con "lyrics", "letra", "audio" en el título
            priority_keywords = ['lyrics', 'letra', 'audio', 'official audio', 'audio oficial']
            avoid_keywords = ['official video', 'video oficial', 'music video', 'visualizer', 'teaser', 'trailer']
            
            def score_video(video):
                title = video.get('title', '').lower()
                score = 0
                
                # Bonificación por palabras clave prioritarias
                for keyword in priority_keywords:
                    if keyword in title:
                        score += 10
                
                # Penalización por videos oficiales
                for keyword in avoid_keywords:
                    if keyword in title:
                        score -= 5
                
                # Bonificación pequeña si es del canal oficial (pero menos que lyrics)
                uploader = video.get('uploader', '').lower()
                if 'vevo' in uploader or 'official' in uploader or 'topic' in uploader:
                    score += 2
                
                return score
            
            # Ordenar por puntaje
            sorted_videos = sorted(videos, key=score_video, reverse=True)
            best_video = sorted_videos[0]
            
            print(json.dumps({
                'success': True,
                'videoId': best_video.get('id'),
                'title': best_video.get('title'),
                'duration': best_video.get('duration', 0),
                'thumbnail': best_video.get('thumbnail'),
                'url': best_video.get('url') or f"https://www.youtube.com/watch?v={best_video.get('id')}",
                'uploader': best_video.get('uploader', 'Desconocido'),
            }))
        else:
            print(json.dumps({'success': False, 'error': 'No se encontraron resultados'}))
except Exception as e:
    print(json.dumps({'success': False, 'error': str(e)}))
      `.trim(),
      query
    ]);

    let searchData = '';
    
    pythonSearch.stdout.on('data', (data) => {
      searchData += data.toString();
    });

    pythonSearch.stderr.on('data', (data) => {
      console.error('⚠️ Python stderr:', data.toString());
    });

    pythonSearch.on('close', (code) => {
      try {
        const result = JSON.parse(searchData.trim());
        
        if (result.success) {
          console.log(`✅ Video encontrado: ${result.title}`);
          console.log(`   ID: ${result.videoId}`);
          res.json(result);
        } else {
          res.json(result);
        }
      } catch (error) {
        console.error('❌ Error parseando resultado:', error.message);
        res.status(500).json({
          success: false,
          error: 'Error procesando búsqueda',
        });
      }
    });

  } catch (error) {
    console.error('❌ Error en búsqueda:', error.message);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// Endpoint para descargar con progreso en tiempo real (usando Python + yt-dlp)
app.post('/api/download', async (req, res) => {
  const downloadId = Date.now().toString();
  
  try {
    const { videoId, title, artist } = req.body;
    
    console.log(`\n⬇️ Descarga iniciada [${downloadId}]`);
    console.log(`   Video ID: ${videoId}`);
    console.log(`   Título: ${title} - ${artist}`);

    // Emitir evento de inicio
    io.emit('download:start', {
      downloadId,
      title,
      artist,
      videoId
    });

    // Ejecutar script Python de descarga
    const downloaderScript = path.join(__dirname, 'downloader.py');
    
    const downloadProcess = spawn(PYTHON_CMD, [
      downloaderScript,
      videoId,
      title,
      artist,
      DOWNLOAD_DIR
    ]);

    let outputData = '';
    let lastProgress = 0;

    downloadProcess.stdout.on('data', (data) => {
      const lines = data.toString().split('\n');
      
      lines.forEach(line => {
        if (!line.trim()) return;
        
        try {
          const event = JSON.parse(line);
          outputData = line; // Guardar última línea para response
          
          switch(event.type) {
            case 'start':
              console.log(`📥 ${event.message}`);
              break;
              
            case 'progress':
              // Solo emitir cada 5% para no saturar
              if (event.progress - lastProgress >= 5) {
                lastProgress = event.progress;
                console.log(`   Progreso: ${event.progress.toFixed(1)}%`);
                
                io.emit('download:progress', {
                  downloadId,
                  progress: event.progress,
                  downloaded: event.downloaded,
                  total: event.total,
                  speed: event.speed,
                  eta: event.eta
                });
              }
              break;
              
            case 'converting':
              console.log(`🔄 ${event.message}`);
              io.emit('download:converting', { downloadId });
              break;
              
            case 'complete':
              console.log(`✅ Descarga completada: ${event.fileName} (${event.sizeMB} MB)`);
              io.emit('download:complete', {
                downloadId,
                fileName: event.fileName,
                size: event.size,
                sizeMB: event.sizeMB
              });
              break;
              
            case 'error':
              console.error(`❌ Error: ${event.error}`);
              break;
          }
        } catch (e) {
          // Línea no es JSON, probablemente log de yt-dlp
          if (line.includes('%')) {
            console.log(`   ${line.trim()}`);
          }
        }
      });
    });

    downloadProcess.stderr.on('data', (data) => {
      const msg = data.toString();
      if (!msg.includes('Deleting original file')) {
        console.error('⚠️ stderr:', msg);
      }
    });

    downloadProcess.on('close', (code) => {
      try {
        if (code === 0 && outputData) {
          const result = JSON.parse(outputData);
          
          if (result.success && result.type === 'complete') {
            res.json({
              success: true,
              downloadId,
              fileName: result.fileName,
              size: result.size,
              sizeMB: result.sizeMB,
              downloadUrl: `/api/file/${encodeURIComponent(result.fileName)}`,
            });
          } else {
            throw new Error(result.error || 'Error desconocido en descarga');
          }
        } else {
          throw new Error(`Proceso terminó con código ${code}`);
        }
      } catch (error) {
        console.error(`❌ Error en descarga [${downloadId}]:`, error.message);
        
        io.emit('download:error', {
          downloadId,
          error: error.message
        });
        
        if (!res.headersSent) {
          res.status(500).json({
            success: false,
            error: error.message,
          });
        }
      }
    });

  } catch (error) {
    console.error(`❌ Error iniciando descarga [${downloadId}]:`, error.message);
    
    io.emit('download:error', {
      downloadId,
      error: error.message
    });
    
    if (!res.headersSent) {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }
});

// Endpoint para descargar el archivo
app.get('/api/file/:filename', (req, res) => {
  try {
    const filename = decodeURIComponent(req.params.filename);
    const filePath = path.join(DOWNLOAD_DIR, filename);

    if (fs.existsSync(filePath)) {
      console.log(`📤 Enviando archivo: ${filename}`);
      
      res.download(filePath, filename, (err) => {
        if (err) {
          console.error('Error enviando archivo:', err);
        } else {
          console.log(`✅ Archivo enviado: ${filename}`);
          // Opcional: eliminar archivo después de enviarlo
          // setTimeout(() => {
          //   if (fs.existsSync(filePath)) {
          //     fs.unlinkSync(filePath);
          //     console.log(`🗑️ Archivo eliminado: ${filename}`);
          //   }
          // }, 5000);
        }
      });
    } else {
      res.status(404).json({
        success: false,
        error: 'Archivo no encontrado',
      });
    }
  } catch (error) {
    console.error('❌ Error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// Endpoint para buscar carátula de álbum en Spotify
app.post('/api/cover', async (req, res) => {
  try {
    const { artist, title } = req.body;
    console.log(`\n🎨 Buscando carátula: ${artist} - ${title}`);

    // Buscar en Spotify usando web scraping (API pública)
    const https = require('https');
    
    // Construir query de búsqueda
    const query = encodeURIComponent(`${artist} ${title}`);
    const searchUrl = `https://api.spotify.com/v1/search?q=${query}&type=track&limit=1`;
    
    // Primero obtener token de acceso (cliente público)
    const getAccessToken = () => {
      return new Promise((resolve, reject) => {
        const tokenData = JSON.stringify({
          grant_type: 'client_credentials'
        });
        
        // Credenciales públicas de Spotify (se renuevan cada hora)
        const clientId = '4f0b6f0f7f3d4e4a8b1e5c3d2a1b0c9d';
        const clientSecret = '8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d';
        const auth = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');
        
        const options = {
          hostname: 'accounts.spotify.com',
          path: '/api/token',
          method: 'POST',
          headers: {
            'Authorization': `Basic ${auth}`,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': tokenData.length
          }
        };
        
        const tokenReq = https.request(options, (tokenRes) => {
          let data = '';
          tokenRes.on('data', chunk => data += chunk);
          tokenRes.on('end', () => {
            try {
              const result = JSON.parse(data);
              resolve(result.access_token);
            } catch (e) {
              reject(e);
            }
          });
        });
        
        tokenReq.on('error', reject);
        tokenReq.write(tokenData);
        tokenReq.end();
      });
    };
    
    // Método alternativo: scraping directo de búsqueda de Spotify (sin autenticación)
    const searchCoverAlternative = () => {
      return new Promise((resolve, reject) => {
        const searchQuery = encodeURIComponent(`${artist} ${title}`);
        const url = `https://open.spotify.com/search/${searchQuery}/tracks`;
        
        https.get(url, (searchRes) => {
          let html = '';
          searchRes.on('data', chunk => html += chunk);
          searchRes.on('end', () => {
            // Buscar URL de imagen en el HTML
            const imgMatch = html.match(/https:\/\/i\.scdn\.co\/image\/[a-f0-9]+/);
            if (imgMatch) {
              resolve({ coverUrl: imgMatch[0], source: 'spotify-web' });
            } else {
              reject(new Error('No se encontró carátula'));
            }
          });
        }).on('error', reject);
      });
    };
    
    // Método usando iTunes API (alternativa gratuita)
    const searchiTunes = () => {
      return new Promise((resolve, reject) => {
        const searchQuery = encodeURIComponent(`${artist} ${title}`);
        const url = `https://itunes.apple.com/search?term=${searchQuery}&entity=song&limit=1`;
        
        https.get(url, (itunesRes) => {
          let data = '';
          itunesRes.on('data', chunk => data += chunk);
          itunesRes.on('end', () => {
            try {
              const result = JSON.parse(data);
              if (result.results && result.results.length > 0) {
                const track = result.results[0];
                // iTunes da imagen de 100x100, cambiar a más alta resolución
                let coverUrl = track.artworkUrl100;
                if (coverUrl) {
                  coverUrl = coverUrl.replace('100x100', '600x600');
                  resolve({ 
                    coverUrl, 
                    source: 'itunes',
                    trackName: track.trackName,
                    artistName: track.artistName,
                    albumName: track.collectionName
                  });
                } else {
                  reject(new Error('No hay carátula disponible'));
                }
              } else {
                reject(new Error('No se encontraron resultados'));
              }
            } catch (e) {
              reject(e);
            }
          });
        }).on('error', reject);
      });
    };
    
    // Intentar iTunes primero (más confiable y sin autenticación)
    try {
      const result = await searchiTunes();
      console.log(`✅ Carátula encontrada (${result.source}): ${result.coverUrl}`);
      res.json({
        success: true,
        coverUrl: result.coverUrl,
        source: result.source,
        trackName: result.trackName,
        artistName: result.artistName,
        albumName: result.albumName
      });
    } catch (itunesError) {
      console.log(`⚠️ iTunes falló, intentando método alternativo...`);
      
      try {
        const result = await searchCoverAlternative();
        console.log(`✅ Carátula encontrada (${result.source}): ${result.coverUrl}`);
        res.json({
          success: true,
          coverUrl: result.coverUrl,
          source: result.source
        });
      } catch (altError) {
        console.error('❌ No se pudo encontrar carátula:', altError.message);
        res.json({
          success: false,
          error: 'No se encontró carátula para esta canción',
          details: altError.message
        });
      }
    }
    
  } catch (error) {
    console.error('❌ Error buscando carátula:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Endpoint para descargar carátula e incrustarla en archivo MP3
app.post('/api/cover/embed', async (req, res) => {
  try {
    const { filePath, coverUrl } = req.body;

    if (!filePath || !coverUrl) {
      return res.status(400).json({
        success: false,
        error: 'Se requieren filePath y coverUrl'
      });
    }

    console.log(`\n📥 Descargando e incrustando carátula en: ${path.basename(filePath)}`);

    // Descargar la imagen
    const imageResponse = await axios.get(coverUrl, {
      responseType: 'arraybuffer',
      timeout: 10000
    });

    const imageBuffer = Buffer.from(imageResponse.data);
    console.log(`✅ Imagen descargada (${(imageBuffer.length / 1024).toFixed(2)} KB)`);

    // Verificar que el archivo MP3 existe
    if (!fs.existsSync(filePath)) {
      throw new Error(`Archivo no encontrado: ${filePath}`);
    }

    // Leer tags actuales
    const currentTags = NodeID3.read(filePath);
    
    // Preparar nuevos tags con la imagen
    const tags = {
      ...currentTags,
      image: {
        mime: 'image/jpeg',
        type: {
          id: 3,
          name: 'front cover'
        },
        description: 'Album Cover',
        imageBuffer: imageBuffer
      }
    };

    // Escribir tags en el archivo
    const success = NodeID3.write(tags, filePath);

    if (success) {
      console.log(`✅ Carátula incrustada exitosamente en: ${path.basename(filePath)}`);
      res.json({
        success: true,
        message: 'Carátula incrustada exitosamente',
        fileSize: (imageBuffer.length / 1024).toFixed(2) + ' KB'
      });
    } else {
      throw new Error('No se pudo escribir los metadatos en el archivo');
    }

  } catch (error) {
    console.error('❌ Error incrustando carátula:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Endpoint para limpiar archivos antiguos
app.post('/api/cleanup', (req, res) => {
  try {
    const files = fs.readdirSync(DOWNLOAD_DIR);
    let deletedCount = 0;

    files.forEach(file => {
      const filePath = path.join(DOWNLOAD_DIR, file);
      const stats = fs.statSync(filePath);
      const ageInHours = (Date.now() - stats.mtimeMs) / (1000 * 60 * 60);

      // Eliminar archivos más antiguos de 24 horas
      if (ageInHours > 24) {
        fs.unlinkSync(filePath);
        deletedCount++;
      }
    });

    console.log(`🗑️ Limpieza completada: ${deletedCount} archivos eliminados`);
    
    res.json({
      success: true,
      deletedCount,
      message: `${deletedCount} archivos eliminados`
    });
  } catch (error) {
    console.error('❌ Error en limpieza:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Iniciar servidor
server.listen(PORT, '0.0.0.0', () => {
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🎵 SPOTYDOWN BACKEND SERVER');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`✅ Servidor corriendo en:`);
  console.log(`   • Local:    http://localhost:${PORT}`);
  console.log(`   • Red:      http://${localIP}:${PORT}`);
  console.log(`   • Socket:   ws://${localIP}:${PORT}`);
  console.log(`\n📁 Directorio de descargas: ${DOWNLOAD_DIR}`);
  console.log(`🖥️  Sistema: ${os.platform()} - ${os.hostname()}`);
  console.log('\n📱 Para conectar desde tu teléfono:');
  console.log(`   1. Asegúrate de estar en la misma red WiFi`);
  console.log(`   2. Usa esta URL en la app: http://${localIP}:${PORT}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
});

// Manejo de errores
process.on('uncaughtException', (error) => {
  console.error('❌ Error no capturado:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Promesa rechazada:', reason);
});
