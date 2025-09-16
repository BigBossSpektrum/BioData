from datetime import datetime, timedelta, time
from django.utils.timezone import localtime

def obtener_rango_semana(fecha_str):
    """
    Dada una fecha en formato YYYY-MM-DD, retorna el inicio (lunes) y fin (domingo) de esa semana.
    """
    if not fecha_str:
        raise ValueError("La fecha no puede estar vacía.")

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("La fecha debe estar en formato YYYY-MM-DD")

    inicio_semana = fecha - timedelta(days=fecha.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    return inicio_semana, fin_semana


def es_turno_nocturno(hora_entrada, hora_salida=None):
    """
    Identifica si es turno nocturno basándose en la hora de entrada y salida.
    Un turno es nocturno cuando:
    - Entrada entre 21:00 y 23:59, O
    - Si no hay salida, pero entrada es entre 21:00 y 23:59
    - Si hay salida: entrada entre 21:00-23:59 Y salida entre 00:00-08:00
    
    Args:
        hora_entrada (time): Hora de entrada al turno
        hora_salida (time, optional): Hora de salida del turno
    
    Returns:
        bool: True si es turno nocturno, False si es diurno
    """
    # Convertir datetime a time si es necesario
    if isinstance(hora_entrada, datetime):
        hora_entrada = hora_entrada.time()
    
    if isinstance(hora_salida, datetime):
        hora_salida = hora_salida.time()
    
    # Condición principal: entrada nocturna
    entrada_nocturna = time(21, 0) <= hora_entrada <= time(23, 59)
    
    # Si no hay salida, solo considerar la entrada
    if not hora_salida:
        return entrada_nocturna
    
    # Si hay salida, verificar que también sea compatible con turno nocturno
    salida_nocturna = time(0, 0) <= hora_salida <= time(8, 0)
    
    # Es nocturno si tiene entrada nocturna Y (no hay salida O salida nocturna)
    return entrada_nocturna and salida_nocturna


def calcular_diferencia_dias_turno_nocturno(entrada_datetime, salida_datetime):
    """
    Calcula la diferencia de días para turnos nocturnos usando nueva lógica estricta.
    Para turnos nocturnos, la entrada debe ser entre 20:00-23:59 y la salida entre 00:00-08:00 del día siguiente.
    
    Args:
        entrada_datetime (datetime): Fecha y hora de entrada
        salida_datetime (datetime): Fecha y hora de salida
    
    Returns:
        dict: Información sobre el turno incluyendo:
            - es_nocturno (bool): Si es turno nocturno
            - diferencia_dias (int): Diferencia en días
            - duracion_horas (float): Duración del turno en horas
            - fecha_entrada (date): Fecha de entrada
            - fecha_salida (date): Fecha de salida
    """
    if not entrada_datetime or not salida_datetime:
        return {
            'es_nocturno': False,
            'diferencia_dias': 0,
            'duracion_horas': 0,
            'fecha_entrada': None,
            'fecha_salida': None,
            'mensaje': 'Faltan datos de entrada o salida'
        }
    
    # Determinar si es turno nocturno usando la nueva lógica estricta
    es_nocturno = es_turno_nocturno(entrada_datetime.time(), salida_datetime.time())
    
    # Calcular diferencia de días
    fecha_entrada = entrada_datetime.date()
    fecha_salida = salida_datetime.date()
    diferencia_dias = (fecha_salida - fecha_entrada).days
    
    # Para turnos nocturnos, verificar que la diferencia sea de 1 día
    if es_nocturno and diferencia_dias != 1:
        # Si las condiciones de hora se cumplen pero no hay diferencia de días,
        # posiblemente los registros están mal ordenados
        es_nocturno = False
    
    # Calcular duración del turno
    duracion = salida_datetime - entrada_datetime
    
    # Si la duración es negativa y es potencialmente nocturno, ajustar
    if duracion.total_seconds() < 0:
        duracion += timedelta(days=1)
        diferencia_dias = 1
        # Re-evaluar si es nocturno con la nueva duración
        if (time(21, 0) <= entrada_datetime.time() <= time(23, 59) and 
            time(0, 0) <= salida_datetime.time() <= time(8, 0)):
            es_nocturno = True
    
    duracion_horas = round(duracion.total_seconds() / 3600, 2)
    
    # Generar mensaje descriptivo
    if es_nocturno:
        if diferencia_dias == 1:
            mensaje = f"Turno nocturno: entrada {entrada_datetime.strftime('%H:%M')} del {fecha_entrada.strftime('%d/%m/%Y')}, salida {salida_datetime.strftime('%H:%M')} del {fecha_salida.strftime('%d/%m/%Y')}"
        else:
            mensaje = f"Turno nocturno extendido: {diferencia_dias} días de diferencia"
    else:
        if diferencia_dias == 0:
            mensaje = f"Turno diurno: mismo día ({fecha_entrada.strftime('%d/%m/%Y')})"
        else:
            mensaje = f"Turno extendido: {diferencia_dias} días de diferencia (no nocturno)"
    
    return {
        'es_nocturno': es_nocturno,
        'diferencia_dias': diferencia_dias,
        'duracion_horas': duracion_horas,
        'fecha_entrada': fecha_entrada,
        'fecha_salida': fecha_salida,
        'mensaje': mensaje,
        'entrada_formateada': entrada_datetime.strftime('%H:%M'),
        'salida_formateada': salida_datetime.strftime('%H:%M')
    }


def validar_y_emparejar_turno_nocturno(registros_usuario_completos):
    """
    Valida y empareja registros de turnos nocturnos que cruzan medianoche.
    
    Para un usuario dado, busca patrones de entrada nocturna (21:00-23:59) 
    seguida de salida al día siguiente (00:00-08:00) y los empareja correctamente.
    
    Args:
        registros_usuario_completos: Lista de registros de un usuario ordenados por fecha
        
    Returns:
        dict: Registros organizados por fecha con turnos nocturnos emparejados
    """
    from collections import defaultdict
    from django.utils.timezone import localtime
    
    # Organizar registros por fecha
    registros_por_fecha = defaultdict(list)
    for registro in registros_usuario_completos:
        fecha_local = localtime(registro.timestamp).date()
        timestamp_local = localtime(registro.timestamp)
        registros_por_fecha[fecha_local].append(timestamp_local)
    
    # Ordenar fechas y registros
    fechas_ordenadas = sorted(registros_por_fecha.keys())
    turnos_emparejados = {}
    registros_procesados = set()  # Para evitar procesar el mismo registro dos veces
    
    for i, fecha in enumerate(fechas_ordenadas):
        registros_fecha = sorted(registros_por_fecha[fecha])
        
        # Buscar entradas nocturnas en esta fecha
        entradas_nocturnas = [
            r for r in registros_fecha 
            if time(21, 0) <= r.time() <= time(23, 59) and r not in registros_procesados
        ]
        
        if entradas_nocturnas:
            # Para cada entrada nocturna, buscar su salida correspondiente
            for entrada_nocturna in entradas_nocturnas:
                salida_encontrada = None
                
                # 1. Buscar salida en el mismo día (poco probable pero posible)
                salidas_mismo_dia = [
                    r for r in registros_fecha 
                    if time(0, 0) <= r.time() <= time(8, 0) 
                    and r > entrada_nocturna 
                    and r not in registros_procesados
                ]
                
                if salidas_mismo_dia:
                    salida_encontrada = min(salidas_mismo_dia)
                else:
                    # 2. Buscar salida en el día siguiente
                    if i + 1 < len(fechas_ordenadas):
                        fecha_siguiente = fechas_ordenadas[i + 1]
                        registros_fecha_siguiente = sorted(registros_por_fecha[fecha_siguiente])
                        
                        salidas_dia_siguiente = [
                            r for r in registros_fecha_siguiente 
                            if time(0, 0) <= r.time() <= time(8, 0)
                            and r not in registros_procesados
                        ]
                        
                        if salidas_dia_siguiente:
                            # Tomar la primera salida válida del día siguiente
                            salida_encontrada = min(salidas_dia_siguiente)
                
                # Si encontramos un par entrada-salida válido
                if salida_encontrada:
                    # Verificar que realmente es un turno nocturno válido
                    if es_turno_nocturno(entrada_nocturna.time(), salida_encontrada.time()):
                        # Calcular en qué fecha clasificar este turno
                        # Generalmente se clasifica en la fecha de entrada
                        fecha_turno = entrada_nocturna.date()
                        
                        turnos_emparejados[fecha_turno] = {
                            'entrada': entrada_nocturna,
                            'salida': salida_encontrada,
                            'es_nocturno': True,
                            'emparejado': True,
                            'crosses_midnight': salida_encontrada.date() > entrada_nocturna.date()
                        }
                        
                        # Marcar ambos registros como procesados
                        registros_procesados.add(entrada_nocturna)
                        registros_procesados.add(salida_encontrada)
                else:
                    # Entrada nocturna sin salida válida encontrada
                    fecha_turno = entrada_nocturna.date()
                    turnos_emparejados[fecha_turno] = {
                        'entrada': entrada_nocturna,
                        'salida': None,
                        'es_nocturno': False,  # No podemos confirmar sin salida
                        'emparejado': False,
                        'sin_salida': True
                    }
                    registros_procesados.add(entrada_nocturna)
    
    # Procesar registros no emparejados (turnos diurnos normales)
    for fecha in fechas_ordenadas:
        if fecha not in turnos_emparejados:
            registros_fecha = sorted(registros_por_fecha[fecha])
            registros_no_procesados = [r for r in registros_fecha if r not in registros_procesados]
            
            if registros_no_procesados:
                if len(registros_no_procesados) >= 2:
                    # Turno diurno normal: primer registro = entrada, último = salida
                    turnos_emparejados[fecha] = {
                        'entrada': registros_no_procesados[0],
                        'salida': registros_no_procesados[-1],
                        'es_nocturno': False,
                        'emparejado': True,
                        'diurno': True
                    }
                else:
                    # Solo un registro
                    registro_unico = registros_no_procesados[0]
                    # Determinar si es entrada o salida basado en la hora
                    if time(0, 0) <= registro_unico.time() <= time(8, 0):
                        # Podría ser salida de turno nocturno no emparejado
                        turnos_emparejados[fecha] = {
                            'entrada': None,
                            'salida': registro_unico,
                            'es_nocturno': False,
                            'emparejado': False,
                            'posible_salida_nocturna': True
                        }
                    else:
                        # Probablemente entrada sin salida
                        turnos_emparejados[fecha] = {
                            'entrada': registro_unico,
                            'salida': None,
                            'es_nocturno': False,
                            'emparejado': False,
                            'sin_salida': True
                        }
    
    return turnos_emparejados


def detectar_tipo_turno_detallado(entrada_datetime, salida_datetime=None):
    """
    Detecta el tipo de turno con información detallada.
    Un turno nocturno real debe cumplir:
    - Entrada alrededor de las 22:00 (entre 21:00 y 23:59)
    - Salida al día siguiente alrededor de las 6:00 (entre 00:00 y 8:00)
    
    NOTA: Se aplica un margen de 1 hora antes de cada turno para determinar correctamente
    el tipo de turno al que pertenece la entrada.
    
    IMPORTANTE: Las horas de madrugada (00:00-06:00) se consideran turno de mañana SOLO si
    no hay evidencia de que sea un turno nocturno (requiere entrada nocturna previa).
    
    Args:
        entrada_datetime (datetime): Fecha y hora de entrada
        salida_datetime (datetime, optional): Fecha y hora de salida
    
    Returns:
        dict: Información detallada del turno
    """
    if not entrada_datetime:
        return {
            'tipo': 'indefinido',
            'es_nocturno': False,
            'descripcion': 'Sin datos de entrada'
        }
    
    hora_entrada = entrada_datetime.time()
    
    # Lógica mejorada para detectar turno nocturno
    es_nocturno = False
    tipo = 'diurno'
    descripcion = 'Turno diurno'
    
    # Para determinar si es nocturno, necesitamos entrada Y salida
    if salida_datetime:
        hora_salida = salida_datetime.time()
        fecha_entrada = entrada_datetime.date()
        fecha_salida = salida_datetime.date()
        
        # Condiciones para turno nocturno real:
        # 1. Entrada entre 21:00 y 23:59 (margen de 1 hora antes de 22:00)
        # 2. Salida entre 00:00 y 8:00 del día siguiente
        # 3. La salida debe ser al día siguiente
        entrada_nocturna = time(21, 0) <= hora_entrada <= time(23, 59)
        salida_nocturna = time(0, 0) <= hora_salida <= time(8, 0)
        diferencia_dias = (fecha_salida - fecha_entrada).days
        
        # Ajustar lógica para ser más flexible con turnos nocturnos
        if entrada_nocturna and salida_nocturna and (diferencia_dias == 1 or diferencia_dias == 0):
            # Permitir diferencia de 0 días si la salida es muy temprano del mismo día
            if diferencia_dias == 0 and hora_salida <= time(6, 0):
                es_nocturno = True
                tipo = 'nocturno'
                descripcion = 'Turno nocturno (22:00 - 06:00)'
            elif diferencia_dias == 1:
                es_nocturno = True
                tipo = 'nocturno'
                descripcion = 'Turno nocturno (22:00 - 06:00)'
            else:
                # Entrada nocturna pero salida no válida para nocturno
                tipo = 'nocturno'
                descripcion = 'Turno nocturno (22:00 - 06:00)'
        elif entrada_nocturna:  # Solo entrada nocturna, sin salida válida
            es_nocturno = True
            tipo = 'nocturno'
            descripcion = 'Turno nocturno (22:00 - 06:00)'
        else:
            # Clasificar como turno diurno basado en hora de entrada con margen de 1 hora
            # NOTA: Las horas de madrugada solo se consideran nocturnas si hay entrada nocturna válida
            if time(6, 0) <= hora_entrada < time(13, 0):  # Turno mañana
                tipo = 'mañana'
                descripcion = 'Turno de mañana (07:00 - 14:00)'
            elif time(13, 0) <= hora_entrada < time(21, 0):  # Turno tarde
                tipo = 'tarde'
                descripcion = 'Turno de tarde (14:00 - 22:00)'
            elif time(21, 0) <= hora_entrada <= time(23, 59):  # Entrada nocturna tardía
                es_nocturno = True
                tipo = 'nocturno'
                descripcion = 'Turno nocturno (22:00 - 06:00)'
            elif time(0, 0) <= hora_entrada < time(6, 0):  # Madrugada - por defecto mañana
                # Sin entrada nocturna previa, probablemente es entrada temprana de mañana
                tipo = 'mañana'
                descripcion = 'Turno de mañana - entrada muy temprana (07:00 - 14:00)'
            else:
                tipo = 'irregular'
                descripcion = 'Horario irregular'
    else:
        # Sin salida, solo clasificar por entrada con margen de 1 hora
        # IMPORTANTE: Ser más conservador con las horas de madrugada
        if time(6, 0) <= hora_entrada < time(13, 0):  # Turno mañana normal
            tipo = 'mañana'
            descripcion = 'Turno de mañana (07:00 - 14:00)'
        elif time(13, 0) <= hora_entrada < time(21, 0):  # Turno tarde
            tipo = 'tarde'
            descripcion = 'Turno de tarde (14:00 - 22:00)'
        elif time(21, 0) <= hora_entrada <= time(23, 59):  # Entrada nocturna
            es_nocturno = True  # Marcar como nocturno aunque no haya salida
            tipo = 'nocturno'
            descripcion = 'Turno nocturno (22:00 - 06:00)'
        elif time(0, 0) <= hora_entrada < time(6, 0):  # Madrugada - AMBIGUO
            # En madrugada sin más contexto, es más probable que sea entrada de mañana
            # que salida de nocturno sin registrar la entrada
            tipo = 'mañana'
            descripcion = 'Turno de mañana - entrada muy temprana (07:00 - 14:00)'
        else:
            tipo = 'irregular'
            descripcion = 'Horario irregular'
    
    resultado = {
        'tipo': tipo,
        'es_nocturno': es_nocturno,
        'descripcion': descripcion,
        'hora_entrada': entrada_datetime.strftime('%H:%M')
    }
    
    # Si hay salida, agregar información del turno completo
    if salida_datetime:
        info_turno = calcular_diferencia_dias_turno_nocturno(entrada_datetime, salida_datetime)
        resultado.update(info_turno)
        resultado['hora_salida'] = salida_datetime.strftime('%H:%M')
    
    return resultado


def calcular_horas_con_horarios_estandar(entrada_datetime, salida_datetime):
    """
    Calcula las horas trabajadas considerando horarios estándar de turnos.
    No cuenta el tiempo trabajado antes de la hora oficial de entrada.
    
    Horarios estándar:
    - Turno Mañana: 07:00 - 14:00 (8 horas)
    - Turno Tarde: 14:00 - 22:00 (8 horas)  
    - Turno Noche: 22:00 - 06:00 (8 horas)
    
    Args:
        entrada_datetime (datetime): Fecha y hora de entrada registrada
        salida_datetime (datetime): Fecha y hora de salida registrada
    
    Returns:
        dict: Información del cálculo incluyendo:
            - horas_trabajadas (float): Total de horas trabajadas
            - horas_normales (float): Horas dentro de la jornada normal (máximo 8)
            - horas_extras (float): Horas trabajadas adicionales
            - entrada_efectiva (datetime): Hora desde la que se empezó a contar
            - salida_efectiva (datetime): Hora hasta la que se contó
            - mensaje (str): Descripción del cálculo
    """
    if not entrada_datetime or not salida_datetime:
        return {
            'horas_trabajadas': 0,
            'horas_normales': 0,
            'horas_extras': 0,
            'entrada_efectiva': None,
            'salida_efectiva': None,
            'mensaje': 'Faltan datos de entrada o salida',
            'tipo_turno': 'No determinado'
        }
    
    # Detectar qué turno es según la hora de entrada
    hora_entrada = entrada_datetime.time()
    fecha_entrada = entrada_datetime.date()
    
    # Definir horarios estándar de inicio de turno
    if time(5, 0) <= hora_entrada < time(13, 0):  # Rango amplio para turno mañana
        # Turno Mañana: 07:00 - 14:00
        inicio_turno = datetime.combine(fecha_entrada, time(7, 0))
        fin_turno = datetime.combine(fecha_entrada, time(14, 0))
        tipo_turno = "Mañana (07:00-14:00)"
    elif time(13, 0) <= hora_entrada < time(21, 0):  # Rango para turno tarde
        # Turno Tarde: 14:00 - 22:00
        inicio_turno = datetime.combine(fecha_entrada, time(14, 0))
        fin_turno = datetime.combine(fecha_entrada, time(22, 0))
        tipo_turno = "Tarde (14:00-22:00)"
    else:  # Turno nocturno
        # Turno Noche: 22:00 - 06:00 (del día siguiente)
        if hora_entrada >= time(21, 0):  # Entrada en la noche
            inicio_turno = datetime.combine(fecha_entrada, time(22, 0))
            fin_turno = datetime.combine(fecha_entrada + timedelta(days=1), time(6, 0))
        else:  # Entrada en la madrugada (es salida de turno nocturno anterior)
            # Tratar como si fuera parte del turno nocturno anterior
            inicio_turno = datetime.combine(fecha_entrada - timedelta(days=1), time(22, 0))
            fin_turno = datetime.combine(fecha_entrada, time(6, 0))
        tipo_turno = "Noche (22:00-06:00)"
    
    # Hacer timezone aware si es necesario
    if hasattr(entrada_datetime, 'tzinfo') and entrada_datetime.tzinfo:
        from django.utils import timezone
        inicio_turno = timezone.make_aware(inicio_turno)
        fin_turno = timezone.make_aware(fin_turno)
    
    # La entrada efectiva no puede ser antes del inicio oficial del turno
    entrada_efectiva = max(entrada_datetime, inicio_turno)
    salida_efectiva = salida_datetime
    
    # Si la entrada efectiva es después de la salida, no hay tiempo válido
    if entrada_efectiva >= salida_efectiva:
        return {
            'horas_trabajadas': 0,
            'horas_normales': 0,
            'horas_extras': 0,
            'entrada_efectiva': entrada_efectiva,
            'salida_efectiva': salida_efectiva,
            'mensaje': f'No hay tiempo válido. Turno: {tipo_turno}',
            'tipo_turno': tipo_turno
        }
    
    # Calcular horas normales (dentro del horario oficial)
    salida_normal = min(salida_efectiva, fin_turno)
    if entrada_efectiva < salida_normal:
        tiempo_normal = salida_normal - entrada_efectiva
        horas_normales = round(tiempo_normal.total_seconds() / 3600, 2)
    else:
        horas_normales = 0
    
    # Calcular horas extras (después del fin oficial del turno)
    horas_extras = 0
    if salida_efectiva > fin_turno:
        tiempo_extra = salida_efectiva - fin_turno
        horas_extras = round(tiempo_extra.total_seconds() / 3600, 2)
    
    # Total de horas trabajadas
    horas_trabajadas = round(horas_normales + horas_extras, 2)
    
    # Generar mensaje informativo
    tiempo_no_contado = ""
    if entrada_datetime < inicio_turno:
        tiempo_antes = inicio_turno - entrada_datetime
        minutos_antes = round(tiempo_antes.total_seconds() / 60)
        tiempo_no_contado = f" (No se contaron {minutos_antes} min antes de las {inicio_turno.strftime('%H:%M')})"
    
    mensaje = f"Turno {tipo_turno}: {horas_normales:.2f}h normales + {horas_extras:.2f}h extras{tiempo_no_contado}"
    
    return {
        'horas_trabajadas': horas_trabajadas,
        'horas_normales': horas_normales,
        'horas_extras': horas_extras,
        'entrada_efectiva': entrada_efectiva,
        'salida_efectiva': salida_efectiva,
        'mensaje': mensaje,
        'tipo_turno': tipo_turno
    }


def procesar_turno_nocturno_con_siguiente_registro(asistencia_por_usuario_fecha, usuario, fecha_actual):
    """
    Procesa turnos nocturnos buscando la salida en el día siguiente.
    Esta función se ejecuta SOLO para turnos nocturnos detectados.
    
    Args:
        asistencia_por_usuario_fecha: Diccionario con todos los registros del usuario por fecha
        usuario: El usuario actual
        fecha_actual: La fecha donde se detectó la entrada nocturna
        
    Returns:
        dict: Información del turno nocturno procesado o None si no se puede procesar
    """
    registros_dia_actual = asistencia_por_usuario_fecha[usuario].get(fecha_actual, [])
    
    if not registros_dia_actual:
        return None
    
    # Ordenar registros del día actual por timestamp
    registros_dia_actual.sort(key=lambda r: r.timestamp)
    
    # Buscar entrada nocturna (21:00-23:59)
    entrada_nocturna = None
    for registro in registros_dia_actual:
        hora_registro = localtime(registro.timestamp).time()
        if time(21, 0) <= hora_registro <= time(23, 59):
            entrada_nocturna = registro
            break
    
    if not entrada_nocturna:
        return None
    
    entrada_dt = localtime(entrada_nocturna.timestamp)
    
    # Verificar que es realmente un turno nocturno
    info_turno = detectar_tipo_turno_detallado(entrada_dt, None)
    if not info_turno['es_nocturno']:
        return None
    
    # Buscar salida en el día siguiente (00:00-08:00)
    from datetime import timedelta
    fecha_siguiente = fecha_actual + timedelta(days=1)
    registros_dia_siguiente = asistencia_por_usuario_fecha[usuario].get(fecha_siguiente, [])
    
    salida_nocturna = None
    if registros_dia_siguiente:
        # Ordenar registros del día siguiente
        registros_dia_siguiente.sort(key=lambda r: r.timestamp)
        
        # Buscar primera salida válida (00:00-23:59 del día siguiente)
        # Nota: Buscamos en todo el día siguiente, pero validaremos duración
        for registro in registros_dia_siguiente:
            hora_registro = localtime(registro.timestamp).time()
            # Ampliar búsqueda pero preferir salidas tempranas
            if time(0, 0) <= hora_registro <= time(23, 59):
                if not salida_nocturna or hora_registro <= time(8, 0):
                    # Preferir salidas entre 00:00-08:00, pero permitir otras
                    salida_nocturna = registro
                    if hora_registro <= time(8, 0):
                        break  # Si encontramos una salida temprana, la usamos
    
    # Si no hay salida en el día siguiente, buscar en el mismo día (para casos edge)
    if not salida_nocturna:
        for registro in registros_dia_actual:
            if registro == entrada_nocturna:
                continue
            hora_registro = localtime(registro.timestamp).time()
            if time(0, 0) <= hora_registro <= time(8, 0):
                salida_nocturna = registro
                break
    
    # Preparar la información de retorno
    entrada = entrada_dt
    salida = localtime(salida_nocturna.timestamp) if salida_nocturna else None
    
    # VALIDACIÓN: No permitir jornadas que superen las 20 horas
    if salida:
        duracion_turno = salida - entrada
        horas_duracion = duracion_turno.total_seconds() / 3600
        
        if horas_duracion > 20:
            # Si la duración supera 20 horas, rechazar este emparejamiento
            salida = None
            mensaje = f"Turno nocturno: {entrada.strftime('%H:%M')} - Salida rechazada (duración > 20h)"
            horas_trabajadas = 0.0
            horas_extra = 0.0
        else:
            # Calcular horas usando la función estándar
            calculo = calcular_horas_con_horarios_estandar(entrada, salida)
            horas_trabajadas = calculo['horas_trabajadas']
            horas_extra = calculo['horas_extras']
            mensaje = f"Turno nocturno: {entrada.strftime('%H:%M')} → {salida.strftime('%H:%M')} (día siguiente) - {horas_duracion:.1f}h"
    else:
        horas_trabajadas = 0.0
        horas_extra = 0.0
        mensaje = "Turno nocturno: Sin salida registrada"
    
    # Actualizar información del turno
    info_turno_completo = detectar_tipo_turno_detallado(entrada, salida)
    
    return {
        'entrada': entrada,
        'salida': salida,
        'horas_trabajadas': horas_trabajadas,
        'horas_extra': horas_extra,
        'es_turno_nocturno': True,
        'info_turno': info_turno_completo,
        'mensaje': mensaje,
        'registros_usados': [entrada_nocturna] + ([salida_nocturna] if salida_nocturna else [])
    }
