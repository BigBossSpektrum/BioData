import os
import sys
import django
from datetime import datetime
from django.utils.timezone import make_aware
from zk import ZK
from dotenv import load_dotenv

load_dotenv()


# ============================== #
# ⚙️ Configuración del entorno Django
# ============================== #
sys.path.append("C:/Users/Entrecables y Redes/Documents/GitHub/BioData")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inverligol.settings")
django.setup()

# ============================== #
# 📦 Importación de modelos
# ============================== #
from API.models import UsuarioBiometrico, RegistroAsistencia

# ============================== #
# 🔁 Diccionario de estados
# ============================== #
STATUS_MAP = {
    0: "Entrada",
    1: "Salida",
    2: "Break Out",
    3: "Break In",
    4: "Overtime",
    15: "Desconocido",
}

# ============================== #
# 📘 Funciones auxiliares
# ============================== #
def interpretar_estado(codigo):
    return STATUS_MAP.get(codigo, f"❓ DESCONOCIDO ({codigo})")


def obtener_estado_alternado(usuario, timestamp):
    """
    Alterna entre 'Entrada' y 'Salida' dependiendo de la cantidad de registros
    para el usuario en ese día.
    """
    fecha = timestamp.date()
    registros = RegistroAsistencia.objects.filter(usuario=usuario, timestamp__date=fecha)
    return 0 if registros.count() % 2 == 0 else 1  # 0=Entrada, 1=Salida


# ============================== #
# 🔌 Funciones de conexión
# ============================== #def conectar_dispositivo(ip='192.168.0.11', puerto=None):
def conectar_dispositivo(ip=os.getenv("BIOMETRICO_IP_ZKTECO"), puerto=None):
    try:
        if puerto is None:
            print("⚠️ Puerto no especificado. Usando 4370 por defecto.")
            puerto = os.getenv
        else:
            puerto = int(puerto)  # Esto lanza error si no es convertible

        print(f"🔌 [CONECTANDO] Verificando disponibilidad del dispositivo en {ip}:{puerto}...")
        zk = ZK(ip, port=puerto, timeout=10, password='0', force_udp=False, ommit_ping=False)
        conn = zk.connect()
        conn.disable_device()
        print("✅ [CONECTADO] Dispositivo ZKTeco en línea.")
        return conn

    except Exception as e:
        print(f"❌ Error al conectar con el dispositivo: {e}")
        return None

# ============================== #
# 🧠 Funciones CRUD
# ============================== #
def crear_o_actualizar_usuario_biometrico(user_id, nombre):
    conn = conectar_dispositivo()
    if conn:
        try:
            conn.set_user(uid=int(user_id), name=nombre, privilege=0, password='', group_id='', user_id=str(user_id))
            print(f"✅ Usuario {nombre} (ID {user_id}) creado/actualizado en el biométrico.")
        except Exception as e:
            print(f"❌ Error al crear/actualizar usuario: {e}")
        finally:
            conn.enable_device()
            conn.disconnect()


def eliminar_usuario_biometrico(zk, user_id):
    zk.disable_device()
    zk.delete_user(uid=int(user_id))
    zk.enable_device()
    print(f"🗑️ Usuario con ID {user_id} eliminado del biométrico.")


# ============================== #
# 📥 Función principal de importación
# ============================== #
def importar_datos_dispositivo():
    zk = ZK(os.getenv("BIOMETRICO_IP_ZKTECO"), port=os.getenv("BIOMETRICO_PUERTO_ZKTECO"), timeout=10, force_udp=False, ommit_ping=False)
    nuevos = 0

    try:
        print("🔌 [CONECTANDO] Verificando disponibilidad del dispositivo...")
        conn = zk.connect()
        print("✅ [CONECTADO] Dispositivo ZKTeco en línea.")

        # Usuarios
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

        # Asistencia
        print("⏱️ [ASISTENCIA] Descargando registros de asistencia...")
        asistencia = conn.get_attendance()

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
                nuevos += 1
                print(f"🧾 Registro - Usuario: {user.nombre}, Hora: {timestamp}, Estado: {tipo.capitalize()}")

        print(f"📊 Total nuevos registros importados: {nuevos}")
        conn.clear_attendance()
        print("🧹 Registros de asistencia eliminados del dispositivo.")
        conn.disconnect()
        print("🔌 Conexión cerrada.")

    except Exception as e:
        print(f"❌ Error de conexión o procesamiento: {e}")


# ============================== #
# ▶️ Ejecución directa
# ============================== #
if __name__ == "__main__":
    importar_datos_dispositivo()
