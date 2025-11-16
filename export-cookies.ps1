# Script para exportar cookies de YouTube a Base64
# Uso: .\export-cookies.ps1

Write-Host "🍪 Exportador de Cookies de YouTube para Spodown" -ForegroundColor Cyan
Write-Host ""

# Verificar que existe el archivo de cookies
$cookiesFile = "youtube_cookies.txt"

if (-not (Test-Path $cookiesFile)) {
    Write-Host "❌ Error: No se encontró el archivo '$cookiesFile'" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Pasos para exportar cookies:" -ForegroundColor Yellow
    Write-Host "1. Instala la extensión 'Get cookies.txt LOCALLY' en Chrome"
    Write-Host "   URL: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
    Write-Host ""
    Write-Host "2. Ve a https://www.youtube.com (asegúrate de estar logueado)"
    Write-Host ""
    Write-Host "3. Click en el ícono de la extensión y exporta las cookies"
    Write-Host ""
    Write-Host "4. Guarda el archivo como 'youtube_cookies.txt' en esta carpeta:" -ForegroundColor Green
    Write-Host "   $PWD"
    Write-Host ""
    Write-Host "5. Ejecuta este script nuevamente" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host "✅ Archivo de cookies encontrado" -ForegroundColor Green
Write-Host ""

# Leer el contenido del archivo
$content = Get-Content $cookiesFile -Raw

# Convertir a Base64
$bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
$base64 = [Convert]::ToBase64String($bytes)

# Copiar al clipboard
$base64 | Set-Clipboard

Write-Host "✅ Cookies convertidas a Base64 y copiadas al clipboard" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Siguiente paso:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Ve a tu dashboard de Render: https://dashboard.render.com" -ForegroundColor Cyan
Write-Host "2. Selecciona tu servicio backend"
Write-Host "3. Ve a 'Environment' en el menú izquierdo"
Write-Host "4. Agrega una nueva variable de entorno:"
Write-Host "   - Key: YOUTUBE_COOKIES_BASE64" -ForegroundColor Green
Write-Host "   - Value: Pega el contenido del clipboard (Ctrl+V)" -ForegroundColor Green
Write-Host "5. Click 'Save Changes'"
Write-Host "6. Espera que Render redespliegue (2-3 minutos)"
Write-Host ""
Write-Host "🎉 ¡Listo! Las descargas deberían funcionar sin problemas" -ForegroundColor Green
Write-Host ""

# Mostrar preview
Write-Host "Preview (primeros 100 caracteres):" -ForegroundColor Gray
Write-Host $base64.Substring(0, [Math]::Min(100, $base64.Length)) -ForegroundColor DarkGray
Write-Host "... ($($base64.Length) caracteres total)" -ForegroundColor DarkGray
