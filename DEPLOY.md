# 🚀 Guía de Despliegue en Render

## Paso 1: Crear/Actualizar Repositorio en GitHub

### Si NO tienes repositorio:
1. Ve a https://github.com/new
2. Nombre: `spotydown-backend` (o el que prefieras)
3. Descripción: "Backend para Spotydown - Descarga de música con Socket.IO"
4. Selecciona "Public" o "Private"
5. **NO** marques "Add README" (ya lo tenemos)
6. Click "Create repository"

### Si YA tienes repositorio:
Anota el URL: `https://github.com/TU_USUARIO/TU_REPO.git`

## Paso 2: Conectar y Subir Código

```bash
# Si es NUEVO repositorio:
git remote add origin https://github.com/TU_USUARIO/spotydown-backend.git
git branch -M main
git push -u origin main

# Si REEMPLAZAS repositorio existente:
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -f origin main  # -f fuerza el reemplazo
```

## Paso 3: Desplegar en Render

### Opción A: Desde Dashboard (Recomendado)

1. Ve a https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect a repository"**
4. Busca y selecciona tu repositorio `spotydown-backend`
5. Render detectará automáticamente `render.yaml`
6. Click **"Apply"** y luego **"Create Web Service"**

### Opción B: Con Blueprint (Automático)

1. En Render Dashboard, click **"New +"** → **"Blueprint"**
2. Conecta tu repositorio
3. Render leerá `render.yaml` y configurará todo automáticamente

## Paso 4: Obtener URL de Producción

Después de desplegar (toma ~5 minutos):

1. Ve a tu servicio en Render Dashboard
2. Copia la URL (algo como `https://spotydown-backend.onrender.com`)
3. **Guarda esta URL** - la necesitarás en la app Flutter

## Paso 5: Configurar Flutter App

En tu app Flutter, cambia la URL del servidor:

```dart
// lib/services/music_service.dart o donde configures la URL
final serverUrl = 'https://spotydown-backend.onrender.com';
```

## 🔧 Configuración Avanzada (Opcional)

### Variables de Entorno en Render

Si necesitas configurar Spotify o YouTube cookies:

1. En tu servicio → **"Environment"**
2. Agrega variables:
   - `SPOTIFY_CLIENT_ID`: tu_client_id
   - `SPOTIFY_CLIENT_SECRET`: tu_client_secret
   - `YOUTUBE_COOKIES_BASE64`: (opcional, para evitar bloqueos)

### Actualizar el Código

Cada vez que hagas cambios:

```bash
git add .
git commit -m "Descripción de cambios"
git push
```

Render detectará el push y redesplegaráautomáticamente 🎉

## ⚠️ Notas Importantes

### Plan Free de Render:
- ✅ Gratis para siempre
- ⚠️ Se "duerme" después de 15 minutos sin uso
- ⚠️ Primer request después de dormir toma ~30 segundos
- ✅ 750 horas/mes gratis (suficiente para uso personal)

### Solución al "Sleep":
En Flutter, agrega un retry si el servidor está dormido:

```dart
try {
  final response = await http.get(url).timeout(Duration(seconds: 45));
  // ...
} catch (e) {
  // Reintentar una vez (el servidor despertó)
  await Future.delayed(Duration(seconds: 2));
  final response = await http.get(url);
}
```

## 🎯 Siguiente Paso

Después de desplegar, prueba tu servidor:

```bash
curl https://TU_URL.onrender.com/api/health
```

Deberías ver:
```json
{
  "status": "ok",
  "message": "Servidor funcionando correctamente",
  ...
}
```

## 🆘 Problemas Comunes

### "Build failed"
- Verifica que `package.json` tenga `"node": ">=16.0.0"` en engines
- Revisa los logs en Render Dashboard

### "Service Unavailable"
- Espera 5 minutos (build inicial toma tiempo)
- Verifica que el puerto sea dinámico: `process.env.PORT`

### No conecta desde Flutter
- Usa HTTPS en producción (HTTP bloqueado en Android)
- Verifica CORS en `server.js` (debe permitir `*` o tu dominio)

---

¿Listo para desplegar? 🚀
Pega el comando de tu Paso 2 en la terminal!
