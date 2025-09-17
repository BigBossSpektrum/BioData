# Registros Biométricos

Esta carpeta contiene los logs de todos los datos recibidos del dispositivo biométrico para control y monitoreo.

## Estructura de los archivos de log

Los archivos se generan con el formato: `biodata_{ESTACION}_{YYYY-MM-DD}.json`

**Ejemplos:**
- `biodata_Iberia_2025-09-17.json`
- `biodata_Monteria_2025-09-17.json`
- `biodata_SinEstacion_2025-09-17.json`

### Contenido del log (Versión 2.0):
```json
{
  "metadata": {
    "version_log": "2.0",
    "servidor": "BioData API",
    "endpoint": "/API/recibir_datos_biometrico/",
    "estacion_principal": "Iberia",
    "fecha_archivo": "2025-09-17",
    "creado_en": "2025-09-17 10:30:00",
    "ultima_actualizacion": "2025-09-17 15:45:00",
    "total_recepciones": 5,
    "total_registros_acumulados": 125
  },
  "recepciones": [
    {
      "timestamp_recepcion": "2025-09-17 10:30:00",
      "ip_cliente": "192.168.1.100",
      "user_agent": "Dispositivo Biométrico/1.0",
      "total_registros": 25,
      "datos_recibidos": [...]
    },
    {
      "timestamp_recepcion": "2025-09-17 15:45:00",
      "ip_cliente": "192.168.1.100",
      "user_agent": "Dispositivo Biométrico/1.0", 
      "total_registros": 30,
      "datos_recibidos": [...]
    }
  ]
}
```

## Características del Sistema

### ✅ **Agrupación Inteligente**
- Un archivo por estación por día
- Los datos se van agregando al mismo archivo
- No se sobreescriben datos existentes

### ✅ **Historial Completo**
- Cada recepción se guarda como entrada separada
- Timestamp de cada envío del dispositivo
- Estadísticas acumulativas

### ✅ **Metadata Enriquecida**
- Información de la estación principal
- Contadores de recepciones y registros
- Timestamps de creación y última actualización

## Propósito

Estos logs permiten:
1. **📊 Auditoría**: Revisar qué datos fueron enviados por cada estación
2. **🔍 Debugging**: Analizar problemas en la recepción de datos
3. **📈 Análisis**: Estudiar patrones de envío por estación y fecha
4. **💾 Backup**: Tener una copia de seguridad organizada por estación
5. **⏰ Historial**: Ver la evolución de los datos a lo largo del día

## Ventajas del Nuevo Sistema

- **🗂️ Organización**: Fácil localización de logs por estación y fecha
- **💾 Eficiencia**: Un solo archivo por estación por día reduce fragmentación
- **📊 Estadísticas**: Contadores automáticos para análisis rápido
- **🔄 Actualización**: Los datos se van agregando sin pérdida de información
- **🎯 Precisión**: Identificación clara de la estación de origen

## Nota de Seguridad

⚠️ **IMPORTANTE**: Estos archivos contienen información sensible de asistencias y NO deben ser compartidos o subidos al repositorio de código.

Los archivos están configurados para ser ignorados por Git mediante el archivo `.gitignore`.
