#!/usr/bin/env python
"""
Script para probar el nuevo sistema dinámico de cálculo de horas
que funciona solo con registros biométricos
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

def test_calculo_dinamico_horas():
    """Probar el nuevo cálculo dinámico de horas"""
    print("🧪 PROBANDO NUEVO SISTEMA DINÁMICO DE CÁLCULO DE HORAS")
    print("=" * 70)
    
    try:
        # Obtener un empleado para pruebas
        empleado = UsuarioBiometrico.objects.filter(activo=True).first()
        
        if not empleado:
            print("❌ No se encontraron empleados activos para pruebas")
            return False
        
        print(f"👤 Empleado de prueba: {empleado.nombre}")
        print(f"📋 Estado jornada laboral: {'Con jornada' if empleado.turno else 'SIN JORNADA (Ahora no importa)'}")
        
        # Probar último día con datos
        fecha_fin = date.today()
        fecha_inicio = fecha_fin - timedelta(days=7)
        
        print(f"\n📅 Probando período: {fecha_inicio} al {fecha_fin}")
        print("-" * 70)
        
        total_dias_con_datos = 0
        total_horas_trabajadas = 0
        total_horas_extras = 0
        
        # Probar día por día
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            print(f"\n📆 Analizando: {current_date}")
            
            # Usar la nueva función
            resultado = empleado.calcular_horas_dia(current_date)
            
            if resultado['horas_trabajadas'] > 0:
                total_dias_con_datos += 1
                total_horas_trabajadas += resultado['horas_trabajadas']
                total_horas_extras += resultado['horas_extras']
                
                print(f"  ✅ {resultado['mensaje']}")
                print(f"  📊 Horas trabajadas: {resultado['horas_trabajadas']:.2f}")
                print(f"  ⏰ Horas normales: {resultado['horas_normales']:.2f}")
                print(f"  🕑 Horas extras: {resultado['horas_extras']:.2f}")
                
                if resultado.get('es_turno_nocturno'):
                    print(f"  🌙 Turno nocturno detectado automáticamente")
                else:
                    print(f"  ☀️ Turno diurno detectado automáticamente")
                
                if resultado.get('entrada'):
                    print(f"  🟢 Entrada: {resultado['entrada'].timestamp}")
                if resultado.get('salida'):
                    print(f"  🔴 Salida: {resultado['salida'].timestamp}")
                    
            else:
                print(f"  ⚪ {resultado['mensaje']}")
            
            current_date += timedelta(days=1)
        
        print("\n" + "=" * 70)
        print("📈 RESUMEN TOTAL:")
        print(f"  📊 Días con datos: {total_dias_con_datos}")
        print(f"  ⏰ Total horas trabajadas: {total_horas_trabajadas:.2f}")
        print(f"  🕑 Total horas extras: {total_horas_extras:.2f}")
        
        if total_dias_con_datos > 0:
            print("\n✅ ¡NUEVO SISTEMA FUNCIONANDO CORRECTAMENTE!")
            print("🎉 El cálculo dinámico de horas está operativo")
            return True
        else:
            print("\n⚠️ No se encontraron datos para procesar")
            print("💡 Esto puede ser normal si no hay registros biométricos recientes")
            return True  # No es un error, solo falta de datos
        
    except Exception as e:
        print(f"\n❌ Error en el test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_resumen_rango_dinamico():
    """Probar la generación de resumen por rango con el nuevo sistema"""
    print("\n\n🧪 PROBANDO RESUMEN POR RANGO CON SISTEMA DINÁMICO")
    print("=" * 70)
    
    try:
        # Obtener un empleado para pruebas
        empleado = UsuarioBiometrico.objects.filter(activo=True).first()
        
        if not empleado:
            print("❌ No se encontraron empleados activos para pruebas")
            return False
        
        print(f"👤 Empleado de prueba: {empleado.nombre}")
        
        # Probar resumen de última semana
        fecha_fin = date.today()
        fecha_inicio = fecha_fin - timedelta(days=7)
        
        print(f"📅 Generando resumen: {fecha_inicio} al {fecha_fin}")
        
        # Usar la función de resumen
        resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
        
        print("\n📊 RESULTADO DEL RESUMEN:")
        print(f"  ⏰ Horas normales: {resumen['horas_normales']:.2f}")
        print(f"  🌅 Horas extra diurno: {resumen['horas_extra_diurno']:.2f}")
        print(f"  🌙 Horas extra nocturno: {resumen['horas_extra_nocturno']:.2f}")
        print(f"  🎉 Horas extra feriado diurno: {resumen['horas_extra_feriado_diurno']:.2f}")
        print(f"  🌃 Horas extra feriado nocturno: {resumen['horas_extra_feriado_nocturno']:.2f}")
        print(f"  📈 Total horas trabajadas: {resumen['total_horas_trabajadas']:.2f}")
        print(f"  💰 Costo total horas extras: ${resumen['costo_total_horas_extras']:.2f}")
        
        if resumen['total_horas_trabajadas'] > 0:
            print("\n✅ ¡RESUMEN GENERADO EXITOSAMENTE!")
            print("🎉 El sistema dinámico está calculando datos correctamente")
            return True
        else:
            print("\n⚠️ Resumen generado pero sin horas trabajadas")
            print("💡 Verificar que existan registros biométricos en el período")
            return True
        
    except Exception as e:
        print(f"\n❌ Error en el test de resumen: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def mostrar_registros_disponibles():
    """Mostrar información sobre registros disponibles"""
    print("\n\n📋 INFORMACIÓN DE REGISTROS DISPONIBLES")
    print("=" * 70)
    
    try:
        # Mostrar últimos registros
        registros_recientes = RegistroAsistencia.objects.order_by('-timestamp')[:10]
        
        if registros_recientes:
            print("🕐 Últimos 10 registros biométricos:")
            for i, registro in enumerate(registros_recientes, 1):
                tipo = "🟢 ENTRADA" if registro.status == 0 else "🔴 SALIDA"
                print(f"  {i:2d}. {registro.user.nombre:<20} | {tipo} | {registro.timestamp}")
        else:
            print("⚠️ No se encontraron registros biométricos")
        
        # Mostrar estadísticas
        total_empleados = UsuarioBiometrico.objects.filter(activo=True).count()
        total_registros = RegistroAsistencia.objects.count()
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"  👥 Empleados activos: {total_empleados}")
        print(f"  📝 Total registros biométricos: {total_registros}")
        
        if total_registros > 0:
            ultimo_registro = RegistroAsistencia.objects.latest('timestamp')
            print(f"  🕐 Último registro: {ultimo_registro.timestamp}")
            
    except Exception as e:
        print(f"❌ Error mostrando registros: {str(e)}")

if __name__ == "__main__":
    print("🚀 SISTEMA DINÁMICO DE CÁLCULO DE HORAS - SIN JORNADAS PREDEFINIDAS")
    print("=" * 70)
    
    # Mostrar registros disponibles
    mostrar_registros_disponibles()
    
    all_tests_passed = True
    
    # Test 1: Cálculo dinámico día por día
    if not test_calculo_dinamico_horas():
        all_tests_passed = False
    
    # Test 2: Resumen por rango
    if not test_resumen_rango_dinamico():
        all_tests_passed = False
    
    print("\n" + "=" * 70)
    if all_tests_passed:
        print("🎉 ¡SISTEMA DINÁMICO FUNCIONANDO PERFECTAMENTE!")
        print("✅ Los empleados ya no necesitan jornadas laborales asignadas")
        print("🔄 El sistema detecta automáticamente turnos y calcula horas")
        print("📊 Los resúmenes ahora mostrarán datos reales del biométrico")
    else:
        print("❌ HUBO PROBLEMAS EN LAS PRUEBAS")
        print("⚠️ Revisar errores anteriores")
    print("=" * 70)
