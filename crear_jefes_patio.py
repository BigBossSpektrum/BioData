#!/usr/bin/env python
"""
Script para crear jefes de patio para cada estación de servicio
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
django.setup()

from API.models import CustomUser, EstacionServicio
from django.contrib.auth.hashers import make_password

def crear_username_from_estacion(nombre_estacion):
    """Convierte el nombre de la estación en un username válido"""
    # Remover espacios y caracteres especiales
    username = nombre_estacion.replace(' ', '').replace('-', '').lower()
    # Remover acentos y caracteres especiales
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u'
    }
    for old, new in replacements.items():
        username = username.replace(old, new)
    return username

def crear_password_from_estacion(nombre_estacion):
    """Crea la contraseña basada en el nombre de la estación"""
    # Remover espacios y mantener mayúsculas/minúsculas
    password_base = nombre_estacion.replace(' ', '')
    return f"{password_base}2025"

def main():
    print("=== CREANDO JEFES DE PATIO PARA CADA ESTACIÓN ===\n")
    
    # Obtener todas las estaciones
    estaciones = EstacionServicio.objects.all()
    print(f"📋 ESTACIONES ENCONTRADAS: {estaciones.count()}")
    
    usuarios_creados = []
    usuarios_actualizados = []
    
    for estacion in estaciones:
        print(f"\n🏢 PROCESANDO: {estacion.nombre}")
        
        # Generar username y password
        username = crear_username_from_estacion(estacion.nombre)
        password = crear_password_from_estacion(estacion.nombre)
        
        print(f"   👤 Username: {username}")
        print(f"   🔐 Password: {password}")
        
        # Verificar si ya existe un usuario con ese username
        usuario_existente = CustomUser.objects.filter(username=username).first()
        
        if usuario_existente:
            print(f"   ⚠️  Usuario ya existe: {usuario_existente.username}")
            print(f"   📝 Actualizando configuración...")
            
            # Actualizar usuario existente
            usuario_existente.rol = 'jefe_patio'
            usuario_existente.estacion = estacion
            usuario_existente.is_active = True
            usuario_existente.set_password(password)
            usuario_existente.save()
            
            # Asignar como jefe de la estación
            estacion.jefe = usuario_existente
            estacion.save()
            
            usuarios_actualizados.append({
                'username': username,
                'password': password,
                'estacion': estacion.nombre,
                'accion': 'actualizado'
            })
            
        else:
            print(f"   ✨ Creando nuevo usuario...")
            
            # Crear nuevo usuario
            nuevo_usuario = CustomUser.objects.create(
                username=username,
                rol='jefe_patio',
                estacion=estacion,
                is_active=True,
                password=make_password(password)
            )
            
            # Asignar como jefe de la estación
            estacion.jefe = nuevo_usuario
            estacion.save()
            
            usuarios_creados.append({
                'username': username,
                'password': password,
                'estacion': estacion.nombre,
                'accion': 'creado'
            })
    
    print(f"\n" + "="*60)
    print(f"📊 RESUMEN DE OPERACIONES:")
    print(f"   ✅ Usuarios creados: {len(usuarios_creados)}")
    print(f"   🔄 Usuarios actualizados: {len(usuarios_actualizados)}")
    
    print(f"\n📋 LISTA COMPLETA DE JEFES DE PATIO:")
    todos_usuarios = usuarios_creados + usuarios_actualizados
    
    for usuario in todos_usuarios:
        print(f"   🏢 {usuario['estacion']}")
        print(f"     👤 Username: {usuario['username']}")
        print(f"     🔐 Password: {usuario['password']}")
        print(f"     📝 Acción: {usuario['accion']}")
        print()
    
    # Verificación final
    print(f"🔍 VERIFICACIÓN FINAL:")
    jefes_patio = CustomUser.objects.filter(rol='jefe_patio')
    for jefe in jefes_patio:
        estacion_asignada = jefe.estacion.nombre if jefe.estacion else "NINGUNA"
        estaciones_como_jefe = EstacionServicio.objects.filter(jefe=jefe)
        es_jefe_de = [e.nombre for e in estaciones_como_jefe]
        
        print(f"   👤 {jefe.username}")
        print(f"     Estación asignada: {estacion_asignada}")
        print(f"     Es jefe de: {es_jefe_de}")

if __name__ == "__main__":
    main()
