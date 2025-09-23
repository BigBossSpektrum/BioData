# API/views.py
import json
import traceback
import os
from django.shortcuts import render, redirect, get_object_or_404
from .Biometricos_connections import crear_o_actualizar_usuario_biometrico, eliminar_usuario_biometrico, conectar_dispositivo, importar_datos_dispositivo
from rest_framework import generics
from .models import RegistroAsistencia
from .serializers import RegistroAsistenciaSerializer
from .models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio
from django.contrib import messages
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .serializers import RegistroAsistenciaSerializer
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.utils import timezone as django_timezone
import traceback
import json
from django.conf import settings
User = get_user_model()

class RegistroAsistenciaListView(generics.ListAPIView):
    queryset = RegistroAsistencia.objects.select_related('usuario__turno').all()
    serializer_class = RegistroAsistenciaSerializer

class RegistroUsuariosView(generics.ListAPIView):
    queryset = RegistroAsistencia.objects.select_related('usuario').all()
    serializer_class = RegistroAsistenciaSerializer

@login_required
def lista_usuarios(request):
    print(f"[DEBUG] Entrando a lista_usuarios. Usuario autenticado: {request.user}, rol: {getattr(request.user, 'rol', None)}")
    rol = request.user.rol
    if rol == 'admin' or rol == 'rrhh':
        usuarios_biometricos = UsuarioBiometrico.objects.select_related('estacion').all()
    elif rol == 'jefe_patio':
        # Solo usuarios biométricos asignados a la misma estación que el jefe de patio
        estaciones_jefe = EstacionServicio.objects.filter(jefe=request.user)
        usuarios_biometricos = UsuarioBiometrico.objects.select_related('estacion').filter(estacion__in=estaciones_jefe)
    else:
        usuarios_biometricos = UsuarioBiometrico.objects.none()
    
    # Obtener la estación del último registro de asistencia para cada usuario
    usuarios_con_estacion = []
    for usuario in usuarios_biometricos:
        ultimo_registro = RegistroAsistencia.objects.filter(user=usuario).select_related('estacion_servicio').order_by('-timestamp').first()
        estacion_nombre = ultimo_registro.estacion_servicio.nombre if ultimo_registro and ultimo_registro.estacion_servicio else "Sin asignar"
        
        # Agregar el atributo estacion_servicio_nombre al usuario
        usuario.estacion_servicio_nombre = estacion_nombre
        usuarios_con_estacion.append(usuario)
    
    estaciones = EstacionServicio.objects.all()
    print(f"[DEBUG] Usuarios encontrados: {len(usuarios_con_estacion)}, Estaciones: {estaciones.count()}")
    return render(request, 'usuarios.html', {
        'usuarios': usuarios_con_estacion,
        'estaciones': estaciones,
    })


@login_required
def crear_usuario(request):
    print(f"[DEBUG] Entrando a crear_usuario. Usuario autenticado: {request.user}, rol: {getattr(request.user, 'rol', None)}")
    if request.user.rol not in ['admin', 'rrhh']:
        print("[DEBUG] Usuario no autorizado para crear usuario biométrico.")
        return redirect('no_autorizado')
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        estacion_id = request.POST.get('estacion_id')
        print(f"[DEBUG] Datos recibidos: nombre={nombre}, estacion_id={estacion_id}")
        
        if not nombre:
            print("[ERROR] Falta el nombre.")
            messages.error(request, "El nombre es obligatorio.")
            return redirect('lista_usuarios')
        
        # Manejo de estación - puede ser vacío para "Sin asignar"
        estacion = None
        if estacion_id and estacion_id.strip():
            try:
                estacion = EstacionServicio.objects.get(id=estacion_id)
                print(f"[DEBUG] Estación encontrada: {estacion}")
            except EstacionServicio.DoesNotExist:
                print("[ERROR] Estación no válida.")
                messages.error(request, "Estación no válida.")
                return redirect('lista_usuarios')
        else:
            print("[DEBUG] No se asignó estación (Sin asignar)")
            
        usuario_bio = UsuarioBiometrico.objects.create(
            nombre=nombre,
            estacion=estacion
        )
        print(f"[DEBUG] Usuario biométrico creado en BD: {usuario_bio}")
        if usuario_bio:
            try:
                biometrico_id = crear_o_actualizar_usuario_biometrico(usuario_bio.id, nombre)
                print(f"[DEBUG] ID biométrico retornado por dispositivo: {biometrico_id}")
                if biometrico_id is not None:
                    usuario_bio.biometrico_id = biometrico_id
                    usuario_bio.save()
                    messages.success(request, "Usuario biométrico creado correctamente.")
                else:
                    print("[ERROR] No se pudo crear el usuario en el biométrico.")
                    messages.error(request, "No se pudo crear el usuario en el biométrico.")
            except Exception as e:
                print(f"[ERROR] Error al crear usuario en dispositivo: {e}")
                messages.error(request, f"Error al crear el usuario biométrico en el dispositivo: {e}")
        else:
            print("[ERROR] Error al crear usuario biométrico en BD.")
            messages.error(request, "Error al crear el usuario biométrico.")
        return redirect('lista_usuarios')
    return redirect('lista_usuarios')

def no_autorizado(request):
    print("[DEBUG] Vista no_autorizado invocada.")
    return render(request, 'no_autorizado.html')

@login_required
def eliminar_usuario(request, user_id):
    print(f"[DEBUG] Ingresando a eliminar_usuario con user_id={user_id}")
    usuario = get_object_or_404(UsuarioBiometrico, id=user_id)
    print(f"[DEBUG] Usuario encontrado: id={usuario.id}, nombre={usuario.nombre}, biometrico_id={usuario.biometrico_id}")
    print(f"[DEBUG] Rol del usuario autenticado: {request.user.rol}")
    if request.user.rol != 'admin':
        print("[DEBUG] Usuario no autorizado para eliminar.")
        return redirect('no_autorizado')
    if request.method == "POST":
        zk = None
        try:
            if usuario.biometrico_id is None:
                print("[ERROR] El usuario no tiene biometrico_id asignado. No se puede eliminar en el dispositivo biométrico.")
                messages.error(request, "El usuario no tiene ID biométrico asignado. No se puede eliminar en el dispositivo biométrico.")
            else:
                print("[DEBUG] Conectando a dispositivo biométrico...")
                zk = conectar_dispositivo()
                print(f"[DEBUG] Dispositivo conectado. Eliminando en biométrico con biometrico_id={usuario.biometrico_id}")
                eliminar_usuario_biometrico(zk, usuario.biometrico_id)
                print("[DEBUG] Eliminación en biométrico completada. Eliminando en base de datos...")
                usuario.delete()
                print("[DEBUG] Usuario eliminado en base de datos.")
                messages.success(request, f"Usuario {usuario.nombre} eliminado correctamente.")
        except Exception as e:
            print(f"[ERROR] Error eliminando usuario: {e}")
            messages.error(request, f"Error eliminando usuario: {e}")
        finally:
            if zk:
                try:
                    print("[DEBUG] Desconectando dispositivo biométrico...")
                    zk.disconnect()
                except Exception as ex:
                    print(f"[ERROR] Error desconectando dispositivo: {ex}")
        print("[DEBUG] Redirigiendo a lista_usuarios")
        return redirect('lista_usuarios')

def crear_log_datos_biometrico(datos_request, ip_cliente, user_agent, timestamp):
    """
    Actualiza el archivo de log con los datos recibidos del dispositivo biométrico.
    Agrupa por fecha y estación, manteniendo un historial de todas las recepciones.
    """
    try:
        # Crear el directorio si no existe
        log_dir = os.path.join(settings.BASE_DIR, 'registros_biometrico')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Determinar la estación principal de los datos recibidos
        estacion_principal = "SinEstacion"
        if isinstance(datos_request, list) and len(datos_request) > 0:
            # Obtener la estación del primer registro
            primer_registro = datos_request[0]
            if isinstance(primer_registro, dict) and 'estacion' in primer_registro:
                estacion_principal = primer_registro['estacion'].replace(' ', '_').replace('/', '_')
        
        # Nombre del archivo con fecha y estación
        fecha_archivo = datetime.now().strftime('%Y-%m-%d')
        nombre_archivo = f"biodata_{estacion_principal}_{fecha_archivo}.json"
        ruta_archivo = os.path.join(log_dir, nombre_archivo)
        
        # Estructura de la nueva recepción
        nueva_recepcion = {
            "timestamp_recepcion": timestamp,
            "ip_cliente": ip_cliente,
            "user_agent": user_agent,
            "total_registros": len(datos_request) if isinstance(datos_request, list) else 1,
            "datos_recibidos": datos_request
        }
        
        # Cargar datos existentes o crear estructura inicial
        if os.path.exists(ruta_archivo):
            try:
                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                print(f"[LOG] 📄 Archivo existente encontrado: {nombre_archivo}")
            except (json.JSONDecodeError, Exception) as e:
                print(f"[WARNING] ⚠️ Error al leer archivo existente, creando nuevo: {str(e)}")
                log_data = {}
        else:
            log_data = {}
            print(f"[LOG] 🆕 Creando nuevo archivo: {nombre_archivo}")
        
        # Inicializar estructura si no existe
        if 'metadata' not in log_data:
            log_data['metadata'] = {
                "version_log": "2.0",
                "servidor": "BioData API",
                "endpoint": "/API/recibir_datos_biometrico/",
                "estacion_principal": estacion_principal,
                "fecha_archivo": fecha_archivo,
                "creado_en": timestamp,
                "ultima_actualizacion": timestamp
            }
        
        if 'recepciones' not in log_data:
            log_data['recepciones'] = []
        
        # Actualizar metadata
        log_data['metadata']['ultima_actualizacion'] = timestamp
        log_data['metadata']['total_recepciones'] = len(log_data['recepciones']) + 1
        
        # Agregar la nueva recepción
        log_data['recepciones'].append(nueva_recepcion)
        
        # Calcular estadísticas
        total_registros_archivo = sum(r.get('total_registros', 0) for r in log_data['recepciones'])
        log_data['metadata']['total_registros_acumulados'] = total_registros_archivo
        
        # Escribir el archivo actualizado
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"[LOG] ✅ Archivo actualizado: {nombre_archivo}")
        print(f"[LOG] � Total recepciones: {len(log_data['recepciones'])}")
        print(f"[LOG] 📈 Total registros acumulados: {total_registros_archivo}")
        
        return ruta_archivo
        
    except Exception as e:
        print(f"[ERROR] ❌ Error al crear/actualizar log: {str(e)}")
        print(f"[ERROR] 📄 Traceback: {traceback.format_exc()}")
        return None

@api_view(["POST"])
@permission_classes([AllowAny])
def recibir_datos_biometrico(request):
    try:
        # 📊 Información de la request
        ip_cliente = request.META.get('REMOTE_ADDR', 'IP_DESCONOCIDA')
        user_agent = request.META.get('HTTP_USER_AGENT', 'UA_DESCONOCIDA')
        timestamp_recepcion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"[DEBUG] 📥 === NUEVA REQUEST BIOMÉTRICA ===")
        print(f"[DEBUG] 🕐 Timestamp: {timestamp_recepcion}")
        print(f"[DEBUG] 🌐 IP Cliente: {ip_cliente}")
        print(f"[DEBUG] 🔧 User-Agent: {user_agent}")
        print(f"[DEBUG] 📍 PATH: {request.get_full_path()}")

        datos = request.data
        
        # 📝 CREAR LOG DE LOS DATOS RECIBIDOS
        log_archivo = crear_log_datos_biometrico(datos, ip_cliente, user_agent, timestamp_recepcion)
        if log_archivo:
            print(f"[LOG] ✅ Datos guardados en log: {os.path.basename(log_archivo)}")
        else:
            print(f"[LOG] ⚠️ No se pudo crear el archivo de log")

        if not isinstance(datos, list):
            print(f"[ERROR] ❌ IP {ip_cliente} envió datos no válidos. Tipo: {type(datos)}")
            return Response({"error": "El cuerpo debe ser una lista de registros"}, status=400)

        total_registros = len(datos)
        print(f"[DEBUG] 📦 Total registros recibidos: {total_registros}")

        # � Validar límite de registros
        MAX_REGISTROS = 1000
        if total_registros > MAX_REGISTROS:
            print(f"[ERROR] ❌ IP {ip_cliente} envió {total_registros} registros. Máximo permitido: {MAX_REGISTROS}")
            return Response({
                "error": f"Máximo {MAX_REGISTROS} registros permitidos por request",
                "registros_enviados": total_registros,
                "timestamp": timestamp_recepcion
            }, status=400)

        # �📊 Contadores y estadísticas
        estaciones_stats = {}
        registros_nuevos = 0
        registros_duplicados = 0
        registros_error = 0
        usuarios_nuevos = 0
        usuarios_actualizados = 0
        estaciones_actualizadas = 0  # Nuevo contador para cambios de estación

        for i, registro in enumerate(datos):
            print(f"[DEBUG] 🔄 Procesando registro #{i+1}/{total_registros}")
            
            if not isinstance(registro, dict):
                print(f"[ERROR] ❌ Registro #{i+1} no es dict válido. Tipo: {type(registro)}")
                registros_error += 1
                continue

            user_id = registro.get("user_id")
            nombre = registro.get("nombre", "").strip()
            timestamp_str = registro.get("timestamp")
            estacion_nombre = registro.get("estacion")
            status = registro.get("status")

            # 📊 Actualizar estadísticas por estación
            if estacion_nombre:
                if estacion_nombre not in estaciones_stats:
                    estaciones_stats[estacion_nombre] = {
                        'total_enviados': 0,
                        'nuevos': 0,
                        'duplicados': 0,
                        'errores': 0,
                        'primer_timestamp': timestamp_str,
                        'ultimo_timestamp': timestamp_str
                    }
                estaciones_stats[estacion_nombre]['total_enviados'] += 1
                
                # Actualizar rango de timestamps
                if timestamp_str:
                    if timestamp_str < estaciones_stats[estacion_nombre]['primer_timestamp']:
                        estaciones_stats[estacion_nombre]['primer_timestamp'] = timestamp_str
                    if timestamp_str > estaciones_stats[estacion_nombre]['ultimo_timestamp']:
                        estaciones_stats[estacion_nombre]['ultimo_timestamp'] = timestamp_str

            # Validaciones
            if not user_id or not timestamp_str or not estacion_nombre:
                print(f"[ERROR] ❌ Registro #{i+1} incompleto: user_id={user_id}, timestamp={timestamp_str}, estacion={estacion_nombre}")
                registros_error += 1
                if estacion_nombre:
                    estaciones_stats[estacion_nombre]['errores'] += 1
                continue

            timestamp = parse_datetime(timestamp_str)
            if not timestamp:
                print(f"[ERROR] ❌ Timestamp inválido en registro #{i+1}: {timestamp_str}")
                registros_error += 1
                if estacion_nombre:
                    estaciones_stats[estacion_nombre]['errores'] += 1
                continue
            
            # Convertir a timezone-aware si es naive
            if timestamp.tzinfo is None:
                timestamp = django_timezone.make_aware(timestamp, django_timezone.get_current_timezone())

            try:
                estacion_obj = EstacionServicio.objects.get(nombre=estacion_nombre)
            except EstacionServicio.DoesNotExist:
                print(f"[ERROR] ❌ Estación '{estacion_nombre}' no existe en BD")
                registros_error += 1
                if estacion_nombre:
                    estaciones_stats[estacion_nombre]['errores'] += 1
                continue

            # Obtener o crear usuario
            user, user_created = UsuarioBiometrico.objects.get_or_create(biometrico_id=user_id)

            if user_created:
                user.nombre = nombre
                user.estacion = estacion_obj  # Asignar estación al crear usuario
                user.save()
                usuarios_nuevos += 1
                print(f"[INFO] 🆕 Usuario biométrico creado: ID={user_id}, Nombre={nombre}, Estación={estacion_nombre}")
            else:
                usuario_actualizado = False
                
                # Actualizar nombre siempre que venga un nombre válido del dispositivo biométrico
                if nombre and nombre.strip():
                    # Solo actualizar si el nombre ha cambiado
                    if user.nombre != nombre:
                        print(f"[INFO] ✏️ Actualizando nombre desde dispositivo: ID={user_id}, '{user.nombre}' → '{nombre}'")
                        user.nombre = nombre
                        usuario_actualizado = True
                    else:
                        print(f"[DEBUG] 📝 Nombre confirmado desde dispositivo: ID={user_id}, '{nombre}'")
                elif not user.nombre:
                    # Si no viene nombre del dispositivo y el usuario no tiene nombre, asignar uno genérico
                    nombre_generico = f"Usuario_{user_id}"
                    print(f"[WARNING] ⚠️ Sin nombre desde dispositivo para ID={user_id}, asignando: '{nombre_generico}'")
                    user.nombre = nombre_generico
                    usuario_actualizado = True
                
                # VALIDACIÓN ESTRICTA: Solo asignar estación si el usuario NO tiene una asignada
                if not user.estacion:
                    user.estacion = estacion_obj
                    usuario_actualizado = True
                    print(f"[INFO] 🏢 Asignando primera estación: ID={user_id}, → '{estacion_nombre}'")
                elif user.estacion != estacion_obj:
                    # ADVERTENCIA: No cambiar estación automáticamente para evitar mezcla de registros
                    print(f"[WARNING] ⚠️ CONFLICTO ESTACIÓN: Usuario {user_id} ({user.nombre}) está asignado a '{user.estacion.nombre}' pero el registro viene de '{estacion_nombre}' - NO SE ACTUALIZA")
                
                # Guardar cambios si hubo actualizaciones
                if usuario_actualizado:
                    user.save()
                    usuarios_actualizados += 1

            # VALIDACIÓN CRÍTICA: Verificar que el registro provenga de la estación correcta
            if user.estacion and user.estacion != estacion_obj:
                print(f"[ERROR] ❌ REGISTRO RECHAZADO: Usuario {user_id} ({user.nombre}) pertenece a '{user.estacion.nombre}' pero registro viene de '{estacion_nombre}'")
                registros_error += 1
                if estacion_nombre:
                    estaciones_stats[estacion_nombre]['errores'] += 1
                continue

            # Verificar duplicados
            duplicado = RegistroAsistencia.objects.filter(
                user=user,
                timestamp=timestamp,
                estacion_servicio=estacion_obj
            ).exists()

            if duplicado:
                print(f"[INFO] 🔁 Duplicado: Usuario {user_id} en {estacion_nombre} a las {timestamp}")
                registros_duplicados += 1
                estaciones_stats[estacion_nombre]['duplicados'] += 1
                continue

            # Crear registro
            RegistroAsistencia.objects.create(
                user=user,
                timestamp=timestamp,
                status=status,
                estacion_servicio=estacion_obj
            )
            registros_nuevos += 1
            estaciones_stats[estacion_nombre]['nuevos'] += 1
            print(f"[DEBUG] ✅ Nuevo registro: Usuario {user_id} en {estacion_nombre}")

        # 📊 REPORTE FINAL DETALLADO
        print(f"\n[DEBUG] 🏁 === REPORTE FINAL ===")
        print(f"[DEBUG] 🌐 IP Cliente: {ip_cliente}")
        print(f"[DEBUG] 📦 Total registros procesados: {total_registros}")
        print(f"[DEBUG] ✅ Registros nuevos: {registros_nuevos}")
        print(f"[DEBUG] 🔁 Registros duplicados: {registros_duplicados}")
        print(f"[DEBUG] ❌ Registros con error: {registros_error}")
        print(f"[DEBUG] 👤 Usuarios nuevos creados: {usuarios_nuevos}")
        print(f"[DEBUG] ✏️ Usuarios actualizados: {usuarios_actualizados}")
        print(f"[DEBUG] 🏢 Estaciones actualizadas: {estaciones_actualizadas}")
        
        print(f"\n[DEBUG] 📊 === ESTADÍSTICAS POR ESTACIÓN ===")
        for estacion, stats in estaciones_stats.items():
            print(f"[DEBUG] 🏢 {estacion}:")
            print(f"         📤 Enviados: {stats['total_enviados']}")
            print(f"         ✅ Nuevos: {stats['nuevos']}")
            print(f"         🔁 Duplicados: {stats['duplicados']}")
            print(f"         ❌ Errores: {stats['errores']}")
            print(f"         🕐 Rango: {stats['primer_timestamp']} → {stats['ultimo_timestamp']}")
            if stats['total_enviados'] > 0:
                print(f"         📈 Tasa éxito: {(stats['nuevos']/(stats['total_enviados'])*100):.1f}%")

        # Respuesta mejorada
        response_data = {
            "status": "ok",
            "timestamp_procesamiento": timestamp_recepcion,
            "ip_cliente": ip_cliente,
            "resumen": {
                "total_procesados": total_registros,
                "nuevos": registros_nuevos,
                "duplicados": registros_duplicados,
                "errores": registros_error,
                "usuarios_nuevos": usuarios_nuevos,
                "usuarios_actualizados": usuarios_actualizados,
                "estaciones_actualizadas": estaciones_actualizadas
            },
            "estaciones": estaciones_stats
        }

        print(f"[DEBUG] 📤 Enviando respuesta: {response_data}")
        return Response(response_data)

    except Exception as e:
        print(f"[ERROR] ❌ === EXCEPCIÓN CRÍTICA ===")
        print(f"[ERROR] 🌐 IP Cliente: {request.META.get('REMOTE_ADDR', 'DESCONOCIDA')}")
        print(f"[ERROR] 🕐 Timestamp: {datetime.now()}")
        print(f"[ERROR] 📄 Traceback completo:")
        print(traceback.format_exc())
        
        return Response({
            "error": "Excepción inesperada en el servidor",
            "detalle": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)
    
@api_view(["GET"])
def obtener_datos_biometrico(request):
    print("[DEBUG] Obteniendo datos del dispositivo biométrico...")
    datos = importar_datos_dispositivo(retornar_datos=True)
    print(f"[DEBUG] Datos obtenidos: {datos}")
    return Response(datos)

@login_required
def ejecutar_sincronizacion(request):
    print(f"[DEBUG] Ejecutando sincronización. Usuario: {request.user}")
    if request.method == "POST" and request.user.is_authenticated:
        try:
            importar_datos_dispositivo()
            print("[DEBUG] Sincronización completada con éxito.")
            return JsonResponse({'success': True, 'message': 'Sincronización completada con éxito.'})
        except Exception as e:
            print(f"[ERROR] Error en sincronización: {e}")
            return JsonResponse({'success': False, 'message': str(e)})
    print("[ERROR] Acceso no autorizado o método no permitido para sincronización.")
    return JsonResponse({'success': False, 'message': 'Acceso no autorizado o método no permitido'})

@login_required
def editar_usuario(request, user_id):
    print(f"[DEBUG] Entrando a editar_usuario con user_id={user_id}")
    usuario = get_object_or_404(UsuarioBiometrico, id=user_id)
    print(f"[DEBUG] Usuario encontrado: {usuario}")
    if request.user.rol not in ['admin', 'rrhh']:
        print("[DEBUG] Usuario no autorizado para editar.")
        return redirect('no_autorizado')
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        estacion_id = request.POST.get('estacion_id')
        activo = request.POST.get('activo') == 'on' or request.POST.get('activo') == 'true'
        print(f"[DEBUG] Datos recibidos para editar: nombre={nombre}, estacion_id={estacion_id}, activo={activo}")
        
        if not nombre:
            print("[ERROR] Falta el nombre en edición.")
            messages.error(request, "El nombre es obligatorio.")
            return redirect('lista_usuarios')
        
        # Manejo de estación - puede ser vacío para "Sin asignar"
        estacion = None
        if estacion_id and estacion_id.strip():
            try:
                estacion = EstacionServicio.objects.get(id=estacion_id)
                print(f"[DEBUG] Estación encontrada para edición: {estacion}")
            except EstacionServicio.DoesNotExist:
                print("[ERROR] Estación no válida en edición.")
                messages.error(request, "Estación no válida.")
                return redirect('lista_usuarios')
        else:
            print("[DEBUG] No se asignó estación (Sin asignar)")
        
        usuario.nombre = nombre
        usuario.estacion = estacion
        usuario.activo = activo
        usuario.save()
        print(f"[DEBUG] Usuario biométrico editado y guardado: {usuario}")
        # crear_o_actualizar_usuario_biometrico(usuario.id, nombre)  # Conexión al biométrico eliminada
        messages.success(request, "Usuario biométrico editado correctamente.")
        return redirect('lista_usuarios')
    return redirect('lista_usuarios')

@csrf_exempt
def api_sincronizar_biometrico(request):
    if request.method == 'POST':
        # En vez de importar, lee los registros existentes
        registros = RegistroAsistencia.objects.all()
        serializer = RegistroAsistenciaSerializer(registros, many=True)
        return JsonResponse({'registros': serializer.data}, safe=False)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def recibir_logs(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            for log in data:
                usuario, _ = UsuarioBiometrico.objects.get_or_create(
                    biometrico_id=log['biometrico_id']
                )

                RegistroAsistencia.objects.get_or_create(
                    usuario=usuario,
                    timestamp=log['timestamp'],
                    defaults={
                        'tipo': 'entrada' if log['punch'] == 0 else 'salida',
                        'aprobado': True
                    }
                )

            return JsonResponse({'status': 'success'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)