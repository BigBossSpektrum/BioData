from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from API.models import RegistroAsistencia


@method_decorator(staff_member_required, name='dispatch')
class DiagnosticoTimezoneView(View):
    """Vista para diagnosticar problemas de timezone en el admin"""
    
    def get(self, request):
        # Verificar estado de la base de datos
        diagnostico = {
            'total_registros': 0,
            'registros_problematicos': [],
            'configuracion_db': {},
            'timezone_django': '',
            'errores': []
        }
        
        try:
            # Información básica
            from django.conf import settings
            from django.utils import timezone
            
            diagnostico['timezone_django'] = settings.TIME_ZONE
            diagnostico['use_tz'] = settings.USE_TZ
            
            # Contar registros total
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM API_registroasistencia")
                diagnostico['total_registros'] = cursor.fetchone()[0]
                
                # Verificar configuración de MySQL
                cursor.execute("SELECT @@time_zone, @@sql_mode")
                tz_info = cursor.fetchone()
                diagnostico['configuracion_db'] = {
                    'time_zone': tz_info[0],
                    'sql_mode': tz_info[1]
                }
            
            # Verificar registros problemáticos
            problemas = []
            registros_muestra = RegistroAsistencia.objects.all()[:100]  # Solo primeros 100
            
            for registro in registros_muestra:
                try:
                    # Intentar acceder al timestamp
                    str(registro.timestamp)
                    registro.get_timestamp_safe()
                except Exception as e:
                    problemas.append({
                        'id': registro.id,
                        'error': str(e),
                        'user_id': registro.user_id if registro.user else None
                    })
            
            diagnostico['registros_problematicos'] = problemas
            
        except Exception as e:
            diagnostico['errores'].append(str(e))
        
        context = {
            'title': 'Diagnóstico de Timezone',
            'diagnostico': diagnostico
        }
        
        return render(request, 'admin/diagnostico_timezone.html', context)


# Registrar las vistas personalizadas en el admin
class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('diagnostico-timezone/', DiagnosticoTimezoneView.as_view(), name='diagnostico_timezone'),
        ]
        return custom_urls + urls
