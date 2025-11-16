# Usar Node.js 18 LTS
FROM node:18-slim

# Instalar Python y dependencias del sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de la app
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./
COPY requirements.txt ./

# Instalar dependencias de Node.js
RUN npm install --production

# Instalar dependencias de Python
RUN pip3 install --break-system-packages -r requirements.txt

# Copiar el resto de los archivos
COPY . .

# Crear directorio de descargas
RUN mkdir -p downloads

# Exponer el puerto (Render usa PORT env variable)
EXPOSE 10000

# Variable de entorno para el puerto
ENV PORT=10000

# Comando para iniciar el servidor
CMD ["node", "server.js"]
