from django.shortcuts import render
from API.models import RegistroAsistencia
from django.db.models import F
from datetime import timedelta

def tabla_biometrico(request):
    registros = RegistroAsistencia.objects.select_related('usuario').all()

    # Agrupar registros por usuario y calcular tiempo de trabajo
    usuarios_registros = {}
    for registro in registros:
        if registro.usuario not in usuarios_registros:
            usuarios_registros[registro.usuario] = {'entrada': None, 'salida': None, 'tiempo_trabajado': timedelta()}

        # Identificar si es entrada o salida
        if registro.estado == 0:  # Entrada
            usuarios_registros[registro.usuario]['entrada'] = registro.timestamp
        elif registro.estado == 1:  # Salida
            usuarios_registros[registro.usuario]['salida'] = registro.timestamp
            if usuarios_registros[registro.usuario]['entrada']:
                tiempo = registro.timestamp - usuarios_registros[registro.usuario]['entrada']
                usuarios_registros[registro.usuario]['tiempo_trabajado'] += tiempo
                usuarios_registros[registro.usuario]['entrada'] = None  # Resetear entrada después de calcular

    return render(request, 'tabla_biometrico.html', {'usuarios_registros': usuarios_registros})
