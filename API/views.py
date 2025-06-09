# API/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .Biometricos_connections import crear_o_actualizar_usuario_biometrico, eliminar_usuario_biometrico, conectar_dispositivo, importar_datos_dispositivo
from rest_framework import generics
from .models import RegistroAsistencia
from .serializers import RegistroAsistenciaSerializer
from .models import UsuarioBiometrico, RegistroAsistencia
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime

class RegistroAsistenciaListView(generics.ListAPIView):
    queryset = RegistroAsistencia.objects.select_related('usuario__turno').all()
    serializer_class = RegistroAsistenciaSerializer

class RegistroUsuariosView(generics.ListAPIView):
    queryset = RegistroAsistencia.objects.select_related('usuario').all()
    serializer_class = RegistroAsistenciaSerializer

def lista_usuarios(request):
    usuarios = UsuarioBiometrico.objects.all()
    return render(request, 'usuarios.html', {'usuarios': usuarios})

def crear_usuario(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        nombre = request.POST.get('nombre')
        dni = request.POST.get('dni')

        usuario = UsuarioBiometrico.objects.create(user_id=user_id, nombre=nombre, dni=dni)

        # Registrar en el dispositivo biométrico
        crear_o_actualizar_usuario_biometrico(user_id, nombre)

        return redirect('lista_usuarios')  # Reemplaza con tu nombre de vista/listado

def editar_usuario(request, user_id):
    usuario = get_object_or_404(UsuarioBiometrico, user_id=user_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        dni = request.POST.get('dni')

        usuario.nombre = nombre
        usuario.dni = dni
        usuario.save()

        # Actualizar en el dispositivo biométrico
        crear_o_actualizar_usuario_biometrico(usuario.user_id, usuario.nombre)

        return redirect('lista_usuarios')  # Reemplaza con tu nombre de vista/listado

    return render(request, 'editar_usuario.html', {'usuario': usuario})

def eliminar_usuario(request, user_id):
    if request.method == "POST":
        usuario = get_object_or_404(UsuarioBiometrico, user_id=user_id)

        try:
            zk = conectar_dispositivo()
            eliminar_usuario_biometrico(zk, user_id)
            zk.disconnect()

            usuario.delete()
            messages.success(request, f"Usuario {usuario.nombre} eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"Error eliminando usuario: {e}")
        return redirect('lista_usuarios')  # Cambiá esto por tu vista principal


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def recibir_datos_biometrico(request):
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