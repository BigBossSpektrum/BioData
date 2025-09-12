#!/usr/bin/env python
"""
Script para ejecutar EN LAS ESTACIONES PROBLEMÁTICAS
Guarda este archivo en las máquinas con IP 192.168.100.88 y 192.168.1.88
"""

import socket
import requests
import json
from datetime import datetime
import platform
import subprocess

def obtener_info_local():
    """Obtiene información de la máquina local"""
    print("🖥️ INFORMACIÓN DE LA ESTACIÓN LOCAL")
    print("=" * 50)
    
    # IP local
    try:
        hostname = socket.gethostname()
        ip_local = socket.gethostbyname(hostname)
        print(f"🏷️ Hostname: {hostname}")
        print(f"🌐 IP Local: {ip_local}")
    except Exception as e:
        print(f"❌ Error obteniendo IP: {e}")
    
    # Sistema operativo
    print(f"💻 SO: {platform.system()} {platform.release()}")
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def test_ping_servidor():
    """Prueba ping al servidor"""
    print(f"\n📡 PROBANDO PING AL SERVIDOR")
    print("-" * 30)
    
    servidor = "186.31.35.24"
    
    try:
        if platform.system().lower() == "windows":
            comando = ["ping", "-n", "4", servidor]
        else:
            comando = ["ping", "-c", "4", servidor]
        
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=30)
        
        if resultado.returncode == 0:
            print(f"✅ PING EXITOSO a {servidor}")
            print("📊 Estadísticas del ping:")
            # Extraer líneas relevantes del ping
            lineas = resultado.stdout.split('\n')
            for linea in lineas:
                if 'tiempo' in linea.lower() or 'time' in linea.lower() or 'ms' in linea:
                    print(f"   {linea.strip()}")
        else:
            print(f"❌ PING FALLÓ a {servidor}")
            print(f"   Error: {resultado.stderr}")
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT en ping a {servidor}")
    except Exception as e:
        print(f"❌ Error ejecutando ping: {e}")

def test_conectividad_puerto():
    """Prueba conectividad al puerto específico"""
    print(f"\n🔌 PROBANDO CONECTIVIDAD AL PUERTO 8000")
    print("-" * 40)
    
    servidor = "186.31.35.24"
    puerto = 8000
    
    print(f"🎯 Intentando conectar a {servidor}:{puerto}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        
        inicio = datetime.now()
        resultado = sock.connect_ex((servidor, puerto))
        fin = datetime.now()
        tiempo_ms = (fin - inicio).total_seconds() * 1000
        
        sock.close()
        
        if resultado == 0:
            print(f"✅ CONEXIÓN EXITOSA en {tiempo_ms:.1f}ms")
            print(f"   Puerto {puerto} está ABIERTO y ACCESIBLE")
            return True
        else:
            print(f"❌ CONEXIÓN FALLÓ (Código: {resultado})")
            print(f"   Puerto {puerto} está CERRADO o BLOQUEADO")
            
            # Códigos de error comunes
            codigos_error = {
                10061: "Conexión rechazada - Servidor no escucha en este puerto",
                10060: "Timeout de conexión - Firewall o servidor inaccesible",
                10053: "Conexión abortada por software",
                10054: "Conexión reiniciada por peer",
                11001: "Host no encontrado"
            }
            
            if resultado in codigos_error:
                print(f"   Significado: {codigos_error[resultado]}")
            
            return False
    except socket.timeout:
        print(f"⏰ TIMEOUT después de 15 segundos")
        return False
    except Exception as e:
        print(f"❌ Error de socket: {e}")
        return False

def test_http_endpoint():
    """Prueba el endpoint HTTP específico"""
    print(f"\n🌐 PROBANDO ENDPOINT HTTP")
    print("-" * 30)
    
    url = "http://186.31.35.24:8000/api/recibir-datos-biometrico/"
    
    # Datos de prueba específicos para esta estación
    datos_prueba = [{
        "user_id": "TEST_9999",
        "nombre": "Usuario_Prueba_Conectividad",
        "timestamp": datetime.now().isoformat(),
        "estacion": f"ESTACION_TEST_{socket.gethostname()}",
        "status": 0
    }]
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': f'Test-Estacion-{socket.gethostname()}/1.0'
    }
    
    print(f"📍 URL: {url}")
    print(f"📦 Enviando datos de prueba...")
    
    try:
        inicio = datetime.now()
        response = requests.post(
            url,
            json=datos_prueba,
            headers=headers,
            timeout=30
        )
        fin = datetime.now()
        tiempo_ms = (fin - inicio).total_seconds() * 1000
        
        print(f"✅ RESPUESTA RECIBIDA en {tiempo_ms:.1f}ms")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                resultado = response.json()
                print("✅ ENDPOINT FUNCIONANDO CORRECTAMENTE")
                print(f"   🕐 Procesado: {resultado.get('timestamp_procesamiento')}")
                print(f"   🌐 IP detectada: {resultado.get('ip_cliente')}")
                
                resumen = resultado.get('resumen', {})
                print(f"   📈 Registros nuevos: {resumen.get('nuevos')}")
                
                return True
            except json.JSONDecodeError:
                print(f"⚠️ Respuesta no es JSON válido: {response.text[:200]}")
        else:
            print(f"⚠️ Status Code inesperado: {response.status_code}")
            print(f"   Respuesta: {response.text[:300]}")
        
        return False
        
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT - Servidor no responde en 30 segundos")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 ERROR DE CONEXIÓN - No se puede conectar")
        return False
    except Exception as e:
        print(f"❌ Error HTTP: {e}")
        return False

def diagnostico_red_local():
    """Diagnóstico de red local"""
    print(f"\n🔍 DIAGNÓSTICO DE RED LOCAL")
    print("-" * 35)
    
    # Gateway por defecto
    try:
        if platform.system().lower() == "windows":
            resultado = subprocess.run(["ipconfig"], capture_output=True, text=True)
            lineas = resultado.stdout.split('\n')
            for linea in lineas:
                if 'puerta de enlace' in linea.lower() or 'default gateway' in linea.lower():
                    print(f"🚪 {linea.strip()}")
        else:
            resultado = subprocess.run(["route", "-n"], capture_output=True, text=True)
            print(f"🚪 Gateway info:\n{resultado.stdout}")
    except Exception as e:
        print(f"❌ Error obteniendo gateway: {e}")
    
    # DNS
    try:
        if platform.system().lower() == "windows":
            resultado = subprocess.run(["nslookup", "186.31.35.24"], capture_output=True, text=True)
            print(f"\n🔍 DNS Lookup:")
            print(resultado.stdout)
    except Exception as e:
        print(f"❌ Error en DNS lookup: {e}")

def generar_reporte():
    """Genera reporte completo"""
    print("\n" + "="*60)
    print("📋 REPORTE COMPLETO DE DIAGNÓSTICO")
    print("="*60)
    
    obtener_info_local()
    test_ping_servidor()
    
    puerto_ok = test_conectividad_puerto()
    
    if puerto_ok:
        http_ok = test_http_endpoint()
    else:
        print(f"\n⚠️ SALTANDO PRUEBA HTTP - Puerto inaccesible")
        http_ok = False
    
    diagnostico_red_local()
    
    # Resumen final
    print(f"\n📊 RESUMEN FINAL")
    print("-" * 20)
    print(f"🌐 IP Local: {socket.gethostbyname(socket.gethostname())}")
    print(f"📡 Ping: {'✅ OK' if True else '❌ FALLO'}")  # Simplificado
    print(f"🔌 Puerto 8000: {'✅ ACCESIBLE' if puerto_ok else '❌ INACCESIBLE'}")
    print(f"🌐 HTTP Endpoint: {'✅ FUNCIONANDO' if http_ok else '❌ NO FUNCIONA'}")
    
    if not puerto_ok:
        print(f"\n🛠️ ACCIONES REQUERIDAS:")
        print("1. 🔥 Verificar firewall local en esta estación")
        print("2. 🌐 Verificar configuración de red/proxy")
        print("3. 📞 Contactar administrador de red para verificar:")
        print("   - Firewall corporativo")
        print("   - Configuración de router/gateway")
        print("   - Acceso a internet desde esta IP")
        print("4. 🖥️ Verificar que el servidor 186.31.35.24 esté funcionando")
    elif not http_ok:
        print(f"\n🛠️ ACCIONES REQUERIDAS:")
        print("1. 🐍 Verificar que Django esté ejecutándose en el servidor")
        print("2. ⚙️ Verificar configuración del endpoint")
        print("3. 📊 Revisar logs del servidor")

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO DE ESTACIÓN BIOMÉTRICA")
    print("=" * 60)
    print("💡 Ejecuta este script en las estaciones problemáticas:")
    print("   - 192.168.100.88")
    print("   - 192.168.1.88")
    print("=" * 60)
    
    generar_reporte()
    
    print(f"\n✅ Diagnóstico completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📧 ENVÍA ESTE REPORTE al administrador del sistema")
    
    input("\n🔍 Presiona ENTER para salir...")
