"""
Comando de prueba para verificar filtros de jefe de patio
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from API.models import EstacionServicio, UsuarioBiometrico, RegistroAsistencia
from frontend.utils_filters import aplicar_filtro_jefe_patio, obtener_info_estacion_jefe

User = get_user_model()

class Command(BaseCommand):
    help = 'Prueba los filtros de jefe de patio'

    def handle(self, *args, **options):
        self.stdout.write("=== Pruebas de Filtros por Jefe de Patio ===\n")
        
        # Buscar jefes de patio
        jefes_patio = User.objects.filter(rol='jefe_patio')
        
        if not jefes_patio.exists():
            self.stdout.write(
                self.style.WARNING('No se encontraron jefes de patio en el sistema')
            )
            return
        
        for jefe in jefes_patio:
            self.stdout.write(f"\n--- Probando Jefe de Patio: {jefe.username} ---")
            
            # Obtener información de estación
            info_estacion = obtener_info_estacion_jefe(jefe)
            
            if info_estacion['estacion_filtrada']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Estación asignada: {info_estacion['estacion_filtrada']}"
                    )
                )
                
                # Probar filtro de registros
                registros_totales = RegistroAsistencia.objects.count()
                registros_filtrados = aplicar_filtro_jefe_patio(
                    RegistroAsistencia.objects.all(), 
                    jefe
                ).count()
                
                self.stdout.write(
                    f"📊 Registros totales: {registros_totales}"
                )
                self.stdout.write(
                    f"📊 Registros filtrados: {registros_filtrados}"
                )
                
                # Probar filtro de usuarios
                usuarios_totales = UsuarioBiometrico.objects.count()
                usuarios_filtrados = aplicar_filtro_jefe_patio(
                    UsuarioBiometrico.objects.all(),
                    jefe,
                    'estacion'
                ).count()
                
                self.stdout.write(
                    f"👤 Usuarios totales: {usuarios_totales}"
                )
                self.stdout.write(
                    f"👤 Usuarios filtrados: {usuarios_filtrados}"
                )
                
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️ No tiene estación asignada"
                    )
                )
                
                # Verificar que el filtro devuelve vacío
                registros_filtrados = aplicar_filtro_jefe_patio(
                    RegistroAsistencia.objects.all(), 
                    jefe
                ).count()
                
                if registros_filtrados == 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "✅ Filtro funciona correctamente (no muestra registros)"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Error: Debería mostrar 0 registros pero muestra {registros_filtrados}"
                        )
                    )
        
        # Probar con usuario no jefe de patio
        self.stdout.write(f"\n--- Probando Usuario No Jefe de Patio ---")
        otros_usuarios = User.objects.exclude(rol='jefe_patio').first()
        
        if otros_usuarios:
            info_estacion = obtener_info_estacion_jefe(otros_usuarios)
            
            if not info_estacion['es_jefe_patio']:
                self.stdout.write(
                    self.style.SUCCESS(
                        "✅ Usuario no es jefe de patio - no hay filtrado"
                    )
                )
                
                registros_sin_filtro = RegistroAsistencia.objects.count()
                registros_con_filtro = aplicar_filtro_jefe_patio(
                    RegistroAsistencia.objects.all(),
                    otros_usuarios
                ).count()
                
                if registros_sin_filtro == registros_con_filtro:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "✅ Filtro no afecta a usuarios que no son jefe de patio"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            "❌ Error: El filtro está afectando usuarios no jefe de patio"
                        )
                    )
        
        self.stdout.write(f"\n=== Fin de Pruebas ===")
