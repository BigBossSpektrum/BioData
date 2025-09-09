#!/usr/bin/env python3
"""
Investigar por qué Django no encuentra los datos
"""

import os
import sys
import django
import sqlite3

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

def investigar_discrepancia():
    print("🔍 INVESTIGANDO DISCREPANCIA ENTRE DJANGO Y SQLITE")
    print("=" * 60)
    
    try:
        from API.models import UsuarioBiometrico, RegistroAsistencia
        from django.db import connection
        
        # Verificar conexión de Django
        print("🔗 VERIFICANDO CONEXIÓN DE DJANGO:")
        print(f"  Base de datos: {connection.settings_dict['NAME']}")
        print(f"  Motor: {connection.settings_dict['ENGINE']}")
        
        # Consulta directa con Django
        print(f"\n📊 CONSULTAS DJANGO:")
        usuarios_django = UsuarioBiometrico.objects.all()
        registros_django = RegistroAsistencia.objects.all()
        print(f"  UsuarioBiometrico: {usuarios_django.count()}")
        print(f"  RegistroAsistencia: {registros_django.count()}")
        
        # Consulta directa con SQLite
        print(f"\n💾 CONSULTAS SQLITE DIRECTAS:")
        db_file = 'db.sqlite3'
        if os.path.exists(db_file):
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Verificar UsuarioBiometrico
            cursor.execute("SELECT COUNT(*) FROM API_usuariobiometrico")
            count_usuarios = cursor.fetchone()[0]
            print(f"  API_usuariobiometrico: {count_usuarios}")
            
            if count_usuarios > 0:
                cursor.execute("SELECT id, nombre, activo FROM API_usuariobiometrico LIMIT 5")
                usuarios = cursor.fetchall()
                print(f"    Ejemplos:")
                for usuario in usuarios:
                    print(f"      ID: {usuario[0]}, Nombre: {usuario[1]}, Activo: {usuario[2]}")
            
            # Verificar RegistroAsistencia
            cursor.execute("SELECT COUNT(*) FROM API_registroasistencia")
            count_registros = cursor.fetchone()[0]
            print(f"  API_registroasistencia: {count_registros}")
            
            if count_registros > 0:
                cursor.execute("SELECT id, user_id, timestamp FROM API_registroasistencia LIMIT 5")
                registros = cursor.fetchall()
                print(f"    Ejemplos:")
                for registro in registros:
                    print(f"      ID: {registro[0]}, User_ID: {registro[1]}, Timestamp: {registro[2]}")
            
            conn.close()
        
        # Verificar configuración de la base de datos
        print(f"\n⚙️ CONFIGURACIÓN DE BD:")
        from django.conf import settings
        print(f"  DATABASE_URL: {getattr(settings, 'DATABASE_URL', 'No definido')}")
        print(f"  DATABASES: {settings.DATABASES}")
        
        # Intentar consulta raw
        print(f"\n🔧 CONSULTA RAW DE DJANGO:")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM API_usuariobiometrico")
            count_raw = cursor.fetchone()[0]
            print(f"  Raw query UsuarioBiometrico: {count_raw}")
            
            cursor.execute("SELECT COUNT(*) FROM API_registroasistencia")
            count_raw = cursor.fetchone()[0]
            print(f"  Raw query RegistroAsistencia: {count_raw}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigar_discrepancia()
