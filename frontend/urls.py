from django.urls import path
from . import views  # o los views que uses
from .views import aprobar_horas_extra, rechazar_horas_extra

urlpatterns = [
    path('', views.home_biometrico, name='home_biometrico'),
    path('resumen_asistencias_diarias/', views.resumen_asistencias_diarias, name='resumen_asistencias_diarias'),
    path('exportar_resumen_asistencias_excel/', views.exportar_resumen_asistencias_excel, name='exportar_resumen_asistencias_excel'),
    path('reporte_horas/', views.reporte_horas_trabajadas, name='reporte_horas_trabajadas'),
    path('aprobar_horas_extra/<int:usuario_id>/<str:dia>/', aprobar_horas_extra, name='aprobar_horas_extra'),
    path('rechazar_horas_extra/<int:usuario_id>/<str:dia>/', rechazar_horas_extra, name='rechazar_horas_extra'),
    
    # Panel Jefe de Patio - Jornadas Especiales
    path('panel-jefe-patio/', views.panel_jefe_patio, name='panel_jefe_patio'),
    path('crear-jornada-especial/', views.crear_jornada_especial, name='crear_jornada_especial'),
    path('desactivar-jornada-especial/<int:jornada_id>/', views.desactivar_jornada_especial, name='desactivar_jornada_especial'),
    path('api/empleados-estacion/', views.lista_empleados_estacion, name='lista_empleados_estacion'),
    
    # Resúmenes Semanales
    path('resumenes-semanales/', views.resumenes_semanales, name='resumenes_semanales'),
    path('generar-resumen-semanal/', views.generar_resumen_semanal, name='generar_resumen_semanal'),
    path('descargar-pdf-resumen/<int:resumen_id>/', views.descargar_pdf_resumen, name='descargar_pdf_resumen'),
    path('generar-pdf-rango/', views.generar_pdf_rango, name='generar_pdf_rango'),
]
