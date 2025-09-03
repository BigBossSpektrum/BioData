"""
Comando para asignar estación a jefe de patio (para pruebas)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from API.models import EstacionServicio

User = get_user_model()

class Command(BaseCommand):
    help = 'Asigna una estación a un jefe de patio'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username del jefe de patio')
        parser.add_argument('estacion_nombre', type=str, help='Nombre de la estación')

    def handle(self, *args, **options):
        username = options['username']
        estacion_nombre = options['estacion_nombre']
        
        try:
            # Buscar el usuario
            usuario = User.objects.get(username=username)
            
            if usuario.rol != 'jefe_patio':
                self.stdout.write(
                    self.style.ERROR(
                        f'Error: {username} no tiene rol de jefe_patio (rol actual: {usuario.rol})'
                    )
                )
                return
            
            # Buscar o crear la estación
            estacion, created = EstacionServicio.objects.get_or_create(
                nombre=estacion_nombre,
                defaults={'direccion': f'Dirección de {estacion_nombre}'}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Estación "{estacion_nombre}" creada')
                )
            
            # Asignar jefe a la estación
            estacion.jefe = usuario
            estacion.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Usuario {username} asignado como jefe de la estación "{estacion_nombre}"'
                )
            )
            
            # Verificar la asignación
            self.stdout.write("\n--- Verificación ---")
            self.stdout.write(f"Usuario: {usuario.username}")
            self.stdout.write(f"Rol: {usuario.rol}")
            self.stdout.write(f"Estación asignada: {estacion.nombre}")
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Error: Usuario "{username}" no encontrado')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
