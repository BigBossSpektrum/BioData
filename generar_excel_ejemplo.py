#!/usr/bin/env python
"""
Script para generar un ejemplo de archivo Excel con la nueva funcionalidad
de horas de retraso y resumen total.
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
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

def generar_excel_ejemplo():
    """Genera un archivo Excel de ejemplo con la nueva funcionalidad"""
    
    # Datos de ejemplo
    registros_ejemplo = [
        {
            'dia': '12/09/2025',
            'nombre': 'Juan Pérez',
            'estacion': 'Estación 1',
            'entrada': '07:00',
            'salida': '15:00',
            'horas_trabajadas': '08:00',
            'tipo_turno': 'Turno 1 (7:00-14:00)',
            'horas_extra': '',
            'aprobado': ''
        },
        {
            'dia': '12/09/2025',
            'nombre': 'María García',
            'estacion': 'Estación 2',
            'entrada': '07:30',
            'salida': '16:00',
            'horas_trabajadas': '08:30',
            'tipo_turno': 'Turno 1 (7:00-14:00)',
            'horas_extra': '00:30',
            'aprobado': 'Aprobado'
        },
        {
            'dia': '12/09/2025',
            'nombre': 'Carlos López ⭐ 12H',
            'estacion': 'Estación 3',
            'entrada': '14:45',
            'salida': '23:30',
            'horas_trabajadas': '08:45',
            'tipo_turno': 'Turno 2 (14:00-22:00)',
            'horas_extra': '00:45',
            'aprobado': 'Pendiente'
        },
        {
            'dia': '12/09/2025',
            'nombre': 'Ana Rodríguez',
            'estacion': 'Estación 1',
            'entrada': '22:30',
            'salida': '06:30',
            'horas_trabajadas': '08:00',
            'tipo_turno': 'Turno 3 (22:00-07:00)',
            'horas_extra': '',
            'aprobado': ''
        },
        {
            'dia': '12/09/2025',
            'nombre': 'Pedro Martínez',
            'estacion': 'Estación 2',
            'entrada': '08:15',
            'salida': '17:00',
            'horas_trabajadas': '08:45',
            'tipo_turno': 'Turno 1 (7:00-14:00)',
            'horas_extra': '00:45',
            'aprobado': 'Rechazado'
        },
    ]
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen Asistencias"

    # Estilos
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2E86AB", end_color="2E86AB", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    cell_alignment = Alignment(horizontal="center", vertical="center")
    border_thin = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Estilos para resumen
    summary_font = Font(bold=True, color="FFFFFF")
    summary_fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
    
    # Encabezados
    headers = [
        "Día", "Nombre", "Estación", "Entrada", "Salida", "Horas de Retraso",
        "Horas Trabajadas", "Tipo de Turno", "Horas Extras", "Aprobado"
    ]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border_thin

    # Variables para calcular resumen
    total_registros = len(registros_ejemplo)
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
    
    # Procesar registros
    for row, registro in enumerate(registros_ejemplo, 2):
        # Calcular horas de retraso
        horas_retraso = calcular_horas_retraso(registro['entrada'], registro['tipo_turno'])
        
        # Contabilizar tipos de retraso para resumen
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

        # Escribir datos
        data = [
            registro['dia'],
            registro['nombre'],
            registro['estacion'],
            registro['entrada'],
            registro['salida'],
            horas_retraso or '-',
            registro['horas_trabajadas'],
            registro['tipo_turno'],
            registro['horas_extra'] or '-',
            registro['aprobado'] or '-'
        ]
        
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.alignment = cell_alignment
            cell.border = border_thin

    # Agregar resumen total al final
    summary_row = len(registros_ejemplo) + 3  # Dejar una fila en blanco
    
    # Función para convertir minutos a HH:MM
    def minutos_a_hhmm(minutos):
        if minutos == 0:
            return "00:00"
        horas = minutos // 60
        mins = minutos % 60
        return f"{horas:02d}:{mins:02d}"
    
    # Título del resumen
    ws.cell(row=summary_row, column=1, value="RESUMEN TOTAL").font = summary_font
    ws.cell(row=summary_row, column=1).fill = summary_fill
    ws.cell(row=summary_row, column=1).alignment = header_alignment
    
    # Merge cells para el título
    ws.merge_cells(f"A{summary_row}:J{summary_row}")
    
    # Datos del resumen
    summary_data = [
        ["Total de Registros:", total_registros],
        ["Total Horas Trabajadas:", minutos_a_hhmm(total_minutos_trabajados)],
        ["Total Horas Extras:", minutos_a_hhmm(total_minutos_extras)],
        ["Horas Extras Aprobadas:", minutos_a_hhmm(total_minutos_extras_aprobadas)],
        ["", ""],  # Fila en blanco
        ["ESTADO DE HORAS EXTRAS:", ""],
        ["Aprobadas:", contador_aprobadas],
        ["Rechazadas:", contador_rechazadas],
        ["Pendientes:", contador_pendientes],
        ["", ""],  # Fila en blanco
        ["RESUMEN DE RETRASOS:", ""],
        ["Sin Retraso:", contador_sin_retraso],
        ["Retraso Leve (1-29 min):", contador_retraso_leve],
        ["Retraso Moderado (30-59 min):", contador_retraso_moderado],
        ["Retraso Grave (60+ min):", contador_retraso_grave],
    ]
    
    for i, (label, value) in enumerate(summary_data):
        row_num = summary_row + 1 + i
        ws.cell(row=row_num, column=1, value=label).font = Font(bold=True)
        ws.cell(row=row_num, column=2, value=value)
        
        # Aplicar borde a las celdas del resumen
        ws.cell(row=row_num, column=1).border = border_thin
        ws.cell(row=row_num, column=2).border = border_thin

    # Ajustar ancho de columnas
    column_widths = [12, 25, 15, 10, 10, 15, 15, 20, 12, 12]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width

    # Guardar archivo
    filename = f'ejemplo_resumen_asistencias_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    wb.save(filename)
    
    print(f"✅ Archivo Excel generado exitosamente: {filename}")
    
    # Mostrar resumen en consola
    print(f"\n📊 RESUMEN GENERADO:")
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
    generar_excel_ejemplo()
