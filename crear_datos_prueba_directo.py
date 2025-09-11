#!/usr/bin/env python
"""
Script para probar directamente usando Django ORM
simulando el guardado de datos biométricos.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio

def crear_datos_prueba_directo():
    """Crea datos de prueba directamente en la base de datos"""
    print("🧪 CREANDO DATOS DE PRUEBA DIRECTAMENTE EN LA BD")
    print("=" * 60)
    
    # Obtener la estación PRINCIPAL
    try:
        estacion_principal = EstacionServicio.objects.get(nombre="PRINCIPAL")
        print(f"✅ Estación encontrada: {estacion_principal.nombre}")
    except EstacionServicio.DoesNotExist:
        print("❌ Error: No se encontró la estación PRINCIPAL")
        return False
    
    # Obtener la estación La Soledad
    try:
        estacion_soledad = EstacionServicio.objects.get(nombre="La Soledad")
        print(f"✅ Estación encontrada: {estacion_soledad.nombre}")
    except EstacionServicio.DoesNotExist:
        print("❌ Error: No se encontró la estación La Soledad")
        return False
    
    # Crear o obtener usuarios
    usuario1, created1 = UsuarioBiometrico.objects.get_or_create(
        biometrico_id=1,
        defaults={
            'nombre': 'Juan Pérez',
            'activo': True,
            'estacion': estacion_principal
        }
    )
    print(f"{'🆕' if created1 else '♻️'} Usuario 1: {usuario1.nombre} (ID: {usuario1.biometrico_id})")
    
    usuario2, created2 = UsuarioBiometrico.objects.get_or_create(
        biometrico_id=2,
        defaults={
            'nombre': 'María González',
            'activo': True,
            'estacion': estacion_soledad
        }
    )
    print(f"{'🆕' if created2 else '♻️'} Usuario 2: {usuario2.nombre} (ID: {usuario2.biometrico_id})")
    
    # Crear registros de asistencia
    ahora = datetime.now()
    
    registros_creados = 0
    
    # Entrada de Juan Pérez
    registro1, created = RegistroAsistencia.objects.get_or_create(
        user=usuario1,
        timestamp=ahora - timedelta(hours=2),
        estacion_servicio=estacion_principal,
        defaults={'status': 0}  # Entrada
    )
    if created:
        registros_creados += 1
        print(f"🟢 Entrada registrada: {usuario1.nombre} a las {registro1.timestamp.strftime('%H:%M:%S')}")
    
    # Salida de Juan Pérez
    registro2, created = RegistroAsistencia.objects.get_or_create(
        user=usuario1,
        timestamp=ahora,
        estacion_servicio=estacion_principal,
        defaults={'status': 1}  # Salida
    )
    if created:
        registros_creados += 1
        print(f"🔴 Salida registrada: {usuario1.nombre} a las {registro2.timestamp.strftime('%H:%M:%S')}")
    
    # Entrada de María González
    registro3, created = RegistroAsistencia.objects.get_or_create(
        user=usuario2,
        timestamp=ahora - timedelta(hours=1),
        estacion_servicio=estacion_soledad,
        defaults={'status': 0}  # Entrada
    )
    if created:
        registros_creados += 1
        print(f"🟢 Entrada registrada: {usuario2.nombre} a las {registro3.timestamp.strftime('%H:%M:%S')}")
    
    print(f"\n✅ Proceso completado: {registros_creados} nuevos registros creados")
    return True

def mostrar_resumen():
    """Muestra un resumen de los datos en la base de datos"""
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE DATOS EN LA BASE DE DATOS")
    print("=" * 60)
    
    total_usuarios = UsuarioBiometrico.objects.count()
    total_registros = RegistroAsistencia.objects.count()
    
    print(f"👥 Total usuarios biométricos: {total_usuarios}")
    print(f"📝 Total registros de asistencia: {total_registros}")
    
    if total_usuarios > 0:
        print("\n👥 USUARIOS:")
        for usuario in UsuarioBiometrico.objects.all():
            registros_usuario = RegistroAsistencia.objects.filter(user=usuario).count()
            print(f"   - {usuario.nombre} (ID: {usuario.biometrico_id}) - {registros_usuario} registros")
    
    if total_registros > 0:
        print("\n📝 ÚLTIMOS 5 REGISTROS:")
        for registro in RegistroAsistencia.objects.order_by('-timestamp')[:5]:
            tipo = "Entrada" if registro.status == 0 else "Salida"
            print(f"   - {registro.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {registro.user.nombre} | {tipo} | {registro.estacion_servicio.nombre}")

def main():
    print(f"🕐 Hora de prueba: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if crear_datos_prueba_directo():
        mostrar_resumen()
        print("\n💡 Los datos se han guardado exitosamente en la base de datos!")
        print("   Puedes verificarlos ejecutando: python ver_datos_guardados.py")
    else:
        print("\n❌ Error al crear los datos de prueba")

if __name__ == "__main__":
    main()
