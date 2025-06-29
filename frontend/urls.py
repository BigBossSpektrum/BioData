from django.urls import path
from . import views  # o los views que uses
from .views import aprobar_horas_extra

urlpatterns = [
    path('', views.home_biometrico, name='home_biometrico'),
    path('historial_asistencia/', views.historial_asistencia, name='historial_asistencia'),
    path('resumen_asistencias_diarias/', views.resumen_asistencias_diarias, name='resumen_asistencias_diarias'),
    path('aprobar_horas_extra/<int:usuario_id>/<str:dia>/', aprobar_horas_extra, name='aprobar_horas_extra'),
]
