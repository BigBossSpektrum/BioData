import os
import sys
import django
from zk import ZK
from django.utils.timezone import make_aware
from datetime import datetime

sys.path.append("C:/Users/Entrecables y Redes/Documents/GitHub/BioData")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inverligol.settings")
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia

STATUS_MAP = {
    0: "Entrada",
    1: "Salida",
    2: "Break Out",
    3: "Break In",
    4: "Overtime",
    15: "Desconocido",
}


def interpretar_estado(codigo):
    return STATUS_MAP.get(codigo, f"❓ DESCONOCIDO ({codigo})")

def obtener_estado_alternado(usuario, timestamp):
    """
    Determina si el registro es Entrada o Salida en función del número
    de registros ya guardados para el mismo día.
    """
    fecha = timestamp.date()
    registros_del_dia = RegistroAsistencia.objects.filter(
        usuario=usuario,
        timestamp__date=fecha
    ).order_by("timestamp")

    return 0 if registros_del_dia.count() % 2 == 0 else 1  # 0=Entrada, 1=Salida


def importar_datos_dispositivo():
    zk = ZK(
        '192.168.0.16',
        port=4370,
        timeout=10,
        password=123456,
        force_udp=False,
        ommit_ping=False,
    )

    try:
        print("🔌 [CONECTANDO] Verificando disponibilidad del dispositivo...")
        conn = zk.connect()
        print("✅ [CONECTADO] Dispositivo ZKTeco en línea.")

        print("📋 [USUARIOS] Leyendo usuarios desde el dispositivo...")
        for user in conn.get_users():
            activo = not getattr(user, 'disabled', False)
            obj, creado = UsuarioBiometrico.objects.update_or_create(
                user_id=user.user_id,
                defaults={
                    'nombre': user.name.strip() if user.name else 'N/A',
                    'privilegio': user.privilege,
                    'activo': activo
                }
            )
            print(f"🔍 ID: {user.user_id}, Nombre: {user.name}, Privilegio: {user.privilege}, Activo: {activo}")
            print(f"✅ Usuario {'creado' if creado else 'actualizado'} en BD: {obj.nombre} ({obj.user_id})")

        print("⏱️ [ASISTENCIA] Descargando registros de asistencia...")
        asistencia = conn.get_attendance()
        nuevos = 0

        for record in asistencia:
            user = UsuarioBiometrico.objects.filter(user_id=record.user_id).first()
            if not user:
                continue

            timestamp = record.timestamp
            if not timestamp.tzinfo:
                timestamp = make_aware(timestamp)

            estado_num = obtener_estado_alternado(user, timestamp)
            tipo = 'entrada' if estado_num == 0 else 'salida'

            _, created = RegistroAsistencia.objects.get_or_create(
                usuario=user,
                timestamp=timestamp,
                tipo=tipo,
            )
            if created:
                print(f"🧾 Registro - Usuario: {user.nombre}, Hora: {timestamp}, Estado: {tipo.capitalize()}")


        print(f"📊 Total nuevos registros importados: {nuevos}")

        conn.clear_attendance()
        print("🧹 Registros de asistencia eliminados del dispositivo.")

        conn.disconnect()
        print("🔌 Conexión cerrada.")

    except Exception as e:
        print(f"❌ Error de conexión o procesamiento: {e}")

if __name__ == "__main__":
    importar_datos_dispositivo()
