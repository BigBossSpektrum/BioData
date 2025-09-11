#!/usr/bin/env python
"""
Script para crear estaciones de prueba en la base de datos
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import EstacionServicio

def crear_estaciones_prueba():
    """Crea las estaciones de prueba si no existen"""
    
    estaciones_prueba = [
        "ESTACION_A",
        "ESTACION_B", 
        "ESTACION_C",
        "OFICINA_CENTRAL"
    ]
    
    print("🏢 CREANDO ESTACIONES DE PRUEBA")
    print("=" * 50)
    
    for nombre_estacion in estaciones_prueba:
        estacion, creada = EstacionServicio.objects.get_or_create(
            nombre=nombre_estacion,
            defaults={
                'direccion': f'Dirección de prueba para {nombre_estacion}'
            }
        )
        
        if creada:
            print(f"✅ Estación creada: {nombre_estacion} (ID: {estacion.id})")
        else:
            print(f"ℹ️  Estación ya existe: {nombre_estacion} (ID: {estacion.id})")
    
    print("\n📊 RESUMEN DE ESTACIONES:")
    todas_estaciones = EstacionServicio.objects.all()
    for estacion in todas_estaciones:
        print(f"   - {estacion.nombre} (ID: {estacion.id})")
    
    print(f"\n✅ Total estaciones en BD: {todas_estaciones.count()}")

if __name__ == "__main__":
    crear_estaciones_prueba()
