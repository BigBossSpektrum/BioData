from django.urls import path
from . import views  # o los views que uses

urlpatterns = [
    path('', views.home, name='home_biometrico'),
    path('resumen/', views.tabla_biometrico, name='tabla_biometrico'),
    path('historial_asistencia/', views.historial_asistencia, name='historial_asistencia'),
    
]
    