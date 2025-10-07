from django import template

register = template.Library()

@register.filter
def count_nocturno(usuarios_finales):
    """Cuenta el número de usuarios con turno nocturno"""
    return len([item for item in usuarios_finales if item.get('es_nocturno', False)])

@register.filter  
def count_diurno(usuarios_finales):
    """Cuenta el número de usuarios con turno diurno"""
    return len([item for item in usuarios_finales if not item.get('es_nocturno', False)])

@register.filter
def count_con_salida_previa(usuarios_finales):
    """Cuenta el número de usuarios que tienen salida del día anterior o salida de turno nocturno"""
    return len([item for item in usuarios_finales if item.get('salida_ayer') or item.get('salida')])
