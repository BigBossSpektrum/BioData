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
    Identifica si es turno nocturno basándose en la hora de entrada.
    Un turno es nocturno cuando la entrada es mayor a la salida (cruza medianoche).
    
    Args:
        hora_entrada (time): Hora de entrada al turno
        hora_salida (time, optional): Hora de salida del turno
    
    Returns:
        bool: True si es turno nocturno, False si es diurno
    """
    # Si la entrada es después de las 22:00 o antes de las 6:00, es nocturno
    if isinstance(hora_entrada, datetime):
        hora_entrada = hora_entrada.time()
    
    if isinstance(hora_salida, datetime):
        hora_salida = hora_salida.time()
    
    # Turno nocturno típico: entrada >= 22:00 o entrada < 6:00 (no incluye las 6:00)
    if hora_entrada >= time(22, 0) or hora_entrada < time(6, 0):
        return True
    
    # Si tenemos hora de salida, verificar si cruza medianoche
    if hora_salida and hora_entrada > hora_salida:
        return True
    
    return False


def calcular_diferencia_dias_turno_nocturno(entrada_datetime, salida_datetime):
    """
    Calcula la diferencia de días para turnos nocturnos.
    Para turnos nocturnos, la salida es al día siguiente.
    
    Args:
        entrada_datetime (datetime): Fecha y hora de entrada
        salida_datetime (datetime): Fecha y hora de salida
    
    Returns:
        dict: Información sobre el turno nocturno incluyendo:
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
    
    # Determinar si es turno nocturno
    es_nocturno = es_turno_nocturno(entrada_datetime.time(), salida_datetime.time())
    
    # Calcular diferencia de días
    fecha_entrada = entrada_datetime.date()
    fecha_salida = salida_datetime.date()
    diferencia_dias = (fecha_salida - fecha_entrada).days
    
    # Calcular duración del turno
    duracion = salida_datetime - entrada_datetime
    
    # Si la salida es anterior a la entrada, significa que cruzó medianoche
    if duracion.total_seconds() < 0:
        duracion += timedelta(days=1)
        diferencia_dias = 1
        es_nocturno = True
    
    duracion_horas = round(duracion.total_seconds() / 3600, 2)
    
    # Generar mensaje descriptivo
    if es_nocturno:
        if diferencia_dias == 1:
            mensaje = f"Turno nocturno: entrada {entrada_datetime.strftime('%H:%M')} del {fecha_entrada.strftime('%d/%m/%Y')}, salida {salida_datetime.strftime('%H:%M')} del {fecha_salida.strftime('%d/%m/%Y')}"
        else:
            mensaje = f"Turno nocturno extendido: {diferencia_dias} días de diferencia"
    else:
        mensaje = f"Turno diurno: mismo día ({fecha_entrada.strftime('%d/%m/%Y')})"
    
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
    
    # Clasificación por horarios
    if time(6, 0) <= hora_entrada < time(14, 0):
        tipo = 'mañana'
        es_nocturno = False
        descripcion = 'Turno de mañana (06:00 - 14:00)'
    elif time(14, 0) <= hora_entrada < time(22, 0):
        tipo = 'tarde'
        es_nocturno = False
        descripcion = 'Turno de tarde (14:00 - 22:00)'
    elif hora_entrada >= time(22, 0) or hora_entrada < time(6, 0):
        tipo = 'nocturno'
        es_nocturno = True
        descripcion = 'Turno nocturno (22:00 - 06:00)'
    else:
        tipo = 'irregular'
        es_nocturno = False
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
        
        # Para turnos nocturnos, verificar que la entrada sea realmente la hora mayor
        if es_nocturno and salida_datetime:
            hora_salida = salida_datetime.time()
            # Si la salida es mayor que la entrada en turno nocturno, posiblemente están invertidas
            if hora_salida > hora_entrada and hora_entrada < time(12, 0) and hora_salida >= time(22, 0):
                # Probablemente los timestamps están invertidos, corregir el mensaje
                resultado['mensaje'] = f"Turno nocturno: entrada {salida_datetime.strftime('%H:%M')}, salida {entrada_datetime.strftime('%H:%M')}"
    
    return resultado
