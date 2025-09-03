from datetime import datetime, timedelta, time

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
    Un turno es nocturno SOLO cuando:
    - Entrada entre 20:00 y 23:59
    - Salida entre 00:00 y 08:00 del día siguiente
    - La salida es cronológicamente posterior a la entrada (cruza medianoche)
    
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
    
    # Para ser turno nocturno necesitamos tanto entrada como salida
    if not hora_salida:
        return False
    
    # Condiciones estrictas para turno nocturno:
    entrada_nocturna = time(20, 0) <= hora_entrada <= time(23, 59)
    salida_nocturna = time(0, 0) <= hora_salida <= time(8, 0)
    
    # Solo es nocturno si cumple ambas condiciones
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
        if (time(20, 0) <= entrada_datetime.time() <= time(23, 59) and 
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


def detectar_tipo_turno_detallado(entrada_datetime, salida_datetime=None):
    """
    Detecta el tipo de turno con información detallada.
    Un turno nocturno real debe cumplir:
    - Entrada alrededor de las 22:00 (entre 20:00 y 23:59)
    - Salida al día siguiente alrededor de las 6:00 (entre 00:00 y 8:00)
    
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
        # 1. Entrada entre 20:00 y 23:59
        # 2. Salida entre 00:00 y 8:00 del día siguiente
        # 3. La salida debe ser al día siguiente
        entrada_nocturna = time(20, 0) <= hora_entrada <= time(23, 59)
        salida_nocturna = time(0, 0) <= hora_salida <= time(8, 0)
        diferencia_dias = (fecha_salida - fecha_entrada).days
        
        if entrada_nocturna and salida_nocturna and diferencia_dias == 1:
            es_nocturno = True
            tipo = 'nocturno'
            descripcion = 'Turno nocturno (20:00 - 08:00)'
        else:
            # Clasificar como turno diurno basado en hora de entrada
            if time(5, 0) <= hora_entrada < time(14, 0):
                tipo = 'mañana'
                descripcion = 'Turno de mañana (05:00 - 14:00)'
            elif time(14, 0) <= hora_entrada < time(22, 0):
                tipo = 'tarde'
                descripcion = 'Turno de tarde (14:00 - 22:00)'
            else:
                tipo = 'irregular'
                descripcion = 'Horario irregular'
    else:
        # Sin salida, solo clasificar por entrada
        if time(5, 0) <= hora_entrada < time(14, 0):
            tipo = 'mañana'
            descripcion = 'Turno de mañana (05:00 - 14:00)'
        elif time(14, 0) <= hora_entrada < time(22, 0):
            tipo = 'tarde'
            descripcion = 'Turno de tarde (14:00 - 22:00)'
        elif time(20, 0) <= hora_entrada <= time(23, 59):
            # Posible inicio de turno nocturno, pero sin salida no podemos confirmarlo
            tipo = 'posible_nocturno'
            descripcion = 'Posible inicio de turno nocturno'
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
