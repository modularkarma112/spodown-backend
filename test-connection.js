// Script para probar la conexión del servidor
const http = require('http');
const os = require('os');

function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return 'localhost';
}

const localIP = getLocalIP();
const PORT = process.env.PORT || 3000;

console.log('\n🧪 Probando conexión al servidor...\n');

// Probar localhost
http.get(`http://localhost:${PORT}/api/health`, (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => {
    console.log('✅ Localhost funciona:');
    console.log(`   http://localhost:${PORT}`);
    console.log(`   Respuesta: ${data}\n`);
  });
}).on('error', (err) => {
  console.log('❌ Error en localhost:', err.message, '\n');
});

// Probar IP local
setTimeout(() => {
  http.get(`http://${localIP}:${PORT}/api/health`, (res) => {
    let data = '';
    res.on('data', (chunk) => data += chunk);
    res.on('end', () => {
      console.log('✅ IP local funciona:');
      console.log(`   http://${localIP}:${PORT}`);
      console.log(`   Respuesta: ${data}\n`);
      console.log('📱 Usa esta URL en tu teléfono:');
      console.log(`   http://${localIP}:${PORT}\n`);
    });
  }).on('error', (err) => {
    console.log('❌ Error en IP local:', err.message);
    console.log('   Verifica que el servidor esté corriendo\n');
  });
}, 1000);
