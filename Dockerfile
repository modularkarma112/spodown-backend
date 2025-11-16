# Usar Node.js 18 LTS
FROM node:18-slim

# Instalar Python, pip y dependencias del sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de la app
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./
COPY requirements.txt ./

# Instalar dependencias de Node.js
RUN npm ci --only=production

# Instalar yt-dlp globalmente
RUN pip3 install --break-system-packages yt-dlp

# Copiar el resto de los archivos
COPY . .

# Crear directorio de descargas
RUN mkdir -p downloads

# Exponer el puerto (Render usa PORT env variable)
EXPOSE 10000

# Variable de entorno para el puerto
ENV PORT=10000
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:10000/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1); });"

# Comando para iniciar el servidor
CMD ["node", "server.js"]
