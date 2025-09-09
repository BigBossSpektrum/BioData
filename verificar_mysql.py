#!/usr/bin/env python3
"""
Verificar conexión a MySQL y datos reales
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

def verificar_mysql():
    print("🔍 VERIFICANDO CONEXIÓN A MYSQL")
    print("=" * 50)
    
    try:
        from API.models import UsuarioBiometrico, RegistroAsistencia, ResumenSemanal
        from django.db import connection
        
        # Verificar conexión
        print("🔗 INFORMACIÓN DE CONEXIÓN:")
        print(f"  Base de datos: {connection.settings_dict['NAME']}")
        print(f"  Host: {connection.settings_dict['HOST']}")
        print(f"  Puerto: {connection.settings_dict['PORT']}")
        print(f"  Usuario: {connection.settings_dict['USER']}")
        
        # Probar conexión
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"  Versión MySQL: {version}")
        
        # Contar registros
        print(f"\n📊 CONTEO DE REGISTROS:")
        usuarios = UsuarioBiometrico.objects.all()
        registros = RegistroAsistencia.objects.all()
        resumenes = ResumenSemanal.objects.all()
        
        print(f"  UsuarioBiometrico: {usuarios.count()}")
        print(f"  RegistroAsistencia: {registros.count()}")
        print(f"  ResumenSemanal: {resumenes.count()}")
        
        # Mostrar algunos ejemplos
        if usuarios.exists():
            print(f"\n👥 EMPLEADOS (primeros 5):")
            for usuario in usuarios[:5]:
                print(f"  ✅ {usuario.nombre} (ID: {usuario.id}, Activo: {usuario.activo})")
        
        if registros.exists():
            print(f"\n📊 REGISTROS RECIENTES (primeros 5):")
            for registro in registros.order_by('-timestamp')[:5]:
                print(f"  📅 {registro.user.nombre} - {registro.timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print(f"💡 Posibles causas:")
        print(f"   - MySQL no está ejecutándose")
        print(f"   - Puerto 3308 no está disponible")
        print(f"   - Credenciales incorrectas")
        print(f"   - Base de datos 'Ligol' no existe")
        return False

if __name__ == "__main__":
    if verificar_mysql():
        print(f"\n✅ CONEXIÓN EXITOSA - El sistema está listo para probar el filtrado")
    else:
        print(f"\n❌ CONEXIÓN FALLIDA - Revisar configuración de MySQL")
