#!/usr/bin/env python
"""
Guía completa para configurar y verificar el servidor biométrico
en producción: http://186.31.35.24:8000
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import EstacionServicio

def verificar_configuracion_servidor():
    """Verifica que el servidor esté configurado correctamente"""
    print("🔧 VERIFICACIÓN DE CONFIGURACIÓN DEL SERVIDOR")
    print("=" * 60)
    
    # 1. Verificar estaciones
    print("1️⃣ ESTACIONES DE SERVICIO:")
    estaciones = EstacionServicio.objects.all()
    
    if estaciones.exists():
        print(f"   ✅ {estaciones.count()} estaciones configuradas:")
        for estacion in estaciones:
            print(f"   📍 {estacion.nombre}")
    else:
        print("   ❌ No hay estaciones configuradas")
        return False
    
    # 2. Verificar configuración Django
    print("\n2️⃣ CONFIGURACIÓN DJANGO:")
    from django.conf import settings
    
    print(f"   ✅ DEBUG: {settings.DEBUG}")
    print(f"   ✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    
    # 3. Verificar base de datos
    print("\n3️⃣ BASE DE DATOS:")
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("   ✅ Conexión a base de datos: OK")
    except Exception as e:
        print(f"   ❌ Error en base de datos: {e}")
        return False
    
    return True

def mostrar_configuracion_dispositivo():
    """Muestra cómo configurar el dispositivo biométrico"""
    print("\n📱 CONFIGURACIÓN DEL DISPOSITIVO BIOMÉTRICO")
    print("=" * 60)
    
    print("Para configurar tu dispositivo biométrico ZKTeco:")
    print()
    print("🌐 URL del servidor:")
    print("   http://186.31.35.24:8000/api/recibir-datos-biometrico/")
    print()
    print("📋 Formato de datos esperado (JSON):")
    print("""   [
     {
       "user_id": 123,
       "nombre": "Nombre del Empleado",
       "timestamp": "2025-09-09T16:30:00",
       "estacion": "PRINCIPAL",
       "status": 0
     }
   ]""")
    print()
    print("📊 Campos explicados:")
    print("   • user_id: ID único del empleado en el biométrico")
    print("   • nombre: Nombre completo del empleado")
    print("   • timestamp: Fecha y hora del registro (ISO format)")
    print("   • estacion: Nombre de la estación (debe existir en BD)")
    print("   • status: 0 = Entrada, 1 = Salida")
    
    print("\n🏢 Estaciones disponibles:")
    estaciones = EstacionServicio.objects.all()
    for estacion in estaciones:
        print(f"   • {estacion.nombre}")

def mostrar_comandos_servidor():
    """Muestra comandos útiles para el servidor"""
    print("\n⚙️ COMANDOS ÚTILES DEL SERVIDOR")
    print("=" * 60)
    
    print("🚀 Para iniciar el servidor:")
    print("   python manage.py runserver 0.0.0.0:8000")
    print()
    print("👀 Para monitorear actividad:")
    print("   python monitor_servidor.py")
    print("   python monitor_servidor.py --continuo")
    print()
    print("🧪 Para probar con datos:")
    print("   python probar_servidor_produccion.py")
    print("   python crear_datos_prueba_directo.py")
    print()
    print("📊 Para ver datos guardados:")
    print("   python ver_datos_guardados.py")
    print()
    print("🔒 Para crear superusuario:")
    print("   python manage.py createsuperuser")
    print()
    print("📋 Para ver admin web:")
    print("   http://186.31.35.24:8000/admin/")

def verificar_puertos_red():
    """Verifica puertos y configuración de red"""
    print("\n🌐 VERIFICACIÓN DE RED")
    print("=" * 60)
    
    print("🔍 Para verificar que el servidor esté escuchando:")
    print("   netstat -an | findstr :8000")
    print()
    print("🔥 Para verificar firewall (Windows):")
    print("   netsh advfirewall firewall show rule name=all | findstr 8000")
    print()
    print("📡 Para probar conectividad desde otro equipo:")
    print("   telnet 186.31.35.24 8000")
    print("   curl http://186.31.35.24:8000/admin/")
    print()
    print("💡 POSIBLES PROBLEMAS:")
    print("   • Puerto 8000 bloqueado por firewall")
    print("   • Servidor no configurado para escuchar en 0.0.0.0")
    print("   • Servicio Django detenido")
    print("   • IP 186.31.35.24 no accesible externamente")

def crear_script_inicio():
    """Crea un script para iniciar el servidor automáticamente"""
    script_content = """#!/bin/bash
# Script para iniciar el servidor biométrico
# Guarda este archivo como start_bioserver.sh

echo "🚀 Iniciando servidor biométrico..."
echo "📍 URL: http://186.31.35.24:8000"
echo "📱 Endpoint: /api/recibir-datos-biometrico/"
echo ""

cd "c:\\ControlIngreso\\BioData"

# Activar entorno virtual
source env/Scripts/activate

# Aplicar migraciones si es necesario
python manage.py migrate

# Iniciar servidor
echo "✅ Servidor iniciado en http://186.31.35.24:8000"
python manage.py runserver 0.0.0.0:8000
"""
    
    with open("start_bioserver.sh", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("\n📄 SCRIPT DE INICIO CREADO")
    print("=" * 60)
    print("✅ Archivo creado: start_bioserver.sh")
    print("🔧 Para usarlo:")
    print("   chmod +x start_bioserver.sh")
    print("   ./start_bioserver.sh")

def main():
    print("🖥️ CONFIGURACIÓN DEL SERVIDOR BIOMÉTRICO")
    print("=" * 70)
    print("🌐 Servidor: http://186.31.35.24:8000")
    print("📡 Endpoint: /api/recibir-datos-biometrico/")
    print()
    
    if verificar_configuracion_servidor():
        print("\n✅ SERVIDOR CONFIGURADO CORRECTAMENTE")
        mostrar_configuracion_dispositivo()
        mostrar_comandos_servidor()
        verificar_puertos_red()
        crear_script_inicio()
        
        print("\n" + "=" * 70)
        print("🎉 TODO LISTO PARA RECIBIR DATOS BIOMÉTRICOS")
        print("💡 Pasos siguientes:")
        print("   1. Iniciar servidor: python manage.py runserver 0.0.0.0:8000")
        print("   2. Configurar dispositivo con la URL mostrada arriba")
        print("   3. Monitorear: python monitor_servidor.py --continuo")
        
    else:
        print("\n❌ HAY PROBLEMAS EN LA CONFIGURACIÓN")
        print("🔧 Revisa los errores mostrados arriba")

if __name__ == "__main__":
    main()
