from django.urls import path
from . import views  # o los views que uses

urlpatterns = [
    path('asistencias/', views.RegistroAsistenciaListView.as_view(), name='asistencia-list'),
]