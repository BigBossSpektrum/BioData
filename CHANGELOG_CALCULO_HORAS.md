# Documentación: Nuevo Cálculo de Horas Trabajadas

## Resumen de Cambios

Se ha modificado el sistema de cálculo de horas trabajadas en los archivos `API/models.py` para implementar las siguientes reglas de negocio:

### Reglas Implementadas

1. **Solo se cuentan las horas dentro de la jornada laboral asignada**
2. **Si el empleado llega antes de la hora pautada, esa hora extra NO se contabiliza**
3. **El tiempo empieza a correr a partir de la hora de inicio de la jornada**
4. **Las horas extras SÍ se contabilizan cuando el empleado sale después del horario**
5. **Se respetan los 3 modelos de jornada laboral:**
   - **Mañana**: 06:00 - 14:00
   - **Tarde**: 14:00 - 22:00  
   - **Nocturno**: 22:00 - 06:00

### Caso Ejemplo: Ramiro de Jesús Amado

**Datos del registro:**
- Jornada: Mañana (06:00 - 14:00)
- Entrada: 05:53 (7 minutos antes)
- Salida: 18:05 (4 horas 5 minutos después)

**Cálculo correcto:**
- ✅ **Horas normales**: 8.0 horas (de 06:00 a 14:00)
- ✅ **Horas extras**: 4.08 horas (de 14:00 a 18:05)
- ✅ **Total**: 12.08 horas

### Ejemplos de Funcionamiento

#### Jornada de Mañana (06:00 - 14:00)
- **Empleado llega a las 05:00 y sale a las 14:00**: 8 horas normales + 0 extras = 8 horas total
- **Empleado llega a las 06:00 y sale a las 15:00**: 8 horas normales + 1 extra = 9 horas total
- **Empleado llega a las 07:30 y sale a las 16:30**: 6.5 horas normales + 2.5 extras = 9 horas total

#### Jornada de Tarde (14:00 - 22:00)
- **Empleado llega a las 13:00 y sale a las 22:00**: 8 horas normales + 0 extras = 8 horas total
- **Empleado llega a las 14:00 y sale a las 23:00**: 8 horas normales + 1 extra = 9 horas total
- **Empleado llega a las 15:30 y sale a las 23:00**: 6.5 horas normales + 1 extra = 7.5 horas total

#### Jornada Nocturna (22:00 - 06:00)
- **Empleado llega a las 21:00 y sale a las 06:00**: 8 horas normales + 0 extras = 8 horas total
- **Empleado llega a las 22:00 y sale a las 07:00**: 8 horas normales + 1 extra = 9 horas total
- **Empleado llega a las 23:30 y sale a las 06:00**: 6.5 horas normales + 0 extras = 6.5 horas total

### Cambios Técnicos

#### Archivo Modificado: `API/models.py`

**1. Método `calcular_horas_trabajadas` actualizado:**
- Ahora calcula las horas totales incluyendo horas extras
- No cuenta tiempo antes del inicio de jornada
- SÍ cuenta tiempo después del fin de jornada como extras

**2. Nuevo método `calcular_horas_normales_y_extras`:**
- Separa claramente horas normales de horas extras
- Retorna un diccionario con:
  - `horas_normales`: Solo dentro de la jornada
  - `horas_extras`: Solo después del fin de jornada
  - `horas_totales`: Suma de normales + extras

**3. Método `calcular_horas_dia` del usuario actualizado:**
- Usa el nuevo método detallado
- Proporciona información más precisa sobre horas normales y extras
- Incluye `horas_normales` en el resultado

### Lógica de Cálculo

1. **Entrada efectiva** = `max(entrada_real, inicio_jornada)`
   - No se cuenta tiempo antes de la jornada

2. **Horas normales** = Tiempo desde entrada efectiva hasta `min(salida_real, fin_jornada)`
   - Máximo: horas_normales de la jornada (generalmente 8)

3. **Horas extras** = Tiempo desde fin_jornada hasta salida_real (si salida > fin_jornada)
   - Solo si el empleado sale después del horario establecido

4. **Total** = Horas normales + Horas extras

### Validación

Se han creado scripts de prueba que validan todos los casos de uso, incluyendo el caso específico de Ramiro, y confirman que la lógica funciona correctamente.

### Impacto en el Sistema

- ✅ **Compatible con el código existente**: Los métodos que llaman a `calcular_horas_trabajadas` siguen funcionando
- ✅ **No afecta la base de datos**: Solo cambia la lógica de cálculo
- ✅ **Respeta los turnos nocturnos**: Maneja correctamente los turnos que cruzan medianoche
- ✅ **Separa horas normales y extras**: Proporciona información más detallada
- ✅ **Calcula horas extras correctamente**: Cuando el empleado trabaja más allá de su jornada

### Beneficios

1. **Mayor precisión**: Solo cuenta tiempo dentro de la jornada como horas normales
2. **Cálculo correcto de extras**: Las horas trabajadas después del horario se contabilizan como extras
3. **Previene abuso**: Empleados no pueden "acumular" horas llegando muy temprano
4. **Transparencia**: Clara separación entre horas normales y extras
5. **Justicia laboral**: Todos los empleados son evaluados bajo las mismas reglas

---

**Fecha de implementación**: Septiembre 2025  
**Desarrollador**: GitHub Copilot  
**Estado**: ✅ Implementado, Validado y Corregido
