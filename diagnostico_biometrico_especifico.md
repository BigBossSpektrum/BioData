📋 GUÍA DE DIAGNÓSTICO PARA DISPOSITIVO BIOMÉTRICO
=====================================================

🎯 PROBLEMA IDENTIFICADO:
- 🖥️ Computador (192.168.1.13): ✅ Conecta perfectamente al servidor
- 🤖 Biométrico (192.168.1.88): ❌ No envía datos al servidor

🔍 PASOS DE DIAGNÓSTICO:

1. 📡 PROBAR CONECTIVIDAD DESDE EL BIOMÉTRICO:
   
   A) ACCESO AL DISPOSITIVO:
   - Acceder a la interfaz web del biométrico: http://192.168.1.88
   - O usar software de configuración del dispositivo
   
   B) PING DESDE EL DISPOSITIVO:
   - Usar herramientas del dispositivo para ping a 186.31.35.24
   - Verificar si el dispositivo puede "ver" el servidor

2. ⚙️ VERIFICAR CONFIGURACIÓN DEL BIOMÉTRICO:
   
   A) URL DE ENVÍO:
   - Verificar que esté configurado: http://186.31.35.24:8000/api/recibir-datos-biometrico/
   - NO debe ser: https:// (usar HTTP)
   
   B) CONFIGURACIÓN DE RED:
   - IP: 192.168.1.88
   - Gateway: Debe ser el mismo que el computador (192.168.1.1)
   - DNS: Verificar configuración
   
   C) PUERTO Y PROTOCOLO:
   - Puerto: 8000
   - Protocolo: HTTP POST
   - Content-Type: application/json

3. 🧪 PRUEBA MANUAL DESDE EL COMPUTADOR:

   Simular envío como si fuera el biométrico:

```python
import requests
import json
from datetime import datetime

# Simular datos del biométrico 192.168.1.88
datos_test = [{
    "user_id": "TEST_88",
    "nombre": "Usuario_Test_Biometrico_88",
    "timestamp": datetime.now().isoformat(),
    "estacion": "San Mateo",  # Usar el nombre correcto de la estación
    "status": 0
}]

headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Biometrico-192.168.1.88/1.0',
    'X-Forwarded-For': '192.168.1.88',  # Simular IP del biométrico
    'X-Real-IP': '192.168.1.88'
}

try:
    response = requests.post(
        'http://186.31.35.24:8000/api/recibir-datos-biometrico/',
        json=datos_test,
        headers=headers,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Respuesta: {response.json()}")
    
except Exception as e:
    print(f"Error: {e}")
```

4. 🔧 CONFIGURACIONES COMUNES A VERIFICAR:

   A) EN EL DISPOSITIVO BIOMÉTRICO:
   - ✅ URL correcta: http://186.31.35.24:8000/api/recibir-datos-biometrico/
   - ✅ Método: POST
   - ✅ Formato: JSON
   - ✅ Timeout: 30-60 segundos
   - ✅ Puerto: 8000
   
   B) CONFIGURACIÓN DE RED:
   - ✅ Mismo gateway que el computador (192.168.1.1)
   - ✅ DNS funcional
   - ✅ Acceso a internet desde el dispositivo
   
   C) FIREWALL:
   - ✅ El dispositivo puede hacer conexiones salientes al puerto 8000
   - ✅ No hay bloqueo específico para la IP 192.168.1.88

5. 📊 MONITOREO EN TIEMPO REAL:

   A) Activar logs detallados en el servidor
   B) Hacer que el biométrico envíe un registro de prueba
   C) Verificar si llega al servidor con el logging mejorado

=====================================================

🚨 POSIBLES CAUSAS DEL PROBLEMA:

1. 🌐 CONFIGURACIÓN DE RED DEL BIOMÉTRICO:
   - Gateway incorrecto
   - DNS no configurado
   - Sin acceso a internet

2. ⚙️ CONFIGURACIÓN DEL ENDPOINT EN EL BIOMÉTRICO:
   - URL incorrecta
   - Puerto incorrecto  
   - Protocolo incorrecto (HTTPS vs HTTP)
   - Formato de datos incorrecto

3. 🔥 FIREWALL:
   - Bloqueo específico de la IP del biométrico
   - Puerto 8000 bloqueado para dispositivos
   - Reglas diferentes para equipos vs dispositivos

4. 🔧 CONFIGURACIÓN DEL DISPOSITIVO:
   - Dispositivo no configurado para envío automático
   - Frecuencia de envío deshabilitada
   - Error en credenciales o autenticación

=====================================================

✅ CONFIRMADO QUE FUNCIONA:
- 🖥️ Conectividad desde el computador (192.168.1.13)
- 🌐 Servidor accesible en 186.31.35.24:8000
- 📊 Endpoint funcionando correctamente
- 📝 Logging mejorado implementado

❓ FALTA VERIFICAR:
- 🤖 Configuración específica del dispositivo biométrico
- 🌐 Conectividad directa desde 192.168.1.88
- ⚙️ Parámetros de envío del dispositivo

=====================================================
