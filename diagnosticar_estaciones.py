#!/usr/bin/env python
"""
Script para diagnosticar conectividad de estaciones específicas
"""

import requests
import json
from datetime import datetime
import socket

# Configuración del servidor
SERVER_URL = "http://186.31.35.24:8000/api/recibir-datos-biometrico/"
SERVER_IP = "186.31.35.24"
SERVER_PORT = 8000

def verificar_conectividad_servidor():
    """Verifica si el servidor está accesible desde esta máquina"""
    print("🌐 VERIFICANDO CONECTIVIDAD AL SERVIDOR")
    print("=" * 50)
    
    # Test 1: Ping/Conectividad básica
    print(f"📡 Probando conectividad a {SERVER_IP}:{SERVER_PORT}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((SERVER_IP, SERVER_PORT))
        sock.close()
        
        if result == 0:
            print(f"✅ Puerto {SERVER_PORT} ABIERTO en {SERVER_IP}")
        else:
            print(f"❌ Puerto {SERVER_PORT} CERRADO o INACCESIBLE en {SERVER_IP}")
            return False
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return False
    
    # Test 2: HTTP Request
    print(f"🌐 Probando HTTP request a {SERVER_URL}")
    try:
        response = requests.get(SERVER_URL.replace('recibir-datos-biometrico/', ''), timeout=10)
        print(f"✅ Servidor HTTP responde (Status: {response.status_code})")
        return True
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT - El servidor no responde en 10 segundos")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 ERROR DE CONEXIÓN - No se puede conectar al servidor")
        return False
    except Exception as e:
        print(f"❌ Error HTTP: {e}")
        return False

def simular_datos_desde_estacion(ip_estacion, nombre_estacion):
    """Simula envío de datos desde una estación específica"""
    print(f"\n🧪 SIMULANDO DATOS DESDE {ip_estacion} ({nombre_estacion})")
    print("-" * 50)
    
    # Datos de prueba específicos para esa estación
    timestamp_actual = datetime.now().isoformat()
    datos_prueba = [
        {
            "user_id": "9988",
            "nombre": f"Usuario_Test_{ip_estacion.replace('.', '_')}",
            "timestamp": timestamp_actual,
            "estacion": nombre_estacion,
            "status": 0  # Entrada
        }
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': f'Biometrico-{nombre_estacion}/1.0',
        'X-Forwarded-For': ip_estacion,  # Simular IP de origen
        'X-Real-IP': ip_estacion
    }
    
    print(f"📦 Enviando datos de prueba...")
    print(f"🌐 IP simulada: {ip_estacion}")
    print(f"📍 Estación: {nombre_estacion}")
    print(f"👤 Usuario: {datos_prueba[0]['user_id']}")
    
    try:
        response = requests.post(
            SERVER_URL,
            json=datos_prueba,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            print("✅ RESPUESTA EXITOSA:")
            print(f"   🕐 Timestamp: {resultado.get('timestamp_procesamiento')}")
            print(f"   🌐 IP detectada: {resultado.get('ip_cliente')}")
            
            resumen = resultado.get('resumen', {})
            print(f"   📈 Procesados: {resumen.get('total_procesados')}")
            print(f"   ✅ Nuevos: {resumen.get('nuevos')}")
            print(f"   ❌ Errores: {resumen.get('errores')}")
            
            estaciones = resultado.get('estaciones', {})
            if nombre_estacion in estaciones:
                stats = estaciones[nombre_estacion]
                print(f"   📊 Stats {nombre_estacion}: {stats}")
            
            return True
        else:
            print(f"❌ ERROR HTTP {response.status_code}")
            print(f"   Respuesta: {response.text[:300]}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT - El servidor no respondió en 30 segundos")
        print("   Posibles causas:")
        print("   - Firewall bloqueando la conexión")
        print("   - Servidor sobrecargado")
        print("   - Problemas de red")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 ERROR DE CONEXIÓN")
        print("   Posibles causas:")
        print("   - Servidor Django no está ejecutándose")
        print("   - Puerto 8000 no está abierto")
        print("   - Firewall bloqueando el puerto")
        return False
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        return False

def diagnostico_completo():
    """Ejecuta diagnóstico completo"""
    print("🔧 DIAGNÓSTICO DE ESTACIONES PROBLEMÁTICAS")
    print("=" * 60)
    print(f"🕐 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar servidor
    if not verificar_conectividad_servidor():
        print("\n❌ PROBLEMA: Servidor no accesible")
        print("   SOLUCIONES:")
        print("   1. Verificar que Django esté ejecutándose")
        print("   2. Verificar firewall/puertos")
        print("   3. Verificar configuración de red")
        return
    
    # Estaciones problemáticas reportadas
    estaciones_problematicas = [
        {"ip": "192.168.100.88", "nombre": "ESTACION_192_168_100_88"},
        {"ip": "192.168.1.88", "nombre": "ESTACION_192_168_1_88"}
    ]
    
    resultados = []
    
    for estacion in estaciones_problematicas:
        exito = simular_datos_desde_estacion(estacion["ip"], estacion["nombre"])
        resultados.append({
            "ip": estacion["ip"],
            "nombre": estacion["nombre"], 
            "exito": exito
        })
    
    # Resumen final
    print(f"\n📊 RESUMEN DE DIAGNÓSTICO")
    print("=" * 50)
    for resultado in resultados:
        estado = "✅ FUNCIONANDO" if resultado["exito"] else "❌ PROBLEMÁTICA"
        print(f"🌐 {resultado['ip']} ({resultado['nombre']}): {estado}")
    
    exitosos = sum(1 for r in resultados if r["exito"])
    print(f"\n📈 Estaciones exitosas: {exitosos}/{len(resultados)}")
    
    if exitosos < len(resultados):
        print(f"\n🛠️ RECOMENDACIONES PARA ESTACIONES PROBLEMÁTICAS:")
        print("   1. Verificar configuración de URL en el dispositivo biométrico")
        print("   2. Verificar conectividad de red desde esas IPs específicas")
        print("   3. Verificar firewall en las estaciones")
        print("   4. Probar con telnet desde esas IPs: telnet 186.31.35.24 8000")
        print("   5. Verificar configuración de proxy/gateway")

def test_firewall():
    """Prueba específica de firewall y conectividad"""
    print(f"\n🔥 PRUEBA DE FIREWALL Y CONECTIVIDAD")
    print("=" * 50)
    
    # Puertos comunes para probar
    puertos_test = [8000, 80, 443, 22]
    
    for puerto in puertos_test:
        print(f"🔌 Probando puerto {puerto}...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((SERVER_IP, puerto))
            sock.close()
            
            if result == 0:
                print(f"   ✅ Puerto {puerto} ABIERTO")
            else:
                print(f"   ❌ Puerto {puerto} CERRADO/FILTRADO")
        except Exception as e:
            print(f"   ❌ Error en puerto {puerto}: {e}")

if __name__ == "__main__":
    diagnostico_completo()
    test_firewall()
    
    print(f"\n✅ Diagnóstico completado a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Ejecutar este script desde las estaciones problemáticas")
    print("   2. Revisar logs del servidor cuando lleguen datos reales")
    print("   3. Verificar configuración de red en los dispositivos biométricos")
