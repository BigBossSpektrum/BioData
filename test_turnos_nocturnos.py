#!/usr/bin/env python3
"""
Script de prueba para verificar la detección de turnos nocturnos con emparejamiento
"""

import os
import sys
import django
from datetime import datetime, time, date, timedelta
from collections import defaultdict

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from frontend.utils import detectar_tipo_turno_detallado, es_turno_nocturno, procesar_turno_nocturno_con_siguiente_registro
from API.models import UsuarioBiometrico, RegistroAsistencia
from django.utils.timezone import make_aware

class MockRegistro:
    """Registro simulado para pruebas"""
    def __init__(self, timestamp, usuario=None, estacion=None):
        self.timestamp = timestamp
        self.user = usuario
        self.estacion_servicio = estacion

class MockUsuario:
    """Usuario simulado para pruebas"""
    def __init__(self, id, nombre):
        self.id = id
        self.nombre = nombre

def test_emparejamiento_turno_nocturno():
    """Prueba la nueva funcionalidad de emparejamiento para turnos nocturnos"""
    
    print("=" * 80)
    print("PRUEBAS DE EMPAREJAMIENTO TURNOS NOCTURNOS")
    print("=" * 80)
    
    # Crear usuario simulado
    usuario = MockUsuario(1, "Juan Perez")
    
    # Caso 1: Entrada nocturna con salida al día siguiente
    print("\n1. Caso: Entrada nocturna con salida al día siguiente")
    print("-" * 50)
    
    fecha_entrada = date(2024, 1, 15)
    fecha_salida = date(2024, 1, 16)
    
    entrada_22_30 = make_aware(datetime.combine(fecha_entrada, time(22, 30)))
    salida_06_30 = make_aware(datetime.combine(fecha_salida, time(6, 30)))
    
    # Simular estructura de datos como en la vista
    asistencia_por_usuario_fecha = defaultdict(lambda: defaultdict(list))
    asistencia_por_usuario_fecha[usuario][fecha_entrada] = [
        MockRegistro(entrada_22_30, usuario)
    ]
    asistencia_por_usuario_fecha[usuario][fecha_salida] = [
        MockRegistro(salida_06_30, usuario)
    ]
    
    resultado = procesar_turno_nocturno_con_siguiente_registro(
        asistencia_por_usuario_fecha, usuario, fecha_entrada
    )
    
    if resultado:
        print(f"✅ Turno nocturno detectado correctamente")
        print(f"   - Entrada: {resultado['entrada'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   - Salida: {resultado['salida'].strftime('%Y-%m-%d %H:%M') if resultado['salida'] else 'No registrada'}")
        print(f"   - Horas trabajadas: {resultado['horas_trabajadas']:.2f}")
        print(f"   - Horas extra: {resultado['horas_extra']:.2f}")
        print(f"   - Mensaje: {resultado['mensaje']}")
    else:
        print("❌ No se detectó turno nocturno")
    
    # Caso 2: Entrada nocturna sin salida
    print("\n2. Caso: Entrada nocturna sin salida")
    print("-" * 50)
    
    fecha_solo_entrada = date(2024, 1, 17)
    entrada_21_45 = make_aware(datetime.combine(fecha_solo_entrada, time(21, 45)))
    
    asistencia_solo_entrada = defaultdict(lambda: defaultdict(list))
    asistencia_solo_entrada[usuario][fecha_solo_entrada] = [
        MockRegistro(entrada_21_45, usuario)
    ]
    
    resultado2 = procesar_turno_nocturno_con_siguiente_registro(
        asistencia_solo_entrada, usuario, fecha_solo_entrada
    )
    
    if resultado2:
        print(f"✅ Turno nocturno detectado (sin salida)")
        print(f"   - Entrada: {resultado2['entrada'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   - Salida: {resultado2['salida'].strftime('%Y-%m-%d %H:%M') if resultado2['salida'] else 'No registrada'}")
        print(f"   - Horas trabajadas: {resultado2['horas_trabajadas']:.2f}")
        print(f"   - Mensaje: {resultado2['mensaje']}")
    else:
        print("❌ No se detectó turno nocturno")
    
    # Caso 3: Turno con duración > 20 horas (debe rechazarse)
    print("\n3. Caso: Turno nocturno con duración > 20 horas (debe rechazarse)")
    print("-" * 50)
    
    fecha_largo = date(2024, 1, 19)
    fecha_largo_salida = date(2024, 1, 20)
    
    entrada_22_00 = make_aware(datetime.combine(fecha_largo, time(22, 0)))
    salida_20_00 = make_aware(datetime.combine(fecha_largo_salida, time(20, 0)))  # 22 horas después
    
    asistencia_larga = defaultdict(lambda: defaultdict(list))
    asistencia_larga[usuario][fecha_largo] = [
        MockRegistro(entrada_22_00, usuario)
    ]
    asistencia_larga[usuario][fecha_largo_salida] = [
        MockRegistro(salida_20_00, usuario)
    ]
    
    resultado_largo = procesar_turno_nocturno_con_siguiente_registro(
        asistencia_larga, usuario, fecha_largo
    )
    
    if resultado_largo:
        if resultado_largo['salida'] is None and "duración > 20h" in resultado_largo['mensaje']:
            print(f"✅ Correcto: Turno rechazado por exceder 20 horas")
            print(f"   - Entrada: {resultado_largo['entrada'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   - Salida: Rechazada (duración excesiva)")
            print(f"   - Horas trabajadas: {resultado_largo['horas_trabajadas']:.2f}")
            print(f"   - Mensaje: {resultado_largo['mensaje']}")
        else:
            print(f"❌ ERROR: Turno no fue rechazado correctamente")
            print(f"   - Entrada: {resultado_largo['entrada'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   - Salida: {resultado_largo['salida'].strftime('%Y-%m-%d %H:%M') if resultado_largo['salida'] else 'No registrada'}")
    else:
        print("✅ Correcto: No se detectó turno nocturno (rechazado)")
    
    # Caso 3.5: Turno de exactamente 20 horas (límite - debe aceptarse)
    print("\n3.5. Caso: Turno nocturno de exactamente 20 horas (límite - debe aceptarse)")
    print("-" * 50)
    
    fecha_limite = date(2024, 1, 21)
    fecha_limite_salida = date(2024, 1, 22)
    
    entrada_22_00_limite = make_aware(datetime.combine(fecha_limite, time(22, 0)))
    salida_18_00_limite = make_aware(datetime.combine(fecha_limite_salida, time(18, 0)))  # Exactamente 20 horas después
    
    asistencia_limite = defaultdict(lambda: defaultdict(list))
    asistencia_limite[usuario][fecha_limite] = [
        MockRegistro(entrada_22_00_limite, usuario)
    ]
    asistencia_limite[usuario][fecha_limite_salida] = [
        MockRegistro(salida_18_00_limite, usuario)
    ]
    
    resultado_limite = procesar_turno_nocturno_con_siguiente_registro(
        asistencia_limite, usuario, fecha_limite
    )
    
    if resultado_limite and resultado_limite['salida']:
        print(f"✅ Correcto: Turno de 20h aceptado (en el límite)")
        print(f"   - Entrada: {resultado_limite['entrada'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   - Salida: {resultado_limite['salida'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   - Horas trabajadas: {resultado_limite['horas_trabajadas']:.2f}")
        print(f"   - Mensaje: {resultado_limite['mensaje']}")
    else:
        print(f"❌ ERROR: Turno de 20h fue rechazado incorrectamente")
    
    # Caso 4: Turno diurno (no debe detectar)
    print("\n4. Caso: Turno diurno (no debe detectar como nocturno)")
    print("-" * 50)
    
    fecha_diurno = date(2024, 1, 18)
    entrada_07_30 = make_aware(datetime.combine(fecha_diurno, time(7, 30)))
    
    asistencia_diurno = defaultdict(lambda: defaultdict(list))
    asistencia_diurno[usuario][fecha_diurno] = [
        MockRegistro(entrada_07_30, usuario)
    ]
    
    resultado3 = procesar_turno_nocturno_con_siguiente_registro(
        asistencia_diurno, usuario, fecha_diurno
    )
    
    if resultado3:
        print(f"❌ ERROR: Se detectó incorrectamente como turno nocturno")
        print(f"   - Entrada: {resultado3['entrada'].strftime('%Y-%m-%d %H:%M')}")
    else:
        print("✅ Correcto: No se detectó como turno nocturno")
    
    # Caso 5: Verificación de función de detección básica
    print("\n5. Verificación de función detectar_tipo_turno_detallado")
    print("-" * 50)
    
    casos_deteccion = [
        (datetime(2024, 1, 15, 21, 59), None, True),  # Entrada nocturna sin salida
        (datetime(2024, 1, 15, 22, 30), datetime(2024, 1, 16, 6, 30), True),  # Turno nocturno completo
        (datetime(2024, 1, 15, 7, 30), datetime(2024, 1, 15, 15, 30), False),  # Turno diurno
        (datetime(2024, 1, 15, 13, 57), None, False),  # Entrada tarde
    ]
    
    for entrada, salida, esperado in casos_deteccion:
        resultado = detectar_tipo_turno_detallado(entrada, salida)
        estado = "✅" if resultado['es_nocturno'] == esperado else "❌"
        print(f"   {estado} {entrada.strftime('%H:%M')} → {salida.strftime('%H:%M') if salida else 'Sin salida'} = {resultado['es_nocturno']} (esperado: {esperado})")

if __name__ == '__main__':
    test_emparejamiento_turno_nocturno()
