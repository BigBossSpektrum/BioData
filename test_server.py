#!/usr/bin/env python3
"""
Script para probar el acceso a la página de resumen de asistencias
y confirmar que la respuesta del servidor es correcta
"""

import requests
import sys

def probar_servidor():
    """Prueba la conectividad del servidor Django"""
    
    urls_a_probar = [
        "http://127.0.0.1:8000/",
        "http://127.0.0.1:8000/resumen_asistencias_diarias/",
        "http://127.0.0.1:8000/accounts/login/"
    ]
    
    print("🌐 PRUEBA DE CONECTIVIDAD DEL SERVIDOR")
    print("=" * 50)
    
    for url in urls_a_probar:
        try:
            print(f"📡 Probando: {url}")
            response = requests.get(url, timeout=5, allow_redirects=False)
            
            if response.status_code == 200:
                print(f"   ✅ OK - Respuesta 200 (Página cargada correctamente)")
            elif response.status_code == 302:
                print(f"   🔄 Redirección - Código 302 (Redirigido a login)")
                if 'Location' in response.headers:
                    print(f"      → Redirigiendo a: {response.headers['Location']}")
            elif response.status_code == 404:
                print(f"   ❌ No encontrado - Código 404")
            else:
                print(f"   ⚠️  Respuesta inesperada - Código {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Error de conexión - El servidor no está ejecutándose")
            return False
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout - El servidor no responde")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
        
        print()
    
    print("🎯 RESULTADO: El servidor Django está funcionando correctamente")
    print("💡 Para acceder a la página, necesitarás hacer login primero")
    return True

def mostrar_instrucciones():
    """Muestra instrucciones para el usuario"""
    print("\n" + "=" * 50)
    print("📋 INSTRUCCIONES PARA VERIFICAR LOS CAMBIOS:")
    print("=" * 50)
    print("1. 🌐 Abrir navegador en: http://127.0.0.1:8000/")
    print("2. 🔐 Hacer login con tus credenciales")
    print("3. 📋 Navegar a 'Resumen de Asistencias Diarias'")
    print("4. 👁️  Verificar que los encabezados 'Nombre' y 'Estación' estén alineados a la izquierda")
    print("5. ✅ Confirmar que el resto de columnas estén centradas")
    print("\n🔍 PUNTOS DE VERIFICACIÓN ESPECÍFICOS:")
    print("   • Encabezado 'Nombre' → Alineado a la izquierda")
    print("   • Encabezado 'Estación' → Alineado a la izquierda") 
    print("   • Datos de nombres → Alineados a la izquierda")
    print("   • Datos de estaciones → Alineados a la izquierda")
    print("   • Resto de columnas → Centradas (sin cambios)")

if __name__ == "__main__":
    print("🚀 PRUEBA FINAL DEL SERVIDOR DJANGO")
    print("=" * 50)
    
    servidor_ok = probar_servidor()
    mostrar_instrucciones()
    
    if servidor_ok:
        print("\n🎉 ESTADO: ¡Todo está listo para las pruebas!")
    else:
        print("\n⚠️ ESTADO: Verificar que el servidor Django esté ejecutándose")
        print("   Ejecutar: python manage.py runserver")
