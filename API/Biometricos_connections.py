import os
import sys
import django
import datetime
from zk import ZK, const
from django.utils.timezone import make_aware

# ✅ Agregar el path del proyecto raíz
sys.path.append("C:/Users/Entrecables y Redes/Documents/GitHub/BioData")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inverligol.settings")

# ✅ Inicializar Django
django.setup()

# ✅ Ahora los modelos funcionan
from API.models import UsuarioBiometrico, RegistroAsistencia


def importar_datos_dispositivo():
    zk = ZK(
        '192.168.0.9',
        port=4370,
        timeout=5,
        password=123456,
        force_udp=False,
        ommit_ping=True
    )

    try:
        print("🔌 Conectando al dispositivo ZKTeco...")
        conn = zk.connect()
        print("✅ Conectado.")

        # Leer usuarios
        print("📋 Leyendo usuarios...")
        for user in conn.get_users():
            print(vars(user))  # debug: ver atributos reales del objeto
            obj, creado = UsuarioBiometrico.objects.update_or_create(
                user_id=user.user_id,
                defaults={
                    'nombre': user.name,
                    'privilegio': user.privilege,
                    'activo': not getattr(user, 'disabled', False)  # fallback
                }
            )
            print(f"🧑 Usuario {'creado' if creado else 'actualizado'}: {obj}")

        # Leer registros de asistencia
        print("⏱️ Descargando registros de asistencia...")
        asistencia = conn.get_attendance()
        nuevos = 0

        for record in asistencia:
            if user := UsuarioBiometrico.objects.filter(
                user_id=record.user_id
            ).first():
                timestamp = record.timestamp
                if not timestamp.tzinfo:
                    timestamp = make_aware(timestamp)

                _, created = RegistroAsistencia.objects.get_or_create(
                    usuario=user,
                    timestamp=timestamp,
                    estado=record.status,
                )
                if created:
                    nuevos += 1

        print(f"✅ {nuevos} registros de asistencia importados.")

        conn.clear_attendance()
        print("🧹 Registros en el dispositivo eliminados.")

        conn.disconnect()
        print("🔌 Conexión cerrada.")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    importar_datos_dispositivo()
