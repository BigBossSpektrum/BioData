#!/usr/bin/env python
"""
Script para monitorear datos recibidos por estación
Uso: python monitorear_estaciones.py
"""

import os
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import RegistroAsistencia, EstacionServicio, UsuarioBiometrico

def monitorear_por_estacion():
    print("🏢 MONITOREO DE ESTACIONES BIOMÉTRICAS")
    print("=" * 60)
    
    # Últimas 2 horas
    tiempo_limite = datetime.now() - timedelta(hours=2)
    
    print(f"📅 Periodo analizado: Últimas 2 horas desde {tiempo_limite.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 Timestamp actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    estaciones = EstacionServicio.objects.all()
    total_estaciones = estaciones.count()
    estaciones_activas = 0
    
    if total_estaciones == 0:
        print("❌ No hay estaciones configuradas en la base de datos.")
        return
    
    for estacion in estaciones:
        # Registros recientes (últimas 2 horas)
        registros_recientes = RegistroAsistencia.objects.filter(
            estacion_servicio=estacion,
            timestamp__gte=tiempo_limite
        ).count()
        
        # Último registro general
        ultimo_registro = RegistroAsistencia.objects.filter(
            estacion_servicio=estacion
        ).order_by('-timestamp').first()
        
        # Total de registros históricos
        total_registros = RegistroAsistencia.objects.filter(
            estacion_servicio=estacion
        ).count()
        
        # Usuarios únicos en esta estación
        usuarios_unicos = RegistroAsistencia.objects.filter(
            estacion_servicio=estacion
        ).values('user').distinct().count()
        
        print(f"📍 {estacion.nombre} (ID: {estacion.id}):")
        print(f"   📊 Total registros históricos: {total_registros}")
        print(f"   👥 Usuarios únicos: {usuarios_unicos}")
        print(f"   ⏰ Registros últimas 2h: {registros_recientes}")
        
        if ultimo_registro:
            tiempo_transcurrido = datetime.now() - ultimo_registro.timestamp.replace(tzinfo=None)
            horas_transcurridas = tiempo_transcurrido.total_seconds() / 3600
            
            if horas_transcurridas < 2:
                estado = "🟢 ACTIVA"
                estaciones_activas += 1
            elif horas_transcurridas < 24:
                estado = "🟡 INACTIVA (< 24h)"
            else:
                estado = "🔴 INACTIVA (> 24h)"
            
            print(f"   {estado}")
            print(f"   🕒 Último registro: {ultimo_registro.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      (hace {horas_transcurridas:.1f} horas)")
            print(f"   👤 Último usuario: {ultimo_registro.user.nombre if ultimo_registro.user.nombre else 'Sin nombre'} (ID: {ultimo_registro.user.biometrico_id})")
        else:
            print(f"   🔴 SIN REGISTROS - Nunca ha enviado datos")
        
        print("-" * 40)
    
    # Resumen general
    print("\n📈 RESUMEN GENERAL:")
    print(f"🏢 Total estaciones configuradas: {total_estaciones}")
    print(f"🟢 Estaciones activas (últimas 2h): {estaciones_activas}")
    print(f"🔴 Estaciones inactivas: {total_estaciones - estaciones_activas}")
    print(f"📊 Porcentaje de actividad: {(estaciones_activas/total_estaciones*100):.1f}%")

def analizar_ips_recientes():
    """Analiza las IPs que han enviado datos recientemente"""
    print("\n🌐 ANÁLISIS DE IPs RECIENTES")
    print("=" * 60)
    
    # Últimas 24 horas
    tiempo_limite = datetime.now() - timedelta(hours=24)
    
    # Nota: Esto requeriría agregar un campo IP a RegistroAsistencia
    # Por ahora, mostramos un mensaje informativo
    print("ℹ️  Para analizar IPs de origen, necesitarías:")
    print("   1. Agregar campo 'ip_origen' al modelo RegistroAsistencia")
    print("   2. Capturar la IP en recibir_datos_biometrico")
    print("   3. Verificar en logs del servidor las IPs que hacen requests")

def mostrar_usuarios_nuevos():
    """Muestra usuarios biométricos creados recientemente"""
    print("\n👤 USUARIOS BIOMÉTRICOS RECIENTES")
    print("=" * 60)
    
    # Usuarios creados en las últimas 24 horas
    tiempo_limite = datetime.now() - timedelta(hours=24)
    
    # Django no guarda fecha de creación por defecto, pero podemos ver por ID
    usuarios_recientes = UsuarioBiometrico.objects.all().order_by('-id')[:10]
    
    if usuarios_recientes:
        print("🔟 Últimos 10 usuarios creados:")
        for usuario in usuarios_recientes:
            ultimo_acceso = RegistroAsistencia.objects.filter(
                user=usuario
            ).order_by('-timestamp').first()
            
            if ultimo_acceso:
                estacion_ultima = ultimo_acceso.estacion_servicio.nombre
                timestamp_ultimo = ultimo_acceso.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                estacion_ultima = "Sin registros"
                timestamp_ultimo = "Nunca"
            
            print(f"   🆔 {usuario.biometrico_id} - {usuario.nombre or 'Sin nombre'}")
            print(f"      📍 Última estación: {estacion_ultima}")
            print(f"      🕒 Último acceso: {timestamp_ultimo}")
    else:
        print("❌ No hay usuarios biométricos registrados")

if __name__ == "__main__":
    try:
        monitorear_por_estacion()
        analizar_ips_recientes()
        mostrar_usuarios_nuevos()
        
        print(f"\n✅ Monitoreo completado a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error durante el monitoreo: {e}")
        import traceback
        traceback.print_exc()
