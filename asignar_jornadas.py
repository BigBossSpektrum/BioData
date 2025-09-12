#!/usr/bin/env python
"""
Script para asignar jornadas laborales a empleados que no las tienen
"""

import os
import sys
import django
from datetime import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from API.models import UsuarioBiometrico, JornadaLaboral

def listar_jornadas():
    """Listar todas las jornadas laborales disponibles"""
    print("📋 JORNADAS LABORALES DISPONIBLES:")
    print("=" * 50)
    
    jornadas = JornadaLaboral.objects.all()
    
    if jornadas.count() == 0:
        print("❌ No hay jornadas laborales configuradas")
        return []
    
    for i, jornada in enumerate(jornadas, 1):
        tipo = "Nocturno" if jornada.es_nocturno else "Diurno"
        print(f"{i}. {jornada.nombre} ({tipo})")
        print(f"   Horario: {jornada.hora_inicio} - {jornada.hora_fin}")
        print(f"   Horas normales: {jornada.horas_normales}")
        print(f"   Días laborables: {jornada.dias_laborables}")
        print()
    
    return list(jornadas)

def crear_jornadas_basicas():
    """Crear jornadas laborales básicas si no existen"""
    print("🔧 CREANDO JORNADAS LABORALES BÁSICAS...")
    
    jornadas_basicas = [
        {
            'nombre': 'Turno Diurno (6:00 - 14:00)',
            'tipo_jornada': 'diurno',
            'hora_inicio': time(6, 0),
            'hora_fin': time(14, 0),
            'horas_normales': 8,
            'dias_laborables': 'lunes,martes,miercoles,jueves,viernes'
        },
        {
            'nombre': 'Turno Tarde (14:00 - 22:00)',
            'tipo_jornada': 'tarde',
            'hora_inicio': time(14, 0),
            'hora_fin': time(22, 0),
            'horas_normales': 8,
            'dias_laborables': 'lunes,martes,miercoles,jueves,viernes'
        },
        {
            'nombre': 'Turno Nocturno (22:00 - 6:00)',
            'tipo_jornada': 'nocturno',
            'hora_inicio': time(22, 0),
            'hora_fin': time(6, 0),
            'horas_normales': 8,
            'dias_laborables': 'lunes,martes,miercoles,jueves,viernes'
        }
    ]
    
    jornadas_creadas = 0
    
    for jornada_data in jornadas_basicas:
        jornada, created = JornadaLaboral.objects.get_or_create(
            nombre=jornada_data['nombre'],
            defaults=jornada_data
        )
        
        if created:
            print(f"✅ Creada: {jornada.nombre}")
            jornadas_creadas += 1
        else:
            print(f"⚠️  Ya existe: {jornada.nombre}")
    
    print(f"\n📊 Total jornadas creadas: {jornadas_creadas}")
    return jornadas_creadas > 0

def listar_empleados_sin_jornada():
    """Listar empleados activos que no tienen jornada asignada"""
    print("\n👥 EMPLEADOS SIN JORNADA ASIGNADA:")
    print("=" * 50)
    
    empleados_sin_jornada = UsuarioBiometrico.objects.filter(
        activo=True,
        turno__isnull=True
    )
    
    if empleados_sin_jornada.count() == 0:
        print("✅ Todos los empleados activos tienen jornada asignada")
        return []
    
    empleados = list(empleados_sin_jornada)
    
    for i, empleado in enumerate(empleados, 1):
        estacion = empleado.estacion.nombre if empleado.estacion else 'Sin estación'
        print(f"{i}. {empleado.nombre} - {estacion}")
    
    print(f"\n📊 Total empleados sin jornada: {len(empleados)}")
    return empleados

def asignar_jornada_automatica():
    """Asignar jornada automáticamente basándose en patrones de registros"""
    print("\n🤖 ASIGNACIÓN AUTOMÁTICA DE JORNADAS:")
    print("=" * 50)
    
    empleados_sin_jornada = UsuarioBiometrico.objects.filter(
        activo=True,
        turno__isnull=True
    )
    
    if empleados_sin_jornada.count() == 0:
        print("✅ No hay empleados sin jornada para asignar")
        return
    
    # Obtener jornada diurna por defecto
    jornada_diurna = JornadaLaboral.objects.filter(tipo_jornada='diurno').first()
    
    if not jornada_diurna:
        print("❌ No hay jornada diurna disponible para asignar")
        return
    
    empleados_asignados = 0
    
    for empleado in empleados_sin_jornada:
        # Por simplicidad, asignar jornada diurna a todos
        # En un sistema real, esto se basaría en análisis de horarios de registros
        empleado.turno = jornada_diurna
        empleado.save()
        
        print(f"✅ {empleado.nombre} -> {jornada_diurna.nombre}")
        empleados_asignados += 1
    
    print(f"\n📊 Total empleados con jornada asignada: {empleados_asignados}")

def probar_calculo_horas():
    """Probar el cálculo de horas después de asignar jornadas"""
    print("\n🧮 PROBANDO CÁLCULO DE HORAS DESPUÉS DE ASIGNAR JORNADAS:")
    print("=" * 60)
    
    from datetime import date, timedelta
    
    empleado = UsuarioBiometrico.objects.filter(activo=True, turno__isnull=False).first()
    
    if not empleado:
        print("❌ No hay empleados con jornada asignada para probar")
        return
    
    print(f"👤 Probando con: {empleado.nombre}")
    print(f"🕐 Jornada: {empleado.turno.nombre}")
    
    # Probar con los últimos 3 días
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=3)
    
    print(f"📅 Período: {fecha_inicio} al {fecha_fin}")
    
    total_horas = 0
    current_date = fecha_inicio
    
    while current_date <= fecha_fin:
        resultado = empleado.calcular_horas_dia(current_date)
        horas = resultado['horas_trabajadas']
        total_horas += horas
        
        estado_emoji = "✅" if horas > 0 else "⚠️"
        print(f"   {estado_emoji} {current_date}: {horas:.2f} horas - {resultado.get('estado', 'N/A')}")
        
        current_date += timedelta(days=1)
    
    print(f"\n📊 Total horas en 3 días: {total_horas:.2f}")
    
    # Probar función de resumen
    resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
    print(f"📋 Resumen función:")
    print(f"   - Horas normales: {resumen['horas_normales']:.2f}")
    print(f"   - Total horas trabajadas: {resumen['total_horas_trabajadas']:.2f}")

if __name__ == "__main__":
    print("🔧 CONFIGURACIÓN DE JORNADAS LABORALES")
    print("=" * 60)
    
    # Paso 1: Listar jornadas existentes
    jornadas_existentes = listar_jornadas()
    
    # Paso 2: Crear jornadas básicas si no existen
    if len(jornadas_existentes) == 0:
        crear_jornadas_basicas()
        jornadas_existentes = listar_jornadas()
    
    # Paso 3: Listar empleados sin jornada
    empleados_sin_jornada = listar_empleados_sin_jornada()
    
    # Paso 4: Asignar jornadas automáticamente
    if len(empleados_sin_jornada) > 0:
        asignar_jornada_automatica()
    
    # Paso 5: Probar cálculo de horas
    probar_calculo_horas()
    
    print("\n" + "=" * 60)
    print("🎉 CONFIGURACIÓN COMPLETADA")
    print("✅ Ahora los empleados deberían tener horas calculadas en los resúmenes")
    print("=" * 60)
