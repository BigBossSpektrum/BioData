#!/usr/bin/env python3
"""
Script de prueba para verificar el caso específico de Ramiro:
- Jornada de mañana (06:00 - 14:00)
- Entrada: 05:53 (7 min antes)
- Salida: 18:05 (4:05 después)
- Debe calcular: 8 horas normales + 4:05 horas extras = 12:05 total
"""

import os
import sys
import django
from datetime import datetime, time, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import JornadaLaboral, UsuarioBiometrico, RegistroAsistencia
from django.utils import timezone


def test_caso_ramiro():
    """
    Prueba el caso específico de Ramiro
    """
    
    print("=== PRUEBA CASO ESPECÍFICO: RAMIRO ===\n")
    
    # Crear jornada de mañana
    jornada_manana = JornadaLaboral(
        nombre='Mañana',
        tipo_jornada='manana',
        hora_inicio=time(6, 0),    # 06:00
        hora_fin=time(14, 0),      # 14:00
        horas_normales=8.00,
        es_nocturno=False
    )
    
    # Caso de Ramiro
    entrada = datetime(2025, 8, 31, 5, 53)  # 05:53 (7 min antes)
    salida = datetime(2025, 8, 31, 18, 5)   # 18:05 (4:05 después)
    
    print("📊 DATOS DEL CASO:")
    print(f"   Jornada: {jornada_manana.hora_inicio} - {jornada_manana.hora_fin}")
    print(f"   Entrada real: {entrada.strftime('%H:%M')}")
    print(f"   Salida real: {salida.strftime('%H:%M')}")
    print()
    
    # Calcular con método original
    horas_totales_original = jornada_manana.calcular_horas_trabajadas(entrada, salida)
    horas_extras_original = jornada_manana.calcular_horas_extras(horas_totales_original)
    
    print("🔍 CÁLCULO CON MÉTODO ACTUAL:")
    print(f"   Horas totales calculadas: {horas_totales_original}")
    print(f"   Horas extras calculadas: {horas_extras_original}")
    print()
    
    # Calcular con nuevo método detallado
    detalle = jornada_manana.calcular_horas_normales_y_extras(entrada, salida)
    
    print("🆕 CÁLCULO CON NUEVO MÉTODO DETALLADO:")
    print(f"   Horas normales: {detalle['horas_normales']}")
    print(f"   Horas extras: {detalle['horas_extras']}")
    print(f"   Horas totales: {detalle['horas_totales']}")
    print()
    
    # Verificar resultados esperados
    print("✅ VERIFICACIÓN DE RESULTADOS:")
    
    # Esperado:
    # - Entrada efectiva: 06:00 (no cuenta los 7 min antes)
    # - Horas normales: 06:00 a 14:00 = 8 horas
    # - Horas extras: 14:00 a 18:05 = 4 horas 5 min = 4.083 horas
    # - Total: 8 + 4.083 = 12.083 horas
    
    esperado_normales = 8.0
    esperado_extras = round((4 * 60 + 5) / 60, 2)  # 4 horas 5 min = 4.08 horas
    esperado_total = esperado_normales + esperado_extras
    
    print(f"   Horas normales esperadas: {esperado_normales}")
    print(f"   Horas extras esperadas: {esperado_extras}")
    print(f"   Total esperado: {esperado_total}")
    print()
    
    # Validar
    print("🎯 VALIDACIÓN:")
    
    normales_ok = abs(detalle['horas_normales'] - esperado_normales) < 0.01
    extras_ok = abs(detalle['horas_extras'] - esperado_extras) < 0.01
    total_ok = abs(detalle['horas_totales'] - esperado_total) < 0.01
    
    print(f"   ✅ Horas normales: {'CORRECTO' if normales_ok else 'ERROR'}")
    print(f"   ✅ Horas extras: {'CORRECTO' if extras_ok else 'ERROR'}")
    print(f"   ✅ Total: {'CORRECTO' if total_ok else 'ERROR'}")
    
    if normales_ok and extras_ok and total_ok:
        print("\n🎉 ¡TODAS LAS VALIDACIONES PASARON!")
        print("   El cálculo es correcto para el caso de Ramiro.")
    else:
        print("\n❌ ALGUNAS VALIDACIONES FALLARON")
        print("   Revisar la lógica de cálculo.")
    
    print("\n" + "="*50)


def test_sistema_completo_ramiro():
    """
    Prueba el sistema completo con un usuario simulado como Ramiro
    """
    print("\n=== PRUEBA SISTEMA COMPLETO - RAMIRO ===\n")
    
    # Crear usuario simulado
    usuario_ramiro = UsuarioBiometrico(
        nombre="RAMIRO DE JESUS AMADO",
        cedula="12345678",
        turno=JornadaLaboral(
            nombre='Mañana',
            tipo_jornada='manana',
            hora_inicio=time(6, 0),
            hora_fin=time(14, 0),
            horas_normales=8.00,
            es_nocturno=False
        )
    )
    
    # Fecha del caso
    fecha_caso = datetime(2025, 8, 31).date()
    
    print("👤 USUARIO SIMULADO:")
    print(f"   Nombre: {usuario_ramiro.nombre}")
    print(f"   Jornada: {usuario_ramiro.turno.hora_inicio} - {usuario_ramiro.turno.hora_fin}")
    print(f"   Fecha: {fecha_caso}")
    print()
    
    # Simular registros de entrada y salida
    entrada_timestamp = timezone.make_aware(datetime(2025, 8, 31, 5, 53))
    salida_timestamp = timezone.make_aware(datetime(2025, 8, 31, 18, 5))
    
    # Crear registros simulados temporalmente (sin guardar en BD)
    entrada_registro = type('RegistroAsistencia', (), {
        'timestamp': entrada_timestamp,
        'status': 0
    })()
    
    salida_registro = type('RegistroAsistencia', (), {
        'timestamp': salida_timestamp,
        'status': 1
    })()
    
    print("📝 REGISTROS SIMULADOS:")
    print(f"   Entrada: {entrada_timestamp.strftime('%H:%M')}")
    print(f"   Salida: {salida_timestamp.strftime('%H:%M')}")
    print()
    
    # Calcular usando el método detallado de la jornada
    detalle = usuario_ramiro.turno.calcular_horas_normales_y_extras(
        entrada_timestamp, salida_timestamp
    )
    
    print("📊 RESULTADO DEL CÁLCULO:")
    print(f"   🕘 Horas normales: {detalle['horas_normales']} ({detalle['horas_normales']*60:.0f} min)")
    print(f"   ⏰ Horas extras: {detalle['horas_extras']} ({detalle['horas_extras']*60:.0f} min)")
    print(f"   📈 Total: {detalle['horas_totales']} ({detalle['horas_totales']*60:.0f} min)")
    print()
    
    print("🧮 DESGLOSE DETALLADO:")
    print(f"   • Entrada real: 05:53")
    print(f"   • Inicio jornada: 06:00 (no cuenta los 7 min antes)")
    print(f"   • Fin jornada: 14:00")
    print(f"   • Salida real: 18:05")
    print()
    print(f"   📊 Horas normales: 06:00 → 14:00 = 8 horas")
    print(f"   📊 Horas extras: 14:00 → 18:05 = 4 horas 5 min = {detalle['horas_extras']} horas")
    print()
    
    # Verificar que coincide con lo que debería mostrar el reporte
    if detalle['horas_normales'] == 8.0 and abs(detalle['horas_extras'] - 4.08) < 0.01:
        print("✅ RESULTADO CORRECTO:")
        print(f"   ✓ El sistema debe mostrar: 8 horas normales + 4:05 horas extras")
        print(f"   ✓ Total trabajado: {detalle['horas_totales']} horas")
        print(f"   ✓ Coincide con el caso real de Ramiro")
    else:
        print("❌ RESULTADO INCORRECTO:")
        print(f"   ✗ Se esperaba: 8 normales + 4.08 extras")
        print(f"   ✗ Se obtuvo: {detalle['horas_normales']} normales + {detalle['horas_extras']} extras")


def test_casos_adicionales():
    """
    Prueba casos adicionales para asegurar que la lógica funciona bien
    """
    print("\n=== PRUEBAS ADICIONALES ===\n")
    
    jornada_manana = JornadaLaboral(
        nombre='Mañana',
        tipo_jornada='manana',
        hora_inicio=time(6, 0),
        hora_fin=time(14, 0),
        horas_normales=8.00,
        es_nocturno=False
    )
    
    casos = [
        {
            'descripcion': 'Llega temprano, sale a tiempo',
            'entrada': datetime(2025, 8, 31, 5, 30),
            'salida': datetime(2025, 8, 31, 14, 0),
            'esperado_normales': 8.0,
            'esperado_extras': 0.0
        },
        {
            'descripcion': 'Llega a tiempo, sale 2 horas tarde',
            'entrada': datetime(2025, 8, 31, 6, 0),
            'salida': datetime(2025, 8, 31, 16, 0),
            'esperado_normales': 8.0,
            'esperado_extras': 2.0
        },
        {
            'descripcion': 'Llega tarde, sale muy tarde',
            'entrada': datetime(2025, 8, 31, 8, 0),
            'salida': datetime(2025, 8, 31, 17, 30),
            'esperado_normales': 6.0,  # 08:00 a 14:00
            'esperado_extras': 3.5     # 14:00 a 17:30
        }
    ]
    
    for i, caso in enumerate(casos, 1):
        print(f"{i}. {caso['descripcion']}")
        
        detalle = jornada_manana.calcular_horas_normales_y_extras(
            caso['entrada'], caso['salida']
        )
        
        normales_ok = abs(detalle['horas_normales'] - caso['esperado_normales']) < 0.01
        extras_ok = abs(detalle['horas_extras'] - caso['esperado_extras']) < 0.01
        
        status_n = "✅" if normales_ok else "❌"
        status_e = "✅" if extras_ok else "❌"
        
        print(f"   {status_n} Normales: {detalle['horas_normales']} (esperado: {caso['esperado_normales']})")
        print(f"   {status_e} Extras: {detalle['horas_extras']} (esperado: {caso['esperado_extras']})")
        print(f"   📊 Total: {detalle['horas_totales']}")
        print()


if __name__ == '__main__':
    test_caso_ramiro()
    test_sistema_completo_ramiro()
    test_casos_adicionales()
