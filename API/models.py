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
        ('manana', 'Mañana (6:00 - 14:00)'),
        ('tarde', 'Tarde (14:00 - 22:00)'),
        ('nocturno', 'Nocturno (22:00 - 6:00)'),
        ('personalizada', 'Personalizada'),
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
        Maneja correctamente los turnos nocturnos.
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
        
        # Calcular la diferencia de tiempo
        tiempo_trabajado = salida_dt - entrada_dt
        
        # Convertir a horas decimales
        horas = tiempo_trabajado.total_seconds() / 3600
        
        # Validar que no sea un tiempo excesivo (más de 24 horas indica error)
        if horas > 24:
            # Probablemente hay un error en los datos, limitar a un máximo razonable
            return 0
        
        return round(horas, 2)

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
    cedula = models.CharField(
        max_length=20,
        unique=True,
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
        Calcula las horas trabajadas en un día específico
        """
        from datetime import datetime, timedelta
        
        if not self.turno:
            return {
                'horas_trabajadas': 0, 
                'horas_extras': 0, 
                'registros': [],
                'estado': 'sin_jornada',
                'mensaje': 'Usuario sin jornada asignada'
            }
        
        # Para turnos nocturnos, buscar registros que correspondan a esa jornada
        if self.turno.es_nocturno:
            # Para turno nocturno del día X, buscar:
            # - Entrada: desde las 20:00 del día X-1 hasta las 23:59 del día X-1
            # - Salida: desde las 00:00 del día X hasta las 10:00 del día X
            fecha_inicio = datetime.combine(fecha - timedelta(days=1), datetime.min.time().replace(hour=20))
            fecha_fin = datetime.combine(fecha, datetime.min.time().replace(hour=10))
        else:
            # Para turnos diurnos, buscar en el mismo día
            fecha_inicio = datetime.combine(fecha, datetime.min.time())
            fecha_fin = datetime.combine(fecha, datetime.max.time())
        
        registros = RegistroAsistencia.objects.filter(
            user=self,
            timestamp__gte=timezone.make_aware(fecha_inicio),
            timestamp__lte=timezone.make_aware(fecha_fin)
        ).order_by('timestamp')
        
        # Buscar pares entrada-salida
        entradas = registros.filter(status=0)  # Entradas
        salidas = registros.filter(status=1)   # Salidas
        
        # Verificar estados de los registros
        if registros.count() == 0:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'registros': list(registros),
                'estado': 'sin_registros',
                'mensaje': 'No hay registros para este día'
            }
        
        if registros.count() == 1:
            registro = registros.first()
            if registro.status == 0:  # Solo entrada
                return {
                    'horas_trabajadas': 0,
                    'horas_extras': 0,
                    'registros': list(registros),
                    'entrada': registro,
                    'salida': None,
                    'estado': 'falta_salida',
                    'mensaje': 'Falta registro de salida'
                }
            else:  # Solo salida
                return {
                    'horas_trabajadas': 0,
                    'horas_extras': 0,
                    'registros': list(registros),
                    'entrada': None,
                    'salida': registro,
                    'estado': 'falta_entrada',
                    'mensaje': 'Falta registro de entrada'
                }
        
        if not entradas.exists():
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'registros': list(registros),
                'estado': 'sin_entradas',
                'mensaje': 'No hay registros de entrada'
            }
        
        if not salidas.exists():
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'registros': list(registros),
                'entrada': entradas.first(),
                'salida': None,
                'estado': 'falta_salida',
                'mensaje': 'Falta registro de salida'
            }
        
        # Para turnos nocturnos, tomar la última entrada del día anterior y la primera salida del día actual
        if self.turno.es_nocturno:
            # Entrada: última del día anterior (después de las 20:00)
            entrada_limite = timezone.make_aware(datetime.combine(fecha - timedelta(days=1), datetime.min.time().replace(hour=20)))
            entrada = entradas.filter(timestamp__gte=entrada_limite).last()
            
            # Salida: primera del día actual (antes de las 10:00)  
            salida_limite = timezone.make_aware(datetime.combine(fecha, datetime.min.time().replace(hour=10)))
            salida = salidas.filter(timestamp__lte=salida_limite).first()
        else:
            # Para turnos diurnos, tomar la primera entrada y última salida del día
            entrada = entradas.first()
            salida = salidas.last()
        
        if not entrada:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'registros': list(registros),
                'entrada': None,
                'salida': salida,
                'estado': 'falta_entrada',
                'mensaje': 'No se encontró entrada válida para esta jornada'
            }
        
        if not salida:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'registros': list(registros),
                'entrada': entrada,
                'salida': None,
                'estado': 'falta_salida',
                'mensaje': 'No se encontró salida válida para esta jornada'
            }
        
        # Verificar si entrada y salida son iguales (mismo timestamp)
        if entrada.timestamp == salida.timestamp:
            return {
                'horas_trabajadas': 0,
                'horas_extras': 0,
                'registros': list(registros),
                'entrada': entrada,
                'salida': salida,
                'estado': 'registros_iguales',
                'mensaje': 'Entrada y salida tienen el mismo horario - Registro incompleto'
            }
        
        # Calcular horas trabajadas
        horas_trabajadas = self.turno.calcular_horas_trabajadas(entrada.timestamp, salida.timestamp)
        horas_extras = self.turno.calcular_horas_extras(horas_trabajadas)
        
        # Determinar estado basado en horas trabajadas
        if horas_trabajadas == 0:
            estado = 'sin_tiempo'
            mensaje = 'No se pudo calcular tiempo trabajado'
        elif horas_extras > 0:
            estado = 'con_extras'
            mensaje = f'Jornada completa con {decimal_a_tiempo(horas_extras)} de horas extras'
        else:
            estado = 'normal'
            mensaje = 'Jornada completa normal'
        
        return {
            'horas_trabajadas': horas_trabajadas,
            'horas_extras': horas_extras,
            'horas_trabajadas_formato': decimal_a_tiempo(horas_trabajadas),
            'horas_extras_formato': decimal_a_tiempo(horas_extras),
            'horas_normales_formato': decimal_a_tiempo(float(self.turno.horas_normales)),
            'registros': list(registros),
            'entrada': entrada,
            'salida': salida,
            'estado': estado,
            'mensaje': mensaje
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
        if not self.user.turno:
            return True
        
        return self.user.turno.esta_en_horario(self.timestamp)

    def calcular_tiempo_hasta_siguiente(self):
        """
        Calcula el tiempo hasta el siguiente registro del mismo usuario
        """
        siguiente = RegistroAsistencia.objects.filter(
            user=self.user,
            timestamp__gt=self.timestamp
        ).order_by('timestamp').first()
        
        if siguiente:
            return siguiente.timestamp - self.timestamp
        return None

    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"
        ordering = ['-timestamp']




