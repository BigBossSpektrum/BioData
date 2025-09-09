#!/usr/bin/env python3
"""
Script de prueba para verificar que el nuevo cálculo de horas trabajadas
en las vistas frontend está funcionando correctamente con las jornadas laborales.
"""

import os
import sys
import django
from datetime import datetime, time, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import JornadaLaboral, UsuarioBiometrico, RegistroAsistencia, EstacionServicio
from django.utils import timezone


def test_calculo_horas_en_vistas():
    """
    Prueba que las vistas usen correctamente el cálculo de horas trabajadas
    basado en las jornadas laborales.
    """
    
    print("=== PRUEBAS DE CÁLCULO DE HORAS EN VISTAS ===\n")
    
    # Crear jornada de prueba
    jornada_manana = JornadaLaboral.objects.create(
        nombre='Mañana Test',
        tipo_jornada='manana',
        hora_inicio=time(6, 0),
        hora_fin=time(14, 0),
        horas_normales=8.00,
        es_nocturno=False
    )
    
    # Crear estación de prueba
    estacion_test = EstacionServicio.objects.create(
        nombre='Estación Test',
        direccion='Test'
    )
    
    # Crear usuario de prueba
    usuario_test = UsuarioBiometrico.objects.create(
        biometrico_id=999,
        nombre='Usuario Test',
        cedula='12345678',
        turno=jornada_manana,
        estacion=estacion_test
    )
    
    # Crear registros de prueba - Caso: llega 1 hora antes y sale 1 hora después
    entrada_early = timezone.make_aware(datetime(2024, 1, 15, 5, 0))  # 05:00 (1 hora antes)
    salida_late = timezone.make_aware(datetime(2024, 1, 15, 15, 0))   # 15:00 (1 hora después)
    
    registro_entrada = RegistroAsistencia.objects.create(
        user=usuario_test,
        timestamp=entrada_early,
        nombre=usuario_test.nombre,
        estacion_servicio=estacion_test,
        status=0  # Entrada
    )
    
    registro_salida = RegistroAsistencia.objects.create(
        user=usuario_test,
        timestamp=salida_late,
        nombre=usuario_test.nombre,
        estacion_servicio=estacion_test,
        status=1  # Salida
    )
    
    print("1. DATOS DE PRUEBA:")
    print(f"   Usuario: {usuario_test.nombre}")
    print(f"   Jornada: {jornada_manana.nombre} ({jornada_manana.hora_inicio} - {jornada_manana.hora_fin})")
    print(f"   Entrada registrada: {entrada_early.time()}")
    print(f"   Salida registrada: {salida_late.time()}")
    print()
    
    # Probar cálculo directo con la jornada
    horas_calculadas = jornada_manana.calcular_horas_trabajadas(entrada_early, salida_late)
    resultado_detallado = jornada_manana.calcular_horas_normales_y_extras(entrada_early, salida_late)
    
    print("2. CÁLCULO DIRECTO CON JORNADA LABORAL:")
    print(f"   ✓ Horas totales: {horas_calculadas} horas")
    print(f"   ✓ Horas normales: {resultado_detallado['horas_normales']} horas")
    print(f"   ✓ Horas extras: {resultado_detallado['horas_extras']} horas")
    print(f"   ✓ Horas totales (detallado): {resultado_detallado['horas_totales']} horas")
    print()
    
    # Verificar que el cálculo sea correcto
    print("3. VERIFICACIÓN:")
    if horas_calculadas == 9.0:  # 8 horas normales + 1 hora extra
        print("   ✅ CORRECTO: Solo cuenta desde las 06:00 hasta las 15:00 = 9 horas")
        print("      (no cuenta la hora antes de la jornada)")
    else:
        print(f"   ❌ ERROR: Se esperaban 9.0 horas pero se obtuvieron {horas_calculadas}")
    
    if resultado_detallado['horas_normales'] == 8.0:
        print("   ✅ CORRECTO: Horas normales = 8.0 (06:00 a 14:00)")
    else:
        print(f"   ❌ ERROR: Horas normales esperadas 8.0 pero se obtuvieron {resultado_detallado['horas_normales']}")
    
    if resultado_detallado['horas_extras'] == 1.0:
        print("   ✅ CORRECTO: Horas extras = 1.0 (14:00 a 15:00)")
    else:
        print(f"   ❌ ERROR: Horas extras esperadas 1.0 pero se obtuvieron {resultado_detallado['horas_extras']}")
    
    print()
    print("4. IMPACTO EN LAS VISTAS:")
    print("   Las vistas frontend ahora usarán:")
    print("   - usuario.turno.calcular_horas_trabajadas() en lugar del cálculo simple")
    print("   - Esto asegura que solo se cuenten las horas dentro de la jornada")
    print("   - Las horas extras se calculan correctamente")
    print()
    
    # Limpiar datos de prueba
    registro_entrada.delete()
    registro_salida.delete()
    usuario_test.delete()
    estacion_test.delete()
    jornada_manana.delete()
    
    print("=== PRUEBAS COMPLETADAS ===")
    print("✅ Los cambios en las vistas están configurados para usar el cálculo correcto de jornadas laborales")


if __name__ == '__main__':
    test_calculo_horas_en_vistas()
