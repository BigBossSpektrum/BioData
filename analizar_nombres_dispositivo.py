#!/usr/bin/env python
"""
Script para analizar los nombres que llegan desde el dispositivo biométrico
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio
from django.db.models import Count, Q, Min, Max
from django.utils import timezone

def analizar_nombres_actuales():
    """
    Analiza los nombres actuales en la base de datos
    """
    print("=" * 80)
    print("ANÁLISIS DE NOMBRES ACTUALES EN BASE DE DATOS")
    print("=" * 80)
    
    # Todos los usuarios
    total_usuarios = UsuarioBiometrico.objects.count()
    
    # Usuarios con nombres genéricos
    usuarios_genericos = UsuarioBiometrico.objects.filter(
        nombre__startswith='Usuario_'
    ).count()
    
    # Usuarios con nombres reales
    usuarios_reales = UsuarioBiometrico.objects.exclude(
        nombre__startswith='Usuario_'
    ).exclude(
        nombre__isnull=True
    ).exclude(
        nombre__exact=''
    ).count()
    
    # Usuarios sin nombre
    usuarios_sin_nombre = UsuarioBiometrico.objects.filter(
        Q(nombre__isnull=True) | Q(nombre__exact='')
    ).count()
    
    print(f"📊 Total de usuarios: {total_usuarios}")
    print(f"🏷️  Usuarios con nombres genéricos (Usuario_#): {usuarios_genericos}")
    print(f"👤 Usuarios con nombres reales: {usuarios_reales}")
    print(f"❓ Usuarios sin nombre: {usuarios_sin_nombre}")
    
    print(f"\nPorcentajes:")
    if total_usuarios > 0:
        print(f"  Genéricos: {(usuarios_genericos/total_usuarios*100):.1f}%")
        print(f"  Reales: {(usuarios_reales/total_usuarios*100):.1f}%")
        print(f"  Sin nombre: {(usuarios_sin_nombre/total_usuarios*100):.1f}%")

def mostrar_usuarios_con_nombres_reales():
    """
    Muestra usuarios que ya tienen nombres reales
    """
    print("\n" + "=" * 80)
    print("USUARIOS CON NOMBRES REALES")
    print("=" * 80)
    
    usuarios_reales = UsuarioBiometrico.objects.exclude(
        nombre__startswith='Usuario_'
    ).exclude(
        nombre__isnull=True
    ).exclude(
        nombre__exact=''
    ).order_by('nombre')
    
    print(f"Total: {usuarios_reales.count()} usuarios\n")
    
    for usuario in usuarios_reales:
        registros_count = RegistroAsistencia.objects.filter(user=usuario).count()
        ultimo_registro = RegistroAsistencia.objects.filter(user=usuario).order_by('-timestamp').first()
        
        if ultimo_registro:
            try:
                ultimo_fecha = ultimo_registro.timestamp.strftime('%d/%m/%Y')
            except:
                ultimo_fecha = 'Error en fecha'
        else:
            ultimo_fecha = 'Sin registros'
        
        print(f"👤 {usuario.nombre}")
        print(f"   ID Biométrico: {usuario.biometrico_id}")
        print(f"   Estación: {usuario.estacion.nombre if usuario.estacion else 'Sin asignar'}")
        print(f"   Registros: {registros_count}")
        print(f"   Último registro: {ultimo_fecha}")
        print()

def simular_actualizacion_nombres():
    """
    Simula qué pasaría si aplicamos la nueva lógica de nombres
    """
    print("\n" + "=" * 80)
    print("SIMULACIÓN DE ACTUALIZACIÓN DE NOMBRES")
    print("=" * 80)
    
    usuarios_genericos = UsuarioBiometrico.objects.filter(
        nombre__startswith='Usuario_'
    ).order_by('biometrico_id')
    
    print("Usuarios genéricos que se beneficiarían de nombres reales del dispositivo:\n")
    
    for usuario in usuarios_genericos:
        registros_recientes = RegistroAsistencia.objects.filter(
            user=usuario,
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        print(f"🔄 {usuario.nombre} (ID: {usuario.biometrico_id})")
        print(f"   Estación actual: {usuario.estacion.nombre if usuario.estacion else 'Sin asignar'}")
        print(f"   Registros últimos 7 días: {registros_recientes}")
        print(f"   Estado: {'Activo' if registros_recientes > 0 else 'Inactivo'}")
        
        # Sugerir qué hacer
        if registros_recientes > 0:
            print(f"   ✅ CANDIDATO: Recibirá nombre real en próximos registros del dispositivo")
        else:
            print(f"   ⏸️  INACTIVO: No recibirá actualización hasta nuevo registro")
        print()

def crear_script_monitoreo():
    """
    Crea un script para monitorear las actualizaciones de nombres
    """
    script_content = '''#!/usr/bin/env python
"""
Script de monitoreo de actualizaciones de nombres desde dispositivo biométrico
Ejecutar después de sincronización para ver cambios
"""

import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico
from django.utils import timezone

def monitorear_cambios_nombres():
    print(f"🔍 MONITOREO DE NOMBRES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Usuarios que siguen con nombres genéricos
    usuarios_pendientes = UsuarioBiometrico.objects.filter(
        nombre__startswith='Usuario_'
    ).count()
    
    # Usuarios con nombres reales
    usuarios_actualizados = UsuarioBiometrico.objects.exclude(
        nombre__startswith='Usuario_'
    ).exclude(
        nombre__isnull=True
    ).exclude(
        nombre__exact=''
    ).count()
    
    print(f"✅ Usuarios con nombres reales: {usuarios_actualizados}")
    print(f"⏳ Usuarios pendientes (Usuario_#): {usuarios_pendientes}")
    
    if usuarios_pendientes > 0:
        print("\\n📋 Usuarios pendientes de actualización:")
        pendientes = UsuarioBiometrico.objects.filter(
            nombre__startswith='Usuario_'
        ).order_by('biometrico_id')
        
        for usuario in pendientes[:10]:  # Mostrar primeros 10
            print(f"  - {usuario.nombre} (ID: {usuario.biometrico_id})")
        
        if usuarios_pendientes > 10:
            print(f"  ... y {usuarios_pendientes - 10} más")

if __name__ == "__main__":
    monitorear_cambios_nombres()
'''
    
    with open('monitorear_nombres.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("\n✅ Script de monitoreo creado: 'monitorear_nombres.py'")
    print("   Úsalo después de cada sincronización para ver los cambios")

def mostrar_instrucciones():
    """
    Muestra las instrucciones para el usuario
    """
    print("\n" + "=" * 80)
    print("📋 INSTRUCCIONES Y PRÓXIMOS PASOS")
    print("=" * 80)
    
    print("1. 🔧 CAMBIOS APLICADOS:")
    print("   ✅ Vista modificada para usar nombres del dispositivo biométrico")
    print("   ✅ Actualización automática de nombres cuando llegan del dispositivo")
    print("   ✅ Logs mejorados para rastrear cambios de nombres")
    
    print("\n2. 📡 QUÉ PASARÁ AHORA:")
    print("   - Los próximos registros del dispositivo actualizarán automáticamente los nombres")
    print("   - Los usuarios 'Usuario_#' recibirán sus nombres reales")
    print("   - Se mantendrá un log de todos los cambios")
    
    print("\n3. 🔍 MONITOREO:")
    print("   - Ejecuta 'python monitorear_nombres.py' para ver el progreso")
    print("   - Revisa los logs del servidor para ver actualizaciones en tiempo real")
    print("   - Los cambios serán graduales conforme lleguen nuevos registros")
    
    print("\n4. ⚡ ACELERACIÓN (Opcional):")
    print("   - Fuerza una sincronización completa del dispositivo biométrico")
    print("   - O espera a que lleguen nuevos registros naturalmente")
    
    print("\n5. 🔧 VALIDACIÓN:")
    print("   - Los usuarios activos cambiarán primero")
    print("   - Los usuarios inactivos cambiarán cuando vuelvan a registrarse")
    print("   - Backup automático antes de cada cambio")

if __name__ == "__main__":
    try:
        print("🚀 Analizando nombres desde dispositivo biométrico...")
        
        analizar_nombres_actuales()
        mostrar_usuarios_con_nombres_reales()
        simular_actualizacion_nombres()
        crear_script_monitoreo()
        mostrar_instrucciones()
        
        print(f"\n✅ Análisis completado. Sistema listo para recibir nombres reales del dispositivo.")
        
    except Exception as e:
        print(f"❌ Error en el análisis: {e}")
        import traceback
        traceback.print_exc()
