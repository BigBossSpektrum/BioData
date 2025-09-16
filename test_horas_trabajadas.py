#!/usr/bin/env python
"""
Script de prueba para verificar que el cálculo de horas trabajadas
no cuenta el tiempo antes del horario estipulado de jornada.
"""

import os
import sys
import django
from datetime import datetime, time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from frontend.utils import calcular_horas_con_horarios_estandar

def test_no_contar_tiempo_antes_jornada():
    """Prueba que no se cuenta el tiempo antes del horario oficial"""
    
    print("=== Prueba: No contar tiempo antes del horario estipulado ===\n")
    
    # Caso 1: Empleado entra 30 minutos antes del turno mañana (06:30 vs 07:00)
    entrada_temprana = datetime(2024, 1, 15, 6, 30)  # 06:30
    salida_normal = datetime(2024, 1, 15, 14, 0)     # 14:00
    
    resultado = calcular_horas_con_horarios_estandar(entrada_temprana, salida_normal)
    
    print("Caso 1: Turno Mañana - Entrada temprana")
    print(f"  Entrada registrada: {entrada_temprana.strftime('%H:%M')}")
    print(f"  Salida registrada: {salida_normal.strftime('%H:%M')}")
    print(f"  Entrada efectiva: {resultado['entrada_efectiva'].strftime('%H:%M')}")
    print(f"  Horas trabajadas: {resultado['horas_trabajadas']}")
    print(f"  Horas normales: {resultado['horas_normales']}")
    print(f"  Mensaje: {resultado['mensaje']}")
    print(f"  Tipo turno: {resultado['tipo_turno']}")
    
    # Verificar que solo cuenta desde las 07:00
    assert resultado['horas_trabajadas'] == 7.0, f"Esperaba 7.0 horas, obtuvo {resultado['horas_trabajadas']}"
    assert resultado['entrada_efectiva'].time() == time(7, 0), "La entrada efectiva debe ser las 07:00"
    
    print("  ✅ Correcto: Solo cuenta desde las 07:00\n")
    
    # Caso 2: Empleado entra 1 hora antes del turno tarde (13:00 vs 14:00)
    entrada_temprana2 = datetime(2024, 1, 15, 13, 0)  # 13:00
    salida_normal2 = datetime(2024, 1, 15, 22, 0)     # 22:00
    
    resultado2 = calcular_horas_con_horarios_estandar(entrada_temprana2, salida_normal2)
    
    print("Caso 2: Turno Tarde - Entrada temprana")
    print(f"  Entrada registrada: {entrada_temprana2.strftime('%H:%M')}")
    print(f"  Salida registrada: {salida_normal2.strftime('%H:%M')}")
    print(f"  Entrada efectiva: {resultado2['entrada_efectiva'].strftime('%H:%M')}")
    print(f"  Horas trabajadas: {resultado2['horas_trabajadas']}")
    print(f"  Horas normales: {resultado2['horas_normales']}")
    print(f"  Mensaje: {resultado2['mensaje']}")
    print(f"  Tipo turno: {resultado2['tipo_turno']}")
    
    # Verificar que solo cuenta desde las 14:00
    assert resultado2['horas_trabajadas'] == 8.0, f"Esperaba 8.0 horas, obtuvo {resultado2['horas_trabajadas']}"
    assert resultado2['entrada_efectiva'].time() == time(14, 0), "La entrada efectiva debe ser las 14:00"
    
    print("  ✅ Correcto: Solo cuenta desde las 14:00\n")
    
    # Caso 3: Empleado entra exactamente a la hora correcta
    entrada_correcta = datetime(2024, 1, 15, 7, 0)   # 07:00
    salida_correcta = datetime(2024, 1, 15, 14, 0)   # 14:00
    
    resultado3 = calcular_horas_con_horarios_estandar(entrada_correcta, salida_correcta)
    
    print("Caso 3: Turno Mañana - Entrada exacta")
    print(f"  Entrada registrada: {entrada_correcta.strftime('%H:%M')}")
    print(f"  Salida registrada: {salida_correcta.strftime('%H:%M')}")
    print(f"  Entrada efectiva: {resultado3['entrada_efectiva'].strftime('%H:%M')}")
    print(f"  Horas trabajadas: {resultado3['horas_trabajadas']}")
    print(f"  Mensaje: {resultado3['mensaje']}")
    
    # Verificar que cuenta exactamente las 7 horas
    assert resultado3['horas_trabajadas'] == 7.0, f"Esperaba 7.0 horas, obtuvo {resultado3['horas_trabajadas']}"
    
    print("  ✅ Correcto: Cuenta exactamente las 7 horas\n")
    
    print("🎉 Todas las pruebas pasaron exitosamente!")
    print("✅ El sistema NO cuenta tiempo trabajado antes del horario estipulado")

if __name__ == "__main__":
    test_no_contar_tiempo_antes_jornada()
