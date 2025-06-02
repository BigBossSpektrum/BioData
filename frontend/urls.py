from django.urls import path
from . import views  # o los views que uses

urlpatterns = [
    path('', views.home_biometrico, name='home_biometrico'),
    path('historial_asistencia/', views.historial_asistencia, name='historial_asistencia'),
]
