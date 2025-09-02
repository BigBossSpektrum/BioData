from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from accounts.utils.decorators import admin_required
import json

User = get_user_model()

# Create your views here.

@login_required
@require_POST
def extend_session(request):
    """
    Vista para extender la sesión del usuario
    """
    try:
        # Actualizar el tiempo de última actividad
        request.session['last_activity'] = timezone.now().isoformat()
        request.session['last_activity_timestamp'] = timezone.now().timestamp()
        
        return JsonResponse({
            'success': True,
            'message': 'Sesión extendida correctamente',
            'last_activity': request.session['last_activity_timestamp']
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al extender sesión: {str(e)}'
        }, status=500)


@login_required
@admin_required
def session_monitor(request):
    """
    Vista para monitorear las sesiones activas (solo para administradores)
    """
    try:
        # Obtener todas las sesiones activas
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        
        session_data = []
        for session in active_sessions:
            try:
                # Decodificar datos de sesión
                session_dict = session.get_decoded()
                user_id = session_dict.get('_auth_user_id')
                last_activity = session_dict.get('last_activity')
                
                if user_id:
                    try:
                        user = User.objects.get(id=user_id)
                        session_info = {
                            'session_key': session.session_key[:10] + '...',
                            'user': user.username,
                            'user_id': user_id,
                            'last_activity': last_activity,
                            'expire_date': session.expire_date,
                            'is_expired': session.expire_date < timezone.now()
                        }
                        session_data.append(session_info)
                    except User.DoesNotExist:
                        # Usuario no encontrado, sesión huérfana
                        session_info = {
                            'session_key': session.session_key[:10] + '...',
                            'user': 'Usuario eliminado',
                            'user_id': user_id,
                            'last_activity': last_activity,
                            'expire_date': session.expire_date,
                            'is_expired': True
                        }
                        session_data.append(session_info)
            except Exception as e:
                # Error al decodificar sesión
                continue
        
        return render(request, 'accounts/session_monitor.html', {
            'sessions': session_data,
            'total_sessions': len(session_data)
        })
        
    except Exception as e:
        return render(request, 'accounts/session_monitor.html', {
            'sessions': [],
            'total_sessions': 0,
            'error': str(e)
        })
