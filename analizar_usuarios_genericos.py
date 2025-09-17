#!/usr/bin/env python
"""
Script para analizar el problema con usuarios 'Usuario_#'
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio
from django.db.models import Count, Q, Min, Max
from django.utils import timezone

def analizar_usuarios_genericos():
    """
    Analiza los usuarios con nombres genéricos 'Usuario_#'
    """
    print("=" * 80)
    print("ANÁLISIS DE USUARIOS GENÉRICOS 'Usuario_#'")
    print("=" * 80)
    
    # Buscar usuarios con nombres genéricos
    usuarios_genericos = UsuarioBiometrico.objects.filter(
        nombre__startswith='Usuario_'
    ).order_by('biometrico_id')
    
    print(f"Total de usuarios genéricos encontrados: {usuarios_genericos.count()}")
    print("-" * 80)
    
    for usuario in usuarios_genericos:
        print(f"\n🔍 USUARIO: {usuario.nombre}")
        print(f"   ID Biométrico: {usuario.biometrico_id}")
        print(f"   ID Base de Datos: {usuario.id}")
        print(f"   Estación asignada: {usuario.estacion.nombre if usuario.estacion else 'Sin asignar'}")
        print(f"   Activo: {'Sí' if usuario.activo else 'No'}")
        
        # Verificar si hay otros usuarios con el mismo biometrico_id
        duplicados_biometrico = UsuarioBiometrico.objects.filter(
            biometrico_id=usuario.biometrico_id
        ).exclude(id=usuario.id)
        
        if duplicados_biometrico.exists():
            print(f"   ⚠️  PROBLEMA: Hay {duplicados_biometrico.count()} usuarios adicionales con el mismo biometrico_id:")
            for dup in duplicados_biometrico:
                print(f"      - ID BD: {dup.id}, Nombre: '{dup.nombre}', Estación: {dup.estacion.nombre if dup.estacion else 'Sin asignar'}")
        
        # Verificar registros de asistencia
        registros = RegistroAsistencia.objects.filter(user=usuario).count()
        print(f"   📋 Total registros de asistencia: {registros}")
        
        if registros > 0:
            # Obtener estadísticas de estaciones en registros
            registros_por_estacion = RegistroAsistencia.objects.filter(
                user=usuario
            ).values('estacion_servicio__nombre').annotate(
                total=Count('id')
            ).order_by('-total')
            
            print(f"   🏢 Registros por estación:")
            for reg in registros_por_estacion:
                estacion_nombre = reg['estacion_servicio__nombre'] or 'Sin estación'
                print(f"      - {estacion_nombre}: {reg['total']} registros")
        
        print()

def buscar_conflictos_biometrico_id():
    """
    Busca conflictos donde múltiples usuarios tienen el mismo biometrico_id
    """
    print("\n" + "=" * 80)
    print("BÚSQUEDA DE CONFLICTOS POR biometrico_id")
    print("=" * 80)
    
    # Buscar biometrico_ids duplicados
    ids_duplicados = UsuarioBiometrico.objects.values('biometrico_id').annotate(
        total=Count('id')
    ).filter(total__gt=1, biometrico_id__isnull=False).order_by('biometrico_id')
    
    print(f"Total de biometrico_ids con conflictos: {ids_duplicados.count()}")
    
    for item in ids_duplicados:
        biometrico_id = item['biometrico_id']
        total_usuarios = item['total']
        
        print(f"\n⚠️  CONFLICTO: biometrico_id = {biometrico_id} ({total_usuarios} usuarios)")
        
        usuarios_conflicto = UsuarioBiometrico.objects.filter(
            biometrico_id=biometrico_id
        ).order_by('id')
        
        for usuario in usuarios_conflicto:
            registros_count = RegistroAsistencia.objects.filter(user=usuario).count()
            print(f"   - ID BD: {usuario.id} | Nombre: '{usuario.nombre}' | Estación: {usuario.estacion.nombre if usuario.estacion else 'Sin asignar'} | Registros: {registros_count}")

def analizar_registros_mezclados():
    """
    Analiza si hay registros que podrían estar mezclados entre usuarios
    """
    print("\n" + "=" * 80)
    print("ANÁLISIS DE REGISTROS POTENCIALMENTE MEZCLADOS")
    print("=" * 80)
    
    # Buscar usuarios genéricos con registros
    usuarios_genericos = UsuarioBiometrico.objects.filter(
        nombre__startswith='Usuario_',
        registroasistencia__isnull=False
    ).distinct()
    
    for usuario in usuarios_genericos:
        print(f"\n🔍 Analizando registros de: {usuario.nombre} (ID biométrico: {usuario.biometrico_id})")
        
        # Obtener registros de los últimos 7 días
        fecha_limite = timezone.now() - timedelta(days=7)
        registros_recientes = RegistroAsistencia.objects.filter(
            user=usuario,
            timestamp__gte=fecha_limite
        ).order_by('timestamp')
        
        if registros_recientes.exists():
            print(f"   📅 Registros de los últimos 7 días: {registros_recientes.count()}")
            
            # Agrupar por estación
            estaciones_usadas = {}
            for registro in registros_recientes:
                estacion = registro.estacion_servicio.nombre if registro.estacion_servicio else 'Sin estación'
                if estacion not in estaciones_usadas:
                    estaciones_usadas[estacion] = []
                estaciones_usadas[estacion].append(registro)
            
            if len(estaciones_usadas) > 1:
                print(f"   ⚠️  POSIBLE PROBLEMA: Usuario registrado en {len(estaciones_usadas)} estaciones diferentes:")
                for estacion, regs in estaciones_usadas.items():
                    print(f"      - {estacion}: {len(regs)} registros")
                    # Mostrar algunos registros de ejemplo
                    for reg in regs[:3]:
                        try:
                            fecha_str = reg.timestamp.strftime('%d/%m/%Y %H:%M')
                        except:
                            fecha_str = str(reg.timestamp)
                        print(f"        * {fecha_str}")
                    if len(regs) > 3:
                        print(f"        * ... y {len(regs) - 3} más")

def verificar_integridad_datos():
    """
    Verifica la integridad general de los datos
    """
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE INTEGRIDAD DE DATOS")
    print("=" * 80)
    
    # 1. Usuarios sin biometrico_id
    usuarios_sin_id = UsuarioBiometrico.objects.filter(biometrico_id__isnull=True).count()
    print(f"👤 Usuarios sin biometrico_id: {usuarios_sin_id}")
    
    # 2. Registros huérfanos (sin usuario válido)
    registros_huerfanos = RegistroAsistencia.objects.filter(user__isnull=True).count()
    print(f"📋 Registros huérfanos: {registros_huerfanos}")
    
    # 3. Registros sin estación
    registros_sin_estacion = RegistroAsistencia.objects.filter(estacion_servicio__isnull=True).count()
    print(f"🏢 Registros sin estación: {registros_sin_estacion}")
    
    # 4. Usuarios con nombres vacíos o None
    usuarios_sin_nombre = UsuarioBiometrico.objects.filter(
        Q(nombre__isnull=True) | Q(nombre='') | Q(nombre__exact='')
    ).count()
    print(f"❓ Usuarios sin nombre: {usuarios_sin_nombre}")
    
    # 5. Verificar si hay registros con timestamps futuros
    ahora = timezone.now()
    registros_futuros = RegistroAsistencia.objects.filter(timestamp__gt=ahora).count()
    print(f"🔮 Registros con timestamp futuro: {registros_futuros}")

def sugerir_soluciones():
    """
    Sugiere soluciones para los problemas encontrados
    """
    print("\n" + "=" * 80)
    print("SUGERENCIAS DE SOLUCIÓN")
    print("=" * 80)
    
    print("1. 🔧 Para usuarios duplicados con mismo biometrico_id:")
    print("   - Consolidar registros en un solo usuario")
    print("   - Eliminar usuarios duplicados")
    print("   - Actualizar referencias en RegistroAsistencia")
    
    print("\n2. 🏷️  Para usuarios genéricos 'Usuario_#':")
    print("   - Asignar nombres reales basados en ID biométrico")
    print("   - Verificar mapping con sistema biométrico")
    print("   - Establecer estación fija por usuario")
    
    print("\n3. 📋 Para registros mezclados:")
    print("   - Verificar configuración de dispositivos biométricos")
    print("   - Revisar proceso de sincronización")
    print("   - Implementar validación más estricta en recibir_datos_biometrico")
    
    print("\n4. 🛠️  Acciones inmediatas recomendadas:")
    print("   - Backup de la base de datos")
    print("   - Script de limpieza de datos")
    print("   - Mejora en validación de vista recibir_datos_biometrico")

if __name__ == "__main__":
    try:
        print("Iniciando análisis de problemas con usuarios genéricos...")
        analizar_usuarios_genericos()
        buscar_conflictos_biometrico_id()
        analizar_registros_mezclados()
        verificar_integridad_datos()
        sugerir_soluciones()
        
    except Exception as e:
        print(f"Error al ejecutar el análisis: {e}")
        import traceback
        traceback.print_exc()
