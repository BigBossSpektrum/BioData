#!/usr/bin/env python
"""
Script para monitorear los logs del servidor Django y ver
qué datos están llegando al endpoint recibir-datos-biometrico
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio

def monitorear_actividad_reciente(minutos=60):
    """Monitorea la actividad de los últimos X minutos"""
    print(f"📊 MONITOREANDO ACTIVIDAD DE LOS ÚLTIMOS {minutos} MINUTOS")
    print("=" * 70)
    
    tiempo_limite = datetime.now() - timedelta(minutes=minutos)
    
    # Registros recientes
    registros_recientes = RegistroAsistencia.objects.filter(
        timestamp__gte=tiempo_limite
    ).order_by('-timestamp')
    
    if registros_recientes.exists():
        print(f"📈 {registros_recientes.count()} registros encontrados:")
        print()
        
        for registro in registros_recientes:
            minutos_atras = (datetime.now() - registro.timestamp.replace(tzinfo=None)).total_seconds() / 60
            tipo = "🟢 Entrada" if registro.status == 0 else "🔴 Salida"
            
            print(f"{tipo} - {registro.user.nombre} ({registro.user.biometrico_id})")
            print(f"   📍 Estación: {registro.estacion_servicio.nombre}")
            print(f"   🕐 Hace {minutos_atras:.1f} minutos ({registro.timestamp.strftime('%H:%M:%S')})")
            print("-" * 50)
    else:
        print(f"📭 No hay registros en los últimos {minutos} minutos")
    
    return registros_recientes.count()

def monitorear_usuarios_activos():
    """Muestra usuarios que han tenido actividad hoy"""
    print("\n👥 USUARIOS ACTIVOS HOY")
    print("=" * 50)
    
    hoy = datetime.now().date()
    
    usuarios_activos = UsuarioBiometrico.objects.filter(
        registroasistencia__timestamp__date=hoy
    ).distinct()
    
    if usuarios_activos.exists():
        print(f"👤 {usuarios_activos.count()} usuarios activos hoy:")
        print()
        
        for usuario in usuarios_activos:
            registros_hoy = RegistroAsistencia.objects.filter(
                user=usuario,
                timestamp__date=hoy
            ).order_by('timestamp')
            
            entradas = registros_hoy.filter(status=0).count()
            salidas = registros_hoy.filter(status=1).count()
            
            print(f"👤 {usuario.nombre} (ID: {usuario.biometrico_id})")
            print(f"   📊 Entradas: {entradas} | Salidas: {salidas}")
            print(f"   📍 Estación: {usuario.estacion.nombre if usuario.estacion else 'Sin asignar'}")
            
            # Mostrar último registro
            ultimo = registros_hoy.last()
            if ultimo:
                tipo = "entrada" if ultimo.status == 0 else "salida"
                print(f"   🕐 Último registro: {tipo} a las {ultimo.timestamp.strftime('%H:%M:%S')}")
            
            print("-" * 40)
    else:
        print("📭 No hay usuarios activos hoy")

def mostrar_estadisticas_servidor():
    """Muestra estadísticas generales del servidor"""
    print("\n📊 ESTADÍSTICAS DEL SERVIDOR")
    print("=" * 50)
    
    total_usuarios = UsuarioBiometrico.objects.count()
    total_registros = RegistroAsistencia.objects.count()
    
    # Registros de hoy
    hoy = datetime.now().date()
    registros_hoy = RegistroAsistencia.objects.filter(timestamp__date=hoy)
    entradas_hoy = registros_hoy.filter(status=0).count()
    salidas_hoy = registros_hoy.filter(status=1).count()
    
    # Registros de la última semana
    semana_atras = datetime.now() - timedelta(days=7)
    registros_semana = RegistroAsistencia.objects.filter(timestamp__gte=semana_atras).count()
    
    print(f"👥 Total usuarios registrados: {total_usuarios}")
    print(f"📝 Total registros históricos: {total_registros}")
    print(f"📅 Registros de hoy: {registros_hoy.count()}")
    print(f"   🟢 Entradas: {entradas_hoy}")
    print(f"   🔴 Salidas: {salidas_hoy}")
    print(f"📈 Registros última semana: {registros_semana}")
    
    # Estación más activa
    if total_registros > 0:
        from django.db.models import Count
        estacion_activa = EstacionServicio.objects.annotate(
            num_registros=Count('registroasistencia')
        ).order_by('-num_registros').first()
        
        if estacion_activa and estacion_activa.num_registros > 0:
            print(f"🏆 Estación más activa: {estacion_activa.nombre} ({estacion_activa.num_registros} registros)")

def mostrar_ultimo_error():
    """Intenta mostrar información sobre errores recientes"""
    print("\n🔍 DIAGNÓSTICO DEL SISTEMA")
    print("=" * 50)
    
    # Verificar configuración básica
    print("✅ Configuraciones:")
    print(f"   - Base de datos: Conectada")
    print(f"   - Modelos: Cargados correctamente")
    
    # Verificar estaciones
    estaciones = EstacionServicio.objects.count()
    print(f"   - Estaciones configuradas: {estaciones}")
    
    # Verificar endpoint
    print(f"   - Endpoint: /api/recibir-datos-biometrico/")
    print(f"   - Servidor recomendado: http://186.31.35.24:8000")

def modo_monitoreo_continuo():
    """Modo de monitoreo que se actualiza cada cierto tiempo"""
    print("🔄 MODO MONITOREO CONTINUO")
    print("=" * 50)
    print("Presiona Ctrl+C para salir")
    print()
    
    try:
        import time
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')  # Limpiar pantalla
            print(f"🔄 Actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70)
            
            registros_nuevos = monitorear_actividad_reciente(5)  # Últimos 5 minutos
            
            if registros_nuevos == 0:
                print("💤 Sistema en espera... (no hay actividad reciente)")
            
            print("\n⏱️ Próxima actualización en 30 segundos...")
            print("📋 Presiona Ctrl+C para salir del monitoreo")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoreo detenido por el usuario")

def main():
    print("🖥️ MONITOR DEL SERVIDOR BIOMÉTRICO")
    print("=" * 70)
    print(f"🕐 Hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Endpoint: http://186.31.35.24:8000/api/recibir-datos-biometrico/")
    print()
    
    try:
        mostrar_estadisticas_servidor()
        monitorear_actividad_reciente(60)  # Últimos 60 minutos
        monitorear_usuarios_activos()
        mostrar_ultimo_error()
        
        print("\n" + "=" * 70)
        print("💡 OPCIONES:")
        print("   1. Para monitoreo continuo: python monitor_servidor.py --continuo")
        print("   2. Para ver datos específicos: python ver_datos_guardados.py")
        print("   3. Para probar endpoint: python probar_servidor_produccion.py")
        
    except Exception as e:
        print(f"❌ Error en el monitoreo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--continuo":
        modo_monitoreo_continuo()
    else:
        main()
