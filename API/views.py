# API/views.py
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
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
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
        usuarios_biometricos = UsuarioBiometrico.objects.all()
    elif rol == 'jefe_patio':
        # Solo usuarios biométricos asignados a la misma estación que el jefe de patio
        estaciones_jefe = EstacionServicio.objects.filter(jefe=request.user)
        usuarios_biometricos = UsuarioBiometrico.objects.filter(estacion__in=estaciones_jefe)
    else:
        usuarios_biometricos = UsuarioBiometrico.objects.none()
    estaciones = EstacionServicio.objects.all()
    print(f"[DEBUG] Usuarios encontrados: {usuarios_biometricos.count()}, Estaciones: {estaciones.count()}")
    return render(request, 'usuarios.html', {
        'usuarios': usuarios_biometricos,
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
        cedula = request.POST.get('cedula')
        estacion_id = request.POST.get('estacion_id')
        print(f"[DEBUG] Datos recibidos: nombre={nombre}, cedula={cedula}, estacion_id={estacion_id}")
        if not nombre or not cedula or not estacion_id:
            print("[ERROR] Faltan campos obligatorios.")
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('lista_usuarios')
        try:
            estacion = EstacionServicio.objects.get(id=estacion_id)
            print(f"[DEBUG] Estación encontrada: {estacion}")
        except EstacionServicio.DoesNotExist:
            print("[ERROR] Estación no válida.")
            messages.error(request, "Estación no válida.")
            return redirect('lista_usuarios')
        if UsuarioBiometrico.objects.filter(cedula=cedula).exists():
            print("[ERROR] Usuario biométrico duplicado por Cedula.")
            messages.error(request, "Ya existe un usuario biométrico con esta Cedula.")
            return redirect('lista_usuarios')
        usuario_bio = UsuarioBiometrico.objects.create(
            nombre=nombre,
            cedula=cedula,
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
    print(f"[DEBUG] Usuario encontrado: id={usuario.id}, nombre={usuario.nombre}, biometrico_id={usuario.biometrico_id}, cedula={usuario.cedula}")
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

@api_view(["POST"])
@permission_classes([AllowAny])
def recibir_datos_biometrico(request):
    try:
        print(f"[DEBUG] 📥 Recibiendo datos biométrico. PATH: {request.get_full_path()}")
        print(f"[DEBUG] Headers: {request.headers}")
        print(f"[DEBUG] Body (JSON): {request.data}")

        datos = request.data

        # 🧱 Validación fundamental:
        if not isinstance(datos, list):
            print("[ERROR] ❌ request.data no es una lista. Tipo:", type(datos))
            return Response({"error": "El cuerpo debe ser una lista de registros"}, status=400)

        nuevos = 0

        for registro in datos:
            user_id = registro.get("user_id")
            timestamp_str = registro.get("timestamp")
            estacion = registro.get("estacion")
            status = registro.get("status")

            if not user_id or not timestamp_str:
                print(f"[ERROR] ❌ Registro incompleto: {registro}")
                continue

            timestamp = parse_datetime(timestamp_str)
            if not timestamp:
                print(f"[ERROR] ❌ Timestamp inválido: {timestamp_str}")
                continue

            fecha = timestamp.date()

            user, _ = UsuarioBiometrico.objects.get_or_create(biometrico_id=user_id)
            registros_dia = RegistroAsistencia.objects.filter(usuario=user, timestamp__date=fecha).order_by('timestamp')

            if not registros_dia.filter(tipo='entrada').exists():
                RegistroAsistencia.objects.create(usuario=user, timestamp=timestamp, tipo='entrada', estacion=estacion)
                print(f"[DEBUG] ✅ Registrada ENTRADA para usuario {user.biometrico_id} en {timestamp}")
                nuevos += 1
            elif not registros_dia.filter(tipo='salida').exists():
                RegistroAsistencia.objects.create(usuario=user, timestamp=timestamp, tipo='salida', estacion=estacion)
                print(f"[DEBUG] ✅ Registrada SALIDA para usuario {user.biometrico_id} en {timestamp}")
                nuevos += 1
            else:
                print(f"[INFO] 🟡 Ya existen entrada y salida para usuario {user.biometrico_id} en {fecha}, se ignora registro adicional.")

        print(f"[DEBUG] 🧾 Registros nuevos importados: {nuevos}")
        return Response({"status": "ok", "registros_importados": nuevos})

    except Exception as e:
        import traceback
        print("[ERROR] ❌ Excepción no controlada:")
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=500)
    
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
        cedula = request.POST.get('cedula')
        estacion_id = request.POST.get('estacion_id')
        activo = request.POST.get('activo') == 'on' or request.POST.get('activo') == 'true'
        print(f"[DEBUG] Datos recibidos para editar: nombre={nombre}, cedula={cedula}, estacion_id={estacion_id}, activo={activo}")
        if not nombre or not cedula or not estacion_id:
            print("[ERROR] Faltan campos obligatorios en edición.")
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('lista_usuarios')
        try:
            estacion = EstacionServicio.objects.get(id=estacion_id)
            print(f"[DEBUG] Estación encontrada para edición: {estacion}")
        except EstacionServicio.DoesNotExist:
            print("[ERROR] Estación no válida en edición.")
            messages.error(request, "Estación no válida.")
            return redirect('lista_usuarios')
        usuario.nombre = nombre
        usuario.cedula = cedula
        usuario.estacion = estacion
        usuario.activo = activo
        usuario.save()
        print(f"[DEBUG] Usuario biométrico editado y guardado: {usuario}")
        crear_o_actualizar_usuario_biometrico(usuario.id, nombre)
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