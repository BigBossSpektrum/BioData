from django import template
from API.models import decimal_a_tiempo

register = template.Library()

@register.filter
def horas_formato(value):
    """
    Convierte horas decimales a formato HH:MM
    Uso en plantilla: {{ horas_trabajadas|horas_formato }}
    """
    try:
        return decimal_a_tiempo(float(value))
    except (ValueError, TypeError):
        return "00:00"

@register.filter  
def tiempo_decimal(value):
    """
    Convierte formato HH:MM a decimal
    Uso en plantilla: {{ "08:30"|tiempo_decimal }}
    """
    try:
        horas, minutos = map(int, str(value).split(':'))
        return horas + (minutos / 60)
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def calcular_horas_usuario(usuario, fecha):
    """
    Calcula las horas de un usuario para una fecha específica
    Uso en plantilla: {% calcular_horas_usuario usuario fecha as calculo %}
    """
    if hasattr(usuario, 'calcular_horas_dia'):
        return usuario.calcular_horas_dia(fecha)
    return {
        'horas_trabajadas': 0,
        'horas_extras': 0,
        'horas_trabajadas_formato': '00:00',
        'horas_extras_formato': '00:00',
        'horas_normales_formato': '08:00'
    }

@register.inclusion_tag('partials/badge_horas_extras.html')
def badge_horas_extras(horas_extras):
    """
    Muestra un badge para horas extras
    """
    return {
        'horas_extras': horas_extras,
        'tiene_extras': horas_extras > 0,
        'formato': decimal_a_tiempo(horas_extras)
    }
