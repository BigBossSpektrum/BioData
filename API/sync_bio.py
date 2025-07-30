import os
import json
import requests
import urllib3
import logging
from datetime import datetime
from zk import ZK
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('biometrico_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("🚀 Iniciando script de sincronización biométrica")

DEFAULT_PORT = 4370
SERVER_URL = "https://rhligol.gventas.net/recibir-datos-biometrico/"


def conectar_dispositivo(ip, puerto=DEFAULT_PORT, timeout=10):
    logger.info(f"🔌 Intentando conectar al dispositivo biométrico en {ip}:{puerto}")
    logger.debug(f"Parámetros de conexión: timeout={timeout}, force_udp=False, ommit_ping=False")
    
    zk = ZK(ip, port=puerto, timeout=timeout, force_udp=False, ommit_ping=False)
    try:
        logger.info("🔄 Estableciendo conexión...")
        conn = zk.connect()
        
        logger.info("🚫 Deshabilitando dispositivo para lectura segura...")
        conn.disable_device()
        
        logger.info(f"✅ Conectado exitosamente al biométrico en {ip}:{puerto}")
        print(f"Conectado al biométrico en {ip}:{puerto}")
        return conn
    except Exception as e:
        logger.error(f"❌ Error al conectar al dispositivo {ip}:{puerto} - {str(e)}")
        print(f"❌ Error al conectar: {e}")
        return None


def obtener_registros(conn, estacion):
    logger.info(f"📄 Obteniendo registros de asistencia de la estación: {estacion}")
    
    try:
        registros_biometrico = conn.get_attendance()
        logger.info(f"📥 Total registros leídos en {estacion}: {len(registros_biometrico)}")
        print(f"Total registros leídos en {estacion}: {len(registros_biometrico)}")
        
        if len(registros_biometrico) == 0:
            logger.warning("⚠️ No se encontraron registros en el dispositivo")
            return []
        
        registros = []
        for i, record in enumerate(registros_biometrico):
            registro = {
                'biometrico_id': record.user_id,
                'timestamp': record.timestamp.isoformat(),
                'estacion': estacion
            }
            registros.append(registro)
            
            if i < 3:  # Log solo los primeros 3 registros para no saturar
                logger.debug(f"Registro {i+1}: ID={record.user_id}, Timestamp={record.timestamp}")
        
        if len(registros_biometrico) > 3:
            logger.debug(f"... y {len(registros_biometrico) - 3} registros más")
            
        logger.info(f"✅ Procesados {len(registros)} registros correctamente")
        return registros
        
    except Exception as e:
        logger.error(f"❌ Error al obtener registros: {str(e)}")
        return []


def enviar_al_servidor(registros, token=None):
    logger.info(f"🚀 Preparando envío de {len(registros)} registros al servidor")
    logger.info(f"🌐 URL destino: {SERVER_URL}")
    
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    logger.debug(f"Headers: {headers}")
    logger.debug(f"Datos a enviar: {json.dumps(registros, indent=2, ensure_ascii=False)[:500]}...")

    # Desactivar warnings de verificación SSL solo para pruebas
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        logger.info("📤 Enviando datos al servidor... (ignorando verificación SSL)")
        response = requests.post(SERVER_URL, json=registros, headers=headers, timeout=10, verify=False)
        
        logger.info(f"📊 Respuesta del servidor: Status {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Datos enviados correctamente al servidor")
            print("Datos enviados correctamente al servidor.")
            logger.debug(f"Respuesta del servidor: {response.text[:200]}...")
        else:
            logger.error(f"❌ Error HTTP {response.status_code} al enviar datos")
            logger.error(f"Respuesta del servidor: {response.text}")
            print(f"Error al enviar datos: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout al enviar datos al servidor (>10s)")
        print("Timeout al enviar al servidor")
    except requests.exceptions.ConnectionError:
        logger.error("❌ Error de conexión al servidor")
        print("Error de conexión al servidor")
    except Exception as e:
        logger.error(f"❌ Excepción inesperada al enviar al servidor: {str(e)}")
        print(f"Excepción al enviar al servidor: {e}")


def main():
    logger.info("🔧 Iniciando función principal")
    
    # Obtener configuración del archivo .env
    logger.info("📁 Cargando configuración del archivo .env")
    ip_biometrico = os.getenv('IP_BIOMETRICO')
    puerto_biometrico = os.getenv('PUERTO_BIOMETRICO')
    nombre_estacion = os.getenv('NOMBRE_ESTACION')
    token_api = os.getenv('TOKEN_API')
    
    logger.debug(f"Variables cargadas: IP={ip_biometrico}, Puerto={puerto_biometrico}, Estación={nombre_estacion}, Token={'Sí' if token_api else 'No'}")
    
    # Validar que las variables estén definidas
    if not ip_biometrico:
        logger.error("❌ IP_BIOMETRICO no está definida en el archivo .env")
        print("❌ Error: IP_BIOMETRICO no está definida en el archivo .env")
        return
    if not nombre_estacion:
        logger.error("❌ NOMBRE_ESTACION no está definida en el archivo .env")
        print("❌ Error: NOMBRE_ESTACION no está definida en el archivo .env")
        return
    
    puerto = int(puerto_biometrico) if puerto_biometrico else DEFAULT_PORT
    
    logger.info(f"🎯 Configuración validada - IP: {ip_biometrico}, Puerto: {puerto}, Estación: {nombre_estacion}")
    print(f"Conectando a biométrico en {ip_biometrico}:{puerto}")
    print(f"Estación: {nombre_estacion}")

    # Intentar conexión al dispositivo
    conn = conectar_dispositivo(ip_biometrico, puerto)
    if not conn:
        logger.error("❌ No se pudo establecer conexión con el dispositivo biométrico")
        return

    # Obtener registros del dispositivo
    registros = obtener_registros(conn, nombre_estacion)

    # Procesar y enviar registros
    if registros:
        logger.info(f"📦 Preparando envío de {len(registros)} registros")
        enviar_al_servidor(registros, token=token_api)
    else:
        logger.warning("⚠️ No se encontraron registros para enviar")
        print("No se encontraron registros para enviar.")

    # Finalizar conexión
    try:
        logger.info("🔄 Habilitando dispositivo nuevamente...")
        conn.enable_device()
        
        logger.info("🔌 Cerrando conexión...")
        conn.disconnect()
        
        logger.info("✅ Proceso completado exitosamente")
        print("Conexión cerrada.")
        
    except Exception as e:
        logger.error(f"❌ Error al cerrar conexión: {str(e)}")
        print(f"Advertencia al cerrar conexión: {e}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⚡ Proceso interrumpido por el usuario")
        print("\nProceso interrumpido por el usuario")
    except Exception as e:
        logger.critical(f"❌ Error crítico en el programa principal: {str(e)}")
        print(f"Error crítico: {e}")
    finally:
        logger.info("🏁 Finalizando script de sincronización biométrica")
