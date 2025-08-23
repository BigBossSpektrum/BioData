import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import os
import sys
import django
from datetime import datetime
from django.utils.timezone import make_aware
from zk import ZK
from dotenv import load_dotenv
from django.conf import settings
import requests
from decouple import config

load_dotenv()


# ============================== #
# ⚙️ Configuración del entorno Django
# ============================== #
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

TURNOS = {
    'diurno': {'inicio': 6, 'fin': 22},       # 06:00 a 21:59
    'nocturno': {'inicio': 22, 'fin': 6},     # 22:00 a 05:59 del siguiente día
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

def detectar_turno(hora):
    if TURNOS['nocturno']['inicio'] <= hora or hora < TURNOS['nocturno']['fin']:
        return 'nocturno'
    return 'diurno'

# ============================== #
# 🔌 Funciones de conexión
# ============================== #
def conectar_dispositivo(ip=None, puerto=None, timeout=10):
    """
    Intenta conectar con el dispositivo ZKTeco usando IP y puerto de argumentos, settings.py o variables de entorno.
    Muestra sugerencias si la conexión falla.
    """
    # Prioridad: argumento > settings.py > variable de entorno > default
    if not ip:
        ip = getattr(settings, 'BIOMETRIC_DEVICE_IP', None) or os.getenv("BIOMETRICO_IP_ZKTECO")
    if not puerto:
        puerto_env = getattr(settings, 'BIOMETRIC_DEVICE_PORT', None) or os.getenv("BIOMETRICO_PUERTO_ZKTECO")
        try:
            puerto = int(puerto_env) if puerto_env else 4370
        except Exception:
            puerto = 4370
    try:
        print(f"🔌 [CONECTANDO] Verificando disponibilidad del dispositivo en {ip}:{puerto}...")
        zk = ZK(ip, port=puerto, timeout=timeout, password='0', force_udp=False, ommit_ping=False)
        conn = zk.connect()
        conn.disable_device()
        print("✅ [CONECTADO] Dispositivo ZKTeco en línea.")
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con el dispositivo: {e}")
        print("ℹ️ Sugerencias:")
        print("- Verifica que el biométrico esté encendido y conectado a la red.")
        print(f"- Haz ping a {ip} desde tu PC para comprobar conectividad.")
        print(f"- Asegúrate de que el puerto {puerto} esté abierto (puedes usar telnet o nmap).")
        print("- Revisa la configuración de red del dispositivo.")
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
            return user_id  # Retornar el ID usado en el biométrico
        except Exception as e:
            print(f"❌ Error al crear/actualizar usuario: {e}")
            return None
        finally:
            conn.enable_device()
            conn.disconnect()
    return None


def eliminar_usuario_biometrico(zk, user_id):
    zk.disable_device()
    zk.delete_user(uid=int(user_id))
    zk.enable_device()
    print(f"🗑️ Usuario con ID {user_id} eliminado del biométrico.")

# ============================== #
# 🧠 Logica de tipo de registro
# ============================== #

def obtener_tipo_registro(usuario, timestamp):
    """
    Determina si el registro es 'entrada' o 'salida' basado en el último registro anterior.
    """
    ultimo_registro = RegistroAsistencia.objects.using('default').filter(
        usuario=usuario,
        timestamp__lt=timestamp
    ).order_by('-timestamp').first()

    if not ultimo_registro:
        return 'entrada'  # No hay registros previos

    return 'salida' if ultimo_registro.tipo == 'entrada' else 'entrada'


# ============================== #
# 📥 Función principal de importación
# ============================== #
def importar_datos_dispositivo(enviar_a_clevercloud=False, clevercloud_url=None, token=None):
    # Usar la IP y puerto definidos en settings.py
    ip = getattr(settings, 'BIOMETRIC_DEVICE_IP', None) or os.getenv("BIOMETRICO_DEVICE_IP")
    puerto_env = getattr(settings, 'BIOMETRIC_DEVICE_PORT', None) or os.getenv("BIOMETRICO_PUERTO_ZKTECO")
    # Leer Clever Cloud info del .env si no se pasa por parámetro
    if enviar_a_clevercloud:
        if not clevercloud_url:
            clevercloud_url = config('CLEVERCLOUD_URL', default=None)
        if not token:
            token = config('CLEVERCLOUD_TOKEN', default=None)
    try:
        puerto = int(puerto_env) if puerto_env else 4370
    except Exception:
        puerto = 4370
    zk = ZK(ip, port=puerto, timeout=10, force_udp=False, ommit_ping=False)
    nuevos = 0
    registros_json = []
    try:
        print(f"🔌 [CONECTANDO] Verificando disponibilidad del dispositivo en {ip}:{puerto}...")
        conn = zk.connect()
        print("✅ [CONECTADO] Dispositivo ZKTeco en línea.")

        # Usuarios
        print("📋 [USUARIOS] Leyendo usuarios desde el dispositivo...")
        for user in conn.get_users():
            activo = not getattr(user, 'disabled', False)
            # Ya no se asocia con CustomUser
            defaults_default = {
                'nombre': user.name.strip() if user.name else 'N/A',
                'privilegio': user.privilege,
                'activo': activo
            }
            obj, creado = UsuarioBiometrico.objects.using('default').update_or_create(
                biometrico_id=user.uid,  # Cambiado de user_id a biometrico_id
                defaults=defaults_default
            )

            print(f"🔍 ID: {user.uid}, Nombre: {user.name}, Privilegio: {user.privilege}, Activo: {activo}")
            print(f"✅ Usuario {'creado' if creado else 'actualizado'} en BD: {obj.nombre} ({obj.biometrico_id})")

        # Asistencia
        print("⏱️ [ASISTENCIA] Descargando registros de asistencia...")
        asistencia = conn.get_attendance()

        # Agrupar todos los registros por usuario y día
        from collections import defaultdict
        registros_por_usuario_fecha = defaultdict(list)
        for record in asistencia:
            user_default = UsuarioBiometrico.objects.using('default').filter(biometrico_id=record.user_id).first()
            if not user_default:
                continue
            timestamp = record.timestamp
            if not timestamp.tzinfo:
                timestamp = make_aware(timestamp)
            fecha = timestamp.date()
            registros_por_usuario_fecha[(record.user_id, fecha)].append((timestamp, user_default))

        for (user_id, fecha), registros in registros_por_usuario_fecha.items():
            registros.sort(key=lambda x: x[0])  # Orden por timestamp
            for timestamp, user_default in [(x[0], x[1]) for x in registros]:
                tipo = obtener_tipo_registro(user_default, timestamp)

                # Guardar en default
                _, created_default = RegistroAsistencia.objects.using('default').get_or_create(
                    usuario=user_default,
                    timestamp=timestamp,
                    tipo=tipo,
                )

                if created_default:
                    nuevos += 1
                    print(f"🧾 Registro - Usuario: {user_default.nombre}, Hora: {timestamp}, Estado: {tipo.capitalize()}")

                registros_json.append({
                    'user_id': user_default.biometrico_id,
                    'nombre': user_default.nombre,
                    'timestamp': timestamp.isoformat(),
                    'tipo': tipo
                })

        print(f"📊 Total nuevos registros importados: {nuevos}")
        conn.clear_attendance()
        print("🧹 Registros de asistencia eliminados del dispositivo.")
        conn.disconnect()
        print("🔌 Conexión cerrada.")
        # Enviar a Clever Cloud si se solicita
        if enviar_a_clevercloud and clevercloud_url and token:
            print(f"🌐 Enviando registros a Clever Cloud: {clevercloud_url}")
            headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}
            response = requests.post(clevercloud_url, json=registros_json, headers=headers)
            print(f"[CLEVER CLOUD] Status: {response.status_code}, Response: {response.text}")
            return response.status_code, response.text
        return registros_json
    except Exception as e:
        print(f"❌ Error de conexión o procesamiento: {e}")
        return None

def calcular_horas_trabajadas_por_usuario(usuario):
    registros = RegistroAsistencia.objects.filter(usuario=usuario).order_by('timestamp')
    entrada = None
    resultados = []

    for registro in registros:
        if registro.tipo == 'entrada':
            entrada = registro.timestamp
        elif registro.tipo == 'salida' and entrada:
            salida = registro.timestamp
            duracion = salida - entrada
            horas_trabajadas = duracion.total_seconds() / 3600

            turno = detectar_turno(entrada.hour)
            horas_extras = max(0, horas_trabajadas - 8)  # Asumiendo 8 horas laborales

            resultados.append({
                'usuario': usuario.nombre,
                'entrada': entrada,
                'salida': salida,
                'turno': turno,
                'horas_trabajadas': round(horas_trabajadas, 2),
                'horas_extras': round(horas_extras, 2),
            })

            entrada = None  # Reset entrada

    return resultados

def resumen_jornadas():
    usuarios = UsuarioBiometrico.objects.all()
    for usuario in usuarios:
        jornadas = calcular_horas_trabajadas_por_usuario(usuario)
        print(f"\n📊 Resumen de {usuario.nombre}:")
        for j in jornadas:
            print(f"Turno: {j['turno'].capitalize()} | Entrada: {j['entrada']} | Salida: {j['salida']} | "
                  f"Horas Trabajadas: {j['horas_trabajadas']}h | Horas Extras: {j['horas_extras']}h")

# ============================== #
# ▶️ Ejecución directa
# ============================== #
if __name__ == "__main__":
    # Ejecuta la importación y muestra los datos en consola como JSON
    datos = importar_datos_dispositivo()
    import json
    print("\n=== DATOS ENVIADOS AL FRONT ===")
    print(json.dumps(datos, indent=2, ensure_ascii=False))
