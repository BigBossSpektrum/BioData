from django.urls import path
from . import views  # o los views que uses

urlpatterns = [
    path('', views.tabla_biometrico, name='tabla_biometrico'),
]
