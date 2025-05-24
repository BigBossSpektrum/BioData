from django.shortcuts import render
from API.models import RegistroAsistencia
from datetime import timedelta
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'home.html')

def tabla_biometrico(request):
    registros = RegistroAsistencia.objects.select_related('usuario').order_by('usuario__id', 'timestamp')

    usuarios_registros = {}
    for registro in registros:
        usuario = registro.usuario

        if usuario not in usuarios_registros:
            usuarios_registros[usuario] = {
                'entrada': None,
                'salida': None,
                'tiempo_trabajado': timedelta()
            }

        # Nueva lógica basada en el turno
        estado_determinado = determinar_estado_por_turno(usuario, registro.timestamp)

        if estado_determinado == 0:  # Entrada
            usuarios_registros[usuario]['entrada'] = registro.timestamp
        elif estado_determinado == 1:  # Salida
            usuarios_registros[usuario]['salida'] = registro.timestamp
            if usuarios_registros[usuario]['entrada']:
                tiempo = registro.timestamp - usuarios_registros[usuario]['entrada']
                usuarios_registros[usuario]['tiempo_trabajado'] += tiempo
                usuarios_registros[usuario]['entrada'] = None

    return render(request, 'tabla_biometrico.html', {
        'usuarios_registros': usuarios_registros
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