#!/usr/bin/env python
"""
Script para probar el endpoint de recepción de datos biométricos
Simula el envío desde diferentes estaciones para verificar el logging
"""

import requests
import json
from datetime import datetime, timedelta
import random

# Configuración del servidor
SERVER_URL = "http://127.0.0.1:8000/api/recibir-datos-biometrico/"

def generar_datos_prueba(estacion_nombre, num_registros=5):
    """Genera datos de prueba para una estación específica"""
    datos = []
    base_time = datetime.now() - timedelta(minutes=30)
    
    for i in range(num_registros):
        timestamp = base_time + timedelta(minutes=i*2)
        
        registro = {
            "user_id": f"{random.randint(1000, 9999)}",
            "nombre": f"Usuario_{random.randint(1, 100)}",
            "timestamp": timestamp.isoformat(),
            "estacion": estacion_nombre,
            "status": random.choice([0, 1])  # 0=entrada, 1=salida
        }
        datos.append(registro)
    
    return datos

def probar_estacion(estacion_nombre, ip_simulada=None):
    """Prueba el envío de datos desde una estación específica"""
    print(f"\n🧪 PROBANDO ESTACIÓN: {estacion_nombre}")
    print("-" * 50)
    
    # Generar datos de prueba
    datos_prueba = generar_datos_prueba(estacion_nombre, 3)
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': f'Biometrico-{estacion_nombre}/1.0'
    }
    
    # Si se especifica una IP simulada, agregar header
    if ip_simulada:
        headers['X-Forwarded-For'] = ip_simulada
    
    print(f"📦 Enviando {len(datos_prueba)} registros...")
    print(f"🌐 URL: {SERVER_URL}")
    if ip_simulada:
        print(f"🔧 IP simulada: {ip_simulada}")
    
    try:
        response = requests.post(
            SERVER_URL,
            json=datos_prueba,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 STATUS CODE: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            print("✅ RESPUESTA EXITOSA:")
            print(f"   🕐 Timestamp procesamiento: {resultado.get('timestamp_procesamiento')}")
            print(f"   🌐 IP detectada: {resultado.get('ip_cliente')}")
            
            resumen = resultado.get('resumen', {})
            print(f"   📈 Total procesados: {resumen.get('total_procesados')}")
            print(f"   ✅ Nuevos: {resumen.get('nuevos')}")
            print(f"   🔁 Duplicados: {resumen.get('duplicados')}")
            print(f"   ❌ Errores: {resumen.get('errores')}")
            
            estaciones_stats = resultado.get('estaciones', {})
            if estacion_nombre in estaciones_stats:
                stats = estaciones_stats[estacion_nombre]
                print(f"   📊 Estadísticas de {estacion_nombre}:")
                print(f"      📤 Enviados: {stats.get('total_enviados')}")
                print(f"      ✅ Nuevos: {stats.get('nuevos')}")
        else:
            print(f"❌ ERROR HTTP {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT - El servidor no respondió en 30 segundos")
    except requests.exceptions.ConnectionError:
        print("🔌 ERROR DE CONEXIÓN - No se pudo conectar al servidor")
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")

def probar_multiples_estaciones():
    """Prueba el envío desde múltiples estaciones simuladas"""
    
    estaciones_prueba = [
        {"nombre": "ESTACION_A", "ip": "192.168.1.100"},
        {"nombre": "ESTACION_B", "ip": "192.168.1.101"},
        {"nombre": "ESTACION_C", "ip": "192.168.1.102"},
        {"nombre": "OFICINA_CENTRAL", "ip": "192.168.1.50"},
    ]
    
    print("🚀 INICIANDO PRUEBAS DE MÚLTIPLES ESTACIONES")
    print("=" * 60)
    print(f"🕐 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for estacion in estaciones_prueba:
        probar_estacion(estacion["nombre"], estacion["ip"])
    
    print(f"\n🏁 PRUEBAS COMPLETADAS a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Verifica los logs del servidor Django")
    print("   2. Ejecuta: python monitorear_estaciones.py")
    print("   3. Revisa la base de datos para confirmar los datos")

def probar_datos_invalidos():
    """Prueba el manejo de datos inválidos"""
    print(f"\n🧪 PROBANDO DATOS INVÁLIDOS")
    print("-" * 50)
    
    casos_prueba = [
        {
            "nombre": "Sin lista (objeto directo)",
            "datos": {"user_id": "123", "timestamp": datetime.now().isoformat()}
        },
        {
            "nombre": "Lista con datos incompletos",
            "datos": [
                {"user_id": "123"},  # Sin timestamp ni estación
                {"timestamp": datetime.now().isoformat()},  # Sin user_id
            ]
        },
        {
            "nombre": "Estación inexistente",
            "datos": [
                {
                    "user_id": "999",
                    "timestamp": datetime.now().isoformat(),
                    "estacion": "ESTACION_INEXISTENTE",
                    "nombre": "Usuario Prueba"
                }
            ]
        }
    ]
    
    for caso in casos_prueba:
        print(f"\n🧪 Caso: {caso['nombre']}")
        try:
            response = requests.post(
                SERVER_URL,
                json=caso['datos'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            print(f"   📊 Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   ⚠️ Respuesta: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🔧 SCRIPT DE PRUEBA DE ENDPOINT BIOMÉTRICO")
    print("=" * 60)
    
    # Verificar conectividad básica
    try:
        response = requests.get(SERVER_URL.replace('recibir-datos-biometrico/', ''), timeout=5)
        print(f"✅ Servidor accesible (Status: {response.status_code})")
    except:
        print("❌ No se pudo conectar al servidor")
        print("   Verifica que Django esté ejecutándose en el puerto 8000")
        exit(1)
    
    # Ejecutar pruebas
    probar_multiples_estaciones()
    probar_datos_invalidos()
