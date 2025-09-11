#!/usr/bin/env python
"""
Script para probar el endpoint recibir-datos-biometrico
y verificar que los datos se guarden correctamente.
"""

import requests
import json
from datetime import datetime, timedelta

# URL del endpoint (ajusta según tu configuración)
BASE_URL = "http://127.0.0.1:8000"  # Cambia si usas otro puerto
ENDPOINT = f"{BASE_URL}/api/recibir-datos-biometrico/"

def crear_datos_prueba():
    """Crea datos de prueba para enviar al endpoint"""
    ahora = datetime.now()
    
    datos_prueba = [
        {
            "user_id": 1,
            "nombre": "Juan Pérez",
            "timestamp": (ahora - timedelta(hours=2)).isoformat(),
            "estacion": "PRINCIPAL",
            "status": 0  # Entrada
        },
        {
            "user_id": 1,
            "nombre": "Juan Pérez", 
            "timestamp": ahora.isoformat(),
            "estacion": "PRINCIPAL",
            "status": 1  # Salida
        },
        {
            "user_id": 2,
            "nombre": "María González",
            "timestamp": (ahora - timedelta(hours=1)).isoformat(),
            "estacion": "La Soledad",
            "status": 0  # Entrada
        }
    ]
    
    return datos_prueba

def enviar_datos_prueba():
    """Envía datos de prueba al endpoint"""
    datos = crear_datos_prueba()
    
    print("📤 Enviando datos de prueba al endpoint...")
    print(f"URL: {ENDPOINT}")
    print(f"Datos: {json.dumps(datos, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(
            ENDPOINT,
            json=datos,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📡 Respuesta del servidor:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            respuesta_json = response.json()
            print(f"✅ Éxito: {json.dumps(respuesta_json, indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor.")
        print("   Asegúrate de que el servidor Django esté ejecutándose.")
        print(f"   Ejecuta: python manage.py runserver")
        
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout al conectar con el servidor.")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def main():
    print("🧪 PRUEBA DEL ENDPOINT RECIBIR-DATOS-BIOMETRICO")
    print("=" * 60)
    print(f"🕐 Hora de prueba: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    enviar_datos_prueba()
    
    print("\n" + "=" * 60)
    print("💡 Para ver los datos guardados, ejecuta:")
    print("   python ver_datos_guardados.py")

if __name__ == "__main__":
    main()
