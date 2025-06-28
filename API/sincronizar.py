import os
import requests
from Biometricos_connections import importar_datos_dispositivo

API_ENDPOINT = "https://biodata-t1zo.onrender.com/API/recibir-datos-biometrico/"
API_KEY = os.getenv("API_KEY_BIOMETRICO")  # corregido typo

def enviar_datos():
    registros = importar_datos_dispositivo(retornar_datos=True)

    headers = {
        "Authorization": f"Token {API_KEY}",
        "Content-Type": "application/json",
    }
    print("Encabezados HTTP:", headers)

    try:
        # Usar json= para enviar automáticamente JSON y headers correctos
        response = requests.post(API_ENDPOINT, json=registros, headers=headers)

        if response.status_code == 200:
            print("✅ Datos sincronizados correctamente.")
        else:
            print(f"⚠️ Error en el servidor remoto: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Fallo al conectar con el servidor remoto: {e}")
