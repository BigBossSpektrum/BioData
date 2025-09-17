#!/usr/bin/env python
"""
Script de monitoreo de actualizaciones de nombres desde dispositivo biométrico
Ejecutar después de sincronización para ver cambios
"""

import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico
from django.utils import timezone

def monitorear_cambios_nombres():
    print(f"🔍 MONITOREO DE NOMBRES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Usuarios que siguen con nombres genéricos
    usuarios_pendientes = UsuarioBiometrico.objects.filter(
        nombre__startswith='Usuario_'
    ).count()
    
    # Usuarios con nombres reales
    usuarios_actualizados = UsuarioBiometrico.objects.exclude(
        nombre__startswith='Usuario_'
    ).exclude(
        nombre__isnull=True
    ).exclude(
        nombre__exact=''
    ).count()
    
    print(f"✅ Usuarios con nombres reales: {usuarios_actualizados}")
    print(f"⏳ Usuarios pendientes (Usuario_#): {usuarios_pendientes}")
    
    if usuarios_pendientes > 0:
        print("\n📋 Usuarios pendientes de actualización:")
        pendientes = UsuarioBiometrico.objects.filter(
            nombre__startswith='Usuario_'
        ).order_by('biometrico_id')
        
        for usuario in pendientes[:10]:  # Mostrar primeros 10
            print(f"  - {usuario.nombre} (ID: {usuario.biometrico_id})")
        
        if usuarios_pendientes > 10:
            print(f"  ... y {usuarios_pendientes - 10} más")

if __name__ == "__main__":
    monitorear_cambios_nombres()
