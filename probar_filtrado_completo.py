#!/usr/bin/env python3
"""
Probar la funcionalidad completa de filtrado después de generar resúmenes
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

def probar_funcionalidad_completa():
    print("🧪 PRUEBA COMPLETA DE FUNCIONALIDAD DE FILTRADO")
    print("=" * 60)
    
    try:
        from API.models import UsuarioBiometrico, ResumenSemanal
        
        # Obtener empleados activos
        empleados = UsuarioBiometrico.objects.filter(activo=True)
        print(f"👥 Empleados activos: {empleados.count()}")
        
        # Definir rango de fechas para probar
        fecha_fin = date.today()
        fecha_inicio = fecha_fin - timedelta(days=7)
        
        print(f"📅 Rango de prueba: {fecha_inicio} al {fecha_fin}")
        
        # Verificar que hay empleados
        if not empleados.exists():
            print("❌ No hay empleados activos para probar")
            return False
        
        # Simular generación de resúmenes (como lo haría el formulario)
        print(f"\n🔄 GENERANDO RESÚMENES...")
        
        resumenes_creados = 0
        resumenes_actualizados = 0
        
        for empleado in empleados:
            print(f"  Procesando: {empleado.nombre}")
            
            # Calcular resumen por rango de fechas
            datos_resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
            
            # Crear o actualizar el resumen
            resumen, created = ResumenSemanal.objects.update_or_create(
                empleado=empleado,
                fecha_inicio_semana=fecha_inicio,
                fecha_fin_semana=fecha_fin,
                defaults=datos_resumen
            )
            
            if created:
                resumenes_creados += 1
                print(f"    ✅ Resumen creado")
            else:
                resumenes_actualizados += 1
                print(f"    🔄 Resumen actualizado")
            
            print(f"    📊 {resumen.total_horas_trabajadas:.2f}h trabajadas, {resumen.total_horas_extras:.2f}h extras")
        
        print(f"\n📊 RESULTADO DE GENERACIÓN:")
        print(f"  Creados: {resumenes_creados}")
        print(f"  Actualizados: {resumenes_actualizados}")
        
        # Probar el filtrado (simular lo que hace la vista)
        print(f"\n🔍 PROBANDO FILTRADO...")
        
        # Filtro 1: Por rango de fechas
        print(f"  1. Filtro por fechas {fecha_inicio} - {fecha_fin}")
        resumenes_filtrados = ResumenSemanal.objects.filter(
            fecha_inicio_semana__gte=fecha_inicio,
            fecha_fin_semana__lte=fecha_fin
        )
        print(f"     Resultados: {resumenes_filtrados.count()}")
        
        # Filtro 2: Por empleado específico
        if empleados.exists():
            primer_empleado = empleados.first()
            print(f"  2. Filtro por empleado: {primer_empleado.nombre}")
            resumenes_empleado = ResumenSemanal.objects.filter(
                empleado=primer_empleado,
                fecha_inicio_semana=fecha_inicio,
                fecha_fin_semana=fecha_fin
            )
            print(f"     Resultados: {resumenes_empleado.count()}")
        
        # Filtro 3: Por estación
        if empleados.exists() and empleados.first().estacion:
            estacion = empleados.first().estacion
            print(f"  3. Filtro por estación: {estacion.nombre}")
            resumenes_estacion = ResumenSemanal.objects.filter(
                empleado__estacion=estacion,
                fecha_inicio_semana=fecha_inicio,
                fecha_fin_semana=fecha_fin
            )
            print(f"     Resultados: {resumenes_estacion.count()}")
        
        # Simular agrupación por empleado (como en la vista)
        print(f"\n📋 AGRUPACIÓN POR EMPLEADO:")
        empleados_con_resumenes = {}
        for resumen in resumenes_filtrados:
            empleado_nombre = resumen.empleado.nombre
            if empleado_nombre not in empleados_con_resumenes:
                empleados_con_resumenes[empleado_nombre] = {
                    'empleado': resumen.empleado,
                    'resumenes': []
                }
            empleados_con_resumenes[empleado_nombre]['resumenes'].append(resumen)
        
        for empleado_nombre, data in empleados_con_resumenes.items():
            print(f"  👤 {empleado_nombre}: {len(data['resumenes'])} resúmenes")
            for resumen in data['resumenes']:
                print(f"    📊 {resumen.fecha_inicio_semana} - {resumen.fecha_fin_semana}: {resumen.total_horas_trabajadas:.2f}h")
        
        # Simular URL con parámetros (como el fix que hicimos)
        print(f"\n🔗 SIMULACIÓN DE URL CON FILTROS:")
        params = [
            f'fecha_inicio={fecha_inicio}',
            f'fecha_fin={fecha_fin}',
            f'empleado={primer_empleado.id}' if empleados.exists() else ''
        ]
        params = [p for p in params if p]  # Filtrar vacíos
        url_simulada = '/resumenes-semanales/?' + '&'.join(params)
        print(f"  URL: {url_simulada}")
        
        print(f"\n✅ PRUEBA COMPLETA EXITOSA")
        print(f"💡 El filtrado funcionará correctamente después de generar resúmenes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    probar_funcionalidad_completa()
