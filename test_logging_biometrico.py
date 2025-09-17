#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del logging 
de datos biométricos.
"""

import requests
import json
from datetime import datetime

# URL del endpoint (ajustar según sea necesario)
URL = "http://localhost:8000/API/recibir_datos_biometrico/"

# Datos de prueba simulando el envío de un dispositivo biométrico
datos_prueba = [
    {
        "user_id": "123",
        "nombre": "Usuario Prueba",
        "timestamp": "2025-09-17T10:30:00",
        "estacion": "Estacion_Test", 
        "status": "entrada"
    },
    {
        "user_id": "456",
        "nombre": "Otro Usuario",
        "timestamp": "2025-09-17T10:35:00",
        "estacion": "Estacion_Test",
        "status": "salida"
    }
]

def probar_logging():
    """
    Envía datos de prueba al endpoint para verificar el logging
    """
    print("🧪 Enviando datos de prueba al endpoint...")
    print(f"📍 URL: {URL}")
    print(f"📦 Datos: {json.dumps(datos_prueba, indent=2)}")
    
    try:
        response = requests.post(
            URL,
            json=datos_prueba,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'TestScript/1.0'
            },
            timeout=30
        )
        
        print(f"\n✅ Respuesta recibida:")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Respuesta: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ ¡Test exitoso! Revisa la carpeta 'registros_biometrico' para ver el log generado.")
        else:
            print(f"\n❌ Error en la respuesta: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar al servidor.")
        print("   Asegúrate de que Django esté ejecutándose en localhost:8000")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")

if __name__ == "__main__":
    probar_logging()
