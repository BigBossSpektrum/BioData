from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UsuarioBiometrico, JornadaLaboral, RegistroAsistencia, EstacionServicio

# ---------- Admin CustomUser ----------
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'estacion', 'is_staff')
    list_filter = ('rol', 'estacion', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'rol', 'estacion__nombre')

    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('rol', 'estacion')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('rol', 'estacion')}),
    )


# ---------- Admin UsuarioBiometrico ----------
@admin.register(UsuarioBiometrico)
class UsuarioBiometricoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula', 'privilegio', 'activo', 'turno', 'jefe', 'estacion')
    list_filter = ('activo', 'turno', 'estacion')
    search_fields = ('nombre', 'cedula', 'jefe__username', 'estacion__nombre')
    autocomplete_fields = ['jefe', 'turno', 'estacion']


# ---------- Admin JornadaLaboral ----------
@admin.register(JornadaLaboral)
class JornadaLaboralAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'hora_inicio', 'hora_fin')
    search_fields = ('nombre',)


# ---------- Admin RegistroAsistencia ----------
@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'timestamp', 'tipo')
    list_filter = ('tipo', 'timestamp')
    search_fields = ('usuario__nombre', 'usuario__dni')


# ---------- Admin EstacionServico ----------
@admin.register(EstacionServicio)
class EstacionServicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'jefe')
    search_fields = ('nombre', 'direccion', 'jefe__username')
    autocomplete_fields = ['jefe']
