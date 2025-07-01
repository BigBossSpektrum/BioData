from django.urls import path
from . import views  # o los views que uses

urlpatterns = [
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path("usuarios/eliminar/<int:user_id>/", views.eliminar_usuario, name="eliminar_usuario"),
    path('usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    
    path('asistencias/', views.RegistroAsistenciaListView.as_view(), name='asistencia-list'),
    
    path('sincronizar-biometrico/', views.ejecutar_sincronizacion, name='sincronizar_biometrico'),
    path("recibir-datos-biometrico/", views.recibir_datos_biometrico, name="recibir_datos_biometrico"),

    path('no-autorizado/', views.no_autorizado, name='no_autorizado'),
    
    path('api_sincronizar_biometrico/', views.api_sincronizar_biometrico, name='api_sincronizar_biometrico'),
]