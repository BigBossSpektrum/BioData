#!/usr/bin/env python
import requests
import json

def test_api_endpoint():
    url = "http://127.0.0.1:8000/api/recibir-datos-biometrico/"
    
    # Datos de prueba pequeños
    test_data = [
        {
            "user_id": "12345",
            "nombre": "USUARIO TEST",
            "timestamp": "2025-09-23T09:30:00",
            "status": 15,
            "estacion": "San Mateo",
            "punch": 0
        }
    ]
    
    print("=== PROBANDO API ENDPOINT ===")
    print(f"URL: {url}")
    print(f"Datos: {test_data}")
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'python-test-client'
        }
        
        response = requests.post(url, json=test_data, headers=headers, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"\n✅ ÉXITO!")
            print(f"Registros nuevos: {response_data.get('resumen', {}).get('nuevos', 0)}")
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR de conexión: {e}")

if __name__ == "__main__":
    test_api_endpoint()
