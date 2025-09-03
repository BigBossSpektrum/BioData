#!/usr/bin/env python
"""
Script para asignar correctamente el jefe de patio a su estación
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
    print("=== ASIGNANDO JEFE DE PATIO A SU ESTACIÓN ===\n")
    
    # Obtener el jefe de patio
    jefe_patio = CustomUser.objects.filter(rol='jefe_patio', username='jefepatio').first()
    
    if not jefe_patio:
        print("❌ No se encontró el usuario jefepatio")
        return
    
    # Obtener la estación La Juana
    estacion_la_juana = EstacionServicio.objects.filter(nombre='La Juana').first()
    
    if not estacion_la_juana:
        print("❌ No se encontró la estación La Juana")
        return
    
    print(f"👤 Usuario: {jefe_patio.username}")
    print(f"🏢 Estación: {estacion_la_juana.nombre}")
    print(f"📍 Jefe actual de la estación: {estacion_la_juana.jefe.username if estacion_la_juana.jefe else 'NINGUNO'}")
    
    # Confirmar la asignación
    respuesta = input(f"\n¿Desea asignar a '{jefe_patio.username}' como jefe de '{estacion_la_juana.nombre}'? (s/n): ")
    
    if respuesta.lower() in ['s', 'si', 'y', 'yes']:
        estacion_la_juana.jefe = jefe_patio
        estacion_la_juana.save()
        
        print(f"✅ ¡Asignación completada!")
        print(f"   - {jefe_patio.username} ahora es jefe de {estacion_la_juana.nombre}")
        
        # Verificar que funcionó
        estacion_actualizada = EstacionServicio.objects.get(id=estacion_la_juana.id)
        print(f"   - Verificación: Jefe actual = {estacion_actualizada.jefe.username}")
        
        # Probar el filtro
        from frontend.utils_filters import aplicar_filtro_jefe_patio, obtener_info_estacion_jefe
        from API.models import RegistroAsistencia
        
        info_estacion = obtener_info_estacion_jefe(jefe_patio)
        print(f"   - Estación filtrada (utils): {info_estacion['estacion_filtrada']}")
        
        registros = RegistroAsistencia.objects.all()
        registros_filtrados = aplicar_filtro_jefe_patio(registros, jefe_patio, 'estacion_servicio')
        print(f"   - Registros que verá el jefe: {registros_filtrados.count()}")
        
    else:
        print("❌ Operación cancelada")

if __name__ == "__main__":
    main()
