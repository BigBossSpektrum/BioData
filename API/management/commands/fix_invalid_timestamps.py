from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from API.models import RegistroAsistencia
import re


class Command(BaseCommand):
    help = 'Identifica y corrige registros con timestamps inválidos que causan errores de timezone'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corregir automáticamente los problemas encontrados',
        )
        parser.add_argument(
            '--delete-invalid',
            action='store_true',
            help='Eliminar registros con timestamps irrecuperables',
        )

    def handle(self, *args, **options):
        self.stdout.write("Buscando registros con timestamps inválidos...")
        
        # Usar consulta SQL directa para identificar problemas
        problemas_encontrados = []
        
        with connection.cursor() as cursor:
            # Obtener todos los registros con sus timestamps raw
            cursor.execute("""
                SELECT id, timestamp, user_id, status 
                FROM API_registroasistencia 
                ORDER BY id
            """)
            
            registros_raw = cursor.fetchall()
            
        self.stdout.write(f"Revisando {len(registros_raw)} registros...")
        
        problemas = 0
        corregidos = 0
        eliminados = 0
        
        for registro_raw in registros_raw:
            id_registro, timestamp_raw, user_id, status = registro_raw
            
            try:
                # Intentar crear un objeto RegistroAsistencia y acceder a su timestamp
                registro = RegistroAsistencia.objects.get(id=id_registro)
                # Si podemos acceder al timestamp sin error, está bien
                str(registro.timestamp)
                
            except Exception as e:
                problemas += 1
                problema_info = {
                    'id': id_registro,
                    'timestamp_raw': timestamp_raw,
                    'user_id': user_id,
                    'status': status,
                    'error': str(e)
                }
                problemas_encontrados.append(problema_info)
                
                self.stdout.write(
                    self.style.ERROR(
                        f"Registro ID {id_registro}: timestamp inválido - {timestamp_raw} - Error: {str(e)}"
                    )
                )
                
                if options['fix']:
                    # Intentar corregir el timestamp
                    timestamp_corregido = self.corregir_timestamp(timestamp_raw)
                    
                    if timestamp_corregido:
                        try:
                            # Actualizar directamente en la base de datos
                            with connection.cursor() as cursor_update:
                                cursor_update.execute(
                                    "UPDATE API_registroasistencia SET timestamp = %s WHERE id = %s",
                                    [timestamp_corregido, id_registro]
                                )
                            corregidos += 1
                            self.stdout.write(
                                f"  → Corregido a: {timestamp_corregido}"
                            )
                        except Exception as e_fix:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"  → No se pudo corregir: {str(e_fix)}"
                                )
                            )
                    else:
                        # Si no se puede corregir y el usuario lo autoriza, eliminar
                        if options['delete_invalid']:
                            try:
                                with connection.cursor() as cursor_delete:
                                    cursor_delete.execute(
                                        "DELETE FROM API_registroasistencia WHERE id = %s",
                                        [id_registro]
                                    )
                                eliminados += 1
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"  → Registro eliminado (irrecuperable)"
                                    )
                                )
                            except Exception as e_del:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"  → No se pudo eliminar: {str(e_del)}"
                                    )
                                )
        
        # Reporte final
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"Total de registros revisados: {len(registros_raw)}")
        self.stdout.write(f"Problemas encontrados: {problemas}")
        
        if options['fix']:
            self.stdout.write(f"Registros corregidos: {corregidos}")
            if options['delete_invalid']:
                self.stdout.write(f"Registros eliminados: {eliminados}")
            
            if corregidos > 0 or eliminados > 0:
                self.stdout.write(
                    self.style.SUCCESS("✓ Corrección completada. Reinicie el servidor Django.")
                )
        else:
            if problemas > 0:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠ Ejecute con --fix para corregir los problemas encontrados."
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        "⚠ Use --delete-invalid junto con --fix para eliminar registros irrecuperables."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("✓ No se encontraron problemas de timestamp.")
                )

    def corregir_timestamp(self, timestamp_raw):
        """
        Intenta corregir un timestamp inválido
        """
        if not timestamp_raw:
            return timezone.now()
        
        # Convertir a string si no lo es
        timestamp_str = str(timestamp_raw)
        
        # Patrones comunes de fechas que podemos intentar parsear
        patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',  # YYYY-MM-DD HH:MM:SS
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # DD/MM/YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, timestamp_str)
            if match:
                fecha_str = match.group(1)
                try:
                    from datetime import datetime
                    if len(fecha_str) == 10:  # Solo fecha
                        dt = datetime.strptime(fecha_str, '%Y-%m-%d')
                    elif '/' in fecha_str:
                        dt = datetime.strptime(fecha_str, '%d/%m/%Y')
                    else:
                        dt = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                    
                    # Hacer timezone aware
                    return timezone.make_aware(dt)
                except:
                    continue
        
        # Si no se puede parsear, usar fecha actual
        return timezone.now()
