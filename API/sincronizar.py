import requests
import json
from Biometricos_connections import importar_datos_dispositivo
from django.core.serializers.json import DjangoJSONEncoder

# Cambiar por tu URL de producción en Render
API_ENDPOINT = "https://biodata-t1zo.onrender.com/API/recibir-datos-biometrico/"
API_KEY = "0fe4aec256f2a2617572ea9d23975624385dc371"

def enviar_datos():
    registros = importar_datos_dispositivo(retornar_datos=True)

    headers = {
        "Authorization": f"Token {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_ENDPOINT, data=json.dumps(registros, cls=DjangoJSONEncoder), headers=headers)
        if response.status_code == 200:
            print("✅ Datos sincronizados correctamente.")
        else:
            print(f"⚠️ Error en el servidor remoto: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Fallo al conectar con el servidor remoto: {e}")
