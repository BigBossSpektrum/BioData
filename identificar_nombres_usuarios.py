#!/usr/bin/env python
"""
Script para identificar y asignar nombres reales a usuarios genéricos 'Usuario_#'
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico, RegistroAsistencia, EstacionServicio, JornadaLaboral
from django.db import transaction
from django.utils import timezone

def analizar_patrones_usuarios():
    """
    Analiza patrones de uso para identificar características de cada usuario genérico
    """
    print("=" * 80)
    print("ANÁLISIS DE PATRONES PARA IDENTIFICACIÓN DE USUARIOS")
    print("=" * 80)
    
    usuarios_genericos = UsuarioBiometrico.objects.filter(
        nombre__startswith='Usuario_'
    ).order_by('biometrico_id')
    
    patrones = {}
    
    for usuario in usuarios_genericos:
        print(f"\n🔍 ANALIZANDO: {usuario.nombre} (ID biométrico: {usuario.biometrico_id})")
        
        # Obtener todos los registros
        registros = RegistroAsistencia.objects.filter(user=usuario).order_by('timestamp')
        
        if not registros.exists():
            print("   ❌ Sin registros de asistencia")
            continue
            
        # Análisis temporal
        primer_registro = registros.first()
        ultimo_registro = registros.last()
        total_registros = registros.count()
        
        print(f"   📅 Primer registro: {primer_registro.timestamp.strftime('%d/%m/%Y %H:%M')}")
        print(f"   📅 Último registro: {ultimo_registro.timestamp.strftime('%d/%m/%Y %H:%M')}")
        print(f"   📊 Total registros: {total_registros}")
        
        # Análisis de horarios
        horarios_entrada = []
        horarios_salida = []
        dias_activos = set()
        
        for registro in registros:
            hora = registro.timestamp.hour
            dia_semana = registro.timestamp.weekday()  # 0=Lunes, 6=Domingo
            dias_activos.add(dia_semana)
            
            # Clasificar como entrada o salida basado en horario
            if 5 <= hora <= 12:  # Horarios típicos de entrada
                horarios_entrada.append(hora)
            elif 13 <= hora <= 23:  # Horarios típicos de salida
                horarios_salida.append(hora)
        
        # Calcular estadísticas
        horario_entrada_promedio = sum(horarios_entrada) / len(horarios_entrada) if horarios_entrada else 0
        horario_salida_promedio = sum(horarios_salida) / len(horarios_salida) if horarios_salida else 0
        
        # Determinar turno predominante
        if horario_entrada_promedio:
            if 5 <= horario_entrada_promedio < 9:
                turno_sugerido = "Mañana (6:00-14:00)"
            elif 9 <= horario_entrada_promedio < 15:
                turno_sugerido = "Tarde (14:00-22:00)"
            elif horario_entrada_promedio >= 20 or horario_entrada_promedio < 5:
                turno_sugerido = "Nocturno (22:00-6:00)"
            else:
                turno_sugerido = "Mixto/Variable"
        else:
            turno_sugerido = "No determinado"
        
        # Análisis de estaciones
        registros_por_estacion = {}
        for registro in registros:
            estacion = registro.estacion_servicio.nombre if registro.estacion_servicio else 'Sin estación'
            registros_por_estacion[estacion] = registros_por_estacion.get(estacion, 0) + 1
        
        estacion_principal = max(registros_por_estacion, key=registros_por_estacion.get) if registros_por_estacion else 'Sin estación'
        
        # Análisis de regularidad (días trabajados por semana)
        semanas_con_registros = set()
        for registro in registros:
            # Calcular número de semana
            semana = registro.timestamp.isocalendar()[1]
            año = registro.timestamp.year
            semanas_con_registros.add(f"{año}-{semana}")
        
        # Calcular actividad reciente (últimos 30 días)
        fecha_limite = timezone.now() - timedelta(days=30)
        registros_recientes = registros.filter(timestamp__gte=fecha_limite)
        dias_recientes = set(reg.timestamp.date() for reg in registros_recientes)
        
        print(f"   🕐 Turno sugerido: {turno_sugerido}")
        print(f"   🏢 Estación principal: {estacion_principal}")
        print(f"   📈 Distribución por estación:")
        for est, count in sorted(registros_por_estacion.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (count / total_registros * 100) if total_registros > 0 else 0
            print(f"      - {est}: {count} registros ({porcentaje:.1f}%)")
        
        print(f"   📅 Días únicos trabajados (últimos 30 días): {len(dias_recientes)}")
        print(f"   📊 Semanas con actividad: {len(semanas_con_registros)}")
        
        # Determinar regularidad
        if len(dias_recientes) >= 20:
            regularidad = "Muy activo"
        elif len(dias_recientes) >= 10:
            regularidad = "Activo"
        elif len(dias_recientes) >= 5:
            regularidad = "Moderadamente activo"
        else:
            regularidad = "Poco activo"
        
        print(f"   🎯 Regularidad: {regularidad}")
        
        # Guardar patrón para posterior procesamiento
        patrones[usuario.id] = {
            'usuario': usuario,
            'turno_sugerido': turno_sugerido,
            'estacion_principal': estacion_principal,
            'registros_por_estacion': registros_por_estacion,
            'regularidad': regularidad,
            'total_registros': total_registros,
            'horario_entrada_promedio': horario_entrada_promedio,
            'horario_salida_promedio': horario_salida_promedio,
            'dias_recientes': len(dias_recientes)
        }
    
    return patrones

def generar_sugerencias_nombres(patrones):
    """
    Genera sugerencias de nombres basadas en los patrones analizados
    """
    print("\n" + "=" * 80)
    print("SUGERENCIAS DE NOMBRES BASADAS EN PATRONES")
    print("=" * 80)
    
    sugerencias = {}
    
    for user_id, patron in patrones.items():
        usuario = patron['usuario']
        estacion = patron['estacion_principal']
        turno = patron['turno_sugerido']
        biometrico_id = usuario.biometrico_id
        
        # Generar diferentes opciones de nombres
        opciones = []
        
        # Opción 1: Basada en estación y ID
        if estacion != 'Sin estación':
            opciones.append(f"Empleado_{estacion}_{biometrico_id}")
        
        # Opción 2: Basada en turno y estación
        turno_corto = turno.split()[0] if turno else "General"
        if estacion != 'Sin estación':
            opciones.append(f"{turno_corto}_{estacion}_{biometrico_id}")
        
        # Opción 3: Basada en regularidad
        if patron['regularidad'] == "Muy activo":
            opciones.append(f"Empleado_Fijo_{biometrico_id}")
        elif patron['regularidad'] == "Poco activo":
            opciones.append(f"Empleado_Temporal_{biometrico_id}")
        
        # Opción 4: Nombre más descriptivo
        if estacion != 'Sin estación':
            if patron['dias_recientes'] >= 15:
                opciones.append(f"Operador_{estacion}_{biometrico_id}")
            else:
                opciones.append(f"Auxiliar_{estacion}_{biometrico_id}")
        
        print(f"\n👤 {usuario.nombre} (ID: {biometrico_id}):")
        print(f"   📊 Contexto: {patron['regularidad']}, {estacion}, {turno}")
        print(f"   💡 Opciones de nombres:")
        for i, opcion in enumerate(opciones, 1):
            print(f"      {i}. {opcion}")
        
        # Recomendar la mejor opción
        if opciones:
            nombre_recomendado = opciones[0]  # Primera opción por defecto
            print(f"   ⭐ RECOMENDADO: {nombre_recomendado}")
            sugerencias[user_id] = {
                'usuario': usuario,
                'nombre_recomendado': nombre_recomendado,
                'opciones': opciones,
                'patron': patron
            }
    
    return sugerencias

def aplicar_nombres_sugeridos(sugerencias, modo_prueba=True):
    """
    Aplica los nombres sugeridos a los usuarios
    """
    print(f"\n{'🧪' if modo_prueba else '✅'} {'MODO PRUEBA - ' if modo_prueba else ''}APLICANDO NOMBRES SUGERIDOS")
    print("=" * 80)
    
    if not modo_prueba:
        print("⚠️  ¿Desea aplicar los nombres recomendados automáticamente?")
        print("   Alternativamente, puede aplicarlos uno por uno para mayor control.")
        respuesta = input("   Escriba 'AUTO' para aplicar todos, 'MANUAL' para uno por uno, o 'CANCELAR': ").upper()
        
        if respuesta == 'CANCELAR':
            print("❌ Operación cancelada")
            return
        elif respuesta not in ['AUTO', 'MANUAL']:
            print("❌ Respuesta no válida. Operación cancelada.")
            return
    else:
        respuesta = 'AUTO'  # En modo prueba, simular automático
    
    nombres_aplicados = 0
    
    with transaction.atomic():
        for user_id, sugerencia in sugerencias.items():
            usuario = sugerencia['usuario']
            nombre_actual = usuario.nombre
            nombre_recomendado = sugerencia['nombre_recomendado']
            
            if not modo_prueba and respuesta == 'MANUAL':
                print(f"\n👤 Usuario actual: {nombre_actual}")
                print(f"💡 Nombre recomendado: {nombre_recomendado}")
                print("📋 Opciones disponibles:")
                for i, opcion in enumerate(sugerencia['opciones'], 1):
                    print(f"   {i}. {opcion}")
                print("   0. Mantener nombre actual")
                print("   X. Escribir nombre personalizado")
                
                eleccion = input("Seleccione una opción: ").strip()
                
                if eleccion == '0':
                    print(f"   ➡️  Manteniendo: {nombre_actual}")
                    continue
                elif eleccion.upper() == 'X':
                    nombre_personalizado = input("Escriba el nuevo nombre: ").strip()
                    if nombre_personalizado:
                        nombre_final = nombre_personalizado
                    else:
                        print("   ❌ Nombre vacío. Manteniendo actual.")
                        continue
                else:
                    try:
                        indice = int(eleccion) - 1
                        if 0 <= indice < len(sugerencia['opciones']):
                            nombre_final = sugerencia['opciones'][indice]
                        else:
                            print("   ❌ Opción no válida. Manteniendo actual.")
                            continue
                    except ValueError:
                        print("   ❌ Entrada no válida. Manteniendo actual.")
                        continue
            else:
                nombre_final = nombre_recomendado
            
            # Aplicar el cambio
            if modo_prueba:
                print(f"   [PRUEBA] {nombre_actual} → {nombre_final}")
            else:
                usuario.nombre = nombre_final
                usuario.save()
                print(f"   ✅ {nombre_actual} → {nombre_final}")
                nombres_aplicados += 1
    
    if not modo_prueba:
        print(f"\n✅ Proceso completado. {nombres_aplicados} nombres actualizados.")
    else:
        print(f"\n🧪 Simulación completada. {len(sugerencias)} cambios propuestos.")

def verificar_nombres_existentes():
    """
    Verifica si ya existen empleados con nombres similares a los sugeridos
    """
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE NOMBRES EXISTENTES")
    print("=" * 80)
    
    # Obtener todos los nombres actuales (excluyendo usuarios genéricos)
    nombres_existentes = set()
    usuarios_con_nombre = UsuarioBiometrico.objects.exclude(
        nombre__startswith='Usuario_'
    ).values_list('nombre', flat=True)
    
    for nombre in usuarios_con_nombre:
        if nombre:
            nombres_existentes.add(nombre.upper())
    
    print(f"📋 Total de nombres reales existentes: {len(nombres_existentes)}")
    print("Muestra de nombres existentes:")
    for i, nombre in enumerate(sorted(nombres_existentes)[:10], 1):
        print(f"   {i:2d}. {nombre}")
    if len(nombres_existentes) > 10:
        print(f"   ... y {len(nombres_existentes) - 10} más")
    
    return nombres_existentes

def generar_reporte_identificacion():
    """
    Genera un reporte final con el plan de identificación
    """
    print("\n" + "=" * 80)
    print("📋 REPORTE FINAL DE IDENTIFICACIÓN")
    print("=" * 80)
    
    print("\n1. 📊 RESUMEN DEL ANÁLISIS:")
    usuarios_genericos = UsuarioBiometrico.objects.filter(nombre__startswith='Usuario_').count()
    print(f"   - Usuarios genéricos identificados: {usuarios_genericos}")
    print(f"   - Usuarios con patrones analizados: {usuarios_genericos}")
    print(f"   - Criterios de identificación: Estación, Turno, Regularidad")
    
    print("\n2. 🎯 ESTRATEGIA DE NOMENCLATURA:")
    print("   - Formato principal: Empleado_[Estación]_[ID]")
    print("   - Formato alternativo: [Turno]_[Estación]_[ID]")
    print("   - Consideración de regularidad y rol")
    
    print("\n3. 🔄 PRÓXIMOS PASOS:")
    print("   ✅ Análisis de patrones completado")
    print("   📋 Sugerencias de nombres generadas")
    print("   🧪 Modo prueba ejecutado")
    print("   ⏳ Pendiente: Aplicación real de nombres")
    
    print("\n4. 📋 PARA APLICAR CAMBIOS REALES:")
    print("   python identificar_nombres_usuarios.py --aplicar")
    print("   (Permitirá selección manual de nombres)")

if __name__ == "__main__":
    try:
        print("🚀 Iniciando identificación de nombres para usuarios genéricos...")
        
        # 1. Verificar nombres existentes
        nombres_existentes = verificar_nombres_existentes()
        
        # 2. Analizar patrones
        patrones = analizar_patrones_usuarios()
        
        if not patrones:
            print("❌ No se encontraron usuarios genéricos para procesar.")
            sys.exit(0)
        
        # 3. Generar sugerencias
        sugerencias = generar_sugerencias_nombres(patrones)
        
        # 4. Aplicar en modo prueba
        aplicar_nombres_sugeridos(sugerencias, modo_prueba=True)
        
        # 5. Verificar si se solicita aplicación real
        if '--aplicar' in sys.argv:
            print("\n" + "="*80)
            print("🔄 MODO APLICACIÓN REAL")
            aplicar_nombres_sugeridos(sugerencias, modo_prueba=False)
        
        # 6. Generar reporte final
        generar_reporte_identificacion()
        
    except Exception as e:
        print(f"❌ Error en la identificación: {e}")
        import traceback
        traceback.print_exc()
