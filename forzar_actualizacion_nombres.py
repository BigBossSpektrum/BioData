#!/usr/bin/env python
"""
Script de emergencia para forzar actualización manual de nombres
USO SOLO SI EL DISPOSITIVO NO ENVÍA NOMBRES CORRECTOS
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico

# NOMBRES MANUALES - ACTUALIZAR SEGÚN SEA NECESARIO
NOMBRES_MANUALES = {
    3: "EMPLEADO ESTACION IBERIA 3",
    4: "EMPLEADO ESTACION IBERIA 4", 
    5: "EMPLEADO ESTACION IBERIA 5",
    6: "EMPLEADO ESTACION IBERIA 6",
    7: "EMPLEADO ESTACION NQS8 7",
    8: "EMPLEADO ESTACION IBERIA 8",
    10: "EMPLEADO ESTACION IBERIA 10"
}

def forzar_actualizacion_manual():
    print("⚠️  ACTUALIZACIÓN MANUAL DE NOMBRES")
    print("=" * 50)
    
    for biometrico_id, nombre in NOMBRES_MANUALES.items():
        try:
            usuario = UsuarioBiometrico.objects.get(biometrico_id=biometrico_id)
            nombre_anterior = usuario.nombre
            usuario.nombre = nombre
            usuario.save()
            print(f"✅ ID {biometrico_id}: '{nombre_anterior}' → '{nombre}'")
        except UsuarioBiometrico.DoesNotExist:
            print(f"❌ Usuario con ID {biometrico_id} no encontrado")

if __name__ == "__main__":
    respuesta = input("¿Confirmar actualización manual? (escriba 'SI'): ")
    if respuesta == 'SI':
        forzar_actualizacion_manual()
    else:
        print("Actualización cancelada")
