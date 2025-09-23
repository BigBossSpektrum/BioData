#!/usr/bin/env python
import os
import sys
import django
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import RegistroAsistencia, UsuarioBiometrico, EstacionServicio
from django.utils.dateparse import parse_datetime
from django.utils import timezone as django_timezone

def cargar_registros_desde_json():
    """
    Carga todos los registros del archivo JSON a la base de datos

    Remplazar la ruta del archivo JSON con la ubicación correcta en tu sistema
    """
    json_file_path = r"c:\ControlIngreso\BioData\registros_biometrico\biodata_San_Mateo_2025-09-23.json"
    
    print("=== CARGANDO REGISTROS DESDE JSON ===")
    print(f"Archivo: {json_file_path}")
    
    # Verificar que el archivo existe
    if not os.path.exists(json_file_path):
        print(f"❌ ERROR: El archivo {json_file_path} no existe")
        return False
    
    # Cargar el JSON
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ JSON cargado correctamente")
    except Exception as e:
        print(f"❌ ERROR al cargar JSON: {e}")
        return False
    
    # Verificar estructura
    if 'recepciones' not in data:
        print(f"❌ ERROR: No se encontró la clave 'recepciones' en el JSON")
        return False
    
    recepciones = data['recepciones']
    total_recepciones = len(recepciones)
    print(f"📦 Total recepciones: {total_recepciones}")
    print(f"📊 Total registros según metadata: {data.get('metadata', {}).get('total_registros_acumulados', 'N/A')}")
    print()
    
    # Contadores globales
    total_registros_procesados = 0
    registros_nuevos = 0
    registros_duplicados = 0
    registros_error = 0
    usuarios_nuevos = 0
    usuarios_actualizados = 0
    
    # Procesar cada recepción
    for idx_recepcion, recepcion in enumerate(recepciones):
        print(f"🔄 Procesando recepción {idx_recepcion + 1}/{total_recepciones}")
        print(f"   📅 Timestamp: {recepcion.get('timestamp_recepcion', 'N/A')}")
        print(f"   🌐 IP Cliente: {recepcion.get('ip_cliente', 'N/A')}")
        print(f"   📦 Registros: {recepcion.get('total_registros', 0)}")
        
        datos_recibidos = recepcion.get('datos_recibidos', [])
        if not isinstance(datos_recibidos, list):
            print(f"   ⚠️ datos_recibidos no es una lista, saltando...")
            continue
        
        # Procesar cada registro de esta recepción
        for idx_registro, registro in enumerate(datos_recibidos):
            total_registros_procesados += 1
            
            if total_registros_procesados % 100 == 0:
                print(f"   🔄 Procesados: {total_registros_procesados}")
            
            # Extraer datos del registro
            user_id = registro.get("user_id")
            nombre = registro.get("nombre", "").strip()
            timestamp_str = registro.get("timestamp")
            estacion_nombre = registro.get("estacion")
            status = registro.get("status")
            
            # Validaciones básicas
            if not user_id or not timestamp_str or not estacion_nombre:
                registros_error += 1
                continue
            
            # Parsear timestamp
            timestamp = parse_datetime(timestamp_str)
            if not timestamp:
                registros_error += 1
                continue
            
            # Convertir a timezone-aware si es naive
            if timestamp.tzinfo is None:
                timestamp = django_timezone.make_aware(timestamp, django_timezone.get_current_timezone())
            
            # Buscar estación
            try:
                estacion_obj = EstacionServicio.objects.get(nombre=estacion_nombre)
            except EstacionServicio.DoesNotExist:
                registros_error += 1
                continue
            
            # Obtener o crear usuario
            user, user_created = UsuarioBiometrico.objects.get_or_create(biometrico_id=user_id)
            
            if user_created:
                user.nombre = nombre
                user.estacion = estacion_obj
                user.save()
                usuarios_nuevos += 1
            else:
                usuario_actualizado = False
                
                # Actualizar nombre si es necesario
                if nombre and nombre.strip() and user.nombre != nombre:
                    user.nombre = nombre
                    usuario_actualizado = True
                
                # Asignar estación si no tiene
                if not user.estacion:
                    user.estacion = estacion_obj
                    usuario_actualizado = True
                elif user.estacion != estacion_obj:
                    # Conflicto de estación, registrar error pero continuar
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
                registros_duplicados += 1
                continue
            
            # Crear registro
            try:
                RegistroAsistencia.objects.create(
                    user=user,
                    timestamp=timestamp,
                    status=status,
                    estacion_servicio=estacion_obj
                )
                registros_nuevos += 1
            except Exception as e:
                registros_error += 1
                continue
        
        print(f"   ✅ Recepción {idx_recepcion + 1} completada")
    
    # Reporte final
    print(f"\n=== REPORTE FINAL ===")
    print(f"📦 Total registros procesados: {total_registros_procesados}")
    print(f"✅ Registros nuevos creados: {registros_nuevos}")
    print(f"🔁 Registros duplicados: {registros_duplicados}")
    print(f"❌ Registros con error: {registros_error}")
    print(f"👤 Usuarios nuevos: {usuarios_nuevos}")
    print(f"✏️ Usuarios actualizados: {usuarios_actualizados}")
    
    # Verificar total en BD
    total_en_bd = RegistroAsistencia.objects.count()
    print(f"🗄️ Total registros en BD: {total_en_bd}")
    
    return True

if __name__ == "__main__":
    print("🚀 INICIANDO CARGA DE REGISTROS...")
    print()
    
    # Verificar estado inicial
    inicial_registros = RegistroAsistencia.objects.count()
    inicial_usuarios = UsuarioBiometrico.objects.count()
    print(f"📊 Estado inicial:")
    print(f"   - Registros en BD: {inicial_registros}")
    print(f"   - Usuarios en BD: {inicial_usuarios}")
    print()
    
    exito = cargar_registros_desde_json()
    
    if exito:
        print(f"\n🎉 CARGA COMPLETADA CON ÉXITO")
    else:
        print(f"\n❌ ERROR EN LA CARGA")
