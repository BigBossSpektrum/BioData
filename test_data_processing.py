#!/usr/bin/env python
import os
import sys
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import RegistroAsistencia, UsuarioBiometrico, EstacionServicio
from django.utils.dateparse import parse_datetime

def test_data_processing():
    # Datos de prueba del JSON
    test_record = {
        "user_id": "65708651",
        "nombre": "ANGELA ROJAS",
        "timestamp": "2025-09-12T10:38:26",
        "status": 15,
        "estacion": "San Mateo",
        "punch": 0
    }
    
    print("=== PRUEBA DE PROCESAMIENTO DE DATOS ===")
    print(f"Datos de prueba: {test_record}")
    print()
    
    # 1. Verificar datos de entrada
    user_id = test_record.get("user_id")
    nombre = test_record.get("nombre", "").strip()
    timestamp_str = test_record.get("timestamp")
    estacion_nombre = test_record.get("estacion")
    status = test_record.get("status")
    
    print(f"1. Extracción de datos:")
    print(f"   - user_id: {user_id}")
    print(f"   - nombre: '{nombre}'")
    print(f"   - timestamp_str: {timestamp_str}")
    print(f"   - estacion_nombre: '{estacion_nombre}'")
    print(f"   - status: {status}")
    print()
    
    # 2. Validar campos requeridos
    if not user_id or not timestamp_str or not estacion_nombre:
        print(f"❌ ERROR: Campos incompletos")
        return False
    
    # 3. Parsear timestamp
    timestamp = parse_datetime(timestamp_str)
    if not timestamp:
        print(f"❌ ERROR: Timestamp inválido")
        return False
    
    print(f"2. Timestamp parseado: {timestamp}")
    print()
    
    # 4. Buscar estación
    try:
        estacion_obj = EstacionServicio.objects.get(nombre=estacion_nombre)
        print(f"3. Estación encontrada: {estacion_obj.id} - {estacion_obj.nombre}")
    except EstacionServicio.DoesNotExist:
        print(f"❌ ERROR: Estación '{estacion_nombre}' no existe")
        return False
    print()
    
    # 5. Obtener o crear usuario
    user, user_created = UsuarioBiometrico.objects.get_or_create(biometrico_id=user_id)
    print(f"4. Usuario: {user.id} - {user.nombre} (creado: {user_created})")
    
    if user_created:
        user.nombre = nombre
        user.estacion = estacion_obj
        user.save()
        print(f"   Usuario actualizado con nombre y estación")
    elif not user.estacion:
        user.estacion = estacion_obj
        user.save()
        print(f"   Estación asignada al usuario existente")
    elif user.estacion != estacion_obj:
        print(f"   ⚠️ CONFLICTO: Usuario asignado a '{user.estacion.nombre}' pero registro de '{estacion_nombre}'")
    print()
    
    # 6. Verificar duplicados
    duplicado = RegistroAsistencia.objects.filter(
        user=user,
        timestamp=timestamp,
        estacion_servicio=estacion_obj
    ).exists()
    
    if duplicado:
        print(f"5. ⚠️ DUPLICADO encontrado")
        return False
    else:
        print(f"5. No hay duplicados")
    print()
    
    # 7. Crear registro
    try:
        registro = RegistroAsistencia.objects.create(
            user=user,
            timestamp=timestamp,
            status=status,
            estacion_servicio=estacion_obj
        )
        print(f"6. ✅ REGISTRO CREADO: {registro.id}")
        print(f"   - Usuario: {registro.user.nombre}")
        print(f"   - Timestamp: {registro.timestamp}")
        print(f"   - Status: {registro.status}")
        print(f"   - Estación: {registro.estacion_servicio.nombre}")
        return True
    except Exception as e:
        print(f"❌ ERROR al crear registro: {e}")
        return False

if __name__ == "__main__":
    test_data_processing()
