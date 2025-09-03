from django.core.management.base import BaseCommand
from django.db import transaction
from API.models import JornadaLaboral, UsuarioBiometrico
from datetime import time


class Command(BaseCommand):
    help = 'Configura las jornadas laborales por defecto y permite asignar usuarios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crear-jornadas',
            action='store_true',
            help='Crear las jornadas laborales por defecto'
        )
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Listar todas las jornadas existentes'
        )
        parser.add_argument(
            '--asignar-usuario',
            type=str,
            help='Nombre del usuario para asignar jornada'
        )
        parser.add_argument(
            '--jornada',
            type=str,
            choices=['manana', 'tarde', 'nocturno'],
            help='Tipo de jornada a asignar'
        )

    def handle(self, *args, **options):
        if options['crear_jornadas']:
            self.crear_jornadas_default()
        
        if options['listar']:
            self.listar_jornadas()
        
        if options['asignar_usuario'] and options['jornada']:
            self.asignar_jornada_usuario(options['asignar_usuario'], options['jornada'])

    def crear_jornadas_default(self):
        """Crea las jornadas laborales por defecto"""
        jornadas_default = [
            {
                'nombre': 'Mañana',
                'tipo_jornada': 'manana',
                'hora_inicio': time(6, 0),
                'hora_fin': time(14, 0),
                'horas_normales': 8.00,
                'es_nocturno': False
            },
            {
                'nombre': 'Tarde',
                'tipo_jornada': 'tarde',
                'hora_inicio': time(14, 0),
                'hora_fin': time(22, 0),
                'horas_normales': 8.00,
                'es_nocturno': False
            },
            {
                'nombre': 'Nocturno',
                'tipo_jornada': 'nocturno',
                'hora_inicio': time(22, 0),
                'hora_fin': time(6, 0),
                'horas_normales': 8.00,
                'es_nocturno': True
            }
        ]

        with transaction.atomic():
            for jornada_data in jornadas_default:
                jornada, created = JornadaLaboral.objects.get_or_create(
                    tipo_jornada=jornada_data['tipo_jornada'],
                    defaults=jornada_data
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Jornada {jornada.nombre} creada: {jornada.hora_inicio} - {jornada.hora_fin}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'- Jornada {jornada.nombre} ya existe: {jornada.hora_inicio} - {jornada.hora_fin}'
                        )
                    )

    def listar_jornadas(self):
        """Lista todas las jornadas existentes"""
        jornadas = JornadaLaboral.objects.all()
        
        if not jornadas.exists():
            self.stdout.write(self.style.WARNING('No hay jornadas configuradas'))
            return

        self.stdout.write(self.style.SUCCESS('\n=== JORNADAS LABORALES ==='))
        for jornada in jornadas:
            usuarios_count = UsuarioBiometrico.objects.filter(turno=jornada).count()
            nocturno_text = " (Nocturno)" if jornada.es_nocturno else ""
            
            self.stdout.write(
                f'{jornada.nombre}: {jornada.hora_inicio} - {jornada.hora_fin}{nocturno_text}'
            )
            self.stdout.write(f'  - Horas normales: {jornada.horas_normales}')
            self.stdout.write(f'  - Usuarios asignados: {usuarios_count}')
            self.stdout.write('')

    def asignar_jornada_usuario(self, nombre_usuario, tipo_jornada):
        """Asigna una jornada a un usuario"""
        try:
            usuario = UsuarioBiometrico.objects.get(nombre__icontains=nombre_usuario)
            jornada = JornadaLaboral.objects.get(tipo_jornada=tipo_jornada)
            
            usuario.turno = jornada
            usuario.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Usuario {usuario.nombre} asignado a jornada {jornada.nombre}'
                )
            )
            
        except UsuarioBiometrico.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Usuario "{nombre_usuario}" no encontrado')
            )
        except JornadaLaboral.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Jornada "{tipo_jornada}" no encontrada')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
