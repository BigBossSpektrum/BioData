from django.core.management.base import BaseCommand
from API.models import TarifaHoraExtra, FeriadoNacional
from datetime import date


class Command(BaseCommand):
    help = 'Puebla la base de datos con tarifas de horas extras y feriados nacionales de ejemplo'

    def handle(self, *args, **options):
        self.stdout.write("Creando tarifas de horas extras...")
        
        # Crear tarifas de horas extras
        tarifas = [
            {'tipo': 'diurno', 'tarifa_por_hora': 15000.00},
            {'tipo': 'nocturno', 'tarifa_por_hora': 18000.00},
            {'tipo': 'feriado_diurno', 'tarifa_por_hora': 22500.00},
            {'tipo': 'feriado_nocturno', 'tarifa_por_hora': 27000.00},
        ]
        
        for tarifa_data in tarifas:
            tarifa, created = TarifaHoraExtra.objects.get_or_create(
                tipo=tarifa_data['tipo'],
                defaults={'tarifa_por_hora': tarifa_data['tarifa_por_hora']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Tarifa {tarifa.get_tipo_display()} creada: ${tarifa.tarifa_por_hora}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Tarifa {tarifa.get_tipo_display()} ya existe: ${tarifa.tarifa_por_hora}')
                )
        
        self.stdout.write("\nCreando feriados nacionales de ejemplo...")
        
        # Crear algunos feriados nacionales de ejemplo para 2025
        feriados = [
            {'fecha': date(2025, 1, 1), 'nombre': 'Año Nuevo'},
            {'fecha': date(2025, 1, 6), 'nombre': 'Día de los Reyes Magos'},
            {'fecha': date(2025, 3, 24), 'nombre': 'Día de San José'},
            {'fecha': date(2025, 4, 17), 'nombre': 'Jueves Santo'},
            {'fecha': date(2025, 4, 18), 'nombre': 'Viernes Santo'},
            {'fecha': date(2025, 5, 1), 'nombre': 'Día del Trabajo'},
            {'fecha': date(2025, 6, 2), 'nombre': 'Ascensión del Señor'},
            {'fecha': date(2025, 6, 23), 'nombre': 'Corpus Christi'},
            {'fecha': date(2025, 7, 20), 'nombre': 'Día de la Independencia'},
            {'fecha': date(2025, 8, 7), 'nombre': 'Batalla de Boyacá'},
            {'fecha': date(2025, 8, 18), 'nombre': 'Asunción de la Virgen'},
            {'fecha': date(2025, 10, 13), 'nombre': 'Día de la Raza'},
            {'fecha': date(2025, 11, 3), 'nombre': 'Independencia de Cartagena'},
            {'fecha': date(2025, 12, 8), 'nombre': 'Día de la Inmaculada Concepción'},
            {'fecha': date(2025, 12, 25), 'nombre': 'Navidad'},
        ]
        
        for feriado_data in feriados:
            feriado, created = FeriadoNacional.objects.get_or_create(
                fecha=feriado_data['fecha'],
                defaults={'nombre': feriado_data['nombre']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Feriado creado: {feriado.nombre} - {feriado.fecha}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Feriado ya existe: {feriado.nombre} - {feriado.fecha}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n¡Poblado inicial completado exitosamente!')
        )
