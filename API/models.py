# biometricos/models.py

from django.db import models

class UsuarioBiometrico(models.Model):
    user_id = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    privilegio = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.user_id})"


class RegistroAsistencia(models.Model):
    usuario = models.ForeignKey(UsuarioBiometrico, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField()
    estado = models.IntegerField(default=0)  # 0: entrada, 1: salida, etc.

    class Meta:
        ordering = ['-timestamp']
        unique_together = ('usuario', 'timestamp', 'estado')

    def __str__(self):
        return f"{self.usuario} - {self.timestamp}"
