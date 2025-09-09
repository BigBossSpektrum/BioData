#!/usr/bin/env python3
"""
Crear datos de prueba para demostrar la funcionalidad de filtrado
"""

import os
import sys
import django
from datetime import date, datetime, timedelta, time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

def crear_datos_prueba():
    print("🔧 CREANDO DATOS DE PRUEBA")
    print("=" * 40)
    
    try:
        from API.models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio
        from django.utils import timezone
        
        # Crear estación de servicio
        estacion, created = EstacionServicio.objects.get_or_create(
            nombre="Estación Central",
            defaults={
                'direccion': 'Calle Principal 123'
            }
        )
        if created:
            print(f"✅ Estación creada: {estacion.nombre}")
        else:
            print(f"🔄 Estación existente: {estacion.nombre}")
        
        # Crear empleados de prueba
        empleados_data = [
            {"nombre": "RUBILCE DURAN", "biometrico_id": 1001},
            {"nombre": "OSCAR ROJAS", "biometrico_id": 1002},
            {"nombre": "RAMIRO DE JESUS AMADO", "biometrico_id": 1003},
        ]
        
        empleados_creados = []
        for emp_data in empleados_data:
            empleado, created = UsuarioBiometrico.objects.get_or_create(
                nombre=emp_data["nombre"],
                defaults={
                    'biometrico_id': emp_data["biometrico_id"],
                    'activo': True,
                    'privilegio': 0,
                    'estacion': estacion
                }
            )
            if created:
                print(f"✅ Empleado creado: {empleado.nombre}")
            else:
                print(f"🔄 Empleado existente: {empleado.nombre}")
                empleado.activo = True
                empleado.save()
            
            empleados_creados.append(empleado)
        
        # Crear registros de asistencia de prueba
        print(f"\n📊 CREANDO REGISTROS DE ASISTENCIA...")
        
        # Datos de los últimos 7 días
        fechas_prueba = []
        for i in range(7):
            fecha = date.today() - timedelta(days=i)
            fechas_prueba.append(fecha)
        
        registros_creados = 0
        for empleado in empleados_creados:
            for fecha in fechas_prueba[:3]:  # Solo 3 días por empleado
                # Crear registros de salida (como en los datos reales)
                horas_salida = [
                    time(11, 0, 0),   # 11:00 AM
                    time(19, 30, 0),  # 7:30 PM
                    time(23, 15, 0),  # 11:15 PM
                ]
                
                for hora in horas_salida[:2]:  # Solo 2 salidas por día
                    timestamp = timezone.make_aware(
                        datetime.combine(fecha, hora)
                    )
                    
                    registro, created = RegistroAsistencia.objects.get_or_create(
                        user=empleado,
                        timestamp=timestamp,
                        defaults={
                            'nombre': empleado.nombre,
                            'estacion_servicio': estacion,
                            'status': 15,  # Como en los datos reales
                            'aprobado': None
                        }
                    )
                    
                    if created:
                        registros_creados += 1
        
        print(f"✅ Registros de asistencia creados: {registros_creados}")
        
        # Verificar datos creados
        print(f"\n📊 VERIFICACIÓN FINAL:")
        print(f"  Empleados activos: {UsuarioBiometrico.objects.filter(activo=True).count()}")
        print(f"  Registros de asistencia: {RegistroAsistencia.objects.count()}")
        print(f"  Estaciones de servicio: {EstacionServicio.objects.count()}")
        
        # Mostrar algunos ejemplos
        print(f"\n👥 EMPLEADOS CREADOS:")
        for empleado in UsuarioBiometrico.objects.filter(activo=True):
            registros_emp = RegistroAsistencia.objects.filter(user=empleado).count()
            print(f"  ✅ {empleado.nombre} - {registros_emp} registros")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if crear_datos_prueba():
        print(f"\n🎉 DATOS DE PRUEBA CREADOS EXITOSAMENTE")
        print(f"💡 Ahora puedes probar la funcionalidad de filtrado en el sistema")
    else:
        print(f"\n❌ ERROR AL CREAR DATOS DE PRUEBA")
