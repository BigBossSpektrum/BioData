#!/usr/bin/env python
"""
Script de prueba para verificar la función procesar_registro_unico
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from datetime import datetime, date
from django.utils.timezone import localtime, make_aware
from API.models import RegistroAsistencia, UsuarioBiometrico
from frontend.views import procesar_registro_unico

def test_registro_unico():
    """
    Prueba básica de la función procesar_registro_unico
    """
    print("=== PRUEBA DE FUNCIÓN procesar_registro_unico ===")
    
    try:
        # Crear un registro de prueba simulado
        class RegistroSimulado:
            def __init__(self, timestamp, tipo='salida'):
                self.timestamp = timestamp
                self.tipo = tipo
        
        # Crear usuario simulado
        class UsuarioSimulado:
            def __init__(self):
                self.turno = None
        
        # Simular registro único de salida (como el caso de ALONZO MENDOZA)
        timestamp_salida = make_aware(datetime(2025, 9, 30, 7, 10, 31))
        registro = RegistroSimulado(timestamp_salida, 'salida')
        usuario = UsuarioSimulado()
        fecha = date(2025, 9, 30)
        
        # Probar la función
        resultado = procesar_registro_unico([registro], usuario, fecha)
        
        if resultado:
            print("✅ Función ejecutada correctamente")
            print(f"   Entrada: {resultado['entrada']}")
            print(f"   Salida: {resultado['salida']}")
            print(f"   Mensaje: {resultado['mensaje_emparejamiento']}")
            print(f"   Tipo de turno: {resultado['tipo_turno']}")
            print(f"   Horas trabajadas: {resultado['horas_trabajadas']}")
        else:
            print("❌ La función retornó None")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_registro_unico()
