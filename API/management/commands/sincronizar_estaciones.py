"""
Comando para sincronizar las estaciones de los usuarios biométricos
basándose en sus registros de asistencia más recientes.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Max
from API.models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio


class Command(BaseCommand):
    help = 'Sincroniza las estaciones de usuarios biométricos basándose en sus registros de asistencia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario-id',
            type=int,
            help='Sincronizar solo un usuario específico por ID',
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Considerar registros de los últimos N días (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar los cambios sin aplicarlos',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== SINCRONIZACIÓN DE ESTACIONES ==='))
        
        # Filtrar usuarios si se especifica un ID
        if options['usuario_id']:
            usuarios = UsuarioBiometrico.objects.filter(id=options['usuario_id'])
            if not usuarios.exists():
                self.stdout.write(self.style.ERROR(f'Usuario con ID {options["usuario_id"]} no encontrado'))
                return
        else:
            usuarios = UsuarioBiometrico.objects.all()

        cambios_realizados = 0
        usuarios_sin_registros = 0

        for usuario in usuarios:
            # Buscar el registro más reciente con estación
            registro_reciente = RegistroAsistencia.objects.filter(
                user=usuario,
                estacion_servicio__isnull=False
            ).select_related('estacion_servicio').order_by('-timestamp').first()

            if registro_reciente:
                nueva_estacion = registro_reciente.estacion_servicio
                
                # Verificar si necesita cambio
                if usuario.estacion != nueva_estacion:
                    self.stdout.write(
                        f'👤 {usuario.nombre}:'
                    )
                    self.stdout.write(
                        f'  📍 {usuario.estacion or "Sin asignar"} → {nueva_estacion}'
                    )
                    self.stdout.write(
                        f'  📅 Basado en registro del {registro_reciente.timestamp.strftime("%Y-%m-%d %H:%M")}'
                    )
                    
                    # Mostrar estadísticas de estaciones para este usuario
                    estadisticas = RegistroAsistencia.objects.filter(
                        user=usuario,
                        estacion_servicio__isnull=False
                    ).values('estacion_servicio__nombre').annotate(
                        count=Count('id')
                    ).order_by('-count')
                    
                    if len(estadisticas) > 1:
                        self.stdout.write('  📊 Distribución de registros:')
                        for stat in estadisticas:
                            self.stdout.write(f'     - {stat["estacion_servicio__nombre"]}: {stat["count"]} registros')
                    
                    # Aplicar cambio si no es dry-run
                    if not options['dry_run']:
                        usuario.estacion = nueva_estacion
                        usuario.save()
                        self.stdout.write(self.style.SUCCESS('  ✅ Actualizado'))
                    else:
                        self.stdout.write(self.style.WARNING('  ⏸️  Simulación (usar --dry-run=False para aplicar)'))
                    
                    cambios_realizados += 1
                    self.stdout.write('')
                else:
                    if options['usuario_id']:  # Solo mostrar si se consulta un usuario específico
                        self.stdout.write(
                            f'✅ {usuario.nombre}: Ya tiene la estación correcta ({usuario.estacion})'
                        )
            else:
                usuarios_sin_registros += 1
                if options['usuario_id']:  # Solo mostrar si se consulta un usuario específico
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {usuario.nombre}: No tiene registros con estación asignada')
                    )

        # Resumen final
        self.stdout.write(self.style.SUCCESS('\n=== RESUMEN ==='))
        self.stdout.write(f'👥 Total usuarios procesados: {usuarios.count()}')
        self.stdout.write(f'🔄 Cambios {"simulados" if options["dry_run"] else "realizados"}: {cambios_realizados}')
        self.stdout.write(f'❓ Usuarios sin registros: {usuarios_sin_registros}')
        
        if options['dry_run'] and cambios_realizados > 0:
            self.stdout.write(self.style.WARNING('\n💡 Ejecuta sin --dry-run para aplicar los cambios'))
