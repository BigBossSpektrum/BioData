from datetime import datetime, timedelta

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
