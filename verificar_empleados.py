#!/usr/bin/env python3
"""
Verificar estado de empleados
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico

def verificar_empleados():
    print("👥 VERIFICACIÓN DE EMPLEADOS")
    print("=" * 40)
    
    # Todos los empleados
    todos = UsuarioBiometrico.objects.all()
    print(f"📊 Total empleados: {todos.count()}")
    
    # Empleados activos
    activos = UsuarioBiometrico.objects.filter(activo=True)
    print(f"✅ Empleados activos: {activos.count()}")
    
    # Empleados inactivos
    inactivos = UsuarioBiometrico.objects.filter(activo=False)
    print(f"❌ Empleados inactivos: {inactivos.count()}")
    
    print(f"\n📋 LISTA DE EMPLEADOS:")
    for emp in todos[:10]:  # Solo los primeros 10
        estado = "✅ Activo" if emp.activo else "❌ Inactivo"
        print(f"  {emp.nombre} - {estado}")
    
    # Activar empleados para prueba si es necesario
    if activos.count() == 0 and todos.count() > 0:
        print(f"\n🔧 ACTIVANDO PRIMEROS 3 EMPLEADOS PARA PRUEBA...")
        empleados_a_activar = todos[:3]
        for emp in empleados_a_activar:
            emp.activo = True
            emp.save()
            print(f"  ✅ Activado: {emp.nombre}")
        
        print(f"\n📊 Empleados activos después: {UsuarioBiometrico.objects.filter(activo=True).count()}")

if __name__ == "__main__":
    verificar_empleados()
