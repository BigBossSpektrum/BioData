#!/usr/bin/env python
"""
Script para corregir la inconsistencia entre las asignaciones de estación
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import CustomUser, EstacionServicio

def main():
    print("=== CORRIGIENDO INCONSISTENCIA DE ESTACIONES ===\n")
    
    # Obtener el jefe de patio
    jefe_patio = CustomUser.objects.filter(rol='jefe_patio', username='jefepatio').first()
    
    if not jefe_patio:
        print("❌ No se encontró el usuario jefepatio")
        return
    
    print(f"👤 Usuario: {jefe_patio.username}")
    print(f"🏢 Estación actual en CustomUser: {jefe_patio.estacion.nombre if jefe_patio.estacion else 'NINGUNA'}")
    
    # Verificar estaciones donde es jefe
    estaciones_como_jefe = EstacionServicio.objects.filter(jefe=jefe_patio)
    print(f"👑 Estaciones donde es jefe actualmente:")
    for estacion in estaciones_como_jefe:
        print(f"   - {estacion.nombre}")
    
    if not jefe_patio.estacion:
        print("❌ El usuario no tiene estación asignada en CustomUser")
        return
    
    estacion_asignada = jefe_patio.estacion
    print(f"\n🔧 CORRECCIÓN NECESARIA:")
    print(f"   - Estación objetivo: {estacion_asignada.nombre}")
    print(f"   - Acción 1: Remover jefe de estaciones anteriores")
    print(f"   - Acción 2: Asignar como jefe de {estacion_asignada.nombre}")
    
    respuesta = input(f"\n¿Proceder con la corrección? (s/n): ")
    
    if respuesta.lower() in ['s', 'si', 'y', 'yes']:
        # Paso 1: Remover como jefe de todas las estaciones anteriores
        estaciones_anteriores = EstacionServicio.objects.filter(jefe=jefe_patio)
        for estacion in estaciones_anteriores:
            print(f"   🗑️ Removiendo como jefe de: {estacion.nombre}")
            estacion.jefe = None
            estacion.save()
        
        # Paso 2: Asignar como jefe de la nueva estación
        print(f"   ✅ Asignando como jefe de: {estacion_asignada.nombre}")
        estacion_asignada.jefe = jefe_patio
        estacion_asignada.save()
        
        print(f"\n🎉 ¡CORRECCIÓN COMPLETADA!")
        
        # Verificar que funcionó
        from frontend.utils_filters import obtener_info_estacion_jefe, aplicar_filtro_jefe_patio
        from API.models import RegistroAsistencia
        
        info_estacion = obtener_info_estacion_jefe(jefe_patio)
        print(f"   - Estación filtrada: {info_estacion['estacion_filtrada']}")
        
        registros = RegistroAsistencia.objects.all()
        registros_filtrados = aplicar_filtro_jefe_patio(registros, jefe_patio, 'estacion_servicio')
        print(f"   - Registros disponibles: {registros_filtrados.count()}")
        
        if registros_filtrados.exists():
            print(f"   - Últimos 3 registros:")
            for registro in registros_filtrados.order_by('-timestamp')[:3]:
                print(f"     * {registro.user.nombre} | {registro.estacion_servicio.nombre}")
        
    else:
        print("❌ Operación cancelada")

if __name__ == "__main__":
    main()
