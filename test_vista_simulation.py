#!/usr/bin/env python
import os
import sys
import django
import json
import requests
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import RegistroAsistencia, UsuarioBiometrico, EstacionServicio
from django.utils.dateparse import parse_datetime
from django.utils import timezone as django_timezone

def test_vista_processing():
    # Simular datos exactos del JSON
    test_data = [
        {
            "user_id": "65708651",
            "nombre": "ANGELA ROJAS",
            "timestamp": "2025-09-12T10:38:26",
            "status": 15,
            "estacion": "San Mateo",
            "punch": 0
        },
        {
            "user_id": "1049533910",
            "nombre": "EULIS RODRIGUEZ",
            "timestamp": "2025-09-12T10:38:30",
            "status": 15,
            "estacion": "San Mateo",
            "punch": 0
        }
    ]
    
    print("=== SIMULANDO PROCESAMIENTO DE LA VISTA ===")
    print(f"Datos de prueba: {len(test_data)} registros")
    print()
    
    # Simular el procesamiento de la vista
    total_registros = len(test_data)
    estaciones_stats = {}
    registros_nuevos = 0
    registros_duplicados = 0
    registros_error = 0
    usuarios_nuevos = 0
    usuarios_actualizados = 0
    
    for i, registro in enumerate(test_data):
        print(f"[DEBUG] 🔄 Procesando registro #{i+1}/{total_registros}")
        
        user_id = registro.get("user_id")
        nombre = registro.get("nombre", "").strip()
        timestamp_str = registro.get("timestamp")
        estacion_nombre = registro.get("estacion")
        status = registro.get("status")
        
        # Validaciones
        if not user_id or not timestamp_str or not estacion_nombre:
            print(f"[ERROR] ❌ Registro #{i+1} incompleto")
            registros_error += 1
            continue
        
        # Parsear timestamp
        timestamp = parse_datetime(timestamp_str)
        if not timestamp:
            print(f"[ERROR] ❌ Timestamp inválido en registro #{i+1}: {timestamp_str}")
            registros_error += 1
            continue
        
        # Convertir a timezone-aware si es naive
        if timestamp.tzinfo is None:
            timestamp = django_timezone.make_aware(timestamp, django_timezone.get_current_timezone())
            print(f"[DEBUG] ✅ Timestamp convertido a timezone-aware: {timestamp}")
        
        # Buscar estación
        try:
            estacion_obj = EstacionServicio.objects.get(nombre=estacion_nombre)
            print(f"[DEBUG] ✅ Estación encontrada: {estacion_obj.nombre}")
        except EstacionServicio.DoesNotExist:
            print(f"[ERROR] ❌ Estación '{estacion_nombre}' no existe")
            registros_error += 1
            continue
        
        # Obtener o crear usuario
        user, user_created = UsuarioBiometrico.objects.get_or_create(biometrico_id=user_id)
        print(f"[DEBUG] Usuario: {user.id} - {user.nombre} (creado: {user_created})")
        
        if user_created:
            user.nombre = nombre
            user.estacion = estacion_obj
            user.save()
            usuarios_nuevos += 1
            print(f"[INFO] 🆕 Usuario biométrico creado: ID={user_id}, Nombre={nombre}")
        else:
            usuario_actualizado = False
            
            # Actualizar nombre
            if nombre and nombre.strip() and user.nombre != nombre:
                print(f"[INFO] ✏️ Actualizando nombre: '{user.nombre}' → '{nombre}'")
                user.nombre = nombre
                usuario_actualizado = True
            
            # Asignar estación si no tiene
            if not user.estacion:
                user.estacion = estacion_obj
                usuario_actualizado = True
                print(f"[INFO] 🏢 Asignando primera estación: → '{estacion_nombre}'")
            elif user.estacion != estacion_obj:
                print(f"[WARNING] ⚠️ CONFLICTO ESTACIÓN: Usuario asignado a '{user.estacion.nombre}' pero registro de '{estacion_nombre}'")
                registros_error += 1
                continue
            
            if usuario_actualizado:
                user.save()
                usuarios_actualizados += 1
        
        # Verificar duplicados
        duplicado = RegistroAsistencia.objects.filter(
            user=user,
            timestamp=timestamp,
            estacion_servicio=estacion_obj
        ).exists()
        
        if duplicado:
            print(f"[INFO] 🔁 Duplicado: Usuario {user_id} en {estacion_nombre}")
            registros_duplicados += 1
            continue
        
        # Crear registro
        try:
            registro_obj = RegistroAsistencia.objects.create(
                user=user,
                timestamp=timestamp,
                status=status,
                estacion_servicio=estacion_obj
            )
            registros_nuevos += 1
            print(f"[DEBUG] ✅ Nuevo registro creado: ID={registro_obj.id}")
        except Exception as e:
            print(f"[ERROR] ❌ Error al crear registro: {e}")
            registros_error += 1
    
    print(f"\n=== RESUMEN ===")
    print(f"Total procesados: {total_registros}")
    print(f"Registros nuevos: {registros_nuevos}")
    print(f"Registros duplicados: {registros_duplicados}")
    print(f"Registros con error: {registros_error}")
    print(f"Usuarios nuevos: {usuarios_nuevos}")
    print(f"Usuarios actualizados: {usuarios_actualizados}")
    
    # Verificar en BD
    total_en_bd = RegistroAsistencia.objects.count()
    print(f"\nTotal en BD: {total_en_bd}")

if __name__ == "__main__":
    test_vista_processing()
