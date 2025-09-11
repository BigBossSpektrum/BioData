#!/usr/bin/env python
"""
Script para ver los datos guardados en la base de datos
de registros biométricos y usuarios.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio

def mostrar_usuarios_biometricos():
    """Muestra todos los usuarios biométricos registrados"""
    print("=" * 80)
    print("USUARIOS BIOMÉTRICOS REGISTRADOS")
    print("=" * 80)
    
    usuarios = UsuarioBiometrico.objects.all().order_by('biometrico_id')
    
    if not usuarios.exists():
        print("❌ No hay usuarios biométricos registrados.")
        return
    
    print(f"Total de usuarios: {usuarios.count()}")
    print()
    
    for usuario in usuarios:
        print(f"🧑 ID Biométrico: {usuario.biometrico_id}")
        print(f"   Nombre: {usuario.nombre or 'Sin nombre'}")
        print(f"   Activo: {'✅ Sí' if usuario.activo else '❌ No'}")
        print(f"   Estación: {usuario.estacion.nombre if usuario.estacion else 'Sin asignar'}")
        print(f"   Turno: {usuario.turno.nombre if usuario.turno else 'Sin turno'}")
        print(f"   Jefe: {usuario.jefe.username if usuario.jefe else 'Sin jefe'}")
        print("-" * 50)

def mostrar_registros_asistencia(limite=20):
    """Muestra los registros de asistencia más recientes"""
    print("\n" + "=" * 80)
    print(f"REGISTROS DE ASISTENCIA (Últimos {limite})")
    print("=" * 80)
    
    registros = RegistroAsistencia.objects.select_related(
        'user', 'estacion_servicio'
    ).order_by('-timestamp')[:limite]
    
    if not registros.exists():
        print("❌ No hay registros de asistencia.")
        return
    
    print(f"Total de registros en BD: {RegistroAsistencia.objects.count()}")
    print(f"Mostrando los últimos {registros.count()} registros:")
    print()
    
    for registro in registros:
        status_icon = "🟢" if registro.status == 0 else "🔴"
        status_text = "Entrada" if registro.status == 0 else "Salida"
        
        print(f"{status_icon} {registro.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Usuario: {registro.user.nombre or f'ID-{registro.user.biometrico_id}'}")
        print(f"   Tipo: {status_text} (status={registro.status})")
        print(f"   Estación: {registro.estacion_servicio.nombre if registro.estacion_servicio else 'Sin estación'}")
        if registro.aprobado is not None:
            print(f"   Aprobado: {'✅ Sí' if registro.aprobado else '❌ No'}")
        print("-" * 50)

def mostrar_estaciones():
    """Muestra las estaciones de servicio registradas"""
    print("\n" + "=" * 80)
    print("ESTACIONES DE SERVICIO")
    print("=" * 80)
    
    estaciones = EstacionServicio.objects.all()
    
    if not estaciones.exists():
        print("❌ No hay estaciones registradas.")
        return
    
    print(f"Total de estaciones: {estaciones.count()}")
    print()
    
    for estacion in estaciones:
        usuarios_count = estacion.usuarios_biometricos.count()
        registros_count = RegistroAsistencia.objects.filter(estacion_servicio=estacion).count()
        
        print(f"🏢 {estacion.nombre}")
        print(f"   Usuarios asignados: {usuarios_count}")
        print(f"   Registros totales: {registros_count}")
        if estacion.jefe:
            print(f"   Jefe: {estacion.jefe.username}")
        print("-" * 50)

def mostrar_estadisticas_recientes():
    """Muestra estadísticas de los últimos días"""
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS RECIENTES (Últimos 7 días)")
    print("=" * 80)
    
    fecha_limite = datetime.now() - timedelta(days=7)
    
    registros_recientes = RegistroAsistencia.objects.filter(
        timestamp__gte=fecha_limite
    )
    
    entradas = registros_recientes.filter(status=0).count()
    salidas = registros_recientes.filter(status=1).count()
    
    print(f"📊 Registros de los últimos 7 días: {registros_recientes.count()}")
    print(f"   🟢 Entradas: {entradas}")
    print(f"   🔴 Salidas: {salidas}")
    
    # Registros por día
    print("\n📅 Registros por día:")
    for i in range(7):
        fecha = datetime.now().date() - timedelta(days=i)
        registros_dia = registros_recientes.filter(
            timestamp__date=fecha
        ).count()
        if registros_dia > 0:
            print(f"   {fecha}: {registros_dia} registros")

def main():
    print(f"🕐 Consulta realizada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        mostrar_usuarios_biometricos()
        mostrar_registros_asistencia()
        mostrar_estaciones()
        mostrar_estadisticas_recientes()
        
    except Exception as e:
        print(f"❌ Error al consultar la base de datos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
