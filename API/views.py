from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .Biometricos_connections import importar_datos_dispositivo  # si lo tienes en otro archivo

@csrf_exempt
def sincronizar_logs(request):
    try:
        logs = importar_datos_dispositivo()
        return JsonResponse({'status': 'ok', 'data': logs})
    except Exception as e:
        print("❌ Error en la vista /logs/:", e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)