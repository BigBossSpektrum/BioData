"""
Utilidades para filtros de datos por roles de usuario
"""
from API.models import EstacionServicio


def aplicar_filtro_jefe_patio(queryset, usuario, campo_estacion='estacion_servicio'):
    """
    Aplica filtro por estación para jefe de patio.
    
    Args:
        queryset: QuerySet a filtrar
        usuario: Usuario logueado
        campo_estacion: Nombre del campo de relación con EstacionServicio (default: 'estacion_servicio')
    
    Returns:
        QuerySet filtrado
    """
    if hasattr(usuario, 'rol') and usuario.rol == 'jefe_patio':
        estacion_jefe = EstacionServicio.objects.filter(jefe=usuario).first()
        if estacion_jefe:
            # Crear el filtro dinámicamente usando el nombre del campo
            filtro = {campo_estacion: estacion_jefe}
            return queryset.filter(**filtro)
        else:
            # Si no tiene estación asignada, no mostrar nada
            return queryset.none()
    return queryset


def obtener_info_estacion_jefe(usuario):
    """
    Obtiene información de la estación asignada al jefe de patio.
    
    Args:
        usuario: Usuario logueado
    
    Returns:
        dict: Información sobre la estación y si es jefe de patio
    """
    es_jefe_patio = hasattr(usuario, 'rol') and usuario.rol == 'jefe_patio'
    estacion_filtrada = None
    
    if es_jefe_patio:
        estacion_jefe = EstacionServicio.objects.filter(jefe=usuario).first()
        if estacion_jefe:
            estacion_filtrada = estacion_jefe.nombre
    
    return {
        'es_jefe_patio': es_jefe_patio,
        'estacion_filtrada': estacion_filtrada
    }
