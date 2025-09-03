#!/usr/bin/env python
"""
Script para verificar los datos del jefe de patio en la base de datos
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
    print("=== VERIFICACIÓN DE DATOS DEL JEFE DE PATIO ===\n")
    
    # 1. Buscar usuarios con rol jefe_patio
    jefes_patio = CustomUser.objects.filter(rol='jefe_patio')
    print(f"🔍 Usuarios con rol 'jefe_patio' encontrados: {jefes_patio.count()}")
    
    for jefe in jefes_patio:
        print(f"\n📋 JEFE DE PATIO: {jefe.username}")
        print(f"   - ID: {jefe.id}")
        print(f"   - Nombre completo: {jefe.first_name} {jefe.last_name}")
        print(f"   - Email: {jefe.email}")
        print(f"   - Activo: {jefe.is_active}")
        print(f"   - Rol: {jefe.get_rol_display()}")
        
        # Verificar estación asignada directamente
        if jefe.estacion:
            print(f"   - Estación asignada (campo estacion): {jefe.estacion.nombre}")
        else:
            print(f"   - Estación asignada (campo estacion): ❌ NINGUNA")
        
        # Verificar estaciones donde es jefe (relación inversa)
        estaciones_como_jefe = EstacionServicio.objects.filter(jefe=jefe)
        if estaciones_como_jefe.exists():
            print(f"   - Estaciones donde es jefe:")
            for estacion in estaciones_como_jefe:
                print(f"     * {estacion.nombre} (ID: {estacion.id})")
        else:
            print(f"   - Estaciones donde es jefe: ❌ NINGUNA")
    
    print(f"\n" + "="*50)
    
    # 2. Buscar todas las estaciones y sus jefes asignados
    estaciones = EstacionServicio.objects.all()
    print(f"🏢 TODAS LAS ESTACIONES DE SERVICIO ({estaciones.count()}):")
    
    for estacion in estaciones:
        print(f"\n🏢 ESTACIÓN: {estacion.nombre}")
        print(f"   - ID: {estacion.id}")
        print(f"   - Dirección: {estacion.direccion}")
        
        if estacion.jefe:
            print(f"   - Jefe asignado: {estacion.jefe.username} ({estacion.jefe.get_rol_display()})")
        else:
            print(f"   - Jefe asignado: ❌ NINGUNO")
    
    print(f"\n" + "="*50)
    
    # 3. Usuarios con estación asignada directamente
    usuarios_con_estacion = CustomUser.objects.exclude(estacion=None)
    print(f"👥 USUARIOS CON ESTACIÓN ASIGNADA (campo estacion): {usuarios_con_estacion.count()}")
    
    for usuario in usuarios_con_estacion:
        print(f"   - {usuario.username} ({usuario.get_rol_display()}) → {usuario.estacion.nombre}")

if __name__ == "__main__":
    main()
