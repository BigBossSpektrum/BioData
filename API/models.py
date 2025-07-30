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
        ('supervisor', 'Supervisor'),
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
    jefe = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jefe_de_patio'
    )

    def __str__(self):
        return self.nombre

class UsuarioBiometrico(models.Model):
    biometrico_id = models.IntegerField(
        null=True,
        blank=True
        )  # ID biométrico en el dispositivo

    estacion = models.ForeignKey(
        'EstacionServicio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='UsuarioBiometrico'
    )

    nombre = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    cedula = models.CharField(
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
        return f"{self.nombre}"


class RegistroAsistencia(models.Model):
    user = models.ForeignKey('UsuarioBiometrico', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    
    estacion_servicio = models.ForeignKey(EstacionServicio, on_delete=models.CASCADE, null=True, blank=True)

    status = models.IntegerField(
        default=0
    )

    aprobado = models.BooleanField(
        null=True,
        blank=True,
        default=None,
        help_text="Aprobación de horas extra por el jefe de patio"
    )

    def __str__(self):
        return f"{self.user} - {self.timestamp}"




