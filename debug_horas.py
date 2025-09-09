#!/usr/bin/env python
"""
Script para debuggear por qué los resúmenes no muestran horas trabajadas
"""

import os
import sys
import django
from datetime import datetime, date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia

def debug_empleado_horas():
    """Debug detallado de un empleado para entender por qué no hay horas"""
    print("🔍 DEBUGGING DE HORAS TRABAJADAS")
    print("=" * 60)
    
    # Obtener un empleado activo
    empleado = UsuarioBiometrico.objects.filter(activo=True).first()
    
    if not empleado:
        print("❌ No se encontraron empleados activos")
        return
    
    print(f"👤 Empleado: {empleado.nombre}")
    print(f"🏢 Estación: {empleado.estacion.nombre if empleado.estacion else 'Sin estación'}")
    print(f"🕐 Turno: {empleado.turno.nombre if empleado.turno else 'Sin turno'}")
    
    if empleado.turno:
        print(f"   - Es nocturno: {empleado.turno.es_nocturno}")
        print(f"   - Hora inicio: {empleado.turno.hora_inicio}")
        print(f"   - Hora fin: {empleado.turno.hora_fin}")
    
    print("\n" + "=" * 60)
    
    # Verificar registros de asistencia
    total_registros = RegistroAsistencia.objects.filter(user=empleado).count()
    print(f"📊 Total registros de asistencia: {total_registros}")
    
    if total_registros == 0:
        print("❌ El empleado no tiene registros de asistencia")
        print("   Esto explica por qué no hay horas calculadas")
        return
    
    # Mostrar algunos registros recientes
    registros_recientes = RegistroAsistencia.objects.filter(
        user=empleado
    ).order_by('-timestamp')[:10]
    
    print("\n📅 Últimos 10 registros:")
    for i, registro in enumerate(registros_recientes, 1):
        status_text = "Entrada" if registro.status == 0 else "Salida"
        print(f"   {i}. {registro.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {status_text}")
    
    print("\n" + "=" * 60)
    
    # Probar cálculo para los últimos 7 días
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=7)
    
    print(f"🧮 Probando cálculo para período: {fecha_inicio} al {fecha_fin}")
    
    print("\n📋 Análisis día por día:")
    current_date = fecha_inicio
    total_horas_encontradas = 0
    
    while current_date <= fecha_fin:
        print(f"\n📆 {current_date.strftime('%Y-%m-%d (%A)')}:")
        
        # Calcular horas del día
        resultado = empleado.calcular_horas_dia(current_date)
        
        print(f"   - Horas trabajadas: {resultado['horas_trabajadas']:.2f}")
        print(f"   - Horas extras: {resultado['horas_extras']:.2f}")
        print(f"   - Estado: {resultado.get('estado', 'N/A')}")
        print(f"   - Mensaje: {resultado.get('mensaje', 'N/A')}")
        print(f"   - Registros encontrados: {len(resultado.get('registros', []))}")
        
        if resultado.get('entrada'):
            print(f"   - Entrada: {resultado['entrada'].timestamp}")
        if resultado.get('salida'):
            print(f"   - Salida: {resultado['salida'].timestamp}")
        
        total_horas_encontradas += resultado['horas_trabajadas']
        current_date += timedelta(days=1)
    
    print(f"\n📊 RESUMEN:")
    print(f"   - Total horas encontradas en 7 días: {total_horas_encontradas:.2f}")
    
    # Probar función de resumen completa
    print(f"\n🧮 Probando función calcular_resumen_rango_fechas:")
    resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
    
    print(f"   - Horas normales: {resumen['horas_normales']:.2f}")
    print(f"   - Horas extra diurno: {resumen['horas_extra_diurno']:.2f}")
    print(f"   - Horas extra nocturno: {resumen['horas_extra_nocturno']:.2f}")
    print(f"   - Total horas trabajadas: {resumen['total_horas_trabajadas']:.2f}")
    print(f"   - Total horas extras: {resumen['total_horas_extras']:.2f}")

def verificar_otros_empleados():
    """Verificar si el problema es general o específico de un empleado"""
    print("\n" + "=" * 60)
    print("🔍 VERIFICANDO OTROS EMPLEADOS")
    print("=" * 60)
    
    empleados = UsuarioBiometrico.objects.filter(activo=True)[:5]  # Primeros 5
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=7)
    
    for empleado in empleados:
        print(f"\n👤 {empleado.nombre}:")
        
        # Contar registros
        total_registros = RegistroAsistencia.objects.filter(user=empleado).count()
        print(f"   - Registros de asistencia: {total_registros}")
        
        if total_registros > 0:
            # Calcular resumen
            resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
            print(f"   - Horas trabajadas (7 días): {resumen['total_horas_trabajadas']:.2f}")
        else:
            print(f"   - Sin registros de asistencia")

def verificar_estructura_datos():
    """Verificar la estructura de datos de los modelos"""
    print("\n" + "=" * 60)
    print("🔍 VERIFICANDO ESTRUCTURA DE DATOS")
    print("=" * 60)
    
    from API.models import Turno, EstacionTrabajo
    
    # Verificar turnos
    turnos = Turno.objects.all()
    print(f"🕐 Turnos configurados: {turnos.count()}")
    for turno in turnos:
        print(f"   - {turno.nombre}: {turno.hora_inicio} - {turno.hora_fin} (Nocturno: {turno.es_nocturno})")
    
    # Verificar estaciones
    estaciones = EstacionTrabajo.objects.all()
    print(f"\n🏢 Estaciones de trabajo: {estaciones.count()}")
    for estacion in estaciones:
        empleados_count = UsuarioBiometrico.objects.filter(estacion=estacion, activo=True).count()
        print(f"   - {estacion.nombre}: {empleados_count} empleados activos")
    
    # Verificar empleados sin turno o estación
    sin_turno = UsuarioBiometrico.objects.filter(activo=True, turno__isnull=True).count()
    sin_estacion = UsuarioBiometrico.objects.filter(activo=True, estacion__isnull=True).count()
    
    print(f"\n⚠️  Empleados activos sin turno: {sin_turno}")
    print(f"⚠️  Empleados activos sin estación: {sin_estacion}")

if __name__ == "__main__":
    debug_empleado_horas()
    verificar_otros_empleados()
    verificar_estructura_datos()
    
    print("\n" + "=" * 60)
    print("🔧 POSIBLES SOLUCIONES:")
    print("=" * 60)
    print("1. Si no hay registros de asistencia: Verificar conexión con dispositivos biométricos")
    print("2. Si hay registros pero no se calculan horas: Revisar función calcular_horas_dia")
    print("3. Si empleados sin turno: Asignar turnos a los empleados")
    print("4. Si problemas con turnos nocturnos: Revisar lógica de fechas")
    print("=" * 60)
