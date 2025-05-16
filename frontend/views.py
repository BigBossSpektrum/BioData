from django.shortcuts import render
from API.models import RegistroAsistencia
from datetime import timedelta

def home(request):
    return render(request, 'home.html')

def tabla_biometrico(request):
    registros = RegistroAsistencia.objects.select_related('usuario').order_by('usuario__user_id', 'timestamp')

    # Agrupar por usuario para resumen
    usuarios_registros = {}
    for registro in registros:
        usuario = registro.usuario
        if usuario not in usuarios_registros:
            usuarios_registros[usuario] = {
                'entrada': None,
                'salida': None,
                'tiempo_trabajado': timedelta()
            }

        if registro.estado == 0:  # Entrada
            usuarios_registros[usuario]['entrada'] = registro.timestamp
        elif registro.estado == 1:  # Salida
            usuarios_registros[usuario]['salida'] = registro.timestamp
            if usuarios_registros[usuario]['entrada']:
                tiempo = registro.timestamp - usuarios_registros[usuario]['entrada']
                usuarios_registros[usuario]['tiempo_trabajado'] += tiempo
                usuarios_registros[usuario]['entrada'] = None  # Reiniciar para siguiente ciclo

    return render(request, 'tabla_biometrico.html', {
        'usuarios_registros': usuarios_registros
    })


def historial_asistencia(request):
    registros = RegistroAsistencia.objects.select_related('usuario').order_by('-timestamp')
    return render(request, 'historial_asistencia.html', {
        'registros': registros
    })
