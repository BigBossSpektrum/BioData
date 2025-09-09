#!/usr/bin/env python3
"""
Investigar qué empleados están disponibles en el sistema
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

def investigar_empleados():
    print("🔍 INVESTIGACIÓN DE EMPLEADOS EN EL SISTEMA")
    print("=" * 60)
    
    try:
        from API.models import UsuarioBiometrico, RegistroAsistencia
        
        # Verificar UsuarioBiometrico
        usuarios_bio = UsuarioBiometrico.objects.all()
        print(f"👥 UsuarioBiometrico: {usuarios_bio.count()} registros")
        
        # Mostrar algunos ejemplos
        for i, usuario in enumerate(usuarios_bio[:5]):
            print(f"  {i+1}. {usuario.nombre} (ID: {usuario.id}, Activo: {usuario.activo})")
        
        # Verificar registros de asistencia para obtener nombres de usuarios
        registros = RegistroAsistencia.objects.select_related('user').all()
        print(f"\n📊 RegistroAsistencia: {registros.count()} registros")
        
        # Obtener usuarios únicos desde los registros
        usuarios_desde_registros = set()
        for registro in registros[:20]:  # Solo los primeros 20
            if registro.user:
                usuarios_desde_registros.add(registro.user.nombre)
        
        print(f"\n🎯 Usuarios únicos en registros de asistencia:")
        for i, nombre in enumerate(sorted(usuarios_desde_registros), 1):
            print(f"  {i}. {nombre}")
        
        # Verificar si podemos activar algunos empleados
        if usuarios_bio.count() > 0:
            print(f"\n🔧 ACTIVANDO ALGUNOS EMPLEADOS...")
            empleados_activar = usuarios_bio[:3]
            for emp in empleados_activar:
                emp.activo = True
                emp.save()
                print(f"  ✅ Activado: {emp.nombre}")
            
            print(f"\n📊 Empleados activos ahora: {UsuarioBiometrico.objects.filter(activo=True).count()}")
        
        # Si no hay en UsuarioBiometrico, crear algunos desde los registros
        elif usuarios_desde_registros and len(usuarios_desde_registros) > 0:
            print(f"\n🔧 CREANDO USUARIOS BIOMÉTRICOS DESDE REGISTROS...")
            
            nombres_crear = list(usuarios_desde_registros)[:3]
            for i, nombre in enumerate(nombres_crear):
                usuario_bio, created = UsuarioBiometrico.objects.get_or_create(
                    nombre=nombre,
                    defaults={
                        'biometrico_id': i + 1000,
                        'activo': True,
                        'privilegio': 0
                    }
                )
                if created:
                    print(f"  ✅ Creado: {usuario_bio.nombre}")
                else:
                    print(f"  🔄 Ya existe: {usuario_bio.nombre}")
        
        # Verificar resultado final
        empleados_finales = UsuarioBiometrico.objects.filter(activo=True)
        print(f"\n✅ RESULTADO FINAL:")
        print(f"📊 Empleados activos disponibles: {empleados_finales.count()}")
        
        for emp in empleados_finales:
            print(f"  ✅ {emp.nombre} (ID: {emp.id})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigar_empleados()
