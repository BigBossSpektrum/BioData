from django.shortcuts import render
from API.models import RegistroAsistencia, UsuarioBiometrico
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now, localtime, make_aware
from collections import defaultdict
from django.db.models import Prefetch

@login_required
def home_biometrico(request):
    usuario = request.user
    hoy = now().date()

    asistencias_hoy = RegistroAsistencia.objects.filter(timestamp__date=hoy).select_related('usuario')

    return render(request, 'home.html', {
        'usuario': request.user,
        'asistencias_hoy': asistencias_hoy,
    })

def obtener_rango_semana(fecha_str):
    """
    A partir de una fecha string (YYYY-MM-DD), devuelve el lunes y domingo de esa semana.
    """
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    inicio_semana = fecha - timedelta(days=fecha.weekday())  # lunes
    fin_semana = inicio_semana + timedelta(days=6)           # domingo
    return inicio_semana, fin_semana

def historial_asistencia(request):
    registros = RegistroAsistencia.objects.select_related('usuario', 'usuario__turno')

    usuario_id = request.GET.get('usuario')
    fecha_str = request.GET.get('fecha')

    if usuario_id:
        registros = registros.filter(usuario__user_id=usuario_id)

    if fecha_str:
        inicio_semana, fin_semana = obtener_rango_semana(fecha_str)
        registros = registros.filter(timestamp__date__range=(inicio_semana, fin_semana))

    registros = registros.order_by('usuario__id', 'timestamp')

    asistencia_por_usuario_fecha = defaultdict(lambda: defaultdict(list))
    for r in registros:
        fecha = localtime(r.timestamp).date()
        asistencia_por_usuario_fecha[r.usuario][fecha].append(r)

    registros_combinados = []

    for usuario, dias in asistencia_por_usuario_fecha.items():
        for fecha, registros_dia in dias.items():
            registros_dia.sort(key=lambda r: r.timestamp)
            i = 0
            while i < len(registros_dia) - 1:
                entrada = registros_dia[i]
                salida = registros_dia[i + 1]

                if entrada.tipo == 'entrada' and salida.tipo == 'salida':
                    entrada_time = localtime(entrada.timestamp)
                    salida_time = localtime(salida.timestamp)

                    if salida_time < entrada_time:
                        salida_time += timedelta(days=1)

                    duracion = salida_time - entrada_time
                    horas = round(duracion.total_seconds() / 3600, 2)

                    # ✅ Nombre del turno
                    turno_nombre = entrada.usuario.turno.nombre if entrada.usuario.turno else "No asignado"

                    # ✅ Cálculo de horas extra
                    horas_extra = 0.0
                    if entrada.usuario.turno:
                        turno = entrada.usuario.turno
                        tzinfo = entrada_time.tzinfo

                        turno_inicio = make_aware(datetime.combine(entrada_time.date(), turno.hora_inicio), timezone=tzinfo)
                        turno_fin = make_aware(datetime.combine(entrada_time.date(), turno.hora_fin), timezone=tzinfo)

                        if turno_fin <= turno_inicio:
                            turno_fin += timedelta(days=1)

                        horas_extra_timedelta = timedelta(0)
                        if entrada_time < turno_inicio:
                            horas_extra_timedelta += turno_inicio - entrada_time
                        if salida_time > turno_fin:
                            horas_extra_timedelta += salida_time - turno_fin

                        horas_extra = round(horas_extra_timedelta.total_seconds() / 3600, 2)

                    registros_combinados.append({
                        'usuario_id': entrada.usuario.user_id,
                        'nombre': entrada.usuario.nombre,
                        'entrada': entrada_time,
                        'salida': salida_time,
                        'horas_trabajadas': horas,
                        'horas_extra': horas_extra,
                        'turno': turno_nombre,
                    })

                    i += 2
                else:
                    i += 1

    context = {
        'registros': registros_combinados,
        'usuarios': UsuarioBiometrico.objects.all(),
        'usuario_id': usuario_id,
        'fecha_seleccionada': fecha_str,
    }
    return render(request, 'tabla_biometrico.html', context)

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

def obtener_turno_por_hora(usuario, entrada_time):
    """
    Devuelve el nombre del turno al que pertenece la hora de entrada, basado en la jornada asignada al usuario.
    """
    turno = usuario.turno
    if not turno:
        return "No asignado"

    hora = entrada_time.time()
    inicio = turno.hora_inicio
    fin = turno.hora_fin

    if inicio > fin:
        # Turno nocturno (22:00 - 06:00)
        if hora >= inicio or hora <= fin:
            return "Turno Noche"
    else:
        if inicio <= hora <= fin:
            if inicio == time(6, 0):
                return "Turno Mañana"
            elif inicio == time(14, 0):
                return "Turno Tarde"
            else:
                return "Turno Día"

    return "Desconocido"


def calcular_horas_trabajadas():
    registros = RegistroAsistencia.objects.select_related('usuario__turno').order_by('usuario__id', 'timestamp')
    
    # Agrupamos registros por usuario y día
    asistencia_por_usuario = defaultdict(lambda: defaultdict(list))

    for r in registros:
        fecha = localtime(r.timestamp).date()
        asistencia_por_usuario[r.usuario][fecha].append(localtime(r.timestamp))
    
    resumen_horas = []

    for usuario, dias in asistencia_por_usuario.items():
        for fecha, timestamps in dias.items():
            timestamps.sort()
            total_trabajado = timedelta()
            
            for i in range(0, len(timestamps) - 1, 2):
                entrada = timestamps[i]
                salida = timestamps[i + 1] if i + 1 < len(timestamps) else None

                if salida:
                    # Si el turno cruza medianoche, ajustamos la salida
                    if salida < entrada:
                        salida += timedelta(days=1)
                    total_trabajado += (salida - entrada)

            resumen_horas.append({
                'usuario': usuario.nombre,
                'fecha': fecha.strftime('%Y-%m-%d'),
                'horas_trabajadas': round(total_trabajado.total_seconds() / 3600, 2)
            })

    return resumen_horas