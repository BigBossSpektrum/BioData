#!/usr/bin/env python3
"""
Verificar estado actual de la base de datos
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

def verificar_bd():
    print("🔍 VERIFICACIÓN DEL ESTADO DE LA BASE DE DATOS")
    print("=" * 60)
    
    try:
        from API.models import UsuarioBiometrico, RegistroAsistencia, ResumenSemanal
        from django.utils import timezone
        
        # Contar todos los registros
        print("📊 CONTEO DE REGISTROS:")
        print(f"  UsuarioBiometrico: {UsuarioBiometrico.objects.count()}")
        print(f"  RegistroAsistencia: {RegistroAsistencia.objects.count()}")
        print(f"  ResumenSemanal: {ResumenSemanal.objects.count()}")
        
        # Verificar registros recientes
        hace_7_dias = timezone.now() - timedelta(days=7)
        registros_recientes = RegistroAsistencia.objects.filter(
            timestamp__gte=hace_7_dias
        ).count()
        print(f"  RegistroAsistencia (últimos 7 días): {registros_recientes}")
        
        # Mostrar algunos registros si existen
        if RegistroAsistencia.objects.count() > 0:
            print(f"\n📋 PRIMEROS 5 REGISTROS DE ASISTENCIA:")
            for registro in RegistroAsistencia.objects.all()[:5]:
                print(f"  {registro.user} - {registro.timestamp}")
        
        if UsuarioBiometrico.objects.count() > 0:
            print(f"\n👥 PRIMEROS 5 USUARIOS BIOMÉTRICOS:")
            for usuario in UsuarioBiometrico.objects.all()[:5]:
                print(f"  {usuario.nombre} (Activo: {usuario.activo})")
        
        # Verificar archivos de base de datos
        import sqlite3
        print(f"\n💾 VERIFICACIÓN DE ARCHIVOS BD:")
        db_files = ['db.sqlite3']
        for db_file in db_files:
            if os.path.exists(db_file):
                size = os.path.getsize(db_file)
                print(f"  {db_file}: {size:,} bytes")
                
                # Conectar y verificar tablas
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"    Tablas: {len(tables)}")
                
                # Verificar si las tablas tienen datos
                for table in ['API_usuariobiometrico', 'API_registroasistencia']:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"    {table}: {count} registros")
                    except sqlite3.OperationalError as e:
                        print(f"    {table}: Error - {e}")
                
                conn.close()
            else:
                print(f"  {db_file}: No existe")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_bd()
