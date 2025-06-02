# API/views.py
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import generics
from .models import RegistroAsistencia
from .serializers import RegistroAsistenciaSerializer
from .models import UsuarioBiometrico
from .forms import UsuarioBiometricoForm
from .Biometricos_connections import crear_o_actualizar_usuario_biometrico

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