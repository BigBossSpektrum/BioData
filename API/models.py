# models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from datetime import datetime, timedelta, time
from django.core.exceptions import ValidationError


def decimal_a_tiempo(horas_decimal):
    """
    Convierte horas decimales a formato HH:MM
    Ejemplo: 8.5 -> "08:30"
    """
    if horas_decimal == 0:
        return "00:00"
    
    horas = int(horas_decimal)
    minutos = int((horas_decimal - horas) * 60)
    return f"{horas:02d}:{minutos:02d}"


def tiempo_a_decimal(tiempo_str):
    """
    Convierte formato HH:MM a horas decimales
    Ejemplo: "08:30" -> 8.5
    """
    try:
        horas, minutos = map(int, tiempo_str.split(':'))
        return horas + (minutos / 60)
    except:
        return 0


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('rrhh', 'Recursos Humanos'),
        ('jefe_patio', 'Jefe de Patio'),
        ('supervisor', 'Supervisor'),
    ]
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)
    estacion = models.ForeignKey(
        'EstacionServicio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='UsuarioBiometrico'
    )

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class JornadaLaboral(models.Model):
    JORNADA_CHOICES = [
        ('manana', 'Mañana (7:00 - 14:00)'),
        ('tarde', 'Tarde (14:00 - 22:00)'),
        ('nocturno', 'Nocturno (22:00 - 7:00)'),
    ]
    
    nombre = models.CharField(max_length=50)
    tipo_jornada = models.CharField(
        max_length=15, 
        choices=JORNADA_CHOICES, 
        default='personalizada'
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    horas_normales = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=8.00,
        help_text="Horas normales de trabajo para esta jornada"
    )
    es_nocturno = models.BooleanField(
        default=False,
        help_text="Indica si es turno nocturno (cruza medianoche)"
    )

    def save(self, *args, **kwargs):
        # Asignar valores automáticamente según el tipo de jornada
        if self.tipo_jornada == 'manana':
            self.hora_inicio = time(6, 0)
            self.hora_fin = time(14, 0)
            self.horas_normales = 8.00
            self.es_nocturno = False
        elif self.tipo_jornada == 'tarde':
            self.hora_inicio = time(14, 0)
            self.hora_fin = time(22, 0)
            self.horas_normales = 8.00
            self.es_nocturno = False
        elif self.tipo_jornada == 'nocturno':
            self.hora_inicio = time(22, 0)
            self.hora_fin = time(6, 0)
            self.horas_normales = 8.00
            self.es_nocturno = True
        
        super().save(*args, **kwargs)

    def clean(self):
        """Validación para turnos nocturnos"""
        if self.es_nocturno and self.hora_inicio <= self.hora_fin:
            # Para turnos nocturnos, la hora de inicio debe ser mayor que la de fin
            pass
        elif not self.es_nocturno and self.hora_inicio >= self.hora_fin:
            raise ValidationError(
                "Para jornadas diurnas, la hora de inicio debe ser menor que la hora de fin"
            )

    def calcular_horas_trabajadas(self, entrada, salida):
        """
        Calcula las horas trabajadas dados los timestamps de entrada y salida.
        Solo cuenta las horas trabajadas dentro del rango de la jornada laboral.
        Si el empleado llega 1 hora antes, esa hora extra no se contabiliza.
        El tiempo empieza a correr a partir de la hora de inicio de la jornada.
        RETORNA LAS HORAS TOTALES TRABAJADAS (normales + extras).
        """
        if not entrada or not salida:
            return 0
        
        # Convertir a datetime locales para facilitar el cálculo
        entrada_dt = entrada if hasattr(entrada, 'date') else entrada
        salida_dt = salida if hasattr(salida, 'date') else salida
        
        # Asegurar que salida sea posterior a entrada
        if salida_dt <= entrada_dt:
            # Si la salida es anterior o igual a la entrada, no hay tiempo trabajado válido
            return 0
        
        # Obtener las fechas y horas
        fecha_entrada = entrada_dt.date()
        hora_entrada = entrada_dt.time()
        hora_salida = salida_dt.time()
        
        # Crear datetime para el inicio y fin de la jornada laboral
        if self.es_nocturno:
            # Para turnos nocturnos (ej: 22:00 - 06:00)
            # El inicio es el mismo día de entrada
            inicio_jornada = datetime.combine(fecha_entrada, self.hora_inicio)
            # El fin es al día siguiente
            fin_jornada = datetime.combine(fecha_entrada + timedelta(days=1), self.hora_fin)
        else:
            # Para turnos diurnos (ej: 06:00 - 14:00 o 14:00 - 22:00)
            inicio_jornada = datetime.combine(fecha_entrada, self.hora_inicio)
            fin_jornada = datetime.combine(fecha_entrada, self.hora_fin)
        
        # Hacer timezone aware si es necesario
        if hasattr(entrada_dt, 'tzinfo') and entrada_dt.tzinfo:
            from django.utils import timezone
            inicio_jornada = timezone.make_aware(inicio_jornada)
            fin_jornada = timezone.make_aware(fin_jornada)
        
        # Ajustar la entrada: no puede ser antes del inicio de la jornada
        entrada_efectiva = max(entrada_dt, inicio_jornada)
        
        # Para el cálculo total, considerar hasta donde realmente salió
        # (incluyendo horas extras)
        salida_efectiva = salida_dt
        
        # Si la entrada efectiva es después de la salida, no hay tiempo trabajado
        if entrada_efectiva >= salida_efectiva:
            return 0
        
        # Calcular la diferencia de tiempo total (incluyendo horas extras)
        tiempo_trabajado = salida_efectiva - entrada_efectiva
        
        # Convertir a horas decimales
        horas = tiempo_trabajado.total_seconds() / 3600
        
        # Validar que no sea un tiempo excesivo (más de 24 horas indica error)
        if horas > 24:
            # Probablemente hay un error en los datos, limitar a un máximo razonable
            return 0
        
        return round(horas, 2)

    def calcular_horas_normales_y_extras(self, entrada, salida):
        """
        Calcula por separado las horas normales (dentro de jornada) y las horas extras.
        Retorna un diccionario con:
        - horas_normales: horas trabajadas dentro de la jornada laboral
        - horas_extras: horas trabajadas fuera de la jornada laboral
        - horas_totales: suma de normales + extras
        """
        if not entrada or not salida:
            return {
                'horas_normales': 0,
                'horas_extras': 0,
                'horas_totales': 0
            }
        
        # Convertir a datetime locales para facilitar el cálculo
        entrada_dt = entrada if hasattr(entrada, 'date') else entrada
        salida_dt = salida if hasattr(salida, 'date') else salida
        
        # Asegurar que salida sea posterior a entrada
        if salida_dt <= entrada_dt:
            return {
                'horas_normales': 0,
                'horas_extras': 0,
                'horas_totales': 0
            }
        
        # Obtener las fechas
        fecha_entrada = entrada_dt.date()
        
        # Crear datetime para el inicio y fin de la jornada laboral
        if self.es_nocturno:
            # Para turnos nocturnos (ej: 22:00 - 06:00)
            inicio_jornada = datetime.combine(fecha_entrada, self.hora_inicio)
            fin_jornada = datetime.combine(fecha_entrada + timedelta(days=1), self.hora_fin)
        else:
            # Para turnos diurnos (ej: 06:00 - 14:00 o 14:00 - 22:00)
            inicio_jornada = datetime.combine(fecha_entrada, self.hora_inicio)
            fin_jornada = datetime.combine(fecha_entrada, self.hora_fin)
        
        # Hacer timezone aware si es necesario
        if hasattr(entrada_dt, 'tzinfo') and entrada_dt.tzinfo:
            from django.utils import timezone
            inicio_jornada = timezone.make_aware(inicio_jornada)
            fin_jornada = timezone.make_aware(fin_jornada)
        
        # Ajustar la entrada: no puede ser antes del inicio de la jornada
        entrada_efectiva = max(entrada_dt, inicio_jornada)
        
        # Calcular horas normales (dentro de la jornada)
        salida_normal = min(salida_dt, fin_jornada)
        if entrada_efectiva < salida_normal:
            tiempo_normal = salida_normal - entrada_efectiva
            horas_normales = round(tiempo_normal.total_seconds() / 3600, 2)
        else:
            horas_normales = 0
        
        # Calcular horas extras (después del fin de jornada)
        horas_extras = 0
        if salida_dt > fin_jornada:
            tiempo_extra = salida_dt - fin_jornada
            horas_extras = round(tiempo_extra.total_seconds() / 3600, 2)
        
        # Calcular total
        horas_totales = round(horas_normales + horas_extras, 2)
        
        return {
            'horas_normales': horas_normales,
            'horas_extras': horas_extras,
            'horas_totales': horas_totales
        }

    def calcular_horas_extras(self, horas_trabajadas):
        """
        Calcula las horas extras basadas en las horas trabajadas
        """
        if horas_trabajadas > self.horas_normales:
            return round(horas_trabajadas - float(self.horas_normales), 2)
        return 0

    def calcular_horas_trabajadas_formato(self, entrada, salida):
        """
        Calcula las horas trabajadas y las devuelve en formato HH:MM
        """
        horas_decimal = self.calcular_horas_trabajadas(entrada, salida)
        return decimal_a_tiempo(horas_decimal)

    def calcular_horas_extras_formato(self, horas_trabajadas):
        """
        Calcula las horas extras y las devuelve en formato HH:MM
        """
        horas_extras = self.calcular_horas_extras(horas_trabajadas)
        return decimal_a_tiempo(horas_extras)

    def esta_en_horario(self, timestamp):
        """
        Verifica si un timestamp está dentro del horario de esta jornada
        """
        hora = timestamp.time()
        
        if self.es_nocturno:
            # Para turnos nocturnos (ej: 22:00 - 6:00)
            return hora >= self.hora_inicio or hora <= self.hora_fin
        else:
            # Para turnos diurnos (ej: 6:00 - 14:00)
            return self.hora_inicio <= hora <= self.hora_fin

    def __str__(self):
        return f"{self.nombre} ({self.hora_inicio} - {self.hora_fin})"

    class Meta:
        verbose_name = "Jornada Laboral"
        verbose_name_plural = "Jornadas Laborales"

class EstacionServicio(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    jefe = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jefe_de_patio'
    )

    def __str__(self):
        return self.nombre

class UsuarioBiometrico(models.Model):
    biometrico_id = models.IntegerField(
        null=True,
        blank=True
        )  # ID biométrico en el dispositivo

    nombre = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    privilegio = models.IntegerField(
        default=0
    )
    activo = models.BooleanField(
        default=True
    )
    turno = models.ForeignKey(
        JornadaLaboral,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    jefe = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empleados'
    )
    estacion = models.ForeignKey(
        EstacionServicio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_biometricos'
    )

    def __str__(self):
        return f"{self.nombre}"

    def calcular_horas_dia(self, fecha):
        """
        Calcula las horas trabajadas en un día específico basándose únicamente 
        en los registros biométricos, sin depender de jornadas laborales predefinidas.
        Sistema dinámico y flexible que detecta automáticamente los patrones de trabajo.
        """
        from datetime import datetime, timedelta
        
        # Verificar si hay una jornada especial activa para esta fecha
        jornada_especial = JornadaEspecial.objects.filter(
            empleado=self,
            activa=True,
            fecha_inicio__lte=fecha,
            fecha_fin__gte=fecha
        ).first()
        
        if jornada_especial:
            return self._calcular_horas_jornada_especial(fecha, jornada_especial)
        
        # Buscar registros biométricos para esta fecha
        # Ampliamos el rango para detectar turnos nocturnos automáticamente
        fecha_inicio = datetime.combine(fecha - timedelta(days=1), datetime.min.time().replace(hour=14))  # Desde 2 PM del día anterior
        fecha_fin = datetime.combine(fecha + timedelta(days=1), datetime.min.time().replace(hour=14))     # Hasta 2 PM del día siguiente
        
        registros = RegistroAsistencia.objects.filter(
            user=self,
            timestamp__gte=timezone.make_aware(fecha_inicio),
            timestamp__lte=timezone.make_aware(fecha_fin)
        ).order_by('timestamp')
        
        if registros.count() == 0:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'horas_normales': 0,
                'registros': [],
                'estado': 'sin_registros',
                'mensaje': 'No hay registros biométricos para este día',
                'entrada': None,
                'salida': None
            }
        
        # Separar entradas y salidas
        entradas = registros.filter(status=0).order_by('timestamp')  # Status 0 = Entrada
        salidas = registros.exclude(status=0).order_by('timestamp')   # Cualquier status != 0 = Salida
        
        # Análisis dinámico de patrones de trabajo
        if entradas.count() == 0:
            # NUEVO: Manejar casos donde solo hay salidas
            # Esto es común cuando el biométrico no registra entradas correctamente
            if salidas.count() > 0:
                return self._calcular_horas_solo_salidas(fecha, list(salidas))
            else:
                return {
                    'horas_trabajadas': 0,
                    'horas_extras': 0,
                    'horas_normales': 0,
                    'registros': list(registros),
                    'estado': 'sin_entradas',
                    'mensaje': 'No hay registros de entrada',
                    'entrada': None,
                    'salida': None
                }
        
        if salidas.count() == 0:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'horas_normales': 0,
                'registros': list(registros),
                'entrada': entradas.first(),
                'salida': None,
                'estado': 'falta_salida',
                'mensaje': 'Falta registro de salida'
            }
        
        # Detectar automáticamente el tipo de turno basado en horarios
        primera_entrada = entradas.first()
        ultima_salida = salidas.last()
        
        # Determinar si es turno nocturno (entrada después de las 6 PM o antes de las 6 AM)
        hora_entrada = primera_entrada.timestamp.hour
        es_turno_nocturno = hora_entrada >= 18 or hora_entrada <= 6
        
        # Lógica para turnos nocturnos
        if es_turno_nocturno:
            # Para turnos nocturnos, buscar entrada del día anterior o noche del día
            # y salida en la madrugada/mañana del día actual
            
            # Buscar la entrada más apropiada (última entrada de la noche anterior o primera del día)
            fecha_noche_anterior = datetime.combine(fecha - timedelta(days=1), datetime.min.time().replace(hour=18))
            fecha_dia_actual = datetime.combine(fecha, datetime.min.time().replace(hour=12))
            
            entradas_periodo = entradas.filter(
                timestamp__gte=timezone.make_aware(fecha_noche_anterior),
                timestamp__lte=timezone.make_aware(fecha_dia_actual)
            )
            
            # Buscar salida en la madrugada/mañana del día actual
            fecha_madrugada = datetime.combine(fecha, datetime.min.time())
            fecha_mediodia = datetime.combine(fecha, datetime.min.time().replace(hour=14))
            
            salidas_periodo = salidas.filter(
                timestamp__gte=timezone.make_aware(fecha_madrugada),
                timestamp__lte=timezone.make_aware(fecha_mediodia)
            )
            
            if entradas_periodo.exists() and salidas_periodo.exists():
                entrada_efectiva = entradas_periodo.last()  # Última entrada de la noche
                salida_efectiva = salidas_periodo.first()   # Primera salida de la mañana
            else:
                # Fallback: usar primera entrada y última salida disponibles
                entrada_efectiva = primera_entrada
                salida_efectiva = ultima_salida
        else:
            # Para turnos diurnos, tomar primera entrada y última salida del día
            fecha_inicio_dia = datetime.combine(fecha, datetime.min.time())
            fecha_fin_dia = datetime.combine(fecha, datetime.max.time())
            
            entradas_dia = entradas.filter(
                timestamp__gte=timezone.make_aware(fecha_inicio_dia),
                timestamp__lte=timezone.make_aware(fecha_fin_dia)
            )
            
            salidas_dia = salidas.filter(
                timestamp__gte=timezone.make_aware(fecha_inicio_dia),
                timestamp__lte=timezone.make_aware(fecha_fin_dia)
            )
            
            if entradas_dia.exists() and salidas_dia.exists():
                entrada_efectiva = entradas_dia.first()
                salida_efectiva = salidas_dia.last()
            else:
                # Fallback: usar registros más cercanos
                entrada_efectiva = primera_entrada
                salida_efectiva = ultima_salida
        
        # Verificar que tengamos entrada y salida válidas
        if not entrada_efectiva or not salida_efectiva:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'horas_normales': 0,
                'registros': list(registros),
                'entrada': entrada_efectiva,
                'salida': salida_efectiva,
                'estado': 'registros_incompletos',
                'mensaje': 'No se pudo determinar par entrada-salida válido'
            }
        
        # Verificar que la salida sea posterior a la entrada
        if salida_efectiva.timestamp <= entrada_efectiva.timestamp:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'horas_normales': 0,
                'registros': list(registros),
                'entrada': entrada_efectiva,
                'salida': salida_efectiva,
                'estado': 'orden_invalido',
                'mensaje': 'La salida debe ser posterior a la entrada'
            }
        
        # Calcular horas trabajadas usando la jornada laboral del usuario si está asignada
        if hasattr(self, 'turno') and self.turno:
            # Usar la función que respeta los horarios establecidos del turno
            calculo_detallado = self.turno.calcular_horas_normales_y_extras(
                entrada_efectiva.timestamp, 
                salida_efectiva.timestamp
            )
            horas_trabajadas = calculo_detallado['horas_totales']
            horas_normales = calculo_detallado['horas_normales']
            horas_extras = calculo_detallado['horas_extras']
        else:
            # Fallback: usar cálculo tradicional para usuarios sin turno asignado
            tiempo_trabajado = salida_efectiva.timestamp - entrada_efectiva.timestamp
            horas_trabajadas = tiempo_trabajado.total_seconds() / 3600
            
            # Aplicar lógica de horas extras dinámicamente
            # Considerar horas extras después de 8 horas para jornadas normales
            # o después de 12 horas para jornadas especiales detectadas automáticamente
            
            # Detectar si es jornada extendida (más de 10 horas indica posible jornada de 12 horas)
            if horas_trabajadas > 10:
                # Jornada extendida - probablemente 12 horas
                horas_normales = min(12, horas_trabajadas)
                horas_extras = max(0, horas_trabajadas - 12)
            else:
                # Jornada normal - 8 horas
                horas_normales = min(8, horas_trabajadas)
                horas_extras = max(0, horas_trabajadas - 8)
        
        # Determinar estado y mensaje
        if horas_trabajadas == 0:
            estado = 'sin_tiempo'
            mensaje = 'No se pudo calcular tiempo trabajado'
        elif horas_extras > 0:
            estado = 'con_extras'
            tipo_turno = 'nocturno' if es_turno_nocturno else 'diurno'
            mensaje = f'Turno {tipo_turno} - {decimal_a_tiempo(horas_normales)} normales + {decimal_a_tiempo(horas_extras)} extras'
        else:
            estado = 'normal'
            tipo_turno = 'nocturno' if es_turno_nocturno else 'diurno'
            mensaje = f'Turno {tipo_turno} - {decimal_a_tiempo(horas_normales)} horas trabajadas'
        
        return {
            'horas_trabajadas': horas_trabajadas,
            'horas_extras': horas_extras,
            'horas_normales': horas_normales,
            'horas_trabajadas_formato': decimal_a_tiempo(horas_trabajadas),
            'horas_extras_formato': decimal_a_tiempo(horas_extras),
            'horas_normales_formato': decimal_a_tiempo(horas_normales),
            'registros': list(registros),
            'entrada': entrada_efectiva,
            'salida': salida_efectiva,
            'estado': estado,
            'mensaje': mensaje,
            'es_turno_nocturno': es_turno_nocturno,
            'deteccion_automatica': True
        }

    def _calcular_horas_jornada_especial(self, fecha, jornada_especial):
        """
        Calcula las horas trabajadas para jornadas especiales de 12 horas
        Lógica: marca la primera entrada del día y la salida sea el siguiente registro
        sin importar que sea del día siguiente
        """
        from datetime import datetime, timedelta
        
        # Para jornadas especiales, buscar en un rango amplio que incluya el día siguiente
        fecha_inicio = datetime.combine(fecha, datetime.min.time())
        fecha_fin = datetime.combine(fecha + timedelta(days=2), datetime.max.time())
        
        # Obtener todos los registros del empleado en el rango de fechas
        registros = RegistroAsistencia.objects.filter(
            user=self,
            timestamp__gte=timezone.make_aware(fecha_inicio),
            timestamp__lte=timezone.make_aware(fecha_fin)
        ).order_by('timestamp')
        
        if registros.count() == 0:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'registros': list(registros),
                'estado': 'sin_registros',
                'mensaje': 'No hay registros para esta jornada especial',
                'jornada_especial': True
            }
        
        # Buscar la primera entrada del día
        primera_entrada = None
        siguiente_salida = None
        
        for registro in registros:
            # Si encontramos una entrada y aún no tenemos una
            if registro.status == 0 and primera_entrada is None:
                # Verificar que la entrada sea en la fecha de la jornada especial
                if registro.timestamp.date() == fecha:
                    primera_entrada = registro
            
            # Si ya tenemos una entrada, buscar la siguiente salida
            elif primera_entrada and registro.status == 1 and siguiente_salida is None:
                siguiente_salida = registro
                break
        
        if not primera_entrada:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'registros': list(registros),
                'entrada': None,
                'salida': None,
                'estado': 'falta_entrada',
                'mensaje': 'No se encontró entrada para esta jornada especial',
                'jornada_especial': True
            }
        
        if not siguiente_salida:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'registros': list(registros),
                'entrada': primera_entrada,
                'salida': None,
                'estado': 'falta_salida',
                'mensaje': 'No se encontró salida para esta jornada especial',
                'jornada_especial': True
            }
        
        # Calcular horas usando el método de la jornada especial
        detalle_horas = jornada_especial.calcular_horas_trabajadas(
            primera_entrada.timestamp, 
            siguiente_salida.timestamp
        )
        
        horas_trabajadas = detalle_horas['horas_totales']
        horas_extras = detalle_horas['horas_extras']
        horas_normales = detalle_horas['horas_normales']
        
        # Determinar estado
        if horas_trabajadas == 0:
            estado = 'sin_tiempo'
            mensaje = 'No se pudo calcular tiempo trabajado en jornada especial'
        elif horas_extras > 0:
            estado = 'jornada_especial_con_extras'
            mensaje = f'Jornada especial: {decimal_a_tiempo(horas_normales)} normales + {decimal_a_tiempo(horas_extras)} extras'
        else:
            estado = 'jornada_especial_normal'
            mensaje = f'Jornada especial: {decimal_a_tiempo(horas_normales)} horas'
        
        return {
            'horas_trabajadas': horas_trabajadas,
            'horas_extras': horas_extras,
            'horas_normales': horas_normales,
            'horas_trabajadas_formato': decimal_a_tiempo(horas_trabajadas),
            'horas_extras_formato': decimal_a_tiempo(horas_extras),
            'horas_normales_formato': decimal_a_tiempo(horas_normales),
            'registros': list(registros),
            'entrada': primera_entrada,
            'salida': siguiente_salida,
            'estado': estado,
            'mensaje': mensaje,
            'jornada_especial': True,
            'jornada_especial_info': jornada_especial
        }

    def calcular_resumen_semanal(self, fecha_inicio_semana):
        """
        Calcula el resumen semanal para un empleado desde domingo hasta lunes
        """
        from datetime import timedelta
        
        # Calcular fecha fin (lunes siguiente)
        fecha_fin_semana = fecha_inicio_semana + timedelta(days=7)
        
        return self.calcular_resumen_rango_fechas(fecha_inicio_semana, fecha_fin_semana)

    def calcular_resumen_rango_fechas(self, fecha_inicio, fecha_fin):
        """
        Calcula el resumen para un empleado en un rango de fechas específico
        """
        from datetime import timedelta
        
        # Inicializar contadores
        horas_normales = 0
        horas_extra_diurno = 0
        horas_extra_nocturno = 0
        horas_extra_feriado_diurno = 0
        horas_extra_feriado_nocturno = 0
        
        # Obtener feriados del rango
        feriados = set(
            FeriadoNacional.objects.filter(
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin,
                activo=True
            ).values_list('fecha', flat=True)
        )
        
        # Calcular día por día
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            calculo_dia = self.calcular_horas_dia(current_date)
            
            if calculo_dia['horas_trabajadas'] > 0:
                horas_normales += calculo_dia['horas_normales']
                
                # Clasificar horas extras
                if calculo_dia['horas_extras'] > 0:
                    es_feriado = current_date in feriados
                    es_nocturno = self.turno and self.turno.es_nocturno
                    
                    if es_feriado and es_nocturno:
                        horas_extra_feriado_nocturno += calculo_dia['horas_extras']
                    elif es_feriado and not es_nocturno:
                        horas_extra_feriado_diurno += calculo_dia['horas_extras']
                    elif not es_feriado and es_nocturno:
                        horas_extra_nocturno += calculo_dia['horas_extras']
                    else:
                        horas_extra_diurno += calculo_dia['horas_extras']
            
            current_date += timedelta(days=1)
        
        # Calcular totales
        total_horas_extras = (
            horas_extra_diurno + 
            horas_extra_nocturno + 
            horas_extra_feriado_diurno + 
            horas_extra_feriado_nocturno
        )
        total_horas_trabajadas = horas_normales + total_horas_extras
        
        # Calcular costos (obtener tarifas actuales)
        try:
            tarifas = {
                tarifa.tipo: tarifa.tarifa_por_hora
                for tarifa in TarifaHoraExtra.objects.filter(activa=True)
            }
            
            costo_horas_extra_diurno = horas_extra_diurno * tarifas.get('diurno', 0)
            costo_horas_extra_nocturno = horas_extra_nocturno * tarifas.get('nocturno', 0)
            costo_horas_extra_feriado_diurno = horas_extra_feriado_diurno * tarifas.get('feriado_diurno', 0)
            costo_horas_extra_feriado_nocturno = horas_extra_feriado_nocturno * tarifas.get('feriado_nocturno', 0)
            
            costo_total_horas_extras = (
                costo_horas_extra_diurno + 
                costo_horas_extra_nocturno + 
                costo_horas_extra_feriado_diurno + 
                costo_horas_extra_feriado_nocturno
            )
        except:
            costo_horas_extra_diurno = 0
            costo_horas_extra_nocturno = 0
            costo_horas_extra_feriado_diurno = 0
            costo_horas_extra_feriado_nocturno = 0
            costo_total_horas_extras = 0
        
        return {
            'fecha_inicio_semana': fecha_inicio,  # Reutilizar campos existentes
            'fecha_fin_semana': fecha_fin,
            'horas_normales': horas_normales,
            'horas_extra_diurno': horas_extra_diurno,
            'horas_extra_nocturno': horas_extra_nocturno,
            'horas_extra_feriado_diurno': horas_extra_feriado_diurno,
            'horas_extra_feriado_nocturno': horas_extra_feriado_nocturno,
            'total_horas_extras': total_horas_extras,
            'total_horas_trabajadas': total_horas_trabajadas,
            'costo_horas_extra_diurno': costo_horas_extra_diurno,
            'costo_horas_extra_nocturno': costo_horas_extra_nocturno,
            'costo_horas_extra_feriado_diurno': costo_horas_extra_feriado_diurno,
            'costo_horas_extra_feriado_nocturno': costo_horas_extra_feriado_nocturno,
            'costo_total_horas_extras': costo_total_horas_extras,
        }

    def obtener_registros_periodo(self, fecha_inicio, fecha_fin):
        """
        Obtiene todos los cálculos de horas para un período
        """
        from datetime import datetime, timedelta
        
        resultados = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            calculo = self.calcular_horas_dia(fecha_actual)
            if calculo['horas_trabajadas'] > 0:
                calculo['fecha'] = fecha_actual
                resultados.append(calculo)
            fecha_actual += timedelta(days=1)
        
        return resultados

    def _calcular_horas_solo_salidas(self, fecha, registros_salida):
        """
        Calcula horas trabajadas cuando solo hay registros de salida.
        Utiliza patrones inteligentes para inferir la hora de entrada.
        """
        from decimal import Decimal
        from datetime import datetime, timedelta
        
        if not registros_salida:
            return self._resultado_vacio()
        
        # Ordenar salidas por hora
        salidas = sorted(registros_salida, key=lambda x: x.timestamp.time())
        
        # Determinar tipo de jornada basado en la hora de salida
        primera_salida = salidas[0].timestamp.time()
        
        # Detectar si es turno nocturno o diurno
        if primera_salida.hour >= 22 or primera_salida.hour <= 6:
            # Turno nocturno - típicamente trabajan de 22:00 a 06:00
            tipo_jornada = 'nocturno'
            duracion_estandar = 8  # 8 horas estándar
            if primera_salida.hour <= 6:
                # Salida en la madrugada, entrada el día anterior
                hora_entrada_estimada = (datetime.combine(fecha, primera_salida) - timedelta(hours=duracion_estandar)).time()
            else:
                # Salida en la noche, entrada el mismo día
                hora_entrada_estimada = (datetime.combine(fecha, primera_salida) - timedelta(hours=duracion_estandar)).time()
        else:
            # Turno diurno - detectar patrón basado en hora de salida
            tipo_jornada = 'diurno'
            
            if primera_salida.hour <= 12:
                # Salida matutina (media jornada o jornada especial)
                duracion_estandar = 4
            elif primera_salida.hour <= 17:
                # Salida tarde normal (8 horas desde las 8-9 AM)
                duracion_estandar = 8
            else:
                # Salida nocturna (jornada extendida)
                duracion_estandar = 10
            
            # Calcular hora de entrada estimada
            hora_entrada_estimada = (datetime.combine(fecha, primera_salida) - timedelta(hours=duracion_estandar)).time()
        
        # Calcular horas totales basado en el patrón detectado
        total_horas = Decimal('0')
        ultima_salida = salidas[-1].timestamp.time()
        
        # Usar la duración estándar como base
        horas_calculadas = duracion_estandar
        
        # Si hay múltiples salidas, usar la última como referencia
        if len(salidas) > 1:
            # Ajustar si hay un patrón de múltiples salidas
            tiempo_entre_salidas = (datetime.combine(fecha, ultima_salida) - 
                                  datetime.combine(fecha, primera_salida)).seconds / 3600
            if tiempo_entre_salidas > 1:  # Si hay más de 1 hora entre salidas
                horas_calculadas += tiempo_entre_salidas * 0.5  # Agregar tiempo parcial
        
        total_horas = Decimal(str(horas_calculadas))
        
        # Calcular horas extras (todo lo que exceda 8 horas)
        horas_normales = min(total_horas, Decimal('8'))
        horas_extras = max(Decimal('0'), total_horas - Decimal('8'))
        
        # Calcular costos (usar valores por defecto simples por ahora)
        valor_hora_normal = Decimal('10000')  # $10,000 por hora
        valor_hora_extra = Decimal('15000')   # $15,000 por hora extra
        
        costo_normal = horas_normales * valor_hora_normal
        costo_extra = horas_extras * valor_hora_extra
        costo_total = costo_normal + costo_extra
        
        # Obtener datos adicionales para el resultado
        empleado_obj = self  # self es el objeto UsuarioBiometrico
        area = empleado_obj.estacion.nombre if empleado_obj.estacion else 'N/A'
        cargo = 'N/A'  # No hay campo cargo en UsuarioBiometrico
        
        return {
            'empleado': empleado_obj,
            'nombre_completo': empleado_obj.nombre,
            'area': area,
            'cargo': cargo,
            'fecha': fecha,
            'tipo_jornada': tipo_jornada,
            'observaciones': f'Calculado desde registros de salida únicamente (Patrón: {duracion_estandar}h)',
            'hora_entrada_estimada': hora_entrada_estimada,
            'hora_salida': ultima_salida,
            'horas_trabajadas': total_horas,
            'horas_normales': horas_normales,
            'horas_extras': horas_extras,
            'valor_hora_normal': valor_hora_normal,
            'valor_hora_extra': valor_hora_extra,
            'costo_horas_normales': costo_normal,
            'costo_horas_extras': costo_extra,
            'costo_total_horas_extras': costo_extra,
        }


class JornadaEspecial(models.Model):
    """
    Modelo para jornadas especiales de 12 horas que pueden pasar de un día a otro
    """
    empleado = models.ForeignKey(
        'UsuarioBiometrico',
        on_delete=models.CASCADE,
        related_name='jornadas_especiales'
    )
    fecha_inicio = models.DateField(
        help_text="Fecha en que inicia la jornada especial"
    )
    fecha_fin = models.DateField(
        help_text="Fecha en que termina la jornada especial (puede ser al día siguiente)"
    )
    hora_inicio_programada = models.TimeField(
        help_text="Hora programada de inicio de la jornada especial"
    )
    hora_fin_programada = models.TimeField(
        help_text="Hora programada de fin de la jornada especial"
    )
    horas_programadas = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=12.00,
        help_text="Horas programadas para esta jornada especial"
    )
    aprobada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'jefe_patio'},
        help_text="Jefe de patio que aprobó esta jornada especial"
    )
    fecha_aprobacion = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora en que se aprobó esta jornada especial"
    )
    activa = models.BooleanField(
        default=True,
        help_text="Indica si la jornada especial está activa"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones adicionales sobre la jornada especial"
    )

    def clean(self):
        """Validaciones del modelo"""
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio")
        
        # Validar que no hay solapamiento con otras jornadas especiales activas
        jornadas_solapadas = JornadaEspecial.objects.filter(
            empleado=self.empleado,
            activa=True,
            fecha_inicio__lte=self.fecha_fin,
            fecha_fin__gte=self.fecha_inicio
        )
        
        if self.pk:
            jornadas_solapadas = jornadas_solapadas.exclude(pk=self.pk)
        
        if jornadas_solapadas.exists():
            raise ValidationError("Ya existe una jornada especial activa para este empleado en las fechas seleccionadas")

    def esta_activa_en_fecha(self, fecha):
        """
        Verifica si la jornada especial está activa en una fecha específica
        """
        return (
            self.activa and 
            self.fecha_inicio <= fecha <= self.fecha_fin
        )

    def calcular_horas_trabajadas(self, entrada, salida):
        """
        Calcula las horas trabajadas para jornadas especiales de 12 horas
        Toma la primera entrada del día y la siguiente salida (puede ser del día siguiente)
        """
        if not entrada or not salida:
            return {
                'horas_normales': 0,
                'horas_extras': 0,
                'horas_totales': 0
            }
        
        # Convertir a datetime locales
        entrada_dt = entrada if hasattr(entrada, 'date') else entrada
        salida_dt = salida if hasattr(salida, 'date') else salida
        
        # Asegurar que salida sea posterior a entrada
        if salida_dt <= entrada_dt:
            return {
                'horas_normales': 0,
                'horas_extras': 0,
                'horas_totales': 0
            }
        
        # Calcular tiempo total trabajado
        tiempo_trabajado = salida_dt - entrada_dt
        horas_totales = round(tiempo_trabajado.total_seconds() / 3600, 2)
        
        # Para jornadas especiales de 12 horas:
        # - Hasta 12 horas son normales
        # - Más de 12 horas son extras
        if horas_totales <= 12:
            horas_normales = horas_totales
            horas_extras = 0
        else:
            horas_normales = 12.0
            horas_extras = round(horas_totales - 12.0, 2)
        
        return {
            'horas_normales': horas_normales,
            'horas_extras': horas_extras,
            'horas_totales': horas_totales
        }

    def __str__(self):
        return f"{self.empleado.nombre} - Jornada especial {self.fecha_inicio} al {self.fecha_fin}"

    class Meta:
        verbose_name = "Jornada Especial"
        verbose_name_plural = "Jornadas Especiales"
        ordering = ['-fecha_inicio']


class RegistroAsistencia(models.Model):
    user = models.ForeignKey('UsuarioBiometrico', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    nombre = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    estacion_servicio = models.ForeignKey(EstacionServicio, on_delete=models.CASCADE, null=True, blank=True)

    status = models.IntegerField(
        default=0
    )

    aprobado = models.BooleanField(
        null=True,
        blank=True,
        default=None,
        help_text="Aprobación de horas extra por el jefe de patio"
    )

    def __str__(self):
        return f"{self.user} - {self.timestamp}"

    @property
    def es_entrada(self):
        """Retorna True si es una entrada (status=0)"""
        return self.status == 0

    @property
    def es_salida(self):
        """Retorna True si es una salida (status=1)"""
        return self.status == 1

    @property
    def tipo_registro(self):
        """Retorna el tipo de registro como string"""
        return "Entrada" if self.es_entrada else "Salida"

    def esta_en_horario_normal(self):
        """
        Verifica si el registro está dentro del horario normal del empleado
        """
        try:
            if not self.user or not self.user.turno:
                return True
            
            # Verificar que el timestamp sea válido
            if not self.timestamp:
                return False
                
            return self.user.turno.esta_en_horario(self.timestamp)
        except Exception:
            # Si hay cualquier error (timezone, etc.), asumir que está en horario normal
            return True

    def calcular_tiempo_hasta_siguiente(self):
        """
        Calcula el tiempo hasta el siguiente registro del mismo usuario
        """
        try:
            if not self.timestamp or not self.user:
                return None
                
            siguiente = RegistroAsistencia.objects.filter(
                user=self.user,
                timestamp__gt=self.timestamp
            ).order_by('timestamp').first()
            
            if siguiente and siguiente.timestamp:
                return siguiente.timestamp - self.timestamp
            return None
        except Exception:
            # Si hay errores de timezone o consulta, retornar None
            return None

    def get_timestamp_safe(self):
        """
        Obtiene el timestamp de forma segura, manejando errores de timezone
        """
        try:
            if self.timestamp:
                from django.utils import timezone
                # Intentar convertir a timezone local
                return timezone.localtime(self.timestamp)
            return None
        except Exception:
            try:
                # Si falla, intentar retornar el timestamp raw
                return self.timestamp
            except Exception:
                # Si todo falla, retornar None
                return None

    def get_timestamp_string(self):
        """
        Obtiene el timestamp como string de forma segura
        """
        try:
            ts = self.get_timestamp_safe()
            if ts:
                return ts.strftime('%Y-%m-%d %H:%M:%S')
            return "Sin fecha"
        except Exception:
            return "Error en fecha"

    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"
        ordering = ['-id']  # Ordenar por ID en lugar de timestamp para evitar errores


class TarifaHoraExtra(models.Model):
    """
    Modelo para definir las tarifas de horas extras según el tipo
    """
    TIPO_CHOICES = [
        ('diurno', 'Diurno'),
        ('nocturno', 'Nocturno'),
        ('feriado_diurno', 'Feriado Diurno'),
        ('feriado_nocturno', 'Feriado Nocturno'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, unique=True)
    tarifa_por_hora = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Tarifa en pesos por hora extra"
    )
    activa = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.tarifa_por_hora}"
    
    class Meta:
        verbose_name = "Tarifa Hora Extra"
        verbose_name_plural = "Tarifas Horas Extras"


class ResumenSemanal(models.Model):
    """
    Modelo para almacenar el resumen semanal de horas trabajadas de cada empleado
    """
    empleado = models.ForeignKey(
        'UsuarioBiometrico',
        on_delete=models.CASCADE,
        related_name='resumenes_semanales'
    )
    
    # Rango de la semana (domingo a lunes)
    fecha_inicio_semana = models.DateField(
        help_text="Domingo que inicia la semana"
    )
    fecha_fin_semana = models.DateField(
        help_text="Lunes que termina la semana"
    )
    
    # Horas trabajadas
    horas_normales = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00
    )
    
    # Horas extras por tipo
    horas_extra_diurno = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00
    )
    horas_extra_nocturno = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00
    )
    horas_extra_feriado_diurno = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00
    )
    horas_extra_feriado_nocturno = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00
    )
    
    # Totales
    total_horas_trabajadas = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00
    )
    total_horas_extras = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00
    )
    
    # Costos calculados
    costo_horas_extra_diurno = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    costo_horas_extra_nocturno = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    costo_horas_extra_feriado_diurno = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    costo_horas_extra_feriado_nocturno = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    costo_total_horas_extras = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def calcular_numero_semana(self):
        """Calcula el número de semana del año"""
        return self.fecha_inicio_semana.isocalendar()[1]
    
    def calcular_costos(self):
        """Calcula los costos de las horas extras basado en las tarifas actuales"""
        from decimal import Decimal
        
        try:
            tarifa_diurno = TarifaHoraExtra.objects.get(tipo='diurno', activa=True)
            self.costo_horas_extra_diurno = Decimal(str(self.horas_extra_diurno)) * tarifa_diurno.tarifa_por_hora
        except TarifaHoraExtra.DoesNotExist:
            self.costo_horas_extra_diurno = Decimal('0')
            
        try:
            tarifa_nocturno = TarifaHoraExtra.objects.get(tipo='nocturno', activa=True)
            self.costo_horas_extra_nocturno = Decimal(str(self.horas_extra_nocturno)) * tarifa_nocturno.tarifa_por_hora
        except TarifaHoraExtra.DoesNotExist:
            self.costo_horas_extra_nocturno = Decimal('0')
            
        try:
            tarifa_feriado_diurno = TarifaHoraExtra.objects.get(tipo='feriado_diurno', activa=True)
            self.costo_horas_extra_feriado_diurno = Decimal(str(self.horas_extra_feriado_diurno)) * tarifa_feriado_diurno.tarifa_por_hora
        except TarifaHoraExtra.DoesNotExist:
            self.costo_horas_extra_feriado_diurno = Decimal('0')
            
        try:
            tarifa_feriado_nocturno = TarifaHoraExtra.objects.get(tipo='feriado_nocturno', activa=True)
            self.costo_horas_extra_feriado_nocturno = Decimal(str(self.horas_extra_feriado_nocturno)) * tarifa_feriado_nocturno.tarifa_por_hora
        except TarifaHoraExtra.DoesNotExist:
            self.costo_horas_extra_feriado_nocturno = Decimal('0')
            
        self.costo_total_horas_extras = (
            self.costo_horas_extra_diurno + 
            self.costo_horas_extra_nocturno + 
            self.costo_horas_extra_feriado_diurno + 
            self.costo_horas_extra_feriado_nocturno
        )
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        
        # Calcular totales
        self.total_horas_extras = (
            Decimal(str(self.horas_extra_diurno)) + 
            Decimal(str(self.horas_extra_nocturno)) + 
            Decimal(str(self.horas_extra_feriado_diurno)) + 
            Decimal(str(self.horas_extra_feriado_nocturno))
        )
        self.total_horas_trabajadas = Decimal(str(self.horas_normales)) + self.total_horas_extras
        
        # Calcular costos
        self.calcular_costos()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        semana_num = self.calcular_numero_semana()
        return f"{self.empleado.nombre} - Semana {semana_num} ({self.fecha_inicio_semana} al {self.fecha_fin_semana})"
    
    class Meta:
        verbose_name = "Resumen Semanal"
        verbose_name_plural = "Resúmenes Semanales"
        unique_together = ['empleado', 'fecha_inicio_semana']
        ordering = ['-fecha_inicio_semana', 'empleado__nombre']


class FeriadoNacional(models.Model):
    """
    Modelo para definir los feriados nacionales
    """
    fecha = models.DateField(unique=True)
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.fecha}"
    
    class Meta:
        verbose_name = "Feriado Nacional"
        verbose_name_plural = "Feriados Nacionales"
        ordering = ['fecha']




