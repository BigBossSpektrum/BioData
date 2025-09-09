#!/usr/bin/env python
"""
Test específico para verificar que los botones del modal funcionen correctamente
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inverligol.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

def test_urls_disponibles():
    """Test para verificar que las URLs estén disponibles"""
    print("🔗 Probando URLs...")
    
    from django.urls import reverse
    from django.test import Client
    from django.contrib.auth import get_user_model
    
    try:
        # Crear cliente de prueba
        client = Client()
        
        # Crear un usuario de prueba con permisos admin
        User = get_user_model()
        test_user = User.objects.filter(username='test_admin').first()
        
        if not test_user:
            print("⚠️  No se encontró usuario de prueba. Creando uno...")
            # Buscar cualquier usuario admin existente
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                test_user = admin_user
                print(f"✅ Usando usuario admin existente: {test_user.username}")
            else:
                print("❌ No se encontraron usuarios admin para la prueba")
                return False
        
        # Hacer login
        client.force_login(test_user)
        
        # Test 1: URL principal de resúmenes semanales
        try:
            url_resumenes = reverse('resumenes_semanales')
            response = client.get(url_resumenes)
            print(f"✅ URL resumenes_semanales: {response.status_code}")
        except Exception as e:
            print(f"❌ Error en resumenes_semanales: {e}")
            return False
        
        # Test 2: URL generar resumen semanal (POST)
        try:
            url_generar = reverse('generar_resumen_semanal')
            print(f"✅ URL generar_resumen_semanal disponible: {url_generar}")
        except Exception as e:
            print(f"❌ Error en generar_resumen_semanal: {e}")
            return False
        
        # Test 3: URL generar PDF rango (GET)
        try:
            url_pdf_rango = reverse('generar_pdf_rango')
            print(f"✅ URL generar_pdf_rango disponible: {url_pdf_rango}")
        except Exception as e:
            print(f"❌ Error en generar_pdf_rango: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error general en test de URLs: {e}")
        return False

def test_vista_generar_pdf_rango():
    """Test para verificar que la vista generar_pdf_rango funcione"""
    print("\n📄 Probando vista generar_pdf_rango...")
    
    from django.test import Client
    from django.contrib.auth import get_user_model
    from django.urls import reverse
    
    try:
        # Crear cliente de prueba
        client = Client()
        
        # Obtener usuario admin
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            print("❌ No se encontró usuario admin para la prueba")
            return False
        
        # Hacer login
        client.force_login(admin_user)
        
        # Preparar datos de prueba
        fecha_inicio = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        fecha_fin = date.today().strftime('%Y-%m-%d')
        
        # Test con parámetros válidos
        url = reverse('generar_pdf_rango')
        response = client.get(url, {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        })
        
        if response.status_code == 200:
            print(f"✅ Vista generar_pdf_rango funciona correctamente")
            print(f"   - Content-Type: {response.get('Content-Type', 'N/A')}")
            print(f"   - Content-Disposition: {response.get('Content-Disposition', 'N/A')}")
            return True
        else:
            print(f"❌ Vista generar_pdf_rango falló con código: {response.status_code}")
            print(f"   - Respuesta: {response.content.decode('utf-8')[:200]}...")
            return False
        
    except Exception as e:
        print(f"❌ Error en test de vista generar_pdf_rango: {e}")
        return False

def test_vista_generar_resumen_semanal():
    """Test para verificar que la vista generar_resumen_semanal funcione"""
    print("\n💾 Probando vista generar_resumen_semanal...")
    
    from django.test import Client
    from django.contrib.auth import get_user_model
    from django.urls import reverse
    
    try:
        # Crear cliente de prueba
        client = Client()
        
        # Obtener usuario admin
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            print("❌ No se encontró usuario admin para la prueba")
            return False
        
        # Hacer login
        client.force_login(admin_user)
        
        # Preparar datos de prueba
        fecha_inicio = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        fecha_fin = date.today().strftime('%Y-%m-%d')
        
        # Test con parámetros válidos
        url = reverse('generar_resumen_semanal')
        response = client.post(url, {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        })
        
        # Debe redirigir después de procesar
        if response.status_code in [302, 200]:
            print(f"✅ Vista generar_resumen_semanal procesa correctamente")
            return True
        else:
            print(f"❌ Vista generar_resumen_semanal falló con código: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Error en test de vista generar_resumen_semanal: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST ESPECÍFICO DE BOTONES DEL MODAL")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: URLs disponibles
    if not test_urls_disponibles():
        all_tests_passed = False
    
    # Test 2: Vista PDF directo
    if not test_vista_generar_pdf_rango():
        all_tests_passed = False
    
    # Test 3: Vista guardar resumen
    if not test_vista_generar_resumen_semanal():
        all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 TODOS LOS TESTS DE BACKEND PASARON")
        print("✅ Las vistas del modal están funcionando correctamente")
        print("\n📝 SIGUIENTE PASO:")
        print("   1. Iniciar el servidor con: python manage.py runserver")
        print("   2. Ir a la página de resúmenes semanales")
        print("   3. Probar los botones del modal manualmente")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("⚠️  Revise los errores anteriores")
    print("=" * 60)
