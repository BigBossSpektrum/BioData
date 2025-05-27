from django.shortcuts import render
from API.models import RegistroAsistencia
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

@login_required
def home_biometrico(request):
    usuario = request.user
    hoy = now().date()

    asistencias_hoy = RegistroAsistencia.objects.filter(timestamp__date=hoy).select_related('usuario')

    return render(request, 'home.html', {
        'usuario': usuario,
        'asistencias_hoy': asistencias_hoy,
    })


def historial_asistencia(request):
    registros = RegistroAsistencia.objects.select_related('usuario').order_by('-timestamp')
    return render(request, 'tabla_biometrico.html', {
        'registros': registros
    })
    
def determinar_estado_por_turno(usuario, timestamp):
    """
    Determina si el registro es entrada (0) o salida (1) según la jornada laboral asignada.
    """
    if not usuario.turno:
        return 0  # Si no hay turno asignado, lo tratamos como entrada

    hora = timestamp.time()
    inicio = usuario.turno.hora_inicio
    fin = usuario.turno.hora_fin

    # Turno nocturno (ej: 22:00 a 06:00 del día siguiente)
    if inicio > fin:
        if hora >= inicio or hora <= fin:
            return 0 if hora >= inicio else 1
    else:
        # Turno normal (ej: 06:00 a 14:00)
        medio = (
            datetime.combine(datetime.today(), inicio) +
            (datetime.combine(datetime.today(), fin) - datetime.combine(datetime.today(), inicio)) / 2
        ).time()

        return 0 if hora <= medio else 1  # 0 = entrada, 1 = salida

    return 0  # fallback