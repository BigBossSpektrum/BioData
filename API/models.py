# models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('rrhh', 'Recursos Humanos'),
        ('jefe_patio', 'Jefe de Patio'),
        ('Vendedor', 'Vendedor'),
        ('Operador', 'Operador'),
        ('Supervisor', 'Supervisor'),
        ('Encargado', 'Encargado'),
        ('Tecnico', 'Técnico'),
        ('Gerente', 'Gerente'),
        ('Otro', 'Otro'),
    ]
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)
    estacion = models.ForeignKey(
        'EstacionServicio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='UsuarioBiometrico'
    )

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class JornadaLaboral(models.Model):
    nombre = models.CharField(max_length=50)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return self.nombre

class EstacionServicio(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre

class UsuarioBiometrico(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='perfil_biometrico'
    )
    nombre = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    dni = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    privilegio = models.IntegerField(
        default=0
    )
    activo = models.BooleanField(
        default=True
    )
    turno = models.ForeignKey(
        JornadaLaboral,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    jefe = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empleados'
    )
    estacion = models.ForeignKey(
        EstacionServicio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_biometricos'
    )

    def __str__(self):
        return f"{self.nombre} ({self.user})"


class RegistroAsistencia(models.Model):
    usuario = models.ForeignKey(
        UsuarioBiometrico,
        on_delete=models.CASCADE
        )
    timestamp = models.DateTimeField(
        default=timezone.now
        )
    tipo = models.CharField(
        max_length=10, choices=(
            ('entrada', 'Entrada'),
            ('salida', 'Salida'))
        )



