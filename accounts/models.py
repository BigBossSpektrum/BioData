from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('rrhh', 'Recursos Humanos'),
        ('jefe_patio', 'Jefe de Patio'),
    ]
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default='jefe_patio')

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
