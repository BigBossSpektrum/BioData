from django.contrib import admin
from .models import JornadaLaboral, UsuarioBiometrico, RegistroAsistencia

@admin.register(JornadaLaboral)
class JornadaLaboralAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'hora_inicio', 'hora_fin')
    search_fields = ('nombre',)

@admin.register(UsuarioBiometrico)
class UsuarioBiometricoAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'nombre', 'privilegio', 'activo', 'turno')
    search_fields = ('user_id', 'nombre')
    list_filter = ('activo', 'turno')

@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'timestamp', 'tipo')
    search_fields = ('usuario__nombre', 'usuario__user_id')
    list_filter = ('tipo', 'usuario__turno')
    date_hierarchy = 'timestamp'
