from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Limpia las sesiones expiradas de la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Número de días de sesiones expiradas a limpiar (por defecto: 7)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Obtener sesiones expiradas
        expired_sessions = Session.objects.filter(expire_date__lt=cutoff_date)
        count = expired_sessions.count()
        
        if count > 0:
            expired_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se eliminaron {count} sesiones expiradas (más de {days} días).'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'No se encontraron sesiones expiradas de más de {days} días.'
                )
            )
        
        # También limpiar sesiones naturalmente expiradas
        all_expired = Session.objects.filter(expire_date__lt=timezone.now())
        naturally_expired_count = all_expired.count()
        
        if naturally_expired_count > 0:
            all_expired.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se eliminaron {naturally_expired_count} sesiones naturalmente expiradas.'
                )
            )
