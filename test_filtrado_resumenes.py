#!/usr/bin/env python3
"""
Script para probar la funcionalidad de filtrado después de generar resúmenes
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import UsuarioBiometrico, ResumenSemanal

def test_filtrado_resumenes():
    print("🧪 PRUEBA DE FILTRADO DE RESÚMENES")
    print("=" * 50)
    
    # Obtener empleados activos
    empleados = UsuarioBiometrico.objects.filter(activo=True)[:2]  # Solo 2 para prueba
    
    if not empleados.exists():
        print("❌ No hay empleados activos para probar")
        return
    
    # Generar un resumen de prueba
    fecha_inicio = date(2025, 9, 1)
    fecha_fin = date(2025, 9, 7)
    
    print(f"📅 Probando con rango: {fecha_inicio} al {fecha_fin}")
    print(f"👥 Empleados: {[emp.nombre for emp in empleados]}")
    
    resumenes_antes = ResumenSemanal.objects.filter(
        fecha_inicio_semana=fecha_inicio,
        fecha_fin_semana=fecha_fin
    ).count()
    
    print(f"📊 Resúmenes existentes antes: {resumenes_antes}")
    
    # Crear resúmenes para empleados de prueba
    for empleado in empleados:
        print(f"\n🔄 Procesando: {empleado.nombre}")
        
        try:
            # Calcular resumen
            datos_resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
            
            # Crear o actualizar
            resumen, created = ResumenSemanal.objects.update_or_create(
                empleado=empleado,
                fecha_inicio_semana=fecha_inicio,
                fecha_fin_semana=fecha_fin,
                defaults=datos_resumen
            )
            
            if created:
                print(f"  ✅ Resumen creado")
            else:
                print(f"  🔄 Resumen actualizado")
                
            print(f"  📊 Horas trabajadas: {resumen.total_horas_trabajadas:.2f}")
            print(f"  ⏰ Horas extras: {resumen.total_horas_extras:.2f}")
            print(f"  💰 Costo extras: ${resumen.costo_total_horas_extras:.2f}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Verificar que se crearon/actualizaron
    resumenes_despues = ResumenSemanal.objects.filter(
        fecha_inicio_semana=fecha_inicio,
        fecha_fin_semana=fecha_fin
    ).count()
    
    print(f"\n📊 Resúmenes después: {resumenes_despues}")
    print(f"🔍 Diferencia: +{resumenes_despues - resumenes_antes}")
    
    # Probar filtrado
    print(f"\n🔍 PROBANDO FILTRADO:")
    print("-" * 30)
    
    # Filtrar por rango de fechas
    resumenes_filtrados = ResumenSemanal.objects.filter(
        fecha_inicio_semana__gte=fecha_inicio,
        fecha_fin_semana__lte=fecha_fin
    )
    
    print(f"📅 Filtro por fechas: {resumenes_filtrados.count()} resultados")
    
    # Filtrar por empleado específico
    if empleados.exists():
        primer_empleado = empleados.first()
        resumenes_empleado = ResumenSemanal.objects.filter(
            empleado=primer_empleado,
            fecha_inicio_semana=fecha_inicio,
            fecha_fin_semana=fecha_fin
        )
        print(f"👤 Filtro por empleado '{primer_empleado.nombre}': {resumenes_empleado.count()} resultados")
        
        if resumenes_empleado.exists():
            resumen = resumenes_empleado.first()
            print(f"  ✅ Resumen encontrado: {resumen.total_horas_trabajadas:.2f}h trabajadas")
    
    print(f"\n✅ PRUEBA COMPLETADA")
    print("=" * 50)

if __name__ == "__main__":
    test_filtrado_resumenes()
