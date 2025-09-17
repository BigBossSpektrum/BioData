#!/usr/bin/env python
"""
Script para limpiar y consolidar registros mezclados de usuarios genéricos
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio
from django.db import transaction
from django.utils import timezone

def backup_datos():
    """
    Crear un backup de los datos antes de la limpieza
    """
    print("📋 Creando backup de datos...")
    
    with open('backup_usuarios_genericos.txt', 'w', encoding='utf-8') as f:
        f.write("BACKUP DE USUARIOS GENÉRICOS - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.write("=" * 80 + "\n\n")
        
        usuarios_genericos = UsuarioBiometrico.objects.filter(nombre__startswith='Usuario_')
        for usuario in usuarios_genericos:
            f.write(f"Usuario: {usuario.nombre}\n")
            f.write(f"ID BD: {usuario.id}\n")
            f.write(f"Biométrico ID: {usuario.biometrico_id}\n")
            f.write(f"Estación: {usuario.estacion.nombre if usuario.estacion else 'Sin asignar'}\n")
            
            registros = RegistroAsistencia.objects.filter(user=usuario).order_by('timestamp')
            f.write(f"Total registros: {registros.count()}\n")
            
            for reg in registros:
                f.write(f"  - {reg.timestamp} | {reg.estacion_servicio.nombre if reg.estacion_servicio else 'Sin estación'} | Status: {reg.status}\n")
            f.write("\n" + "-" * 40 + "\n\n")
    
    print("✅ Backup creado en 'backup_usuarios_genericos.txt'")

def analizar_estrategia_consolidacion():
    """
    Analiza la mejor estrategia para consolidar los datos
    """
    print("\n🔍 Analizando estrategia de consolidación...")
    
    usuarios_genericos = UsuarioBiometrico.objects.filter(nombre__startswith='Usuario_')
    
    estrategias = {}
    
    for usuario in usuarios_genericos:
        registros_por_estacion = {}
        registros = RegistroAsistencia.objects.filter(user=usuario)
        
        for reg in registros:
            estacion = reg.estacion_servicio.nombre if reg.estacion_servicio else 'Sin estación'
            if estacion not in registros_por_estacion:
                registros_por_estacion[estacion] = []
            registros_por_estacion[estacion].append(reg)
        
        # Determinar estación principal (la que tiene más registros)
        estacion_principal = max(registros_por_estacion.keys(), 
                               key=lambda x: len(registros_por_estacion[x])) if registros_por_estacion else None
        
        estrategias[usuario.id] = {
            'usuario': usuario,
            'estacion_principal': estacion_principal,
            'registros_por_estacion': registros_por_estacion,
            'total_registros': sum(len(regs) for regs in registros_por_estacion.values())
        }
        
        print(f"\n{usuario.nombre} (ID: {usuario.biometrico_id}):")
        print(f"  Estación principal recomendada: {estacion_principal}")
        print(f"  Distribución de registros:")
        for est, regs in registros_por_estacion.items():
            porcentaje = (len(regs) / estrategias[usuario.id]['total_registros'] * 100) if estrategias[usuario.id]['total_registros'] > 0 else 0
            print(f"    - {est}: {len(regs)} registros ({porcentaje:.1f}%)")
    
    return estrategias

def ejecutar_consolidacion(estrategias, modo_prueba=True):
    """
    Ejecuta la consolidación de datos
    """
    print(f"\n{'🧪' if modo_prueba else '🔧'} {'MODO PRUEBA - ' if modo_prueba else ''}Ejecutando consolidación...")
    
    if not modo_prueba:
        respuesta = input("⚠️  ¿Estás seguro de que quieres proceder con la consolidación REAL? (escriba 'SI' para confirmar): ")
        if respuesta != 'SI':
            print("❌ Consolidación cancelada")
            return
    
    with transaction.atomic():
        for user_id, estrategia in estrategias.items():
            usuario = estrategia['usuario']
            estacion_principal = estrategia['estacion_principal']
            
            print(f"\n🔄 Procesando {usuario.nombre}...")
            
            if estacion_principal and estacion_principal != 'Sin estación':
                try:
                    estacion_obj = EstacionServicio.objects.get(nombre=estacion_principal)
                    
                    if modo_prueba:
                        print(f"   [PRUEBA] Asignaría estación: {estacion_principal}")
                    else:
                        usuario.estacion = estacion_obj
                        usuario.save()
                        print(f"   ✅ Estación asignada: {estacion_principal}")
                    
                    # Procesar registros de otras estaciones
                    for estacion, registros in estrategia['registros_por_estacion'].items():
                        if estacion != estacion_principal and estacion != 'Sin estación':
                            if modo_prueba:
                                print(f"   [PRUEBA] Marcaría {len(registros)} registros de '{estacion}' como problemáticos")
                            else:
                                # En la implementación real, aquí podrías:
                                # 1. Mover los registros a un usuario específico de esa estación
                                # 2. Marcar los registros como problemáticos
                                # 3. Crear un log de registros inconsistentes
                                print(f"   ⚠️  {len(registros)} registros de '{estacion}' requieren revisión manual")
                
                except EstacionServicio.DoesNotExist:
                    print(f"   ❌ Error: Estación '{estacion_principal}' no existe")

def proponer_nombres_reales():
    """
    Propone nombres reales basados en patrones de uso
    """
    print("\n💡 Propuestas de nombres reales para usuarios genéricos:")
    
    usuarios_genericos = UsuarioBiometrico.objects.filter(nombre__startswith='Usuario_')
    
    for usuario in usuarios_genericos:
        # Analizar patrones de horarios para sugerir turno
        registros_recientes = RegistroAsistencia.objects.filter(
            user=usuario,
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).order_by('timestamp')
        
        horarios = []
        for reg in registros_recientes:
            horarios.append(reg.timestamp.hour)
        
        if horarios:
            horario_promedio = sum(horarios) / len(horarios)
            if horario_promedio >= 6 and horario_promedio < 14:
                turno_sugerido = "Mañana"
            elif horario_promedio >= 14 and horario_promedio < 22:
                turno_sugerido = "Tarde"
            else:
                turno_sugerido = "Nocturno"
        else:
            turno_sugerido = "Desconocido"
        
        estacion = usuario.estacion.nombre if usuario.estacion else "Sin asignar"
        
        print(f"\n{usuario.nombre} (ID biométrico: {usuario.biometrico_id}):")
        print(f"  📍 Estación: {estacion}")
        print(f"  🕐 Turno sugerido: {turno_sugerido}")
        print(f"  📊 Registros últimos 30 días: {registros_recientes.count()}")
        print(f"  💡 Nombre sugerido: Empleado_{estacion}_{usuario.biometrico_id}")

def generar_reporte_final():
    """
    Genera un reporte final con las acciones recomendadas
    """
    print("\n" + "=" * 80)
    print("📊 REPORTE FINAL Y RECOMENDACIONES")
    print("=" * 80)
    
    print("\n1. 🔧 ACCIONES INMEDIATAS:")
    print("   ✅ Vista corregida: Ya no actualiza estaciones automáticamente")
    print("   ✅ Validación agregada: Rechaza registros de estaciones incorrectas")
    print("   ✅ Backup creado: Datos respaldados antes de cambios")
    
    print("\n2. 📋 ACCIONES PENDIENTES:")
    print("   🔄 Ejecutar consolidación real (cambiar modo_prueba=False)")
    print("   👤 Asignar nombres reales a usuarios genéricos")
    print("   🔍 Revisar configuración de dispositivos biométricos")
    print("   📝 Implementar monitoreo de registros inconsistentes")
    
    print("\n3. 🛡️ PREVENCIÓN:")
    print("   ✅ Validación mejorada implementada")
    print("   📊 Sistema de alertas para registros mezclados")
    print("   🔒 Estaciones fijas por usuario biométrico")
    
    print("\n4. 📈 MONITOREO CONTINUO:")
    print("   - Ejecutar script de análisis semanalmente")
    print("   - Revisar logs de registros rechazados")
    print("   - Validar integridad de datos mensualmente")

if __name__ == "__main__":
    try:
        print("🚀 Iniciando proceso de limpieza y consolidación...")
        
        # 1. Crear backup
        backup_datos()
        
        # 2. Analizar estrategia
        estrategias = analizar_estrategia_consolidacion()
        
        # 3. Ejecutar consolidación en modo prueba
        ejecutar_consolidacion(estrategias, modo_prueba=True)
        
        # 4. Proponer nombres reales
        proponer_nombres_reales()
        
        # 5. Generar reporte final
        generar_reporte_final()
        
        print(f"\n✅ Proceso completado. Para aplicar cambios reales, ejecute:")
        print(f"   python {sys.argv[0]} --real")
        
        if len(sys.argv) > 1 and sys.argv[1] == '--real':
            print("\n⚠️  EJECUTANDO CAMBIOS REALES...")
            ejecutar_consolidacion(estrategias, modo_prueba=False)
        
    except Exception as e:
        print(f"❌ Error en el proceso: {e}")
        import traceback
        traceback.print_exc()
