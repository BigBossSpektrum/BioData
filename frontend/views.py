from django.shortcuts import render
from API.models import RegistroAsistencia, UsuarioBiometrico
from datetime import datetime, timedelta, time
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now, localtime, make_aware
from collections import defaultdict
from django.utils import timezone
from .utils import obtener_rango_semana
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse

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

    registros = RegistroAsistencia.objects.select_related('usuario').all().order_by('timestamp')

    # Filtro por usuario (si se selecciona uno)
    if usuario_id:
        registros = registros.filter(usuario__user_id=usuario_id)

    # Filtro por fechas
    if fecha_inicio:
        try:
            inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            registros = registros.filter(timestamp__date__gte=inicio)
        except ValueError:
            pass

    if fecha_fin:
        try:
            fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            registros = registros.filter(timestamp__date__lte=fin)
        except ValueError:
            pass

    # Agrupa y combina registros como en historial_asistencia
    asistencia_por_usuario_fecha = defaultdict(lambda: defaultdict(list))
    for r in registros:
        fecha = r.timestamp.date()
        asistencia_por_usuario_fecha[r.usuario][fecha].append(r)

    registros_combinados = []
    for dias in asistencia_por_usuario_fecha.values():
        for fecha, registros_dia in dias.items():
            registros_dia.sort(key=lambda r: r.timestamp)
            i = 0
            while i < len(registros_dia):
                entrada = registros_dia[i]
                if entrada.tipo != 'entrada':
                    i += 1
                    continue  # Solo nos interesan las entradas

                # Busca la siguiente salida
                salida = None
                for j in range(i + 1, len(registros_dia)):
                    if registros_dia[j].tipo == 'salida':
                        salida = registros_dia[j]
                        break

                if salida:
                    entrada_time = entrada.timestamp
                    salida_time = salida.timestamp
                    if salida_time < entrada_time:
                        salida_time += timedelta(days=1)
                    duracion = salida_time - entrada_time
                    horas = round(duracion.total_seconds() / 3600, 2)
                    turno_detectado = detectar_turno(entrada_time)

                    # Cálculo de horas extra por turno (igual que antes)
                    horas_extra = 0.0
                    # Nuevo cálculo basado en el turno asignado al usuario
                    if entrada.usuario.turno:
                        turno_inicio = entrada.usuario.turno.hora_inicio
                        turno_fin = entrada.usuario.turno.hora_fin
                        # Duración del turno en horas
                        if turno_inicio < turno_fin:
                            duracion_turno = (datetime.combine(entrada_time.date(), turno_fin) - datetime.combine(entrada_time.date(), turno_inicio)).total_seconds() / 3600
                        else:
                            # Turno nocturno (ej: 22:00 a 06:00)
                            duracion_turno = ((datetime.combine(entrada_time.date(), time(23,59,59)) - datetime.combine(entrada_time.date(), turno_inicio)).total_seconds() + (datetime.combine(entrada_time.date() + timedelta(days=1), turno_fin) - datetime.combine(entrada_time.date() + timedelta(days=1), time(0,0,0))).total_seconds() + 1) / 3600
                        if horas > duracion_turno:
                            horas_extra = round(horas - duracion_turno, 2)
                        else:
                            horas_extra = 0.0
                    else:
                        # Si no tiene turno asignado, usar el cálculo anterior por horario
                        if turno_detectado == "Turno 1":
                            turno_inicio = timezone.make_aware(datetime.combine(entrada_time.date(), time(6, 0)))
                            turno_fin = timezone.make_aware(datetime.combine(entrada_time.date(), time(14, 0)))
                        elif turno_detectado == "Turno 2":
                            turno_inicio = timezone.make_aware(datetime.combine(entrada_time.date(), time(14, 0)))
                            turno_fin = timezone.make_aware(datetime.combine(entrada_time.date(), time(22, 0)))
                        else:  # Turno 3
                            turno_inicio = timezone.make_aware(datetime.combine(entrada_time.date(), time(22, 0)))
                            turno_fin = timezone.make_aware(datetime.combine(entrada_time.date() + timedelta(days=1), time(6, 0)))
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
                    })
                    # Salta al registro después de la salida encontrada
                    i = registros_dia.index(salida) + 1
                else:
                    # No hay salida después de esta entrada
                    i += 1

    usuarios = UsuarioBiometrico.objects.all()

    context = {
        'registros': registros_combinados,
        'usuarios': usuarios,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'usuario_id': usuario_id
    }

    return render(request, 'tabla_biometrico.html', context)

def historial_asistencia(request):
    nombre = request.GET.get('nombre')
    dni = request.GET.get('dni')
    estacion = request.GET.get('estacion')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    registros = RegistroAsistencia.objects.select_related('usuario', 'usuario__estacion').all()

    if nombre:
        registros = registros.filter(usuario__nombre__icontains=nombre)
    if dni:
        registros = registros.filter(usuario__dni__icontains=dni)
    if estacion:
        registros = registros.filter(usuario__estacion__nombre__icontains=estacion)
    if fecha_inicio:
        registros = registros.filter(timestamp__date__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(timestamp__date__lte=fecha_fin)

    registros = registros.order_by('usuario__id', 'timestamp')
    asistencia_por_usuario_fecha = defaultdict(lambda: defaultdict(list))
    for r in registros:
        fecha = r.timestamp.date()
        asistencia_por_usuario_fecha[r.usuario][fecha].append(r)

    registros_combinados = []
    for usuario, dias in asistencia_por_usuario_fecha.items():
        for fecha, registros_dia in dias.items():
            registros_dia.sort(key=lambda r: r.timestamp)
            entradas = [localtime(r.timestamp) for r in registros_dia if r.tipo == 'entrada']
            salidas = [localtime(r.timestamp) for r in registros_dia if r.tipo == 'salida']
            # Emparejar entradas y salidas correctamente, incluso si la salida es al día siguiente
            i, j = 0, 0
            while i < len(entradas):
                entrada = entradas[i]
                salida = None
                # Buscar la primera salida después de la entrada (puede ser al día siguiente)
                for k in range(j, len(salidas)):
                    posible_salida = salidas[k]
                    # Turno nocturno: entrada >= 22:00 y salida al día siguiente entre 0:00 y 12:00
                    if entrada.hour >= 22 and posible_salida > entrada and (
                        posible_salida.date() == (entrada + timedelta(days=1)).date() and posible_salida.hour <= 12
                    ):
                        salida = posible_salida
                        j = k + 1
                        break
                    # Lógica normal: salida después de entrada
                    elif posible_salida > entrada:
                        salida = posible_salida
                        j = k + 1
                        break
                horas_trabajadas = 0.0
                if salida:
                    delta = salida - entrada
                    if delta.total_seconds() < 0:
                        delta += timedelta(days=1)
                    horas_trabajadas = round(delta.total_seconds() / 3600, 2)
                horas_extra = 0.0
                if horas_trabajadas > 8:
                    horas_extra = round(horas_trabajadas - 8, 2)
                aprobados = [r.aprobado for r in registros_dia]
                aprobado = None
                if aprobados:
                    if all(a is True for a in aprobados):
                        aprobado = True
                    elif any(a is False for a in aprobados):
                        aprobado = False
                    else:
                        aprobado = None
                registros_combinados.append({
                    'dia': entrada.date().strftime('%Y-%m-%d'),
                    'usuario_id': usuario.id,
                    'nombre': usuario.nombre,
                    'dni': usuario.dni,
                    'estacion': usuario.estacion.nombre if usuario.estacion else '',
                    'entrada': entrada,
                    'salida': salida,
                    'horas_trabajadas': horas_trabajadas if salida else None,
                    'horas_extra': horas_extra if salida else None,
                    'aprobado': aprobado,
                })
                i += 1

    context = {
        'registros': registros_combinados,
        'usuarios': UsuarioBiometrico.objects.all(),
        'nombre': nombre,
        'dni': dni,
        'estacion': estacion,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
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

@login_required
def resumen_asistencias_diarias(request):
    nombre = request.GET.get('nombre')
    dni = request.GET.get('dni')
    estacion = request.GET.get('estacion')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    registros_qs = RegistroAsistencia.objects.select_related('usuario', 'usuario__turno', 'usuario__estacion').all()

    if nombre:
        registros_qs = registros_qs.filter(usuario__nombre__icontains=nombre)
    if dni:
        registros_qs = registros_qs.filter(usuario__dni__icontains=dni)
    if estacion:
        registros_qs = registros_qs.filter(usuario__estacion__nombre__icontains=estacion)
    if fecha_inicio:
        registros_qs = registros_qs.filter(timestamp__date__gte=fecha_inicio)
    if fecha_fin:
        registros_qs = registros_qs.filter(timestamp__date__lte=fecha_fin)

    registros_qs = registros_qs.order_by('usuario__id', 'timestamp')
    asistencia_por_usuario_fecha = defaultdict(lambda: defaultdict(list))
    for r in registros_qs:
        fecha = localtime(r.timestamp).date()
        asistencia_por_usuario_fecha[r.usuario][fecha].append(r)

    registros = []
    for usuario, dias in asistencia_por_usuario_fecha.items():
        fechas_ordenadas = sorted(dias.keys())
        for idx, fecha in enumerate(fechas_ordenadas):
            registros_dia = dias[fecha]
            registros_dia.sort(key=lambda r: r.timestamp)
            entradas = [localtime(r.timestamp) for r in registros_dia if r.tipo == 'entrada']
            salidas = [localtime(r.timestamp) for r in registros_dia if r.tipo == 'salida']
            # Para turnos nocturnos, también buscar salidas en el siguiente día
            if idx + 1 < len(fechas_ordenadas):
                next_fecha = fechas_ordenadas[idx + 1]
                next_registros_dia = dias[next_fecha]
                salidas += [localtime(r.timestamp) for r in next_registros_dia if r.tipo == 'salida']
            i, j = 0, 0
            while i < len(entradas):
                entrada = entradas[i]
                salida = None
                while j < len(salidas):
                    posible_salida = salidas[j]
                    # Lógica especial para turnos nocturnos: si entrada >= 22:00 y salida <= 12:00 del día siguiente
                    if entrada.hour >= 22 and (
                        (posible_salida.date() == (entrada + timedelta(days=1)).date() and posible_salida.hour <= 12)
                    ):
                        salida = posible_salida
                        j += 1
                        break
                    elif posible_salida > entrada:
                        salida = posible_salida
                        j += 1
                        break
                    j += 1
                horas_trabajadas = 0.0
                if salida:
                    delta = salida - entrada
                    if delta.total_seconds() < 0:
                        delta += timedelta(days=1)
                    horas_trabajadas = round(delta.total_seconds() / 3600, 2)
                horas_extra = 0.0
                if horas_trabajadas > 8:
                    horas_extra = round(horas_trabajadas - 8, 2)
                aprobados = [r.aprobado for r in registros_dia]
                aprobado = None
                if aprobados:
                    if all(a is True for a in aprobados):
                        aprobado = True
                    elif any(a is False for a in aprobados):
                        aprobado = False
                    else:
                        aprobado = None
                registros.append({
                    'dia': entrada.date().strftime('%Y-%m-%d'),
                    'usuario_id': usuario.id,
                    'nombre': usuario.nombre,
                    'dni': usuario.dni,
                    'estacion': usuario.estacion.nombre if usuario.estacion else '',
                    'entrada': entrada,
                    'salida': salida,
                    'horas_trabajadas': horas_trabajadas if salida else None,
                    'horas_extra': horas_extra if salida else None,
                    'aprobado': aprobado,
                })
                i += 1

    context = {
        'registros': registros,
        'nombre': nombre,
        'dni': dni,
        'estacion': estacion,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'resumen_asistencias_diarias.html', {'registros': registros, 'nombre': nombre, 'dni': dni, 'estacion': estacion, 'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin})

@login_required
def aprobar_horas_extra(request, usuario_id, dia):
    if request.method == 'POST' and hasattr(request.user, 'rol') and request.user.rol == 'jefe_patio':
        try:
            usuario = UsuarioBiometrico.objects.get(id=usuario_id, jefe=request.user)
        except UsuarioBiometrico.DoesNotExist:
            print("[APROBACION] Usuario no autorizado para este jefe de patio")
            return HttpResponseForbidden("No autorizado para este usuario")
        fecha = datetime.strptime(dia, '%Y-%m-%d').date()
        from datetime import time
        from django.utils.timezone import make_aware
        inicio_dia = make_aware(datetime.combine(fecha, time.min))
        fin_dia = make_aware(datetime.combine(fecha, time.max))
        # Log de todos los registros de ese usuario
        registros = RegistroAsistencia.objects.filter(usuario_id=usuario_id)
        for r in registros:
            print(f"[APROBACION-DEBUG] Registro: {r.id}, fecha: {r.timestamp.date()}, aprobado: {r.aprobado}")
        qs = RegistroAsistencia.objects.filter(
            usuario_id=int(usuario_id),
            timestamp__gte=inicio_dia,
            timestamp__lte=fin_dia
        )
        print(f"[APROBACION] Registros encontrados para usuario {usuario_id} en {fecha}: {qs.count()}")
        for r in qs:
            print(f"[APROBACION-ENCONTRADO] Registro: {r.id}, fecha: {r.timestamp.date()}, aprobado: {r.aprobado}")
        updated = qs.update(aprobado=True)
        print(f"[APROBACION] Registros actualizados para usuario {usuario_id} en {fecha}: {updated}")
        return HttpResponseRedirect(reverse('resumen_asistencias_diarias') + '?aprobado=1')
    print("[APROBACION] Intento de acceso no autorizado o método incorrecto")
    return HttpResponseForbidden("No autorizado")