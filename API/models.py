# models.py

from django.db import models

class JornadaLaboral(models.Model):
    nombre = models.CharField(max_length=50)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return self.nombre

class UsuarioBiometrico(models.Model):
    user_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    privilegio = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    turno = models.ForeignKey(JornadaLaboral, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.user_id})"

class RegistroAsistencia(models.Model):
    usuario = models.ForeignKey(UsuarioBiometrico, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    tipo = models.CharField(max_length=10, choices=(('entrada', 'Entrada'), ('salida', 'Salida')))

class EstacionServico(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre