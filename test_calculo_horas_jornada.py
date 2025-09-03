#!/usr/bin/env python3
"""
Script de prueba para verificar el nuevo cálculo de horas trabajadas
que respeta los horarios de jornada laboral.
"""

import os
import sys
import django
from datetime import datetime, time, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import JornadaLaboral


def test_calculo_horas_jornada():
    """
    Prueba el cálculo de horas trabajadas con las nuevas reglas:
    - Solo se cuenta el tiempo dentro de la jornada laboral
    - Si llega 1 hora antes, esa hora no se contabiliza
    """
    
    print("=== PRUEBAS DE CÁLCULO DE HORAS TRABAJADAS ===\n")
    
    # Crear jornadas de prueba
    jornadas = {
        'manana': JornadaLaboral(
            nombre='Mañana',
            tipo_jornada='manana',
            hora_inicio=time(6, 0),
            hora_fin=time(14, 0),
            horas_normales=8.00,
            es_nocturno=False
        ),
        'tarde': JornadaLaboral(
            nombre='Tarde',
            tipo_jornada='tarde',
            hora_inicio=time(14, 0),
            hora_fin=time(22, 0),
            horas_normales=8.00,
            es_nocturno=False
        ),
        'nocturno': JornadaLaboral(
            nombre='Nocturno',
            tipo_jornada='nocturno',
            hora_inicio=time(22, 0),
            hora_fin=time(6, 0),
            horas_normales=8.00,
            es_nocturno=True
        )
    }
    
    # Casos de prueba para jornada de MAÑANA (06:00 - 14:00)
    print("1. JORNADA DE MAÑANA (06:00 - 14:00)")
    print("-" * 40)
    
    casos_manana = [
        {
            'descripcion': 'Llega 1 hora antes (05:00) y sale a tiempo (14:00)',
            'entrada': datetime(2024, 1, 15, 5, 0),
            'salida': datetime(2024, 1, 15, 14, 0),
            'esperado': 8.0  # Solo 06:00-14:00 = 8 horas
        },
        {
            'descripcion': 'Llega a tiempo (06:00) y sale a tiempo (14:00)',
            'entrada': datetime(2024, 1, 15, 6, 0),
            'salida': datetime(2024, 1, 15, 14, 0),
            'esperado': 8.0  # 06:00-14:00 = 8 horas
        },
        {
            'descripcion': 'Llega tarde (07:30) y sale a tiempo (14:00)',
            'entrada': datetime(2024, 1, 15, 7, 30),
            'salida': datetime(2024, 1, 15, 14, 0),
            'esperado': 6.5  # 07:30-14:00 = 6.5 horas
        },
        {
            'descripcion': 'Llega a tiempo (06:00) pero sale 1 hora después (15:00)',
            'entrada': datetime(2024, 1, 15, 6, 0),
            'salida': datetime(2024, 1, 15, 15, 0),
            'esperado': 8.0  # Solo 06:00-14:00 = 8 horas (hora extra no cuenta)
        }
    ]
    
    for caso in casos_manana:
        resultado = jornadas['manana'].calcular_horas_trabajadas(caso['entrada'], caso['salida'])
        status = "✓" if resultado == caso['esperado'] else "✗"
        print(f"{status} {caso['descripcion']}")
        print(f"   Resultado: {resultado} horas | Esperado: {caso['esperado']} horas")
        if resultado != caso['esperado']:
            print(f"   ¡ERROR! Se esperaba {caso['esperado']} pero se obtuvo {resultado}")
        print()
    
    # Casos de prueba para jornada de TARDE (14:00 - 22:00)
    print("2. JORNADA DE TARDE (14:00 - 22:00)")
    print("-" * 40)
    
    casos_tarde = [
        {
            'descripcion': 'Llega 1 hora antes (13:00) y sale a tiempo (22:00)',
            'entrada': datetime(2024, 1, 15, 13, 0),
            'salida': datetime(2024, 1, 15, 22, 0),
            'esperado': 8.0  # Solo 14:00-22:00 = 8 horas
        },
        {
            'descripcion': 'Llega a tiempo (14:00) y sale a tiempo (22:00)',
            'entrada': datetime(2024, 1, 15, 14, 0),
            'salida': datetime(2024, 1, 15, 22, 0),
            'esperado': 8.0  # 14:00-22:00 = 8 horas
        },
        {
            'descripcion': 'Llega tarde (15:30) y sale tarde (23:00)',
            'entrada': datetime(2024, 1, 15, 15, 30),
            'salida': datetime(2024, 1, 15, 23, 0),
            'esperado': 6.5  # Solo 15:30-22:00 = 6.5 horas
        }
    ]
    
    for caso in casos_tarde:
        resultado = jornadas['tarde'].calcular_horas_trabajadas(caso['entrada'], caso['salida'])
        status = "✓" if resultado == caso['esperado'] else "✗"
        print(f"{status} {caso['descripcion']}")
        print(f"   Resultado: {resultado} horas | Esperado: {caso['esperado']} horas")
        if resultado != caso['esperado']:
            print(f"   ¡ERROR! Se esperaba {caso['esperado']} pero se obtuvo {resultado}")
        print()
    
    # Casos de prueba para jornada NOCTURNA (22:00 - 06:00)
    print("3. JORNADA NOCTURNA (22:00 - 06:00)")
    print("-" * 40)
    
    casos_nocturno = [
        {
            'descripcion': 'Llega 1 hora antes (21:00) y sale a tiempo (06:00)',
            'entrada': datetime(2024, 1, 15, 21, 0),
            'salida': datetime(2024, 1, 16, 6, 0),
            'esperado': 8.0  # Solo 22:00-06:00 = 8 horas
        },
        {
            'descripcion': 'Llega a tiempo (22:00) y sale a tiempo (06:00)',
            'entrada': datetime(2024, 1, 15, 22, 0),
            'salida': datetime(2024, 1, 16, 6, 0),
            'esperado': 8.0  # 22:00-06:00 = 8 horas
        },
        {
            'descripcion': 'Llega tarde (23:30) y sale a tiempo (06:00)',
            'entrada': datetime(2024, 1, 15, 23, 30),
            'salida': datetime(2024, 1, 16, 6, 0),
            'esperado': 6.5  # 23:30-06:00 = 6.5 horas
        },
        {
            'descripcion': 'Llega a tiempo (22:00) pero sale 1 hora después (07:00)',
            'entrada': datetime(2024, 1, 15, 22, 0),
            'salida': datetime(2024, 1, 16, 7, 0),
            'esperado': 8.0  # Solo 22:00-06:00 = 8 horas
        }
    ]
    
    for caso in casos_nocturno:
        resultado = jornadas['nocturno'].calcular_horas_trabajadas(caso['entrada'], caso['salida'])
        status = "✓" if resultado == caso['esperado'] else "✗"
        print(f"{status} {caso['descripcion']}")
        print(f"   Resultado: {resultado} horas | Esperado: {caso['esperado']} horas")
        if resultado != caso['esperado']:
            print(f"   ¡ERROR! Se esperaba {caso['esperado']} pero se obtuvo {resultado}")
        print()
    
    print("=== FIN DE PRUEBAS ===")


if __name__ == '__main__':
    test_calculo_horas_jornada()
