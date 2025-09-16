#!/usr/bin/env python
"""
Script de prueba adicional para verificar el cálculo de horas en turnos nocturnos
"""

import os
import sys
import django
from datetime import datetime, time, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from frontend.utils import calcular_horas_con_horarios_estandar

def test_turnos_nocturnos():
    """Prueba específica para turnos nocturnos"""
    
    print("=== Prueba: Turnos Nocturnos - No contar tiempo antes del horario estipulado ===\n")
    
    # Caso 1: Empleado entra temprano al turno nocturno (21:00 vs 22:00)
    entrada_temprana = datetime(2024, 1, 15, 21, 0)  # 21:00
    salida_normal = datetime(2024, 1, 16, 6, 0)      # 06:00 del día siguiente
    
    resultado = calcular_horas_con_horarios_estandar(entrada_temprana, salida_normal)
    
    print("Caso 1: Turno Nocturno - Entrada temprana")
    print(f"  Entrada registrada: {entrada_temprana.strftime('%d/%m/%Y %H:%M')}")
    print(f"  Salida registrada: {salida_normal.strftime('%d/%m/%Y %H:%M')}")
    print(f"  Entrada efectiva: {resultado['entrada_efectiva'].strftime('%d/%m/%Y %H:%M')}")
    print(f"  Horas trabajadas: {resultado['horas_trabajadas']}")
    print(f"  Horas normales: {resultado['horas_normales']}")
    print(f"  Mensaje: {resultado['mensaje']}")
    print(f"  Tipo turno: {resultado['tipo_turno']}")
    
    # Verificar que solo cuenta desde las 22:00
    assert resultado['horas_trabajadas'] == 8.0, f"Esperaba 8.0 horas, obtuvo {resultado['horas_trabajadas']}"
    assert resultado['entrada_efectiva'].time() == time(22, 0), "La entrada efectiva debe ser las 22:00"
    
    print("  ✅ Correcto: Solo cuenta desde las 22:00\n")
    
    # Caso 2: Empleado trabaja horas extras en turno nocturno
    entrada_normal = datetime(2024, 1, 15, 22, 0)   # 22:00
    salida_extra = datetime(2024, 1, 16, 8, 0)      # 08:00 del día siguiente (2 horas extra)
    
    resultado2 = calcular_horas_con_horarios_estandar(entrada_normal, salida_extra)
    
    print("Caso 2: Turno Nocturno - Con horas extras")
    print(f"  Entrada registrada: {entrada_normal.strftime('%d/%m/%Y %H:%M')}")
    print(f"  Salida registrada: {salida_extra.strftime('%d/%m/%Y %H:%M')}")
    print(f"  Horas trabajadas: {resultado2['horas_trabajadas']}")
    print(f"  Horas normales: {resultado2['horas_normales']}")
    print(f"  Horas extras: {resultado2['horas_extras']}")
    print(f"  Mensaje: {resultado2['mensaje']}")
    
    # Verificar cálculo correcto de horas normales y extras
    assert resultado2['horas_normales'] == 8.0, f"Esperaba 8.0 horas normales, obtuvo {resultado2['horas_normales']}"
    assert resultado2['horas_extras'] == 2.0, f"Esperaba 2.0 horas extras, obtuvo {resultado2['horas_extras']}"
    assert resultado2['horas_trabajadas'] == 10.0, f"Esperaba 10.0 horas totales, obtuvo {resultado2['horas_trabajadas']}"
    
    print("  ✅ Correcto: 8h normales + 2h extras = 10h totales\n")
    
    print("🎉 Pruebas de turnos nocturnos pasaron exitosamente!")

def test_comparacion_antes_y_despues():
    """Compara el comportamiento antes y después de la mejora"""
    
    print("=== Comparación: Antes vs Después de la mejora ===\n")
    
    # Simular cálculo "antiguo" (tiempo total sin restricciones)
    entrada_temprana = datetime(2024, 1, 15, 6, 0)   # 06:00 (1 hora antes)
    salida_normal = datetime(2024, 1, 15, 14, 0)     # 14:00
    
    # Cálculo antiguo (total de tiempo)
    tiempo_total = salida_normal - entrada_temprana
    horas_antiguo = tiempo_total.total_seconds() / 3600
    
    # Cálculo nuevo (con horarios estipulados)
    resultado_nuevo = calcular_horas_con_horarios_estandar(entrada_temprana, salida_normal)
    
    print("Empleado entra 1 hora antes de su horario:")
    print(f"  Entrada: {entrada_temprana.strftime('%H:%M')}")
    print(f"  Salida: {salida_normal.strftime('%H:%M')}")
    print(f"  Cálculo ANTIGUO: {horas_antiguo} horas (cuenta todo el tiempo)")
    print(f"  Cálculo NUEVO: {resultado_nuevo['horas_trabajadas']} horas (solo desde horario oficial)")
    print(f"  Diferencia: {horas_antiguo - resultado_nuevo['horas_trabajadas']} horas NO contabilizadas")
    print(f"  Mensaje: {resultado_nuevo['mensaje']}")
    
    print("\n✅ La mejora evita que se paguen horas no autorizadas")

if __name__ == "__main__":
    test_turnos_nocturnos()
    print()
    test_comparacion_antes_y_despues()
