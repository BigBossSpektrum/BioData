from django.core.management.base import BaseCommand
from django.utils import timezone
from API.models import RegistroAsistencia
from datetime import datetime


class Command(BaseCommand):
    help = 'Verifica y corrige problemas de timezone en los datos existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corregir automáticamente los problemas encontrados',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada',
        )

    def handle(self, *args, **options):
        self.stdout.write("Verificando problemas de timezone en RegistroAsistencia...")
        
        problemas = 0
        corregidos = 0
        total = 0
        
        # Revisar todos los registros
        for registro in RegistroAsistencia.objects.all():
            total += 1
            
            try:
                # Intentar acceder al timestamp
                ts = registro.timestamp
                if ts:
                    # Verificar si tiene timezone info
                    if timezone.is_naive(ts):
                        problemas += 1
                        if options['verbose']:
                            self.stdout.write(
                                f"Registro ID {registro.id}: timestamp sin timezone - {ts}"
                            )
                        
                        if options['fix']:
                            # Hacer que el timestamp sea aware usando la zona horaria por defecto
                            ts_aware = timezone.make_aware(ts)
                            registro.timestamp = ts_aware
                            registro.save()
                            corregidos += 1
                            if options['verbose']:
                                self.stdout.write(
                                    f"  → Corregido a: {ts_aware}"
                                )
                    
                    # Verificar funciones del modelo
                    registro.esta_en_horario_normal()
                    
            except Exception as e:
                problemas += 1
                if options['verbose']:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Registro ID {registro.id}: Error - {str(e)}"
                        )
                    )
                
                if options['fix']:
                    # Para errores graves, intentar reconstruir el timestamp
                    try:
                        # Si el timestamp está completamente corrupto, usar fecha actual
                        registro.timestamp = timezone.now()
                        registro.save()
                        corregidos += 1
                        if options['verbose']:
                            self.stdout.write(
                                f"  → Timestamp reconstruido con fecha actual"
                            )
                    except Exception as e2:
                        self.stdout.write(
                            self.style.ERROR(
                                f"  → No se pudo corregir: {str(e2)}"
                            )
                        )
        
        # Reporte final
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"Total de registros revisados: {total}")
        self.stdout.write(f"Problemas encontrados: {problemas}")
        
        if options['fix']:
            self.stdout.write(f"Registros corregidos: {corregidos}")
            if corregidos > 0:
                self.stdout.write(
                    self.style.SUCCESS("✓ Corrección completada.")
                )
        else:
            if problemas > 0:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠ Ejecute con --fix para corregir los problemas encontrados."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("✓ No se encontraron problemas de timezone.")
                )
