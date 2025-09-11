#!/usr/bin/env python
"""
Script para probar el endpoint de producción y enviar datos de prueba
a tu servidor real en 186.31.35.24:8000
"""

import requests
import json
from datetime import datetime, timedelta

# URL de tu servidor en producción
SERVIDOR_PRODUCCION = "http://186.31.35.24:8000"
ENDPOINT = f"{SERVIDOR_PRODUCCION}/api/recibir-datos-biometrico/"

def crear_datos_prueba_produccion():
    """Crea datos de prueba realistas para enviar a producción"""
    ahora = datetime.now()
    
    datos_prueba = [
        {
            "user_id": 101,
            "nombre": "Carlos Rodríguez",
            "timestamp": (ahora - timedelta(hours=8)).isoformat(),
            "estacion": "PRINCIPAL",
            "status": 0  # Entrada
        },
        {
            "user_id": 102,
            "nombre": "Ana López",
            "timestamp": (ahora - timedelta(hours=7, minutes=30)).isoformat(),
            "estacion": "La Soledad",
            "status": 0  # Entrada
        },
        {
            "user_id": 101,
            "nombre": "Carlos Rodríguez",
            "timestamp": (ahora - timedelta(minutes=30)).isoformat(),
            "estacion": "PRINCIPAL",
            "status": 1  # Salida
        }
    ]
    
    return datos_prueba

def probar_servidor_produccion():
    """Prueba el servidor de producción enviando datos de prueba"""
    print("🌐 PROBANDO SERVIDOR DE PRODUCCIÓN")
    print("=" * 60)
    print(f"🔗 URL: {ENDPOINT}")
    print(f"🕐 Hora de prueba: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    datos = crear_datos_prueba_produccion()
    
    print("📤 Datos a enviar:")
    print(json.dumps(datos, indent=2, ensure_ascii=False))
    print("-" * 50)
    
    try:
        print("🚀 Enviando datos al servidor...")
        
        response = requests.post(
            ENDPOINT,
            json=datos,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'BioData-Test-Client/1.0'
            },
            timeout=15
        )
        
        print(f"📡 RESPUESTA DEL SERVIDOR:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Tiempo de respuesta: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            try:
                respuesta_json = response.json()
                print(f"✅ ÉXITO - Respuesta JSON:")
                print(json.dumps(respuesta_json, indent=2, ensure_ascii=False))
                
                registros_importados = respuesta_json.get('registros_importados', 0)
                print(f"\n🎉 ¡Datos guardados exitosamente!")
                print(f"   📊 Registros importados: {registros_importados}")
                
            except json.JSONDecodeError:
                print(f"✅ ÉXITO - Respuesta texto:")
                print(response.text)
                
        elif response.status_code == 400:
            print(f"⚠️ ERROR DE VALIDACIÓN:")
            print(response.text)
            
        elif response.status_code == 500:
            print(f"❌ ERROR DEL SERVIDOR:")
            print(response.text)
            
        else:
            print(f"❓ RESPUESTA INESPERADA:")
            print(response.text)
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERROR DE CONEXIÓN:")
        print(f"   No se puede conectar al servidor {SERVIDOR_PRODUCCION}")
        print(f"   Detalles: {e}")
        print(f"   🔍 Verifica que:")
        print(f"   - El servidor esté ejecutándose")
        print(f"   - La IP {SERVIDOR_PRODUCCION} sea accesible")
        print(f"   - No haya firewalls bloqueando el puerto 8000")
        
    except requests.exceptions.Timeout:
        print(f"⏱️ TIMEOUT:")
        print(f"   El servidor tardó más de 15 segundos en responder")
        
    except Exception as e:
        print(f"❌ ERROR INESPERADO:")
        print(f"   {type(e).__name__}: {e}")

def verificar_conectividad():
    """Verifica si el servidor está disponible"""
    print("\n🔍 VERIFICANDO CONECTIVIDAD AL SERVIDOR")
    print("=" * 50)
    
    try:
        # Intentar una petición simple al servidor principal
        response = requests.get(
            SERVIDOR_PRODUCCION,
            timeout=10
        )
        print(f"✅ Servidor accesible - Status: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar al servidor {SERVIDOR_PRODUCCION}")
        
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout al conectar con {SERVIDOR_PRODUCCION}")
        
    except Exception as e:
        print(f"❓ Error: {e}")

def main():
    verificar_conectividad()
    probar_servidor_produccion()
    
    print("\n" + "=" * 60)
    print("💡 RECOMENDACIONES:")
    print("   1. Si el test fue exitoso, tu endpoint está funcionando")
    print("   2. Revisa los logs del servidor para ver los datos recibidos")
    print("   3. Verifica en tu base de datos que los datos se guardaron")
    print("   4. Configura tu dispositivo biométrico para usar esta URL")

if __name__ == "__main__":
    main()
