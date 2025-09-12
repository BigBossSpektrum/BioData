from django.core.management.base import BaseCommand
from API.models import UsuarioBiometrico, ResumenSemanal
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Genera resúmenes semanales de ejemplo para empleados activos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--semanas',
            type=int,
            default=4,
            help='Número de semanas hacia atrás para generar (default: 4)'
        )

    def handle(self, *args, **options):
        semanas = options['semanas']
        empleados = UsuarioBiometrico.objects.filter(activo=True)
        
        if not empleados.exists():
            self.stdout.write(
                self.style.ERROR('No hay empleados activos para generar resúmenes.')
            )
            return
        
        self.stdout.write(f"Generando resúmenes para {empleados.count()} empleados...")
        self.stdout.write(f"Generando {semanas} semanas hacia atrás...")
        
        # Obtener el domingo de la semana actual
        hoy = date.today()
        dias_desde_domingo = (hoy.weekday() + 1) % 7  # Lunes = 0, Domingo = 6
        domingo_actual = hoy - timedelta(days=dias_desde_domingo)
        
        resumenes_creados = 0
        resumenes_actualizados = 0
        
        for empleado in empleados:
            self.stdout.write(f"\nProcesando empleado: {empleado.nombre}")
            
            for semana in range(semanas):
                fecha_inicio_semana = domingo_actual - timedelta(weeks=semana)
                
                # Generar datos realistas pero aleatorios
                horas_normales = round(random.uniform(30, 45), 2)  # Entre 30 y 45 horas normales por semana
                
                # Horas extras (no siempre tienen)
                tiene_extras = random.choice([True, False, False])  # 33% de probabilidad de tener extras
                
                if tiene_extras:
                    horas_extra_diurno = round(random.uniform(0, 8), 2)
                    horas_extra_nocturno = round(random.uniform(0, 4), 2) if empleado.turno and empleado.turno.es_nocturno else 0
                    horas_extra_feriado_diurno = round(random.uniform(0, 2), 2) if random.choice([True, False]) else 0
                    horas_extra_feriado_nocturno = round(random.uniform(0, 2), 2) if empleado.turno and empleado.turno.es_nocturno and random.choice([True, False]) else 0
                else:
                    horas_extra_diurno = 0
                    horas_extra_nocturno = 0
                    horas_extra_feriado_diurno = 0
                    horas_extra_feriado_nocturno = 0
                
                # Crear o actualizar el resumen
                resumen_data = {
                    'fecha_inicio_semana': fecha_inicio_semana,
                    'fecha_fin_semana': fecha_inicio_semana + timedelta(days=7),
                    'horas_normales': horas_normales,
                    'horas_extra_diurno': horas_extra_diurno,
                    'horas_extra_nocturno': horas_extra_nocturno,
                    'horas_extra_feriado_diurno': horas_extra_feriado_diurno,
                    'horas_extra_feriado_nocturno': horas_extra_feriado_nocturno,
                }
                
                resumen, created = ResumenSemanal.objects.update_or_create(
                    empleado=empleado,
                    fecha_inicio_semana=fecha_inicio_semana,
                    defaults=resumen_data
                )
                
                if created:
                    resumenes_creados += 1
                    status = "✓ Creado"
                else:
                    resumenes_actualizados += 1
                    status = "↻ Actualizado"
                
                total_extras = resumen.total_horas_extras
                self.stdout.write(
                    f"  {status}: Semana {fecha_inicio_semana} - "
                    f"Normal: {horas_normales}h, Extras: {total_extras}h, "
                    f"Costo: ${resumen.costo_total_horas_extras}"
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado!\n'
                f'Resúmenes creados: {resumenes_creados}\n'
                f'Resúmenes actualizados: {resumenes_actualizados}\n'
                f'Total procesados: {resumenes_creados + resumenes_actualizados}'
            )
        )
