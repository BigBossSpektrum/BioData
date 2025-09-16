#!/usr/bin/env python3
"""
Script para verificar que TODOS los estilos de alineación izquierda están correctamente aplicados
en la plantilla resumen_asistencias_diarias.html (TODOS LOS ENCABEZADOS)
"""

import re
import os

def verificar_estilos_alineacion():
    """Verifica que los estilos CSS para alineación izquierda estén aplicados correctamente a TODOS los encabezados"""
    
    archivo_template = r"c:\ControlIngreso\BioData\frontend\templates\resumen_asistencias_diarias.html"
    
    print("🔍 Verificando estilos de alineación para TODOS LOS ENCABEZADOS...")
    print("=" * 70)
    
    try:
        with open(archivo_template, 'r', encoding='utf-8') as file:
            contenido = file.read()
            
        # Verificaciones específicas para TODOS los encabezados
        verificaciones = [
            {
                'nombre': 'Clase CSS th-left definida para todos los encabezados',
                'patron': r'\.th-left.*?text-align:\s*left\s*!important',
                'esperado': True
            },
            {
                'nombre': 'HTML con clase th-left en todos los encabezados',
                'patron': r'<th\s+class="th-left".*?style="text-align:\s*left\s*!important',
                'esperado': True
            },
            {
                'nombre': 'Thead sin clase text-center (removida)',
                'patron': r'<thead\s+class="table-dark"\s*>',
                'esperado': True
            },
            {
                'nombre': 'Reglas CSS específicas para nth-child(1) hasta nth-child(11)',
                'patron': r'th:nth-child\((?:1[01]?|[1-9])\).*?text-align:\s*left\s*!important',
                'esperado': True
            },
            {
                'nombre': 'Reglas con máxima especificidad para Bootstrap (todos los encabezados)',
                'patron': r'\.table\.table-bordered\.table-striped\.align-middle.*?thead.*?th.*?text-align:\s*left\s*!important',
                'esperado': True
            },
            {
                'nombre': 'Todas las clases th-left, th-nombre-left, th-estacion-left definidas',
                'patron': r'\.th-left,\s*\.th-nombre-left,\s*\.th-estacion-left.*?text-align:\s*left\s*!important',
                'esperado': True
            }
        ]
        
        resultados = []
        
        for verificacion in verificaciones:
            encontrado = bool(re.search(verificacion['patron'], contenido, re.DOTALL | re.IGNORECASE))
            resultados.append({
                'nombre': verificacion['nombre'],
                'encontrado': encontrado,
                'esperado': verificacion['esperado'],
                'pasó': encontrado == verificacion['esperado']
            })
            
        # Mostrar resultados
        for resultado in resultados:
            icono = "✅" if resultado['pasó'] else "❌"
            print(f"{icono} {resultado['nombre']}")
            if not resultado['pasó']:
                print(f"   ⚠️  Esperado: {resultado['esperado']}, Encontrado: {resultado['encontrado']}")
        
        print("\n" + "=" * 70)
        
        # Estadísticas
        total_verificaciones = len(resultados)
        verificaciones_exitosas = sum(1 for r in resultados if r['pasó'])
        porcentaje_exito = (verificaciones_exitosas / total_verificaciones) * 100
        
        print(f"📊 RESUMEN:")
        print(f"   Total de verificaciones: {total_verificaciones}")
        print(f"   Verificaciones exitosas: {verificaciones_exitosas}")
        print(f"   Porcentaje de éxito: {porcentaje_exito:.1f}%")
        
        if porcentaje_exito == 100:
            print("\n🎉 ¡PERFECTO! Todos los estilos de alineación están correctamente aplicados.")
            print("   TODOS los encabezados deberían estar alineados a la izquierda.")
        elif porcentaje_exito >= 80:
            print("\n✅ ¡BIEN! La mayoría de los estilos están aplicados correctamente.")
            print("   Puede que haya algunos casos menores que revisar.")
        else:
            print("\n⚠️ ATENCIÓN: Faltan algunos estilos importantes.")
            print("   Los cambios pueden no ser visibles completamente.")
            
        # Verificar elementos específicos
        print("\n🎯 VERIFICACIONES ESPECÍFICAS:")
        
        # Contar reglas CSS con text-align: left !important
        reglas_left = len(re.findall(r'text-align:\s*left\s*!important', contenido, re.IGNORECASE))
        print(f"   📝 Reglas CSS con 'text-align: left !important': {reglas_left}")
        
        # Verificar encabezados con clase th-left
        encabezados_th_left = len(re.findall(r'<th\s+class="th-left"', contenido))
        print(f"   🏷️  Encabezados con clase 'th-left': {encabezados_th_left}")
        
        # Verificar si se removió text-center del thead
        thead_sin_text_center = bool(re.search(r'<thead\s+class="table-dark"\s*>', contenido))
        if thead_sin_text_center:
            print("   🔄 ✅ Clase 'text-center' removida del thead")
        else:
            print("   🔄 ❌ Clase 'text-center' AÚN presente en thead")
        
        # Verificar estructura de la tabla
        tabla_encontrada = re.search(r'<table[^>]*id="tabla-asistencias"', contenido)
        if tabla_encontrada:
            print("   📋 ✅ Tabla con ID 'tabla-asistencias' encontrada")
        else:
            print("   📋 ❌ Tabla con ID 'tabla-asistencias' NO encontrada")
            
        # Contar todos los encabezados
        total_encabezados = len(re.findall(r'<th[^>]*>', contenido))
        print(f"   📊 Total de encabezados <th> encontrados: {total_encabezados}")
            
        return porcentaje_exito == 100
        
    except FileNotFoundError:
        print(f"❌ Error: No se pudo encontrar el archivo {archivo_template}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def mostrar_recomendaciones():
    """Muestra recomendaciones para verificar visualmente los cambios"""
    print("\n" + "=" * 70)
    print("🔧 RECOMENDACIONES PARA VERIFICAR LOS CAMBIOS:")
    print("=" * 70)
    print("1. 🌐 Abrir el navegador en: http://127.0.0.1:8000/resumen_asistencias_diarias/")
    print("2. 🔐 Hacer login si es necesario")
    print("3. 👁️  Inspeccionar TODOS los encabezados de la tabla")
    print("4. ✅ Verificar que TODOS los encabezados estén alineados a la izquierda")
    print("5. 🔍 Usar herramientas de desarrollador (F12) para inspeccionar CSS aplicado")
    print("\n💡 PUNTOS CLAVE A VERIFICAR:")
    print("   • TODOS los encabezados deben estar alineados a la izquierda:")
    print("     - # (número)")
    print("     - Día")
    print("     - Nombre")
    print("     - Estación")
    print("     - Entrada")
    print("     - Salida")
    print("     - H.Retraso")
    print("     - H.T")
    print("     - T.Turno")
    print("     - H.Extras")
    print("     - Aprobado")
    print("   • Los datos en las columnas 'Nombre' y 'Estación' deben estar alineados a la izquierda")
    print("   • Los estilos deben sobrescribir cualquier alineación de Bootstrap")

if __name__ == "__main__":
    print("🧪 SCRIPT DE VERIFICACIÓN DE ESTILOS DE ALINEACIÓN - TODOS LOS ENCABEZADOS")
    print("=" * 70)
    
    exito = verificar_estilos_alineacion()
    mostrar_recomendaciones()
    
    if exito:
        print("\n🎯 RESULTADO FINAL: ¡Verificación EXITOSA! 🎉")
    else:
        print("\n⚠️ RESULTADO FINAL: Se encontraron algunos problemas. 🔧")
    
    print("\n" + "=" * 70)
