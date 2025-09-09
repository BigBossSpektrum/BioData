#!/usr/bin/env python
"""
Script para probar el sistema dinámico con empleados que tienen registros recientes
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

def test_empleado_con_datos():
    """Probar con empleados que tienen registros recientes"""
    print("🧪 PROBANDO CON EMPLEADOS QUE TIENEN DATOS RECIENTES")
    print("=" * 70)
    
    try:
        # Buscar empleados con registros en los últimos 3 días
        fecha_limite = datetime.now() - timedelta(days=3)
        
        empleados_con_registros = UsuarioBiometrico.objects.filter(
            activo=True,
            registroasistencia__timestamp__gte=fecha_limite
        ).distinct()
        
        if not empleados_con_registros.exists():
            print("⚠️ No se encontraron empleados con registros recientes")
            return False
        
        print(f"👥 Empleados con registros recientes: {empleados_con_registros.count()}")
        
        # Probar con el primer empleado que tenga datos
        for empleado in empleados_con_registros[:3]:  # Probar máximo 3
            print(f"\n👤 Probando con: {empleado.nombre}")
            print("-" * 50)
            
            # Buscar días con registros para este empleado
            registros_recientes = RegistroAsistencia.objects.filter(
                user=empleado,
                timestamp__gte=fecha_limite
            ).order_by('timestamp')
            
            if not registros_recientes.exists():
                print("  ⚪ Sin registros para este empleado")
                continue
            
            # Obtener fechas únicas con registros
            fechas_con_registros = set()
            for registro in registros_recientes:
                fechas_con_registros.add(registro.timestamp.date())
            
            print(f"  📅 Fechas con registros: {sorted(fechas_con_registros)}")
            
            # Probar cálculo para cada fecha
            datos_encontrados = False
            for fecha in sorted(fechas_con_registros):
                print(f"\n  📆 Analizando fecha: {fecha}")
                
                resultado = empleado.calcular_horas_dia(fecha)
                
                if resultado['horas_trabajadas'] > 0:
                    datos_encontrados = True
                    # Mostrar mensaje si existe, o una descripción del resultado
                    mensaje = resultado.get('mensaje', resultado.get('observaciones', 'Horas calculadas exitosamente'))
                    print(f"    ✅ {mensaje}")
                    print(f"    📊 Horas trabajadas: {resultado['horas_trabajadas']:.2f}")
                    print(f"    ⏰ Horas normales: {resultado['horas_normales']:.2f}")
                    print(f"    🕑 Horas extras: {resultado['horas_extras']:.2f}")
                    
                    # Verificar tipo de jornada
                    tipo_jornada = resultado.get('tipo_jornada', 'desconocido')
                    if tipo_jornada == 'nocturno':
                        print(f"    🌙 Turno nocturno detectado")
                    elif tipo_jornada == 'diurno':
                        print(f"    ☀️ Turno diurno detectado")
                    else:
                        print(f"    🔍 Tipo de jornada: {tipo_jornada}")
                    
                    # Mostrar horas de entrada y salida
                    if resultado.get('entrada'):
                        print(f"    🟢 Entrada: {resultado['entrada'].timestamp}")
                    elif resultado.get('hora_entrada_estimada'):
                        print(f"    🟢 Entrada estimada: {resultado['hora_entrada_estimada']}")
                    
                    if resultado.get('salida'):
                        print(f"    🔴 Salida: {resultado['salida'].timestamp}")
                    elif resultado.get('hora_salida'):
                        print(f"    🔴 Salida: {resultado['hora_salida']}")
                else:
                    # Mostrar el mensaje de error o estado
                    mensaje = resultado.get('mensaje', resultado.get('observaciones', f"Estado: {resultado.get('estado', 'sin datos')}"))
                    print(f"    ⚪ {mensaje}")
            
            if datos_encontrados:
                print(f"\n  ✅ ¡EMPLEADO {empleado.nombre} CON DATOS PROCESADOS!")
                
                # Probar resumen para este empleado
                fecha_inicio = min(fechas_con_registros)
                fecha_fin = max(fechas_con_registros)
                
                print(f"  📊 Generando resumen: {fecha_inicio} al {fecha_fin}")
                resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
                
                print(f"    ⏰ Total horas trabajadas: {resumen['total_horas_trabajadas']:.2f}")
                print(f"    🕑 Total horas extras: {resumen['total_horas_extras']:.2f}")
                print(f"    💰 Costo total: ${resumen['costo_total_horas_extras']:.2f}")
                
                return True
            else:
                print(f"  ⚠️ No se pudieron procesar datos para {empleado.nombre}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def mostrar_registros_por_empleado():
    """Mostrar registros agrupados por empleado"""
    print("\n📊 REGISTROS POR EMPLEADO (ÚLTIMOS 3 DÍAS)")
    print("=" * 70)
    
    try:
        fecha_limite = datetime.now() - timedelta(days=3)
        
        # Obtener empleados con registros
        empleados_con_registros = UsuarioBiometrico.objects.filter(
            activo=True,
            registroasistencia__timestamp__gte=fecha_limite
        ).distinct()
        
        for empleado in empleados_con_registros:
            registros = RegistroAsistencia.objects.filter(
                user=empleado,
                timestamp__gte=fecha_limite
            ).order_by('timestamp')
            
            print(f"\n👤 {empleado.nombre} ({registros.count()} registros)")
            
            for registro in registros:
                tipo = "🟢 ENTRADA" if registro.status == 0 else "🔴 SALIDA"
                print(f"  {tipo} | {registro.timestamp}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🎯 PRUEBA ESPECÍFICA CON DATOS REALES")
    print("=" * 70)
    
    # Mostrar registros por empleado
    mostrar_registros_por_empleado()
    
    # Probar con empleados que tienen datos
    if test_empleado_con_datos():
        print("\n🎉 ¡SISTEMA DINÁMICO PROBADO CON DATOS REALES!")
        print("✅ El nuevo sistema funciona correctamente")
        print("📊 Los resúmenes mostrarán datos del biométrico")
    else:
        print("\n⚠️ No se pudo probar con datos reales")
        print("💡 Puede ser que los registros no tengan pares entrada-salida completos")
    
    print("=" * 70)
