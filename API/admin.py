from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CustomUser, UsuarioBiometrico, JornadaLaboral, RegistroAsistencia, EstacionServicio

# ---------- Admin CustomUser ----------
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'estacion', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('rol', 'estacion', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'estacion__nombre')
    readonly_fields = ('date_joined', 'last_login')
    list_per_page = 25

    fieldsets = (
        ('Información Personal', {
            'fields': ('username', 'password', 'email', 'first_name', 'last_name')
        }),
        ('Permisos y Roles', {
            'fields': ('rol', 'estacion', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas Importantes', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Información Básica', {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name'),
        }),
        ('Permisos y Roles', {
            'classes': ('wide',),
            'fields': ('rol', 'estacion', 'is_staff', 'is_active', 'is_superuser'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('estacion')


# ---------- Admin UsuarioBiometrico ----------
@admin.register(UsuarioBiometrico)
class UsuarioBiometricoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula', 'biometrico_id', 'privilegio', 'activo', 'turno', 'jefe', 'estacion', 'ver_registros')
    list_filter = ('activo', 'privilegio', 'turno', 'estacion', 'jefe')
    search_fields = ('nombre', 'cedula', 'biometrico_id', 'jefe__username', 'estacion__nombre')
    autocomplete_fields = ['jefe', 'turno', 'estacion']
    list_editable = ('activo', 'privilegio')
    list_per_page = 25
    ordering = ('nombre',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'cedula', 'biometrico_id')
        }),
        ('Configuración de Acceso', {
            'fields': ('privilegio', 'activo')
        }),
        ('Asignaciones Laborales', {
            'fields': ('turno', 'jefe', 'estacion')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('turno', 'jefe', 'estacion')

    def ver_registros(self, obj):
        count = RegistroAsistencia.objects.filter(user=obj).count()
        url = reverse('admin:API_registroasistencia_changelist') + f'?user__id__exact={obj.id}'
        return format_html('<a href="{}">{} registros</a>', url, count)
    ver_registros.short_description = 'Registros'
    ver_registros.admin_order_field = 'registros_count'

    actions = ['activar_usuarios', 'desactivar_usuarios']

    def activar_usuarios(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} usuarios activados correctamente.')
    activar_usuarios.short_description = "Activar usuarios seleccionados"

    def desactivar_usuarios(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} usuarios desactivados correctamente.')
    desactivar_usuarios.short_description = "Desactivar usuarios seleccionados"


# ---------- Admin JornadaLaboral ----------
@admin.register(JornadaLaboral)
class JornadaLaboralAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_jornada', 'hora_inicio', 'hora_fin', 'horas_normales', 'es_nocturno', 'empleados_asignados')
    list_filter = ('tipo_jornada', 'es_nocturno')
    search_fields = ('nombre',)
    ordering = ('tipo_jornada', 'hora_inicio')
    list_per_page = 20

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo_jornada')
        }),
        ('Horarios', {
            'fields': ('hora_inicio', 'hora_fin', 'horas_normales', 'es_nocturno'),
            'description': 'Para jornadas personalizadas, configure manualmente los horarios.'
        }),
    )

    readonly_fields = ('empleados_asignados',)

    def empleados_asignados(self, obj):
        count = obj.usuariobiometrico_set.count()
        if count > 0:
            url = reverse('admin:API_usuariobiometrico_changelist') + f'?turno__id__exact={obj.id}'
            return format_html('<a href="{}">{} empleados</a>', url, count)
        return "0 empleados"
    empleados_asignados.short_description = 'Empleados Asignados'

    def save_model(self, request, obj, form, change):
        """Guardar con validación personalizada"""
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except Exception as e:
            self.message_user(request, f'Error al guardar: {str(e)}', level='ERROR')


# ---------- Admin RegistroAsistencia ----------
@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('user_safe', 'nombre', 'timestamp_safe', 'tipo_registro', 'estacion_servicio_safe', 'aprobado_safe')
    list_filter = ('status', 'aprobado', 'estacion_servicio')
    search_fields = ('user__nombre', 'user__cedula', 'nombre', 'estacion_servicio__nombre')
    list_per_page = 50
    ordering = ('-id',)  # Usar ID en lugar de timestamp para evitar errores
    
    fieldsets = (
        ('Información del Registro', {
            'fields': ('user', 'nombre', 'timestamp', 'status')
        }),
        ('Ubicación y Aprobación', {
            'fields': ('estacion_servicio', 'aprobado')
        }),
    )

    readonly_fields = ('tipo_registro_display', 'timestamp_raw')

    def get_queryset(self, request):
        """QuerySet personalizado que evita errores de timezone"""
        try:
            # Intentar usar el queryset normal
            queryset = RegistroAsistencia.objects.all()
            # Probar si podemos iterar sin errores
            list(queryset[:1])  # Test con solo un elemento
            return queryset.select_related('user', 'estacion_servicio', 'user__turno')
        except Exception as e:
            # Si hay errores, usar queryset raw más básico
            from django.contrib import messages
            messages.error(request, f'Problema con timezone detectado. Usando vista simplificada. Error: {str(e)}')
            return RegistroAsistencia.objects.all()

    def user_safe(self, obj):
        """Versión segura para mostrar usuario"""
        try:
            return obj.user.nombre if obj.user else "Sin usuario"
        except Exception:
            return "Error al cargar usuario"
    user_safe.short_description = 'Usuario'

    def timestamp_safe(self, obj):
        """Versión segura del timestamp que maneja errores de timezone"""
        try:
            if obj.timestamp:
                # Intentar acceder al timestamp como string directo
                return str(obj.timestamp)
            return "Sin fecha"
        except Exception as e:
            # Si hay error, intentar acceder a los datos raw
            try:
                # Usar consulta SQL directa para obtener el timestamp
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT timestamp FROM API_registroasistencia WHERE id = %s", [obj.id])
                    row = cursor.fetchone()
                    if row:
                        return f"Raw: {row[0]}"
                return "Error en fecha"
            except Exception:
                return f"Error crítico - ID: {obj.id}"
    timestamp_safe.short_description = 'Fecha/Hora'

    def estacion_servicio_safe(self, obj):
        """Versión segura para mostrar estación"""
        try:
            return obj.estacion_servicio.nombre if obj.estacion_servicio else "Sin estación"
        except Exception:
            return "Error al cargar estación"
    estacion_servicio_safe.short_description = 'Estación'

    def aprobado_safe(self, obj):
        """Versión segura para mostrar estado de aprobación"""
        try:
            if obj.aprobado is True:
                return format_html('<span style="color: green;">✓ Aprobado</span>')
            elif obj.aprobado is False:
                return format_html('<span style="color: red;">✗ Rechazado</span>')
            else:
                return format_html('<span style="color: orange;">⏳ Pendiente</span>')
        except Exception:
            return "Error"
    aprobado_safe.short_description = 'Aprobado'

    def tipo_registro(self, obj):
        try:
            if obj.status == 0:
                return format_html('<span style="color: green;">🟢 Entrada</span>')
            else:
                return format_html('<span style="color: red;">🔴 Salida</span>')
        except Exception:
            return "Error"
    tipo_registro.short_description = 'Tipo'

    def tipo_registro_display(self, obj):
        try:
            return "Entrada" if obj.status == 0 else "Salida"
        except Exception:
            return "Error"
    tipo_registro_display.short_description = 'Tipo de Registro'

    def timestamp_raw(self, obj):
        """Muestra el timestamp raw de la base de datos"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT timestamp FROM API_registroasistencia WHERE id = %s", [obj.id])
                row = cursor.fetchone()
                if row:
                    return f"Raw DB: {row[0]}"
                return "No encontrado"
        except Exception as e:
            return f"Error: {str(e)}"
    timestamp_raw.short_description = 'Timestamp Raw'

    actions = ['aprobar_registros', 'rechazar_registros', 'exportar_csv_seguro', 'limpiar_timestamps_invalidos', 'ir_a_diagnostico']

    def ir_a_diagnostico(self, request, queryset):
        """Redirigir a la página de diagnóstico de timezone"""
        from django.shortcuts import redirect
        return redirect('/admin/diagnostico-timezone/')
    ir_a_diagnostico.short_description = "🔧 Ir a diagnóstico de timezone"

    def aprobar_registros(self, request, queryset):
        try:
            # Usar update directo para evitar problemas con timestamp
            ids = [obj.id for obj in queryset]
            updated = RegistroAsistencia.objects.filter(id__in=ids).update(aprobado=True)
            self.message_user(request, f'{updated} registros aprobados correctamente.')
        except Exception as e:
            self.message_user(request, f'Error al aprobar registros: {str(e)}', level='ERROR')
    aprobar_registros.short_description = "Aprobar registros seleccionados"

    def rechazar_registros(self, request, queryset):
        try:
            ids = [obj.id for obj in queryset]
            updated = RegistroAsistencia.objects.filter(id__in=ids).update(aprobado=False)
            self.message_user(request, f'{updated} registros rechazados.')
        except Exception as e:
            self.message_user(request, f'Error al rechazar registros: {str(e)}', level='ERROR')
    rechazar_registros.short_description = "Rechazar registros seleccionados"

    def limpiar_timestamps_invalidos(self, request, queryset):
        """Acción para limpiar timestamps inválidos"""
        from django.utils import timezone
        corregidos = 0
        errores = 0
        
        for obj in queryset:
            try:
                # Intentar acceder al timestamp
                ts = obj.timestamp
                if not ts:
                    # Si es None, asignar timestamp actual
                    obj.timestamp = timezone.now()
                    obj.save()
                    corregidos += 1
            except Exception:
                try:
                    # Si hay error, forzar un timestamp válido
                    obj.timestamp = timezone.now()
                    obj.save()
                    corregidos += 1
                except Exception:
                    errores += 1
        
        if corregidos > 0:
            self.message_user(request, f'{corregidos} timestamps corregidos.')
        if errores > 0:
            self.message_user(request, f'{errores} registros no pudieron ser corregidos.', level='WARNING')
    limpiar_timestamps_invalidos.short_description = "Limpiar timestamps inválidos"

    def exportar_csv_seguro(self, request, queryset):
        """Exportación CSV que maneja errores de timestamp"""
        import csv
        from django.http import HttpResponse
        from django.db import connection
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="registros_asistencia_seguro.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Usuario', 'Cédula', 'Fecha/Hora Raw', 'Tipo', 'Estación', 'Aprobado'])
        
        # Usar consulta SQL directa para evitar problemas de conversión
        ids = [obj.id for obj in queryset]
        id_list = ','.join(map(str, ids))
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT ra.id, ub.nombre, ub.cedula, ra.timestamp, ra.status, es.nombre, ra.aprobado
                FROM API_registroasistencia ra
                LEFT JOIN API_usuariobiometrico ub ON ra.user_id = ub.id
                LEFT JOIN API_estacionservicio es ON ra.estacion_servicio_id = es.id
                WHERE ra.id IN ({id_list})
                ORDER BY ra.id DESC
            """)
            
            for row in cursor.fetchall():
                writer.writerow([
                    row[0],  # ID
                    row[1] if row[1] else 'Sin usuario',  # Usuario
                    row[2] if row[2] else 'Sin cédula',   # Cédula
                    str(row[3]) if row[3] else 'Sin fecha',  # Timestamp raw
                    'Entrada' if row[4] == 0 else 'Salida',  # Tipo
                    row[5] if row[5] else 'Sin estación',    # Estación
                    'Sí' if row[6] else 'No' if row[6] is False else 'Pendiente'  # Aprobado
                ])
        
        return response
    exportar_csv_seguro.short_description = "Exportar CSV (modo seguro)"

    # Deshabilitamos date_hierarchy para evitar errores
    # date_hierarchy = 'timestamp'  # Comentado por problemas de timezone


# ---------- Admin EstacionServicio ----------
@admin.register(EstacionServicio)
class EstacionServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'jefe', 'usuarios_asignados', 'registros_hoy')
    search_fields = ('nombre', 'direccion', 'jefe__username', 'jefe__first_name', 'jefe__last_name')
    autocomplete_fields = ['jefe']
    list_per_page = 20
    ordering = ('nombre',)

    fieldsets = (
        ('Información de la Estación', {
            'fields': ('nombre', 'direccion')
        }),
        ('Responsable', {
            'fields': ('jefe',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('jefe')

    def usuarios_asignados(self, obj):
        count = obj.usuarios_biometricos.count()
        if count > 0:
            url = reverse('admin:API_usuariobiometrico_changelist') + f'?estacion__id__exact={obj.id}'
            return format_html('<a href="{}">{} usuarios</a>', url, count)
        return "0 usuarios"
    usuarios_asignados.short_description = 'Usuarios Asignados'

    def registros_hoy(self, obj):
        from django.utils import timezone
        from datetime import datetime
        
        hoy = timezone.now().date()
        inicio_dia = timezone.make_aware(datetime.combine(hoy, datetime.min.time()))
        fin_dia = timezone.make_aware(datetime.combine(hoy, datetime.max.time()))
        
        count = RegistroAsistencia.objects.filter(
            estacion_servicio=obj,
            timestamp__range=(inicio_dia, fin_dia)
        ).count()
        
        if count > 0:
            url = reverse('admin:API_registroasistencia_changelist') + f'?estacion_servicio__id__exact={obj.id}&timestamp__date={hoy}'
            return format_html('<a href="{}">{} registros</a>', url, count)
        return "0 registros"
    registros_hoy.short_description = 'Registros Hoy'


# ---------- Configuración adicional del Admin ----------
admin.site.site_header = "BioData - Administración"
admin.site.site_title = "BioData Admin"
admin.site.index_title = "Panel de Administración del Sistema Biométrico"

# Personalizar el admin site
admin.site.enable_nav_sidebar = True

# Agregar vista de diagnóstico personalizada
from django.urls import path
from .admin_views import DiagnosticoTimezoneView

# Extender las URLs del admin
original_get_urls = admin.site.get_urls
def get_urls():
    urls = original_get_urls()
    custom_urls = [
        path('diagnostico-timezone/', DiagnosticoTimezoneView.as_view(), name='diagnostico_timezone'),
    ]
    return custom_urls + urls

admin.site.get_urls = get_urls
