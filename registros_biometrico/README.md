# Registros Biométricos

Esta carpeta contiene los logs de todos los datos recibidos del dispositivo biométrico para control y monitoreo.

## Estructura de los archivos de log

Los archivos se generan con el formato: `biodata_log_YYYY-MM-DD_HH-MM-SS.json`

### Contenido del log:
- **timestamp_recepcion**: Momento en que se recibieron los datos
- **ip_cliente**: Dirección IP del dispositivo que envió los datos
- **user_agent**: Información del cliente que realizó la petición
- **total_registros**: Cantidad de registros recibidos
- **datos_recibidos**: Array completo con todos los datos enviados por el dispositivo
- **metadata**: Información adicional del sistema

## Propósito

Estos logs permiten:
1. **Auditoría**: Revisar qué datos fueron enviados por los dispositivos biométricos
2. **Debugging**: Analizar problemas en la recepción de datos
3. **Análisis**: Estudiar patrones de envío de datos
4. **Backup**: Tener una copia de seguridad de los datos recibidos

## Nota de Seguridad

⚠️ **IMPORTANTE**: Estos archivos contienen información sensible de asistencias y NO deben ser compartidos o subidos al repositorio de código.

Los archivos están configurados para ser ignorados por Git mediante el archivo `.gitignore`.
