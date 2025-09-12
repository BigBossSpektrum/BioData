#!/usr/bin/env python
"""
Script de prueba para verificar la funcionalidad de exportación a Excel
con horas de retraso y resumen total.
"""

from datetime import datetime

def calcular_horas_retraso(entrada_str, tipo_turno):
    """Calcula las horas de retraso basado en la entrada y tipo de turno"""
    if not entrada_str:
        return ""
    
    try:
        hora_entrada = datetime.strptime(entrada_str, '%H:%M').time()
        minutos_entrada = hora_entrada.hour * 60 + hora_entrada.minute
        
        # Horarios estándar con margen de 1 hora
        horarios = {
            'Turno 1 (7:00-14:00)': {'estandar': 420, 'inicio': 360, 'fin': 780},  # 7:00, margen 6:00-13:00
            'Turno 2 (14:00-22:00)': {'estandar': 840, 'inicio': 780, 'fin': 1260},  # 14:00, margen 13:00-21:00  
            'Turno 3 (22:00-07:00)': {'estandar': 1320, 'inicio': 1260, 'fin': 360}   # 22:00, margen 21:00-06:00
        }
        
        # Determinar turno correcto basado en hora de entrada
        turno_detectado = None
        if 0 <= minutos_entrada < 360:  # 00:00-06:00 - Turno mañana (no nocturno)
            turno_detectado = 'Turno 1 (7:00-14:00)'
        elif 360 <= minutos_entrada < 780:  # 06:00-13:00
            turno_detectado = 'Turno 1 (7:00-14:00)'
        elif 780 <= minutos_entrada < 1260:  # 13:00-21:00
            turno_detectado = 'Turno 2 (14:00-22:00)'
        elif 1260 <= minutos_entrada <= 1440:  # 21:00-23:59
            turno_detectado = 'Turno 3 (22:00-07:00)'
        
        if not turno_detectado:
            return ""
            
        hora_estandar = horarios[turno_detectado]['estandar']
        
        # Calcular retraso
        if turno_detectado == 'Turno 3 (22:00-07:00)' and minutos_entrada < 360:
            # Entrada nocturna del día siguiente
            retraso = (minutos_entrada + 1440) - hora_estandar
        else:
            retraso = minutos_entrada - hora_estandar
        
        if retraso > 0:
            horas_retraso = retraso // 60
            minutos_retraso = retraso % 60
            
            if horas_retraso > 0 and minutos_retraso > 0:
                return f"{horas_retraso}h {minutos_retraso}m"
            elif horas_retraso > 0:
                return f"{horas_retraso}h"
            else:
                return f"{minutos_retraso}m"
        else:
            return "A tiempo"
            
    except Exception as e:
        print(f"Error calculando retraso para {entrada_str}: {e}")
        return ""

def minutos_a_hhmm(minutos):
    """Convierte minutos a formato HH:MM"""
    if minutos == 0:
        return "00:00"
    horas = minutos // 60
    mins = minutos % 60
    return f"{horas:02d}:{mins:02d}"

def test_calcular_retrasos():
    """Prueba la función de calcular horas de retraso"""
    print("=== PRUEBAS DE CÁLCULO DE RETRASOS ===")
    
    casos_prueba = [
        ("07:00", "Turno 1 (7:00-14:00)", "A tiempo"),  # Hora exacta
        ("07:30", "Turno 1 (7:00-14:00)", "30m"),       # 30 min tarde
        ("08:15", "Turno 1 (7:00-14:00)", "1h 15m"),    # 1h 15m tarde
        ("06:45", "Turno 1 (7:00-14:00)", "A tiempo"),  # 15 min antes
        ("14:00", "Turno 2 (14:00-22:00)", "A tiempo"), # Hora exacta turno 2
        ("14:45", "Turno 2 (14:00-22:00)", "45m"),      # 45 min tarde turno 2
        ("22:00", "Turno 3 (22:00-07:00)", "A tiempo"), # Hora exacta turno 3
        ("22:30", "Turno 3 (22:00-07:00)", "30m"),      # 30 min tarde turno 3
        ("02:00", "Turno 1 (7:00-14:00)", "A tiempo"),  # Madrugada - asignado a turno 1
        ("05:30", "Turno 1 (7:00-14:00)", "A tiempo"),  # Madrugada - asignado a turno 1
        ("21:59", "Turno 3 (22:00-07:00)", "A tiempo"), # 1 min antes nocturno
        ("13:57", "Turno 2 (14:00-22:00)", "A tiempo"), # 3 min antes turno 2
    ]
    
    for entrada, turno_esperado, retraso_esperado in casos_prueba:
        resultado = calcular_horas_retraso(entrada, turno_esperado)
        status = "✅" if resultado == retraso_esperado else "❌"
        print(f"{status} {entrada} -> {resultado} (esperado: {retraso_esperado})")
    
    print("\n=== PRUEBAS DE CONVERSIÓN DE MINUTOS ===")
    casos_minutos = [
        (0, "00:00"),
        (30, "00:30"),
        (60, "01:00"),
        (90, "01:30"),
        (480, "08:00"),
        (525, "08:45"),
    ]
    
    for minutos, esperado in casos_minutos:
        resultado = minutos_a_hhmm(minutos)
        status = "✅" if resultado == esperado else "❌"
        print(f"{status} {minutos} min -> {resultado} (esperado: {esperado})")

def test_resumen_datos():
    """Prueba el cálculo del resumen con datos simulados"""
    print("\n=== PRUEBA DE RESUMEN TOTAL ===")
    
    # Datos simulados
    registros_simulados = [
        {"entrada": "07:30", "horas_trabajadas": "08:00", "horas_extra": "", "aprobado": ""},
        {"entrada": "14:45", "horas_trabajadas": "08:30", "horas_extra": "00:30", "aprobado": "Aprobado"},
        {"entrada": "22:30", "horas_trabajadas": "08:15", "horas_extra": "00:15", "aprobado": "Pendiente"},
        {"entrada": "06:45", "horas_trabajadas": "08:45", "horas_extra": "00:45", "aprobado": "Rechazado"},
        {"entrada": "08:15", "horas_trabajadas": "07:30", "horas_extra": "", "aprobado": ""},
    ]
    
    total_registros = len(registros_simulados)
    total_minutos_trabajados = 0
    total_minutos_extras = 0
    total_minutos_extras_aprobadas = 0
    contador_aprobadas = 0
    contador_rechazadas = 0
    contador_pendientes = 0
    contador_sin_retraso = 0
    contador_retraso_leve = 0
    contador_retraso_moderado = 0
    contador_retraso_grave = 0
    
    for registro in registros_simulados:
        # Calcular horas de retraso
        horas_retraso = calcular_horas_retraso(registro['entrada'], "")
        
        # Contabilizar tipos de retraso
        if horas_retraso == "A tiempo":
            contador_sin_retraso += 1
        elif horas_retraso and horas_retraso != "":
            # Extraer minutos del retraso para clasificar
            retraso_minutos = 0
            if 'h' in horas_retraso and 'm' in horas_retraso:
                partes = horas_retraso.replace('h', '').replace('m', '').split()
                if len(partes) == 2:
                    retraso_minutos = int(partes[0]) * 60 + int(partes[1])
            elif 'h' in horas_retraso:
                retraso_minutos = int(horas_retraso.replace('h', '')) * 60
            elif 'm' in horas_retraso:
                retraso_minutos = int(horas_retraso.replace('m', ''))
            
            if retraso_minutos >= 60:
                contador_retraso_grave += 1
            elif retraso_minutos >= 30:
                contador_retraso_moderado += 1
            elif retraso_minutos >= 1:
                contador_retraso_leve += 1
        
        # Calcular totales para resumen
        if registro['horas_trabajadas']:
            try:
                partes = registro['horas_trabajadas'].split(':')
                if len(partes) == 2:
                    total_minutos_trabajados += int(partes[0]) * 60 + int(partes[1])
            except:
                pass

        if registro['horas_extra']:
            try:
                partes = registro['horas_extra'].split(':')
                if len(partes) == 2:
                    minutos_extras = int(partes[0]) * 60 + int(partes[1])
                    total_minutos_extras += minutos_extras
                    
                    # Contabilizar por estado de aprobación
                    if registro['aprobado'] == 'Aprobado':
                        total_minutos_extras_aprobadas += minutos_extras
                        contador_aprobadas += 1
                    elif registro['aprobado'] == 'Rechazado':
                        contador_rechazadas += 1
                    elif registro['aprobado'] == 'Pendiente':
                        contador_pendientes += 1
            except:
                pass
    
    # Mostrar resumen
    print(f"Total de Registros: {total_registros}")
    print(f"Total Horas Trabajadas: {minutos_a_hhmm(total_minutos_trabajados)}")
    print(f"Total Horas Extras: {minutos_a_hhmm(total_minutos_extras)}")
    print(f"Horas Extras Aprobadas: {minutos_a_hhmm(total_minutos_extras_aprobadas)}")
    print(f"\nESTADO DE HORAS EXTRAS:")
    print(f"Aprobadas: {contador_aprobadas}")
    print(f"Rechazadas: {contador_rechazadas}")
    print(f"Pendientes: {contador_pendientes}")
    print(f"\nRESUMEN DE RETRASOS:")
    print(f"Sin Retraso: {contador_sin_retraso}")
    print(f"Retraso Leve (1-29 min): {contador_retraso_leve}")
    print(f"Retraso Moderado (30-59 min): {contador_retraso_moderado}")
    print(f"Retraso Grave (60+ min): {contador_retraso_grave}")

if __name__ == "__main__":
    test_calcular_retrasos()
    test_resumen_datos()
    print("\n✅ ¡Todas las pruebas completadas!")
