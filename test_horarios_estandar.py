#!/usr/bin/env python
"""
Script de prueba para verificar el nuevo cálculo de horas con horarios estándar.
Este script prueba diferentes escenarios para asegurar que:
1. No se cuenta el tiempo antes de la hora oficial de entrada
2. Las 8 horas normales se calculan correctamente
3. Las horas extras se calculan solo después de las 8 horas normales o del fin del turno
"""

import os
import sys
import django
from datetime import datetime, time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from frontend.utils import calcular_horas_con_horarios_estandar

def probar_escenario(nombre, entrada_str, salida_str, esperado_horas=None, esperado_extras=None):
    """Probar un escenario específico"""
    print(f"\n🧪 {nombre}")
    print(f"   Entrada: {entrada_str}")
    print(f"   Salida: {salida_str}")
    
    # Convertir strings a datetime
    entrada = datetime.strptime(entrada_str, "%Y-%m-%d %H:%M")
    salida = datetime.strptime(salida_str, "%Y-%m-%d %H:%M")
    
    # Calcular con la nueva función
    resultado = calcular_horas_con_horarios_estandar(entrada, salida)
    
    print(f"   📊 Resultado:")
    print(f"      - Horas normales: {resultado['horas_normales']:.2f}")
    print(f"      - Horas extras: {resultado['horas_extras']:.2f}")
    print(f"      - Total trabajadas: {resultado['horas_trabajadas']:.2f}")
    print(f"      - Entrada efectiva: {resultado['entrada_efectiva'].strftime('%H:%M')}")
    print(f"      - Mensaje: {resultado['mensaje']}")
    
    # Verificar expectativas si se proporcionan
    if esperado_horas is not None:
        if abs(resultado['horas_trabajadas'] - esperado_horas) < 0.1:
            print(f"   ✅ Horas trabajadas correctas: {resultado['horas_trabajadas']:.2f}")
        else:
            print(f"   ❌ ERROR: Esperado {esperado_horas:.2f}, obtenido {resultado['horas_trabajadas']:.2f}")
    
    if esperado_extras is not None:
        if abs(resultado['horas_extras'] - esperado_extras) < 0.1:
            print(f"   ✅ Horas extras correctas: {resultado['horas_extras']:.2f}")
        else:
            print(f"   ❌ ERROR: Esperado {esperado_extras:.2f}, obtenido {resultado['horas_extras']:.2f}")

def main():
    """Ejecutar todas las pruebas"""
    print("=" * 70)
    print("🧪 PRUEBAS DEL NUEVO CÁLCULO DE HORAS CON HORARIOS ESTÁNDAR")
    print("=" * 70)
    
    # Caso 1: Empleado llega 1 hora antes - NO debe contar esa hora
    probar_escenario(
        "Caso 1: Llega 1 hora antes (06:00), sale normal (15:00)",
        "2024-09-15 06:00",  # Llega a las 6:00
        "2024-09-15 15:00",  # Sale a las 15:00 (9 horas después)
        esperado_horas=8.0,  # Solo debe contar 8 horas (desde las 07:00)
        esperado_extras=1.0   # 1 hora extra (15:00 - 14:00)
    )
    
    # Caso 2: Jornada normal exacta
    probar_escenario(
        "Caso 2: Jornada normal (07:00 - 14:00)",
        "2024-09-15 07:00",
        "2024-09-15 14:00",
        esperado_horas=7.0,   # 7 horas exactas
        esperado_extras=0.0
    )
    
    # Caso 3: Llega tarde, sale normal
    probar_escenario(
        "Caso 3: Llega tarde (08:00), sale normal (14:00)",
        "2024-09-15 08:00",
        "2024-09-15 14:00",
        esperado_horas=6.0,   # 6 horas trabajadas
        esperado_extras=0.0
    )
    
    # Caso 4: Turno tarde con llegada anticipada
    probar_escenario(
        "Caso 4: Turno tarde - llega 1 hora antes (13:00), sale tarde (23:00)",
        "2024-09-15 13:00",  # Llega 1 hora antes
        "2024-09-15 23:00",  # Sale 1 hora tarde
        esperado_horas=9.0,  # 8 normales + 1 extra
        esperado_extras=1.0
    )
    
    # Caso 5: Turno nocturno
    probar_escenario(
        "Caso 5: Turno nocturno - llega antes (21:00), sale normal (06:00)",
        "2024-09-15 21:00",  # Llega 1 hora antes
        "2024-09-16 06:00",  # Sale a las 6:00 del día siguiente
        esperado_horas=8.0,  # 8 horas normales (22:00 - 06:00)
        esperado_extras=0.0
    )
    
    # Caso 6: Turno nocturno con horas extras
    probar_escenario(
        "Caso 6: Turno nocturno con extras - llega antes (21:00), sale tarde (07:00)",
        "2024-09-15 21:00",  # Llega 1 hora antes
        "2024-09-16 07:00",  # Sale 1 hora tarde
        esperado_horas=9.0,  # 8 normales + 1 extra
        esperado_extras=1.0
    )
    
    # Caso 7: Jornada muy larga (más de 12 horas)
    probar_escenario(
        "Caso 7: Jornada larga - llega muy temprano (05:00), sale muy tarde (18:00)",
        "2024-09-15 05:00",  # Llega 2 horas antes
        "2024-09-15 18:00",  # Sale 4 horas tarde
        esperado_horas=11.0, # 7 normales + 4 extras (NO cuenta las 2 horas antes de las 07:00)
        esperado_extras=4.0
    )
    
    print("\n" + "=" * 70)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 70)
    print("📝 RESUMEN:")
    print("   - Las horas antes del horario oficial NO se cuentan")
    print("   - Máximo 8 horas normales por jornada estándar")
    print("   - Las horas extras se calculan después del fin oficial del turno")
    print("   - Se mantiene compatibilidad con turnos nocturnos")

if __name__ == "__main__":
    main()
