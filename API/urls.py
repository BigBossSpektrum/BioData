from django.urls import path
from . import views  # o los views que uses

urlpatterns = [
    path('asistencias/', views.RegistroAsistenciaListView.as_view(), name='asistencia-list'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<str:user_id>/', views.editar_usuario, name='editar_usuario'),
    path("usuarios/eliminar/<int:user_id>/", views.eliminar_usuario, name="eliminar_usuario"),
    path('sincronizar-biometrico/', views.ejecutar_sincronizacion, name='sincronizar_biometrico'),
]