#!/usr/bin/env python
"""
Script de prueba para verificar que el modal de resumen funciona correctamente
"""

import os
import sys
import django
from datetime import datetime, date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from API.models import UsuarioBiometrico

def test_calcular_resumen_rango():
    """Probar la función de calcular resumen por rango de fechas"""
    print("🧪 Iniciando test del modal de resumen...")
    
    try:
        # Obtener un empleado activo para pruebas
        empleado = UsuarioBiometrico.objects.filter(activo=True).first()
        
        if not empleado:
            print("❌ No se encontraron empleados activos para pruebas")
            return False
        
        print(f"✅ Empleado de prueba: {empleado.nombre}")
        
        # Definir rango de fechas de prueba (última semana)
        fecha_fin = date.today()
        fecha_inicio = fecha_fin - timedelta(days=7)
        
        print(f"📅 Rango de fechas: {fecha_inicio} al {fecha_fin}")
        
        # Calcular resumen
        resumen = empleado.calcular_resumen_rango_fechas(fecha_inicio, fecha_fin)
        
        print("📊 Resultados del resumen:")
        print(f"   - Horas normales: {resumen['horas_normales']:.2f}")
        print(f"   - Horas extra diurno: {resumen['horas_extra_diurno']:.2f}")
        print(f"   - Horas extra nocturno: {resumen['horas_extra_nocturno']:.2f}")
        print(f"   - Total horas trabajadas: {resumen['total_horas_trabajadas']:.2f}")
        print(f"   - Total horas extras: {resumen['total_horas_extras']:.2f}")
        print(f"   - Costo total horas extras: ${resumen['costo_total_horas_extras']:.2f}")
        
        print("✅ Test de cálculo de resumen completado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en el test: {str(e)}")
        return False

def test_reportlab_import():
    """Probar que ReportLab se puede importar correctamente"""
    print("\n🧪 Probando importación de ReportLab...")
    
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        print("✅ ReportLab importado correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando ReportLab: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 TEST DEL MODAL DE RESUMEN POR RANGO DE FECHAS")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Importación de ReportLab
    if not test_reportlab_import():
        all_tests_passed = False
    
    # Test 2: Cálculo de resumen
    if not test_calcular_resumen_rango():
        all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("✅ El modal de resumen está listo para usar")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("⚠️  Revise los errores anteriores")
    print("=" * 60)
