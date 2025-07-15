import sys
import django
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from zk import ZK

import os
from dotenv import load_dotenv
load_dotenv()

# Configurar entorno Django
sys.path.append("C:/Users/Entrecables y Redes/Documents/GitHub/BioData")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inverligol.settings")
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia

DEFAULT_PORT = 4370
JORNADA_LABORAL_HORAS = 8


def conectar_dispositivo(ip, puerto=DEFAULT_PORT, timeout=10):
    zk = ZK(ip, port=puerto, timeout=timeout, force_udp=False, ommit_ping=False)
    try:
        conn = zk.connect()
        conn.disable_device()
        print(f"✅ Conectado al dispositivo en {ip}:{puerto}")
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con el biométrico: {e}")
        return None


def obtener_tipo_registro(usuario, timestamp):
    ultimo_registro = RegistroAsistencia.objects.filter(
        usuario=usuario,
        timestamp__lt=timestamp
    ).order_by('-timestamp').first()

    return 'entrada' if not ultimo_registro or ultimo_registro.tipo == 'salida' else 'salida'


def procesar_registros(ip, puerto=DEFAULT_PORT, estacion="Estación Desconocida"):
    conn = conectar_dispositivo(ip, puerto)
    if not conn:
        return

    registros_biometrico = conn.get_attendance()
    print(f"\n📥 Total registros leídos en {estacion}: {len(registros_biometrico)}")

    for record in registros_biometrico:
        usuario = UsuarioBiometrico.objects.filter(biometrico_id=record.user_id).first()
        if not usuario:
            continue

        timestamp = record.timestamp
        if not timestamp.tzinfo:
            timestamp = make_aware(timestamp)

        tipo = obtener_tipo_registro(usuario, timestamp)

        registro, creado = RegistroAsistencia.objects.get_or_create(
            usuario=usuario,
            timestamp=timestamp,
            tipo=tipo
        )
        if creado:
            print(f"📝 [{estacion}] {usuario.nombre} - {tipo} registrada a las {timestamp}")

    calcular_horas_trabajadas(estacion)

    conn.enable_device()
    conn.disconnect()
    print("🔌 Conexión cerrada.")


def calcular_horas_trabajadas(estacion):
    print(f"\n📊 Cálculo de horas trabajadas en: {estacion}")
    usuarios = UsuarioBiometrico.objects.all()
    for usuario in usuarios:
        registros = RegistroAsistencia.objects.filter(usuario=usuario).order_by('timestamp')
        entrada = None
        resumen = []

        for registro in registros:
            if registro.tipo == 'entrada':
                entrada = registro.timestamp
            elif registro.tipo == 'salida' and entrada:
                salida = registro.timestamp

                # Si la salida es menor que la entrada, asumimos que cruzó medianoche
                if salida < entrada:
                    salida += timedelta(days=1)

                duracion = salida - entrada
                horas_trabajadas = duracion.total_seconds() / 3600
                horas_extras = max(0, horas_trabajadas - JORNADA_LABORAL_HORAS)

                resumen.append({
                    'usuario': usuario.nombre,
                    'fecha_entrada': entrada.date(),
                    'entrada': entrada,
                    'salida': salida,
                    'horas_trabajadas': round(horas_trabajadas, 2),
                    'horas_extras': round(horas_extras, 2)
                })
                entrada = None  # reset

        if resumen:
            print(f"\n📌 Resumen de {usuario.nombre} en {estacion}:")
            for r in resumen:
                print(f"Fecha Entrada: {r['fecha_entrada']} | Entrada: {r['entrada'].time()} | Salida: {r['salida'].time()} | "
                      f"Horas Trabajadas: {r['horas_trabajadas']}h | Horas Extras: {r['horas_extras']}h")
        else:
            print(f"⚠️ No se encontraron pares completos para {usuario.nombre} en {estacion}")


if __name__ == '__main__':
    IP_BIOMETRICO = "192.168.0.18"
    PUERTO_BIOMETRICO = 4370
    NOMBRE_ESTACION = "La Soledad"

    procesar_registros(IP_BIOMETRICO, PUERTO_BIOMETRICO, NOMBRE_ESTACION)
