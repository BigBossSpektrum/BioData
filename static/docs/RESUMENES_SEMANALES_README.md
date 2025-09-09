# Sistema de Resúmenes Semanales

## Descripción
Se ha implementado un sistema completo para calcular y gestionar resúmenes semanales de horas trabajadas de los empleados, con cálculo automático de horas extras discriminadas por tipo y sus respectivos costos.

## Características Implementadas

### 1. Modelos de Datos

#### TarifaHoraExtra
- Gestiona las tarifas por hora extra según el tipo:
  - **Diurno**: Horas extras en horario diurno normal
  - **Nocturno**: Horas extras en horario nocturno  
  - **Feriado Diurno**: Horas extras en feriados durante el día
  - **Feriado Nocturno**: Horas extras en feriados durante la noche

#### ResumenSemanal
- Almacena el resumen semanal de cada empleado
- **Período**: Domingo a Lunes (7 días)
- **Información incluida**:
  - Horas normales trabajadas
  - Horas extras por tipo (diurno, nocturno, feriado diurno, feriado nocturno)
  - Costos calculados automáticamente
  - Totales y subtotales

#### FeriadoNacional
- Gestiona los feriados nacionales para cálculo correcto de horas extras

### 2. Funcionalidades del Sistema

#### Cálculo Automático
- El método `calcular_resumen_semanal()` en el modelo `UsuarioBiometrico` procesa automáticamente:
  - Horas trabajadas día por día en la semana
  - Clasificación de horas extras según el tipo de jornada y si es feriado
  - Cálculo de costos basado en las tarifas configuradas

#### Interfaz Web
- **Vista de Resúmenes**: `/resumenes-semanales/`
  - Tabla paginada con todos los resúmenes
  - Filtros por fecha, empleado y estación
  - Información detallada de costos
  - Acciones para ver detalle y descargar PDF

#### Generación Masiva
- Función para generar resúmenes semanales de forma masiva
- Puede procesar empleados individuales o todos a la vez
- Actualiza resúmenes existentes si ya existen

#### Exportación PDF
- Descarga de resúmenes individuales en formato PDF
- Incluye información completa del empleado y desglose de costos
- Diseño profesional con tablas y gráficos

### 3. Permisos y Acceso

#### Restricciones de Acceso
- **Solo Admin y RRHH** pueden acceder a los resúmenes semanales
- Control de permisos implementado en todas las vistas
- Validación tanto en backend como en interfaz

#### Menú de Navegación
- Opción "Resúmenes Semanales" agregada al menú lateral
- Disponible solo para usuarios con rol `admin` o `rrhh`

### 4. Comandos de Gestión

#### populate_initial_data
```bash
python manage.py populate_initial_data
```
- Crea las tarifas iniciales de horas extras
- Añade feriados nacionales de Colombia para 2025

#### generate_sample_resumenes
```bash
python manage.py generate_sample_resumenes --semanas 4
```
- Genera resúmenes semanales de ejemplo
- Útil para pruebas y demostración
- Configurable número de semanas hacia atrás

### 5. Características Técnicas

#### Manejo de Tipos de Datos
- Uso correcto de `Decimal` para cálculos monetarios
- Conversión automática entre tipos para evitar errores
- Precisión matemática en cálculos de costos

#### Paginación
- Tabla con paginación de 20 elementos por página
- Navegación intuitiva con filtros persistentes
- Performance optimizada con `select_related`

#### Responsive Design
- Interfaz adaptable a diferentes tamaños de pantalla
- Uso de Bootstrap 5 para componentes modernos
- Iconos descriptivos para mejor UX

### 6. Lógica de Negocio

#### Semana Laboral
- **Inicio**: Domingo a las 00:00
- **Fin**: Lunes siguiente a las 00:00
- Total: 7 días calendario

#### Clasificación de Horas Extras
1. **Horas Normales**: Dentro del horario establecido de la jornada
2. **Horas Extras Diurno**: Exceso en jornada diurna en días normales
3. **Horas Extras Nocturno**: Exceso en jornada nocturna en días normales  
4. **Horas Extras Feriado Diurno**: Exceso en jornada diurna en feriados
5. **Horas Extras Feriado Nocturno**: Exceso en jornada nocturna en feriados

#### Cálculo de Costos
- Multiplicación automática: `horas_extras × tarifa_por_hora`
- Suma de todos los tipos para costo total
- Actualización automática al cambiar tarifas

### 7. URLs y Rutas

```python
# Nuevas rutas agregadas
path('resumenes-semanales/', views.resumenes_semanales, name='resumenes_semanales'),
path('generar-resumen-semanal/', views.generar_resumen_semanal, name='generar_resumen_semanal'),
path('descargar-pdf-resumen/<int:resumen_id>/', views.descargar_pdf_resumen, name='descargar_pdf_resumen'),
```

### 8. Dependencias Nuevas

```bash
pip install reportlab  # Para generación de PDFs
```

### 9. Migraciones

```bash
python manage.py makemigrations  # Crear migraciones
python manage.py migrate         # Aplicar a la base de datos
```

## Uso del Sistema

### Para Administradores y RRHH:

1. **Configurar Tarifas**:
   - Ir al Admin Django
   - Sección "Tarifas Horas Extras"
   - Configurar precios por tipo

2. **Agregar Feriados**:
   - Sección "Feriados Nacionales" en el Admin
   - Marcar fechas especiales del año

3. **Generar Resúmenes**:
   - Acceder a "Resúmenes Semanales" desde el menú
   - Usar botón "Generar Resumen" para crear nuevos
   - Seleccionar fecha y empleado(s)

4. **Consultar y Exportar**:
   - Usar filtros para buscar resúmenes específicos
   - Ver detalles en modals informativos
   - Descargar PDFs individuales

### Automatización:

El sistema está diseñado para ser usado de forma manual o automática:
- **Manual**: Generación bajo demanda desde la interfaz web
- **Automático**: Se puede configurar con cron jobs o tareas programadas

## Mejoras Futuras Sugeridas

1. **Automatización completa** con tareas programadas semanales
2. **Dashboard** con gráficos y estadísticas
3. **Notificaciones** para administradores sobre resúmenes generados
4. **Exportación masiva** a Excel/CSV
5. **Comparativas** entre semanas/meses
6. **Integración** con sistemas de nómina externos
