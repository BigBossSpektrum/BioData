#!/usr/bin/env python
"""
Simulador de envío desde el dispositivo biométrico 192.168.1.88
Ejecutar desde el computador 192.168.1.13 para probar el endpoint
"""

import requests
import json
from datetime import datetime

def simular_biometrico_192_168_1_88():
    """Simula envío de datos desde el dispositivo biométrico"""
    
    print("🤖 SIMULANDO DISPOSITIVO BIOMÉTRICO 192.168.1.88")
    print("=" * 55)
    
    # URL del servidor (cambiar a local para pruebas)
    url = "http://127.0.0.1:8000/api/recibir-datos-biometrico/"
    
    # Datos simulados del biométrico
    datos_biometrico = [
        {
            "user_id": 9988,  # Debe ser número entero
            "nombre": "Usuario_Test_Biometrico_1_88",
            "timestamp": datetime.now().isoformat(),
            "estacion": "San Mateo",  # Nombre de la estación creada
            "status": 0  # 0=entrada, 1=salida
        },
        {
            "user_id": 9989,  # Debe ser número entero
            "nombre": "Usuario_Test_Biometrico_2_88",
            "timestamp": datetime.now().isoformat(),
            "estacion": "San Mateo",
            "status": 1
        }
    ]
    
    # Headers simulando el dispositivo biométrico
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'ZKTeco-Biometric-Device/1.0',
        'X-Forwarded-For': '192.168.1.88',  # Simular IP del biométrico
        'X-Real-IP': '192.168.1.88',
        'X-Device-IP': '192.168.1.88'
    }
    
    print(f"📍 URL destino: {url}")
    print(f"🤖 IP simulada del biométrico: 192.168.1.88")
    print(f"📦 Enviando {len(datos_biometrico)} registros...")
    
    for i, registro in enumerate(datos_biometrico, 1):
        print(f"   📝 Registro {i}: Usuario {registro['user_id']} - {registro['nombre']}")
    
    try:
        print(f"\n🚀 Enviando datos al servidor...")
        inicio = datetime.now()
        
        response = requests.post(
            url,
            json=datos_biometrico,
            headers=headers,
            timeout=30
        )
        
        fin = datetime.now()
        tiempo_ms = (fin - inicio).total_seconds() * 1000
        
        print(f"⏱️ Tiempo de respuesta: {tiempo_ms:.1f}ms")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                resultado = response.json()
                print("\n✅ RESPUESTA EXITOSA DEL SERVIDOR:")
                print(f"   🕐 Timestamp procesamiento: {resultado.get('timestamp_procesamiento')}")
                print(f"   🌐 IP detectada por servidor: {resultado.get('ip_cliente')}")
                
                resumen = resultado.get('resumen', {})
                print(f"\n📈 RESUMEN DEL PROCESAMIENTO:")
                print(f"   📦 Total procesados: {resumen.get('total_procesados')}")
                print(f"   ✅ Registros nuevos: {resumen.get('nuevos')}")
                print(f"   🔁 Registros duplicados: {resumen.get('duplicados')}")
                print(f"   ❌ Registros con error: {resumen.get('errores')}")
                print(f"   👤 Usuarios nuevos: {resumen.get('usuarios_nuevos')}")
                print(f"   ✏️ Usuarios actualizados: {resumen.get('usuarios_actualizados')}")
                
                estaciones = resultado.get('estaciones', {})
                print(f"\n📊 ESTADÍSTICAS POR ESTACIÓN:")
                for nombre_estacion, stats in estaciones.items():
                    print(f"   🏢 {nombre_estacion}:")
                    print(f"      📤 Enviados: {stats.get('total_enviados')}")
                    print(f"      ✅ Nuevos: {stats.get('nuevos')}")
                    print(f"      🔁 Duplicados: {stats.get('duplicados')}")
                    print(f"      ❌ Errores: {stats.get('errores')}")
                    print(f"      🕐 Rango: {stats.get('primer_timestamp')} → {stats.get('ultimo_timestamp')}")
                
                print(f"\n🎯 CONCLUSIÓN: El endpoint SÍ puede procesar datos del biométrico")
                return True
                
            except json.JSONDecodeError as e:
                print(f"⚠️ Respuesta no es JSON válido: {e}")
                print(f"Respuesta raw: {response.text[:500]}")
                return False
        else:
            print(f"\n❌ ERROR HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error')}")
                print(f"   Detalle: {error_data.get('detalle')}")
            except:
                print(f"   Respuesta: {response.text[:300]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n⏰ TIMEOUT - Servidor no respondió en 30 segundos")
        print("   Posibles causas:")
        print("   - Servidor sobrecargado")
        print("   - Problemas de red")
        print("   - Firewall bloqueando la conexión")
        return False
        
    except requests.exceptions.ConnectionError:
        print(f"\n🔌 ERROR DE CONEXIÓN")
        print("   Posibles causas:")
        print("   - Servidor Django no está ejecutándose")
        print("   - Problemas de conectividad a 186.31.35.24:8000")
        print("   - Firewall bloqueando el puerto 8000")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        return False

def verificar_datos_recibidos():
    """Verifica si los datos llegaron a la base de datos"""
    print(f"\n🔍 VERIFICACIÓN DE DATOS RECIBIDOS")
    print("=" * 40)
    print("💡 Ejecuta estos comandos para verificar:")
    print("   1. python monitorear_estaciones.py")
    print("   2. Buscar usuarios con ID: TEST_BIOM_88, TEST_BIOM_89")
    print("   3. Verificar registros en estación 'San Mateo'")

if __name__ == "__main__":
    print("🧪 SIMULADOR DE DISPOSITIVO BIOMÉTRICO")
    print("=" * 60)
    print("💡 Este script simula el envío de datos desde el dispositivo")
    print("   biométrico 192.168.1.88 hacia el servidor.")
    print("=" * 60)
    
    exito = simular_biometrico_192_168_1_88()
    
    if exito:
        verificar_datos_recibidos()
        print(f"\n✅ SIMULACIÓN EXITOSA")
        print("🔧 PRÓXIMO PASO: Configurar el dispositivo biométrico real")
        print("   para que envíe a: http://186.31.35.24:8000/api/recibir-datos-biometrico/")
    else:
        print(f"\n❌ SIMULACIÓN FALLÓ")
        print("🔧 REVISAR: Conectividad y configuración del servidor")
    
    print(f"\n🕐 Simulación completada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
