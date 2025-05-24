from datetime import datetime, time

def determinar_estado_por_turno(usuario, registro_datetime):
    if not usuario.turno:
        return 0  # Default: entrada

    inicio = usuario.turno.hora_inicio
    fin = usuario.turno.hora_fin
    hora_registro = registro_datetime.time()

    if inicio > fin:
        # Turno nocturno (ej. 22:00 a 06:00)
        if hora_registro >= inicio or hora_registro <= fin:
            return 0 if hora_registro >= inicio else 1
    else:
        medio_turno = (
            datetime.combine(datetime.today(), inicio) + 
            (datetime.combine(datetime.today(), fin) - datetime.combine(datetime.today(), inicio)) / 2
        ).time()

        if hora_registro <= medio_turno:
            return 0  # Entrada
        else:
            return 1  # Salida

    return 0  # Fallback
