#!/usr/bin/env python3
"""
Script para probar las jornadas especiales de 12 horas
Este script crea ejemplos de jornadas especiales y demuestra el funcionamiento
"""

import os
import sys
import django
from datetime import datetime, date, time, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import JornadaEspecial, UsuarioBiometrico, CustomUser, EstacionServicio, RegistroAsistencia
from django.utils import timezone


def crear_jornada_especial_ejemplo():
    """
    Crea una jornada especial de ejemplo para demostrar el funcionamiento
    """
    
    print("=== CREANDO JORNADA ESPECIAL DE EJEMPLO ===\n")
    
    # Buscar o crear un jefe de patio
    jefe_patio, created = CustomUser.objects.get_or_create(
        username='jefe_ejemplo',
        defaults={
            'email': 'jefe@ejemplo.com',
            'rol': 'jefe_patio',
            'first_name': 'Jefe',
            'last_name': 'Patio'
        }
    )
    
    if created:
        jefe_patio.set_password('123456')
        jefe_patio.save()
        print(f"✅ Creado jefe de patio: {jefe_patio.username}")
    else:
        print(f"ℹ️  Usando jefe existente: {jefe_patio.username}")
    
    # Buscar o crear una estación
    estacion, created = EstacionServicio.objects.get_or_create(
        nombre='Estación Ejemplo',
        defaults={
            'direccion': 'Dirección de ejemplo',
            'jefe': jefe_patio
        }
    )
    
    if created:
        print(f"✅ Creada estación: {estacion.nombre}")
    else:
        estacion.jefe = jefe_patio
        estacion.save()
        print(f"ℹ️  Usando estación existente: {estacion.nombre}")
    
    # Buscar o crear un empleado
    empleado, created = UsuarioBiometrico.objects.get_or_create(
        nombre='Juan Carlos Trabajador',
        defaults={
            'biometrico_id': 999,
            'estacion': estacion,
            'activo': True
        }
    )
    
    if created:
        print(f"✅ Creado empleado: {empleado.nombre}")
    else:
        empleado.estacion = estacion
        empleado.save()
        print(f"ℹ️  Usando empleado existente: {empleado.nombre}")
    
    # Crear jornada especial
    fecha_inicio = date.today()
    fecha_fin = fecha_inicio + timedelta(days=2)
    
    jornada_especial, created = JornadaEspecial.objects.get_or_create(
        empleado=empleado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        defaults={
            'hora_inicio_programada': time(6, 0),
            'hora_fin_programada': time(18, 0),
            'horas_programadas': 12.0,
            'aprobada_por': jefe_patio,
            'observaciones': 'Jornada especial creada para pruebas del sistema',
            'activa': True
        }
    )
    
    if created:
        print(f"✅ Creada jornada especial para {empleado.nombre}")
        print(f"   📅 Fechas: {fecha_inicio} al {fecha_fin}")
        print(f"   🕐 Horario: {jornada_especial.hora_inicio_programada} - {jornada_especial.hora_fin_programada}")
        print(f"   ⏱️  Horas programadas: {jornada_especial.horas_programadas}")
    else:
        print(f"ℹ️  Ya existe jornada especial para estas fechas")
    
    return jefe_patio, empleado, jornada_especial


def crear_registros_ejemplo(empleado, jornada_especial):
    """
    Crea registros de asistencia de ejemplo para probar las jornadas especiales
    """
    
    print(f"\n=== CREANDO REGISTROS DE ASISTENCIA DE EJEMPLO ===\n")
    
    # Obtener la estación del empleado
    estacion = empleado.estacion
    
    # Crear entrada del primer día a las 6:15 AM
    entrada_datetime = timezone.make_aware(
        datetime.combine(jornada_especial.fecha_inicio, time(6, 15))
    )
    
    # Crear salida del día siguiente a las 6:30 AM (12 horas 15 minutos después)
    salida_datetime = timezone.make_aware(
        datetime.combine(jornada_especial.fecha_inicio + timedelta(days=1), time(6, 30))
    )
    
    # Crear registro de entrada
    entrada, created = RegistroAsistencia.objects.get_or_create(
        user=empleado,
        timestamp=entrada_datetime,
        status=0,  # Entrada
        defaults={
            'nombre': empleado.nombre,
            'estacion_servicio': estacion
        }
    )
    
    if created:
        print(f"✅ Creado registro de ENTRADA: {entrada.timestamp}")
    else:
        print(f"ℹ️  Ya existe registro de entrada: {entrada.timestamp}")
    
    # Crear registro de salida
    salida, created = RegistroAsistencia.objects.get_or_create(
        user=empleado,
        timestamp=salida_datetime,
        status=1,  # Salida
        defaults={
            'nombre': empleado.nombre,
            'estacion_servicio': estacion
        }
    )
    
    if created:
        print(f"✅ Creado registro de SALIDA: {salida.timestamp}")
    else:
        print(f"ℹ️  Ya existe registro de salida: {salida.timestamp}")
    
    return entrada, salida


def probar_calculo_jornada_especial(empleado, jornada_especial):
    """
    Prueba el cálculo de horas para jornadas especiales
    """
    
    print(f"\n=== PROBANDO CÁLCULO DE JORNADA ESPECIAL ===\n")
    
    # Probar el cálculo para el primer día de la jornada especial
    fecha_prueba = jornada_especial.fecha_inicio
    resultado = empleado.calcular_horas_dia(fecha_prueba)
    
    print(f"📊 RESULTADO DEL CÁLCULO para {fecha_prueba}:")
    print(f"   ✅ Es jornada especial: {resultado.get('jornada_especial', False)}")
    print(f"   ⏱️  Horas trabajadas: {resultado['horas_trabajadas']} ({resultado['horas_trabajadas_formato']})")
    print(f"   📋 Horas normales: {resultado['horas_normales']} ({resultado['horas_normales_formato']})")
    print(f"   ⚠️  Horas extras: {resultado['horas_extras']} ({resultado['horas_extras_formato']})")
    print(f"   📝 Estado: {resultado['estado']}")
    print(f"   💬 Mensaje: {resultado['mensaje']}")
    
    if resultado.get('entrada'):
        print(f"   🚪 Entrada: {resultado['entrada'].timestamp}")
    if resultado.get('salida'):
        print(f"   🚪 Salida: {resultado['salida'].timestamp}")
    
    # Calcular duración total
    if resultado.get('entrada') and resultado.get('salida'):
        duracion = resultado['salida'].timestamp - resultado['entrada'].timestamp
        print(f"   ⏰ Duración total: {duracion}")


def mostrar_resumen():
    """
    Muestra un resumen del sistema de jornadas especiales
    """
    
    print(f"\n=== RESUMEN DEL SISTEMA ===\n")
    
    total_jornadas = JornadaEspecial.objects.count()
    activas = JornadaEspecial.objects.filter(activa=True).count()
    
    print(f"📊 Estadísticas:")
    print(f"   📋 Total jornadas especiales: {total_jornadas}")
    print(f"   ✅ Jornadas activas: {activas}")
    print(f"   ❌ Jornadas inactivas: {total_jornadas - activas}")
    
    print(f"\n🔧 Características del sistema:")
    print(f"   ✅ Jornadas de 12 horas que pueden pasar al día siguiente")
    print(f"   ✅ Panel exclusivo para jefes de patio")
    print(f"   ✅ Cálculo automático: primera entrada + siguiente salida")
    print(f"   ✅ Validación de solapamientos")
    print(f"   ✅ Control de activación/desactivación")
    
    print(f"\n🌐 Acceso al sistema:")
    print(f"   👨‍💼 Panel jefe de patio: http://127.0.0.1:8000/panel-jefe-patio/")
    print(f"   🔧 Admin Django: http://127.0.0.1:8000/admin/")


def main():
    """
    Función principal que ejecuta todos los ejemplos
    """
    
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE JORNADAS ESPECIALES\n")
    
    try:
        # Crear datos de ejemplo
        jefe_patio, empleado, jornada_especial = crear_jornada_especial_ejemplo()
        
        # Crear registros de asistencia
        entrada, salida = crear_registros_ejemplo(empleado, jornada_especial)
        
        # Probar el cálculo
        probar_calculo_jornada_especial(empleado, jornada_especial)
        
        # Mostrar resumen
        mostrar_resumen()
        
        print(f"\n✅ PRUEBAS COMPLETADAS EXITOSAMENTE")
        print(f"\n🔑 CREDENCIALES DE ACCESO:")
        print(f"   👤 Usuario: jefe_ejemplo")
        print(f"   🔒 Contraseña: 123456")
        print(f"   🌐 URL: http://127.0.0.1:8000/panel-jefe-patio/")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
