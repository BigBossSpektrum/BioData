from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class SessionTimeoutMiddleware:
    """
    Middleware para manejar el timeout de sesión automático
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar si el usuario está autenticado
        if request.user.is_authenticated:
            # Obtener el último tiempo de actividad
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Convertir a datetime si es string
                if isinstance(last_activity, str):
                    last_activity = timezone.datetime.fromisoformat(last_activity)
                
                # Calcular tiempo transcurrido
                time_elapsed = timezone.now() - last_activity
                
                # Si han pasado más de 30 minutos, cerrar sesión
                if time_elapsed > timedelta(minutes=30):
                    logger.info(f"Sesión expirada para usuario {request.user.username}")
                    logout(request)
                    
                    # Si es una petición AJAX, devolver respuesta JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        from django.http import JsonResponse
                        return JsonResponse({
                            'session_expired': True,
                            'message': 'Tu sesión ha expirado. Serás redirigido al login.'
                        }, status=401)
                    
                    # Redirigir al login con parámetro de sesión expirada
                    login_url = reverse('login')
                    return redirect(f"{login_url}?expired=true")
            
            # Actualizar último tiempo de actividad
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Guardar información adicional para el frontend
            request.session['session_timeout'] = 30  # minutos
            request.session['last_activity_timestamp'] = timezone.now().timestamp()

        response = self.get_response(request)
        return response
