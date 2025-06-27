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
User = get_user_model()

class RegistroAsistenciaListView(generics.ListAPIView):
    queryset = RegistroAsistencia.objects.select_related('usuario__turno').all()
    serializer_class = RegistroAsistenciaSerializer

class RegistroUsuariosView(generics.ListAPIView):
    queryset = RegistroAsistencia.objects.select_related('usuario').all()
    serializer_class = RegistroAsistenciaSerializer

@login_required
def lista_usuarios(request):
    rol = request.user.rol

    if rol == 'admin':
        usuarios_biometricos = UsuarioBiometrico.objects.all()
    elif rol == 'rrhh':
        usuarios_biometricos = UsuarioBiometrico.objects.filter(activo=True)
    elif rol == 'jefe_patio':
        usuarios_biometricos = UsuarioBiometrico.objects.filter(jefe=request.user)
    else:
        usuarios_biometricos = UsuarioBiometrico.objects.none()

    estaciones = EstacionServicio.objects.all()

    return render(request, 'usuarios.html', {
        'usuarios': usuarios_biometricos,
        'estaciones': estaciones,
    })


@login_required
def crear_usuario(request):
    if request.user.rol not in ['admin', 'rrhh']:
        return redirect('no_autorizado')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        dni = request.POST.get('dni')
        estacion_id = request.POST.get('estacion_id')

        if not nombre or not dni or not estacion_id:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('lista_usuarios')

        try:
            estacion = EstacionServicio.objects.get(id=estacion_id)
        except EstacionServicio.DoesNotExist:
            messages.error(request, "Estación no válida.")
            return redirect('lista_usuarios')

        # Validar que no exista duplicado por DNI
        if UsuarioBiometrico.objects.filter(dni=dni).exists():
            messages.error(request, "Ya existe un usuario biométrico con este DNI.")
            return redirect('lista_usuarios')

        usuario_bio = UsuarioBiometrico.objects.create(
            nombre=nombre,
            dni=dni,
            estacion=estacion
        )

        if usuario_bio:
            crear_o_actualizar_usuario_biometrico(usuario_bio.id, nombre)
            messages.success(request, "Usuario biométrico creado correctamente.")
        else:
            messages.error(request, "Error al crear el usuario biométrico.")

        return redirect('lista_usuarios')

    return redirect('lista_usuarios')

def no_autorizado(request):
    return render(request, 'no_autorizado.html')

@login_required
def editar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    usuario = get_object_or_404(UsuarioBiometrico, user_id=user)

    # Seguridad por rol
    if request.user.rol not in ['admin', 'rrhh'] and usuario.jefe != request.user:
        return redirect('no_autorizado')

    if request.method == 'POST':
        usuario.nombre = request.POST.get('nombre')
        usuario.dni = request.POST.get('dni')
        usuario.save()
        crear_o_actualizar_usuario_biometrico(user, usuario.nombre)
        return redirect('lista_usuarios')

    return render(request, 'editar_usuario.html', {'usuario': usuario})


@login_required
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(UsuarioBiometrico, user_id=user_id)

    if request.user.rol != 'admin':
        return redirect('no_autorizado')

    if request.method == "POST":
        try:
            zk = conectar_dispositivo()
            eliminar_usuario_biometrico(zk, user_id)
            zk.disconnect()
            usuario.delete()
            messages.success(request, f"Usuario {usuario.nombre} eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"Error eliminando usuario: {e}")
        return redirect('lista_usuarios')


@csrf_exempt
@api_view(["POST"])
def recibir_datos_biometrico(request):
    print("🛰️  PATH recibido:", request.get_full_path())
    print("📨  Headers:", request.headers)
    print("🧱  Body (JSON):", request.data)
    print("🧱  Body (RAW):", request.body)

    datos = request.data
    nuevos = 0

    for registro in datos:
        user_id = registro.get("user_id")
        nombre = registro.get("nombre")
        timestamp = parse_datetime(registro.get("timestamp"))
        tipo = registro.get("tipo")

        user, _ = UsuarioBiometrico.objects.get_or_create(user_id=user_id, defaults={"nombre": nombre})
        RegistroAsistencia.objects.get_or_create(usuario=user, timestamp=timestamp, tipo=tipo)
        nuevos += 1

    return Response({"status": "ok", "registros_importados": nuevos})


@api_view(["GET"])
def obtener_datos_biometrico(request):
    # Supongamos que importar_datos_dispositivo(retornar_datos=True) devuelve lista de dicts
    datos = importar_datos_dispositivo(retornar_datos=True)
    return Response(datos)

@login_required
def ejecutar_sincronizacion(request):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            importar_datos_dispositivo()  # Llama tu lógica
            return JsonResponse({'success': True, 'message': 'Sincronización completada con éxito.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Acceso no autorizado o método no permitido'})