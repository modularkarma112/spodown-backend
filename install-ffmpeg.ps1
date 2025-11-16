# Instalador de FFmpeg para Windows
# Descarga FFmpeg y lo configura en el sistema

$ErrorActionPreference = "Stop"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "🎬 INSTALADOR DE FFMPEG" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""

# Directorio de instalación
$installDir = "$PSScriptRoot\ffmpeg"
$binDir = "$installDir\bin"

# Crear directorio si no existe
if (!(Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}

Write-Host "📦 Descargando FFmpeg..." -ForegroundColor Yellow

# URL de FFmpeg (build estático de gyan.dev)
$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$zipFile = "$installDir\ffmpeg.zip"

try {
    # Descargar con progreso
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipFile -UseBasicParsing
    $ProgressPreference = 'Continue'
    
    Write-Host "✅ Descarga completada" -ForegroundColor Green
    Write-Host ""
    Write-Host "📂 Extrayendo archivos..." -ForegroundColor Yellow
    
    # Extraer ZIP
    Expand-Archive -Path $zipFile -DestinationPath $installDir -Force
    
    # Encontrar el directorio bin dentro del ZIP extraído
    $extractedDir = Get-ChildItem -Path $installDir -Directory | Where-Object { $_.Name -like "ffmpeg-*" } | Select-Object -First 1
    
    if ($extractedDir) {
        $extractedBinDir = Join-Path $extractedDir.FullName "bin"
        
        # Copiar archivos al directorio bin
        if (!(Test-Path $binDir)) {
            New-Item -ItemType Directory -Path $binDir | Out-Null
        }
        
        Copy-Item -Path "$extractedBinDir\*" -Destination $binDir -Force
        
        # Limpiar archivos temporales
        Remove-Item -Path $extractedDir.FullName -Recurse -Force
    }
    
    Remove-Item -Path $zipFile -Force
    
    Write-Host "✅ Extracción completada" -ForegroundColor Green
    Write-Host ""
    
    # Verificar instalación
    $ffmpegExe = Join-Path $binDir "ffmpeg.exe"
    $ffprobeExe = Join-Path $binDir "ffprobe.exe"
    
    if ((Test-Path $ffmpegExe) -and (Test-Path $ffprobeExe)) {
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
        Write-Host "✅ FFmpeg instalado correctamente" -ForegroundColor Green
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
        Write-Host ""
        Write-Host "📁 Ubicación: $binDir" -ForegroundColor Cyan
        Write-Host ""
        
        # Mostrar versiones
        $version = & $ffmpegExe -version 2>&1 | Select-Object -First 1
        Write-Host "🎬 $version" -ForegroundColor White
        Write-Host ""
        Write-Host "🔄 Reinicia el servidor Node.js para aplicar los cambios" -ForegroundColor Yellow
        Write-Host ""
    } else {
        throw "No se encontraron los ejecutables de FFmpeg"
    }
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}
