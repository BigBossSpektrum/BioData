from django.shortcuts import render
from API.models import RegistroAsistencia, UsuarioBiometrico
from datetime import datetime, timedelta, time
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

def filtrar_asistencias(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    usuario_id = request.GET.get('usuario')

    registros = RegistroAsistencia.objects.all().order_by('-fecha')

    # Filtro por usuario (si se selecciona uno)
    if usuario_id:
        registros = registros.filter(usuario__user_id=usuario_id)

    # Filtro por fechas
    if fecha_inicio:
        try:
            inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            registros = registros.filter(fecha__gte=inicio)
        except ValueError:
            pass

    if fecha_fin:
        try:
            fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            fin_con_hora = datetime.combine(fin, time.max)  # 23:59:59.999999
            registros = registros.filter(fecha__lte=fin_con_hora)
        except ValueError:
            pass

    # Obtener todos los usuarios para el select del formulario
    usuarios = UsuarioBiometrico.objects.all()

    context = {
        'registros': registros,
        'usuarios': usuarios,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'usuario_id': usuario_id
    }

    return render(request, 'tabla_biometrico.html', context)

def detectar_turno(entrada_time):
    hora = entrada_time.time()
    if time(6, 0) <= hora < time(14, 0):
        return "Turno 1"
    elif time(14, 0) <= hora < time(22, 0):
        return "Turno 2"
    else:
        return "Turno 3"

def historial_asistencia(request):
    registros = RegistroAsistencia.objects.select_related('usuario')

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

                    # ✅ Detectar turno automáticamente
                    turno_detectado = detectar_turno(entrada_time)

                    # ✅ Cálculo de horas extra por turno
                    horas_extra = 0.0
                    if turno_detectado == "Turno 1":
                        turno_inicio = make_aware(datetime.combine(entrada_time.date(), time(6, 0)), timezone=entrada_time.tzinfo)
                        turno_fin = make_aware(datetime.combine(entrada_time.date(), time(14, 0)), timezone=entrada_time.tzinfo)
                    elif turno_detectado == "Turno 2":
                        turno_inicio = make_aware(datetime.combine(entrada_time.date(), time(14, 0)), timezone=entrada_time.tzinfo)
                        turno_fin = make_aware(datetime.combine(entrada_time.date(), time(22, 0)), timezone=entrada_time.tzinfo)
                    else:  # Turno 3
                        turno_inicio = make_aware(datetime.combine(entrada_time.date(), time(22, 0)), timezone=entrada_time.tzinfo)
                        turno_fin = make_aware(datetime.combine(entrada_time.date() + timedelta(days=1), time(6, 0)), timezone=entrada_time.tzinfo)

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
                        'turno': turno_detectado,
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

"""FUNCION PARA DETECTAR SI ES ENTRADA O SALIDA"""
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


"""FUNCION PARA DETECTAR EL TURNOS DE ACUERDO A LA HORA"""
def detectar_turno_por_hora(hora: time) -> str:
    """
    Detecta automáticamente el turno laboral según la hora proporcionada.

    Parámetros:
        hora (datetime.time): Hora de entrada o salida.

    Retorna:
        str: Nombre del turno detectado.
    """
    if time(6, 0) <= hora < time(14, 0):
        return "Turno Mañana"
    elif time(14, 0) <= hora < time(22, 0):
        return "Turno Tarde"
    elif hora >= time(22, 0) or hora < time(6, 0):
        return "Turno Noche"
    else:
        return "Desconocido"


"""FUNCION PARA CONSIDERAR LOS TURNOS DE LOS USUARIOS COMO PRIORIDAD"""
def procesar_registros_asistencia(registros):
    registros_por_usuario = defaultdict(list)

    # Agrupar por usuario
    for registro in registros:
        user_id = registro['usuario']['user_id']
        registros_por_usuario[user_id].append(registro)

    resumen_jornadas = []

    for user_id, lista_registros in registros_por_usuario.items():
        # Ordenar por timestamp
        lista_ordenada = sorted(lista_registros, key=lambda r: r['timestamp'])

        i = 0
        while i < len(lista_ordenada):
            registro_entrada = lista_ordenada[i]
            entrada_time = datetime.fromisoformat(registro_entrada['timestamp'])

            if registro_entrada['tipo'] != 'entrada':
                i += 1
                continue  # saltamos registros huérfanos de tipo "salida" sin entrada previa

            # Buscar siguiente salida del mismo usuario
            salida_time = None
            for j in range(i+1, len(lista_ordenada)):
                if lista_ordenada[j]['tipo'] == 'salida':
                    salida_time = datetime.fromisoformat(lista_ordenada[j]['timestamp'])
                    i = j  # saltamos al índice de la salida
                    break
            else:
                i += 1
                continue  # si no hay salida, no procesamos jornada

            turno = detectar_turno_por_hora(entrada_time.time())
            duracion = salida_time - entrada_time

            resumen_jornadas.append({
                "usuario": registro_entrada['usuario']['nombre'],
                "fecha": entrada_time.date().isoformat(),
                "hora_entrada": entrada_time.time().isoformat(timespec='minutes'),
                "hora_salida": salida_time.time().isoformat(timespec='minutes'),
                "turno": turno,
                "tiempo_trabajado": str(duracion)
            })

            i += 1

    return resumen_jornadas


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