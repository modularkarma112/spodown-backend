# 🍪 Guía para Exportar Cookies de YouTube

## Método 1: Extensión de Chrome (Más Fácil)

### Paso 1: Instalar Extensión
1. Abre Chrome
2. Ve a: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
3. Click en "Agregar a Chrome"

### Paso 2: Exportar Cookies
1. Ve a https://www.youtube.com (asegúrate de estar logueado)
2. Click en el ícono de la extensión (arriba a la derecha)
3. Click en "Export" o "Export as cookies.txt"
4. Guarda el archivo como `youtube_cookies.txt`

### Paso 3: Subir a Render
1. Ve a tu dashboard de Render: https://dashboard.render.com
2. Selecciona tu servicio backend
3. Ve a la pestaña "Shell" (consola)
4. Copia el contenido del archivo `youtube_cookies.txt`
5. En la shell de Render ejecuta:
   ```bash
   cat > /etc/youtube_cookies.txt << 'EOF'
   # Pega aquí el contenido de youtube_cookies.txt
   EOF
   ```

## Método 2: Exportar Manualmente con DevTools

### Paso 1: Obtener Cookies
1. Abre Chrome
2. Ve a https://www.youtube.com (logueado)
3. Presiona F12 para abrir DevTools
4. Ve a la pestaña "Application" (o "Aplicación")
5. En el panel izquierdo: Storage → Cookies → https://www.youtube.com
6. Busca estas cookies importantes:
   - `__Secure-1PSID`
   - `__Secure-1PAPISID`
   - `__Secure-1PSIDTS`
   - `CONSENT`
   - `VISITOR_INFO1_LIVE`

### Paso 2: Crear archivo cookies.txt manualmente
Crea un archivo `youtube_cookies.txt` con este formato:

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	0	__Secure-1PSID	[VALOR_DE_LA_COOKIE]
.youtube.com	TRUE	/	TRUE	0	__Secure-1PAPISID	[VALOR_DE_LA_COOKIE]
.youtube.com	TRUE	/	TRUE	0	__Secure-1PSIDTS	[VALOR_DE_LA_COOKIE]
.youtube.com	TRUE	/	TRUE	0	CONSENT	[VALOR_DE_LA_COOKIE]
.youtube.com	TRUE	/	TRUE	0	VISITOR_INFO1_LIVE	[VALOR_DE_LA_COOKIE]
```

Reemplaza `[VALOR_DE_LA_COOKIE]` con los valores reales de DevTools.

## Método 3: Usar Variable de Entorno en Render (Recomendado)

### Paso 1: Exportar cookies con extensión (ver Método 1)

### Paso 2: Convertir a Base64
En PowerShell:
```powershell
$content = Get-Content "youtube_cookies.txt" -Raw
$bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
$base64 = [Convert]::ToBase64String($bytes)
$base64 | Set-Clipboard
Write-Host "Cookies copiadas al clipboard en Base64"
```

### Paso 3: Configurar Variable de Entorno en Render
1. Ve a tu servicio en Render Dashboard
2. Ve a "Environment" en el menú izquierdo
3. Agrega nueva variable:
   - **Key**: `YOUTUBE_COOKIES_BASE64`
   - **Value**: Pega el contenido del clipboard (Base64)
4. Click "Save Changes"
5. Render redesplegará automáticamente

## ⚠️ Notas Importantes

- Las cookies expiran. Si deja de funcionar, repite el proceso
- Nunca compartas tus cookies públicamente (son como tu contraseña)
- Las cookies se renuevan cada vez que usas YouTube normalmente
- Si cambias la contraseña de Google, necesitas exportar nuevas cookies

## 🔍 Verificar que funciona

Después de configurar las cookies, prueba descargar una canción. Si ves:

```
✅ Descargando desde YouTube...
✅ Convirtiendo a MP3...
```

¡Funcionó! 🎉
