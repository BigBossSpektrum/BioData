from django.contrib import admin
from .models import UsuarioBiometrico, RegistroAsistencia

@admin.register(UsuarioBiometrico)
class UsuarioBiometricoAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'nombre', 'privilegio', 'activo')
    search_fields = ('user_id', 'nombre')
    list_filter = ('activo', 'privilegio')


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'timestamp', 'estado')
    search_fields = ('usuario__nombre', 'usuario__user_id')
    list_filter = ('estado', 'timestamp')
    date_hierarchy = 'timestamp'
