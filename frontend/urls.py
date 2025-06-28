from django.urls import path
from . import views  # o los views que uses

urlpatterns = [
    path('', views.home_biometrico, name='home_biometrico'),
    path('historial_asistencia/', views.historial_asistencia, name='historial_asistencia'),
    path('resumen_asistencias_diarias/', views.resumen_asistencias_diarias, name='resumen_asistencias_diarias'),
]
