#!/usr/bin/env python
"""
Script para verificar que los filtros de jefe de patio funcionen correctamente
con los registros existentes de la estación La Juana
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import CustomUser, EstacionServicio, RegistroAsistencia, UsuarioBiometrico
from frontend.utils_filters import aplicar_filtro_jefe_patio, obtener_info_estacion_jefe

def main():
    print("=== VERIFICACIÓN DE FILTROS PARA JEFE DE PATIO ===\n")
    
    # Obtener el jefe de patio
    jefe_patio = CustomUser.objects.filter(rol='jefe_patio', username='jefepatio').first()
    
    if not jefe_patio:
        print("❌ No se encontró el usuario jefepatio")
        return
    
    print(f"👤 USUARIO: {jefe_patio.username}")
    print(f"   - Rol: {jefe_patio.get_rol_display()}")
    print(f"   - Estación asignada: {jefe_patio.estacion.nombre if jefe_patio.estacion else 'NINGUNA'}")
    
    # Verificar información de estación usando la función de utilidades
    info_estacion = obtener_info_estacion_jefe(jefe_patio)
    print(f"   - Es jefe de patio (según utils): {info_estacion['es_jefe_patio']}")
    print(f"   - Estación filtrada (según utils): {info_estacion['estacion_filtrada']}")
    
    print(f"\n" + "="*60)
    
    # Obtener todos los registros de asistencia
    todos_registros = RegistroAsistencia.objects.all()
    print(f"📊 REGISTROS TOTALES EN LA BD: {todos_registros.count()}")
    
    # Filtrar por estación La Juana
    registros_la_juana = todos_registros.filter(estacion_servicio__nombre='La Juana')
    print(f"🏢 REGISTROS DE LA ESTACIÓN 'LA JUANA': {registros_la_juana.count()}")
    
    if registros_la_juana.exists():
        print("   📋 Últimos 5 registros de La Juana:")
        for registro in registros_la_juana.order_by('-timestamp')[:5]:
            print(f"     - {registro.user.nombre} | {registro.timestamp.strftime('%Y-%m-%d %H:%M')} | Estado: {registro.status}")
    
    print(f"\n" + "="*60)
    
    # Aplicar filtro de jefe de patio usando la función de utilidades
    registros_filtrados = aplicar_filtro_jefe_patio(todos_registros, jefe_patio, 'estacion_servicio')
    print(f"🔍 REGISTROS FILTRADOS PARA JEFE DE PATIO: {registros_filtrados.count()}")
    
    if registros_filtrados.exists():
        print("   📋 Últimos 5 registros filtrados:")
        for registro in registros_filtrados.order_by('-timestamp')[:5]:
            print(f"     - {registro.user.nombre} | {registro.timestamp.strftime('%Y-%m-%d %H:%M')} | Estación: {registro.estacion_servicio.nombre}")
    else:
        print("   ❌ NO HAY REGISTROS FILTRADOS")
        
        # Diagnosticar el problema
        print(f"\n🔧 DIAGNÓSTICO:")
        estacion_jefe = EstacionServicio.objects.filter(jefe=jefe_patio).first()
        if estacion_jefe:
            print(f"   - Estación donde es jefe: {estacion_jefe.nombre}")
        else:
            print(f"   - ❌ No es jefe de ninguna estación en la tabla EstacionServicio")
            print(f"   - ✅ Pero SÍ tiene estación asignada en CustomUser: {jefe_patio.estacion.nombre}")
    
    print(f"\n" + "="*60)
    
    # Verificar usuarios biométricos de La Juana
    usuarios_bio_la_juana = UsuarioBiometrico.objects.filter(estacion__nombre='La Juana')
    print(f"👥 USUARIOS BIOMÉTRICOS EN LA JUANA: {usuarios_bio_la_juana.count()}")
    
    if usuarios_bio_la_juana.exists():
        print("   📋 Usuarios biométricos:")
        for usuario in usuarios_bio_la_juana[:10]:  # Mostrar máximo 10
            print(f"     - {usuario.nombre} (ID: {usuario.biometrico_id}) | Activo: {usuario.activo}")

if __name__ == "__main__":
    main()
