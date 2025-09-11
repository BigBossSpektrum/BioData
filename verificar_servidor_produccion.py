#!/usr/bin/env python
"""
Script para verificar el estado del servidor en producción
"""

import requests
import subprocess
import socket
from datetime import datetime

def verificar_servidor_produccion():
    """Verifica el estado del servidor de producción"""
    
    servidor_prod = "186.31.35.24"
    puerto = 8000
    
    print("🏥 VERIFICANDO SERVIDOR DE PRODUCCIÓN")
    print("=" * 50)
    print(f"🌐 Servidor: {servidor_prod}:{puerto}")
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test de conectividad básica
    print(f"\n📡 Probando conectividad básica...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((servidor_prod, puerto))
        sock.close()
        
        if result == 0:
            print(f"✅ Puerto {puerto} ACCESIBLE")
        else:
            print(f"❌ Puerto {puerto} INACCESIBLE (Código: {result})")
            print("   Posibles causas:")
            print("   - Servidor Django no está ejecutándose")
            print("   - Firewall bloqueando el puerto")
            print("   - Servidor fuera de línea")
            return False
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return False
    
    # Test HTTP
    print(f"\n🌐 Probando endpoint HTTP...")
    urls_test = [
        f"http://{servidor_prod}:{puerto}/",
        f"http://{servidor_prod}:{puerto}/api/",
        f"http://{servidor_prod}:{puerto}/api/recibir-datos-biometrico/"
    ]
    
    for url in urls_test:
        try:
            print(f"   📍 Probando: {url}")
            response = requests.get(url, timeout=15)
            print(f"      ✅ Status: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"      ⏰ TIMEOUT (>15s)")
        except requests.exceptions.ConnectionError:
            print(f"      🔌 ERROR DE CONEXIÓN")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    return True

def comando_para_estaciones():
    """Genera comandos para probar desde las estaciones"""
    
    print(f"\n🔧 COMANDOS PARA EJECUTAR EN LAS ESTACIONES")
    print("=" * 50)
    
    servidor = "186.31.35.24"
    puerto = 8000
    
    print("📝 Desde Windows (CMD):")
    print(f"   telnet {servidor} {puerto}")
    print(f"   ping {servidor}")
    print(f"   nslookup {servidor}")
    
    print("\n📝 Desde Linux/Unix:")
    print(f"   telnet {servidor} {puerto}")
    print(f"   nc -zv {servidor} {puerto}")
    print(f"   curl -I http://{servidor}:{puerto}/")
    
    print("\n📝 Desde Python (crear archivo test_conexion.py):")
    codigo_python = f'''
import socket
import requests
from datetime import datetime

def test_conexion():
    servidor = "{servidor}"
    puerto = {puerto}
    
    print(f"🧪 Probando desde esta estación: {{datetime.now()}}")
    
    # Test socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((servidor, puerto))
        sock.close()
        
        if result == 0:
            print(f"✅ Conectividad OK al puerto {{puerto}}")
        else:
            print(f"❌ No se puede conectar al puerto {{puerto}}")
    except Exception as e:
        print(f"❌ Error: {{e}}")
    
    # Test HTTP
    try:
        url = f"http://{{servidor}}:{{puerto}}/api/recibir-datos-biometrico/"
        response = requests.post(url, json=[{{"test": "conexion"}}], timeout=10)
        print(f"✅ HTTP funciona: Status {{response.status_code}}")
    except Exception as e:
        print(f"❌ HTTP error: {{e}}")

if __name__ == "__main__":
    test_conexion()
'''
    
    print(f"```python{codigo_python}```")

if __name__ == "__main__":
    verificar_servidor_produccion()
    comando_para_estaciones()
    
    print(f"\n💡 RECOMENDACIONES:")
    print("1. 🔥 Verificar firewall en servidor 186.31.35.24")
    print("2. 🐍 Verificar que Django esté ejecutándose en el servidor")
    print("3. 🌐 Verificar configuración de red/routing")
    print("4. 📱 Probar comandos desde las estaciones problemáticas")
    print("5. 🔧 Considerar usar puerto estándar (80/443) si es posible")
