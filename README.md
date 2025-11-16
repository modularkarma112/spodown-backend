# 🎵 Spodown Backend - Sistema Multi-Fuente

Backend mejorado con soporte para YouTube, SoundCloud y Bandcamp. Detección automática de fuentes alternativas cuando YouTube falla.

## 🚀 Características Nuevas

### Sistema de Descarga Inteligente
- **Multi-fuente automática**: Intenta YouTube → SoundCloud → Bandcamp
- **Soporte de cookies de YouTube**: Evita detección de bots (opcional)
- **Fallback robusto**: Si una fuente falla, prueba la siguiente automáticamente
- **Rate limiting inteligente**: Delays entre reintentos

### Fuentes Soportadas
1. **YouTube** (requiere cookies opcionales para mejor confiabilidad)
2. **SoundCloud** (sin autenticación, funciona siempre)
3. **Bandcamp** (sin autenticación, música independiente)

## 📋 Requisitos

- Python 3.10+
- `yt-dlp` y `ffmpeg` instalados
- Credenciales de Spotify (Client ID y Client Secret)
- **Opcional**: Cookies de YouTube para mejor confiabilidad

## 🔧 Configuración Local

### 1. Crea archivo `.env`

```bash
cd backend
```

Crea `.env` con:

```env
SPOTIFY_CLIENT_ID=tu_id
SPOTIFY_CLIENT_SECRET=tu_secret
SPOTIFY_REDIRECT_URI=http://localhost:8080/callback

# Opcional: Mejora descargas de YouTube
# YOUTUBE_COOKIES_BASE64=<base64_de_tus_cookies>
```

### 2. Instala dependencias

```bash
# Con uv (recomendado)
uv sync

# O con pip
pip install -r requirements.txt
```

### 3. Ejecuta el servidor

```bash
uv run uvicorn app.main:app --reload --port 8000
# O: uvicorn app.main:app --reload --port 8000
```

## 🍪 Cookies de YouTube (Opcional pero Recomendado)

Sin cookies, YouTube bloqueará la mayoría de descargas. El backend automáticamente usará SoundCloud/Bandcamp como alternativa.

### Método Rápido: Exportar cookies

1. Instala [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Abre ventana incógnito → Ve a `https://www.youtube.com/robots.txt`
3. Exporta cookies como `youtube_cookies.txt`
4. Guárdalo en `backend/youtube_cookies.txt`

Ver [COOKIES_SETUP.md](./COOKIES_SETUP.md) para instrucciones completas.

## 🌐 Deploy en Render.com

### Deploy Automático

```bash
git add .
git commit -m "Update backend with multi-source support"
git push origin master
```

Render detecta cambios y redeplega automáticamente.

### Variables de Entorno en Render

En Dashboard → Environment:

```bash
# Opcional: Mejora YouTube (base64 de youtube_cookies.txt)
YOUTUBE_COOKIES_BASE64=<tu_base64>

# Spotify credentials
SPOTIFY_CLIENT_ID=tu_id
SPOTIFY_CLIENT_SECRET=tu_secret
```

## 📡 Endpoints

- `GET /health` – Verificación del servicio
- `POST /playlists/export?playlist_id=...` – Obtiene tracks de Spotify
- `POST /playlists/download` – Descarga track individual
- `POST /playlists/download/batch` – Descarga playlist completa

### Ejemplo de uso

```bash
# Test básico
curl http://localhost:8000/health

# Descargar playlist
curl -X POST http://localhost:8000/playlists/download/batch \
  -H "Content-Type: application/json" \
  -d '{"playlist_id": "37i9dQZF1DXcBWIGoYBM5M"}'
```

## 📊 Logs y Monitoreo

### Símbolos en logs

- `🔍` = Búsqueda en fuente
- `📺` = Intento de YouTube  
- `🎵` = SoundCloud/Bandcamp
- `🍪` = Usando cookies
- `✅` = Descarga exitosa
- `⚠` = Warning/fallback

### Ejemplo: Descarga exitosa sin cookies

```
🔍 Intento 1/3: Buscando en ytsearch
  📺 YouTube query 1: Song Name Artist audio...
  ⚠ YouTube requiere cookies - intento 1 falló
🔍 Intento 2/3: Buscando en scsearch
  🎵 Buscando en SoundCloud...
  ✅ Descargado desde SoundCloud: Song.mp3 (3.2 MB)
```

### Ejemplo: Con cookies de YouTube

```
🔍 Intento 1/3: Buscando en ytsearch
  📺 YouTube query 1: Song Name Artist audio...
  🍪 Usando cookies: /tmp/youtube_cookies.txt
  ✅ Descargado desde YouTube: Song.mp3 (4.1 MB)
```

## 🛠️ Solución de Problemas

### "Sign in to confirm you're not a bot"

**Sin cookies:**
- Esperado. SoundCloud/Bandcamp se usarán automáticamente.

**Con cookies:**
- Cookies expiraron. Exporta nuevas cookies (ver COOKIES_SETUP.md).
- Asegúrate de usar ventana incógnito al exportar.

### Todas las fuentes fallan

```bash
# Actualiza yt-dlp
pip install --upgrade yt-dlp

# Prueba manual
yt-dlp "scsearch:test song" --extract-audio --audio-format mp3
```

### YouTube siempre falla

Normal sin cookies. Soluciones:

1. **Agrega cookies** (ver sección arriba)
2. **Usa SoundCloud** (funciona sin configuración)
3. **Espera 1 hora** si IP bloqueada

## 📝 Configuración Avanzada

### Formato de salida

- **Formato**: MP3 192kbps
- **Naming**: `{Title} - {Artist}.mp3`
- **Metadata**: Incluida automáticamente
- **Ubicación**: `/tmp/spodown_downloads/` (Linux) o `%TEMP%\spodown_downloads\` (Windows)

### Timeouts

- YouTube: 180s por query
- SoundCloud/Bandcamp: 150s
- Delay entre fuentes: 3s

### Filtros de búsqueda

- Duración: 30s - 10min
- Excluye: streams en vivo
- Calidad: mejor audio disponible

## 🔗 Enlaces Útiles

- [yt-dlp Wiki](https://github.com/yt-dlp/yt-dlp)
- [YouTube Extractors Guide](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#youtube)
- [COOKIES_SETUP.md](./COOKIES_SETUP.md) - Guía completa de cookies

## 📄 Licencia

MIT

