from django.core.management.base import BaseCommand
from django.db.models import Q
from API.models import UsuarioBiometrico, RegistroAsistencia, decimal_a_tiempo
from datetime import datetime, date, timedelta


class Command(BaseCommand):
    help = 'Genera reportes de horas trabajadas y horas extras'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha para el reporte (YYYY-MM-DD). Por defecto: hoy'
        )
        parser.add_argument(
            '--usuario',
            type=str,
            help='Nombre del usuario específico'
        )
        parser.add_argument(
            '--jornada',
            type=str,
            choices=['manana', 'tarde', 'nocturno'],
            help='Filtrar por tipo de jornada'
        )
        parser.add_argument(
            '--solo-extras',
            action='store_true',
            help='Mostrar solo usuarios con horas extras'
        )

    def handle(self, *args, **options):
        # Determinar fecha
        if options['fecha']:
            try:
                fecha = datetime.strptime(options['fecha'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('Formato de fecha inválido. Use YYYY-MM-DD'))
                return
        else:
            fecha = date.today()

        self.generar_reporte(fecha, options)

    def generar_reporte(self, fecha, options):
        """Genera el reporte de horas trabajadas"""
        
        # Filtrar usuarios
        usuarios = UsuarioBiometrico.objects.filter(activo=True)
        
        if options['usuario']:
            usuarios = usuarios.filter(nombre__icontains=options['usuario'])
        
        if options['jornada']:
            usuarios = usuarios.filter(turno__tipo_jornada=options['jornada'])

        # Solo usuarios con jornada asignada
        usuarios = usuarios.filter(turno__isnull=False)

        if not usuarios.exists():
            self.stdout.write(self.style.WARNING('No se encontraron usuarios con los criterios especificados'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n=== REPORTE DE HORAS - {fecha} ===\n'))

        total_horas_trabajadas = 0
        total_horas_extras = 0
        usuarios_con_extras = 0

        for usuario in usuarios:
            calculo = usuario.calcular_horas_dia(fecha)
            
            # Filtrar solo usuarios con horas extras si se solicita
            if options['solo_extras'] and calculo['horas_extras'] == 0:
                continue

            # Incluir usuarios con registros incompletos o con horas trabajadas
            estado = calculo.get('estado', 'normal')
            incluir_usuario = (
                calculo['horas_trabajadas'] > 0 or 
                estado in ['falta_salida', 'falta_entrada', 'registros_iguales', 'sin_registros']
            )
            
            if incluir_usuario:
                self.mostrar_detalle_usuario(usuario, calculo, fecha)
                
                # Solo sumar al total si hay horas trabajadas válidas
                if calculo['horas_trabajadas'] > 0:
                    total_horas_trabajadas += calculo['horas_trabajadas']
                    total_horas_extras += calculo['horas_extras']
                    if calculo['horas_extras'] > 0:
                        usuarios_con_extras += 1

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n=== RESUMEN ==='))
        self.stdout.write(f'Total horas trabajadas: {decimal_a_tiempo(total_horas_trabajadas)}')
        self.stdout.write(f'Total horas extras: {decimal_a_tiempo(total_horas_extras)}')
        self.stdout.write(f'Usuarios con horas extras: {usuarios_con_extras}')

    def mostrar_detalle_usuario(self, usuario, calculo, fecha):
        """Muestra el detalle de un usuario"""
        
        # Encabezado del usuario
        self.stdout.write(f'👤 {usuario.nombre}')
        self.stdout.write(f'   Jornada: {usuario.turno.nombre} ({usuario.turno.hora_inicio} - {usuario.turno.hora_fin})')
        
        # Estado del registro
        estado = calculo.get('estado', 'normal')
        mensaje = calculo.get('mensaje', '')
        
        if estado == 'falta_salida':
            self.stdout.write(self.style.ERROR(f'   ❌ {mensaje}'))
            if 'entrada' in calculo and calculo['entrada']:
                entrada_hora = calculo['entrada'].timestamp.strftime('%H:%M')
                self.stdout.write(f'   Entrada: {entrada_hora}')
            self.stdout.write(f'   Salida: FALTA REGISTRO')
            
        elif estado == 'falta_entrada':
            self.stdout.write(self.style.ERROR(f'   ❌ {mensaje}'))
            self.stdout.write(f'   Entrada: FALTA REGISTRO')
            if 'salida' in calculo and calculo['salida']:
                salida_hora = calculo['salida'].timestamp.strftime('%H:%M')
                self.stdout.write(f'   Salida: {salida_hora}')
                
        elif estado == 'registros_iguales':
            self.stdout.write(self.style.ERROR(f'   ❌ {mensaje}'))
            if 'entrada' in calculo and calculo['entrada']:
                hora = calculo['entrada'].timestamp.strftime('%H:%M')
                self.stdout.write(f'   Registro: {hora} (entrada = salida)')
                
        elif estado == 'sin_registros':
            self.stdout.write(self.style.WARNING(f'   ⚠️  {mensaje}'))
            
        elif estado in ['sin_entradas', 'sin_tiempo', 'sin_jornada']:
            self.stdout.write(self.style.WARNING(f'   ⚠️  {mensaje}'))
            
        else:
            # Registro normal o con extras
            # Registros
            if 'entrada' in calculo and calculo['entrada']:
                entrada_hora = calculo['entrada'].timestamp.strftime('%H:%M')
                self.stdout.write(f'   Entrada: {entrada_hora}')
            
            if 'salida' in calculo and calculo['salida']:
                salida_hora = calculo['salida'].timestamp.strftime('%H:%M')
                self.stdout.write(f'   Salida: {salida_hora}')
            
            # Cálculos
            self.stdout.write(f'   Horas trabajadas: {calculo["horas_trabajadas_formato"]}')
            self.stdout.write(f'   Horas normales: {calculo["horas_normales_formato"]}')
            
            if calculo['horas_extras'] > 0:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️  HORAS EXTRAS: {calculo["horas_extras_formato"]}')
                )
                
                # Verificar si hay registros que requieren aprobación
                registros_sin_aprobar = RegistroAsistencia.objects.filter(
                    user=usuario,
                    timestamp__date=fecha,
                    aprobado__isnull=True
                )
                
                if registros_sin_aprobar.exists():
                    self.stdout.write(
                        self.style.ERROR('   🔴 REQUIERE APROBACIÓN DE JEFE DE PATIO')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('   ✅ Horas extras aprobadas')
                    )
            else:
                self.stdout.write('   ✅ Sin horas extras')
        
        self.stdout.write('')  # Línea en blanco
