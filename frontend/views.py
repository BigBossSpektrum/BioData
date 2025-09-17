from django.shortcuts import render, redirect, get_object_or_404
from API.models import RegistroAsistencia, UsuarioBiometrico, EstacionServicio, JornadaLaboral, JornadaEspecial, ResumenSemanal, TarifaHoraExtra, FeriadoNacional
from API.Biometricos_connections import detectar_turno
from datetime import datetime, timedelta, time, date
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now, localtime, make_aware
from collections import defaultdict
from django.utils import timezone
from django.db.models import Q
from .utils import obtener_rango_semana, es_turno_nocturno, calcular_diferencia_dias_turno_nocturno, detectar_tipo_turno_detallado, validar_y_emparejar_turno_nocturno, calcular_horas_con_horarios_estandar, procesar_turno_nocturno_con_siguiente_registro, verificar_registros_ya_procesados_en_turno_nocturno
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from .utils_filters import aplicar_filtro_jefe_patio, obtener_info_estacion_jefe
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib import messages

import logging

@login_required
def home_biometrico(request):
    logger = logging.getLogger(__name__)
    hoy = localtime(now()).date()
    ayer = hoy - timedelta(days=1)

    try:
        rol = getattr(request.user, 'rol', None)
        registros = RegistroAsistencia.objects.select_related(
            'user', 'user__estacion', 'user__estacion__jefe'
        ).all()

        # Agregar timestamp_local a cada registro
        for r in registros:
            r.timestamp_local = localtime(r.timestamp)

        registros_hoy = [r for r in registros if r.timestamp_local.date() == hoy]
        registros_ayer = [r for r in registros if r.timestamp_local.date() == ayer]

        if rol == 'jefe_patio':
            registros_hoy = [
                r for r in registros_hoy
                if r.user.estacion and getattr(r.user.estacion, 'jefe_id', None) == request.user.id
            ]
            registros_ayer = [
                r for r in registros_ayer
                if r.user.estacion and getattr(r.user.estacion, 'jefe_id', None) == request.user.id
            ]

        # Obtener primera entrada de hoy
        entradas_hoy_por_usuario = {}
        for r in registros_hoy:
            uid = r.user.id
            if uid not in entradas_hoy_por_usuario or r.timestamp_local < entradas_hoy_por_usuario[uid].timestamp_local:
                entradas_hoy_por_usuario[uid] = r

        # Última salida válida de ayer
        salidas_ayer_por_usuario = {}
        for r in registros_ayer:
            uid = r.user.id
            if uid not in salidas_ayer_por_usuario or r.timestamp_local > salidas_ayer_por_usuario[uid].timestamp_local:
                salidas_ayer_por_usuario[uid] = r

        usuarios_finales = []
        for uid, entrada in entradas_hoy_por_usuario.items():
            salida_ayer = salidas_ayer_por_usuario.get(uid)
            entrada_time = entrada.timestamp_local

            salida_valida = None
            if salida_ayer:
                salida_time = salida_ayer.timestamp_local
                delta = entrada_time - salida_time
                if timedelta(hours=0) <= delta <= timedelta(hours=8):
                    salida_valida = salida_ayer

            usuarios_finales.append({
                'usuario': entrada.user,
                'entrada': entrada,
                'salida_ayer': salida_valida,  # Puede ser None
                'estacion': entrada.estacion_servicio.nombre if entrada.estacion_servicio else None,

            })

        usuarios_finales.sort(key=lambda x: x['usuario'].nombre)

        return render(request, 'home.html', {
            'usuario': request.user,
            'usuarios_finales': usuarios_finales,
            'today': hoy,
        })

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error en home_biometrico: {e}")
        return render(request, 'home.html', {
            'usuario': request.user,
            'usuarios_finales': [],
            'today': hoy,
            'error': str(e),
        })
    
def filtrar_asistencias(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    usuario_id = request.GET.get('usuario')

    registros = RegistroAsistencia.objects.select_related('user').all().order_by('timestamp')
    
    # Filtro por jefe de patio - solo ver registros de su estación asignada
    registros = aplicar_filtro_jefe_patio(registros, request.user)

    # Filtro por usuario (si se selecciona uno)
    if usuario_id:
        registros = registros.filter(user__id=usuario_id)

    # Filtro por fechas
    if fecha_inicio:
        try:
            from django.utils import timezone
            inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            inicio_aware = timezone.make_aware(datetime.combine(inicio.date(), datetime.min.time()))
            registros = registros.filter(timestamp__gte=inicio_aware)
        except ValueError:
            pass

    if fecha_fin:
        try:
            from django.utils import timezone
            fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            fin_aware = timezone.make_aware(datetime.combine(fin.date(), datetime.max.time()))
            registros = registros.filter(timestamp__lte=fin_aware)
        except ValueError:
            pass

    # Agrupa y combina registros como en historial_asistencia
    asistencia_por_usuario_fecha = defaultdict(lambda: defaultdict(list))
    for r in registros:
        fecha = r.timestamp.date()
        asistencia_por_usuario_fecha[r.user][fecha].append(r)

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
                    
                    # Usar la nueva función que considera horarios estándar
                    calculo = calcular_horas_con_horarios_estandar(entrada_time, salida_time)
                    horas = calculo['horas_trabajadas']
                    horas_extra = calculo['horas_extras']
                    
                    turno_detectado = detectar_turno(entrada_time)

                    registros_combinados.append({
                        'usuario_id': entrada.user.id,
                        'nombre': entrada.user.nombre,
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
    
    # Filtrar usuarios para jefe de patio - solo mostrar usuarios de su estación
    usuarios = aplicar_filtro_jefe_patio(usuarios, request.user, 'estacion')

    # Obtener información de estación para el contexto
    info_estacion = obtener_info_estacion_jefe(request.user)

    context = {
        'registros': registros_combinados,
        'usuarios': usuarios,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'usuario_id': usuario_id,
        **info_estacion
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

            turno = detectar_turno(entrada_time.time())
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
    registros = RegistroAsistencia.objects.select_related('user__turno').order_by('user__id', 'timestamp')
    
    # Agrupamos registros por usuario y día
    asistencia_por_usuario = defaultdict(lambda: defaultdict(list))

    for r in registros:
        fecha = localtime(r.timestamp).date()
        asistencia_por_usuario[r.user][fecha].append(localtime(r.timestamp))

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
    from django.utils import timezone
    from datetime import datetime
    
    nombre = request.GET.get('nombre')
    estacion = request.GET.get('estacion')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    registros_qs = RegistroAsistencia.objects.select_related('user', 'user__estacion').all()
    
    # Filtro por jefe de patio - solo ver registros de su estación asignada
    registros_qs = aplicar_filtro_jefe_patio(registros_qs, request.user)

    if nombre:
        registros_qs = registros_qs.filter(user__nombre__icontains=nombre)
    if estacion:
        registros_qs = registros_qs.filter(estacion_servicio__nombre__icontains=estacion)
    
    # CORRECCIÓN: Usar rangos timezone-aware en lugar de timestamp__date
    if fecha_inicio:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_inicio_aware = timezone.make_aware(datetime.combine(fecha_inicio_dt.date(), datetime.min.time()))
        registros_qs = registros_qs.filter(timestamp__gte=fecha_inicio_aware)
    if fecha_fin:
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        fecha_fin_aware = timezone.make_aware(datetime.combine(fecha_fin_dt.date(), datetime.max.time()))
        registros_qs = registros_qs.filter(timestamp__lte=fecha_fin_aware)

    registros_qs = registros_qs.order_by('user__id', 'timestamp')

    asistencia_por_usuario_fecha = defaultdict(lambda: defaultdict(list))
    for r in registros_qs:
        fecha = localtime(r.timestamp).date()
        asistencia_por_usuario_fecha[r.user][fecha].append(r)

    registros = []
    for usuario, dias in asistencia_por_usuario_fecha.items():
        # Procesar cada fecha directamente usando el método corregido del modelo
        fechas_ordenadas = sorted(dias.keys())
        
        for fecha in fechas_ordenadas:
            registros_dia = dias[fecha]
            
            # NUEVA LÓGICA ESPECIAL PARA TURNOS NOCTURNOS:
            # Primero verificar si hay entrada nocturna y buscar salida en día siguiente
            resultado_nocturno = procesar_turno_nocturno_con_siguiente_registro(
                asistencia_por_usuario_fecha, usuario, fecha
            )
            
            if resultado_nocturno:
                # Es un turno nocturno válido con posible salida al día siguiente
                entrada = resultado_nocturno['entrada']
                salida = resultado_nocturno['salida']
                horas_trabajadas = resultado_nocturno['horas_trabajadas']
                horas_extra = resultado_nocturno['horas_extra']
                info_turno = resultado_nocturno['info_turno']
                mensaje_emparejamiento = resultado_nocturno['mensaje']
                horas_normales = horas_trabajadas - horas_extra if horas_trabajadas > 0 else 0.0
                es_turno_nocturno_flag = True
            else:
                # VERIFICAR SI LOS REGISTROS DE ESTE DÍA YA FUERON PROCESADOS EN UN TURNO NOCTURNO ANTERIOR
                registros_ya_procesados = verificar_registros_ya_procesados_en_turno_nocturno(
                    asistencia_por_usuario_fecha, usuario, fecha
                )
                
                if registros_ya_procesados:
                    # Los registros de este día ya fueron utilizados en un turno nocturno anterior
                    # No mostrar este registro para evitar duplicación
                    continue
                
                # Usar el método normal del modelo para turnos diurnos
                calculo_modelo = usuario.calcular_horas_dia(fecha)
                
                # Extraer información del cálculo del modelo
                entrada = calculo_modelo.get('entrada')
                salida = calculo_modelo.get('salida')
                horas_trabajadas = calculo_modelo.get('horas_trabajadas', 0.0)
                horas_normales = calculo_modelo.get('horas_normales', 0.0)
                horas_extra = calculo_modelo.get('horas_extras', 0.0)
                es_turno_nocturno_flag = calculo_modelo.get('es_turno_nocturno', False)
                
                # Convertir timestamps de modelo a datetime locales si es necesario
                if entrada and hasattr(entrada, 'timestamp'):
                    entrada = localtime(entrada.timestamp)
                if salida and hasattr(salida, 'timestamp'):
                    salida = localtime(salida.timestamp)

                # Detectar tipo de turno usando la nueva funcionalidad
                info_turno = detectar_tipo_turno_detallado(entrada, salida if salida else None)
                
                # Mensaje de emparejamiento por defecto
                if entrada and salida:
                    mensaje_emparejamiento = "Turno diurno normal"
                elif entrada and not salida:
                    mensaje_emparejamiento = "Sin salida registrada"
                elif not entrada and salida:
                    mensaje_emparejamiento = "Sin entrada registrada"
                else:
                    mensaje_emparejamiento = "Ausente"
            
            # Mantener compatibilidad con resultado_turno si se requiere
            resultado_turno = None
            if horas_trabajadas > 0:
                resultado_turno = {
                    'duracion_horas': horas_trabajadas,
                    'diferencia_dias': 1 if es_turno_nocturno_flag else 0,
                    'mensaje': mensaje_emparejamiento
                }

            aprobados = [r.aprobado for r in registros_dia]
            aprobado = None
            if aprobados:
                if all(a is True for a in aprobados):
                    aprobado = True
                elif any(a is False for a in aprobados):
                    aprobado = False

            # Verificar si hay jornada especial activa para esta fecha
            fecha_registro = None
            if entrada:
                if isinstance(entrada, datetime):
                    fecha_registro = entrada.date()
                elif hasattr(entrada, 'timestamp'):
                    fecha_registro = entrada.timestamp.date()
                elif hasattr(entrada, 'date') and callable(entrada.date):
                    fecha_registro = entrada.date()
                elif hasattr(entrada, 'date'):
                    fecha_registro = entrada.date
            jornada_especial_info = None
            es_jornada_especial = False
            
            if fecha_registro:
                jornada_especial = JornadaEspecial.objects.filter(
                    empleado=usuario,
                    activa=True,
                    fecha_inicio__lte=fecha_registro,
                    fecha_fin__gte=fecha_registro
                ).first()
                
                if jornada_especial:
                    es_jornada_especial = True
                    jornada_especial_info = {
                        'id': jornada_especial.id,
                        'fecha_inicio': jornada_especial.fecha_inicio,
                        'fecha_fin': jornada_especial.fecha_fin,
                        'horas_programadas': jornada_especial.horas_programadas,
                        'observaciones': jornada_especial.observaciones
                    }
            
            # Determinar el día para el registro
            dia_str = fecha.strftime('%Y-%m-%d')  # Default
            if entrada:
                if isinstance(entrada, datetime):
                    dia_str = entrada.date().strftime('%Y-%m-%d')
                elif hasattr(entrada, 'timestamp'):
                    dia_str = entrada.timestamp.date().strftime('%Y-%m-%d')
                elif hasattr(entrada, 'date') and callable(entrada.date):
                    dia_str = entrada.date().strftime('%Y-%m-%d')
                elif hasattr(entrada, 'date'):
                    dia_str = entrada.date.strftime('%Y-%m-%d')

            # Verificar si hay jornada especial activa para esta fecha
            es_jornada_especial = False
            jornada_especial_info = None
            fecha_registro = fecha  # Usar la fecha del bucle
            
            if fecha_registro:
                jornada_especial = JornadaEspecial.objects.filter(
                    fecha_inicio__lte=fecha_registro,
                    fecha_fin__gte=fecha_registro
                ).first()
                
                if jornada_especial:
                    es_jornada_especial = True
                    jornada_especial_info = {
                        'id': jornada_especial.id,
                        'fecha_inicio': jornada_especial.fecha_inicio,
                        'fecha_fin': jornada_especial.fecha_fin,
                        'horas_programadas': jornada_especial.horas_programadas,
                        'observaciones': jornada_especial.observaciones
                    }

            # Solo agregar registro si hay entrada o salida (empleado con registros reales)
            if entrada or salida:
                registros.append({
                            'dia': dia_str,
                            'user_id': usuario.id,
                            'nombre': usuario.nombre,
                            'estacion': registros_dia[0].estacion_servicio.nombre if registros_dia and registros_dia[0].estacion_servicio else '',
                            'entrada': entrada,
                            'salida': salida,
                            'horas_trabajadas': horas_trabajadas if salida else None,
                            'horas_trabajadas_hhmm': (lambda h: f"{int(h):02d}:{int(round((h-int(h))*60)):02d}")(horas_trabajadas) if salida and horas_trabajadas is not None else None,
                            'horas_extra': horas_extra if salida else None,
                            'horas_extra_hhmm': (lambda h: f"{int(h):02d}:{int(round((h-int(h))*60)):02d}")(horas_extra) if salida and horas_extra > 0 else None,
                            'aprobado': aprobado,
                            # Nueva información de turno nocturno
                            'es_turno_nocturno': info_turno['es_nocturno'],
                            'tipo_turno': info_turno['tipo'],
                            'descripcion_turno': info_turno['descripcion'],
                            'diferencia_dias': resultado_turno['diferencia_dias'] if resultado_turno else 0,
                            'mensaje_turno': resultado_turno['mensaje'] if resultado_turno else None,
                            # Información de emparejamiento
                            'emparejado': True if entrada and salida else False,
                            'mensaje_emparejamiento': mensaje_emparejamiento,
                            # Información de jornada especial
                            'es_jornada_especial': es_jornada_especial,
                            'jornada_especial_info': jornada_especial_info,
                    })

    # SIEMPRE MOSTRAR TODOS LOS EMPLEADOS: Con registros y sin registros
    # Determinar el rango de fechas a procesar considerando TODOS los parámetros de fecha
    fecha_inicio_obj = None
    fecha_fin_obj = None
    
    # Obtener filtros adicionales de búsqueda
    search_query = request.GET.get('search', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    
    # Determinar rango de fechas desde cualquier fuente
    if fecha_inicio and fecha_fin:
        fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    elif fecha_desde and fecha_hasta:
        fecha_inicio_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_fin_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    elif fecha_inicio:
        fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_obj = date.today()
    elif fecha_desde:
        fecha_inicio_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_fin_obj = fecha_inicio_obj  # Si solo hay fecha_desde, usar el mismo día
    elif fecha_fin:
        fecha_inicio_obj = date.today() - timedelta(days=7)
        fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    elif fecha_hasta:
        fecha_fin_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        fecha_inicio_obj = fecha_fin_obj - timedelta(days=7)
    
    # PROCESAR empleados sin registros para mostrar vista completa
    if fecha_inicio_obj and fecha_fin_obj:
        # Aplicar filtros de fecha primero para determinar el rango correcto
        fecha_inicio_filtrado = fecha_inicio_obj
        fecha_fin_filtrado = fecha_fin_obj
        
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                fecha_inicio_filtrado = max(fecha_inicio_filtrado, fecha_desde_obj)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                fecha_fin_filtrado = min(fecha_fin_filtrado, fecha_hasta_obj)
            except ValueError:
                pass

        # Aplicar filtros de fecha a los registros existentes
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                registros = [r for r in registros if datetime.strptime(r['dia'], '%Y-%m-%d').date() >= fecha_desde_obj]
            except ValueError:
                pass

        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                registros = [r for r in registros if datetime.strptime(r['dia'], '%Y-%m-%d').date() <= fecha_hasta_obj]
            except ValueError:
                pass

        # Obtener todos los empleados que cumplen con los filtros
        empleados_qs = UsuarioBiometrico.objects.filter(activo=True).select_related('estacion')
        
        # Aplicar filtros de nombre y estación a empleados
        if nombre:
            empleados_qs = empleados_qs.filter(nombre__icontains=nombre)
        if estacion:
            empleados_qs = empleados_qs.filter(estacion__nombre__icontains=estacion)
        if search_query:
            empleados_qs = empleados_qs.filter(
                Q(nombre__icontains=search_query) | 
                Q(estacion__nombre__icontains=search_query)
            )
        
        # Aplicar filtro por jefe de patio
        empleados_qs = aplicar_filtro_jefe_patio(empleados_qs, request.user, 'estacion')
        
        # Generar fechas en el rango filtrado
        fecha_actual = fecha_inicio_filtrado
        fechas_rango = []
        while fecha_actual <= fecha_fin_filtrado:
            fechas_rango.append(fecha_actual)
            fecha_actual += timedelta(days=1)
        
        # Para cada fecha en el rango, verificar qué empleados no tienen registros
        empleados_ausentes_agregados = 0
        for fecha in fechas_rango:
            fecha_str = fecha.strftime('%Y-%m-%d')
            
            # Obtener IDs de empleados que ya tienen registros en esta fecha específica desde los registros procesados
            empleados_con_registros_fecha = set()
            for registro in registros:
                if registro['dia'] == fecha_str:
                    empleados_con_registros_fecha.add(registro['user_id'])
            
            # Agregar registros vacíos para empleados sin registros en esta fecha
            for empleado in empleados_qs:
                if empleado.id not in empleados_con_registros_fecha:
                    registros.append({
                        'dia': fecha_str,
                        'user_id': empleado.id,
                        'nombre': empleado.nombre,
                        'estacion': empleado.estacion.nombre if empleado.estacion else 'Sin estación',
                        'entrada': None,
                        'salida': None,
                        'horas_trabajadas': None,
                        'horas_trabajadas_hhmm': None,
                        'horas_extra': None,
                        'horas_extra_hhmm': None,
                        'aprobado': None,
                        'es_turno_nocturno': False,
                        'tipo_turno': 'Ausente',
                        'descripcion_turno': 'Empleado ausente',
                        'diferencia_dias': 0,
                        'mensaje_turno': 'Ausente',
                        'emparejado': False,
                        'mensaje_emparejamiento': 'Ausente',
                        'es_jornada_especial': False,
                        'jornada_especial_info': None,
                    })
                    empleados_ausentes_agregados += 1

    # Aplicar filtros de búsqueda adicionales
    if search_query:
        registros = [r for r in registros if (
            search_query.lower() in r['nombre'].lower() or
            search_query.lower() in str(r['user_id']).lower() or
            search_query.lower() in r['estacion'].lower()
        )]

    # Ordenar registros por fecha más reciente
    registros.sort(key=lambda x: datetime.strptime(x['dia'], '%Y-%m-%d'), reverse=True)
    
    # Implementar paginación
    paginator = Paginator(registros, 50)  # 50 registros por página
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    # Obtener información de la estación filtrada para jefe de patio
    info_estacion = obtener_info_estacion_jefe(request.user)

    context = {
        'registros': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'nombre': nombre,
        'estacion': estacion,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'search_query': search_query,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        **info_estacion
    }
    return render(request, 'resumen_asistencias_diarias.html', context)

@login_required
def exportar_resumen_asistencias_excel(request):
    """Vista para exportar el resumen de asistencias diarias filtrado a Excel"""
    
    # Obtener los mismos filtros que la vista principal
    nombre = request.GET.get('nombre')
    estacion = request.GET.get('estacion')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    search_query = request.GET.get('search', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    # Reutilizar la misma lógica de filtrado que en resumen_asistencias_diarias
    registros_qs = RegistroAsistencia.objects.select_related('user', 'user__estacion').all()
    
    # Aplicar filtro por jefe de patio
    from .utils_filters import aplicar_filtro_jefe_patio
    registros_qs = aplicar_filtro_jefe_patio(registros_qs, request.user)

    if nombre:
        registros_qs = registros_qs.filter(user__nombre__icontains=nombre)
    if estacion:
        registros_qs = registros_qs.filter(estacion_servicio__nombre__icontains=estacion)
    
    # CORRECCIÓN: Usar rangos timezone-aware en lugar de timestamp__date
    if fecha_inicio:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_inicio_aware = timezone.make_aware(datetime.combine(fecha_inicio_dt.date(), time.min))
        registros_qs = registros_qs.filter(timestamp__gte=fecha_inicio_aware)
    if fecha_fin:
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        fecha_fin_aware = timezone.make_aware(datetime.combine(fecha_fin_dt.date(), time.max))
        registros_qs = registros_qs.filter(timestamp__lte=fecha_fin_aware)

    registros_qs = registros_qs.order_by('user__id', 'timestamp')

    # Procesar registros (misma lógica que en resumen_asistencias_diarias)
    asistencia_por_usuario_fecha = defaultdict(lambda: defaultdict(list))
    for r in registros_qs:
        fecha = localtime(r.timestamp).date()
        asistencia_por_usuario_fecha[r.user][fecha].append(r)

    registros = []
    for usuario, dias in asistencia_por_usuario_fecha.items():
        fechas_ordenadas = sorted(dias.keys())
        for idx, fecha in enumerate(fechas_ordenadas):
            registros_dia = dias[fecha]
            
            # VERIFICAR SI LOS REGISTROS DE ESTE DÍA YA FUERON PROCESADOS EN UN TURNO NOCTURNO ANTERIOR
            registros_ya_procesados = verificar_registros_ya_procesados_en_turno_nocturno(
                asistencia_por_usuario_fecha, usuario, fecha
            )
            
            if registros_ya_procesados:
                # Los registros de este día ya fueron utilizados en un turno nocturno anterior
                # No mostrar este registro para evitar duplicación
                continue
                
            registros_dia.sort(key=lambda r: r.timestamp)

            timestamps = [localtime(r.timestamp) for r in registros_dia]
            
            # Lógica de entrada/salida (mismo código que en resumen_asistencias_diarias)
            entrada = None
            salida = None
            
            if len(timestamps) >= 2:
                posibles_entradas_nocturnas = []
                posibles_salidas_nocturnas = []
                
                for ts in timestamps:
                    if time(20, 0) <= ts.time() <= time(23, 59):
                        posibles_entradas_nocturnas.append(ts)
                    elif time(0, 0) <= ts.time() <= time(8, 0):
                        posibles_salidas_nocturnas.append(ts)
                
                if posibles_entradas_nocturnas and posibles_salidas_nocturnas:
                    entrada = max(posibles_entradas_nocturnas)
                    
                    salidas_mismo_dia = [ts for ts in posibles_salidas_nocturnas if ts.date() == entrada.date()]
                    salidas_dia_siguiente = [ts for ts in posibles_salidas_nocturnas if ts.date() > entrada.date()]
                    
                    if salidas_dia_siguiente:
                        salida = min(salidas_dia_siguiente)
                    elif salidas_mismo_dia:
                        salida = min(salidas_mismo_dia)
                    else:
                        if idx + 1 < len(fechas_ordenadas):
                            next_fecha = fechas_ordenadas[idx + 1]
                            next_registros_dia = dias[next_fecha]
                            for r in sorted(next_registros_dia, key=lambda r: r.timestamp):
                                ts = localtime(r.timestamp)
                                if time(0, 0) <= ts.time() <= time(8, 0):
                                    salida = ts
                                    break
                
                if not entrada or not salida:
                    if posibles_entradas_nocturnas and not salida:
                        entrada = max(posibles_entradas_nocturnas)
                        if idx + 1 < len(fechas_ordenadas):
                            next_fecha = fechas_ordenadas[idx + 1]
                            next_registros_dia = dias[next_fecha]
                            for r in sorted(next_registros_dia, key=lambda r: r.timestamp):
                                ts = localtime(r.timestamp)
                                if time(0, 0) <= ts.time() <= time(8, 0):
                                    salida = ts
                                    break
                        
                        if not salida:
                            entrada = timestamps[0]
                            salida = timestamps[-1]
                    else:
                        entrada = timestamps[0]
                        salida = timestamps[-1]
            else:
                entrada = timestamps[0] if timestamps else None
                salida = timestamps[0] if timestamps else None

            info_turno = detectar_tipo_turno_detallado(entrada, salida if len(timestamps) > 1 else None)

            horas_trabajadas = 0.0
            horas_extra = 0.0
            resultado_turno = None
            if salida and entrada:
                # Usar la nueva función que considera horarios estándar
                calculo = calcular_horas_con_horarios_estandar(entrada, salida)
                horas_trabajadas = calculo['horas_trabajadas']
                horas_extra = calculo['horas_extras']
                
                # Mantener información para compatibilidad
                if len(timestamps) > 1 and calculo.get('tipo_turno', '').startswith('Noche'):
                    resultado_turno = {
                        'duracion_horas': horas_trabajadas,
                        'mensaje': calculo['mensaje']
                    }

            aprobados = [r.aprobado for r in registros_dia]
            aprobado = None
            if aprobados:
                if all(a is True for a in aprobados):
                    aprobado = True
                elif any(a is False for a in aprobados):
                    aprobado = False

            # Verificar jornada especial
            fecha_registro = None
            if entrada:
                if isinstance(entrada, datetime):
                    fecha_registro = entrada.date()
                elif hasattr(entrada, 'timestamp'):
                    fecha_registro = entrada.timestamp.date()
                elif hasattr(entrada, 'date') and callable(entrada.date):
                    fecha_registro = entrada.date()
                elif hasattr(entrada, 'date'):
                    fecha_registro = entrada.date
            jornada_especial_info = None
            es_jornada_especial = False
            
            if fecha_registro:
                jornada_especial = JornadaEspecial.objects.filter(
                    empleado=usuario,
                    activa=True,
                    fecha_inicio__lte=fecha_registro,
                    fecha_fin__gte=fecha_registro
                ).first()
                
                if jornada_especial:
                    es_jornada_especial = True
                    jornada_especial_info = {
                        'horas_programadas': jornada_especial.horas_programadas,
                        'observaciones': jornada_especial.observaciones
                    }

            # Determinar el día para el registro
            dia_str = fecha.strftime('%Y-%m-%d')  # Default
            if entrada:
                if isinstance(entrada, datetime):
                    dia_str = entrada.date().strftime('%Y-%m-%d')
                elif hasattr(entrada, 'timestamp'):
                    dia_str = entrada.timestamp.date().strftime('%Y-%m-%d')
                elif hasattr(entrada, 'date') and callable(entrada.date):
                    dia_str = entrada.date().strftime('%Y-%m-%d')
                elif hasattr(entrada, 'date'):
                    dia_str = entrada.date.strftime('%Y-%m-%d')

            # Solo agregar registro si hay entrada o salida (empleado con registros reales)
            if entrada or salida:
                registros.append({
                    'dia': dia_str,
                    'nombre': usuario.nombre,
                    'estacion': registros_dia[0].estacion_servicio.nombre if registros_dia and registros_dia[0].estacion_servicio else '',
                    'entrada': entrada.strftime('%H:%M') if entrada else '',
                    'salida': salida.strftime('%H:%M') if salida and salida != entrada else '',
                    'horas_trabajadas': (lambda h: f"{int(h):02d}:{int(round((h-int(h))*60)):02d}")(horas_trabajadas) if salida and horas_trabajadas is not None else '',
                    'horas_extra': (lambda h: f"{int(h):02d}:{int(round((h-int(h))*60)):02d}")(horas_extra) if salida and horas_extra > 0 else '',
                    'tipo_turno': info_turno['descripcion'],
                    'aprobado': 'Aprobado' if aprobado is True else 'Rechazado' if aprobado is False else 'Pendiente' if horas_extra > 0 else '',
                    'es_jornada_especial': es_jornada_especial,
                    'jornada_especial_info': jornada_especial_info,
                })

    # Aplicar filtros adicionales
    if search_query:
        registros = [r for r in registros if (
            search_query.lower() in r['nombre'].lower() or
            search_query.lower() in r['estacion'].lower()
        )]

    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            registros = [r for r in registros if datetime.strptime(r['dia'], '%Y-%m-%d').date() >= fecha_desde_obj]
        except ValueError:
            pass

    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            registros = [r for r in registros if datetime.strptime(r['dia'], '%Y-%m-%d').date() <= fecha_hasta_obj]
        except ValueError:
            pass

    # Ordenar registros por fecha más reciente
    registros.sort(key=lambda x: datetime.strptime(x['dia'], '%Y-%m-%d'), reverse=True)

    # Función para calcular horas de retraso
    def calcular_horas_retraso(entrada_str, tipo_turno):
        """Calcula las horas de retraso basado en la entrada y tipo de turno"""
        if not entrada_str:
            return ""
        
        try:
            hora_entrada = datetime.strptime(entrada_str, '%H:%M').time()
            minutos_entrada = hora_entrada.hour * 60 + hora_entrada.minute
            
            # Horarios estándar con margen de 1 hora
            horarios = {
                'Turno 1 (7:00-14:00)': {'estandar': 420, 'inicio': 360, 'fin': 780},  # 7:00, margen 6:00-13:00
                'Turno 2 (14:00-22:00)': {'estandar': 840, 'inicio': 780, 'fin': 1260},  # 14:00, margen 13:00-21:00  
                'Turno 3 (22:00-07:00)': {'estandar': 1320, 'inicio': 1260, 'fin': 360}   # 22:00, margen 21:00-06:00
            }
            
            # Determinar turno correcto basado en hora de entrada
            turno_detectado = None
            if 0 <= minutos_entrada < 360:  # 00:00-06:00 - Turno mañana (no nocturno)
                turno_detectado = 'Turno 1 (7:00-14:00)'
            elif 360 <= minutos_entrada < 780:  # 06:00-13:00
                turno_detectado = 'Turno 1 (7:00-14:00)'
            elif 780 <= minutos_entrada < 1260:  # 13:00-21:00
                turno_detectado = 'Turno 2 (14:00-22:00)'
            elif 1260 <= minutos_entrada <= 1440:  # 21:00-23:59
                turno_detectado = 'Turno 3 (22:00-07:00)'
            
            if not turno_detectado:
                return ""
                
            hora_estandar = horarios[turno_detectado]['estandar']
            
            # Calcular retraso
            if turno_detectado == 'Turno 3 (22:00-07:00)' and minutos_entrada < 360:
                # Entrada nocturna del día siguiente
                retraso = (minutos_entrada + 1440) - hora_estandar
            else:
                retraso = minutos_entrada - hora_estandar
            
            if retraso > 0:
                horas_retraso = retraso // 60
                minutos_retraso = retraso % 60
                
                if horas_retraso > 0 and minutos_retraso > 0:
                    return f"{horas_retraso}h {minutos_retraso}m"
                elif horas_retraso > 0:
                    return f"{horas_retraso}h"
                else:
                    return f"{minutos_retraso}m"
            else:
                return "A tiempo"
                
        except Exception:
            return ""

    # Crear el archivo Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen Asistencias"

    # Estilos
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2E86AB", end_color="2E86AB", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    cell_alignment = Alignment(horizontal="center", vertical="center")
    border_thin = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Estilos para resumen
    summary_font = Font(bold=True, color="FFFFFF")
    summary_fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
    
    # Encabezados (agregamos columna de Horas de Retraso)
    headers = [
        "Día", "Nombre", "Estación", "Entrada", "Salida", "Horas de Retraso",
        "Horas Trabajadas", "Tipo de Turno", "Horas Extras", "Aprobado"
    ]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border_thin

    # Datos con variables para cálculo de resumen
    total_registros = len(registros)
    total_minutos_trabajados = 0
    total_minutos_extras = 0
    total_minutos_extras_aprobadas = 0
    contador_aprobadas = 0
    contador_rechazadas = 0
    contador_pendientes = 0
    contador_sin_retraso = 0
    contador_retraso_leve = 0
    contador_retraso_moderado = 0
    contador_retraso_grave = 0
    
    for row, registro in enumerate(registros, 2):
        # Formatear día
        try:
            fecha_obj = datetime.strptime(registro['dia'], '%Y-%m-%d')
            dia_formateado = fecha_obj.strftime('%d/%m/%Y')
        except:
            dia_formateado = registro['dia']

        # Nombre con indicador de jornada especial
        nombre_texto = registro['nombre']
        if registro['es_jornada_especial']:
            horas_prog = registro['jornada_especial_info'].get('horas_programadas', '12')
            nombre_texto += f" ⭐ {horas_prog}H"

        # Calcular horas de retraso
        horas_retraso = calcular_horas_retraso(registro['entrada'], registro['tipo_turno'])
        
        # Contabilizar tipos de retraso para resumen
        if horas_retraso == "A tiempo":
            contador_sin_retraso += 1
        elif horas_retraso and horas_retraso != "":
            # Extraer minutos del retraso para clasificar
            retraso_minutos = 0
            if 'h' in horas_retraso and 'm' in horas_retraso:
                partes = horas_retraso.replace('h', '').replace('m', '').split()
                if len(partes) == 2:
                    retraso_minutos = int(partes[0]) * 60 + int(partes[1])
            elif 'h' in horas_retraso:
                retraso_minutos = int(horas_retraso.replace('h', '')) * 60
            elif 'm' in horas_retraso:
                retraso_minutos = int(horas_retraso.replace('m', ''))
            
            if retraso_minutos >= 60:
                contador_retraso_grave += 1
            elif retraso_minutos >= 30:
                contador_retraso_moderado += 1
            elif retraso_minutos >= 1:
                contador_retraso_leve += 1

        # Calcular totales para resumen
        if registro['horas_trabajadas']:
            try:
                partes = registro['horas_trabajadas'].split(':')
                if len(partes) == 2:
                    total_minutos_trabajados += int(partes[0]) * 60 + int(partes[1])
            except:
                pass

        if registro['horas_extra']:
            try:
                partes = registro['horas_extra'].split(':')
                if len(partes) == 2:
                    minutos_extras = int(partes[0]) * 60 + int(partes[1])
                    total_minutos_extras += minutos_extras
                    
                    # Contabilizar por estado de aprobación
                    if registro['aprobado'] == 'Aprobado':
                        total_minutos_extras_aprobadas += minutos_extras
                        contador_aprobadas += 1
                    elif registro['aprobado'] == 'Rechazado':
                        contador_rechazadas += 1
                    elif registro['aprobado'] == 'Pendiente':
                        contador_pendientes += 1
            except:
                pass

        data = [
            dia_formateado,
            nombre_texto,
            registro['estacion'] or '-',
            registro['entrada'] or '-',
            registro['salida'] or 'Sin salida registrada' if registro['entrada'] and not registro['salida'] else registro['salida'] or '-',
            horas_retraso or '-',
            registro['horas_trabajadas'] or '-',
            registro['tipo_turno'],
            registro['horas_extra'] or '-',
            registro['aprobado'] or '-'
        ]
        
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.alignment = cell_alignment
            cell.border = border_thin

    # Agregar resumen total al final
    if registros:
        summary_row = len(registros) + 3  # Dejar una fila en blanco
        
        # Función para convertir minutos a HH:MM
        def minutos_a_hhmm(minutos):
            if minutos == 0:
                return "00:00"
            horas = minutos // 60
            mins = minutos % 60
            return f"{horas:02d}:{mins:02d}"
        
        # Título del resumen
        ws.cell(row=summary_row, column=1, value="RESUMEN TOTAL").font = summary_font
        ws.cell(row=summary_row, column=1).fill = summary_fill
        ws.cell(row=summary_row, column=1).alignment = header_alignment
        
        # Merge cells para el título
        ws.merge_cells(f"A{summary_row}:J{summary_row}")
        
        # Datos del resumen
        summary_data = [
            ["Total de Registros:", total_registros],
            ["Total Horas Trabajadas:", minutos_a_hhmm(total_minutos_trabajados)],
            ["Total Horas Extras:", minutos_a_hhmm(total_minutos_extras)],
            ["Horas Extras Aprobadas:", minutos_a_hhmm(total_minutos_extras_aprobadas)],
            ["", ""],  # Fila en blanco
            ["ESTADO DE HORAS EXTRAS:", ""],
            ["Aprobadas:", contador_aprobadas],
            ["Rechazadas:", contador_rechazadas],
            ["Pendientes:", contador_pendientes],
            ["", ""],  # Fila en blanco
            ["RESUMEN DE RETRASOS:", ""],
            ["Sin Retraso:", contador_sin_retraso],
            ["Retraso Leve (1-29 min):", contador_retraso_leve],
            ["Retraso Moderado (30-59 min):", contador_retraso_moderado],
            ["Retraso Grave (60+ min):", contador_retraso_grave],
        ]
        
        for i, (label, value) in enumerate(summary_data):
            row_num = summary_row + 1 + i
            ws.cell(row=row_num, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row_num, column=2, value=value)
            
            # Aplicar borde a las celdas del resumen
            ws.cell(row=row_num, column=1).border = border_thin
            ws.cell(row=row_num, column=2).border = border_thin

    # Ajustar ancho de columnas (agregamos una columna más)
    column_widths = [12, 25, 15, 10, 10, 15, 15, 20, 12, 12]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width

    # Crear respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Nombre del archivo con fecha actual
    fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'resumen_asistencias_{fecha_actual}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Guardar el archivo en la respuesta
    wb.save(response)
    
    return response
    
@login_required
def aprobar_horas_extra(request, usuario_id, dia):
    if request.method == 'POST' and hasattr(request.user, 'rol') and request.user.rol == 'jefe_patio':
        try:
            usuario = UsuarioBiometrico.objects.get(id=usuario_id)
            # Permitir aprobar si el usuario no tiene estación asignada (cualquier jefe puede aprobar)
            # o si el usuario pertenece a la estación del jefe que hace la petición
            if usuario.estacion and usuario.estacion.jefe_id != request.user.id:
                print(f"[APROBACION] Usuario {usuario.nombre} (ID: {usuario_id}) no autorizado para jefe de patio {request.user.username}")
                return HttpResponseForbidden("No autorizado para este usuario")
        except UsuarioBiometrico.DoesNotExist:
            print("[APROBACION] Usuario no encontrado")
            return HttpResponseForbidden("Usuario no encontrado")
        fecha = datetime.strptime(dia, '%Y-%m-%d').date()
        from datetime import time
        from django.utils.timezone import make_aware
        inicio_dia = make_aware(datetime.combine(fecha, time.min))
        fin_dia = make_aware(datetime.combine(fecha, time.max))
        qs = RegistroAsistencia.objects.filter(
            user_id=int(usuario_id),
            timestamp__gte=inicio_dia,
            timestamp__lte=fin_dia,
            id__gt=5  # Excluir registros con ID <= 5 para evitar conflictos con biométricos de estación
        )
        updated = qs.update(aprobado=True)
        print(f"[APROBACION] Registros actualizados para usuario {usuario_id} en {fecha}: {updated}")
        return HttpResponseRedirect(reverse('resumen_asistencias_diarias') + '?aprobado=1')
    print("[APROBACION] Intento de acceso no autorizado o método incorrecto")
    return HttpResponseForbidden("No autorizado")

@login_required
def rechazar_horas_extra(request, usuario_id, dia):
    if request.method == 'POST' and hasattr(request.user, 'rol') and request.user.rol == 'jefe_patio':
        try:
            usuario = UsuarioBiometrico.objects.get(id=usuario_id)
            # Permitir rechazar si el usuario no tiene estación asignada (cualquier jefe puede rechazar)
            # o si el usuario pertenece a la estación del jefe que hace la petición
            if usuario.estacion and usuario.estacion.jefe_id != request.user.id:
                print(f"[RECHAZO] Usuario {usuario.nombre} (ID: {usuario_id}) no autorizado para jefe de patio {request.user.username}")
                return HttpResponseForbidden("No autorizado para este usuario")
        except UsuarioBiometrico.DoesNotExist:
            print("[RECHAZO] Usuario no encontrado")
            return HttpResponseForbidden("Usuario no encontrado")
        fecha = datetime.strptime(dia, '%Y-%m-%d').date()
        from datetime import time
        from django.utils.timezone import make_aware
        inicio_dia = make_aware(datetime.combine(fecha, time.min))
        fin_dia = make_aware(datetime.combine(fecha, time.max))
        qs = RegistroAsistencia.objects.filter(
            user_id=int(usuario_id),
            timestamp__gte=inicio_dia,
            timestamp__lte=fin_dia,
            id__gt=5  # Excluir registros con ID <= 5 para evitar conflictos con biométricos de estación
        )
        updated = qs.update(aprobado=False)
        print(f"[RECHAZO] Registros actualizados para usuario {usuario_id} en {fecha}: {updated}")
        return HttpResponseRedirect(reverse('resumen_asistencias_diarias') + '?aprobado=0')
    print("[RECHAZO] Intento de acceso no autorizado o método incorrecto")
    return HttpResponseForbidden("No autorizado")


@login_required
def reporte_horas_trabajadas(request):
    """
    Vista para mostrar el reporte de horas trabajadas con formato HH:MM
    """
    # Obtener fecha del parámetro o usar hoy por defecto
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()
    
    # Filtros
    jornada_filtro = request.GET.get('jornada')
    solo_extras = request.GET.get('solo_extras') == '1'
    usuario_filtro = request.GET.get('usuario')
    
    # Obtener usuarios con jornada asignada
    usuarios = UsuarioBiometrico.objects.filter(
        activo=True,
        turno__isnull=False
    ).select_related('turno', 'estacion')
    
    # Aplicar filtros de rol
    rol = getattr(request.user, 'rol', None)
    if rol == 'jefe_patio':
        usuarios = usuarios.filter(estacion__jefe=request.user)
    
    # Aplicar filtros de la URL
    if jornada_filtro:
        usuarios = usuarios.filter(turno__tipo_jornada=jornada_filtro)
    
    if usuario_filtro:
        usuarios = usuarios.filter(nombre__icontains=usuario_filtro)
    
    # Calcular horas para cada usuario
    reporte_data = []
    total_horas_trabajadas = 0
    total_horas_extras = 0
    usuarios_con_extras = 0
    
    for usuario in usuarios:
        calculo = usuario.calcular_horas_dia(fecha)
        
        # Filtrar solo usuarios con horas extras si se solicita
        if solo_extras and calculo['horas_extras'] == 0:
            continue
        
        # Incluir usuarios con registros incompletos o con horas trabajadas
        estado = calculo.get('estado', 'normal')
        incluir_usuario = (
            calculo['horas_trabajadas'] > 0 or 
            estado in ['falta_salida', 'falta_entrada', 'registros_iguales', 'sin_registros']
        )
        
        if incluir_usuario:
            reporte_data.append({
                'usuario': usuario,
                'calculo': calculo
            })
            
            # Solo sumar al total si hay horas trabajadas válidas
            if calculo['horas_trabajadas'] > 0:
                total_horas_trabajadas += calculo['horas_trabajadas']
                total_horas_extras += calculo['horas_extras']
                if calculo['horas_extras'] > 0:
                    usuarios_con_extras += 1
    
    # Convertir totales a formato HH:MM
    from API.models import decimal_a_tiempo
    total_trabajadas_formato = decimal_a_tiempo(total_horas_trabajadas)
    total_extras_formato = decimal_a_tiempo(total_horas_extras)
    
    # Obtener jornadas para el filtro
    jornadas = JornadaLaboral.objects.all()
    
    context = {
        'reporte_data': reporte_data,
        'fecha': fecha,
        'fecha_str': fecha.strftime('%Y-%m-%d'),
        'jornadas': jornadas,
        'jornada_filtro': jornada_filtro,
        'solo_extras': solo_extras,
        'usuario_filtro': usuario_filtro,
        'total_trabajadas_formato': total_trabajadas_formato,
        'total_extras_formato': total_extras_formato,
        'usuarios_con_extras': usuarios_con_extras,
        'total_usuarios': len(reporte_data)
    }
    
    return render(request, 'frontend/reporte_horas.html', context)


# ===========================
# PANEL JEFE DE PATIO - JORNADAS ESPECIALES
# ===========================

@login_required
def panel_jefe_patio(request):
    """
    Vista principal del panel para jefe de patio
    """
    # Verificar que el usuario sea jefe de patio
    if not hasattr(request.user, 'rol') or request.user.rol != 'jefe_patio':
        messages.error(request, "No tiene permisos para acceder a esta sección.")
        return redirect('home_biometrico')
    
    # Obtener la estación del jefe de patio
    info_estacion = obtener_info_estacion_jefe(request.user)
    
    if not info_estacion['estacion_filtrada']:
        messages.warning(request, "No tiene una estación asignada. Contacte al administrador.")
        return redirect('home_biometrico')
    
    # Obtener empleados de la estación
    empleados = UsuarioBiometrico.objects.filter(
        estacion__jefe=request.user,
        activo=True
    ).order_by('nombre')
    
    # Obtener jornadas especiales activas
    jornadas_especiales = JornadaEspecial.objects.filter(
        empleado__estacion__jefe=request.user,
        activa=True
    ).order_by('-fecha_inicio')
    
    context = {
        'empleados': empleados,
        'jornadas_especiales': jornadas_especiales,
        'estacion': info_estacion['estacion_filtrada'],
        'total_empleados': empleados.count(),
        'jornadas_activas': jornadas_especiales.count()
    }
    
    return render(request, 'frontend/panel_jefe_patio.html', context)


@login_required
def crear_jornada_especial(request):
    """
    Vista para crear una nueva jornada especial
    """
    # Verificar que el usuario sea jefe de patio
    if not hasattr(request.user, 'rol') or request.user.rol != 'jefe_patio':
        messages.error(request, "No tiene permisos para realizar esta acción.")
        return redirect('home_biometrico')
    
    if request.method == 'POST':
        try:
            empleado_id = request.POST.get('empleado_id')
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            hora_inicio = request.POST.get('hora_inicio')
            hora_fin = request.POST.get('hora_fin')
            horas_programadas = request.POST.get('horas_programadas', '12.00')
            observaciones = request.POST.get('observaciones', '')
            
            # Validaciones
            if not all([empleado_id, fecha_inicio, fecha_fin, hora_inicio, hora_fin]):
                messages.error(request, "Todos los campos son obligatorios.")
                return redirect('panel_jefe_patio')
            
            # Obtener empleado y verificar que pertenece a la estación del jefe
            empleado = get_object_or_404(
                UsuarioBiometrico, 
                id=empleado_id, 
                estacion__jefe=request.user
            )
            
            # Convertir fechas
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            hora_inicio_dt = datetime.strptime(hora_inicio, '%H:%M').time()
            hora_fin_dt = datetime.strptime(hora_fin, '%H:%M').time()
            
            # Crear la jornada especial
            jornada_especial = JornadaEspecial(
                empleado=empleado,
                fecha_inicio=fecha_inicio_dt,
                fecha_fin=fecha_fin_dt,
                hora_inicio_programada=hora_inicio_dt,
                hora_fin_programada=hora_fin_dt,
                horas_programadas=float(horas_programadas),
                aprobada_por=request.user,
                observaciones=observaciones
            )
            
            # Validar antes de guardar
            jornada_especial.full_clean()
            jornada_especial.save()
            
            messages.success(
                request, 
                f"Jornada especial creada exitosamente para {empleado.nombre} "
                f"del {fecha_inicio} al {fecha_fin}."
            )
            
        except ValueError as e:
            messages.error(request, f"Error en el formato de fecha/hora: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error al crear la jornada especial: {str(e)}")
    
    return redirect('panel_jefe_patio')


@login_required
def desactivar_jornada_especial(request, jornada_id):
    """
    Vista para desactivar una jornada especial
    """
    # Verificar que el usuario sea jefe de patio
    if not hasattr(request.user, 'rol') or request.user.rol != 'jefe_patio':
        messages.error(request, "No tiene permisos para realizar esta acción.")
        return redirect('home_biometrico')
    
    if request.method == 'POST':
        try:
            # Obtener la jornada especial y verificar que pertenece al jefe de patio
            jornada = get_object_or_404(
                JornadaEspecial,
                id=jornada_id,
                empleado__estacion__jefe=request.user
            )
            
            jornada.activa = False
            jornada.save()
            
            messages.success(
                request,
                f"Jornada especial de {jornada.empleado.nombre} desactivada exitosamente."
            )
            
        except Exception as e:
            messages.error(request, f"Error al desactivar la jornada especial: {str(e)}")
    
    return redirect('panel_jefe_patio')


@login_required
def lista_empleados_estacion(request):
    """
    Vista AJAX para obtener empleados de la estación del jefe de patio
    """
    # Verificar que el usuario sea jefe de patio
    if not hasattr(request.user, 'rol') or request.user.rol != 'jefe_patio':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    empleados = UsuarioBiometrico.objects.filter(
        estacion__jefe=request.user,
        activo=True
    ).values('id', 'nombre')
    
    return JsonResponse({'empleados': list(empleados)})


def obtener_inicio_semana(fecha):
    """
    Obtiene el domingo que inicia la semana para una fecha dada
    """
    # Ajustar para que domingo sea día 0
    dias_desde_domingo = (fecha.weekday() + 1) % 7
    return fecha - timedelta(days=dias_desde_domingo)


@login_required
def resumenes_semanales(request):
    """
    Vista para mostrar los resúmenes por rango de fechas de horas trabajadas
    Solo accesible para admin y rrhh
    """
    if not hasattr(request.user, 'rol') or request.user.rol not in ['admin', 'rrhh']:
        return HttpResponseForbidden("No tienes permisos para acceder a esta página.")
    
    from API.models import ResumenSemanal, TarifaHoraExtra
    from django.db.models import Q
    
    # Obtener parámetros de filtrado
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    empleado_id = request.GET.get('empleado')
    estacion_id = request.GET.get('estacion')
    
    # Consulta base
    resumenes = ResumenSemanal.objects.select_related(
        'empleado', 'empleado__estacion', 'empleado__turno'
    ).all()
    
    # Aplicar filtros
    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            # Filtrar por fecha de inicio del resumen
            resumenes = resumenes.filter(
                Q(fecha_inicio_semana__gte=fecha_inicio_dt) | 
                Q(fecha_fin_semana__gte=fecha_inicio_dt)
            )
        except ValueError:
            pass
    
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            # Filtrar por fecha de fin del resumen
            resumenes = resumenes.filter(
                Q(fecha_inicio_semana__lte=fecha_fin_dt) | 
                Q(fecha_fin_semana__lte=fecha_fin_dt)
            )
        except ValueError:
            pass
    
    if empleado_id:
        resumenes = resumenes.filter(empleado_id=empleado_id)
    
    if estacion_id:
        resumenes = resumenes.filter(empleado__estacion_id=estacion_id)
    
    # Ordenar por empleado y fecha
    resumenes = resumenes.order_by('empleado__nombre', '-fecha_inicio_semana')
    
    # Agrupar resúmenes por empleado
    empleados_con_resumenes = {}
    for resumen in resumenes:
        empleado_nombre = resumen.empleado.nombre
        if empleado_nombre not in empleados_con_resumenes:
            empleados_con_resumenes[empleado_nombre] = {
                'empleado': resumen.empleado,
                'resumenes': []
            }
        empleados_con_resumenes[empleado_nombre]['resumenes'].append(resumen)
    
    # Obtener listas para filtros
    empleados = UsuarioBiometrico.objects.filter(activo=True).order_by('nombre')
    estaciones = EstacionServicio.objects.all().order_by('nombre')
    tarifas = TarifaHoraExtra.objects.filter(activa=True)
    
    context = {
        'resumenes': resumenes,
        'empleados_con_resumenes': empleados_con_resumenes,
        'empleados': empleados,
        'estaciones': estaciones,
        'tarifas': tarifas,
        'filtros': {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'empleado_id': empleado_id,
            'estacion_id': estacion_id,
        }
    }
    
    return render(request, 'frontend/resumenes_semanales.html', context)


@login_required
def generar_resumen_semanal(request):
    """
    Vista para generar resúmenes por rango de fechas
    Solo accesible para admin y rrhh
    """
    if not hasattr(request.user, 'rol') or request.user.rol not in ['admin', 'rrhh']:
        return HttpResponseForbidden("No tienes permisos para acceder a esta función.")
    
    from API.models import ResumenSemanal
    
    if request.method == 'POST':
        fecha_inicio_str = request.POST.get('fecha_inicio')
        fecha_fin_str = request.POST.get('fecha_fin')
        empleado_id = request.POST.get('empleado_id')
        
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            
            # Validar que la fecha de inicio no sea mayor que la de fin
            if fecha_inicio > fecha_fin:
                messages.error(request, "La fecha de inicio no puede ser mayor que la fecha de fin")
                return redirect('resumenes_semanales')
            
            # Validar rango de fechas (máximo 6 meses para evitar problemas de rendimiento)
            if (fecha_fin - fecha_inicio).days > 180:
                messages.error(request, "El rango de fechas no puede ser mayor a 6 meses")
                return redirect('resumenes_semanales')
            
            if empleado_id:
                # Generar para un empleado específico
                empleado = get_object_or_404(UsuarioBiometrico, id=empleado_id)
                empleados = [empleado]
            else:
                # Generar para todos los empleados activos
                empleados = UsuarioBiometrico.objects.filter(activo=True)
            
            resumen_creados = 0
            resumen_actualizados = 0
            
            for empleado in empleados:
                # Calcular resumen por rango de fechas
                datos_resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
                
                # Crear o actualizar el resumen
                resumen, created = ResumenSemanal.objects.update_or_create(
                    empleado=empleado,
                    fecha_inicio_semana=fecha_inicio,
                    fecha_fin_semana=fecha_fin,
                    defaults=datos_resumen
                )
                
                if created:
                    resumen_creados += 1
                else:
                    resumen_actualizados += 1
            
            if resumen_creados > 0 or resumen_actualizados > 0:
                mensaje = f"Resúmenes procesados: {resumen_creados} creados, {resumen_actualizados} actualizados"
                messages.success(request, mensaje)
            else:
                messages.info(request, "No se procesaron resúmenes")
                
        except Exception as e:
            messages.error(request, f"Error al generar resúmenes: {str(e)}")
    
    # Construir URL de redirect con filtros aplicados
    redirect_url = reverse('resumenes_semanales')
    params = []
    
    if request.method == 'POST':
        # Mantener los filtros del formulario de generación
        if fecha_inicio_str:
            params.append(f'fecha_inicio={fecha_inicio_str}')
        if fecha_fin_str:
            params.append(f'fecha_fin={fecha_fin_str}')
        if empleado_id:
            params.append(f'empleado={empleado_id}')
    
    if params:
        redirect_url += '?' + '&'.join(params)
    
    return HttpResponseRedirect(redirect_url)


@login_required
def descargar_pdf_resumen(request, resumen_id):
    """
    Vista para descargar un resumen por rango de fechas en PDF
    Solo accesible para admin y rrhh
    """
    if not hasattr(request.user, 'rol') or request.user.rol not in ['admin', 'rrhh']:
        return HttpResponseForbidden("No tienes permisos para descargar este archivo.")
    
    try:
        # Importaciones condicionales para ReportLab
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO
    except ImportError:
        messages.error(request, "ReportLab no está instalado. Instale con: pip install reportlab")
        return redirect('resumenes_semanales')
    
    from django.http import HttpResponse
    
    try:
        resumen = get_object_or_404(ResumenSemanal, id=resumen_id)
        
        # Crear el archivo PDF en memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centrado
        )
        
        # Contenido del PDF
        story = []
        
        # Título
        title = Paragraph(f"Resumen de Horas - {resumen.empleado.nombre}", title_style)
        story.append(title)
        
        # Información básica
        info_data = [
            ['Empleado:', resumen.empleado.nombre],
            ['Estación:', resumen.empleado.estacion.nombre if resumen.empleado.estacion else 'N/A'],
            ['Turno:', resumen.empleado.turno.nombre if resumen.empleado.turno else 'N/A'],
            ['Rango de Fechas:', f"{resumen.fecha_inicio_semana} al {resumen.fecha_fin_semana}"],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Tabla de horas
        horas_data = [
            ['Tipo de Horas', 'Cantidad', 'Costo'],
            ['Horas Normales', f"{resumen.horas_normales:.2f}", 'N/A'],
            ['Horas Extra Diurno', f"{resumen.horas_extra_diurno:.2f}", f"${resumen.costo_horas_extra_diurno:.2f}"],
            ['Horas Extra Nocturno', f"{resumen.horas_extra_nocturno:.2f}", f"${resumen.costo_horas_extra_nocturno:.2f}"],
            ['Horas Extra Feriado Diurno', f"{resumen.horas_extra_feriado_diurno:.2f}", f"${resumen.costo_horas_extra_feriado_diurno:.2f}"],
            ['Horas Extra Feriado Nocturno', f"{resumen.horas_extra_feriado_nocturno:.2f}", f"${resumen.costo_horas_extra_feriado_nocturno:.2f}"],
            ['TOTAL HORAS TRABAJADAS', f"{resumen.total_horas_trabajadas:.2f}", ''],
            ['TOTAL HORAS EXTRAS', f"{resumen.total_horas_extras:.2f}", f"${resumen.costo_total_horas_extras:.2f}"],
        ]
        
        horas_table = Table(horas_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        horas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -3), colors.beige),
            ('BACKGROUND', (0, -2), (-1, -1), colors.lightblue),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(horas_table)
        
        # Generar el PDF
        doc.build(story)
        
        # Preparar la respuesta
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f"resumen_horas_{resumen.empleado.nombre}_{resumen.fecha_inicio_semana}_{resumen.fecha_fin_semana}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error al generar el PDF: {str(e)}")
        return redirect('resumenes_semanales')
    
    return render(request, 'frontend/reporte_horas.html', context)


@login_required
def generar_pdf_rango(request):
    """
    Vista para generar PDF directamente por rango de fechas sin guardar en BD
    Solo accesible para admin y rrhh
    """
    if not hasattr(request.user, 'rol') or request.user.rol not in ['admin', 'rrhh']:
        return HttpResponseForbidden("No tienes permisos para acceder a esta función.")
    
    try:
        # Importaciones condicionales para ReportLab
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO
    except ImportError:
        messages.error(request, "ReportLab no está instalado. Instale con: pip install reportlab")
        return redirect('resumenes_semanales')
    
    from django.http import HttpResponse
    from datetime import datetime
    
    try:
        # Obtener parámetros
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        empleado_id = request.GET.get('empleado_id')
        
        if not fecha_inicio_str or not fecha_fin_str:
            messages.error(request, "Debe especificar las fechas de inicio y fin")
            return redirect('resumenes_semanales')
        
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        
        # Validar fechas
        if fecha_inicio > fecha_fin:
            messages.error(request, "La fecha de inicio no puede ser mayor que la fecha de fin")
            return redirect('resumenes_semanales')
        
        # Validar rango de fechas (máximo 6 meses para evitar problemas de rendimiento)
        from datetime import timedelta
        if (fecha_fin - fecha_inicio).days > 180:
            messages.error(request, "El rango de fechas no puede ser mayor a 6 meses")
            return redirect('resumenes_semanales')
        
        # Obtener empleados
        if empleado_id:
            empleados = [get_object_or_404(UsuarioBiometrico, id=empleado_id)]
            filename_suffix = f"{empleados[0].nombre}_{fecha_inicio}_{fecha_fin}"
        else:
            empleados = UsuarioBiometrico.objects.filter(activo=True)
            filename_suffix = f"todos_empleados_{fecha_inicio}_{fecha_fin}"
        
        # Crear el archivo PDF en memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Centrado
            textColor=colors.darkblue
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            alignment=1,  # Centrado
            textColor=colors.darkred
        )
        
        employee_title_style = ParagraphStyle(
            'EmployeeTitle',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.darkgreen
        )
        
        # Contenido del PDF
        story = []
        
        # Título principal
        if len(empleados) == 1:
            title = Paragraph(f"Resumen de Horas - {empleados[0].nombre}", title_style)
        else:
            title = Paragraph("Resumen de Horas - Todos los Empleados", title_style)
        story.append(title)
        
        # Subtítulo con rango de fechas
        subtitle = Paragraph(f"Período: {fecha_inicio} al {fecha_fin}", subtitle_style)
        story.append(subtitle)
        story.append(Spacer(1, 20))
        
        # Procesar cada empleado
        for i, empleado in enumerate(empleados):
            if i > 0:
                story.append(PageBreak())  # Nueva página para cada empleado (excepto el primero)
            
            # Título del empleado (solo si hay múltiples empleados)
            if len(empleados) > 1:
                emp_title = Paragraph(f"Empleado: {empleado.nombre}", employee_title_style)
                story.append(emp_title)
                story.append(Spacer(1, 10))
            
            # Calcular resumen para este empleado
            datos_resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
            
            # Información básica del empleado
            info_data = [
                ['Empleado:', empleado.nombre],
                ['Estación:', empleado.estacion.nombre if empleado.estacion else 'N/A'],
                ['Turno:', empleado.turno.nombre if empleado.turno else 'N/A'],
                ['Rango de Fechas:', f"{fecha_inicio} al {fecha_fin}"],
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Verificar si el empleado tiene horas trabajadas
            if datos_resumen['total_horas_trabajadas'] == 0:
                no_data_table = Table([['Sin registros de horas para este período']], colWidths=[6*inch])
                no_data_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightyellow),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
                    ('TOPPADDING', (0, 0), (-1, -1), 20),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(no_data_table)
                continue
            
            # Tabla de horas
            horas_data = [
                ['Tipo de Horas', 'Cantidad', 'Costo'],
                ['Horas Normales', f"{datos_resumen['horas_normales']:.2f}", 'N/A'],
                ['Horas Extra Diurno', f"{datos_resumen['horas_extra_diurno']:.2f}", f"${datos_resumen['costo_horas_extra_diurno']:.2f}"],
                ['Horas Extra Nocturno', f"{datos_resumen['horas_extra_nocturno']:.2f}", f"${datos_resumen['costo_horas_extra_nocturno']:.2f}"],
                ['Horas Extra Feriado Diurno', f"{datos_resumen['horas_extra_feriado_diurno']:.2f}", f"${datos_resumen['costo_horas_extra_feriado_diurno']:.2f}"],
                ['Horas Extra Feriado Nocturno', f"{datos_resumen['horas_extra_feriado_nocturno']:.2f}", f"${datos_resumen['costo_horas_extra_feriado_nocturno']:.2f}"],
                ['', '', ''],  # Línea separadora
                ['TOTAL HORAS TRABAJADAS', f"{datos_resumen['total_horas_trabajadas']:.2f}", ''],
                ['TOTAL HORAS EXTRAS', f"{datos_resumen['total_horas_extras']:.2f}", f"${datos_resumen['costo_total_horas_extras']:.2f}"],
            ]
            
            horas_table = Table(horas_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            horas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, 5), colors.beige),
                ('BACKGROUND', (0, 6), (-1, 6), colors.white),  # Línea separadora
                ('BACKGROUND', (0, 7), (-1, -1), colors.lightblue),
                ('FONTNAME', (0, 7), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, 5), 1, colors.black),
                ('GRID', (0, 7), (-1, -1), 1, colors.black)
            ]))
            
            story.append(horas_table)
            
            # Agregar espaciado entre empleados si hay múltiples
            if len(empleados) > 1 and i < len(empleados) - 1:
                story.append(Spacer(1, 30))
        
        # Generar el PDF
        doc.build(story)
        
        # Preparar la respuesta
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f"resumen_horas_{filename_suffix}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error al generar el PDF: {str(e)}")
        return redirect('resumenes_semanales')