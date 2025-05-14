from django.urls import path
from . import views  # o los views que uses

urlpatterns = [
    path('logs/', views.sincronizar_logs, name='sincronizar_logs'),
]
