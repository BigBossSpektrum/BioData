# Panel Exclusivo para Jefes de Patio - Jornadas Especiales de 12 Horas

## 📋 Resumen de Implementación

Se ha implementado un sistema completo que permite a los jefes de patio habilitar jornadas especiales de 12 horas para empleados de su estación. Estas jornadas pueden extenderse de un día a otro.

## 🚀 Características Principales

### ✅ Panel Exclusivo para Jefes de Patio
- **URL**: `/panel-jefe-patio/`
- **Acceso**: Solo usuarios con rol `jefe_patio`
- **Funcionalidades**:
  - Crear nuevas jornadas especiales
  - Ver jornadas especiales activas
  - Desactivar jornadas especiales
  - Visualizar estadísticas de empleados

### ✅ Jornadas Especiales de 12 Horas
- **Duración**: Configurable (por defecto 12 horas)
- **Flexibilidad**: Pueden pasar de un día a otro
- **Lógica**: Toma la primera entrada del día y la siguiente salida sin importar que sea del día siguiente
- **Validaciones**: Previene solapamientos de jornadas especiales

### ✅ Cálculo Inteligente de Horas
- **Algoritmo Especial**: Para jornadas especiales de 12 horas:
  - Hasta 12 horas: consideradas normales
  - Más de 12 horas: consideradas extras
- **Integración**: Se integra con el sistema existente de cálculo de horas
- **Identificación**: Los registros con jornadas especiales se marcan con badge especial

## 🛠️ Implementación Técnica

### 📁 Modelos
```python
# API/models.py
class JornadaEspecial(models.Model):
    empleado = models.ForeignKey('UsuarioBiometrico', ...)
    fecha_inicio = models.DateField(...)
    fecha_fin = models.DateField(...)
    hora_inicio_programada = models.TimeField(...)
    hora_fin_programada = models.TimeField(...)
    horas_programadas = models.DecimalField(default=12.00)
    aprobada_por = models.ForeignKey(CustomUser, ...)
    activa = models.BooleanField(default=True)
    observaciones = models.TextField(...)
```

### 📁 Vistas
```python
# frontend/views.py
@login_required
def panel_jefe_patio(request):
    """Panel principal para jefe de patio"""

@login_required  
def crear_jornada_especial(request):
    """Crear nueva jornada especial"""

@login_required
def desactivar_jornada_especial(request, jornada_id):
    """Desactivar jornada especial"""
```

### 📁 URLs
```python
# frontend/urls.py
path('panel-jefe-patio/', views.panel_jefe_patio, name='panel_jefe_patio'),
path('crear-jornada-especial/', views.crear_jornada_especial, name='crear_jornada_especial'),
path('desactivar-jornada-especial/<int:jornada_id>/', views.desactivar_jornada_especial, name='desactivar_jornada_especial'),
```

### 📁 Templates
- `frontend/templates/frontend/panel_jefe_patio.html`: Panel principal
- Modificaciones en `resumen_asistencias_diarias.html`: Badge para jornadas especiales

## 🔧 Funcionalidades del Sistema

### 1. Creación de Jornadas Especiales
- **Formulario Intuitivo**: Modal con validaciones en tiempo real
- **Campos**:
  - Empleado (filtrado por estación del jefe)
  - Fecha de inicio y fin
  - Horario programado
  - Horas programadas (default: 12)
  - Observaciones opcionales

### 2. Gestión de Jornadas Activas
- **Vista de Tabla**: Muestra todas las jornadas especiales activas
- **Información Mostrada**:
  - Empleado y su información
  - Fechas de vigencia
  - Horario programado
  - Estado (activa/inactiva)
  - Acciones disponibles

### 3. Cálculo Especial de Horas
- **Algoritmo Inteligente**: 
  ```python
  def _calcular_horas_jornada_especial(self, fecha, jornada_especial):
      # Busca la primera entrada del día
      # Busca la siguiente salida (puede ser del día siguiente)
      # Calcula: hasta 12h normales, más de 12h extras
  ```

### 4. Integración con Sistema Existente
- **Badge Especial**: En resumen de asistencias se marca con badge "12H"
- **Tooltips Informativos**: Muestran detalles de la jornada especial
- **Filtros Respetados**: Solo ve empleados de su estación

## 🎯 Casos de Uso

### Caso 1: Jornada Normal de 12 Horas
- **Entrada**: 06:00 del día 1
- **Salida**: 18:00 del día 1
- **Resultado**: 12 horas normales, 0 extras

### Caso 2: Jornada Extendida al Día Siguiente
- **Entrada**: 06:00 del día 1
- **Salida**: 06:00 del día 2
- **Resultado**: 12 horas normales, 12 extras (total: 24h)

### Caso 3: Jornada con Horas Extras
- **Entrada**: 06:00 del día 1
- **Salida**: 20:00 del día 1
- **Resultado**: 12 horas normales, 2 extras (total: 14h)

## 📊 Validaciones Implementadas

### 1. Validaciones de Modelo
- No solapamiento de jornadas especiales para el mismo empleado
- Fecha fin no puede ser anterior a fecha inicio
- Solo jefes de patio pueden aprobar jornadas

### 2. Validaciones de Vista
- Usuario debe ser jefe de patio
- Empleado debe pertenecer a la estación del jefe
- Campos obligatorios completos

### 3. Validaciones de Frontend
- Fecha mínima es hoy
- Fecha fin no puede ser anterior a fecha inicio
- Confirmación para desactivar jornadas

## 🔐 Seguridad y Permisos

### Control de Acceso
- **Rol Requerido**: `jefe_patio`
- **Filtrado por Estación**: Solo ve empleados de su estación
- **CSRF Protection**: Todos los formularios protegidos

### Auditoría
- **Registro de Aprobación**: Quién y cuándo aprobó cada jornada
- **Timestamps**: Fecha de creación y modificación
- **Observaciones**: Campo para documentar motivos

## 🧪 Datos de Prueba

Se incluye el script `test_jornadas_especiales.py` que:
- Crea un jefe de patio de ejemplo (`jefe_ejemplo` / `123456`)
- Crea una estación y empleado de prueba
- Crea una jornada especial activa
- Genera registros de asistencia de ejemplo
- Demuestra el cálculo de horas especiales

### Ejecutar Pruebas
```bash
cd /c/ControlIngreso/BioData
env/Scripts/python.exe test_jornadas_especiales.py
```

## 🌐 URLs de Acceso

- **Panel Jefe de Patio**: http://127.0.0.1:8000/panel-jefe-patio/
- **Admin Django**: http://127.0.0.1:8000/admin/
- **Login Principal**: http://127.0.0.1:8000/

## 📱 Navegación del Sistema

El panel se integra en el menú lateral existente:
```
Para Jefe de Patio:
├── Panel Jefe de Patio (NUEVO)
├── Historial de Asistencias
└── Resumen Asistencias
```

## ✨ Características Adicionales

### 1. Interfaz Responsive
- Diseño adaptable a móviles y tablets
- Bootstrap 5 para UI moderna
- Iconos Bootstrap Icons

### 2. Experiencia de Usuario
- Tooltips informativos
- Confirmaciones de acciones críticas
- Mensajes de éxito/error claros
- Validaciones en tiempo real

### 3. Estadísticas en Tiempo Real
- Total de empleados por estación
- Jornadas especiales activas
- Indicadores visuales de estado

## 🔄 Flujo de Trabajo

1. **Jefe de Patio** accede al panel
2. **Selecciona empleado** de su estación
3. **Configure fechas y horarios** de la jornada especial
4. **Agrega observaciones** si es necesario
5. **Crea la jornada especial**
6. **El sistema calcula automáticamente** las horas cuando hay registros
7. **Se muestra badge especial** en reportes de asistencia

## 🎉 Resultado Final

El sistema ahora permite:
- ✅ Jefes de patio pueden crear jornadas especiales de 12 horas
- ✅ Las jornadas pueden extenderse al día siguiente
- ✅ Cálculo automático: primera entrada + siguiente salida
- ✅ Panel exclusivo con control de acceso
- ✅ Integración completa con sistema existente
- ✅ Validaciones y seguridad implementadas
- ✅ Interfaz moderna y responsive

¡El panel exclusivo para jefes de patio está completamente implementado y funcional!
